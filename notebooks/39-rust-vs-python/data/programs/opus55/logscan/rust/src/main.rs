use std::collections::HashMap;
use std::fs::File;
use std::hash::{BuildHasherDefault, Hasher};
use std::io::{Read, Write};

/// FxHash-style hasher: template keys are short and trusted, so a fast
/// non-cryptographic hash is fine.
#[derive(Default)]
struct FxHasher {
    hash: u64,
}

const SEED: u64 = 0x51_7c_c1_b7_27_22_0a_95;

impl FxHasher {
    #[inline]
    fn add(&mut self, w: u64) {
        self.hash = (self.hash.rotate_left(5) ^ w).wrapping_mul(SEED);
    }
}

impl Hasher for FxHasher {
    #[inline]
    fn write(&mut self, mut bytes: &[u8]) {
        while bytes.len() >= 8 {
            self.add(u64::from_le_bytes(bytes[..8].try_into().unwrap()));
            bytes = &bytes[8..];
        }
        let mut tail = 0u64;
        for (i, &b) in bytes.iter().enumerate() {
            tail |= (b as u64) << (8 * i);
        }
        self.add(tail);
    }
    #[inline]
    fn write_u8(&mut self, i: u8) {
        self.add(i as u64);
    }
    #[inline]
    fn write_usize(&mut self, i: usize) {
        self.add(i as u64);
    }
    #[inline]
    fn finish(&self) -> u64 {
        self.hash
    }
}

type FxMap<K, V> = HashMap<K, V, BuildHasherDefault<FxHasher>>;

/// Latency whose integer part has more significant digits than fit in u64
/// tenths. Every such value is larger than every `u64` latency.
#[derive(PartialEq, Eq, PartialOrd, Ord)]
struct BigLatency {
    int_len: usize,
    digits: Vec<u8>, // significant integer digits followed by the tenths digit
}

#[derive(Default)]
struct Group {
    small: Vec<u64>,
    big: Vec<BigLatency>,
}

impl Group {
    fn count(&self) -> usize {
        self.small.len() + self.big.len()
    }
}

const fn path_table() -> [bool; 256] {
    let mut t = [false; 256];
    let mut c = 0;
    while c < 256 {
        let b = c as u8;
        t[c] = b.is_ascii_alphanumeric() || b == b'_' || b == b'/' || b == b'-';
        c += 1;
    }
    t
}

static PATH_CHAR: [bool; 256] = path_table();

const LO: u64 = 0x0101_0101_0101_0101;
const HI: u64 = 0x8080_8080_8080_8080;

#[cfg(target_arch = "x86_64")]
#[inline]
fn find_byte(hay: &[u8], needle: u8) -> Option<usize> {
    use std::arch::x86_64::*;
    let mut i = 0;
    // SAFETY: SSE2 is part of the x86_64 baseline; loads are unaligned and
    // stay within `hay`.
    unsafe {
        let pat = _mm_set1_epi8(needle as i8);
        while i + 16 <= hay.len() {
            let v = _mm_loadu_si128(hay.as_ptr().add(i) as *const __m128i);
            let m = _mm_movemask_epi8(_mm_cmpeq_epi8(v, pat));
            if m != 0 {
                return Some(i + m.trailing_zeros() as usize);
            }
            i += 16;
        }
    }
    find_byte_swar(&hay[i..], needle).map(|p| p + i)
}

#[cfg(not(target_arch = "x86_64"))]
#[inline]
fn find_byte(hay: &[u8], needle: u8) -> Option<usize> {
    find_byte_swar(hay, needle)
}

#[inline]
fn find_byte_swar(hay: &[u8], needle: u8) -> Option<usize> {
    let pat = LO * needle as u64;
    let mut i = 0;
    while i + 8 <= hay.len() {
        let x = u64::from_le_bytes(hay[i..i + 8].try_into().unwrap()) ^ pat;
        let m = x.wrapping_sub(LO) & !x & HI;
        if m != 0 {
            return Some(i + (m.trailing_zeros() / 8) as usize);
        }
        i += 8;
    }
    hay[i..].iter().position(|&b| b == needle).map(|p| p + i)
}

#[inline]
fn is_digit(b: u8) -> bool {
    b.wrapping_sub(b'0') < 10
}

struct Stats {
    lines: u64,
    malformed: u64,
    status: [u64; 10],
    groups: FxMap<Vec<u8>, Group>,
    template: Vec<u8>,
}

impl Stats {
    /// Parses one line (without its newline). Returns false if malformed.
    #[inline]
    fn line(&mut self, l: &[u8]) -> bool {
        let n = l.len();
        if n < 25 {
            return false;
        }
        // Timestamp: YYYY-MM-DDTHH:MM:SS.mmmZ followed by a space.
        const DIGITS: [usize; 17] = [0, 1, 2, 3, 5, 6, 8, 9, 11, 12, 14, 15, 17, 18, 20, 21, 22];
        for &k in DIGITS.iter() {
            if !is_digit(l[k]) {
                return false;
            }
        }
        if l[4] != b'-'
            || l[7] != b'-'
            || l[10] != b'T'
            || l[13] != b':'
            || l[16] != b':'
            || l[19] != b'.'
            || l[23] != b'Z'
            || l[24] != b' '
        {
            return false;
        }
        let mut i = 25;
        // Host: [a-z]+-\d+
        let s = i;
        while i < n && l[i].is_ascii_lowercase() {
            i += 1;
        }
        if i == s || i >= n || l[i] != b'-' {
            return false;
        }
        i += 1;
        let s = i;
        while i < n && is_digit(l[i]) {
            i += 1;
        }
        if i == s || i >= n || l[i] != b' ' {
            return false;
        }
        i += 1;
        // Method.
        let rest = &l[i..];
        let mlen = if rest.starts_with(b"GET ") || rest.starts_with(b"PUT ") {
            4
        } else if rest.starts_with(b"POST ") {
            5
        } else if rest.starts_with(b"PATCH ") || rest.starts_with(b"DELETE ") {
            if rest[0] == b'P' { 6 } else { 7 }
        } else {
            return false;
        };
        i += mlen;
        // Path.
        if i >= n || l[i] != b'/' {
            return false;
        }
        let path_start = i;
        i += 1;
        while i < n && PATH_CHAR[l[i] as usize] {
            i += 1;
        }
        let path_end = i;
        if i < n && l[i] == b'?' {
            match find_byte(&l[i..], b' ') {
                Some(p) => i += p,
                None => return false,
            }
        }
        // Status, size, latency: ' ddd ' '\d+B ' '\d+\.\dms "'
        if i + 5 > n || l[i] != b' ' {
            return false;
        }
        let (s0, s1, s2) = (l[i + 1], l[i + 2], l[i + 3]);
        if !is_digit(s0) || !is_digit(s1) || !is_digit(s2) || l[i + 4] != b' ' {
            return false;
        }
        i += 5;
        let s = i;
        while i < n && is_digit(l[i]) {
            i += 1;
        }
        if i == s || i + 1 >= n || l[i] != b'B' || l[i + 1] != b' ' {
            return false;
        }
        i += 2;
        let lat_start = i;
        while i < n && is_digit(l[i]) {
            i += 1;
        }
        let lat_end = i;
        if lat_end == lat_start
            || i + 6 > n
            || l[i] != b'.'
            || !is_digit(l[i + 1])
            || l[i + 2] != b'm'
            || l[i + 3] != b's'
            || l[i + 4] != b' '
            || l[i + 5] != b'"'
        {
            return false;
        }
        let tenth = l[i + 1] - b'0';
        i += 6;
        // User agent: no quote until the final byte, which is a quote.
        if i >= n || l[n - 1] != b'"' || find_byte(&l[i..n - 1], b'"').is_some() {
            return false;
        }

        self.status[(s0 - b'0') as usize] += 1;

        // Template.
        let t = &mut self.template;
        t.clear();
        let path = &l[path_start..path_end];
        for (k, seg) in path.split(|&b| b == b'/').enumerate() {
            if k > 0 {
                t.push(b'/');
            }
            if !seg.is_empty() && seg.iter().all(|&b| is_digit(b)) {
                t.extend_from_slice(b"{id}");
            } else {
                t.extend_from_slice(seg);
            }
        }
        let group = match self.groups.get_mut(t.as_slice()) {
            Some(g) => g,
            None => self.groups.entry(t.clone()).or_default(),
        };

        // Latency in tenths.
        let mut digits = &l[lat_start..lat_end];
        while digits.len() > 1 && digits[0] == b'0' {
            digits = &digits[1..];
        }
        if digits.len() <= 17 {
            let mut v = 0u64;
            for &d in digits {
                v = v * 10 + (d - b'0') as u64;
            }
            group.small.push(v * 10 + tenth as u64);
        } else {
            let mut d = digits.to_vec();
            d.push(b'0' + tenth);
            group.big.push(BigLatency { int_len: digits.len(), digits: d });
        }
        true
    }

    fn block(&mut self, buf: &[u8]) {
        let mut pos = 0;
        while let Some(p) = find_byte(&buf[pos..], b'\n') {
            self.lines += 1;
            if !self.line(&buf[pos..pos + p]) {
                self.malformed += 1;
            }
            pos += p + 1;
        }
    }
}

fn fmt_small(out: &mut String, v: u64) {
    use std::fmt::Write;
    write!(out, "{}.{}", v / 10, v % 10).unwrap();
}

fn fmt_big(out: &mut String, b: &BigLatency) {
    let s = std::str::from_utf8(&b.digits).unwrap();
    out.push_str(&s[..b.int_len]);
    out.push('.');
    out.push_str(&s[b.int_len..]);
}

fn main() {
    let path = std::env::args().nth(1).expect("input path");
    let mut file = File::open(path).expect("open input");

    let mut st = Stats {
        lines: 0,
        malformed: 0,
        status: [0; 10],
        groups: FxMap::default(),
        template: Vec::with_capacity(256),
    };

    const CHUNK: usize = 1 << 22;
    let mut buf: Vec<u8> = vec![0; CHUNK];
    let mut filled = 0;
    loop {
        if filled == buf.len() {
            buf.resize(buf.len() * 2, 0);
        }
        let r = file.read(&mut buf[filled..]).expect("read input");
        if r == 0 {
            break;
        }
        let start = filled;
        filled += r;
        // Process complete lines only; keep the partial tail for the next read.
        if let Some(last) = buf[start..filled].iter().rposition(|&b| b == b'\n') {
            let end = start + last + 1;
            st.block(&buf[..end]);
            buf.copy_within(end..filled, 0);
            filled -= end;
        }
    }

    let mut out = String::with_capacity(4096);
    use std::fmt::Write as _;
    writeln!(out, "lines {}", st.lines).unwrap();
    writeln!(out, "malformed {}", st.malformed).unwrap();
    for (c, &cnt) in st.status.iter().enumerate() {
        if cnt > 0 {
            writeln!(out, "status {}xx {}", c, cnt).unwrap();
        }
    }

    let mut ranked: Vec<(&Vec<u8>, &mut Group)> = st.groups.iter_mut().collect();
    ranked.sort_unstable_by(|a, b| b.1.count().cmp(&a.1.count()).then_with(|| a.0.cmp(b.0)));
    for (name, g) in ranked.into_iter().take(10) {
        g.small.sort_unstable();
        g.big.sort_unstable();
        let n = g.count();
        out.push_str("path ");
        out.push_str(std::str::from_utf8(name).unwrap());
        write!(out, " {}", n).unwrap();
        for k in [(50 * n).div_ceil(100) - 1, (95 * n).div_ceil(100) - 1, n - 1] {
            out.push(' ');
            if k < g.small.len() {
                fmt_small(&mut out, g.small[k]);
            } else {
                fmt_big(&mut out, &g.big[k - g.small.len()]);
            }
        }
        out.push('\n');
    }
    std::io::stdout().lock().write_all(out.as_bytes()).unwrap();
}
