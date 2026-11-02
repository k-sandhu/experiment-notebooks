use regex::bytes::Regex;
use std::collections::HashMap;
use std::env;
use std::fs::File;
use std::io::{self, BufRead, BufReader, Write};

#[derive(Default)]
struct Latencies {
    small: Vec<u64>,
    large: Vec<String>,
}
impl Latencies {
    fn len(&self) -> usize { self.small.len() + self.large.len() }
    fn push(&mut self, whole: &[u8], fraction: u8) {
        let mut value = Some(0u64);
        for &d in whole.iter().chain(std::iter::once(&fraction)) {
            value = value.and_then(|v| v.checked_mul(10)?.checked_add((d - b'0') as u64));
            if value.is_none() { break; }
        }
        if let Some(v) = value {
            self.small.push(v);
        } else {
            let first = whole.iter().position(|&b| b != b'0').unwrap_or(whole.len());
            let mut s = String::from_utf8(whole[first..].to_vec()).unwrap();
            s.push(fraction as char);
            self.large.push(s);
        }
    }
    fn rank(&mut self, index: usize) -> String {
        let small_len = self.small.len();
        if index < small_len {
            let value = *self.small.select_nth_unstable(index).1;
            format!("{}.{:01}", value / 10, value % 10)
        } else {
            let s = &self.large[index - small_len];
            format!("{}.{}", &s[..s.len()-1], &s[s.len()-1..])
        }
    }
}
fn template(path: &[u8]) -> String {
    let mut result = String::with_capacity(path.len());
    for (i, segment) in path.split(|&b| b == b'/').enumerate() {
        if i != 0 { result.push('/'); }
        if !segment.is_empty() && segment.iter().all(u8::is_ascii_digit) {
            result.push_str("{id}");
        } else {
            result.push_str(std::str::from_utf8(segment).unwrap());
        }
    }
    result
}
fn main() -> io::Result<()> {
    let pattern = Regex::new(r#"\A[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}Z [a-z]+-[0-9]+ (?:GET|POST|PUT|DELETE|PATCH) (/[A-Za-z0-9_/-]*)(?:\?[^ ]*)? ([0-9])[0-9]{2} [0-9]+B ([0-9]+)\.([0-9])ms "[^"]*"\z"#).unwrap();
    let file = File::open(env::args_os().nth(1).expect("input path required"))?;
    let mut reader = BufReader::with_capacity(1024 * 1024, file);
    let mut line = Vec::with_capacity(256);
    let mut paths: HashMap<String, Latencies> = HashMap::new();
    let mut statuses = [0usize; 10];
    let (mut lines, mut malformed) = (0usize, 0usize);
    loop {
        line.clear();
        if reader.read_until(b'\n', &mut line)? == 0 { break; }
        lines += 1;
        line.pop();
        if let Some(c) = pattern.captures(&line) {
            statuses[(c[2][0] - b'0') as usize] += 1;
            paths.entry(template(&c[1])).or_default().push(&c[3], c[4][0]);
        } else {
            malformed += 1;
        }
    }
    let mut top: Vec<_> = paths.into_iter().collect();
    top.sort_unstable_by(|a, b| b.1.len().cmp(&a.1.len()).then_with(|| a.0.cmp(&b.0)));
    let mut output = String::new();
    use std::fmt::Write as _;
    writeln!(output, "lines {lines}\nmalformed {malformed}").unwrap();
    for (i, &count) in statuses.iter().enumerate() {
        if count != 0 { writeln!(output, "status {i}xx {count}").unwrap(); }
    }
    for (path, mut values) in top.into_iter().take(10) {
        let n = values.len();
        values.large.sort_unstable_by(|a,b| a.len().cmp(&b.len()).then_with(|| a.cmp(b)));
        let p50 = values.rank((n - 1) / 2);
        let p95 = values.rank(n - n / 20 - 1);
        let max = values.rank(n - 1);
        writeln!(output, "path {path} {n} {p50} {p95} {max}").unwrap();
    }
    io::stdout().lock().write_all(output.as_bytes())
}
