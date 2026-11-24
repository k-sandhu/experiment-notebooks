use serde::de::{self, SeqAccess, Visitor};
use serde::{Deserialize, Deserializer};
use std::borrow::Cow;
use std::collections::HashMap;
use std::fmt;
use std::fs::File;
use std::io::{self, BufRead, BufReader, BufWriter, Write};

#[derive(Deserialize)]
struct Header {
    rates: HashMap<String, Box<serde_json::value::RawValue>>,
}

#[derive(Deserialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
enum Kind {
    Credit,
    Debit,
    Refund,
    Void,
}

// Reduce tags during decoding; never allocate a vector of strings.
struct TestTag(bool);

impl<'de> Deserialize<'de> for TestTag {
    fn deserialize<D: Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
        struct TagVisitor;
        impl Visitor<'_> for TagVisitor {
            type Value = TestTag;
            fn expecting(&self, f: &mut fmt::Formatter) -> fmt::Result {
                f.write_str("a tag string")
            }
            fn visit_str<E: de::Error>(self, value: &str) -> Result<TestTag, E> {
                Ok(TestTag(value == "test"))
            }
        }
        deserializer.deserialize_str(TagVisitor)
    }
}

fn test_tags<'de, D: Deserializer<'de>>(deserializer: D) -> Result<bool, D::Error> {
    struct TagsVisitor;
    impl<'de> Visitor<'de> for TagsVisitor {
        type Value = bool;
        fn expecting(&self, f: &mut fmt::Formatter) -> fmt::Result {
            f.write_str("an array of tags")
        }
        fn visit_seq<A: SeqAccess<'de>>(self, mut tags: A) -> Result<bool, A::Error> {
            let mut test = false;
            while let Some(tag) = tags.next_element::<TestTag>()? {
                test |= tag.0;
            }
            Ok(test)
        }
    }
    deserializer.deserialize_seq(TagsVisitor)
}

#[derive(Deserialize)]
struct Meta<'a> {
    #[serde(borrow)]
    channel: Cow<'a, str>,
}

#[derive(Deserialize)]
struct Transaction<'a> {
    #[serde(borrow)]
    account: Cow<'a, str>,
    #[serde(rename = "type")]
    kind: Kind,
    #[serde(borrow)]
    amount: Cow<'a, str>,
    #[serde(borrow)]
    currency: Cow<'a, str>,
    #[serde(deserialize_with = "test_tags")]
    tags: bool,
    #[serde(borrow)]
    meta: Meta<'a>,
}

#[inline]
fn hundredths(amount: &str) -> u64 {
    let mut value = 0u64;
    let mut decimals = None;
    for byte in amount.bytes() {
        if byte == b'.' {
            decimals = Some(0u8);
        } else {
            value = value * 10 + u64::from(byte - b'0');
            if let Some(ref mut digits) = decimals {
                *digits += 1;
            }
        }
    }
    match decimals {
        None => value * 100,
        Some(1) => value * 10,
        _ => value,
    }
}

#[derive(Default)]
struct Ledger {
    counted: u64,
    net: i64,
    accounts: HashMap<String, i64>,
    channels: HashMap<String, (u64, i64)>,
}

impl Ledger {
    #[inline]
    fn process(&mut self, line: &[u8], rates: &HashMap<String, i64>) {
        let transaction: Transaction<'_> = serde_json::from_slice(line).expect("transaction JSON");
        if transaction.kind == Kind::Void || transaction.tags {
            return;
        }
        let rate = rates[transaction.currency.as_ref()];
        let usd = if rate == 0 {
            0
        } else {
            let product = (i128::from(hundredths(&transaction.amount)) * i128::from(rate)) as i64;
            product.div_euclid(1_000_000)
        };
        let value = if transaction.kind == Kind::Debit {
            -usd
        } else {
            usd
        };
        self.counted += 1;
        self.net = self.net.wrapping_add(value);

        if let Some(total) = self.accounts.get_mut(transaction.account.as_ref()) {
            *total = total.wrapping_add(value);
        } else {
            self.accounts
                .insert(transaction.account.into_owned(), value);
        }
        if let Some((count, total)) = self.channels.get_mut(transaction.meta.channel.as_ref()) {
            *count += 1;
            *total = total.wrapping_add(value);
        } else {
            self.channels
                .insert(transaction.meta.channel.into_owned(), (1, value));
        }
    }
}

fn main() -> io::Result<()> {
    let path = std::env::args_os().nth(1).expect("input path");
    let mut source = BufReader::with_capacity(1024 * 1024, File::open(path)?);
    let mut spill = Vec::new();
    source.read_until(b'\n', &mut spill)?;
    let header: Header = serde_json::from_slice(&spill).expect("rates JSON");
    // If a rate exceeds i64, the promised product bound implies that every
    // counted amount in that currency is zero. Avoid imposing a rate-size limit.
    let rates: HashMap<String, i64> = header
        .rates
        .into_iter()
        .map(|(name, rate)| (name, rate.get().parse::<i64>().unwrap_or(0)))
        .collect();
    spill.clear();
    let mut ledger = Ledger::default();

    // Reuse a single line allocation; read_until uses the standard library's
    // optimized delimiter search inside the large input buffer.
    while source.read_until(b'\n', &mut spill)? != 0 {
        ledger.process(&spill, &rates);
        spill.clear();
    }

    let mut out = BufWriter::new(io::stdout().lock());
    writeln!(out, "counted {}", ledger.counted)?;
    writeln!(out, "net {}", ledger.net)?;
    let mut channels: Vec<_> = ledger.channels.iter().collect();
    channels.sort_unstable_by(|a, b| a.0.cmp(b.0));
    for (name, (count, total)) in channels {
        writeln!(out, "channel {name} {count} {total}")?;
    }
    let mut accounts: Vec<_> = ledger.accounts.iter().collect();
    let compare =
        |a: &(&String, &i64), b: &(&String, &i64)| b.1.cmp(a.1).then_with(|| a.0.cmp(b.0));
    if accounts.len() > 10 {
        accounts.select_nth_unstable_by(10, compare);
        accounts.truncate(10);
    }
    accounts.sort_unstable_by(compare);
    for (name, total) in accounts {
        writeln!(out, "account {name} {total}")?;
    }
    out.flush()
}
