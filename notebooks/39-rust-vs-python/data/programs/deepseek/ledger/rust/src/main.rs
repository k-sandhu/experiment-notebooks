use std::borrow::Cow;
use std::collections::HashMap;
use std::fs::File;
use std::io::{self, BufRead, BufReader, BufWriter, Write};

#[inline]
fn skip_ws(b: &[u8], mut i: usize) -> usize {
    while i < b.len() {
        match b[i] {
            b' ' | b'\t' | b'\n' | b'\r' => i += 1,
            _ => break,
        }
    }
    i
}

/// b[i] must be '"'. Returns (content_start, content_end, next_after_quote, has_escape).
#[inline]
fn scan_string(b: &[u8], i: usize) -> (usize, usize, usize, bool) {
    let start = i + 1;
    let mut j = start;
    while j < b.len() {
        let c = b[j];
        if c == b'"' {
            return (start, j, j + 1, false);
        }
        if c == b'\\' {
            break;
        }
        j += 1;
    }
    // Slow path: find the real closing quote of an escaped string.
    let mut k = j;
    while k < b.len() {
        match b[k] {
            b'\\' => k += 2,
            b'"' => return (start, k, k + 1, true),
            _ => k += 1,
        }
    }
    (start, b.len(), b.len(), true)
}

#[inline]
fn hex4(b: &[u8], i: usize) -> u32 {
    let mut v = 0u32;
    for k in 0..4 {
        let c = b[i + k];
        let d = match c {
            b'0'..=b'9' => (c - b'0') as u32,
            b'a'..=b'f' => (c - b'a' + 10) as u32,
            b'A'..=b'F' => (c - b'A' + 10) as u32,
            _ => 0,
        };
        v = (v << 4) | d;
    }
    v
}

#[inline]
fn push_utf8(cp: u32, out: &mut Vec<u8>) {
    if cp < 0x80 {
        out.push(cp as u8);
    } else if cp < 0x800 {
        out.push(0xC0 | (cp >> 6) as u8);
        out.push(0x80 | (cp & 0x3F) as u8);
    } else if cp < 0x10000 {
        out.push(0xE0 | (cp >> 12) as u8);
        out.push(0x80 | ((cp >> 6) & 0x3F) as u8);
        out.push(0x80 | (cp & 0x3F) as u8);
    } else {
        out.push(0xF0 | (cp >> 18) as u8);
        out.push(0x80 | ((cp >> 12) & 0x3F) as u8);
        out.push(0x80 | ((cp >> 6) & 0x3F) as u8);
        out.push(0x80 | (cp & 0x3F) as u8);
    }
}

fn decode_string(raw: &[u8], out: &mut Vec<u8>) {
    out.clear();
    let mut i = 0;
    while i < raw.len() {
        let c = raw[i];
        if c != b'\\' {
            out.push(c);
            i += 1;
            continue;
        }
        i += 1;
        if i >= raw.len() {
            break;
        }
        match raw[i] {
            b'"' => out.push(b'"'),
            b'\\' => out.push(b'\\'),
            b'/' => out.push(b'/'),
            b'n' => out.push(b'\n'),
            b't' => out.push(b'\t'),
            b'r' => out.push(b'\r'),
            b'b' => out.push(0x08),
            b'f' => out.push(0x0C),
            b'u' => {
                let mut cp = hex4(raw, i + 1);
                i += 4;
                if (0xD800..0xDC00).contains(&cp)
                    && i + 3 < raw.len()
                    && raw[i + 1] == b'\\'
                    && raw[i + 2] == b'u'
                {
                    let lo = hex4(raw, i + 3);
                    if (0xDC00..0xE000).contains(&lo) {
                        cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
                        i += 6;
                    }
                }
                push_utf8(cp, out);
            }
            _ => {}
        }
        i += 1;
    }
}

#[inline]
fn cow_string<'a>(b: &'a [u8], s: usize, e: usize, escaped: bool) -> Cow<'a, [u8]> {
    if !escaped {
        Cow::Borrowed(&b[s..e])
    } else {
        let mut v = Vec::with_capacity(e - s);
        decode_string(&b[s..e], &mut v);
        Cow::Owned(v)
    }
}

/// Skip one JSON value starting at i; returns index just past it.
fn skip_value(b: &[u8], i: usize) -> usize {
    if i >= b.len() {
        return i;
    }
    match b[i] {
        b'"' => scan_string(b, i).2,
        b'{' | b'[' => {
            let mut depth = 0i32;
            let mut j = i;
            while j < b.len() {
                match b[j] {
                    b'"' => {
                        j = scan_string(b, j).2;
                        continue;
                    }
                    b'{' | b'[' => depth += 1,
                    b'}' | b']' => {
                        depth -= 1;
                        if depth == 0 {
                            return j + 1;
                        }
                    }
                    _ => {}
                }
                j += 1;
            }
            j
        }
        _ => {
            let mut j = i;
            while j < b.len() {
                match b[j] {
                    b',' | b'}' | b']' | b' ' | b'\t' | b'\r' | b'\n' => break,
                    _ => j += 1,
                }
            }
            j
        }
    }
}

#[inline]
fn parse_amount(s: &[u8]) -> i64 {
    let mut v: i64 = 0;
    let mut i = 0;
    while i < s.len() && s[i] != b'.' {
        v = v * 10 + (s[i] - b'0') as i64;
        i += 1;
    }
    if i < s.len() {
        i += 1;
        let mut f: i64 = 0;
        let mut fd = 0;
        while i < s.len() {
            f = f * 10 + (s[i] - b'0') as i64;
            fd += 1;
            i += 1;
        }
        if fd == 1 {
            f *= 10;
        }
        v * 100 + f
    } else {
        v * 100
    }
}

/// Parse a top-level tags array. Returns (contains_exact_test, next index).
fn parse_tags(b: &[u8], mut i: usize, scratch: &mut Vec<u8>) -> (bool, usize) {
    let mut has = false;
    i += 1; // '['
    loop {
        i = skip_ws(b, i);
        if i >= b.len() {
            return (has, i);
        }
        if b[i] == b']' {
            return (has, i + 1);
        }
        let (s, e, nx, esc) = scan_string(b, i);
        if !has {
            if !esc {
                if &b[s..e] == b"test" {
                    has = true;
                }
            } else {
                decode_string(&b[s..e], scratch);
                if scratch.as_slice() == b"test" {
                    has = true;
                }
            }
        }
        i = skip_ws(b, nx);
        if i < b.len() && b[i] == b',' {
            i += 1;
        }
    }
}

/// Parse a meta object, returning the channel string (if any) and next index.
fn parse_meta<'a>(b: &'a [u8], mut i: usize) -> (Option<Cow<'a, [u8]>>, usize) {
    let mut chan: Option<Cow<'a, [u8]>> = None;
    i += 1; // '{'
    loop {
        i = skip_ws(b, i);
        if i >= b.len() {
            break;
        }
        if b[i] == b'}' {
            i += 1;
            break;
        }
        let (ks, ke, nx, kesc) = scan_string(b, i);
        i = skip_ws(b, nx);
        if i < b.len() && b[i] == b':' {
            i += 1;
        }
        i = skip_ws(b, i);
        let is_channel = if !kesc {
            &b[ks..ke] == b"channel"
        } else {
            let mut kb = Vec::new();
            decode_string(&b[ks..ke], &mut kb);
            kb.as_slice() == b"channel"
        };
        if is_channel && i < b.len() && b[i] == b'"' {
            let (s, e, nx2, esc) = scan_string(b, i);
            chan = Some(cow_string(b, s, e, esc));
            i = nx2;
        } else {
            i = skip_value(b, i);
        }
        i = skip_ws(b, i);
        if i < b.len() && b[i] == b',' {
            i += 1;
        } else {
            if i < b.len() && b[i] == b'}' {
                i += 1;
            }
            break;
        }
    }
    (chan, i)
}

#[allow(clippy::too_many_arguments)]
fn process_line(
    b: &[u8],
    rates: &HashMap<Vec<u8>, i64>,
    channels: &mut HashMap<Vec<u8>, (i64, i64)>,
    accounts: &mut HashMap<Vec<u8>, i64>,
    total: &mut (i64, i64),
) {
    let mut ty: u8 = 0;
    let mut hundredths: i64 = 0;
    let mut rate: i64 = 0;
    let mut account: Option<Cow<[u8]>> = None;
    let mut channel: Option<Cow<[u8]>> = None;
    let mut has_test = false;
    let mut scratch: Vec<u8> = Vec::new();

    let mut i = skip_ws(b, 0);
    if i >= b.len() || b[i] != b'{' {
        return;
    }
    i += 1;
    loop {
        i = skip_ws(b, i);
        if i >= b.len() {
            break;
        }
        if b[i] == b'}' {
            break;
        }
        let (ks, ke, nx, kesc) = scan_string(b, i);
        i = skip_ws(b, nx);
        if i < b.len() && b[i] == b':' {
            i += 1;
        }
        i = skip_ws(b, i);
        let key: Cow<[u8]> = if !kesc {
            Cow::Borrowed(&b[ks..ke])
        } else {
            let mut kb = Vec::new();
            decode_string(&b[ks..ke], &mut kb);
            Cow::Owned(kb)
        };
        match key.as_ref() {
            b"type" => {
                if i < b.len() && b[i] == b'"' {
                    let (s, e, nx2, esc) = scan_string(b, i);
                    let val: Cow<[u8]> = if !esc {
                        Cow::Borrowed(&b[s..e])
                    } else {
                        let mut v = Vec::new();
                        decode_string(&b[s..e], &mut v);
                        Cow::Owned(v)
                    };
                    ty = match val.as_ref() {
                        b"credit" => 1,
                        b"debit" => 2,
                        b"refund" => 3,
                        b"void" => 4,
                        _ => 0,
                    };
                    i = nx2;
                } else {
                    i = skip_value(b, i);
                }
            }
            b"amount" => {
                if i < b.len() && b[i] == b'"' {
                    let (s, e, nx2, esc) = scan_string(b, i);
                    if !esc {
                        hundredths = parse_amount(&b[s..e]);
                    } else {
                        decode_string(&b[s..e], &mut scratch);
                        hundredths = parse_amount(&scratch);
                    }
                    i = nx2;
                } else {
                    i = skip_value(b, i);
                }
            }
            b"currency" => {
                if i < b.len() && b[i] == b'"' {
                    let (s, e, nx2, esc) = scan_string(b, i);
                    let cur: Cow<[u8]> = if !esc {
                        Cow::Borrowed(&b[s..e])
                    } else {
                        let mut v = Vec::new();
                        decode_string(&b[s..e], &mut v);
                        Cow::Owned(v)
                    };
                    rate = rates.get(cur.as_ref()).copied().unwrap_or(0);
                    i = nx2;
                } else {
                    i = skip_value(b, i);
                }
            }
            b"account" => {
                if i < b.len() && b[i] == b'"' {
                    let (s, e, nx2, esc) = scan_string(b, i);
                    account = Some(cow_string(b, s, e, esc));
                    i = nx2;
                } else {
                    i = skip_value(b, i);
                }
            }
            b"tags" => {
                if i < b.len() && b[i] == b'[' {
                    let (t, nx2) = parse_tags(b, i, &mut scratch);
                    has_test = t;
                    i = nx2;
                } else {
                    i = skip_value(b, i);
                }
            }
            b"meta" => {
                if i < b.len() && b[i] == b'{' {
                    let (c, nx2) = parse_meta(b, i);
                    if c.is_some() {
                        channel = c;
                    }
                    i = nx2;
                } else {
                    i = skip_value(b, i);
                }
            }
            _ => {
                i = skip_value(b, i);
            }
        }
        i = skip_ws(b, i);
        if i < b.len() && b[i] == b',' {
            i += 1;
        } else {
            break;
        }
    }

    if ty == 4 || has_test || account.is_none() || channel.is_none() {
        return;
    }
    let usd = (hundredths * rate) / 1_000_000;
    let signed = if ty == 2 { -usd } else { usd };

    total.0 += 1;
    total.1 += signed;

    let ch = channel.unwrap();
    match channels.get_mut(ch.as_ref()) {
        Some(e) => {
            e.0 += 1;
            e.1 += signed;
        }
        None => {
            channels.insert(ch.into_owned(), (1, signed));
        }
    }
    let ac = account.unwrap();
    match accounts.get_mut(ac.as_ref()) {
        Some(v) => *v += signed,
        None => {
            accounts.insert(ac.into_owned(), signed);
        }
    }
}

fn main() {
    let path = match std::env::args_os().nth(1) {
        Some(p) => p,
        None => {
            eprintln!("usage: solution INPUT");
            std::process::exit(2);
        }
    };
    let file = match File::open(&path) {
        Ok(f) => f,
        Err(e) => {
            eprintln!("cannot open input: {e}");
            std::process::exit(2);
        }
    };
    let mut reader = BufReader::with_capacity(1 << 20, file);

    let mut line: Vec<u8> = Vec::with_capacity(1024);
    if reader.read_until(b'\n', &mut line).is_err() || line.is_empty() {
        return;
    }
    let rates_val: serde_json::Value = match serde_json::from_slice(&line) {
        Ok(v) => v,
        Err(_) => return,
    };
    let mut rates: HashMap<Vec<u8>, i64> = HashMap::new();
    if let Some(obj) = rates_val.get("rates").and_then(|v| v.as_object()) {
        rates.reserve(obj.len());
        for (k, v) in obj {
            if let Some(n) = v.as_i64() {
                rates.insert(k.as_bytes().to_vec(), n);
            }
        }
    }

    let mut channels: HashMap<Vec<u8>, (i64, i64)> = HashMap::with_capacity(64);
    let mut accounts: HashMap<Vec<u8>, i64> = HashMap::with_capacity(1 << 17);
    let mut total: (i64, i64) = (0, 0);

    line.clear();
    loop {
        line.clear();
        match reader.read_until(b'\n', &mut line) {
            Ok(0) => break,
            Ok(_) => {
                if line.iter().all(|&c| c.is_ascii_whitespace()) {
                    continue;
                }
                process_line(&line, &rates, &mut channels, &mut accounts, &mut total);
            }
            Err(_) => break,
        }
    }

    let mut chan_vec: Vec<(Vec<u8>, i64, i64)> = channels
        .into_iter()
        .map(|(k, (c, n))| (k, c, n))
        .collect();
    chan_vec.sort_unstable_by(|a, b| a.0.cmp(&b.0));

    let mut acc_vec: Vec<(Vec<u8>, i64)> = accounts.into_iter().collect();
    acc_vec.sort_unstable_by(|a, b| b.1.cmp(&a.1).then_with(|| a.0.cmp(&b.0)));

    let stdout = io::stdout();
    let mut out = BufWriter::with_capacity(1 << 16, stdout.lock());
    let _ = write!(out, "counted {}\nnet {}\n", total.0, total.1);
    for (name, c, n) in &chan_vec {
        let _ = out.write_all(b"channel ");
        let _ = out.write_all(name);
        let _ = write!(out, " {} {}\n", c, n);
    }
    for (name, n) in acc_vec.iter().take(10) {
        let _ = out.write_all(b"account ");
        let _ = out.write_all(name);
        let _ = write!(out, " {}\n", n);
    }
    let _ = out.flush();
}
