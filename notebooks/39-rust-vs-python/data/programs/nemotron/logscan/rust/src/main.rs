// Log scan summariser — Rust, single-threaded, release.
//
// Reads an access log, counts requests by status class and finds the busiest
// path templates with their latency p50/p95/max. Malformed lines (any line not
// matching the spec's regular expression in full) are counted but otherwise
// ignored.

use std::collections::HashMap;
use std::env;
use std::fs;
use std::io::{self, Write};

struct TemplateStats {
    count: u64,
    lats: Vec<u64>, // latency in tenths of a millisecond
}

fn all_digits(s: &[u8]) -> bool {
    s.iter().all(|&b| b.is_ascii_digit())
}

fn is_path_char(b: u8) -> bool {
    matches!(b, b'A'..=b'Z' | b'a'..=b'z' | b'0'..=b'9' | b'_' | b'/' | b'-')
}

// Parses one line (without its trailing newline) according to the spec's
// regex, in full. Returns (path, status class digit, latency tenths) or None
// for a malformed line. Every byte is validated, so this is equivalent to
// re.fullmatch on the line.
fn parse_line(line: &[u8]) -> Option<(&[u8], u8, u64)> {
    let n = line.len();

    // timestamp: \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z  then ' '
    if n < 25 || line[24] != b' ' {
        return None;
    }
    if !all_digits(&line[0..4]) || line[4] != b'-'
        || !all_digits(&line[5..7]) || line[7] != b'-'
        || !all_digits(&line[8..10]) || line[10] != b'T'
        || !all_digits(&line[11..13]) || line[13] != b':'
        || !all_digits(&line[14..16]) || line[16] != b':'
        || !all_digits(&line[17..19]) || line[19] != b'.'
        || !all_digits(&line[20..23]) || line[23] != b'Z'
    {
        return None;
    }

    // host: [a-z]+-\d+  then ' '
    let mut p = 25;
    let host_start = p;
    while p < n && line[p].is_ascii_lowercase() {
        p += 1;
    }
    if p == host_start || p >= n || line[p] != b'-' {
        return None;
    }
    p += 1;
    let dig_start = p;
    while p < n && line[p].is_ascii_digit() {
        p += 1;
    }
    if p == dig_start || p >= n || line[p] != b' ' {
        return None;
    }
    p += 1;

    // method: one of GET POST PUT DELETE PATCH, then ' '
    let meth_end = if line[p..].starts_with(b"GET") {
        p + 3
    } else if line[p..].starts_with(b"POST") {
        p + 4
    } else if line[p..].starts_with(b"PUT") {
        p + 3
    } else if line[p..].starts_with(b"DELETE") {
        p + 6
    } else if line[p..].starts_with(b"PATCH") {
        p + 5
    } else {
        return None;
    };
    if meth_end >= n || line[meth_end] != b' ' {
        return None;
    }
    p = meth_end + 1;

    // path: /[A-Za-z0-9_/-]*  (stops at ' ' or '?')
    let path_start = p;
    while p < n && line[p] != b' ' && line[p] != b'?' {
        if !is_path_char(line[p]) {
            return None;
        }
        p += 1;
    }
    if p == path_start {
        return None;
    }
    let path = &line[path_start..p];
    if path[0] != b'/' {
        return None;
    }

    // optional query string: ?[^ ]*
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

    // status: \d{3} then ' '
    if p + 3 > n || !all_digits(&line[p..p + 3]) {
        return None;
    }
    let class = line[p] - b'0';
    p += 3;
    if p >= n || line[p] != b' ' {
        return None;
    }
    p += 1;

    // size: \d+B then ' '
    let size_start = p;
    while p < n && line[p].is_ascii_digit() {
        p += 1;
    }
    if p == size_start || p >= n || line[p] != b'B' {
        return None;
    }
    p += 1;
    if p >= n || line[p] != b' ' {
        return None;
    }
    p += 1;

    // latency: \d+ \. \d ms "
    let int_start = p;
    while p < n && line[p].is_ascii_digit() {
        p += 1;
    }
    if p == int_start {
        return None;
    }
    let mut lat: u64 = 0;
    for &b in &line[int_start..p] {
        lat = lat.wrapping_mul(10).wrapping_add((b - b'0') as u64);
    }
    if p >= n || line[p] != b'.' {
        return None;
    }
    p += 1;
    if p >= n || !line[p].is_ascii_digit() {
        return None;
    }
    lat = lat.wrapping_mul(10).wrapping_add((line[p] - b'0') as u64);
    p += 1;
    if p + 4 > n
        || line[p] != b'm'
        || line[p + 1] != b's'
        || line[p + 2] != b' '
        || line[p + 3] != b'"'
    {
        return None;
    }
    p += 4;

    // user agent: "[^"]*" then end of line
    while p < n && line[p] != b'"' {
        p += 1;
    }
    if p >= n || line[p] != b'"' {
        return None;
    }
    p += 1;
    if p != n {
        return None;
    }

    Some((path, class, lat))
}

// Path template: split on '/', replace every non-empty all-digits segment
// with `{id}`, join back with '/'. All bytes here are ASCII (validated above).
fn path_template(path: &[u8]) -> String {
    // path starts with '/' (validated); keep it and template each segment.
    let mut out = String::with_capacity(path.len());
    out.push('/');
    let mut seg_start = 1usize;
    for (i, &b) in path.iter().enumerate().skip(1) {
        if b == b'/' {
            let seg = &path[seg_start..i];
            if !seg.is_empty() && all_digits(seg) {
                out.push_str("{id}");
            } else {
                out.push_str(unsafe { std::str::from_utf8_unchecked(seg) });
            }
            out.push('/');
            seg_start = i + 1;
        }
    }
    let seg = &path[seg_start..];
    if !seg.is_empty() && all_digits(seg) {
        out.push_str("{id}");
    } else {
        out.push_str(unsafe { std::str::from_utf8_unchecked(seg) });
    }
    out
}

fn nearest_rank(p: u64, n: usize) -> usize {
    // 1-based position ceil(p * n / 100), converted to 0-based index.
    ((p * n as u64 + 99) / 100) as usize - 1
}

fn fmt_lat(tenths: u64) -> String {
    format!("{}.{}", tenths / 10, tenths % 10)
}

fn feed(
    line: &[u8],
    lines: &mut u64,
    malformed: &mut u64,
    status: &mut [u64; 10],
    templates: &mut HashMap<String, TemplateStats>,
) {
    *lines += 1;
    if let Some((path, class, lat)) = parse_line(line) {
        status[class as usize] += 1;
        let t = path_template(path);
        let stats = templates
            .entry(t)
            .or_insert(TemplateStats {
                count: 0,
                lats: Vec::new(),
            });
        stats.count += 1;
        stats.lats.push(lat);
    } else {
        *malformed += 1;
    }
}

fn main() -> io::Result<()> {
    let input = env::args().nth(1).expect("usage: solution <input-file>");
    let data = fs::read(&input).unwrap_or_else(|e| {
        eprintln!("{e}");
        std::process::exit(1);
    });

    let mut lines: u64 = 0;
    let mut malformed: u64 = 0;
    let mut status = [0u64; 10];
    let mut templates: HashMap<String, TemplateStats> = HashMap::new();

    let mut start = 0usize;
    for (i, &b) in data.iter().enumerate() {
        if b != b'\n' {
            continue;
        }
        feed(&data[start..i], &mut lines, &mut malformed, &mut status, &mut templates);
        start = i + 1;
    }
    // A trailing newline means the last line was already handled above; any
    // remaining bytes (file not ending in '\n') form one last line.
    if start < data.len() {
        feed(&data[start..], &mut lines, &mut malformed, &mut status, &mut templates);
    }

    let mut out = String::with_capacity(4096);
    out.push_str(&format!("lines {}\n", lines));
    out.push_str(&format!("malformed {}\n", malformed));
    for class in 0..10u64 {
        let cnt = status[class as usize];
        if cnt > 0 {
            out.push_str(&format!("status {}xx {}\n", class, cnt));
        }
    }

    let mut items: Vec<(&str, u64, &[u64])> = templates
        .iter()
        .map(|(t, s)| (t.as_str(), s.count, &s.lats[..]))
        .collect();
    // Count descending, then template ascending in byte order.
    items.sort_by(|a, b| b.1.cmp(&a.1).then_with(|| a.0.cmp(b.0)));
    let limit = items.len().min(10);
    for item in &items[..limit] {
        let mut lats = item.2.to_vec();
        lats.sort_unstable();
        let n = lats.len();
        let p50 = lats[nearest_rank(50, n)];
        let p95 = lats[nearest_rank(95, n)];
        let mx = lats[n - 1];
        out.push_str(&format!(
            "path {} {} {} {} {}\n",
            item.0,
            item.1,
            fmt_lat(p50),
            fmt_lat(p95),
            fmt_lat(mx),
        ));
    }

    io::stdout().lock().write_all(out.as_bytes())?;
    Ok(())
}
