use std::collections::HashMap;
use std::hash::{BuildHasherDefault, Hasher};
use std::io::Write;

// Small FNV-1a hasher: std's SipHash is needlessly slow for short byte keys.
#[derive(Default)]
struct FnvHasher(u64);

impl Hasher for FnvHasher {
    #[inline]
    fn finish(&self) -> u64 {
        self.0
    }
    #[inline]
    fn write(&mut self, bytes: &[u8]) {
        let mut h = if self.0 == 0 {
            0xcbf2_9ce4_8422_2325
        } else {
            self.0
        };
        for &b in bytes {
            h ^= b as u64;
            h = h.wrapping_mul(0x0000_0100_0000_01b3);
        }
        self.0 = h;
    }
}

type FastMap<K, V> = HashMap<K, V, BuildHasherDefault<FnvHasher>>;

#[inline(always)]
fn is_digit(b: u8) -> bool {
    b.is_ascii_digit()
}

/// Validate one line against the spec regex and, if well-formed, return
/// (status first digit, path, latency in tenths of a ms).
#[inline]
fn parse(line: &[u8]) -> Option<(u8, &[u8], u64)> {
    let len = line.len();
    // Timestamp: 24 fixed chars plus the following space at index 24.
    if len < 25 {
        return None;
    }
    if line[4] != b'-'
        || line[7] != b'-'
        || line[10] != b'T'
        || line[13] != b':'
        || line[16] != b':'
        || line[19] != b'.'
        || line[23] != b'Z'
        || line[24] != b' '
    {
        return None;
    }
    for &i in &[
        0usize, 1, 2, 3, 5, 6, 8, 9, 11, 12, 14, 15, 17, 18, 20, 21, 22,
    ] {
        if !is_digit(line[i]) {
            return None;
        }
    }
    let mut pos = 25usize;

    // Server: [a-z]+ - \d+
    let start = pos;
    while pos < len && line[pos].is_ascii_lowercase() {
        pos += 1;
    }
    if pos == start || pos >= len || line[pos] != b'-' {
        return None;
    }
    pos += 1;
    let start = pos;
    while pos < len && is_digit(line[pos]) {
        pos += 1;
    }
    if pos == start || pos >= len || line[pos] != b' ' {
        return None;
    }
    pos += 1;

    // Method token up to the next space.
    let start = pos;
    while pos < len && line[pos] != b' ' {
        pos += 1;
    }
    if pos >= len {
        return None;
    }
    match &line[start..pos] {
        b"GET" | b"POST" | b"PUT" | b"DELETE" | b"PATCH" => {}
        _ => return None,
    }
    pos += 1;

    // Path: / [A-Za-z0-9_/-]*
    if pos >= len || line[pos] != b'/' {
        return None;
    }
    let path_start = pos;
    pos += 1;
    while pos < len
        && (line[pos].is_ascii_alphanumeric()
            || line[pos] == b'_'
            || line[pos] == b'/'
            || line[pos] == b'-')
    {
        pos += 1;
    }
    let path = &line[path_start..pos];

    // Optional query: ? [^ ]*
    if pos < len && line[pos] == b'?' {
        pos += 1;
        while pos < len && line[pos] != b' ' {
            pos += 1;
        }
    }
    if pos >= len || line[pos] != b' ' {
        return None;
    }
    pos += 1;

    // Status: exactly 3 digits then a space.
    if pos + 3 >= len
        || !is_digit(line[pos])
        || !is_digit(line[pos + 1])
        || !is_digit(line[pos + 2])
        || line[pos + 3] != b' '
    {
        return None;
    }
    let status_digit = line[pos] - b'0';
    pos += 4;

    // Response size: \d+ B
    let start = pos;
    while pos < len && is_digit(line[pos]) {
        pos += 1;
    }
    if pos == start || pos + 1 >= len || line[pos] != b'B' || line[pos + 1] != b' ' {
        return None;
    }
    pos += 2;

    // Latency: (\d+) \. (\d) ms
    let start = pos;
    let mut whole: u128 = 0;
    while pos < len && is_digit(line[pos]) {
        whole = whole.saturating_mul(10).saturating_add((line[pos] - b'0') as u128);
        pos += 1;
    }
    if pos == start
        || pos + 4 >= len
        || line[pos] != b'.'
        || !is_digit(line[pos + 1])
        || line[pos + 2] != b'm'
        || line[pos + 3] != b's'
        || line[pos + 4] != b' '
    {
        return None;
    }
    let latency128 = whole * 10 + (line[pos + 1] - b'0') as u128;
    let latency = latency128.min(u64::MAX as u128) as u64;
    pos += 5;

    // User agent: " [^"]* " at end of line.
    if pos >= len || line[pos] != b'"' || pos + 1 >= len || line[len - 1] != b'"' {
        return None;
    }
    for &b in &line[pos + 1..len - 1] {
        if b == b'"' {
            return None;
        }
    }

    Some((status_digit, path, latency))
}

fn main() {
    let path_arg = std::env::args().nth(1).expect("usage: solution INPUT");
    let data = std::fs::read(&path_arg).expect("cannot read input");

    let mut total: u64 = 0;
    let mut malformed: u64 = 0;
    let mut status = [0u64; 10];
    let mut agg: FastMap<Vec<u8>, Vec<u64>> = FastMap::default();
    let mut templ: Vec<u8> = Vec::with_capacity(64);

    let handle_line = |line: &[u8],
                           total: &mut u64,
                           malformed: &mut u64,
                           status: &mut [u64; 10],
                           agg: &mut FastMap<Vec<u8>, Vec<u64>>,
                           templ: &mut Vec<u8>| {
        *total += 1;
        match parse(line) {
            Some((digit, pth, lat)) => {
                status[digit as usize] += 1;
                // Build template: digit-only segments become {id}.
                templ.clear();
                let mut seg_start = 0usize;
                let mut i = 0usize;
                loop {
                    if i == pth.len() || pth[i] == b'/' {
                        let seg = &pth[seg_start..i];
                        if !seg.is_empty() && seg.iter().all(|&b| is_digit(b)) {
                            templ.extend_from_slice(b"{id}");
                        } else {
                            templ.extend_from_slice(seg);
                        }
                        if i < pth.len() {
                            templ.push(b'/');
                        }
                        seg_start = i + 1;
                        if i == pth.len() {
                            break;
                        }
                    }
                    i += 1;
                }
                match agg.get_mut(templ.as_slice()) {
                    Some(v) => v.push(lat),
                    None => {
                        agg.insert(templ.clone(), vec![lat]);
                    }
                }
            }
            None => *malformed += 1,
        }
    };

    let mut start = 0usize;
    for i in 0..data.len() {
        if data[i] == b'\n' {
            handle_line(
                &data[start..i],
                &mut total,
                &mut malformed,
                &mut status,
                &mut agg,
                &mut templ,
            );
            start = i + 1;
        }
    }
    if start < data.len() {
        handle_line(
            &data[start..],
            &mut total,
            &mut malformed,
            &mut status,
            &mut agg,
            &mut templ,
        );
    }

    // Top 10 templates: count descending, then template ascending.
    let mut entries: Vec<(Vec<u8>, Vec<u64>)> = agg.into_iter().collect();
    entries.sort_unstable_by(|a, b| {
        b.1.len()
            .cmp(&a.1.len())
            .then_with(|| a.0.cmp(&b.0))
    });
    entries.truncate(10);

    let mut out = String::new();
    out.push_str(&format!("lines {total}\n"));
    out.push_str(&format!("malformed {malformed}\n"));
    for (d, &c) in status.iter().enumerate() {
        if c > 0 {
            out.push_str(&format!("status {d}xx {c}\n"));
        }
    }
    for (name, mut lats) in entries {
        let n = lats.len();
        lats.sort_unstable();
        let p50 = lats[(50 * n + 99) / 100 - 1];
        let p95 = lats[(95 * n + 99) / 100 - 1];
        let mx = lats[n - 1];
        // name is pure ASCII per the path character class.
        out.push_str(&format!(
            "path {} {} {}.{} {}.{} {}.{}\n",
            // SAFETY-free lossy conversion; bytes are ASCII so it is exact.
            String::from_utf8_lossy(&name),
            n,
            p50 / 10,
            p50 % 10,
            p95 / 10,
            p95 % 10,
            mx / 10,
            mx % 10
        ));
    }

    let stdout = std::io::stdout();
    let mut lock = stdout.lock();
    let _ = lock.write_all(out.as_bytes());
}
