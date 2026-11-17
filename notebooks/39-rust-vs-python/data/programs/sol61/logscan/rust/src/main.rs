use std::collections::HashMap;
use std::fs::File;
use std::io::{self, BufRead, BufReader, Write};

#[derive(Default)]
struct Latencies {
    small: Vec<u64>,
    // Canonical decimal integers, used only when a latency exceeds u64.
    big: Vec<Box<[u8]>>,
}

impl Latencies {
    fn len(&self) -> usize {
        self.small.len() + self.big.len()
    }

    fn push(&mut self, mut whole: &[u8], fraction: u8) {
        if whole.len() > 18 {
            let first = whole.iter().position(|&b| b != b'0').unwrap_or(whole.len());
            whole = &whole[first..];
        }
        if whole.len() <= 19 {
            let mut value = 0u64;
            for &b in whole {
                value = value * 10 + u64::from(b - b'0');
            }
            if let Some(value) = value
                .checked_mul(10)
                .and_then(|v| v.checked_add(u64::from(fraction)))
            {
                self.small.push(value);
                return;
            }
        }
        let mut decimal = Vec::with_capacity(whole.len() + 1);
        decimal.extend_from_slice(whole);
        decimal.push(b'0' + fraction);
        self.big.push(decimal.into_boxed_slice());
    }

    fn percentile(&mut self, rank: usize) -> String {
        if rank < self.small.len() {
            let (_, value, _) = self.small.select_nth_unstable(rank);
            format_small(*value)
        } else {
            format_big(&self.big[rank - self.small.len()])
        }
    }

    fn summary(&mut self) -> (String, String, String) {
        let n = self.len();
        self.big
            .sort_unstable_by(|a, b| a.len().cmp(&b.len()).then_with(|| a.cmp(b)));
        let maximum = match self.big.last() {
            Some(value) => format_big(value),
            None => format_small(*self.small.iter().max().unwrap()),
        };
        let p50 = self.percentile((n - 1) / 2);
        let p95 = self.percentile(n - n / 20 - 1);
        (p50, p95, maximum)
    }
}

fn format_small(value: u64) -> String {
    format!("{}.{:01}", value / 10, value % 10)
}

fn format_big(value: &[u8]) -> String {
    let n = value.len();
    let mut result = String::with_capacity(n + 1);
    result.push_str(std::str::from_utf8(&value[..n - 1]).unwrap());
    result.push('.');
    result.push(char::from(value[n - 1]));
    result
}

const fn path_characters() -> [bool; 256] {
    let mut table = [false; 256];
    let mut i = 0;
    while i < 256 {
        let c = i as u8;
        table[i] = c.is_ascii_alphanumeric() || c == b'_' || c == b'/' || c == b'-';
        i += 1;
    }
    table
}

const PATH_CHAR: [bool; 256] = path_characters();

#[inline]
fn digits(s: &[u8], pos: &mut usize) -> bool {
    let start = *pos;
    while *pos < s.len() && s[*pos].is_ascii_digit() {
        *pos += 1;
    }
    *pos != start
}

#[inline]
fn literal(s: &[u8], pos: &mut usize, expected: &[u8]) -> bool {
    if s.get(*pos..*pos + expected.len()) != Some(expected) {
        return false;
    }
    *pos += expected.len();
    true
}

struct Record<'a> {
    path: &'a [u8],
    class: usize,
    whole: &'a [u8],
    fraction: u8,
}

// Validate the full grammar, without allocating or interpreting dates/byte counts.
#[inline]
fn parse(s: &[u8]) -> Option<Record<'_>> {
    if s.len() < 50 {
        return None;
    }
    for (&actual, &expected) in s[..25].iter().zip(b"0000-00-00T00:00:00.000Z ") {
        if if expected == b'0' {
            !actual.is_ascii_digit()
        } else {
            actual != expected
        } {
            return None;
        }
    }
    let mut i = 25;
    let host_start = i;
    while i < s.len() && s[i].is_ascii_lowercase() {
        i += 1;
    }
    if i == host_start
        || !literal(s, &mut i, b"-")
        || !digits(s, &mut i)
        || !literal(s, &mut i, b" ")
    {
        return None;
    }
    let method_start = i;
    while i < s.len() && s[i] != b' ' {
        i += 1;
    }
    if !matches!(
        &s[method_start..i],
        b"GET" | b"POST" | b"PUT" | b"DELETE" | b"PATCH"
    ) || !literal(s, &mut i, b" ")
    {
        return None;
    }
    let path_start = i;
    if !literal(s, &mut i, b"/") {
        return None;
    }
    while i < s.len() && PATH_CHAR[s[i] as usize] {
        i += 1;
    }
    let path_end = i;
    if s.get(i) == Some(&b'?') {
        i += 1;
        while i < s.len() && s[i] != b' ' {
            i += 1;
        }
    }
    if !literal(s, &mut i, b" ") {
        return None;
    }
    let status = s.get(i..i + 3)?;
    if !status.iter().all(u8::is_ascii_digit) {
        return None;
    }
    let class = (status[0] - b'0') as usize;
    i += 3;
    if !literal(s, &mut i, b" ") || !digits(s, &mut i) || !literal(s, &mut i, b"B ") {
        return None;
    }
    let whole_start = i;
    if !digits(s, &mut i) {
        return None;
    }
    let whole = &s[whole_start..i];
    if !literal(s, &mut i, b".") {
        return None;
    }
    let fraction = *s.get(i)?;
    if !fraction.is_ascii_digit() {
        return None;
    }
    i += 1;
    if !literal(s, &mut i, b"ms \"") {
        return None;
    }
    if s.last() != Some(&b'"') || i >= s.len() || s[i..s.len() - 1].contains(&b'"') {
        return None;
    }
    Some(Record {
        path: &s[path_start..path_end],
        class,
        whole,
        fraction: fraction - b'0',
    })
}

fn normalize(path: &[u8], template: &mut Vec<u8>) {
    template.clear();
    let mut start = 0;
    loop {
        let mut end = start;
        let mut numeric = true;
        while end < path.len() && path[end] != b'/' {
            numeric &= path[end].is_ascii_digit();
            end += 1;
        }
        if numeric && end != start {
            template.extend_from_slice(b"{id}");
        } else {
            template.extend_from_slice(&path[start..end]);
        }
        if end == path.len() {
            break;
        }
        template.push(b'/');
        start = end + 1;
    }
}

fn main() -> io::Result<()> {
    let filename = std::env::args_os().nth(1).expect("expected input path");
    let mut source = BufReader::with_capacity(1024 * 1024, File::open(filename)?);
    let mut line = Vec::with_capacity(256);
    let mut template = Vec::with_capacity(128);
    let mut paths: HashMap<Vec<u8>, Latencies> = HashMap::new();
    let mut statuses = [0u64; 10];
    let mut lines = 0u64;
    let mut malformed = 0u64;
    loop {
        line.clear();
        if source.read_until(b'\n', &mut line)? == 0 {
            break;
        }
        lines += 1;
        match parse(&line[..line.len() - 1]) {
            Some(record) => {
                statuses[record.class] += 1;
                normalize(record.path, &mut template);
                if let Some(values) = paths.get_mut(template.as_slice()) {
                    values.push(record.whole, record.fraction);
                } else {
                    let mut values = Latencies::default();
                    values.push(record.whole, record.fraction);
                    paths.insert(template.clone(), values);
                }
            }
            None => malformed += 1,
        }
    }
    let mut top: Vec<_> = paths.iter_mut().collect();
    let order = |a: &(&Vec<u8>, &mut Latencies), b: &(&Vec<u8>, &mut Latencies)| {
        b.1.len().cmp(&a.1.len()).then_with(|| a.0.cmp(b.0))
    };
    if top.len() > 10 {
        top.select_nth_unstable_by(10, order);
        top.truncate(10);
    }
    top.sort_unstable_by(order);

    let stdout = io::stdout();
    let mut output = io::BufWriter::new(stdout.lock());
    writeln!(output, "lines {lines}\nmalformed {malformed}")?;
    for (class, count) in statuses.iter().enumerate() {
        if *count != 0 {
            writeln!(output, "status {class}xx {count}")?;
        }
    }
    for (path, values) in top {
        let n = values.len();
        let (p50, p95, maximum) = values.summary();
        writeln!(
            output,
            "path {} {n} {p50} {p95} {maximum}",
            std::str::from_utf8(path).unwrap()
        )?;
    }
    output.flush()
}
