use std::collections::HashMap;
use std::hash::{BuildHasherDefault, Hasher};

#[derive(Default)]
struct Fx(u64);

impl Hasher for Fx {
    #[inline]
    fn write(&mut self, bytes: &[u8]) {
        let mut h = self.0;
        let mut chunks = bytes.chunks_exact(8);
        for c in &mut chunks {
            let w = u64::from_le_bytes(c.try_into().unwrap());
            h = (h.rotate_left(5) ^ w).wrapping_mul(0x517c_c1b7_2722_0a95);
        }
        for &b in chunks.remainder() {
            h = (h.rotate_left(5) ^ b as u64).wrapping_mul(0x517c_c1b7_2722_0a95);
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

const fn path_table() -> [bool; 256] {
    let mut t = [false; 256];
    let mut c = 0usize;
    while c < 256 {
        let b = c as u8;
        t[c] = b.is_ascii_alphanumeric() || b == b'_' || b == b'/' || b == b'-';
        c += 1;
    }
    t
}
static PATH_OK: [bool; 256] = path_table();

#[inline]
fn find_nl(buf: &[u8], from: usize) -> usize {
    const LO: u64 = 0x0101_0101_0101_0101;
    const HI: u64 = 0x8080_8080_8080_8080;
    const NL: u64 = LO * b'\n' as u64;
    let mut i = from;
    while i + 8 <= buf.len() {
        let w = u64::from_le_bytes(buf[i..i + 8].try_into().unwrap()) ^ NL;
        let m = w.wrapping_sub(LO) & !w & HI;
        if m != 0 {
            return i + (m.trailing_zeros() / 8) as usize;
        }
        i += 8;
    }
    while i < buf.len() {
        if buf[i] == b'\n' {
            return i;
        }
        i += 1;
    }
    buf.len()
}

#[inline]
fn dig(l: &[u8], i: usize) -> bool {
    l.get(i).is_some_and(|b| b.is_ascii_digit())
}

/// Returns (path, status first digit, latency in tenths) for a well-formed line.
fn parse(l: &[u8]) -> Option<(&[u8], u8, u64)> {
    let n = l.len();
    if n < 50 {
        return None;
    }
    for &i in &[0usize, 1, 2, 3, 5, 6, 8, 9, 11, 12, 14, 15, 17, 18, 20, 21, 22] {
        if !l[i].is_ascii_digit() {
            return None;
        }
    }
    if l[4] != b'-' || l[7] != b'-' || l[10] != b'T' || l[13] != b':' || l[16] != b':'
        || l[19] != b'.' || l[23] != b'Z' || l[24] != b' '
    {
        return None;
    }
    let mut i = 25;
    let s = i;
    while i < n && l[i].is_ascii_lowercase() {
        i += 1;
    }
    if i == s || l.get(i) != Some(&b'-') {
        return None;
    }
    i += 1;
    let s = i;
    while dig(l, i) {
        i += 1;
    }
    if i == s || l.get(i) != Some(&b' ') {
        return None;
    }
    i += 1;
    let rest = &l[i..];
    i += if rest.starts_with(b"GET ") {
        4
    } else if rest.starts_with(b"PUT ") {
        4
    } else if rest.starts_with(b"POST ") || rest.starts_with(b"PATCH ") {
        if rest[0] == b'P' && rest[1] == b'O' { 5 } else { 6 }
    } else if rest.starts_with(b"DELETE ") {
        7
    } else {
        return None;
    };
    if l.get(i) != Some(&b'/') {
        return None;
    }
    let ps = i;
    i += 1;
    while i < n && PATH_OK[l[i] as usize] {
        i += 1;
    }
    let path = &l[ps..i];
    match l.get(i) {
        Some(b'?') => {
            i += 1;
            while i < n && l[i] != b' ' {
                i += 1;
            }
            if i >= n {
                return None;
            }
        }
        Some(b' ') => {}
        _ => return None,
    }
    i += 1; // space
    if !(dig(l, i) && dig(l, i + 1) && dig(l, i + 2)) || l.get(i + 3) != Some(&b' ') {
        return None;
    }
    let status = l[i];
    i += 4;
    let s = i;
    while dig(l, i) {
        i += 1;
    }
    if i == s || l.get(i) != Some(&b'B') || l.get(i + 1) != Some(&b' ') {
        return None;
    }
    i += 2;
    let s = i;
    let mut v: u64 = 0;
    while dig(l, i) {
        v = v.wrapping_mul(10).wrapping_add((l[i] - b'0') as u64);
        i += 1;
    }
    if i == s || l.get(i) != Some(&b'.') || !dig(l, i + 1) {
        return None;
    }
    let lat = v.wrapping_mul(10).wrapping_add((l[i + 1] - b'0') as u64);
    i += 2;
    if l.get(i..i + 4) != Some(b"ms \"") {
        return None;
    }
    i += 3; // at opening quote
    if n < i + 2 || l[n - 1] != b'"' || l[i + 1..n - 1].contains(&b'"') {
        return None;
    }
    Some((path, status, lat))
}

fn main() {
    let path = std::env::args().nth(1).expect("input path");
    let data = std::fs::read(&path).expect("read input");

    let mut lines: u64 = 0;
    let mut good: u64 = 0;
    let mut status = [0u64; 10];
    let mut map: HashMap<Box<[u8]>, usize, BuildHasherDefault<Fx>> = HashMap::default();
    let mut names: Vec<Box<[u8]>> = Vec::new();
    let mut lats: Vec<Vec<u64>> = Vec::new();
    let mut scratch: Vec<u8> = Vec::with_capacity(256);

    let mut pos = 0;
    while pos < data.len() {
        let end = find_nl(&data, pos);
        let line = &data[pos..end];
        pos = end + 1;
        lines += 1;
        let Some((p, st, lat)) = parse(line) else { continue };
        good += 1;
        status[(st - b'0') as usize] += 1;

        scratch.clear();
        let mut seg_start = 0;
        let pl = p.len();
        loop {
            let mut e = seg_start;
            while e < pl && p[e] != b'/' {
                e += 1;
            }
            let seg = &p[seg_start..e];
            if !seg.is_empty() && seg.iter().all(|b| b.is_ascii_digit()) {
                scratch.extend_from_slice(b"{id}");
            } else {
                scratch.extend_from_slice(seg);
            }
            if e >= pl {
                break;
            }
            scratch.push(b'/');
            seg_start = e + 1;
        }
        let idx = match map.get(scratch.as_slice()) {
            Some(&i) => i,
            None => {
                let i = names.len();
                let b: Box<[u8]> = scratch.as_slice().into();
                map.insert(b.clone(), i);
                names.push(b);
                lats.push(Vec::new());
                i
            }
        };
        lats[idx].push(lat);
    }

    let mut out = String::new();
    out.push_str(&format!("lines {}\nmalformed {}\n", lines, lines - good));
    for (d, &c) in status.iter().enumerate() {
        if c > 0 {
            out.push_str(&format!("status {}xx {}\n", d, c));
        }
    }
    let mut order: Vec<usize> = (0..names.len()).collect();
    order.sort_by(|&a, &b| lats[b].len().cmp(&lats[a].len()).then_with(|| names[a].cmp(&names[b])));
    let fmt = |t: u64| format!("{}.{}", t / 10, t % 10);
    for &i in order.iter().take(10) {
        let v = &mut lats[i];
        v.sort_unstable();
        let n = v.len() as u128;
        let at = |p: u128| v[((p * n + 99) / 100) as usize - 1];
        out.push_str(&format!(
            "path {} {} {} {} {}\n",
            String::from_utf8_lossy(&names[i]),
            v.len(),
            fmt(at(50)),
            fmt(at(95)),
            fmt(*v.last().unwrap())
        ));
    }
    print!("{}", out);
}
