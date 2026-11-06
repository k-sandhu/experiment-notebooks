use std::collections::HashMap;
use std::env;
use std::fmt::Write as _;
use std::fs;
use std::io::{self, Write as _};

#[inline(always)]
fn dig(b: u8) -> bool {
    b.is_ascii_digit()
}

struct Stat {
    count: u64,
    lats: Vec<u128>,
}

/// Hand-rolled exact equivalent of the SPEC.md line regex.
/// Returns (status first digit, path bytes, latency in tenths of a millisecond).
fn parse_line(l: &[u8]) -> Option<(u8, &[u8], u128)> {
    let n = l.len();
    // Shortest possible well-formed line is 51 bytes.
    if n < 51 {
        return None;
    }
    // Fixed 25-byte timestamp prefix: \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z
    if !(dig(l[0]) && dig(l[5]) && dig(l[8]) && dig(l[11]) && dig(l[14]) && dig(l[17])
        && dig(l[20]) && dig(l[21]) && dig(l[22]))
    {
        return None;
    }
    if l[4] != b'-' || l[7] != b'-' || l[10] != b'T' || l[13] != b':' || l[16] != b':'
        || l[19] != b'.' || l[23] != b'Z' || l[24] != b' '
    {
        return None;
    }
    // Host: [a-z]+-\d+ followed by a space.
    let mut i = 25;
    let h0 = i;
    while i < n && l[i].is_ascii_lowercase() {
        i += 1;
    }
    if i == h0 || i >= n || l[i] != b'-' {
        return None;
    }
    i += 1;
    let d0 = i;
    while i < n && dig(l[i]) {
        i += 1;
    }
    if i == d0 || i >= n || l[i] != b' ' {
        return None;
    }
    i += 1;
    // Method.
    let rest = &l[i..];
    let mlen = if rest.starts_with(b"DELETE ") {
        7
    } else if rest.starts_with(b"PATCH ") {
        6
    } else if rest.starts_with(b"POST ") {
        5
    } else if rest.starts_with(b"GET ") || rest.starts_with(b"PUT ") {
        4
    } else {
        return None;
    };
    i += mlen;
    // Path: /([A-Za-z0-9_/-]*) then optional \?[^ ]* then a space.
    if i >= n || l[i] != b'/' {
        return None;
    }
    let ps = i;
    i += 1;
    while i < n
        && matches!(l[i], b'A'..=b'Z' | b'a'..=b'z' | b'0'..=b'9' | b'_' | b'/' | b'-')
    {
        i += 1;
    }
    let pe = i;
    if i < n && l[i] == b'?' {
        i += 1;
        while i < n && l[i] != b' ' {
            i += 1;
        }
    }
    if i >= n || l[i] != b' ' {
        return None;
    }
    let pb = &l[ps..pe];
    i += 1;
    // Status: exactly 3 digits.
    if i + 4 > n || !(dig(l[i]) && dig(l[i + 1]) && dig(l[i + 2]) && l[i + 3] == b' ') {
        return None;
    }
    let st0 = l[i];
    i += 4;
    // Size: \d+B followed by a space.
    let z0 = i;
    while i < n && dig(l[i]) {
        i += 1;
    }
    if i == z0 || i + 2 > n || l[i] != b'B' || l[i + 1] != b' ' {
        return None;
    }
    i += 2;
    // Latency: (\d+)\.(\d)ms followed by a space and the quoted user agent.
    let t0 = i;
    let mut val: u128 = 0;
    while i < n && dig(l[i]) {
        val = val.checked_mul(10)?.checked_add((l[i] - b'0') as u128)?;
        i += 1;
    }
    if i == t0 || i + 6 > n {
        return None;
    }
    if l[i] != b'.'
        || !dig(l[i + 1])
        || l[i + 2] != b'm'
        || l[i + 3] != b's'
        || l[i + 4] != b' '
        || l[i + 5] != b'"'
    {
        return None;
    }
    val = val.checked_mul(10)?.checked_add((l[i + 1] - b'0') as u128)?;
    // User agent: "[^"]*" ending exactly at end of line.
    let mut q = i + 6;
    while q < n && l[q] != b'"' {
        q += 1;
    }
    if q != n - 1 {
        return None;
    }
    Some((st0, pb, val))
}

fn main() {
    let arg = env::args().nth(1).unwrap_or_else(|| {
        eprintln!("usage: solution <input>");
        std::process::exit(2);
    });
    let data = fs::read(&arg).unwrap_or_else(|e| {
        eprintln!("cannot read {arg}: {e}");
        std::process::exit(2);
    });

    let mut lines: u64 = 0;
    let mut ok: u64 = 0;
    let mut classes = [0u64; 10];
    let mut paths: HashMap<Vec<u8>, Stat> = HashMap::with_capacity(64);
    let mut tpl: Vec<u8> = Vec::with_capacity(64);

    for raw in data.split_inclusive(|&b| b == b'\n') {
        let line: &[u8] = if raw.last() == Some(&b'\n') {
            &raw[..raw.len() - 1]
        } else {
            raw
        };
        lines += 1;
        if let Some((st0, pb, t)) = parse_line(line) {
            ok += 1;
            classes[(st0 - b'0') as usize] += 1;
            // Template: split on '/', digit-only segments become {id}.
            let key: &[u8] = if pb.iter().any(|&b| dig(b)) {
                tpl.clear();
                tpl.push(b'/');
                let mut first = true;
                for seg in pb[1..].split(|&b| b == b'/') {
                    if !first {
                        tpl.push(b'/');
                    }
                    first = false;
                    if !seg.is_empty() && seg.iter().all(|&b| dig(b)) {
                        tpl.extend_from_slice(b"{id}");
                    } else {
                        tpl.extend_from_slice(seg);
                    }
                }
                &tpl
            } else {
                pb
            };
            match paths.get_mut(key) {
                Some(st) => {
                    st.count += 1;
                    st.lats.push(t);
                }
                None => {
                    paths.insert(
                        key.to_vec(),
                        Stat {
                            count: 1,
                            lats: vec![t],
                        },
                    );
                }
            }
        }
    }

    let mut rows: Vec<(u64, Vec<u8>, Vec<u128>)> = paths
        .into_iter()
        .map(|(k, s)| (s.count, k, s.lats))
        .collect();
    rows.sort_unstable_by(|a, b| b.0.cmp(&a.0).then_with(|| a.1.cmp(&b.1)));

    let mut out = String::with_capacity(1 << 16);
    let _ = write!(out, "lines {lines}\nmalformed {}\n", lines - ok);
    for (c, &cnt) in classes.iter().enumerate() {
        if cnt > 0 {
            let _ = write!(out, "status {c}xx {cnt}\n");
        }
    }
    for (count, k, mut lats) in rows.into_iter().take(10) {
        let n = lats.len();
        lats.sort_unstable();
        let p50 = lats[(50 * n + 99) / 100 - 1];
        let p95 = lats[(95 * n + 99) / 100 - 1];
        let mx = lats[n - 1];
        let name = std::str::from_utf8(&k).unwrap_or_default();
        let _ = write!(
            out,
            "path {name} {count} {}.{} {}.{} {}.{}\n",
            p50 / 10,
            p50 % 10,
            p95 / 10,
            p95 % 10,
            mx / 10,
            mx % 10
        );
    }

    let stdout = io::stdout();
    let mut h = stdout.lock();
    let _ = h.write_all(out.as_bytes());
    let _ = h.flush();
}
