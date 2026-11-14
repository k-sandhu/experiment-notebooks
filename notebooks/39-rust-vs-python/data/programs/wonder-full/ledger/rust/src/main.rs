use std::collections::HashMap;
use std::hash::{BuildHasherDefault, Hasher};
use std::io::{BufReader, BufRead, Write};

// FxHash-style hasher: much faster than SipHash for short byte-string keys.
#[derive(Default)]
struct FxHasher {
    hash: u64,
}
const FX_SEED: u64 = 0x51_7c_c1_b7_27_22_0a_95;
impl FxHasher {
    #[inline]
    fn add(&mut self, w: u64) {
        self.hash = (self.hash.rotate_left(5) ^ w).wrapping_mul(FX_SEED);
    }
}
impl Hasher for FxHasher {
    #[inline]
    fn write(&mut self, mut bytes: &[u8]) {
        while bytes.len() >= 8 {
            self.add(u64::from_le_bytes(bytes[..8].try_into().unwrap()));
            bytes = &bytes[8..];
        }
        if !bytes.is_empty() {
            let mut buf = [0u8; 8];
            buf[..bytes.len()].copy_from_slice(bytes);
            self.add(u64::from_le_bytes(buf));
        }
    }
    #[inline]
    fn write_usize(&mut self, n: usize) {
        self.add(n as u64);
    }
    #[inline]
    fn write_u64(&mut self, n: u64) {
        self.add(n);
    }
    #[inline]
    fn write_u32(&mut self, n: u32) {
        self.add(n as u64);
    }
    #[inline]
    fn write_u8(&mut self, n: u8) {
        self.add(n as u64);
    }
    #[inline]
    fn finish(&self) -> u64 {
        self.hash
    }
}
type FastMap<K, V> = HashMap<K, V, BuildHasherDefault<FxHasher>>;

struct P<'a> {
    s: &'a [u8],
    i: usize,
}

impl<'a> P<'a> {
    #[inline]
    fn ws(&mut self) {
        while self.i < self.s.len() && matches!(self.s[self.i], b' ' | b'\t' | b'\r' | b'\n') {
            self.i += 1;
        }
    }
    // Parse a string, return content range and has_escape. Assumes s[i]=='"'.
    #[inline]
    fn string_raw(&mut self) -> (usize, usize, bool) {
        self.i += 1;
        let start = self.i;
        let mut esc = false;
        loop {
            let b = self.s[self.i];
            if b == b'"' {
                let end = self.i;
                self.i += 1;
                return (start, end, esc);
            } else if b == b'\\' {
                esc = true;
                self.i += 2;
            } else {
                self.i += 1;
            }
        }
    }
    #[inline]
    fn skip_string(&mut self) {
        self.i += 1;
        loop {
            let b = self.s[self.i];
            if b == b'"' {
                self.i += 1;
                return;
            } else if b == b'\\' {
                self.i += 2;
            } else {
                self.i += 1;
            }
        }
    }
    fn skip_value(&mut self) {
        self.ws();
        match self.s[self.i] {
            b'"' => self.skip_string(),
            b'{' | b'[' => {
                let mut depth = 1usize;
                self.i += 1;
                while depth > 0 {
                    match self.s[self.i] {
                        b'"' => self.skip_string(),
                        b'{' | b'[' => { depth += 1; self.i += 1; }
                        b'}' | b']' => { depth -= 1; self.i += 1; }
                        _ => self.i += 1,
                    }
                }
            }
            _ => {
                while self.i < self.s.len()
                    && !matches!(self.s[self.i], b',' | b'}' | b']' | b' ' | b'\t' | b'\r' | b'\n')
                {
                    self.i += 1;
                }
            }
        }
    }
}

fn hex4(s: &[u8], mut i: usize) -> u32 {
    let mut v = 0u32;
    for _ in 0..4 {
        let c = s[i];
        v = v * 16 + match c {
            b'0'..=b'9' => (c - b'0') as u32,
            b'a'..=b'f' => (c - b'a' + 10) as u32,
            b'A'..=b'F' => (c - b'A' + 10) as u32,
            _ => 0,
        };
        i += 1;
    }
    v
}

/// Decode JSON string content s[start..end] into buf (as UTF-8 bytes). Returns slice of buf logic via buf itself.
fn decode_into(s: &[u8], start: usize, end: usize, has_esc: bool, buf: &mut Vec<u8>) {
    buf.clear();
    if !has_esc {
        buf.extend_from_slice(&s[start..end]);
        return;
    }
    let mut i = start;
    while i < end {
        let b = s[i];
        if b != b'\\' {
            buf.push(b);
            i += 1;
            continue;
        }
        let e = s[i + 1];
        i += 2;
        match e {
            b'"' => buf.push(b'"'),
            b'\\' => buf.push(b'\\'),
            b'/' => buf.push(b'/'),
            b'b' => buf.push(8),
            b'f' => buf.push(12),
            b'n' => buf.push(b'\n'),
            b'r' => buf.push(b'\r'),
            b't' => buf.push(b'\t'),
            b'u' => {
                let cp = hex4(s, i);
                i += 4;
                let ch = if (0xD800..0xDC00).contains(&cp) {
                    // surrogate pair?
                    if i + 5 < end && s[i] == b'\\' && s[i + 1] == b'u' {
                        let lo = hex4(s, i + 2);
                        if (0xDC00..0xE000).contains(&lo) {
                            i += 6;
                            let c = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
                            char::from_u32(c).unwrap_or('\u{FFFD}')
                        } else {
                            '\u{FFFD}'
                        }
                    } else {
                        '\u{FFFD}'
                    }
                } else {
                    char::from_u32(cp).unwrap_or('\u{FFFD}')
                };
                let mut tmp = [0u8; 4];
                buf.extend_from_slice(ch.encode_utf8(&mut tmp).as_bytes());
            }
            _ => buf.push(e),
        }
    }
}

#[inline]
fn parse_amount(b: &[u8]) -> i64 {
    let mut v: i64 = 0;
    let mut i = 0usize;
    while i < b.len() && b[i] != b'.' {
        v = v * 10 + (b[i] - b'0') as i64;
        i += 1;
    }
    v *= 100;
    if i < b.len() {
        // '.'
        let frac = &b[i + 1..];
        if frac.len() == 1 {
            v += (frac[0] - b'0') as i64 * 10;
        } else if frac.len() >= 2 {
            v += (frac[0] - b'0') as i64 * 10 + (frac[1] - b'0') as i64;
        }
    }
    v
}

#[inline]
fn parse_i64(p: &mut P) -> i64 {
    p.ws();
    let s = p.s;
    let mut neg = false;
    if s[p.i] == b'-' {
        neg = true;
        p.i += 1;
    }
    let mut v: i64 = 0;
    while p.i < s.len() && s[p.i].is_ascii_digit() {
        v = v * 10 + (s[p.i] - b'0') as i64;
        p.i += 1;
    }
    // Skip any fractional/exponent part just in case (rates are integers per spec)
    if p.i < s.len() && matches!(s[p.i], b'.' | b'e' | b'E') {
        // Fall back: reparse as float text (should not happen)
        let start = p.i;
        while p.i < s.len() && matches!(s[p.i], b'0'..=b'9' | b'.' | b'e' | b'E' | b'+' | b'-') {
            p.i += 1;
        }
        let _ = start;
    }
    if neg { -v } else { v }
}

// field kinds
const K_ACCOUNT: u8 = 1;
const K_TYPE: u8 = 2;
const K_AMOUNT: u8 = 3;
const K_CURRENCY: u8 = 4;
const K_TAGS: u8 = 5;
const K_META: u8 = 6;

#[inline]
fn key_kind(k: &[u8]) -> u8 {
    match k {
        b"account" => K_ACCOUNT,
        b"type" => K_TYPE,
        b"amount" => K_AMOUNT,
        b"currency" => K_CURRENCY,
        b"tags" => K_TAGS,
        b"meta" => K_META,
        _ => 0,
    }
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let path = &args[1];
    let file = std::fs::File::open(path).expect("open input");
    let mut reader = BufReader::with_capacity(1 << 18, file);
    let mut line: Vec<u8> = Vec::with_capacity(1024);

    // First line: rates
    let mut rates: Vec<(Vec<u8>, i64)> = Vec::new();
    let n = reader.read_until(b'\n', &mut line).expect("read");
    if n == 0 {
        print!("counted 0\nnet 0\n");
        return;
    }
    {
        let mut p = P { s: &line, i: 0 };
        let mut kbuf: Vec<u8> = Vec::new();
        p.ws();
        p.i += 1; // {
        loop {
            p.ws();
            if p.s[p.i] == b'}' { p.i += 1; break; }
            let (ks, ke, kesc) = p.string_raw();
            decode_into(p.s, ks, ke, kesc, &mut kbuf);
            let is_rates = kbuf == b"rates";
            p.ws(); p.i += 1; // :
            if is_rates {
                p.ws();
                p.i += 1; // {
                loop {
                    p.ws();
                    if p.s[p.i] == b'}' { p.i += 1; break; }
                    let (cs, ce, cesc) = p.string_raw();
                    let mut cbuf: Vec<u8> = Vec::new();
                    decode_into(p.s, cs, ce, cesc, &mut cbuf);
                    p.ws(); p.i += 1; // :
                    let v = parse_i64(&mut p);
                    rates.push((cbuf, v));
                    p.ws();
                    if p.i < p.s.len() && p.s[p.i] == b',' { p.i += 1; continue; }
                    if p.s[p.i] == b'}' { p.i += 1; break; }
                }
            } else {
                p.skip_value();
            }
            p.ws();
            if p.i < p.s.len() && p.s[p.i] == b',' { p.i += 1; continue; }
            if p.i < p.s.len() && p.s[p.i] == b'}' { p.i += 1; break; }
        }
    }
    // Fast rate lookup
    let rate_of = |cur: &[u8], rates: &Vec<(Vec<u8>, i64)>| -> i64 {
        for (k, v) in rates.iter() {
            if k.as_slice() == cur { return *v; }
        }
        0
    };

    let mut counted: i64 = 0;
    let mut net: i64 = 0;
    let mut channels: FastMap<Vec<u8>, (i64, i64)> =
        FastMap::with_capacity_and_hasher(64, BuildHasherDefault::default());
    let mut accounts: FastMap<Vec<u8>, i64> =
        FastMap::with_capacity_and_hasher(1 << 14, BuildHasherDefault::default());

    let mut kbuf: Vec<u8> = Vec::with_capacity(32);
    let mut vbuf: Vec<u8> = Vec::with_capacity(32);
    // Per-transaction scratch (decoded copies, reused)
    let mut account: Vec<u8> = Vec::with_capacity(16);
    let mut channel: Vec<u8> = Vec::with_capacity(16);

    loop {
        line.clear();
        let n = reader.read_until(b'\n', &mut line).expect("read");
        if n == 0 { break; }
        if line.iter().all(|&b| matches!(b, b' ' | b'\t' | b'\r' | b'\n')) { continue; }

        account.clear();
        channel.clear();
        let mut typ: u8 = 0; // 1 credit/refund(+), 2 debit(-), 3 void
        let mut hundredths: i64 = 0;
        let mut rate: i64 = 0;
        let mut has_test = false;

        {
            let mut p = P { s: &line, i: 0 };
            p.ws();
            p.i += 1; // {
            loop {
                p.ws();
                if p.s[p.i] == b'}' { p.i += 1; break; }
                let (ks, ke, kesc) = p.string_raw();
                let kind = if !kesc {
                    key_kind(&p.s[ks..ke])
                } else {
                    decode_into(p.s, ks, ke, true, &mut kbuf);
                    key_kind(&kbuf)
                };
                p.ws(); p.i += 1; // :
                p.ws();
                match kind {
                    K_ACCOUNT => {
                        let (vs, ve, vesc) = p.string_raw();
                        let src = p.s;
                        decode_into(src, vs, ve, vesc, &mut account);
                    }
                    K_TYPE => {
                        let (vs, ve, vesc) = p.string_raw();
                        let raw: &[u8] = if !vesc {
                            &p.s[vs..ve]
                        } else {
                            decode_into(p.s, vs, ve, true, &mut vbuf);
                            &vbuf
                        };
                        typ = match raw {
                            b"debit" => 2,
                            b"void" => 3,
                            _ => 1, // credit, refund
                        };
                    }
                    K_AMOUNT => {
                        let (vs, ve, vesc) = p.string_raw();
                        if !vesc {
                            hundredths = parse_amount(&p.s[vs..ve]);
                        } else {
                            decode_into(p.s, vs, ve, true, &mut vbuf);
                            hundredths = parse_amount(&vbuf);
                        }
                    }
                    K_CURRENCY => {
                        let (vs, ve, vesc) = p.string_raw();
                        if !vesc {
                            rate = rate_of(&p.s[vs..ve], &rates);
                        } else {
                            decode_into(p.s, vs, ve, true, &mut vbuf);
                            rate = rate_of(&vbuf, &rates);
                        }
                    }
                    K_TAGS => {
                        // array
                        p.i += 1; // [
                        loop {
                            p.ws();
                            if p.s[p.i] == b']' { p.i += 1; break; }
                            if p.s[p.i] == b'"' {
                                let (vs, ve, vesc) = p.string_raw();
                                if !vesc {
                                    if &p.s[vs..ve] == b"test" { has_test = true; }
                                } else {
                                    decode_into(p.s, vs, ve, true, &mut vbuf);
                                    if vbuf == b"test" { has_test = true; }
                                }
                            } else {
                                p.skip_value();
                            }
                            p.ws();
                            if p.s[p.i] == b',' { p.i += 1; continue; }
                            if p.s[p.i] == b']' { p.i += 1; break; }
                        }
                    }
                    K_META => {
                        p.i += 1; // {
                        loop {
                            p.ws();
                            if p.s[p.i] == b'}' { p.i += 1; break; }
                            let (ks2, ke2, kesc2) = p.string_raw();
                            let is_chan = if !kesc2 {
                                &p.s[ks2..ke2] == b"channel"
                            } else {
                                decode_into(p.s, ks2, ke2, true, &mut kbuf);
                                kbuf == b"channel"
                            };
                            p.ws(); p.i += 1; // :
                            p.ws();
                            if is_chan {
                                let (vs, ve, vesc) = p.string_raw();
                                let src = p.s;
                                decode_into(src, vs, ve, vesc, &mut channel);
                            } else {
                                p.skip_value();
                            }
                            p.ws();
                            if p.s[p.i] == b',' { p.i += 1; continue; }
                            if p.s[p.i] == b'}' { p.i += 1; break; }
                        }
                    }
                    _ => p.skip_value(),
                }
                p.ws();
                if p.i < p.s.len() && p.s[p.i] == b',' { p.i += 1; continue; }
                if p.i < p.s.len() && p.s[p.i] == b'}' { p.i += 1; break; }
            }
        }

        if typ == 3 || has_test {
            continue;
        }
        let usd = (hundredths * rate).div_euclid(1_000_000);
        let signed = if typ == 2 { -usd } else { usd };
        counted += 1;
        net += signed;
        match channels.get_mut(channel.as_slice()) {
            Some(e) => { e.0 += 1; e.1 += signed; }
            None => { channels.insert(channel.clone(), (1, signed)); }
        }
        match accounts.get_mut(account.as_slice()) {
            Some(e) => { *e += signed; }
            None => { accounts.insert(account.clone(), signed); }
        }
    }

    let mut out: Vec<u8> = Vec::with_capacity(4096);
    out.extend_from_slice(format!("counted {}\nnet {}\n", counted, net).as_bytes());
    let mut chans: Vec<(&Vec<u8>, &(i64, i64))> = channels.iter().collect();
    chans.sort_unstable_by(|a, b| a.0.cmp(b.0));
    for (name, (c, s)) in chans {
        out.extend_from_slice(b"channel ");
        out.extend_from_slice(name);
        out.extend_from_slice(format!(" {} {}\n", c, s).as_bytes());
    }
    let mut accs: Vec<(&Vec<u8>, &i64)> = accounts.iter().collect();
    accs.sort_unstable_by(|a, b| b.1.cmp(a.1).then_with(|| a.0.cmp(b.0)));
    for (name, v) in accs.into_iter().take(10) {
        out.extend_from_slice(b"account ");
        out.extend_from_slice(name);
        out.extend_from_slice(format!(" {}\n", v).as_bytes());
    }
    let stdout = std::io::stdout();
    let mut lock = stdout.lock();
    let _ = lock.write_all(&out);
    // suppress unused warnings for Read import path on some editions
    let _ = &reader;
}
