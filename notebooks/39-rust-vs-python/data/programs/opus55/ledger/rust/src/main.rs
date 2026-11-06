use std::collections::HashMap;
use std::fs::File;
use std::hash::{BuildHasherDefault, Hasher};
use std::io::{Read, Write};

#[derive(Default, Clone, Copy)]
struct FxHasher(u64);

impl Hasher for FxHasher {
    #[inline]
    fn write(&mut self, bytes: &[u8]) {
        const K: u64 = 0x517c_c1b7_2722_0a95;
        let mut h = self.0;
        let mut b = bytes;
        while b.len() >= 8 {
            let v = u64::from_le_bytes(b[..8].try_into().unwrap());
            h = (h.rotate_left(5) ^ v).wrapping_mul(K);
            b = &b[8..];
        }
        if b.len() >= 4 {
            let v = u32::from_le_bytes(b[..4].try_into().unwrap()) as u64;
            h = (h.rotate_left(5) ^ v).wrapping_mul(K);
            b = &b[4..];
        }
        for &x in b {
            h = (h.rotate_left(5) ^ x as u64).wrapping_mul(K);
        }
        self.0 = h;
    }
    #[inline]
    fn write_u8(&mut self, i: u8) {
        self.0 = (self.0.rotate_left(5) ^ i as u64).wrapping_mul(0x517c_c1b7_2722_0a95);
    }
    #[inline]
    fn write_usize(&mut self, i: usize) {
        self.0 = (self.0.rotate_left(5) ^ i as u64).wrapping_mul(0x517c_c1b7_2722_0a95);
    }
    #[inline]
    fn finish(&self) -> u64 {
        self.0
    }
}

type FxMap<K, V> = HashMap<K, V, BuildHasherDefault<FxHasher>>;

#[derive(serde::Deserialize)]
struct RatesLine {
    rates: HashMap<String, i64>,
}

const T_CREDIT: u8 = 1;
const T_DEBIT: u8 = 2;
const T_REFUND: u8 = 3;
const T_VOID: u8 = 4;

#[inline(always)]
fn skip_ws(b: &[u8], i: &mut usize) {
    while matches!(b[*i], b' ' | b'\t' | b'\r' | b'\n') {
        *i += 1;
    }
}

/// Finds the next '"' or '\\' at or after `i`.
#[inline(always)]
fn find_quote_or_bs(b: &[u8], mut i: usize) -> usize {
    use std::arch::x86_64::*;
    unsafe {
        let q = _mm_set1_epi8(b'"' as i8);
        let bs = _mm_set1_epi8(b'\\' as i8);
        while i + 16 <= b.len() {
            let v = _mm_loadu_si128(b.as_ptr().add(i) as *const __m128i);
            let m = _mm_movemask_epi8(_mm_or_si128(_mm_cmpeq_epi8(v, q), _mm_cmpeq_epi8(v, bs)));
            if m != 0 {
                return i + m.trailing_zeros() as usize;
            }
            i += 16;
        }
    }
    while b[i] != b'"' && b[i] != b'\\' {
        i += 1;
    }
    i
}

/// Finds the next '"', '{', '[', '}' or ']' at or after `i`.
#[inline(always)]
fn find_structural(b: &[u8], mut i: usize) -> usize {
    use std::arch::x86_64::*;
    unsafe {
        let q = _mm_set1_epi8(b'"' as i8);
        let lower = _mm_set1_epi8(0x20);
        let open = _mm_set1_epi8(b'{' as i8);
        let close = _mm_set1_epi8(b'}' as i8);
        while i + 16 <= b.len() {
            let v = _mm_loadu_si128(b.as_ptr().add(i) as *const __m128i);
            let l = _mm_or_si128(v, lower);
            let m = _mm_movemask_epi8(_mm_or_si128(
                _mm_cmpeq_epi8(v, q),
                _mm_or_si128(_mm_cmpeq_epi8(l, open), _mm_cmpeq_epi8(l, close)),
            ));
            if m != 0 {
                return i + m.trailing_zeros() as usize;
            }
            i += 16;
        }
    }
    while CLASS[b[i] as usize] == 0 {
        i += 1;
    }
    i
}

/// `i` points just past the opening quote; leaves `i` just past the closing quote.
#[inline(always)]
fn skip_string(b: &[u8], i: &mut usize) {
    let mut j = *i;
    loop {
        j = find_quote_or_bs(b, j);
        if b[j] == b'"' {
            *i = j + 1;
            return;
        }
        j += 2;
    }
}

fn hex4(b: &[u8], i: usize) -> u32 {
    let mut v = 0u32;
    for k in 0..4 {
        let c = b[i + k];
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

fn push_utf8(out: &mut Vec<u8>, cp: u32) {
    let mut tmp = [0u8; 4];
    let ch = char::from_u32(cp).unwrap_or('\u{FFFD}');
    out.extend_from_slice(ch.encode_utf8(&mut tmp).as_bytes());
}

/// Slow path: decode a string with escapes. `i` points just past the opening quote.
#[cold]
fn decode_string(b: &[u8], i: &mut usize, out: &mut Vec<u8>) {
    out.clear();
    let mut j = *i;
    loop {
        let k = find_quote_or_bs(b, j);
        out.extend_from_slice(&b[j..k]);
        if b[k] == b'"' {
            *i = k + 1;
            return;
        }
        let e = b[k + 1];
        j = k + 2;
        match e {
            b'n' => out.push(b'\n'),
            b't' => out.push(b'\t'),
            b'r' => out.push(b'\r'),
            b'b' => out.push(8),
            b'f' => out.push(12),
            b'u' => {
                let mut cp = hex4(b, j);
                j += 4;
                if (0xD800..0xDC00).contains(&cp) && b[j] == b'\\' && b[j + 1] == b'u' {
                    let lo = hex4(b, j + 2);
                    if (0xDC00..0xE000).contains(&lo) {
                        cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
                        j += 6;
                    }
                }
                push_utf8(out, cp);
            }
            c => out.push(c),
        }
    }
}

/// Reads a string value (`i` at opening quote). Returns the raw slice when it has no escapes,
/// otherwise decodes into `scratch` and returns that.
#[inline(always)]
fn read_str<'a>(b: &'a [u8], i: &mut usize, scratch: &'a mut Vec<u8>) -> &'a [u8] {
    let start = *i + 1;
    let k = find_quote_or_bs(b, start);
    if b[k] == b'"' {
        *i = k + 1;
        &b[start..k]
    } else {
        let mut j = start;
        decode_string(b, &mut j, scratch);
        *i = j;
        &scratch[..]
    }
}

static CLASS: [u8; 256] = {
    let mut t = [0u8; 256];
    t[b'"' as usize] = 1;
    t[b'{' as usize] = 2;
    t[b'[' as usize] = 2;
    t[b'}' as usize] = 3;
    t[b']' as usize] = 3;
    t
};

/// Skips any JSON value starting at `i` (after whitespace).
fn skip_value(b: &[u8], i: &mut usize) {
    match b[*i] {
        b'"' => {
            *i += 1;
            skip_string(b, i);
        }
        b'{' | b'[' => {
            let mut depth = 1u32;
            let mut j = *i + 1;
            loop {
                j = find_structural(b, j);
                match CLASS[b[j] as usize] {
                    1 => {
                        j += 1;
                        skip_string(b, &mut j);
                    }
                    2 => {
                        depth += 1;
                        j += 1;
                    }
                    _ => {
                        depth -= 1;
                        j += 1;
                        if depth == 0 {
                            break;
                        }
                    }
                }
            }
            *i = j;
        }
        _ => {
            let mut j = *i;
            while !matches!(b[j], b',' | b'}' | b']' | b' ' | b'\t' | b'\r' | b'\n') {
                j += 1;
            }
            *i = j;
        }
    }
}

fn parse_amount(s: &[u8]) -> i64 {
    let mut v: i64 = 0;
    let mut frac: i32 = -1;
    for &c in s {
        if c == b'.' {
            frac = 0;
        } else {
            v = v * 10 + (c - b'0') as i64;
            if frac >= 0 {
                frac += 1;
            }
        }
    }
    match frac {
        -1 | 0 => v * 100,
        1 => v * 10,
        _ => v,
    }
}

struct State {
    rates: FxMap<Vec<u8>, i64>,
    accounts: FxMap<Box<[u8]>, i64>,
    channels: FxMap<Box<[u8]>, (i64, i64)>,
    counted: i64,
    net: i64,
    acct: Vec<u8>,
    chan: Vec<u8>,
    scratch: Vec<u8>,
    scratch2: Vec<u8>,
}

impl State {
    /// Parses one transaction object starting at `i` (pointing at '{'); returns position after it.
    fn record(&mut self, b: &[u8], mut i: usize) -> usize {
        i += 1;
        let mut ty = 0u8;
        let mut has_test = false;
        let mut hundredths: i64 = 0;
        let mut rate: i64 = 0;
        loop {
            skip_ws(b, &mut i);
            if b[i] == b'}' {
                i += 1;
                break;
            }
            let key = read_str(b, &mut i, &mut self.scratch);
            let kid: u8 = match key {
                b"account" => 1,
                b"type" => 2,
                b"amount" => 3,
                b"currency" => 4,
                b"tags" => 5,
                b"meta" => 6,
                _ => 0,
            };
            skip_ws(b, &mut i);
            i += 1; // ':'
            skip_ws(b, &mut i);
            match kid {
                1 => {
                    let s = read_str(b, &mut i, &mut self.scratch);
                    self.acct.clear();
                    self.acct.extend_from_slice(s);
                }
                2 => {
                    let s = read_str(b, &mut i, &mut self.scratch);
                    ty = match s {
                        b"credit" => T_CREDIT,
                        b"debit" => T_DEBIT,
                        b"refund" => T_REFUND,
                        _ => T_VOID,
                    };
                }
                3 => {
                    let s = read_str(b, &mut i, &mut self.scratch);
                    hundredths = parse_amount(s);
                }
                4 => {
                    let s = read_str(b, &mut i, &mut self.scratch);
                    rate = *self.rates.get(s).expect("unknown currency");
                }
                5 => {
                    i += 1; // '['
                    loop {
                        skip_ws(b, &mut i);
                        match b[i] {
                            b']' => {
                                i += 1;
                                break;
                            }
                            b',' => i += 1,
                            b'"' => {
                                if read_str(b, &mut i, &mut self.scratch) == b"test" {
                                    has_test = true;
                                }
                            }
                            _ => skip_value(b, &mut i),
                        }
                    }
                }
                6 => {
                    i += 1; // '{'
                    loop {
                        skip_ws(b, &mut i);
                        match b[i] {
                            b'}' => {
                                i += 1;
                                break;
                            }
                            b',' => i += 1,
                            _ => {
                                let is_chan = read_str(b, &mut i, &mut self.scratch2) == b"channel";
                                skip_ws(b, &mut i);
                                i += 1; // ':'
                                skip_ws(b, &mut i);
                                if is_chan {
                                    let s = read_str(b, &mut i, &mut self.scratch);
                                    self.chan.clear();
                                    self.chan.extend_from_slice(s);
                                } else {
                                    skip_value(b, &mut i);
                                }
                            }
                        }
                    }
                }
                _ => skip_value(b, &mut i),
            }
            skip_ws(b, &mut i);
            if b[i] == b',' {
                i += 1;
            }
        }

        if ty != T_VOID && !has_test {
            let usd = hundredths * rate / 1_000_000;
            let v = if ty == T_DEBIT { -usd } else { usd };
            self.counted += 1;
            self.net += v;
            match self.accounts.get_mut(&self.acct[..]) {
                Some(s) => *s += v,
                None => {
                    self.accounts.insert(self.acct.clone().into_boxed_slice(), v);
                }
            }
            match self.channels.get_mut(&self.chan[..]) {
                Some(s) => {
                    s.0 += 1;
                    s.1 += v;
                }
                None => {
                    self.channels.insert(self.chan.clone().into_boxed_slice(), (1, v));
                }
            }
        }
        i
    }

    /// Processes all complete lines in `b`; returns the number of bytes consumed.
    fn process(&mut self, b: &[u8]) -> usize {
        let mut i = 0;
        let mut done = 0;
        // Only process up to the last newline so a record never crosses the buffer end.
        let end = match b.iter().rposition(|&c| c == b'\n') {
            Some(p) => p + 1,
            None => return 0,
        };
        let b = &b[..end];
        while i < end {
            while matches!(b[i], b' ' | b'\t' | b'\r') {
                i += 1;
            }
            if b[i] == b'{' {
                i = self.record(b, i);
            }
            // move to the end of the line
            while b[i] != b'\n' {
                i += 1;
            }
            i += 1;
            done = i;
            if i >= end {
                break;
            }
        }
        done
    }
}

fn main() {
    let path = std::env::args().nth(1).expect("usage: solution INPUT");
    let mut f = File::open(path).expect("open");

    const CHUNK: usize = 1 << 22;
    let mut buf: Vec<u8> = vec![0; CHUNK + 64];
    let mut len = 0usize;

    // Read the rates line.
    let first_nl;
    loop {
        if let Some(p) = buf[..len].iter().position(|&c| c == b'\n') {
            first_nl = p;
            break;
        }
        if len == buf.len() {
            buf.resize(buf.len() * 2, 0);
        }
        let n = f.read(&mut buf[len..]).expect("read");
        if n == 0 {
            first_nl = len;
            break;
        }
        len += n;
    }
    let rl: RatesLine = serde_json::from_slice(&buf[..first_nl]).expect("rates");
    let mut rates: FxMap<Vec<u8>, i64> = FxMap::default();
    for (k, v) in rl.rates {
        rates.insert(k.into_bytes(), v);
    }

    let mut st = State {
        rates,
        accounts: FxMap::default(),
        channels: FxMap::default(),
        counted: 0,
        net: 0,
        acct: Vec::new(),
        chan: Vec::new(),
        scratch: Vec::new(),
        scratch2: Vec::new(),
    };

    let start = (first_nl + 1).min(len);
    buf.copy_within(start..len, 0);
    len -= start;

    loop {
        if len == buf.len() {
            buf.resize(buf.len() * 2, 0);
        }
        let n = f.read(&mut buf[len..]).expect("read");
        len += n;
        if n == 0 {
            // final partial line without newline
            if len > 0 {
                if buf[len - 1] != b'\n' {
                    if len == buf.len() {
                        buf.push(0);
                    }
                    buf[len] = b'\n';
                    len += 1;
                }
                let used = st.process(&buf[..len]);
                debug_assert_eq!(used, len);
            }
            break;
        }
        let used = st.process(&buf[..len]);
        buf.copy_within(used..len, 0);
        len -= used;
    }

    let mut out = String::with_capacity(4096);
    use std::fmt::Write as _;
    writeln!(out, "counted {}", st.counted).unwrap();
    writeln!(out, "net {}", st.net).unwrap();
    let mut chans: Vec<(&Box<[u8]>, &(i64, i64))> = st.channels.iter().collect();
    chans.sort_unstable_by(|a, b| a.0.cmp(b.0));
    for (name, (c, v)) in chans {
        writeln!(out, "channel {} {} {}", String::from_utf8_lossy(name), c, v).unwrap();
    }
    let mut accts: Vec<(&Box<[u8]>, i64)> = st.accounts.iter().map(|(k, v)| (k, *v)).collect();
    let cmp = |a: &(&Box<[u8]>, i64), b: &(&Box<[u8]>, i64)| b.1.cmp(&a.1).then_with(|| a.0.cmp(b.0));
    if accts.len() > 10 {
        accts.select_nth_unstable_by(10, cmp);
        accts.truncate(10);
    }
    accts.sort_unstable_by(cmp);
    for (name, v) in accts {
        writeln!(out, "account {} {}", String::from_utf8_lossy(name), v).unwrap();
    }
    std::io::stdout().write_all(out.as_bytes()).unwrap();
}
