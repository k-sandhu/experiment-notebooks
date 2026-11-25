use std::collections::HashMap;
use std::fmt::Write as _;
use std::hash::{BuildHasherDefault, Hasher};

#[derive(Default)]
struct FnvHasher(u64);

impl Hasher for FnvHasher {
    #[inline]
    fn finish(&self) -> u64 {
        self.0
    }
    #[inline]
    fn write(&mut self, bytes: &[u8]) {
        let mut h = if self.0 == 0 { 0xcbf29ce484222325 } else { self.0 };
        for &b in bytes {
            h ^= b as u64;
            h = h.wrapping_mul(0x100000001b3);
        }
        self.0 = h;
    }
}

type FnvMap<K, V> = HashMap<K, V, BuildHasherDefault<FnvHasher>>;

#[inline(always)]
fn is_digit(b: u8) -> bool {
    b.wrapping_sub(b'0') < 10
}

#[inline(always)]
fn is_lower(b: u8) -> bool {
    b.wrapping_sub(b'a') < 26
}

#[inline(always)]
fn is_path_char(b: u8) -> bool {
    is_lower(b)
        || b.wrapping_sub(b'A') < 26
        || is_digit(b)
        || b == b'_'
        || b == b'-'
        || b == b'/'
}

fn valid_timestamp(ts: &[u8]) -> bool {
    ts.len() == 24
        && is_digit(ts[0])
        && is_digit(ts[1])
        && is_digit(ts[2])
        && is_digit(ts[3])
        && ts[4] == b'-'
        && is_digit(ts[5])
        && is_digit(ts[6])
        && ts[7] == b'-'
        && is_digit(ts[8])
        && is_digit(ts[9])
        && ts[10] == b'T'
        && is_digit(ts[11])
        && is_digit(ts[12])
        && ts[13] == b':'
        && is_digit(ts[14])
        && is_digit(ts[15])
        && ts[16] == b':'
        && is_digit(ts[17])
        && is_digit(ts[18])
        && ts[19] == b'.'
        && is_digit(ts[20])
        && is_digit(ts[21])
        && is_digit(ts[22])
        && ts[23] == b'Z'
}

fn valid_host(h: &[u8]) -> bool {
    let mut i = 0;
    let n = h.len();
    while i < n && is_lower(h[i]) {
        i += 1;
    }
    if i == 0 || i >= n || h[i] != b'-' {
        return false;
    }
    i += 1;
    if i >= n {
        return false;
    }
    while i < n {
        if !is_digit(h[i]) {
            return false;
        }
        i += 1;
    }
    true
}

fn valid_method(m: &[u8]) -> bool {
    m == b"GET" || m == b"POST" || m == b"PUT" || m == b"DELETE" || m == b"PATCH"
}

/// Returns (path, status class digit, latency in tenths of a millisecond).
fn parse_line(line: &[u8]) -> Option<(&[u8], u8, u128)> {
    if line.len() < 25 || line[24] != b' ' {
        return None;
    }
    let mut it = line.splitn(8, |&b| b == b' ');
    let ts = it.next()?;
    if !valid_timestamp(ts) {
        return None;
    }
    let host = it.next()?;
    if !valid_host(host) {
        return None;
    }
    let method = it.next()?;
    if !valid_method(method) {
        return None;
    }
    let target = it.next()?;
    if target.first() != Some(&b'/') {
        return None;
    }
    let path = match target.iter().position(|&b| b == b'?') {
        Some(i) => &target[..i],
        None => target,
    };
    if !path.iter().all(|&b| is_path_char(b)) {
        return None;
    }

    let status = it.next()?;
    if status.len() != 3
        || !is_digit(status[0])
        || !is_digit(status[1])
        || !is_digit(status[2])
    {
        return None;
    }

    let bytes_f = it.next()?;
    if bytes_f.len() < 2 || bytes_f[bytes_f.len() - 1] != b'B' {
        return None;
    }
    if !bytes_f[..bytes_f.len() - 1].iter().all(|&b| is_digit(b)) {
        return None;
    }

    let lat_f = it.next()?;
    if lat_f.len() < 5 || &lat_f[lat_f.len() - 2..] != b"ms" {
        return None;
    }
    let body = &lat_f[..lat_f.len() - 2];
    let dot = body.iter().position(|&b| b == b'.')?;
    let int_part = &body[..dot];
    let frac = &body[dot + 1..];
    if int_part.is_empty() || frac.len() != 1 || !is_digit(frac[0]) {
        return None;
    }
    let mut v: u128 = 0;
    for &c in int_part {
        if !is_digit(c) {
            return None;
        }
        v = v.saturating_mul(10).saturating_add((c - b'0') as u128);
    }
    v = v.saturating_mul(10).saturating_add((frac[0] - b'0') as u128);

    let ua = it.next()?;
    if ua.len() < 2 || ua[0] != b'"' || ua[ua.len() - 1] != b'"' {
        return None;
    }
    if ua.iter().filter(|&&b| b == b'"').count() != 2 {
        return None;
    }

    Some((path, status[0] - b'0', v))
}

struct Tmpl {
    name: Vec<u8>,
    lats: Vec<u128>,
}

fn main() {
    let path = std::env::args().nth(1).expect("usage: solution INPUT");
    let data = std::fs::read(&path).expect("read input");

    let mut status = [0u64; 10];
    let mut map: FnvMap<Vec<u8>, u32> = FnvMap::default();
    let mut tmpls: Vec<Tmpl> = Vec::new();
    let mut key: Vec<u8> = Vec::with_capacity(96);
    let mut total: u64 = 0;
    let mut valid: u64 = 0;

    for line in data.split(|&b| b == b'\n') {
        total += 1;
        let Some((p, class, lat)) = parse_line(line) else {
            continue;
        };
        valid += 1;
        status[class as usize] += 1;

        key.clear();
        let mut first = true;
        for seg in p.split(|&b| b == b'/') {
            if !first {
                key.push(b'/');
            }
            first = false;
            if !seg.is_empty() && seg.iter().all(|&b| is_digit(b)) {
                key.extend_from_slice(b"{id}");
            } else {
                key.extend_from_slice(seg);
            }
        }
        let idx = match map.get(key.as_slice()) {
            Some(&i) => i as usize,
            None => {
                let i = tmpls.len();
                tmpls.push(Tmpl {
                    name: key.clone(),
                    lats: Vec::new(),
                });
                map.insert(key.clone(), i as u32);
                i
            }
        };
        tmpls[idx].lats.push(lat);
    }

    // The final split element after the trailing newline is not a real line.
    if data.last() == Some(&b'\n') {
        total -= 1;
    }
    if data.is_empty() {
        total = 0;
    }
    let malformed = total - valid;

    let mut order: Vec<usize> = (0..tmpls.len()).collect();
    order.sort_unstable_by(|&a, &b| {
        tmpls[b]
            .lats
            .len()
            .cmp(&tmpls[a].lats.len())
            .then_with(|| tmpls[a].name.cmp(&tmpls[b].name))
    });
    order.truncate(10);

    let mut out = String::with_capacity(1024);
    let _ = writeln!(out, "lines {}", total);
    let _ = writeln!(out, "malformed {}", malformed);
    for c in 0..10u8 {
        if status[c as usize] != 0 {
            let _ = writeln!(out, "status {}xx {}", c, status[c as usize]);
        }
    }
    for &i in &order {
        let t = &mut tmpls[i];
        t.lats.sort_unstable();
        let n = t.lats.len();
        let p50 = t.lats[(50 * n + 99) / 100 - 1];
        let p95 = t.lats[(95 * n + 99) / 100 - 1];
        let max = t.lats[n - 1];
        let _ = write!(
            out,
            "path {} {} {}.{} {}.{} {}.{}\n",
            String::from_utf8_lossy(&t.name),
            n,
            p50 / 10,
            p50 % 10,
            p95 / 10,
            p95 % 10,
            max / 10,
            max % 10
        );
    }

    let stdout = std::io::stdout();
    let mut lock = stdout.lock();
    use std::io::Write as _;
    let _ = lock.write_all(out.as_bytes());
}
