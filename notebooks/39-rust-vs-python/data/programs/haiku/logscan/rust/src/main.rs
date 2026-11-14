//! Web access log summary: status-class counts and the busiest path templates
//! with latency percentiles. One streaming pass over the file, single thread.
//!
//! Lines are checked with a hand-written byte parser that accepts exactly the
//! language of the SPEC regex, which is much cheaper than running `regex` per line.

use std::collections::HashMap;
use std::error::Error;
use std::fmt::Write as _;
use std::fs::File;
use std::hash::{BuildHasherDefault, Hasher};
use std::io::{self, Read, Write};
use std::process::ExitCode;

/// Bytes read from the file per step.
const CHUNK: usize = 1 << 20;
/// Shape of the timestamp: `d` is a digit, anything else is a literal.
const TS_PATTERN: &[u8; 24] = b"dddd-dd-ddTdd:dd:dd.dddZ";
const METHODS: [&[u8]; 5] = [b"GET ", b"POST ", b"PUT ", b"DELETE ", b"PATCH "];
const LAT_TOO_LARGE: &str = "latency does not fit in 64-bit tenths of a millisecond";

/// FNV-1a: a cheap hash for the short template keys.
struct Fnv(u64);

impl Default for Fnv {
    fn default() -> Self {
        Fnv(0xcbf2_9ce4_8422_2325)
    }
}

impl Hasher for Fnv {
    fn finish(&self) -> u64 {
        self.0
    }

    fn write(&mut self, bytes: &[u8]) {
        for &b in bytes {
            self.0 = (self.0 ^ b as u64).wrapping_mul(0x0100_0000_01b3);
        }
    }
}

type FastMap<K, V> = HashMap<K, V, BuildHasherDefault<Fnv>>;

struct Group {
    name: Vec<u8>,
    lats: Vec<u64>,
}

#[derive(Default)]
struct Scan {
    lines: u64,
    malformed: u64,
    status: [u64; 10],
    index: FastMap<Vec<u8>, usize>,
    groups: Vec<Group>,
    tpl: Vec<u8>,
}

fn is_timestamp(t: &[u8]) -> bool {
    t.iter()
        .zip(TS_PATTERN)
        .all(|(&c, &p)| if p == b'd' { c.is_ascii_digit() } else { c == p })
}

/// Parses one line without its newline. `Ok(None)` means the line is malformed.
/// On success returns the status class digit, the path without query, and the
/// latency in tenths of a millisecond.
fn parse(line: &[u8]) -> Result<Option<(u8, &[u8], u64)>, &'static str> {
    let n = line.len();
    if n < 25 || line[24] != b' ' || !is_timestamp(&line[..24]) {
        return Ok(None);
    }
    let mut i = 25;

    // host: [a-z]+-[0-9]+ followed by a space
    let start = i;
    while i < n && line[i].is_ascii_lowercase() {
        i += 1;
    }
    if i == start || i >= n || line[i] != b'-' {
        return Ok(None);
    }
    i += 1;
    let start = i;
    while i < n && line[i].is_ascii_digit() {
        i += 1;
    }
    if i == start || i >= n || line[i] != b' ' {
        return Ok(None);
    }
    i += 1;

    // method, including its trailing space
    match METHODS.iter().find(|m| line[i..].starts_with(m)) {
        Some(m) => i += m.len(),
        None => return Ok(None),
    }

    // path [/A-Za-z0-9_-]*, optional ?query (no spaces), then a space
    if i >= n || line[i] != b'/' {
        return Ok(None);
    }
    let path_start = i;
    while i < n && (line[i].is_ascii_alphanumeric() || matches!(line[i], b'_' | b'/' | b'-')) {
        i += 1;
    }
    let path = &line[path_start..i];
    if i < n && line[i] == b'?' {
        while i < n && line[i] != b' ' {
            i += 1;
        }
    }
    if i >= n || line[i] != b' ' {
        return Ok(None);
    }
    i += 1;

    // status: three digits and a space
    if i + 4 > n || !line[i..i + 3].iter().all(u8::is_ascii_digit) || line[i + 3] != b' ' {
        return Ok(None);
    }
    let class = line[i] - b'0';
    i += 4;

    // size: digits, 'B', space
    let start = i;
    while i < n && line[i].is_ascii_digit() {
        i += 1;
    }
    if i == start || i + 2 > n || line[i] != b'B' || line[i + 1] != b' ' {
        return Ok(None);
    }
    i += 2;

    // latency: digits '.' digit "ms" space
    let int_start = i;
    while i < n && line[i].is_ascii_digit() {
        i += 1;
    }
    let int_part = &line[int_start..i];
    if int_part.is_empty()
        || i + 5 > n
        || line[i] != b'.'
        || !line[i + 1].is_ascii_digit()
        || &line[i + 2..i + 4] != b"ms"
        || line[i + 4] != b' '
    {
        return Ok(None);
    }
    let frac = line[i + 1] - b'0';
    i += 5;

    // user agent: "[^"]*" running to the end of the line
    let ua = &line[i..];
    if ua.len() < 2 || ua[0] != b'"' || ua[ua.len() - 1] != b'"' || ua[1..ua.len() - 1].contains(&b'"') {
        return Ok(None);
    }

    let mut tenths: u64 = 0;
    for &d in int_part {
        tenths = tenths
            .checked_mul(10)
            .and_then(|v| v.checked_add((d - b'0') as u64))
            .ok_or(LAT_TOO_LARGE)?;
    }
    tenths = tenths
        .checked_mul(10)
        .and_then(|v| v.checked_add(frac as u64))
        .ok_or(LAT_TOO_LARGE)?;
    Ok(Some((class, path, tenths)))
}

/// Writes the path template (digit-only segments become `{id}`) into `out`.
fn template(path: &[u8], out: &mut Vec<u8>) {
    out.clear();
    for (k, seg) in path.split(|&c| c == b'/').enumerate() {
        if k > 0 {
            out.push(b'/');
        }
        if !seg.is_empty() && seg.iter().all(u8::is_ascii_digit) {
            out.extend_from_slice(b"{id}");
        } else {
            out.extend_from_slice(seg);
        }
    }
}

impl Scan {
    fn line(&mut self, line: &[u8]) -> Result<(), &'static str> {
        self.lines += 1;
        let Some((class, path, tenths)) = parse(line)? else {
            self.malformed += 1;
            return Ok(());
        };
        self.status[class as usize] += 1;
        template(path, &mut self.tpl);
        let id = if let Some(&id) = self.index.get(self.tpl.as_slice()) {
            id
        } else {
            let id = self.groups.len();
            self.groups.push(Group { name: self.tpl.clone(), lats: Vec::new() });
            self.index.insert(self.tpl.clone(), id);
            id
        };
        self.groups[id].lats.push(tenths);
        Ok(())
    }
}

/// Feeds complete lines; `body` holds the lines joined by `\n`, without a final newline.
fn feed(scan: &mut Scan, body: &[u8]) -> Result<(), &'static str> {
    for line in body.split(|&c| c == b'\n') {
        scan.line(line)?;
    }
    Ok(())
}

/// Nearest-rank percentile: the element at 1-based position ceil(p * n / 100).
fn nearest_rank(v: &mut [u64], p: usize) -> u64 {
    let k = (p * v.len() + 99) / 100;
    *v.select_nth_unstable(k - 1).1
}

/// Formats tenths of a millisecond with one decimal place.
fn tenths(t: u64) -> String {
    format!("{}.{}", t / 10, t % 10)
}

fn report(scan: &mut Scan) -> String {
    let mut out = String::new();
    let _ = writeln!(out, "lines {}", scan.lines);
    let _ = writeln!(out, "malformed {}", scan.malformed);
    for (class, &count) in scan.status.iter().enumerate() {
        if count > 0 {
            let _ = writeln!(out, "status {class}xx {count}");
        }
    }

    let mut order: Vec<usize> = (0..scan.groups.len()).collect();
    order.sort_unstable_by(|&a, &b| {
        let (ga, gb) = (&scan.groups[a], &scan.groups[b]);
        gb.lats.len().cmp(&ga.lats.len()).then_with(|| ga.name.cmp(&gb.name))
    });
    for &id in order.iter().take(10) {
        let g = &mut scan.groups[id];
        let n = g.lats.len();
        let max = *g.lats.iter().max().unwrap();
        let p50 = nearest_rank(&mut g.lats, 50);
        let p95 = nearest_rank(&mut g.lats, 95);
        let _ = writeln!(
            out,
            "path {} {} {} {} {}",
            String::from_utf8_lossy(&g.name),
            n,
            tenths(p50),
            tenths(p95),
            tenths(max)
        );
    }
    out
}

fn run() -> Result<(), Box<dyn Error>> {
    let path = std::env::args_os().nth(1).ok_or("usage: solution INPUT_PATH")?;
    let mut file = File::open(path)?;
    let mut scan = Scan::default();
    let mut chunk = vec![0u8; CHUNK];
    let mut pending: Vec<u8> = Vec::with_capacity(2 * CHUNK);

    loop {
        let n = match file.read(&mut chunk) {
            Ok(0) => break,
            Ok(n) => n,
            Err(e) if e.kind() == io::ErrorKind::Interrupted => continue,
            Err(e) => return Err(e.into()),
        };
        pending.extend_from_slice(&chunk[..n]);
        if let Some(end) = pending.iter().rposition(|&c| c == b'\n') {
            feed(&mut scan, &pending[..end])?;
            pending.drain(..=end);
        }
    }
    if !pending.is_empty() {
        // A final line without its newline still counts as a line.
        pending.push(b'\n');
        let end = pending.len() - 1;
        feed(&mut scan, &pending[..end])?;
    }

    let text = report(&mut scan);
    io::stdout().lock().write_all(text.as_bytes())?;
    Ok(())
}

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(e) => {
            eprintln!("error: {e}");
            ExitCode::FAILURE
        }
    }
}
