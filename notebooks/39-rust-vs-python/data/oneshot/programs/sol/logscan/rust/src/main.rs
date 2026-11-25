use std::cmp::Ordering;
use std::collections::HashMap;
use std::fs;
use std::io::{self, Write};

const BIG_TAG: u64 = 1 << 63;

struct Parsed<'a> {
    path: &'a [u8],
    whole: &'a [u8],
    fractional: u8,
    class: usize,
}

struct LargeLatency<'a> {
    whole: &'a [u8],
    fractional: u8,
}

#[inline]
fn parse_line(s: &[u8]) -> Option<Parsed<'_>> {
    let n = s.len();
    if n < 25 {
        return None;
    }

    if s[4] != b'-'
        || s[7] != b'-'
        || s[10] != b'T'
        || s[13] != b':'
        || s[16] != b':'
        || s[19] != b'.'
        || s[23] != b'Z'
        || s[24] != b' '
    {
        return None;
    }

    for j in [
        0usize, 1, 2, 3, 5, 6, 8, 9, 11, 12, 14, 15, 17, 18, 20, 21, 22,
    ] {
        if !s[j].is_ascii_digit() {
            return None;
        }
    }

    let mut i = 25;
    let start = i;
    while i < n && s[i].is_ascii_lowercase() {
        i += 1;
    }
    if i == start || s.get(i) != Some(&b'-') {
        return None;
    }
    i += 1;

    let start = i;
    while i < n && s[i].is_ascii_digit() {
        i += 1;
    }
    if i == start || s.get(i) != Some(&b' ') {
        return None;
    }
    i += 1;

    let rest = &s[i..];
    let method_len = if rest.starts_with(b"GET ") || rest.starts_with(b"PUT ") {
        4
    } else if rest.starts_with(b"POST ") {
        5
    } else if rest.starts_with(b"PATCH ") {
        6
    } else if rest.starts_with(b"DELETE ") {
        7
    } else {
        return None;
    };
    i += method_len;

    if s.get(i) != Some(&b'/') {
        return None;
    }
    let path_start = i;
    i += 1;
    while i < n {
        let c = s[i];
        if c.is_ascii_alphanumeric() || c == b'_' || c == b'/' || c == b'-' {
            i += 1;
        } else {
            break;
        }
    }
    let path_end = i;

    if s.get(i) == Some(&b'?') {
        i += 1;
        while i < n && s[i] != b' ' {
            i += 1;
        }
    }
    if s.get(i) != Some(&b' ') {
        return None;
    }
    i += 1;

    if i + 4 > n
        || !s[i].is_ascii_digit()
        || !s[i + 1].is_ascii_digit()
        || !s[i + 2].is_ascii_digit()
        || s[i + 3] != b' '
    {
        return None;
    }
    let class = (s[i] - b'0') as usize;
    i += 4;

    let start = i;
    while i < n && s[i].is_ascii_digit() {
        i += 1;
    }
    if i == start || s.get(i..i + 2)? != b"B " {
        return None;
    }
    i += 2;

    let latency_start = i;
    while i < n && s[i].is_ascii_digit() {
        i += 1;
    }
    if i == latency_start || s.get(i) != Some(&b'.') {
        return None;
    }
    let latency_end = i;
    i += 1;

    let fractional = *s.get(i)?;
    if !fractional.is_ascii_digit() {
        return None;
    }
    i += 1;

    if s.get(i..i + 4)? != b"ms \"" {
        return None;
    }
    i += 4;

    if i >= n || s[n - 1] != b'"' || s[i..n - 1].contains(&b'"') {
        return None;
    }

    Some(Parsed {
        path: &s[path_start..path_end],
        whole: &s[latency_start..latency_end],
        fractional: fractional - b'0',
        class,
    })
}

#[inline]
fn encode_latency<'a>(
    whole: &'a [u8],
    fractional: u8,
    large: &mut Vec<LargeLatency<'a>>,
) -> u64 {
    let mut start = 0;
    while start < whole.len() && whole[start] == b'0' {
        start += 1;
    }
    let whole = &whole[start..];

    if whole.len() <= 18 {
        let mut value = 0u64;
        for &digit in whole {
            value = value * 10 + (digit - b'0') as u64;
        }
        value = value * 10 + fractional as u64;
        if value < BIG_TAG {
            return value;
        }
    }

    let index = large.len() as u64;
    large.push(LargeLatency { whole, fractional });
    BIG_TAG | index
}

#[inline]
fn compare_latency(a: u64, b: u64, large: &[LargeLatency<'_>]) -> Ordering {
    if (a & b & BIG_TAG) == 0 {
        return a.cmp(&b);
    }

    let a = &large[(a & !BIG_TAG) as usize];
    let b = &large[(b & !BIG_TAG) as usize];
    a.whole
        .len()
        .cmp(&b.whole.len())
        .then_with(|| a.whole.cmp(b.whole))
        .then_with(|| a.fractional.cmp(&b.fractional))
}

fn make_template(path: &[u8], buffer: &mut Vec<u8>) {
    buffer.clear();
    for (index, segment) in path.split(|&c| c == b'/').enumerate() {
        if index != 0 {
            buffer.push(b'/');
        }
        if !segment.is_empty() && segment.iter().all(u8::is_ascii_digit) {
            buffer.extend_from_slice(b"{id}");
        } else {
            buffer.extend_from_slice(segment);
        }
    }
}

type PathData = (Box<[u8]>, Vec<u64>);

fn compare_paths(a: &PathData, b: &PathData) -> Ordering {
    b.1.len()
        .cmp(&a.1.len())
        .then_with(|| a.0.cmp(&b.0))
}

fn statistics(values: &mut [u64], large: &[LargeLatency<'_>]) -> (u64, u64, u64) {
    let n = values.len();
    let p50_index = (n - 1) / 2;
    let p95_index = n - n / 20 - 1;

    if n <= 32 {
        values.sort_unstable_by(|a, b| compare_latency(*a, *b, large));
        return (values[p50_index], values[p95_index], values[n - 1]);
    }

    let (_, median, upper) =
        values.select_nth_unstable_by(p50_index, |a, b| compare_latency(*a, *b, large));
    let p50 = *median;

    let (_, percentile, tail) = upper.select_nth_unstable_by(
        p95_index - p50_index - 1,
        |a, b| compare_latency(*a, *b, large),
    );
    let p95 = *percentile;
    let mut maximum = p95;
    for &value in tail.iter() {
        if compare_latency(value, maximum, large) == Ordering::Greater {
            maximum = value;
        }
    }

    (p50, p95, maximum)
}

fn write_latency<W: Write>(
    out: &mut W,
    value: u64,
    large: &[LargeLatency<'_>],
) -> io::Result<()> {
    if value < BIG_TAG {
        write!(out, "{}.{}", value / 10, value % 10)
    } else {
        let value = &large[(value & !BIG_TAG) as usize];
        out.write_all(value.whole)?;
        out.write_all(&[b'.', b'0' + value.fractional])
    }
}

fn main() {
    let input_path = std::env::args_os().nth(1).unwrap();
    let input = fs::read(input_path).unwrap();

    let mut lines = 0u64;
    let mut malformed = 0u64;
    let mut statuses = [0u64; 10];
    let mut paths: HashMap<Box<[u8]>, Vec<u64>> = HashMap::new();
    let mut large = Vec::new();
    let mut template = Vec::with_capacity(128);

    if !input.is_empty() {
        for line in input[..input.len() - 1].split(|&c| c == b'\n') {
            lines += 1;
            let Some(parsed) = parse_line(line) else {
                malformed += 1;
                continue;
            };

            statuses[parsed.class] += 1;
            let latency = encode_latency(parsed.whole, parsed.fractional, &mut large);
            make_template(parsed.path, &mut template);

            if let Some(values) = paths.get_mut(template.as_slice()) {
                values.push(latency);
            } else {
                paths.insert(Box::<[u8]>::from(template.as_slice()), vec![latency]);
            }
        }
    }

    let mut busiest: Vec<PathData> = paths.into_iter().collect();
    if busiest.len() > 10 {
        busiest.select_nth_unstable_by(10, compare_paths);
        busiest.truncate(10);
    }
    busiest.sort_unstable_by(compare_paths);

    let stdout = io::stdout();
    let mut out = io::BufWriter::with_capacity(64 * 1024, stdout.lock());

    writeln!(out, "lines {}", lines).unwrap();
    writeln!(out, "malformed {}", malformed).unwrap();

    for (class, &count) in statuses.iter().enumerate() {
        if count != 0 {
            writeln!(out, "status {}xx {}", class, count).unwrap();
        }
    }

    for (path, mut values) in busiest {
        let count = values.len();
        let (p50, p95, maximum) = statistics(&mut values, &large);
        write!(
            out,
            "path {} {} ",
            std::str::from_utf8(&path).unwrap(),
            count
        )
        .unwrap();
        write_latency(&mut out, p50, &large).unwrap();
        out.write_all(b" ").unwrap();
        write_latency(&mut out, p95, &large).unwrap();
        out.write_all(b" ").unwrap();
        write_latency(&mut out, maximum, &large).unwrap();
        out.write_all(b"\n").unwrap();
    }

    out.flush().unwrap();
}
