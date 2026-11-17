use std::borrow::Cow;
use std::cmp::Reverse;
use std::collections::{BinaryHeap, HashMap};
use std::hash::{BuildHasherDefault, Hasher};
use std::io::{self, Write};

#[derive(Default)]
struct FastHasher(u64);

impl FastHasher {
    #[inline]
    fn mix(&mut self, value: u64) {
        self.0 = (self.0.rotate_left(5) ^ value).wrapping_mul(0x517cc1b727220a95);
    }
}

impl Hasher for FastHasher {
    #[inline]
    fn finish(&self) -> u64 {
        self.0
    }

    #[inline]
    fn write(&mut self, mut bytes: &[u8]) {
        while bytes.len() >= 8 {
            self.mix(u64::from_ne_bytes(bytes[..8].try_into().unwrap()));
            bytes = &bytes[8..];
        }
        if bytes.len() >= 4 {
            self.mix(u32::from_ne_bytes(bytes[..4].try_into().unwrap()) as u64);
            bytes = &bytes[4..];
        }
        if bytes.len() >= 2 {
            self.mix(u16::from_ne_bytes(bytes[..2].try_into().unwrap()) as u64);
            bytes = &bytes[2..];
        }
        if !bytes.is_empty() {
            self.mix(bytes[0] as u64);
        }
    }

    #[inline]
    fn write_u8(&mut self, value: u8) {
        self.mix(value as u64);
    }
}

type Map<V> = HashMap<String, V, BuildHasherDefault<FastHasher>>;

#[inline]
fn find_string_special(bytes: &[u8], mut i: usize) -> usize {
    const LOW: u64 = 0x0101010101010101;
    const HIGH: u64 = 0x8080808080808080;

    while i + 8 <= bytes.len() {
        let word = u64::from_le_bytes(bytes[i..i + 8].try_into().unwrap());
        let quotes = word ^ 0x2222222222222222;
        let slashes = word ^ 0x5c5c5c5c5c5c5c5c;
        let hits = ((quotes.wrapping_sub(LOW) & !quotes)
            | (slashes.wrapping_sub(LOW) & !slashes))
            & HIGH;

        if hits != 0 {
            return i + (hits.trailing_zeros() as usize / 8);
        }
        i += 8;
    }

    while bytes[i] != b'"' && bytes[i] != b'\\' {
        i += 1;
    }
    i
}

struct Parser<'a> {
    bytes: &'a [u8],
    pos: usize,
}

struct Transaction<'a> {
    account: Cow<'a, str>,
    currency: Cow<'a, str>,
    channel: Cow<'a, str>,
    hundredths: u64,
    kind: i8,
}

impl<'a> Parser<'a> {
    #[inline]
    fn whitespace(&mut self) {
        while self.pos < self.bytes.len() && self.bytes[self.pos] <= b' ' {
            self.pos += 1;
        }
    }

    #[inline]
    fn string_span(&mut self) -> (usize, usize, bool) {
        let start = self.pos + 1;
        let mut i = start;
        let mut escaped = false;

        loop {
            i = find_string_special(self.bytes, i);
            if self.bytes[i] == b'"' {
                self.pos = i + 1;
                return (start, i, escaped);
            }
            escaped = true;
            i += 2;
        }
    }

    #[inline]
    fn string(&mut self) -> Cow<'a, str> {
        let opening = self.pos;
        let (start, end, escaped) = self.string_span();

        if escaped {
            Cow::Owned(
                serde_json::from_slice::<String>(&self.bytes[opening..self.pos]).unwrap(),
            )
        } else {
            // The input is valid UTF-8 JSON, and this span contains no escapes.
            Cow::Borrowed(unsafe {
                std::str::from_utf8_unchecked(&self.bytes[start..end])
            })
        }
    }

    #[inline]
    fn next_key(&mut self) -> Option<Cow<'a, str>> {
        self.whitespace();
        if self.bytes[self.pos] == b',' {
            self.pos += 1;
            self.whitespace();
        }
        if self.bytes[self.pos] == b'}' {
            self.pos += 1;
            return None;
        }

        let key = self.string();
        self.whitespace();
        self.pos += 1; // Colon.
        self.whitespace();
        Some(key)
    }

    fn skip_container_tail(&mut self) {
        let mut depth = 1usize;
        loop {
            match self.bytes[self.pos] {
                b'"' => {
                    self.string_span();
                }
                b'{' | b'[' => {
                    depth += 1;
                    self.pos += 1;
                }
                b'}' | b']' => {
                    self.pos += 1;
                    depth -= 1;
                    if depth == 0 {
                        return;
                    }
                }
                _ => self.pos += 1,
            }
        }
    }

    #[inline]
    fn skip_value(&mut self) {
        self.whitespace();
        match self.bytes[self.pos] {
            b'"' => {
                self.string_span();
            }
            b'{' | b'[' => {
                self.pos += 1;
                self.skip_container_tail();
            }
            _ => {
                while self.pos < self.bytes.len() {
                    let b = self.bytes[self.pos];
                    if b <= b' ' || b == b',' || b == b']' || b == b'}' {
                        break;
                    }
                    self.pos += 1;
                }
            }
        }
    }

    fn rate(&mut self) -> i64 {
        let negative = self.bytes[self.pos] == b'-';
        if negative {
            self.pos += 1;
        }

        let mut value = 0u64;
        while self.pos < self.bytes.len() {
            let b = self.bytes[self.pos];
            if !b.is_ascii_digit() {
                break;
            }
            value = value
                .saturating_mul(10)
                .saturating_add((b - b'0') as u64);
            self.pos += 1;
        }

        if negative {
            if value >= (1u64 << 63) {
                i64::MIN
            } else {
                -(value as i64)
            }
        } else {
            value.min(i64::MAX as u64) as i64
        }
    }

    fn rates(&mut self) -> Map<i64> {
        let mut rates = Map::default();
        self.whitespace();
        self.pos += 1;

        while let Some(key) = self.next_key() {
            if key.as_ref() == "rates" {
                rates.clear();
                self.pos += 1;
                while let Some(currency) = self.next_key() {
                    let value = self.rate();
                    rates.insert(currency.into_owned(), value);
                }
            } else {
                self.skip_value();
            }
        }
        rates
    }

    #[inline]
    fn tags_contain_test(&mut self) -> bool {
        self.pos += 1;
        self.whitespace();
        if self.bytes[self.pos] == b']' {
            self.pos += 1;
            return false;
        }

        loop {
            if self.string().as_ref() == "test" {
                self.skip_container_tail();
                return true;
            }

            self.whitespace();
            if self.bytes[self.pos] == b']' {
                self.pos += 1;
                return false;
            }
            self.pos += 1;
            self.whitespace();
        }
    }

    #[inline]
    fn channel(&mut self) -> Cow<'a, str> {
        self.pos += 1;
        let mut channel = Cow::Borrowed("");

        while let Some(key) = self.next_key() {
            if key.as_ref() == "channel" {
                channel = self.string();
            } else {
                self.skip_value();
            }
        }
        channel
    }

    #[inline]
    fn transaction(&mut self) -> Option<Transaction<'a>> {
        self.pos += 1;
        let mut transaction = Transaction {
            account: Cow::Borrowed(""),
            currency: Cow::Borrowed(""),
            channel: Cow::Borrowed(""),
            hundredths: 0,
            kind: 1,
        };
        let mut test = false;

        while let Some(key) = self.next_key() {
            match key.as_ref() {
                "account" => transaction.account = self.string(),
                "currency" => transaction.currency = self.string(),
                "amount" => transaction.hundredths = parse_amount(self.string().as_bytes()),
                "type" => {
                    transaction.kind = match self.string().as_ref() {
                        "void" => 0,
                        "debit" => -1,
                        _ => 1,
                    };
                }
                "tags" => test = self.tags_contain_test(),
                "meta" => transaction.channel = self.channel(),
                _ => self.skip_value(),
            }
        }

        if test || transaction.kind == 0 {
            None
        } else {
            Some(transaction)
        }
    }
}

#[inline]
fn parse_amount(bytes: &[u8]) -> u64 {
    let mut whole = 0u64;
    let mut i = 0;

    while i < bytes.len() && bytes[i] != b'.' {
        whole = whole
            .saturating_mul(10)
            .saturating_add((bytes[i] - b'0') as u64);
        i += 1;
    }

    let mut hundredths = whole.saturating_mul(100);
    if i < bytes.len() {
        i += 1;
        hundredths = hundredths.saturating_add((bytes[i] - b'0') as u64 * 10);
        if i + 1 < bytes.len() {
            hundredths = hundredths.saturating_add((bytes[i + 1] - b'0') as u64);
        }
    }
    hundredths
}

fn main() {
    let path = std::env::args_os().nth(1).unwrap();
    let input = std::fs::read(path).unwrap();
    let mut parser = Parser {
        bytes: &input,
        pos: 0,
    };

    let rates = parser.rates();
    let mut accounts: Map<i64> = Map::default();
    let mut channels: Map<(u64, i64)> = Map::default();
    let mut counted = 0u64;
    let mut net = 0i64;

    loop {
        parser.whitespace();
        if parser.pos == input.len() {
            break;
        }

        let Some(transaction) = parser.transaction() else {
            continue;
        };

        let rate = *rates.get(transaction.currency.as_ref()).unwrap();
        // The guaranteed signed-64-bit product is also its wrapping product.
        let product = (transaction.hundredths as i64).wrapping_mul(rate);
        let usd = product.div_euclid(1_000_000);
        let value = if transaction.kind < 0 { -usd } else { usd };

        counted += 1;
        net = net.wrapping_add(value);

        if let Some(total) = accounts.get_mut(transaction.account.as_ref()) {
            *total = total.wrapping_add(value);
        } else {
            accounts.insert(transaction.account.into_owned(), value);
        }

        if let Some((count, total)) = channels.get_mut(transaction.channel.as_ref()) {
            *count += 1;
            *total = total.wrapping_add(value);
        } else {
            channels.insert(transaction.channel.into_owned(), (1, value));
        }
    }

    let stdout = io::stdout();
    let mut output = io::BufWriter::with_capacity(65536, stdout.lock());

    writeln!(output, "counted {counted}").unwrap();
    writeln!(output, "net {net}").unwrap();

    let mut channel_rows: Vec<_> = channels.into_iter().collect();
    channel_rows.sort_unstable_by(|a, b| a.0.cmp(&b.0));
    for (name, (count, total)) in channel_rows {
        writeln!(output, "channel {name} {count} {total}").unwrap();
    }

    let mut best: BinaryHeap<(Reverse<i64>, String)> = BinaryHeap::with_capacity(10);
    for (account, total) in accounts {
        let candidate = (Reverse(total), account);
        if best.len() < 10 {
            best.push(candidate);
        } else if candidate < *best.peek().unwrap() {
            *best.peek_mut().unwrap() = candidate;
        }
    }

    for (Reverse(total), account) in best.into_sorted_vec() {
        writeln!(output, "account {account} {total}").unwrap();
    }
    output.flush().unwrap();
}
