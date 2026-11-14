use std::collections::HashMap;
use std::env;
use std::fs;
use std::io::{self, BufWriter, Write};

struct Request<'a> {
    path: &'a [u8],
    status: usize,
    whole: &'a [u8],
    fraction: u8,
}

#[inline]
fn parse_line(line: &[u8]) -> Option<Request<'_>> {
    let n = line.len();
    if n < 25 {
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

    for i in [
        0usize, 1, 2, 3, 5, 6, 8, 9, 11, 12, 14, 15, 17, 18, 20, 21, 22,
    ] {
        if !line[i].is_ascii_digit() {
            return None;
        }
    }

    let mut i = 25;
    let host_start = i;
    while i < n && line[i].is_ascii_lowercase() {
        i += 1;
    }
    if i == host_start || i == n || line[i] != b'-' {
        return None;
    }
    i += 1;

    let host_number_start = i;
    while i < n && line[i].is_ascii_digit() {
        i += 1;
    }
    if i == host_number_start || i == n || line[i] != b' ' {
        return None;
    }
    i += 1;

    let rest = &line[i..];
    let method_length = if rest.starts_with(b"GET ") {
        4
    } else if rest.starts_with(b"POST ") {
        5
    } else if rest.starts_with(b"PUT ") {
        4
    } else if rest.starts_with(b"DELETE ") {
        7
    } else if rest.starts_with(b"PATCH ") {
        6
    } else {
        return None;
    };
    i += method_length;

    if i == n || line[i] != b'/' {
        return None;
    }
    let path_start = i;
    i += 1;
    while i < n {
        let c = line[i];
        if c.is_ascii_alphanumeric() || c == b'_' || c == b'/' || c == b'-' {
            i += 1;
        } else {
            break;
        }
    }
    let path_end = i;

    if i < n && line[i] == b'?' {
        i += 1;
        while i < n && line[i] != b' ' {
            i += 1;
        }
    }
    if i == n || line[i] != b' ' {
        return None;
    }
    i += 1;

    if n - i < 4
        || !line[i].is_ascii_digit()
        || !line[i + 1].is_ascii_digit()
        || !line[i + 2].is_ascii_digit()
        || line[i + 3] != b' '
    {
        return None;
    }
    let status = (line[i] - b'0') as usize;
    i += 4;

    let size_start = i;
    while i < n && line[i].is_ascii_digit() {
        i += 1;
    }
    if i == size_start || n - i < 2 || line[i] != b'B' || line[i + 1] != b' ' {
        return None;
    }
    i += 2;

    let latency_start = i;
    while i < n && line[i].is_ascii_digit() {
        i += 1;
    }
    let latency_end = i;

    if i == latency_start
        || n - i < 7
        || line[i] != b'.'
        || !line[i + 1].is_ascii_digit()
        || line[i + 2] != b'm'
        || line[i + 3] != b's'
        || line[i + 4] != b' '
        || line[i + 5] != b'"'
        || line[n - 1] != b'"'
    {
        return None;
    }

    if line[i + 6..n - 1].contains(&b'"') {
        return None;
    }

    Some(Request {
        path: &line[path_start..path_end],
        status,
        whole: &line[latency_start..latency_end],
        fraction: line[i + 1] - b'0',
    })
}

#[inline]
fn make_template(path: &[u8], output: &mut Vec<u8>) {
    output.clear();
    let mut first = true;
    for segment in path.split(|&c| c == b'/') {
        if !first {
            output.push(b'/');
        }
        first = false;

        if !segment.is_empty() && segment.iter().all(u8::is_ascii_digit) {
            output.extend_from_slice(b"{id}");
        } else {
            output.extend_from_slice(segment);
        }
    }
}

#[derive(Default)]
struct Latencies {
    small: Vec<u64>,
    large: Vec<Box<[u8]>>,
}

#[inline]
fn format_small(value: u64) -> String {
    format!("{}.{}", value / 10, value % 10)
}

fn format_large(digits: &[u8]) -> String {
    let split = digits.len() - 1;
    let mut result = String::with_capacity(digits.len() + 1);
    result.push_str(std::str::from_utf8(&digits[..split]).unwrap());
    result.push('.');
    result.push(digits[split] as char);
    result
}

impl Latencies {
    #[inline]
    fn len(&self) -> usize {
        self.small.len() + self.large.len()
    }

    #[inline]
    fn push(&mut self, whole: &[u8], fraction: u8) {
        let mut start = 0;
        while start < whole.len() && whole[start] == b'0' {
            start += 1;
        }
        let digits = &whole[start..];

        if digits.len() <= 19 {
            let mut value = 0u64;
            for &digit in digits {
                value = value * 10 + (digit - b'0') as u64;
            }

            if let Some(tenths) = value
                .checked_mul(10)
                .and_then(|v| v.checked_add(fraction as u64))
            {
                self.small.push(tenths);
                return;
            }
        }

        let mut tenths = Vec::with_capacity(digits.len() + 1);
        tenths.extend_from_slice(digits);
        tenths.push(b'0' + fraction);
        self.large.push(tenths.into_boxed_slice());
    }

    fn percentile(&mut self, index: usize, upper: usize) -> String {
        if index < self.small.len() {
            let end = upper.min(self.small.len());
            let (_, value, _) = self.small[..end].select_nth_unstable(index);
            format_small(*value)
        } else {
            let small_count = self.small.len();
            let index = index - small_count;
            let end = upper - small_count;
            let (_, value, _) = self.large[..end].select_nth_unstable_by(index, |a, b| {
                a.len().cmp(&b.len()).then_with(|| a.cmp(b))
            });
            format_large(value)
        }
    }

    fn maximum(&self) -> String {
        if self.large.is_empty() {
            format_small(*self.small.iter().max().unwrap())
        } else {
            let value = self
                .large
                .iter()
                .max_by(|a, b| a.len().cmp(&b.len()).then_with(|| a.cmp(b)))
                .unwrap();
            format_large(value)
        }
    }
}

fn main() {
    let input_path = env::args_os().nth(1).unwrap();
    let data = fs::read(input_path).unwrap();

    let mut line_count = 0usize;
    let mut malformed = 0usize;
    let mut statuses = [0usize; 10];
    let mut paths: HashMap<Vec<u8>, Latencies> = HashMap::new();
    let mut template = Vec::with_capacity(128);

    for raw in data.split_inclusive(|&c| c == b'\n') {
        line_count += 1;
        let line = &raw[..raw.len() - 1];

        let Some(request) = parse_line(line) else {
            malformed += 1;
            continue;
        };

        statuses[request.status] += 1;
        make_template(request.path, &mut template);

        if let Some(latencies) = paths.get_mut(template.as_slice()) {
            latencies.push(request.whole, request.fraction);
        } else {
            let mut latencies = Latencies::default();
            latencies.push(request.whole, request.fraction);
            paths.insert(template.clone(), latencies);
        }
    }

    drop(data);

    let mut entries: Vec<(Vec<u8>, Latencies)> = paths.into_iter().collect();

    let compare = |a: &(Vec<u8>, Latencies), b: &(Vec<u8>, Latencies)| {
        b.1.len().cmp(&a.1.len()).then_with(|| a.0.cmp(&b.0))
    };

    if entries.len() > 10 {
        entries.select_nth_unstable_by(10, compare);
        entries.truncate(10);
    }
    entries.sort_unstable_by(compare);

    let stdout = io::stdout();
    let mut output = BufWriter::new(stdout.lock());

    writeln!(output, "lines {}", line_count).unwrap();
    writeln!(output, "malformed {}", malformed).unwrap();

    for (class, count) in statuses.into_iter().enumerate() {
        if count != 0 {
            writeln!(output, "status {}xx {}", class, count).unwrap();
        }
    }

    for (path, mut latencies) in entries {
        let count = latencies.len();
        let p50_index = (count - 1) / 2;
        let p95_index = count - count / 20 - 1;

        let maximum = latencies.maximum();
        let p95 = latencies.percentile(p95_index, count);
        let p50 = if p50_index == p95_index {
            p95.clone()
        } else {
            latencies.percentile(p50_index, p95_index)
        };

        writeln!(
            output,
            "path {} {} {} {} {}",
            std::str::from_utf8(&path).unwrap(),
            count,
            p50,
            p95,
            maximum
        )
        .unwrap();
    }

    output.flush().unwrap();
}
