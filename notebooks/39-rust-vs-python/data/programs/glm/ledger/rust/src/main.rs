use std::collections::HashMap;
use std::fs::File;
use std::io::{Read, Write};
use std::process::exit;

#[inline(always)]
fn skip_ws(b: &[u8], i: &mut usize) {
    while *i < b.len() {
        match b[*i] {
            b' ' | b'\t' | b'\n' | b'\r' => *i += 1,
            _ => break,
        }
    }
}

/// Scan a JSON string (b[*i] must be '"'). Returns the raw content slice
/// (escapes left as-is) and advances past the closing quote.
fn scan_string<'a>(b: &'a [u8], i: &mut usize) -> Option<&'a [u8]> {
    let n = b.len();
    let mut j = *i + 1;
    let start = j;
    while j < n {
        let c = b[j];
        if c == b'"' {
            *i = j + 1;
            return Some(&b[start..j]);
        }
        if c == b'\\' {
            j += 2;
            continue;
        }
        j += 1;
    }
    None
}

/// Unescape a JSON string content (already between the quotes) into `out`.
fn unescape(s: &[u8], out: &mut Vec<u8>) -> Option<()> {
    out.clear();
    let mut j = 0;
    while j < s.len() {
        let c = s[j];
        if c != b'\\' {
            out.push(c);
            j += 1;
            continue;
        }
        j += 1;
        let e = *s.get(j)?;
        j += 1;
        match e {
            b'"' => out.push(b'"'),
            b'\\' => out.push(b'\\'),
            b'/' => out.push(b'/'),
            b'b' => out.push(0x08),
            b'f' => out.push(0x0c),
            b'n' => out.push(b'\n'),
            b'r' => out.push(b'\r'),
            b't' => out.push(b'\t'),
            b'u' => {
                let hi = hex4(s.get(j..j + 4)?)? as u32;
                j += 4;
                let cp = if (0xd800..0xdc00).contains(&hi) {
                    // surrogate pair
                    if s.get(j) != Some(&b'\\') || s.get(j + 1) != Some(&b'u') {
                        return None;
                    }
                    let lo = hex4(s.get(j + 2..j + 6)?)? as u32;
                    j += 6;
                    0x10000 + ((hi - 0xd800) << 10) + (lo - 0xdc00)
                } else {
                    hi
                };
                let ch = char::from_u32(cp)?;
                let mut buf = [0u8; 4];
                out.extend_from_slice(ch.encode_utf8(&mut buf).as_bytes());
            }
            _ => return None,
        }
    }
    Some(())
}

fn hex4(s: &[u8]) -> Option<u16> {
    if s.len() < 4 {
        return None;
    }
    let mut v = 0u16;
    for &c in s.iter().take(4) {
        let d = match c {
            b'0'..=b'9' => c - b'0',
            b'a'..=b'f' => c - b'a' + 10,
            b'A'..=b'F' => c - b'A' + 10,
            _ => return None,
        };
        v = (v << 4) | d as u16;
    }
    Some(v)
}

/// Skip over any JSON value (string, object, array, number, true/false/null).
fn skip_value(b: &[u8], i: &mut usize) -> Option<()> {
    skip_ws(b, i);
    match *b.get(*i)? {
        b'"' => {
            scan_string(b, i)?;
        }
        b'{' => {
            *i += 1;
            loop {
                skip_ws(b, i);
                match *b.get(*i)? {
                    b'}' => {
                        *i += 1;
                        return Some(());
                    }
                    b',' => {
                        *i += 1;
                    }
                    _ => {}
                }
                skip_ws(b, i);
                if b.get(*i) != Some(&b'"') {
                    return None;
                }
                scan_string(b, i)?;
                skip_ws(b, i);
                if b.get(*i) != Some(&b':') {
                    return None;
                }
                *i += 1;
                skip_value(b, i)?;
            }
        }
        b'[' => {
            *i += 1;
            loop {
                skip_ws(b, i);
                match *b.get(*i)? {
                    b']' => {
                        *i += 1;
                        return Some(());
                    }
                    b',' => {
                        *i += 1;
                    }
                    _ => {}
                }
                skip_value(b, i)?;
            }
        }
        _ => {
            // number / true / false / null
            while *i < b.len() {
                match b[*i] {
                    b',' | b'}' | b']' | b' ' | b'\t' | b'\n' | b'\r' => break,
                    _ => *i += 1,
                }
            }
        }
    }
    Some(())
}

/// Parse the amount string into integer hundredths.
fn parse_amount(s: &[u8]) -> Option<i64> {
    let mut int_part: i64 = 0;
    let mut j = 0;
    while j < s.len() && s[j].is_ascii_digit() {
        int_part = int_part * 10 + (s[j] - b'0') as i64;
        j += 1;
    }
    if j == s.len() {
        return Some(int_part * 100);
    }
    if s[j] != b'.' {
        return None;
    }
    j += 1;
    let mut frac = 0i64;
    let mut k = 0;
    while j < s.len() && s[j].is_ascii_digit() {
        if k >= 2 {
            return None;
        }
        frac = frac * 10 + (s[j] - b'0') as i64;
        k += 1;
        j += 1;
    }
    if j != s.len() || k == 0 {
        return None;
    }
    Some(match k {
        1 => int_part * 100 + frac * 10,
        _ => int_part * 100 + frac,
    })
}

const TYPE_CREDIT: u8 = 1;
const TYPE_DEBIT: u8 = 2;
const TYPE_REFUND: u8 = 3;
const TYPE_VOID: u8 = 4;

/// Compare a raw string content to an expected ASCII name, unescaping if needed.
fn content_eq(s: &[u8], name: &[u8], scratch: &mut Vec<u8>) -> bool {
    if !s.contains(&b'\\') {
        s == name
    } else {
        match unescape(s, scratch) {
            Some(()) => &scratch[..] == name,
            None => false,
        }
    }
}

fn main() {
    let path = std::env::args().nth(1).unwrap_or_else(|| {
        eprintln!("usage: solution INPUT_PATH");
        exit(2);
    });
    let mut data = Vec::new();
    match File::open(&path) {
        Ok(mut f) => {
            if let Ok(meta) = f.metadata() {
                data.reserve(meta.len() as usize + 16);
            }
            if let Err(e) = f.read_to_end(&mut data) {
                eprintln!("read error: {e}");
                exit(1);
            }
        }
        Err(e) => {
            eprintln!("cannot open {path}: {e}");
            exit(1);
        }
    }

    // ---- rates line: use serde_json for this single small line ----
    let first_end = data.iter().position(|&c| c == b'\n').unwrap_or(data.len());
    #[derive(serde::Deserialize)]
    struct RatesLine {
        rates: HashMap<String, i64>,
    }
    let rates_line: RatesLine = match serde_json::from_slice(&data[..first_end]) {
        Ok(v) => v,
        Err(e) => {
            eprintln!("bad rates line: {e}");
            exit(1);
        }
    };
    let mut rates: Vec<(Box<[u8]>, i64)> = rates_line
        .rates
        .into_iter()
        .map(|(k, v)| (k.into_bytes().into_boxed_slice(), v))
        .collect();
    rates.shrink_to_fit();

    let mut scratch: Vec<u8> = Vec::with_capacity(64);
    let mut i = first_end;

    let mut counted: u64 = 0;
    let mut net: i64 = 0;
    let mut ch_map: HashMap<Vec<u8>, (u64, i64)> = HashMap::new();
    let mut acc_map: HashMap<Vec<u8>, i64> = HashMap::new();

    while i < data.len() {
        skip_ws(&data, &mut i);
        if i >= data.len() {
            break;
        }
        if data[i] != b'{' {
            eprintln!("unexpected byte at {i}");
            exit(1);
        }
        i += 1;
        let mut typ: u8 = 0;
        let mut hundredths: i64 = -1;
        let mut rate: i64 = 0;
        let mut has_rate = false;
        let mut has_test = false;
        let mut channel: Option<Vec<u8>> = None;
        let mut account: Option<Vec<u8>> = None;

        loop {
            skip_ws(&data, &mut i);
            match data.get(i) {
                Some(b'}') => {
                    i += 1;
                    break;
                }
                Some(b',') => {
                    i += 1;
                    continue;
                }
                Some(b'"') => {}
                _ => {
                    eprintln!("bad object at {i}");
                    exit(1);
                }
            }
            let key = scan_string(&data, &mut i).unwrap();
            skip_ws(&data, &mut i);
            if data.get(i) != Some(&b':') {
                eprintln!("expected ':' at {i}");
                exit(1);
            }
            i += 1;
            skip_ws(&data, &mut i);
            match key {
                b"type" => {
                    let s = scan_string(&data, &mut i).unwrap();
                    typ = if s.contains(&b'\\') {
                        if content_eq(s, b"credit", &mut scratch) {
                            TYPE_CREDIT
                        } else if content_eq(s, b"debit", &mut scratch) {
                            TYPE_DEBIT
                        } else if content_eq(s, b"refund", &mut scratch) {
                            TYPE_REFUND
                        } else if content_eq(s, b"void", &mut scratch) {
                            TYPE_VOID
                        } else {
                            0
                        }
                    } else {
                        match s {
                            b"credit" => TYPE_CREDIT,
                            b"debit" => TYPE_DEBIT,
                            b"refund" => TYPE_REFUND,
                            b"void" => TYPE_VOID,
                            _ => 0,
                        }
                    };
                }
                b"amount" => {
                    let s = scan_string(&data, &mut i).unwrap();
                    hundredths = parse_amount(s).unwrap_or(-1);
                }
                b"currency" => {
                    let s = scan_string(&data, &mut i).unwrap();
                    let raw: &[u8] = if s.contains(&b'\\') {
                        if unescape(s, &mut scratch).is_some() {
                            &scratch[..]
                        } else {
                            b""
                        }
                    } else {
                        s
                    };
                    for (name, r) in rates.iter() {
                        if &**name == raw {
                            rate = *r;
                            has_rate = true;
                            break;
                        }
                    }
                }
                b"tags" => {
                    skip_ws(&data, &mut i);
                    if data.get(i) != Some(&b'[') {
                        skip_value(&data, &mut i);
                        continue;
                    }
                    i += 1;
                    loop {
                        skip_ws(&data, &mut i);
                        match data.get(i) {
                            Some(b']') => {
                                i += 1;
                                break;
                            }
                            Some(b',') => {
                                i += 1;
                                continue;
                            }
                            Some(b'"') => {
                                let s = scan_string(&data, &mut i).unwrap();
                                if content_eq(s, b"test", &mut scratch) {
                                    has_test = true;
                                }
                            }
                            Some(_) => {
                                skip_value(&data, &mut i);
                            }
                            None => {
                                eprintln!("unterminated tags");
                                exit(1);
                            }
                        }
                    }
                }
                b"meta" => {
                    skip_ws(&data, &mut i);
                    if data.get(i) != Some(&b'{') {
                        skip_value(&data, &mut i);
                        continue;
                    }
                    i += 1;
                    loop {
                        skip_ws(&data, &mut i);
                        match data.get(i) {
                            Some(b'}') => {
                                i += 1;
                                break;
                            }
                            Some(b',') => {
                                i += 1;
                                continue;
                            }
                            Some(b'"') => {
                                let k = scan_string(&data, &mut i).unwrap();
                                skip_ws(&data, &mut i);
                                if data.get(i) != Some(&b':') {
                                    eprintln!("expected ':' in meta at {i}");
                                    exit(1);
                                }
                                i += 1;
                                skip_ws(&data, &mut i);
                                if k == b"channel" {
                                    if data.get(i) == Some(&b'"') {
                                        let s = scan_string(&data, &mut i).unwrap();
                                        let ch = if s.contains(&b'\\') {
                                            match unescape(s, &mut scratch) {
                                                Some(()) => scratch.clone(),
                                                None => b"".to_vec(),
                                            }
                                        } else {
                                            s.to_vec()
                                        };
                                        channel = Some(ch);
                                    } else {
                                        skip_value(&data, &mut i);
                                    }
                                } else {
                                    skip_value(&data, &mut i);
                                }
                            }
                            _ => {
                                eprintln!("bad meta at {i}");
                                exit(1);
                            }
                        }
                    }
                }
                b"account" => {
                    if data.get(i) == Some(&b'"') {
                        let s = scan_string(&data, &mut i).unwrap();
                        let a = if s.contains(&b'\\') {
                            match unescape(s, &mut scratch) {
                                Some(()) => scratch.clone(),
                                None => b"".to_vec(),
                            }
                        } else {
                            s.to_vec()
                        };
                        account = Some(a);
                    } else {
                        skip_value(&data, &mut i);
                    }
                }
                _ => {
                    skip_value(&data, &mut i);
                }
            }
        }

        if typ != 0 && typ != TYPE_VOID && !has_test && hundredths >= 0 && has_rate {
            if let (Some(ch), Some(acc)) = (channel, account) {
                let usd = hundredths * rate / 1_000_000;
                let signed = if typ == TYPE_DEBIT { -usd } else { usd };
                counted += 1;
                net += signed;
                match ch_map.get_mut(&ch) {
                    Some(v) => {
                        v.0 += 1;
                        v.1 += signed;
                    }
                    None => {
                        ch_map.insert(ch, (1, signed));
                    }
                }
                match acc_map.get_mut(&acc) {
                    Some(v) => *v += signed,
                    None => {
                        acc_map.insert(acc, signed);
                    }
                }
            }
        }
    }

    let mut channels: Vec<(&Vec<u8>, &(u64, i64))> = ch_map.iter().collect();
    channels.sort_unstable_by(|a, b| a.0.cmp(b.0));
    let mut accounts: Vec<(Vec<u8>, i64)> = acc_map.into_iter().collect();
    accounts.sort_unstable_by(|a, b| b.1.cmp(&a.1).then_with(|| a.0.cmp(&b.0)));
    accounts.truncate(10);

    let mut out = String::with_capacity(4096);
    out.push_str(&format!("counted {counted}\n"));
    out.push_str(&format!("net {net}\n"));
    for (name, (c, v)) in &channels {
        out.push_str(&format!(
            "channel {} {} {}\n",
            String::from_utf8_lossy(name),
            c,
            v
        ));
    }
    for (name, v) in &accounts {
        out.push_str(&format!(
            "account {} {}\n",
            String::from_utf8_lossy(name),
            v
        ));
    }
    let stdout = std::io::stdout();
    let mut lock = stdout.lock();
    let _ = lock.write_all(out.as_bytes());
    let _ = lock.flush();
}
