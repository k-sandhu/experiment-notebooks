use serde::Deserialize;
use std::borrow::Cow;
use std::collections::HashMap;
use std::fs::File;
use std::hash::{BuildHasherDefault, Hasher};
use std::io::{self, Read, Write};

const CHUNK: usize = 1 << 22;
const SEED: u64 = 0x51_7c_c1_b7_27_22_0a_95;

// Small, fast non-cryptographic hasher (the std SipHash is slow for short keys).
#[derive(Default)]
struct FxHasher(u64);

impl Hasher for FxHasher {
    #[inline]
    fn write(&mut self, bytes: &[u8]) {
        let mut h = self.0;
        let mut chunks = bytes.chunks_exact(8);
        for c in &mut chunks {
            let v = u64::from_le_bytes(c.try_into().unwrap());
            h = (h.rotate_left(5) ^ v).wrapping_mul(SEED);
        }
        let rem = chunks.remainder();
        if !rem.is_empty() {
            let mut buf = [0u8; 8];
            buf[..rem.len()].copy_from_slice(rem);
            h = (h.rotate_left(5) ^ u64::from_le_bytes(buf)).wrapping_mul(SEED);
        }
        self.0 = h;
    }

    #[inline]
    fn write_usize(&mut self, i: usize) {
        self.0 = (self.0.rotate_left(5) ^ i as u64).wrapping_mul(SEED);
    }

    #[inline]
    fn finish(&self) -> u64 {
        self.0.rotate_left(26)
    }
}

type FxMap<K, V> = HashMap<K, V, BuildHasherDefault<FxHasher>>;

#[derive(Deserialize)]
struct RatesLine {
    rates: HashMap<String, i64>,
}

#[derive(Default)]
struct Totals {
    count: i64,
    net: i64,
    channels: FxMap<Vec<u8>, (i64, i64)>,
    accounts: FxMap<Vec<u8>, i64>,
}

// Decodes the body of a JSON string (the bytes between the quotes) that contains escapes.
fn unescape(raw: &[u8]) -> Option<Vec<u8>> {
    let mut out = Vec::with_capacity(raw.len());
    let mut i = 0;
    while i < raw.len() {
        let c = raw[i];
        if c != b'\\' {
            out.push(c);
            i += 1;
            continue;
        }
        let e = *raw.get(i + 1)?;
        i += 2;
        match e {
            b'"' | b'\\' | b'/' => out.push(e),
            b'b' => out.push(8),
            b'f' => out.push(12),
            b'n' => out.push(b'\n'),
            b'r' => out.push(b'\r'),
            b't' => out.push(b'\t'),
            b'u' => {
                let mut cp = hex4(raw.get(i..i + 4)?)?;
                i += 4;
                if (0xD800..0xDC00).contains(&cp)
                    && raw.get(i) == Some(&b'\\')
                    && raw.get(i + 1) == Some(&b'u')
                {
                    let lo = hex4(raw.get(i + 2..i + 6)?)?;
                    if (0xDC00..0xE000).contains(&lo) {
                        cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
                        i += 6;
                    }
                }
                let ch = char::from_u32(cp).unwrap_or('\u{FFFD}');
                let mut utf8 = [0u8; 4];
                out.extend_from_slice(ch.encode_utf8(&mut utf8).as_bytes());
            }
            _ => return None,
        }
    }
    Some(out)
}

fn hex4(h: &[u8]) -> Option<u32> {
    let mut v = 0;
    for &c in h {
        v = v * 16 + (c as char).to_digit(16)?;
    }
    Some(v)
}

// Scans JSON tokens from one line. Only the parts the spec needs are kept; everything else is skipped.
struct Parser<'a> {
    s: &'a [u8],
    p: usize,
}

impl<'a> Parser<'a> {
    #[inline]
    fn ws(&mut self) {
        while self.p < self.s.len() && matches!(self.s[self.p], b' ' | b'\t' | b'\n' | b'\r') {
            self.p += 1;
        }
    }

    #[inline]
    fn peek(&self) -> u8 {
        self.s.get(self.p).copied().unwrap_or(0)
    }

    #[inline]
    fn expect(&mut self, c: u8) -> Option<()> {
        self.ws();
        if self.peek() == c {
            self.p += 1;
            Some(())
        } else {
            None
        }
    }

    // Reads a string token. Borrows from the line unless the string has escapes.
    fn string(&mut self) -> Option<Cow<'a, [u8]>> {
        self.ws();
        if self.peek() != b'"' {
            return None;
        }
        let start = self.p + 1;
        let mut i = start;
        let mut escaped = false;
        loop {
            match *self.s.get(i)? {
                b'"' => break,
                b'\\' => {
                    escaped = true;
                    i += 2;
                }
                _ => i += 1,
            }
        }
        self.p = i + 1;
        let raw = &self.s[start..i];
        if escaped {
            Some(Cow::Owned(unescape(raw)?))
        } else {
            Some(Cow::Borrowed(raw))
        }
    }

    fn skip_value(&mut self) -> Option<()> {
        self.ws();
        match self.peek() {
            b'"' => {
                self.string()?;
            }
            b'{' | b'[' => {
                let mut depth = 0usize;
                loop {
                    match *self.s.get(self.p)? {
                        b'"' => {
                            self.string()?;
                            continue;
                        }
                        b'{' | b'[' => depth += 1,
                        b'}' | b']' => depth -= 1,
                        _ => {}
                    }
                    self.p += 1;
                    if depth == 0 {
                        break;
                    }
                }
            }
            _ => {
                while self.p < self.s.len()
                    && !matches!(self.s[self.p], b',' | b'}' | b']' | b' ' | b'\t' | b'\n' | b'\r')
                {
                    self.p += 1;
                }
            }
        }
        Some(())
    }
}

#[derive(Default)]
struct Txn<'a> {
    account: Cow<'a, [u8]>,
    kind: Cow<'a, [u8]>,
    amount: Cow<'a, [u8]>,
    currency: Cow<'a, [u8]>,
    channel: Cow<'a, [u8]>,
    test: bool,
}

// Parses the top-level members of one transaction object.
// Nested keys (such as an "account" inside "extra") are never looked at.
fn parse_txn(line: &[u8]) -> Option<Txn<'_>> {
    let mut ps = Parser { s: line, p: 0 };
    let mut t = Txn::default();
    ps.expect(b'{')?;
    loop {
        ps.ws();
        if ps.peek() == b'}' {
            break;
        }
        let key = ps.string()?;
        ps.expect(b':')?;
        match &key[..] {
            b"account" => t.account = ps.string()?,
            b"type" => t.kind = ps.string()?,
            b"amount" => t.amount = ps.string()?,
            b"currency" => t.currency = ps.string()?,
            b"tags" => {
                ps.expect(b'[')?;
                loop {
                    ps.ws();
                    if ps.peek() == b']' {
                        ps.p += 1;
                        break;
                    }
                    if ps.peek() == b'"' {
                        let tag = ps.string()?;
                        if &tag[..] == b"test" {
                            t.test = true;
                        }
                    } else {
                        ps.skip_value()?;
                    }
                    ps.ws();
                    if ps.peek() == b',' {
                        ps.p += 1;
                    }
                }
            }
            b"meta" => {
                ps.expect(b'{')?;
                loop {
                    ps.ws();
                    if ps.peek() == b'}' {
                        ps.p += 1;
                        break;
                    }
                    let mk = ps.string()?;
                    ps.expect(b':')?;
                    if &mk[..] == b"channel" {
                        t.channel = ps.string()?;
                    } else {
                        ps.skip_value()?;
                    }
                    ps.ws();
                    if ps.peek() == b',' {
                        ps.p += 1;
                    }
                }
            }
            _ => ps.skip_value()?,
        }
        ps.ws();
        if ps.peek() == b',' {
            ps.p += 1;
        }
    }
    Some(t)
}

// Parses "12", "12.5" or "12.05" into hundredths using exact integer arithmetic.
#[inline]
fn hundredths(s: &[u8]) -> Option<i64> {
    const SCALE: [i64; 3] = [100, 10, 1];
    let mut n: i64 = 0;
    let mut frac_digits = 0usize;
    let mut dot = false;
    for &c in s {
        match c {
            b'0'..=b'9' => {
                n = n * 10 + (c - b'0') as i64;
                if dot {
                    frac_digits += 1;
                }
            }
            b'.' => dot = true,
            _ => return None,
        }
    }
    Some(n * SCALE.get(frac_digits)?)
}

fn handle_line(line: &[u8], rates: &FxMap<Vec<u8>, i64>, totals: &mut Totals) -> Option<()> {
    let t = parse_txn(line)?;
    if &t.kind[..] == b"void" || t.test {
        return Some(());
    }
    let sign = match &t.kind[..] {
        b"credit" | b"refund" => 1,
        b"debit" => -1,
        _ => return Some(()),
    };
    let rate = *rates.get(&t.currency[..])?;
    let usd = hundredths(&t.amount)? * rate / 1_000_000;
    let value = sign * usd;

    totals.count += 1;
    totals.net += value;
    match totals.channels.get_mut(&t.channel[..]) {
        Some(e) => {
            e.0 += 1;
            e.1 += value;
        }
        None => {
            totals.channels.insert(t.channel.to_vec(), (1, value));
        }
    }
    match totals.accounts.get_mut(&t.account[..]) {
        Some(s) => *s += value,
        None => {
            totals.accounts.insert(t.account.to_vec(), value);
        }
    }
    Some(())
}

fn main() -> io::Result<()> {
    let path = std::env::args_os().nth(1).expect("usage: solution INPUT_PATH");
    let mut file = File::open(path)?;

    let mut rates: FxMap<Vec<u8>, i64> = FxMap::default();
    let mut totals = Totals::default();
    let mut buf: Vec<u8> = Vec::with_capacity(CHUNK * 2);
    let mut first = true;
    let mut eof = false;

    while !eof {
        let old_len = buf.len();
        buf.resize(old_len + CHUNK, 0);
        let n = file.read(&mut buf[old_len..])?;
        buf.truncate(old_len + n);
        eof = n == 0;

        // Only whole lines are processed; the partial last line waits for the next read.
        let end = if eof {
            buf.len()
        } else {
            buf.iter().rposition(|&b| b == b'\n').map_or(0, |p| p + 1)
        };

        for line in buf[..end].split(|&b| b == b'\n') {
            if line.is_empty() {
                continue;
            }
            if first {
                first = false;
                let r: RatesLine = serde_json::from_slice(line).map_err(io::Error::other)?;
                for (k, v) in r.rates {
                    rates.insert(k.into_bytes(), v);
                }
                continue;
            }
            handle_line(line, &rates, &mut totals);
        }
        buf.drain(..end);
    }

    let stdout = io::stdout();
    let mut out = io::BufWriter::new(stdout.lock());
    writeln!(out, "counted {}", totals.count)?;
    writeln!(out, "net {}", totals.net)?;

    let mut channels: Vec<(&[u8], (i64, i64))> =
        totals.channels.iter().map(|(k, v)| (&k[..], *v)).collect();
    channels.sort_unstable_by(|a, b| a.0.cmp(b.0));
    for (name, (count, sum)) in channels {
        out.write_all(b"channel ")?;
        out.write_all(name)?;
        writeln!(out, " {count} {sum}")?;
    }

    let mut accounts: Vec<(&[u8], i64)> =
        totals.accounts.iter().map(|(k, v)| (&k[..], *v)).collect();
    let by_sum_then_id = |a: &(&[u8], i64), b: &(&[u8], i64)| b.1.cmp(&a.1).then_with(|| a.0.cmp(b.0));
    if accounts.len() > 10 {
        accounts.select_nth_unstable_by(9, by_sum_then_id);
        accounts.truncate(10);
    }
    accounts.sort_unstable_by(by_sum_then_id);
    for (id, sum) in accounts {
        out.write_all(b"account ")?;
        out.write_all(id)?;
        writeln!(out, " {sum}")?;
    }
    out.flush()
}
