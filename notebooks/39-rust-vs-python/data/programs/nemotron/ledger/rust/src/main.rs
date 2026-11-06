use std::collections::HashMap;
use std::env;
use std::fs;

use serde_json::Value;

/// Mode for scanning a JSON object.
#[derive(PartialEq, Clone, Copy)]
enum Mode {
    Top,    // transaction object: extract account/type/amount/currency/tags/meta
    Meta,   // meta object: extract channel
    Skip,   // unknown nested object: skip everything
}

/// Reusable scratch space for one line being scanned.
struct Ctx<'r> {
    buf: String,      // unescaped string scratch
    account: String,  // unescaped account id
    channel: String,  // unescaped channel name
    rate: Option<u64>,
    hundredths: i64,
    is_void: bool,
    is_debit: bool,
    skip_test: bool,
    rates: &'r HashMap<String, u64>,
}

impl<'r> Ctx<'r> {
    fn new(rates: &'r HashMap<String, u64>) -> Self {
        Ctx {
            buf: String::new(),
            account: String::new(),
            channel: String::new(),
            rate: None,
            hundredths: 0,
            is_void: false,
            is_debit: false,
            skip_test: false,
            rates,
        }
    }

    fn reset_line(&mut self) {
        self.buf.clear();
        self.account.clear();
        self.channel.clear();
        self.rate = None;
        self.hundredths = 0;
        self.is_void = false;
        self.is_debit = false;
        self.skip_test = false;
    }
}

/// Convert an amount string like "12", "12.5", "12.05" to integer hundredths.
fn to_hundredths(s: &str) -> i64 {
    let mut n: i64 = 0;
    let mut f: i64 = 0;
    let mut k: i64 = 0;
    let mut dot = false;
    for b in s.bytes() {
        match b {
            b'0'..=b'9' => {
                let d = (b - b'0') as i64;
                if dot {
                    f = f * 10 + d;
                    k += 1;
                } else {
                    n = n * 10 + d;
                }
            }
            b'.' => dot = true,
            _ => {}
        }
    }
    let h = n * 100;
    for _ in k..2 {
        f *= 10;
    }
    h + f
}

fn skip_ws(b: &[u8], p: &mut usize) {
    while *p < b.len() && matches!(b[*p], b' ' | b'\t' | b'\r' | b'\n') {
        *p += 1;
    }
}

/// Advance `p` past the closing quote of the string that starts at b[p] == '"'.
/// Does not validate escapes; assumes well-formed input.
fn scan_string(b: &[u8], p: &mut usize) -> bool {
    debug_assert!(b.get(*p) == Some(&b'"'));
    *p += 1;
    while *p < b.len() {
        match b[*p] {
            b'"' => {
                *p += 1;
                return true;
            }
            b'\\' => {
                *p += 2;
            }
            _ => {
                *p += 1;
            }
        }
    }
    false
}

/// Unescape the JSON string starting at b[p] == '"' into `out`, advancing `p`
/// past the closing quote. Handles \" \\ \/ control escapes and \uXXXX including
/// surrogate pairs. Returns false on malformed input.
fn unescape_string(b: &[u8], p: &mut usize, out: &mut String) -> bool {
    debug_assert!(b.get(*p) == Some(&b'"'));
    out.clear();
    *p += 1;
    while *p < b.len() {
        let c = b[*p];
        if c == b'"' {
            *p += 1;
            return true;
        }
        if c == b'\\' {
            *p += 1;
            let esc = match b.get(*p) {
                Some(&c) => c,
                None => return false,
            };
            match esc {
                b'"' => out.push('"'),
                b'\\' => out.push('\\'),
                b'/' => out.push('/'),
                b'n' => out.push('\n'),
                b't' => out.push('\t'),
                b'r' => out.push('\r'),
                b'b' => out.push('\u{08}'),
                b'f' => out.push('\u{0c}'),
                b'u' => {
                    if *p + 5 > b.len() {
                        return false;
                    }
                    let hex = unsafe { std::str::from_utf8_unchecked(&b[*p + 1..*p + 5]) };
                    let code = match u32::from_str_radix(hex, 16) {
                        Ok(c) => c,
                        Err(_) => return false,
                    };
                    *p += 5;
                    let ch = if (0xD800..=0xDBFF).contains(&code)
                        && *p + 1 < b.len()
                        && b[*p] == b'\\'
                        && b.get(*p + 1) == Some(&b'u')
                        && *p + 6 <= b.len()
                    {
                        let hex2 =
                            unsafe { std::str::from_utf8_unchecked(&b[*p + 1..*p + 5]) };
                        let low = match u32::from_str_radix(hex2, 16) {
                            Ok(c) => c,
                            Err(_) => return false,
                        };
                        *p += 5;
                        let cp = 0x10000 + ((code - 0xD800) << 10) + (low - 0xDC00);
                        char::from_u32(cp)
                    } else {
                        char::from_u32(code)
                    };
                    match ch {
                        Some(c) => out.push(c),
                        None => return false,
                    }
                }
                c => out.push(c as char),
            }
            *p += 1;
        } else if c >= 0x80 {
            // UTF-8 sequence: copy it verbatim.
            let len = utf8_seq_len(c);
            if *p + len > b.len() {
                return false;
            }
            let s = unsafe { std::str::from_utf8_unchecked(&b[*p..*p + len]) };
            out.push_str(s);
            *p += len;
        } else {
            out.push(c as char);
            *p += 1;
        }
    }
    false
}

/// Length of the UTF-8 sequence starting with leading byte `c`.
fn utf8_seq_len(c: u8) -> usize {
    match c {
        0xC0..=0xDF => 2,
        0xE0..=0xEF => 3,
        0xF0..=0xF7 => 4,
        _ => 1,
    }
}

fn skip_number(b: &[u8], p: &mut usize) {
    while *p < b.len()
        && matches!(
            b[*p],
            b'0'..=b'9' | b'+' | b'-' | b'.' | b'e' | b'E'
        )
    {
        *p += 1;
    }
}

/// Skip any literal (true/false/null/number). b[p] is the first char of it.
fn skip_literal(b: &[u8], p: &mut usize) {
    match b[*p] {
        b't' => *p += 4,
        b'f' => *p += 5,
        b'n' => *p += 4,
        _ => skip_number(b, p),
    }
}

fn skip_value(b: &[u8], p: &mut usize, ctx: &mut Ctx) -> bool {
    match b.get(*p) {
        Some(&b'"') => scan_string(b, p),
        Some(&b'{') => scan_object(b, p, Mode::Skip, &mut *ctx),
        Some(&b'[') => skip_array(b, p, false, &mut *ctx),
        Some(&b't') | Some(&b'f') | Some(&b'n') => {
            skip_literal(b, p);
            true
        }
        Some(_) => {
            skip_number(b, p);
            true
        }
        None => false,
    }
}

fn skip_array(b: &[u8], p: &mut usize, is_tags: bool, ctx: &mut Ctx) -> bool {
    debug_assert!(b.get(*p) == Some(&b'['));
    *p += 1;
    loop {
        skip_ws(b, p);
        match b.get(*p) {
            Some(&b']') => {
                *p += 1;
                return true;
            }
            Some(&b',') => {
                *p += 1;
                continue;
            }
            Some(&b'"') => {
                if is_tags {
                    if !unescape_string(b, p, &mut ctx.buf) {
                        return false;
                    }
                    if ctx.buf == "test" {
                        ctx.skip_test = true;
                    }
                } else {
                    if !scan_string(b, p) {
                        return false;
                    }
                }
            }
            Some(&b'{') => {
                if !scan_object(b, p, Mode::Skip, &mut *ctx) {
                    return false;
                }
            }
            Some(&b'[') => {
                if !skip_array(b, p, false, &mut *ctx) {
                    return false;
                }
            }
            Some(_) => {
                skip_literal(b, p);
            }
            None => return false,
        }
    }
}

/// Scan a JSON object starting at b[p] == '{'. Returns false on malformed input.
fn scan_object(
    b: &[u8],
    p: &mut usize,
    mode: Mode,
    ctx: &mut Ctx,
) -> bool {
    debug_assert!(b.get(*p) == Some(&b'{'));
    *p += 1;
    loop {
        skip_ws(b, p);
        match b.get(*p) {
            Some(&b'}') => {
                *p += 1;
                return true;
            }
            Some(&b',') => {
                *p += 1;
                continue;
            }
            Some(&b'"') => {
                if !unescape_string(b, p, &mut ctx.buf) {
                    return false;
                }
                skip_ws(b, p);
                match b.get(*p) {
                    Some(&b':') => *p += 1,
                    _ => return false,
                }
                skip_ws(b, p);
                if !dispatch_value(b, p, mode, &mut *ctx) {
                    return false;
                }
            }
            _ => return false,
        }
    }
}

fn dispatch_value(b: &[u8], p: &mut usize, mode: Mode, ctx: &mut Ctx) -> bool {
    let key = ctx.buf.as_str();
    if key == "account" {
        if mode != Mode::Top {
            return skip_value(b, p, ctx);
        }
        if b.get(*p) != Some(&b'"') {
            return skip_value(b, p, ctx);
        }
        if !unescape_string(b, p, &mut ctx.buf) {
            return false;
        }
        ctx.account.clear();
        ctx.account.push_str(&ctx.buf);
    } else if key == "type" {
        if mode != Mode::Top {
            return skip_value(b, p, ctx);
        }
        if b.get(*p) != Some(&b'"') {
            return skip_value(b, p, ctx);
        }
        if !unescape_string(b, p, &mut ctx.buf) {
            return false;
        }
        match ctx.buf.as_str() {
            "void" => ctx.is_void = true,
            "debit" => ctx.is_debit = true,
            _ => {}
        }
    } else if key == "amount" {
        if mode != Mode::Top {
            return skip_value(b, p, ctx);
        }
        if b.get(*p) != Some(&b'"') {
            return skip_value(b, p, ctx);
        }
        if !unescape_string(b, p, &mut ctx.buf) {
            return false;
        }
        ctx.hundredths = to_hundredths(&ctx.buf);
    } else if key == "currency" {
        if mode != Mode::Top {
            return skip_value(b, p, ctx);
        }
        if b.get(*p) != Some(&b'"') {
            return skip_value(b, p, ctx);
        }
        if !unescape_string(b, p, &mut ctx.buf) {
            return false;
        }
        ctx.rate = ctx.rates.get(ctx.buf.as_str()).copied();
    } else if key == "tags" {
        if mode != Mode::Top {
            return skip_value(b, p, ctx);
        }
        if b.get(*p) != Some(&b'[') {
            return skip_value(b, p, ctx);
        }
        if !skip_array(b, p, true, &mut *ctx) {
            return false;
        }
    } else if key == "meta" {
        if mode != Mode::Top {
            return skip_value(b, p, ctx);
        }
        if b.get(*p) != Some(&b'{') {
            return skip_value(b, p, ctx);
        }
        if !scan_object(b, p, Mode::Meta, &mut *ctx) {
            return false;
        }
    } else if key == "channel" {
        if mode != Mode::Meta {
            return skip_value(b, p, ctx);
        }
        if b.get(*p) != Some(&b'"') {
            return skip_value(b, p, ctx);
        }
        if !unescape_string(b, p, &mut ctx.buf) {
            return false;
        }
        ctx.channel.clear();
        ctx.channel.push_str(&ctx.buf);
    } else {
        return skip_value(b, p, ctx);
    }
    true
}

/// Process one transaction line; returns its signed US-cent value, or None if
/// the line is skipped (void / test tag) or unparseable.
fn process_line(b: &[u8], ctx: &mut Ctx) -> Option<i64> {
    ctx.reset_line();
    let mut p = 0;
    skip_ws(b, &mut p);
    if b.get(p) != Some(&b'{') {
        return None;
    }
    if !scan_object(b, &mut p, Mode::Top, ctx) {
        return None;
    }
    if ctx.is_void || ctx.skip_test {
        return None;
    }
    let rate = ctx.rate?;
    let usd = ctx.hundredths * rate as i64 / 1_000_000;
    let signed = if ctx.is_debit { -usd } else { usd };
    Some(signed)
}

fn main() -> std::io::Result<()> {
    let path = env::args().nth(1).expect("usage: solution INPUT_PATH");
    let data = fs::read(&path).expect("failed to read input file");

    let mut lines = data.split(|b| *b == b'\n');
    let first = lines.next().expect("input file is empty");
    let rates_val: Value = serde_json::from_slice(first).expect("failed to parse rates");
    let rates_obj = rates_val
        .get("rates")
        .and_then(Value::as_object)
        .expect("rates object missing");
    let rates: HashMap<String, u64> = rates_obj
        .iter()
        .filter_map(|(k, v)| v.as_u64().map(|u| (k.clone(), u)))
        .collect();

    let mut ctx = Ctx::new(&rates);

    let mut count: u64 = 0;
    let mut net: i64 = 0;
    let mut channels: HashMap<String, (u64, i64)> = HashMap::new();
    let mut accounts: HashMap<String, i64> = HashMap::new();

    for line in lines {
        if line.is_empty() {
            continue;
        }
        let Some(signed) = process_line(line, &mut ctx) else {
            continue;
        };
        count += 1;
        net += signed;

        let c = channels.entry(ctx.channel.clone()).or_insert((0u64, 0i64));
        c.0 += 1;
        c.1 += signed;
        *accounts.entry(ctx.account.clone()).or_insert(0) += signed;
    }

    let mut out = String::with_capacity(512);
    out.push_str("counted ");
    out.push_str(&count.to_string());
    out.push('\n');
    out.push_str("net ");
    out.push_str(&net.to_string());
    out.push('\n');

    let mut ch: Vec<(String, (u64, i64))> = channels.into_iter().collect();
    ch.sort_by(|a, b| a.0.cmp(&b.0));
    for (name, (c, n)) in &ch {
        out.push_str("channel ");
        out.push_str(name);
        out.push(' ');
        out.push_str(&c.to_string());
        out.push(' ');
        out.push_str(&n.to_string());
        out.push('\n');
    }

    let mut ac: Vec<(String, i64)> = accounts.into_iter().collect();
    ac.sort_by(|a, b| b.1.cmp(&a.1).then_with(|| a.0.cmp(&b.0)));
    for (id, n) in ac.iter().take(10) {
        out.push_str("account ");
        out.push_str(id);
        out.push(' ');
        out.push_str(&n.to_string());
        out.push('\n');
    }

    print!("{}", out);
    Ok(())
}
