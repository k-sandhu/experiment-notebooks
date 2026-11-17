use std::borrow::Cow;
use std::collections::HashMap;
use std::io::{self, Write};

type Bytes<'a> = Cow<'a, [u8]>;

struct Transaction<'a> {
    account: Bytes<'a>,
    amount: Bytes<'a>,
    currency: Bytes<'a>,
    channel: Bytes<'a>,
    debit: bool,
}

struct Parser<'a> {
    data: &'a [u8],
    pos: usize,
}

impl<'a> Parser<'a> {
    #[inline]
    fn whitespace(&mut self) {
        while self.pos < self.data.len()
            && matches!(self.data[self.pos], b' ' | b'\t' | b'\r' | b'\n')
        {
            self.pos += 1;
        }
    }

    #[inline]
    fn string(&mut self) -> Bytes<'a> {
        let start = self.pos;
        let mut i = start + 1;
        let mut escaped = false;

        loop {
            match self.data[i] {
                b'"' => break,
                b'\\' => {
                    escaped = true;
                    i += 2;
                }
                _ => i += 1,
            }
        }

        self.pos = i + 1;
        if escaped {
            Cow::Owned(
                serde_json::from_slice::<String>(&self.data[start..self.pos])
                    .unwrap()
                    .into_bytes(),
            )
        } else {
            Cow::Borrowed(&self.data[start + 1..i])
        }
    }

    #[inline]
    fn skip_string(&mut self) {
        let mut i = self.pos + 1;
        loop {
            match self.data[i] {
                b'"' => {
                    self.pos = i + 1;
                    return;
                }
                b'\\' => i += 2,
                _ => i += 1,
            }
        }
    }

    fn skip_value(&mut self) {
        self.whitespace();
        match self.data[self.pos] {
            b'"' => self.skip_string(),
            b'{' | b'[' => {
                self.pos += 1;
                let mut depth = 1usize;
                while depth != 0 {
                    match self.data[self.pos] {
                        b'"' => self.skip_string(),
                        b'{' | b'[' => {
                            depth += 1;
                            self.pos += 1;
                        }
                        b'}' | b']' => {
                            depth -= 1;
                            self.pos += 1;
                        }
                        _ => self.pos += 1,
                    }
                }
            }
            _ => {
                while !matches!(
                    self.data[self.pos],
                    b',' | b'}' | b']' | b' ' | b'\t' | b'\r' | b'\n'
                ) {
                    self.pos += 1;
                }
            }
        }
    }

    #[inline]
    fn skip_line(&mut self) {
        // Literal newlines cannot occur inside JSON strings.
        while self.data[self.pos] != b'\n' {
            self.pos += 1;
        }
        self.pos += 1;
    }

    fn rate_integer(&mut self) -> i128 {
        let negative = self.data[self.pos] == b'-';
        if negative {
            self.pos += 1;
        }

        // Larger magnitudes can only multiply zero under the product bound.
        const LIMIT: i128 = (1i128 << 63) + 1;
        let mut value = 0i128;
        while self.pos < self.data.len() {
            let digit = self.data[self.pos];
            if !digit.is_ascii_digit() {
                break;
            }
            value = (value * 10 + i128::from(digit - b'0')).min(LIMIT);
            self.pos += 1;
        }

        if negative { -value } else { value }
    }

    fn rates(&mut self) -> HashMap<Bytes<'a>, i128> {
        let mut rates = HashMap::new();
        self.whitespace();
        self.pos += 1;

        loop {
            self.whitespace();
            if self.data[self.pos] == b'}' {
                self.pos += 1;
                break;
            }

            let key = self.string();
            self.whitespace();
            self.pos += 1;
            self.whitespace();

            if key.as_ref() == b"rates" {
                self.pos += 1;
                loop {
                    self.whitespace();
                    if self.data[self.pos] == b'}' {
                        self.pos += 1;
                        break;
                    }

                    let currency = self.string();
                    self.whitespace();
                    self.pos += 1;
                    self.whitespace();

                    let rate = self.rate_integer();
                    rates.insert(currency, rate);

                    self.whitespace();
                    let separator = self.data[self.pos];
                    self.pos += 1;
                    if separator == b'}' {
                        break;
                    }
                }
            } else {
                self.skip_value();
            }

            self.whitespace();
            let separator = self.data[self.pos];
            self.pos += 1;
            if separator == b'}' {
                break;
            }
        }

        rates
    }

    fn tags_contain_test(&mut self) -> bool {
        self.pos += 1;
        self.whitespace();
        if self.data[self.pos] == b']' {
            self.pos += 1;
            return false;
        }

        loop {
            self.whitespace();
            if self.string().as_ref() == b"test" {
                // The caller discards the remainder of this JSON line.
                return true;
            }

            self.whitespace();
            let separator = self.data[self.pos];
            self.pos += 1;
            if separator == b']' {
                return false;
            }
        }
    }

    fn meta_channel(&mut self) -> Bytes<'a> {
        let mut channel: Bytes<'a> = Cow::Borrowed(b"");
        self.pos += 1;

        loop {
            self.whitespace();
            if self.data[self.pos] == b'}' {
                self.pos += 1;
                break;
            }

            let key = self.string();
            self.whitespace();
            self.pos += 1;
            self.whitespace();

            if key.as_ref() == b"channel" {
                channel = self.string();
            } else {
                self.skip_value();
            }

            self.whitespace();
            let separator = self.data[self.pos];
            self.pos += 1;
            if separator == b'}' {
                break;
            }
        }

        channel
    }

    fn transaction(&mut self) -> Option<Transaction<'a>> {
        let mut tx = Transaction {
            account: Cow::Borrowed(b""),
            amount: Cow::Borrowed(b""),
            currency: Cow::Borrowed(b""),
            channel: Cow::Borrowed(b""),
            debit: false,
        };
        self.pos += 1;

        loop {
            self.whitespace();
            let key = self.string();
            self.whitespace();
            self.pos += 1;
            self.whitespace();

            match key.as_ref() {
                b"account" => tx.account = self.string(),
                b"amount" => tx.amount = self.string(),
                b"currency" => tx.currency = self.string(),
                b"type" => {
                    let kind = self.string();
                    if kind.as_ref() == b"void" {
                        self.skip_line();
                        return None;
                    }
                    tx.debit = kind.as_ref() == b"debit";
                }
                b"tags" => {
                    if self.tags_contain_test() {
                        self.skip_line();
                        return None;
                    }
                }
                b"meta" => tx.channel = self.meta_channel(),
                _ => self.skip_value(),
            }

            self.whitespace();
            let separator = self.data[self.pos];
            self.pos += 1;
            if separator == b'}' {
                break;
            }
        }

        Some(tx)
    }
}

#[inline]
fn hundredths(amount: &[u8]) -> u64 {
    let mut whole = 0u64;
    let mut i = 0;

    while i < amount.len() && amount[i] != b'.' {
        whole = whole * 10 + u64::from(amount[i] - b'0');
        i += 1;
    }

    let mut result = whole * 100;
    if i < amount.len() {
        i += 1;
        result += u64::from(amount[i] - b'0') * 10;
        if i + 1 < amount.len() {
            result += u64::from(amount[i + 1] - b'0');
        }
    }
    result
}

fn main() {
    let path = std::env::args_os().nth(1).unwrap();
    let input = std::fs::read(path).unwrap();
    let mut parser = Parser {
        data: &input,
        pos: 0,
    };
    let rates = parser.rates();

    let mut counted = 0u64;
    let mut net = 0i128;
    let mut channels: HashMap<Bytes<'_>, (u64, i128)> = HashMap::new();
    let mut accounts: HashMap<Bytes<'_>, i128> = HashMap::new();

    loop {
        parser.whitespace();
        if parser.pos == input.len() {
            break;
        }

        let Some(tx) = parser.transaction() else {
            continue;
        };

        let rate = *rates.get(tx.currency.as_ref()).unwrap();
        let usd = if rate == 0 {
            0i64
        } else {
            let cents = hundredths(tx.amount.as_ref());
            let product = (i128::from(cents) * rate) as i64;
            product.div_euclid(1_000_000)
        };
        let signed = if tx.debit {
            -i128::from(usd)
        } else {
            i128::from(usd)
        };

        counted += 1;
        net += signed;

        let channel = channels.entry(tx.channel).or_insert((0, 0));
        channel.0 += 1;
        channel.1 += signed;

        *accounts.entry(tx.account).or_insert(0) += signed;
    }

    let mut channels: Vec<_> = channels.into_iter().collect();
    channels.sort_unstable_by(|a, b| a.0.as_ref().cmp(b.0.as_ref()));

    let mut accounts: Vec<_> = accounts.into_iter().collect();
    if accounts.len() > 10 {
        accounts.select_nth_unstable_by(10, |a, b| {
            b.1.cmp(&a.1)
                .then_with(|| a.0.as_ref().cmp(b.0.as_ref()))
        });
        accounts.truncate(10);
    }
    accounts.sort_unstable_by(|a, b| {
        b.1.cmp(&a.1)
            .then_with(|| a.0.as_ref().cmp(b.0.as_ref()))
    });

    let stdout = io::stdout();
    let mut out = io::BufWriter::with_capacity(64 * 1024, stdout.lock());

    writeln!(out, "counted {}", counted).unwrap();
    writeln!(out, "net {}", net).unwrap();

    for (name, (count, total)) in channels {
        writeln!(
            out,
            "channel {} {} {}",
            std::str::from_utf8(name.as_ref()).unwrap(),
            count,
            total
        )
        .unwrap();
    }

    for (account, total) in accounts {
        writeln!(
            out,
            "account {} {}",
            std::str::from_utf8(account.as_ref()).unwrap(),
            total
        )
        .unwrap();
    }

    out.flush().unwrap();
}
