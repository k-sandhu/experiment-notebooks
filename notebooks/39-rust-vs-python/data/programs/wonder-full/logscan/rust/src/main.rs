use std::collections::HashMap;
use std::fmt::Write as _;
use std::hash::{BuildHasherDefault, Hasher};
use std::io::Write as _;

// FxHash-style hasher: much cheaper than SipHash for short byte keys.
#[derive(Default)]
struct FxHasher {
    hash: u64,
}

const FX_SEED: u64 = 0x51_7c_c1_b7_27_22_0a_95;

impl FxHasher {
    #[inline]
    fn add(&mut self, word: u64) {
        self.hash = (self.hash.rotate_left(5) ^ word).wrapping_mul(FX_SEED);
    }
}

impl Hasher for FxHasher {
    #[inline]
    fn finish(&self) -> u64 {
        self.hash
    }

    #[inline]
    fn write(&mut self, mut bytes: &[u8]) {
        while bytes.len() >= 8 {
            let (chunk, rest) = bytes.split_at(8);
            self.add(u64::from_le_bytes(chunk.try_into().unwrap()));
            bytes = rest;
        }
        let mut tail = 0u64;
        let mut shift = 0;
        for &b in bytes {
            tail |= (b as u64) << shift;
            shift += 8;
        }
        if !bytes.is_empty() {
            self.add(tail);
        }
    }

    #[inline]
    fn write_usize(&mut self, n: usize) {
        self.add(n as u64);
    }

    #[inline]
    fn write_u8(&mut self, n: u8) {
        self.add(n as u64);
    }
}

type FxMap = HashMap<Vec<u8>, Vec<u128>, BuildHasherDefault<FxHasher>>;

/// Index of the next b'\n' at or after `from`, or data.len().
#[inline]
fn find_newline(data: &[u8], from: usize) -> usize {
    let mut i = from;
    while i + 8 <= data.len() {
        let word = u64::from_le_bytes(data[i..i + 8].try_into().unwrap());
        let v = word ^ 0x0a0a_0a0a_0a0a_0a0a;
        let found = v.wrapping_sub(0x0101_0101_0101_0101) & !v & 0x8080_8080_8080_8080;
        if found != 0 {
            return i + (found.trailing_zeros() / 8) as usize;
        }
        i += 8;
    }
    while i < data.len() {
        if data[i] == b'\n' {
            return i;
        }
        i += 1;
    }
    data.len()
}

/// Validate one line against the spec's regex.  On success returns
/// (status first digit 0..=9, path start, path end, latency in tenths).
#[inline]
fn parse(line: &[u8]) -> Option<(u8, usize, usize, u128)> {
    let n = line.len();
    if n < 50 {
        return None;
    }
    #[inline(always)]
    fn dig(b: u8) -> bool {
        b.is_ascii_digit()
    }
    // Timestamp: fixed width, offsets 0..=24.
    if !(dig(line[0]) && dig(line[1]) && dig(line[2]) && dig(line[3])
        && line[4] == b'-' && dig(line[5]) && dig(line[6])
        && line[7] == b'-' && dig(line[8]) && dig(line[9])
        && line[10] == b'T' && dig(line[11]) && dig(line[12])
        && line[13] == b':' && dig(line[14]) && dig(line[15])
        && line[16] == b':' && dig(line[17]) && dig(line[18])
        && line[19] == b'.' && dig(line[20]) && dig(line[21]) && dig(line[22])
        && line[23] == b'Z' && line[24] == b' ')
    {
        return None;
    }
    let mut p = 25usize;

    // Host: [a-z]+-\d+
    let s = p;
    while p < n && line[p].is_ascii_lowercase() {
        p += 1;
    }
    if p == s || p >= n || line[p] != b'-' {
        return None;
    }
    p += 1;
    let s = p;
    while p < n && dig(line[p]) {
        p += 1;
    }
    if p == s || p >= n || line[p] != b' ' {
        return None;
    }
    p += 1;

    // Method.
    let rest = &line[p..];
    if rest.starts_with(b"GET ") {
        p += 4;
    } else if rest.starts_with(b"POST ") || rest.starts_with(b"PATCH ") {
        p += if rest[1] == b'O' { 5 } else { 6 };
    } else if rest.starts_with(b"PUT ") {
        p += 4;
    } else if rest.starts_with(b"DELETE ") {
        p += 7;
    } else {
        return None;
    }

    // Path: /[A-Za-z0-9_/-]*
    let path_start = p;
    if p >= n || line[p] != b'/' {
        return None;
    }
    p += 1;
    while p < n {
        let c = line[p];
        if c.is_ascii_alphanumeric() || c == b'_' || c == b'/' || c == b'-' {
            p += 1;
        } else {
            break;
        }
    }
    let path_end = p;

    // Optional query: ?[^ ]*
    if p < n && line[p] == b'?' {
        p += 1;
        while p < n && line[p] != b' ' {
            p += 1;
        }
    }
    if p >= n || line[p] != b' ' {
        return None;
    }
    p += 1;

    // Status: exactly 3 digits.
    if p + 3 >= n || !dig(line[p]) || !dig(line[p + 1]) || !dig(line[p + 2])
        || line[p + 3] != b' '
    {
        return None;
    }
    let status_digit = line[p] - b'0';
    p += 4;

    // Size: \d+B
    let s = p;
    while p < n && dig(line[p]) {
        p += 1;
    }
    if p == s || p + 1 >= n || line[p] != b'B' || line[p + 1] != b' ' {
        return None;
    }
    p += 2;

    // Latency: \d+\.\dms
    let s = p;
    let mut lat: u128 = 0;
    while p < n && dig(line[p]) {
        lat = lat.saturating_mul(10).saturating_add((line[p] - b'0') as u128);
        p += 1;
    }
    if p == s || p >= n || line[p] != b'.' {
        return None;
    }
    p += 1;
    if p >= n || !dig(line[p]) {
        return None;
    }
    lat = lat.saturating_mul(10).saturating_add((line[p] - b'0') as u128);
    p += 1;
    if p + 2 >= n || line[p] != b'm' || line[p + 1] != b's' || line[p + 2] != b' ' {
        return None;
    }
    p += 3;

    // User agent: "[^"]*" and then end of line.
    if p + 1 >= n || line[p] != b'"' || line[n - 1] != b'"'
        || line[p + 1..n - 1].contains(&b'"')
    {
        return None;
    }

    Some((status_digit, path_start, path_end, lat))
}

fn main() {
    let path = std::env::args_os().nth(1).expect("input path argument");
    let data = std::fs::read(&path).expect("read input file");

    let mut lines: u64 = 0;
    let mut malformed: u64 = 0;
    let mut status = [0u64; 10];
    let mut map: FxMap = HashMap::default();
    let mut scratch: Vec<u8> = Vec::with_capacity(64);

    let mut start = 0usize;
    while start < data.len() {
        let end = find_newline(&data, start);
        let line = &data[start..end];
        lines += 1;
        match parse(line) {
            Some((digit, ps, pe, lat)) => {
                status[digit as usize] += 1;
                // Build the path template into the reused scratch buffer.
                scratch.clear();
                let pth = &line[ps..pe];
                let mut seg_start = 0usize;
                let mut i = 0usize;
                loop {
                    if i == pth.len() || pth[i] == b'/' {
                        let seg = &pth[seg_start..i];
                        if !seg.is_empty() && seg.iter().all(|c| c.is_ascii_digit()) {
                            scratch.extend_from_slice(b"{id}");
                        } else {
                            scratch.extend_from_slice(seg);
                        }
                        if i == pth.len() {
                            break;
                        }
                        scratch.push(b'/');
                        seg_start = i + 1;
                    }
                    i += 1;
                }
                match map.get_mut(scratch.as_slice()) {
                    Some(v) => v.push(lat),
                    None => {
                        map.insert(scratch.clone(), vec![lat]);
                    }
                }
            }
            None => malformed += 1,
        }
        start = end + 1;
    }

    let mut entries: Vec<(Vec<u8>, Vec<u128>)> = map.into_iter().collect();
    entries.sort_by(|a, b| b.1.len().cmp(&a.1.len()).then_with(|| a.0.cmp(&b.0)));
    entries.truncate(10);

    let mut out = String::with_capacity(1024);
    let _ = writeln!(out, "lines {lines}");
    let _ = writeln!(out, "malformed {malformed}");
    for (d, &c) in status.iter().enumerate() {
        if c > 0 {
            let _ = writeln!(out, "status {d}xx {c}");
        }
    }
    for (template, mut lats) in entries {
        lats.sort_unstable();
        let n = lats.len();
        let p50 = lats[(50 * n).div_ceil(100) - 1];
        let p95 = lats[(95 * n).div_ceil(100) - 1];
        let mx = lats[n - 1];
        let t = std::str::from_utf8(&template).unwrap();
        let _ = writeln!(
            out,
            "path {t} {n} {}.{} {}.{} {}.{}",
            p50 / 10, p50 % 10, p95 / 10, p95 % 10, mx / 10, mx % 10
        );
    }
    let stdout = std::io::stdout();
    let mut lock = stdout.lock();
    let _ = lock.write_all(out.as_bytes());
}
