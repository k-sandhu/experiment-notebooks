use std::borrow::Cow;
use std::collections::HashMap;
use std::hash::{BuildHasherDefault, Hasher};
use std::io::{Read, Write};

#[derive(Default)]
struct Fx(u64);

const K: u64 = 0x517c_c1b7_2722_0a95;

impl Hasher for Fx {
    #[inline]
    fn write(&mut self, bytes: &[u8]) {
        let mut h = self.0;
        let mut chunks = bytes.chunks_exact(8);
        for c in &mut chunks {
            let v = u64::from_le_bytes(c.try_into().unwrap());
            h = (h.rotate_left(5) ^ v).wrapping_mul(K);
        }
        let rem = chunks.remainder();
        if !rem.is_empty() {
            let mut buf = [0u8; 8];
            buf[..rem.len()].copy_from_slice(rem);
            h = (h.rotate_left(5) ^ u64::from_le_bytes(buf)).wrapping_mul(K);
        }
        self.0 = h;
    }
    #[inline]
    fn write_u8(&mut self, i: u8) {
        self.0 = (self.0.rotate_left(5) ^ i as u64).wrapping_mul(K);
    }
    #[inline]
    fn write_usize(&mut self, i: usize) {
        self.0 = (self.0.rotate_left(5) ^ i as u64).wrapping_mul(K);
    }
    #[inline]
    fn finish(&self) -> u64 {
        self.0 ^ (self.0 >> 29)
    }
}

type FxMap<V> = HashMap<Vec<u8>, V, BuildHasherDefault<Fx>>;

struct P<'a> {
    b: &'a [u8],
    i: usize,
}

fn push_utf8(out: &mut Vec<u8>, c: u32) {
    let ch = char::from_u32(c).unwrap_or('\u{fffd}');
    let mut buf = [0u8; 4];
    out.extend_from_slice(ch.encode_utf8(&mut buf).as_bytes());
}

impl<'a> P<'a> {
    #[inline]
    fn ws(&mut self) {
        while self.i < self.b.len() && matches!(self.b[self.i], b' ' | b'\t' | b'\r' | b'\n') {
            self.i += 1;
        }
    }

    #[inline]
    fn peek(&self) -> u8 {
        if self.i < self.b.len() { self.b[self.i] } else { 0 }
    }

    // After the opening quote: returns index of closing quote and whether escapes exist.
    #[inline]
    fn scan_str(&mut self) -> (usize, bool) {
        let b = self.b;
        let mut j = self.i;
        let mut esc = false;
        loop {
            match b[j] {
                b'"' => break,
                b'\\' => {
                    esc = true;
                    j += 2;
                }
                _ => j += 1,
            }
        }
        (j, esc)
    }

    fn hex4(&self, at: usize) -> u32 {
        let mut v = 0u32;
        for k in 0..4 {
            let c = self.b[at + k];
            let d = match c {
                b'0'..=b'9' => c - b'0',
                b'a'..=b'f' => c - b'a' + 10,
                _ => c - b'A' + 10,
            };
            v = v * 16 + d as u32;
        }
        v
    }

    fn decode(&self, s: usize, e: usize) -> Vec<u8> {
        let mut out = Vec::with_capacity(e - s);
        let mut j = s;
        while j < e {
            let c = self.b[j];
            if c != b'\\' {
                out.push(c);
                j += 1;
                continue;
            }
            let n = self.b[j + 1];
            j += 2;
            match n {
                b'n' => out.push(b'\n'),
                b't' => out.push(b'\t'),
                b'r' => out.push(b'\r'),
                b'b' => out.push(8),
                b'f' => out.push(12),
                b'u' => {
                    let mut cp = self.hex4(j);
                    j += 4;
                    if (0xD800..0xDC00).contains(&cp)
                        && j + 6 <= e
                        && self.b[j] == b'\\'
                        && self.b[j + 1] == b'u'
                    {
                        let lo = self.hex4(j + 2);
                        if (0xDC00..0xE000).contains(&lo) {
                            cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
                            j += 6;
                        }
                    }
                    push_utf8(&mut out, cp);
                }
                other => out.push(other), // \" \\ \/
            }
        }
        out
    }

    // Expects current byte to be the opening quote.
    #[inline]
    fn read_str(&mut self) -> Cow<'a, [u8]> {
        self.i += 1;
        let s = self.i;
        let (e, esc) = self.scan_str();
        self.i = e + 1;
        if esc {
            Cow::Owned(self.decode(s, e))
        } else {
            Cow::Borrowed(&self.b[s..e])
        }
    }

    fn skip_value(&mut self) {
        self.ws();
        match self.peek() {
            b'"' => {
                self.i += 1;
                let (e, _) = self.scan_str();
                self.i = e + 1;
            }
            b'{' | b'[' => {
                let mut depth = 0usize;
                loop {
                    match self.b[self.i] {
                        b'"' => {
                            self.i += 1;
                            let (e, _) = self.scan_str();
                            self.i = e;
                        }
                        b'{' | b'[' => depth += 1,
                        b'}' | b']' => {
                            depth -= 1;
                            if depth == 0 {
                                self.i += 1;
                                break;
                            }
                        }
                        _ => {}
                    }
                    self.i += 1;
                }
            }
            _ => {
                while self.i < self.b.len()
                    && !matches!(self.b[self.i], b',' | b'}' | b']' | b' ' | b'\t' | b'\r' | b'\n')
                {
                    self.i += 1;
                }
            }
        }
    }

    // Returns the next object key (positioned at its value) or None at the closing '}'.
    #[inline]
    fn next_key(&mut self) -> Option<Cow<'a, [u8]>> {
        self.ws();
        if self.peek() == b',' {
            self.i += 1;
            self.ws();
        }
        if self.peek() == b'}' {
            self.i += 1;
            return None;
        }
        let k = self.read_str();
        self.ws();
        self.i += 1; // ':'
        self.ws();
        Some(k)
    }
}

fn parse_rates(line: &[u8]) -> Vec<(Vec<u8>, i64)> {
    let mut p = P { b: line, i: 0 };
    let mut rates = Vec::new();
    p.ws();
    p.i += 1;
    while let Some(k) = p.next_key() {
        if &*k == b"rates" {
            p.i += 1; // '{'
            while let Some(c) = p.next_key() {
                let mut v = 0i64;
                while p.peek().is_ascii_digit() {
                    v = v * 10 + (p.peek() - b'0') as i64;
                    p.i += 1;
                }
                rates.push((c.into_owned(), v));
            }
        } else {
            p.skip_value();
        }
    }
    rates
}

struct State {
    rates: Vec<(Vec<u8>, i64)>,
    count: u64,
    net: i64,
    channels: FxMap<(u64, i64)>,
    accounts: FxMap<i64>,
}

fn process_line(st: &mut State, line: &[u8]) {
    let mut p = P { b: line, i: 0 };
    p.ws();
    p.i += 1;
    let mut account: Cow<[u8]> = Cow::Borrowed(b"");
    let mut typ = 0u8; // 1 credit/refund, 2 debit, 3 void
    let mut amount: Cow<[u8]> = Cow::Borrowed(b"");
    let mut currency: Cow<[u8]> = Cow::Borrowed(b"");
    let mut channel: Cow<[u8]> = Cow::Borrowed(b"");
    let mut test = false;
    while let Some(k) = p.next_key() {
        match &*k {
            b"account" => account = p.read_str(),
            b"type" => {
                let t = p.read_str();
                typ = match &*t {
                    b"credit" | b"refund" => 1,
                    b"debit" => 2,
                    _ => 3,
                };
            }
            b"amount" => amount = p.read_str(),
            b"currency" => currency = p.read_str(),
            b"tags" => {
                p.i += 1; // '['
                loop {
                    p.ws();
                    match p.peek() {
                        b']' => {
                            p.i += 1;
                            break;
                        }
                        b',' => p.i += 1,
                        _ => {
                            let t = p.read_str();
                            if &*t == b"test" {
                                test = true;
                            }
                        }
                    }
                }
            }
            b"meta" => {
                p.i += 1; // '{'
                while let Some(mk) = p.next_key() {
                    if &*mk == b"channel" {
                        channel = p.read_str();
                    } else {
                        p.skip_value();
                    }
                }
            }
            _ => p.skip_value(),
        }
    }
    if typ == 3 || test {
        return;
    }
    // amount -> hundredths
    let a = &*amount;
    let mut ip = 0i64;
    let mut j = 0;
    while j < a.len() && a[j] != b'.' {
        ip = ip * 10 + (a[j] - b'0') as i64;
        j += 1;
    }
    let mut h = ip * 100;
    if j < a.len() {
        j += 1;
        if j < a.len() {
            h += (a[j] - b'0') as i64 * 10;
            j += 1;
            if j < a.len() {
                h += (a[j] - b'0') as i64;
            }
        }
    }
    let mut rate = 0i64;
    for (n, r) in &st.rates {
        if n.as_slice() == &*currency {
            rate = *r;
            break;
        }
    }
    let usd = h * rate / 1_000_000;
    let v = if typ == 2 { -usd } else { usd };
    st.count += 1;
    st.net += v;
    if let Some(e) = st.channels.get_mut(&*channel) {
        e.0 += 1;
        e.1 += v;
    } else {
        st.channels.insert(channel.into_owned(), (1, v));
    }
    if let Some(e) = st.accounts.get_mut(&*account) {
        *e += v;
    } else {
        st.accounts.insert(account.into_owned(), v);
    }
}

fn main() {
    let path = std::env::args().nth(1).expect("path");
    let mut file = std::fs::File::open(path).expect("open");
    let mut st = State {
        rates: Vec::new(),
        count: 0,
        net: 0,
        channels: FxMap::default(),
        accounts: FxMap::default(),
    };
    let mut buf: Vec<u8> = vec![0; 4 << 20];
    let mut have = 0usize;
    let mut first = true;
    let mut eof = false;
    while !eof {
        if have == buf.len() {
            buf.resize(buf.len() * 2, 0);
        }
        let n = file.read(&mut buf[have..]).expect("read");
        if n == 0 {
            eof = true;
        }
        have += n;
        let end = if eof {
            have
        } else {
            match buf[..have].iter().rposition(|&c| c == b'\n') {
                Some(x) => x + 1,
                None => continue,
            }
        };
        let mut s = 0;
        while s < end {
            let e = match buf[s..end].iter().position(|&c| c == b'\n') {
                Some(x) => s + x,
                None => end,
            };
            let mut line = &buf[s..e];
            if line.last() == Some(&b'\r') {
                line = &line[..line.len() - 1];
            }
            if !line.is_empty() {
                if first {
                    st.rates = parse_rates(line);
                    first = false;
                } else {
                    process_line(&mut st, line);
                }
            }
            s = e + 1;
        }
        buf.copy_within(end..have, 0);
        have -= end;
    }

    let mut out = String::new();
    out.push_str(&format!("counted {}\nnet {}\n", st.count, st.net));
    let mut chans: Vec<_> = st.channels.into_iter().collect();
    chans.sort();
    for (n, (c, v)) in &chans {
        out.push_str(&format!("channel {} {} {}\n", String::from_utf8_lossy(n), c, v));
    }
    let mut accs: Vec<_> = st.accounts.into_iter().collect();
    accs.sort_by(|a, b| b.1.cmp(&a.1).then_with(|| a.0.cmp(&b.0)));
    for (n, v) in accs.iter().take(10) {
        out.push_str(&format!("account {} {}\n", String::from_utf8_lossy(n), v));
    }
    std::io::stdout().write_all(out.as_bytes()).unwrap();
}
