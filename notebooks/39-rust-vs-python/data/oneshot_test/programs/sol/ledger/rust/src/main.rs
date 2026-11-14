use std::borrow::Cow;
use std::collections::HashMap;
use std::fs::File;
use std::hash::{BuildHasherDefault, Hasher};
use std::io::{self, BufRead, BufReader, BufWriter, Write};

#[derive(Default)]
struct FastHasher(u64);

impl FastHasher {
    #[inline(always)]
    fn add(&mut self, value: u64) {
        self.0 = (self.0.rotate_left(5) ^ value).wrapping_mul(0x517cc1b727220a95);
    }
}

impl Hasher for FastHasher {
    #[inline(always)]
    fn finish(&self) -> u64 {
        self.0
    }

    #[inline]
    fn write(&mut self, mut bytes: &[u8]) {
        while bytes.len() >= 8 {
            self.add(u64::from_le_bytes(bytes[..8].try_into().unwrap()));
            bytes = &bytes[8..];
        }
        if bytes.len() >= 4 {
            self.add(u32::from_le_bytes(bytes[..4].try_into().unwrap()) as u64);
            bytes = &bytes[4..];
        }
        if bytes.len() >= 2 {
            self.add(u16::from_le_bytes(bytes[..2].try_into().unwrap()) as u64);
            bytes = &bytes[2..];
        }
        if !bytes.is_empty() {
            self.add(bytes[0] as u64);
        }
    }

    #[inline(always)]
    fn write_u8(&mut self, value: u8) {
        self.add(value as u64);
    }
}

type FastMap<V> = HashMap<Box<str>, V, BuildHasherDefault<FastHasher>>;

#[inline]
fn string_end(data: &[u8], mut pos: usize) -> (usize, bool) {
    const ONES: u64 = 0x0101010101010101;
    const HIGHS: u64 = 0x8080808080808080;
    const QUOTES: u64 = 0x2222222222222222;
    const SLASHES: u64 = 0x5c5c5c5c5c5c5c5c;

    let mut escaped = false;

    loop {
        if pos + 8 <= data.len() {
            let word = unsafe {
                u64::from_le(std::ptr::read_unaligned(
                    data.as_ptr().add(pos) as *const u64
                ))
            };
            let quotes = word ^ QUOTES;
            let slashes = word ^ SLASHES;
            let hits = ((quotes.wrapping_sub(ONES) & !quotes)
                | (slashes.wrapping_sub(ONES) & !slashes))
                & HIGHS;

            if hits == 0 {
                pos += 8;
                continue;
            }
            pos += (hits.trailing_zeros() / 8) as usize;
        }

        match data[pos] {
            b'"' => return (pos, escaped),
            b'\\' => {
                escaped = true;
                pos += 2;
            }
            _ => pos += 1,
        }
    }
}

struct Parser<'a> {
    data: &'a [u8],
    pos: usize,
}

impl<'a> Parser<'a> {
    #[inline]
    fn new(data: &'a [u8]) -> Self {
        Self { data, pos: 0 }
    }

    #[inline(always)]
    fn whitespace(&mut self) {
        while self.pos < self.data.len() && self.data[self.pos] <= b' ' {
            self.pos += 1;
        }
    }

    #[inline]
    fn string(&mut self) -> Cow<'a, str> {
        let start = self.pos;
        let (end, escaped) = string_end(self.data, start + 1);
        self.pos = end + 1;

        if escaped {
            Cow::Owned(serde_json::from_slice::<String>(&self.data[start..self.pos]).unwrap())
        } else {
            Cow::Borrowed(unsafe {
                std::str::from_utf8_unchecked(&self.data[start + 1..end])
            })
        }
    }

    #[inline]
    fn skip_string(&mut self) {
        self.pos = string_end(self.data, self.pos + 1).0 + 1;
    }

    #[inline]
    fn begin_object(&mut self) {
        self.whitespace();
        self.pos += 1;
    }

    #[inline]
    fn next_key(&mut self) -> Option<Cow<'a, str>> {
        self.whitespace();
        if self.data[self.pos] == b',' {
            self.pos += 1;
            self.whitespace();
        }
        if self.data[self.pos] == b'}' {
            self.pos += 1;
            return None;
        }

        let key = self.string();
        self.whitespace();
        self.pos += 1;
        self.whitespace();
        Some(key)
    }

    #[inline]
    fn skip_value(&mut self) {
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
                while self.pos < self.data.len() {
                    match self.data[self.pos] {
                        b',' | b'}' | b']' | b' ' | b'\t' | b'\r' | b'\n' => break,
                        _ => self.pos += 1,
                    }
                }
            }
        }
    }

    fn rate(&mut self) -> i128 {
        let negative = self.data[self.pos] == b'-';
        if negative {
            self.pos += 1;
        }

        let mut magnitude = 0u64;
        while self.pos < self.data.len() {
            let digit = self.data[self.pos];
            if !digit.is_ascii_digit() {
                break;
            }
            magnitude = magnitude
                .saturating_mul(10)
                .saturating_add((digit - b'0') as u64);
            self.pos += 1;
        }

        if negative {
            -(magnitude as i128)
        } else {
            magnitude as i128
        }
    }

    #[inline]
    fn test_tag(&mut self) -> bool {
        self.pos += 1;
        self.whitespace();

        while self.data[self.pos] != b']' {
            if self.string().as_ref() == "test" {
                return true;
            }
            self.whitespace();
            if self.data[self.pos] == b',' {
                self.pos += 1;
                self.whitespace();
            }
        }

        self.pos += 1;
        false
    }

    #[inline]
    fn channel(&mut self) -> Cow<'a, str> {
        self.begin_object();
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
}

fn parse_rates(line: &[u8]) -> FastMap<i128> {
    let mut parser = Parser::new(line);
    let mut rates = FastMap::default();

    parser.begin_object();
    while let Some(key) = parser.next_key() {
        if key.as_ref() == "rates" {
            parser.begin_object();
            while let Some(currency) = parser.next_key() {
                let rate = parser.rate();
                rates.insert(currency.into_owned().into_boxed_str(), rate);
            }
        } else {
            parser.skip_value();
        }
    }
    rates
}

#[inline]
fn hundredths(amount: &str) -> u64 {
    let mut value = 0u64;
    let mut fractional = false;
    let mut decimal_places = 0u8;

    for byte in amount.bytes() {
        if byte == b'.' {
            fractional = true;
        } else {
            value = value * 10 + (byte - b'0') as u64;
            if fractional {
                decimal_places += 1;
            }
        }
    }

    match decimal_places {
        0 => value * 100,
        1 => value * 10,
        _ => value,
    }
}

struct Transaction<'a> {
    account: Cow<'a, str>,
    channel: Cow<'a, str>,
    value: i64,
}

#[inline]
fn parse_transaction<'a>(
    line: &'a [u8],
    rates: &FastMap<i128>,
) -> Option<Transaction<'a>> {
    let mut parser = Parser::new(line);
    let mut account = Cow::Borrowed("");
    let mut channel = Cow::Borrowed("");
    let mut currency = Cow::Borrowed("");
    let mut amount = Cow::Borrowed("");
    let mut debit = false;

    parser.begin_object();
    while let Some(key) = parser.next_key() {
        match key.as_ref() {
            "account" => account = parser.string(),
            "currency" => currency = parser.string(),
            "amount" => amount = parser.string(),
            "type" => {
                let kind = parser.string();
                match kind.as_ref() {
                    "void" => return None,
                    "debit" => debit = true,
                    _ => debit = false,
                }
            }
            "tags" => {
                if parser.test_tag() {
                    return None;
                }
            }
            "meta" => channel = parser.channel(),
            _ => parser.skip_value(),
        }
    }

    let rate = *rates.get(currency.as_ref()).unwrap();
    let usd = if rate == 0 {
        0
    } else {
        let product = (hundredths(amount.as_ref()) as i128 * rate) as i64;
        product.div_euclid(1_000_000)
    };

    Some(Transaction {
        account,
        channel,
        value: if debit { -usd } else { usd },
    })
}

#[derive(Default)]
struct ChannelTotal {
    count: u64,
    net: i128,
}

#[inline]
fn account_order(a: &(&str, i128), b: &(&str, i128)) -> std::cmp::Ordering {
    b.1.cmp(&a.1).then_with(|| a.0.cmp(b.0))
}

fn main() {
    let path = std::env::args_os().nth(1).expect("missing input path");
    let file = File::open(path).unwrap();
    let mut reader = BufReader::with_capacity(1 << 20, file);
    let mut line = Vec::with_capacity(1024);

    reader.read_until(b'\n', &mut line).unwrap();
    let rates = parse_rates(&line);

    let mut accounts: FastMap<i128> = FastMap::default();
    let mut channels: FastMap<ChannelTotal> = FastMap::default();
    let mut counted = 0u64;
    let mut net = 0i128;

    loop {
        line.clear();
        if reader.read_until(b'\n', &mut line).unwrap() == 0 {
            break;
        }

        if let Some(transaction) = parse_transaction(&line, &rates) {
            let value = transaction.value as i128;
            counted += 1;
            net += value;

            if let Some(total) = accounts.get_mut(transaction.account.as_ref()) {
                *total += value;
            } else {
                accounts.insert(transaction.account.into_owned().into_boxed_str(), value);
            }

            if let Some(total) = channels.get_mut(transaction.channel.as_ref()) {
                total.count += 1;
                total.net += value;
            } else {
                channels.insert(
                    transaction.channel.into_owned().into_boxed_str(),
                    ChannelTotal {
                        count: 1,
                        net: value,
                    },
                );
            }
        }
    }

    let stdout = io::stdout();
    let mut output = BufWriter::new(stdout.lock());

    writeln!(output, "counted {counted}").unwrap();
    writeln!(output, "net {net}").unwrap();

    let mut sorted_channels: Vec<_> = channels.iter().collect();
    sorted_channels.sort_unstable_by(|a, b| a.0.cmp(b.0));
    for (name, total) in sorted_channels {
        writeln!(
            output,
            "channel {} {} {}",
            name, total.count, total.net
        )
        .unwrap();
    }

    let mut top: Vec<(&str, i128)> = Vec::with_capacity(10);
    for (account, &total) in &accounts {
        let candidate = (account.as_ref(), total);
        if top.len() < 10 {
            top.push(candidate);
            top.sort_unstable_by(account_order);
        } else if account_order(&candidate, &top[9]).is_lt() {
            top[9] = candidate;
            top.sort_unstable_by(account_order);
        }
    }

    for (account, total) in top {
        writeln!(output, "account {account} {total}").unwrap();
    }

    output.flush().unwrap();
}
