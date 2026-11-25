use std::borrow::Cow;
use std::collections::HashMap;
use std::fs::File;
use std::hash::{BuildHasherDefault, Hasher};
use std::io::{BufRead, BufReader, Write};

#[derive(Default)]
struct Fx(u64);
impl Fx {
    #[inline]
    fn add(&mut self, v: u64) {
        self.0 = (self.0.rotate_left(5) ^ v).wrapping_mul(0x517cc1b727220a95);
    }
}
impl Hasher for Fx {
    #[inline]
    fn write(&mut self, b: &[u8]) {
        let mut c = b.chunks_exact(8);
        for x in &mut c {
            self.add(u64::from_le_bytes(x.try_into().unwrap()));
        }
        let r = c.remainder();
        if !r.is_empty() {
            let mut buf = [0u8; 8];
            buf[..r.len()].copy_from_slice(r);
            self.add(u64::from_le_bytes(buf));
        }
    }
    #[inline]
    fn finish(&self) -> u64 {
        (self.0 ^ (self.0 >> 29)).wrapping_mul(0x9E3779B97F4A7C15)
    }
}
type FxMap<K, V> = HashMap<K, V, BuildHasherDefault<Fx>>;

#[inline]
fn str_end(b: &[u8], mut i: usize) -> (usize, bool) {
    let mut esc = false;
    loop {
        match b[i] {
            b'"' => return (i, esc),
            b'\\' => {
                esc = true;
                i += 2;
            }
            _ => i += 1,
        }
    }
}

fn hex4(s: &[u8]) -> u32 {
    let mut v = 0u32;
    for &c in &s[..4] {
        let d = match c {
            b'0'..=b'9' => c - b'0',
            b'a'..=b'f' => c - b'a' + 10,
            b'A'..=b'F' => c - b'A' + 10,
            _ => 0,
        };
        v = v * 16 + d as u32;
    }
    v
}

fn unescape(s: &[u8]) -> Vec<u8> {
    let mut o = Vec::with_capacity(s.len());
    let mut i = 0;
    while i < s.len() {
        let c = s[i];
        if c != b'\\' {
            o.push(c);
            i += 1;
            continue;
        }
        i += 1;
        match s[i] {
            b'n' => o.push(b'\n'),
            b't' => o.push(b'\t'),
            b'r' => o.push(b'\r'),
            b'b' => o.push(8),
            b'f' => o.push(12),
            b'u' => {
                let mut cp = hex4(&s[i + 1..]);
                i += 4;
                if (0xD800..0xDC00).contains(&cp)
                    && i + 7 <= s.len()
                    && s[i + 1] == b'\\'
                    && s[i + 2] == b'u'
                {
                    let lo = hex4(&s[i + 3..]);
                    if (0xDC00..0xE000).contains(&lo) {
                        cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
                        i += 6;
                    }
                }
                let ch = char::from_u32(cp).unwrap_or('\u{FFFD}');
                let mut tmp = [0u8; 4];
                o.extend_from_slice(ch.encode_utf8(&mut tmp).as_bytes());
            }
            other => o.push(other),
        }
        i += 1;
    }
    o
}

struct P<'a> {
    b: &'a [u8],
    i: usize,
}

impl<'a> P<'a> {
    #[inline]
    fn ws(&mut self) {
        while self.i < self.b.len() && matches!(self.b[self.i], b' ' | b'\n' | b'\r' | b'\t') {
            self.i += 1;
        }
    }
    #[inline]
    fn string(&mut self) -> Cow<'a, [u8]> {
        let b = self.b;
        let s = self.i + 1;
        let (e, esc) = str_end(b, s);
        self.i = e + 1;
        if esc {
            Cow::Owned(unescape(&b[s..e]))
        } else {
            Cow::Borrowed(&b[s..e])
        }
    }
    /// After '{' consumed. Returns next key with the cursor at the value, or None at '}'.
    #[inline]
    fn next_key(&mut self) -> Option<Cow<'a, [u8]>> {
        loop {
            self.ws();
            if self.i >= self.b.len() {
                return None;
            }
            match self.b[self.i] {
                b'}' => {
                    self.i += 1;
                    return None;
                }
                b',' => {
                    self.i += 1;
                }
                _ => break,
            }
        }
        let k = self.string();
        self.ws();
        self.i += 1; // colon
        self.ws();
        Some(k)
    }
    /// After '[' consumed. True if an element follows (cursor at it).
    #[inline]
    fn next_elem(&mut self) -> bool {
        loop {
            self.ws();
            if self.i >= self.b.len() {
                return false;
            }
            match self.b[self.i] {
                b']' => {
                    self.i += 1;
                    return false;
                }
                b',' => {
                    self.i += 1;
                }
                _ => return true,
            }
        }
    }
    fn skip_value(&mut self) {
        let b = self.b;
        let mut i = self.i;
        match b[i] {
            b'"' => {
                i = str_end(b, i + 1).0 + 1;
            }
            b'{' | b'[' => {
                let mut depth = 0i32;
                loop {
                    match b[i] {
                        b'"' => {
                            i = str_end(b, i + 1).0 + 1;
                            continue;
                        }
                        b'{' | b'[' => depth += 1,
                        b'}' | b']' => {
                            depth -= 1;
                            if depth == 0 {
                                i += 1;
                                break;
                            }
                        }
                        _ => {}
                    }
                    i += 1;
                }
            }
            _ => {
                while i < b.len()
                    && !matches!(b[i], b',' | b'}' | b']' | b' ' | b'\n' | b'\r' | b'\t')
                {
                    i += 1;
                }
            }
        }
        self.i = i;
    }
}

fn parse_amount(s: &[u8]) -> i64 {
    let mut int: i64 = 0;
    let mut i = 0;
    while i < s.len() && s[i] != b'.' {
        int = int * 10 + (s[i] - b'0') as i64;
        i += 1;
    }
    let mut frac: i64 = 0;
    if i < s.len() {
        i += 1;
        let rest = &s[i..];
        if rest.len() >= 2 {
            frac = (rest[0] - b'0') as i64 * 10 + (rest[1] - b'0') as i64;
        } else if rest.len() == 1 {
            frac = (rest[0] - b'0') as i64 * 10;
        }
    }
    int * 100 + frac
}

fn parse_rates(line: &[u8]) -> Vec<(Vec<u8>, i64)> {
    let mut p = P { b: line, i: 0 };
    p.ws();
    p.i += 1; // '{'
    let mut rates = Vec::new();
    while let Some(k) = p.next_key() {
        if &*k == b"rates" {
            p.i += 1; // '{'
            while let Some(name) = p.next_key() {
                let mut v: i64 = 0;
                while p.i < line.len() && line[p.i].is_ascii_digit() {
                    v = v * 10 + (line[p.i] - b'0') as i64;
                    p.i += 1;
                }
                // skip any remaining number characters
                p.skip_value();
                rates.push((name.into_owned(), v));
            }
        } else {
            p.skip_value();
        }
    }
    rates
}

fn main() {
    let path = std::env::args().nth(1).expect("input path");
    let f = File::open(path).expect("open");
    let mut rd = BufReader::with_capacity(1 << 20, f);
    let mut line: Vec<u8> = Vec::with_capacity(4096);

    rd.read_until(b'\n', &mut line).unwrap();
    let rates = parse_rates(&line);

    let mut count: u64 = 0;
    let mut net: i64 = 0;
    let mut channels: FxMap<Vec<u8>, (u64, i64)> = FxMap::default();
    let mut accounts: FxMap<Vec<u8>, i64> = FxMap::default();

    loop {
        line.clear();
        let n = rd.read_until(b'\n', &mut line).unwrap();
        if n == 0 {
            break;
        }
        let b: &[u8] = &line;
        let mut p = P { b, i: 0 };
        p.ws();
        if p.i >= b.len() || b[p.i] != b'{' {
            continue;
        }
        p.i += 1;

        let mut account: Option<Cow<[u8]>> = None;
        let mut ty: u8 = 255;
        let mut hundredths: i64 = 0;
        let mut rate: i64 = 0;
        let mut test = false;
        let mut channel: Option<Cow<[u8]>> = None;

        while let Some(k) = p.next_key() {
            match &*k {
                b"account" => account = Some(p.string()),
                b"type" => {
                    let t = p.string();
                    ty = match &*t {
                        b"credit" => 0,
                        b"debit" => 1,
                        b"refund" => 2,
                        b"void" => 3,
                        _ => 255,
                    };
                }
                b"amount" => {
                    let a = p.string();
                    hundredths = parse_amount(&a);
                }
                b"currency" => {
                    let c = p.string();
                    for (name, r) in rates.iter() {
                        if name.as_slice() == &*c {
                            rate = *r;
                            break;
                        }
                    }
                }
                b"tags" => {
                    if b[p.i] == b'[' {
                        p.i += 1;
                        while p.next_elem() {
                            if b[p.i] == b'"' {
                                let s = p.string();
                                if &*s == b"test" {
                                    test = true;
                                }
                            } else {
                                p.skip_value();
                            }
                        }
                    } else {
                        p.skip_value();
                    }
                }
                b"meta" => {
                    if b[p.i] == b'{' {
                        p.i += 1;
                        while let Some(mk) = p.next_key() {
                            if &*mk == b"channel" && b[p.i] == b'"' {
                                channel = Some(p.string());
                            } else {
                                p.skip_value();
                            }
                        }
                    } else {
                        p.skip_value();
                    }
                }
                _ => p.skip_value(),
            }
        }

        if ty == 3 || ty == 255 || test {
            continue;
        }
        let usd = (hundredths * rate) / 1_000_000;
        let signed = if ty == 1 { -usd } else { usd };
        count += 1;
        net += signed;

        if let Some(ch) = channel {
            if let Some(e) = channels.get_mut(&*ch) {
                e.0 += 1;
                e.1 += signed;
            } else {
                channels.insert(ch.into_owned(), (1, signed));
            }
        }
        if let Some(ac) = account {
            if let Some(e) = accounts.get_mut(&*ac) {
                *e += signed;
            } else {
                accounts.insert(ac.into_owned(), signed);
            }
        }
    }

    let mut out: Vec<u8> = Vec::new();
    writeln!(out, "counted {}", count).unwrap();
    writeln!(out, "net {}", net).unwrap();
    let mut chs: Vec<(&Vec<u8>, &(u64, i64))> = channels.iter().collect();
    chs.sort_by(|a, b| a.0.cmp(b.0));
    for (name, (c, s)) in chs {
        out.extend_from_slice(b"channel ");
        out.extend_from_slice(name);
        writeln!(out, " {} {}", c, s).unwrap();
    }
    let mut accs: Vec<(&Vec<u8>, &i64)> = accounts.iter().collect();
    accs.sort_by(|a, b| b.1.cmp(a.1).then_with(|| a.0.cmp(b.0)));
    for (id, s) in accs.into_iter().take(10) {
        out.extend_from_slice(b"account ");
        out.extend_from_slice(id);
        writeln!(out, " {}", s).unwrap();
    }
    std::io::stdout().write_all(&out).unwrap();
}
