use std::collections::HashMap;
use std::hash::{BuildHasherDefault, Hasher};
use std::io::Write;

// ---------- FxHash (same algorithm as rustc-hash) ----------
#[derive(Default)]
struct FxHasher {
    hash: usize,
}
const FX_SEED: usize = 0x51_7c_c1_b7_27_22_0a_95;
impl FxHasher {
    #[inline]
    fn add(&mut self, w: usize) {
        self.hash = (self.hash.rotate_left(5) ^ w).wrapping_mul(FX_SEED);
    }
}
impl Hasher for FxHasher {
    #[inline]
    fn write(&mut self, mut bytes: &[u8]) {
        while bytes.len() >= 8 {
            self.add(usize::from_le_bytes(bytes[..8].try_into().unwrap()));
            bytes = &bytes[8..];
        }
        if bytes.len() >= 4 {
            self.add(u32::from_le_bytes(bytes[..4].try_into().unwrap()) as usize);
            bytes = &bytes[4..];
        }
        if bytes.len() >= 2 {
            self.add(u16::from_le_bytes(bytes[..2].try_into().unwrap()) as usize);
            bytes = &bytes[2..];
        }
        if !bytes.is_empty() {
            self.add(bytes[0] as usize);
        }
    }
    #[inline]
    fn write_u8(&mut self, n: u8) {
        self.add(n as usize);
    }
    #[inline]
    fn write_usize(&mut self, n: usize) {
        self.add(n);
    }
    #[inline]
    fn finish(&self) -> u64 {
        self.hash as u64
    }
}
type FxBuild = BuildHasherDefault<FxHasher>;
type FxMap<K, V> = HashMap<K, V, FxBuild>;

// ---------- low-level JSON scanning over a line ----------

#[inline]
fn skip_ws(s: &[u8], p: &mut usize) {
    while *p < s.len() && matches!(s[*p], b' ' | b'\t' | b'\r' | b'\n') {
        *p += 1;
    }
}

/// s[*p] == '"'. Returns (content_start, content_end, had_escape); *p moves past closing quote.
#[inline]
fn parse_string(s: &[u8], p: &mut usize) -> (usize, usize, bool) {
    let start = *p + 1;
    let mut i = start;
    let mut esc = false;
    while i < s.len() {
        match s[i] {
            b'"' => {
                *p = i + 1;
                return (start, i, esc);
            }
            b'\\' => {
                esc = true;
                i += 2;
            }
            _ => i += 1,
        }
    }
    *p = i;
    (start, s.len(), esc)
}

#[inline]
fn skip_string(s: &[u8], p: &mut usize) {
    let mut i = *p + 1;
    while i < s.len() {
        match s[i] {
            b'"' => {
                *p = i + 1;
                return;
            }
            b'\\' => i += 2,
            _ => i += 1,
        }
    }
    *p = i;
}

fn skip_value(s: &[u8], p: &mut usize) {
    skip_ws(s, p);
    if *p >= s.len() {
        return;
    }
    match s[*p] {
        b'"' => skip_string(s, p),
        b'{' | b'[' => {
            let mut depth = 0usize;
            let mut i = *p;
            while i < s.len() {
                match s[i] {
                    b'"' => {
                        i += 1;
                        while i < s.len() {
                            match s[i] {
                                b'"' => {
                                    i += 1;
                                    break;
                                }
                                b'\\' => i += 2,
                                _ => i += 1,
                            }
                        }
                    }
                    b'{' | b'[' => {
                        depth += 1;
                        i += 1;
                    }
                    b'}' | b']' => {
                        depth -= 1;
                        i += 1;
                        if depth == 0 {
                            break;
                        }
                    }
                    _ => i += 1,
                }
            }
            *p = i;
        }
        _ => {
            let mut i = *p;
            while i < s.len() && !matches!(s[i], b',' | b'}' | b']' | b' ' | b'\t' | b'\r' | b'\n') {
                i += 1;
            }
            *p = i;
        }
    }
}

fn hex4(s: &[u8], i: &mut usize) -> u32 {
    let mut v: u32 = 0;
    for _ in 0..4 {
        if *i >= s.len() {
            break;
        }
        let c = s[*i];
        *i += 1;
        v = (v << 4)
            | match c {
                b'0'..=b'9' => (c - b'0') as u32,
                b'a'..=b'f' => (c - b'a') as u32 + 10,
                b'A'..=b'F' => (c - b'A') as u32 + 10,
                _ => 0,
            };
    }
    v
}

/// Decode a JSON string's raw content (with escapes) to its UTF-8 bytes.
fn unescape(raw: &[u8], out: &mut Vec<u8>) {
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
        let e = raw[i];
        i += 1;
        match e {
            b'"' => out.push(b'"'),
            b'\\' => out.push(b'\\'),
            b'/' => out.push(b'/'),
            b'b' => out.push(0x08),
            b'f' => out.push(0x0C),
            b'n' => out.push(b'\n'),
            b'r' => out.push(b'\r'),
            b't' => out.push(b'\t'),
            b'u' => {
                let mut cp = hex4(raw, &mut i);
                if (0xD800..0xDC00).contains(&cp)
                    && i + 1 < raw.len()
                    && raw[i] == b'\\'
                    && raw[i + 1] == b'u'
                {
                    i += 2;
                    let lo = hex4(raw, &mut i);
                    if (0xDC00..0xE000).contains(&lo) {
                        cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
                    }
                }
                let ch = char::from_u32(cp).unwrap_or('\u{FFFD}');
                let mut buf = [0u8; 4];
                out.extend_from_slice(ch.encode_utf8(&mut buf).as_bytes());
            }
            _ => out.push(e),
        }
    }
}

#[inline]
fn str_bytes<'a>(s: &'a [u8], r: (usize, usize, bool), buf: &'a mut Vec<u8>) -> &'a [u8] {
    if r.2 {
        unescape(&s[r.0..r.1], buf);
        &buf[..]
    } else {
        &s[r.0..r.1]
    }
}

#[inline]
fn parse_hundredths(b: &[u8]) -> i64 {
    let mut i = 0usize;
    let mut v: i64 = 0;
    while i < b.len() && b[i].is_ascii_digit() {
        v = v * 10 + (b[i] - b'0') as i64;
        i += 1;
    }
    v *= 100;
    if i < b.len() && b[i] == b'.' {
        i += 1;
        if i < b.len() && b[i].is_ascii_digit() {
            v += (b[i] - b'0') as i64 * 10;
            i += 1;
            if i < b.len() && b[i].is_ascii_digit() {
                v += (b[i] - b'0') as i64;
            }
        }
    }
    v
}

#[derive(Clone, Copy, PartialEq)]
enum Field {
    Account,
    Type,
    Amount,
    Currency,
    Tags,
    Meta,
    Other,
}

struct Tx {
    account: (usize, usize, bool),
    has_account: bool,
    ty: (usize, usize, bool),
    has_ty: bool,
    hundredths: i64,
    rate: i64,
    has_test: bool,
    channel: (usize, usize, bool),
    has_channel: bool,
}

/// Parse one transaction line. Returns None only if the line has no object.
fn parse_line(s: &[u8], rates: &FxMap<Vec<u8>, i64>, buf: &mut Vec<u8>, buf2: &mut Vec<u8>) -> Option<Tx> {
    let mut tx = Tx {
        account: (0, 0, false),
        has_account: false,
        ty: (0, 0, false),
        has_ty: false,
        hundredths: 0,
        rate: 0,
        has_test: false,
        channel: (0, 0, false),
        has_channel: false,
    };
    let mut p = 0usize;
    skip_ws(s, &mut p);
    if p >= s.len() || s[p] != b'{' {
        return None;
    }
    p += 1;
    loop {
        skip_ws(s, &mut p);
        if p >= s.len() {
            break;
        }
        match s[p] {
            b'}' => {
                p += 1;
                break;
            }
            b',' => {
                p += 1;
                continue;
            }
            b'"' => {}
            _ => {
                p += 1;
                continue;
            }
        }
        let kr = parse_string(s, &mut p);
        let field = {
            let kb = str_bytes(s, kr, buf);
            match kb {
                b"account" => Field::Account,
                b"type" => Field::Type,
                b"amount" => Field::Amount,
                b"currency" => Field::Currency,
                b"tags" => Field::Tags,
                b"meta" => Field::Meta,
                _ => Field::Other,
            }
        };
        skip_ws(s, &mut p);
        if p < s.len() && s[p] == b':' {
            p += 1;
        }
        skip_ws(s, &mut p);
        match field {
            Field::Account => {
                if p < s.len() && s[p] == b'"' {
                    tx.account = parse_string(s, &mut p);
                    tx.has_account = true;
                } else {
                    skip_value(s, &mut p);
                }
            }
            Field::Type => {
                if p < s.len() && s[p] == b'"' {
                    tx.ty = parse_string(s, &mut p);
                    tx.has_ty = true;
                } else {
                    skip_value(s, &mut p);
                }
            }
            Field::Amount => {
                if p < s.len() && s[p] == b'"' {
                    let r = parse_string(s, &mut p);
                    if r.2 {
                        unescape(&s[r.0..r.1], buf2);
                        tx.hundredths = parse_hundredths(&buf2[..]);
                    } else {
                        tx.hundredths = parse_hundredths(&s[r.0..r.1]);
                    }
                } else {
                    skip_value(s, &mut p);
                }
            }
            Field::Currency => {
                if p < s.len() && s[p] == b'"' {
                    let r = parse_string(s, &mut p);
                    let cb = str_bytes(s, r, buf2);
                    tx.rate = rates.get(cb).copied().unwrap_or(0);
                } else {
                    skip_value(s, &mut p);
                }
            }
            Field::Tags => {
                if p < s.len() && s[p] == b'[' {
                    p += 1;
                    let mut has = false;
                    loop {
                        skip_ws(s, &mut p);
                        if p >= s.len() {
                            break;
                        }
                        match s[p] {
                            b']' => {
                                p += 1;
                                break;
                            }
                            b',' => p += 1,
                            b'"' => {
                                let r = parse_string(s, &mut p);
                                if str_bytes(s, r, buf2) == b"test" {
                                    has = true;
                                }
                            }
                            _ => skip_value(s, &mut p),
                        }
                    }
                    tx.has_test = has;
                } else {
                    skip_value(s, &mut p);
                }
            }
            Field::Meta => {
                if p < s.len() && s[p] == b'{' {
                    p += 1;
                    loop {
                        skip_ws(s, &mut p);
                        if p >= s.len() {
                            break;
                        }
                        match s[p] {
                            b'}' => {
                                p += 1;
                                break;
                            }
                            b',' => {
                                p += 1;
                                continue;
                            }
                            b'"' => {}
                            _ => {
                                p += 1;
                                continue;
                            }
                        }
                        let kr = parse_string(s, &mut p);
                        let is_channel = str_bytes(s, kr, buf) == b"channel";
                        skip_ws(s, &mut p);
                        if p < s.len() && s[p] == b':' {
                            p += 1;
                        }
                        skip_ws(s, &mut p);
                        if is_channel && p < s.len() && s[p] == b'"' {
                            tx.channel = parse_string(s, &mut p);
                            tx.has_channel = true;
                        } else {
                            skip_value(s, &mut p);
                        }
                    }
                } else {
                    skip_value(s, &mut p);
                }
            }
            Field::Other => skip_value(s, &mut p),
        }
    }
    Some(tx)
}

fn push_i64(out: &mut Vec<u8>, v: i64) {
    let mut buf = [0u8; 20];
    let mut u = v.unsigned_abs();
    let mut i = 20;
    if u == 0 {
        out.push(b'0');
        return;
    }
    while u > 0 {
        i -= 1;
        buf[i] = b'0' + (u % 10) as u8;
        u /= 10;
    }
    if v < 0 {
        out.push(b'-');
    }
    out.extend_from_slice(&buf[i..]);
}

fn main() {
    let path = std::env::args_os().nth(1).expect("usage: solution INPUT");
    let data = std::fs::read(path).expect("cannot read input");
    let mut data = &data[..];
    if data.starts_with(&[0xEF, 0xBB, 0xBF]) {
        data = &data[3..];
    }
    // First line: exchange rates (tiny; parsed with serde_json).
    let first_end = data.iter().position(|&b| b == b'\n').unwrap_or(data.len());
    let mut rates: FxMap<Vec<u8>, i64> = HashMap::default();
    if first_end > 0 {
        if let Ok(v) = serde_json::from_slice::<serde_json::Value>(&data[..first_end]) {
            if let Some(obj) = v.get("rates").and_then(|r| r.as_object()) {
                rates.reserve(obj.len());
                for (k, val) in obj {
                    rates.insert(k.clone().into_bytes(), val.as_i64().unwrap_or(0));
                }
            }
        }
    }

    let mut counted: i64 = 0;
    let mut net: i64 = 0;
    let mut channels: Vec<(Vec<u8>, i64, i64)> = Vec::new(); // name, count, net
    let mut accounts: FxMap<Vec<u8>, i64> = HashMap::default();
    accounts.reserve(1 << 15);

    let mut buf: Vec<u8> = Vec::with_capacity(64);
    let mut buf2: Vec<u8> = Vec::with_capacity(64);
    let mut owned: Vec<u8> = Vec::with_capacity(64);

    for line in data[first_end..].split(|&b| b == b'\n') {
        if line.is_empty() {
            continue;
        }
        let Some(tx) = parse_line(line, &rates, &mut buf, &mut buf2) else {
            continue;
        };
        if !tx.has_ty || tx.has_test {
            continue;
        }
        let tyb: &[u8] = if tx.ty.2 {
            unescape(&line[tx.ty.0..tx.ty.1], &mut buf);
            &buf[..]
        } else {
            &line[tx.ty.0..tx.ty.1]
        };
        let sign: i64 = match tyb {
            b"credit" | b"refund" => 1,
            b"debit" => -1,
            _ => continue, // "void" or anything else: not counted
        };
        let usd = (tx.hundredths * tx.rate) / 1_000_000 * sign;
        counted += 1;
        net += usd;

        if tx.has_channel {
            let cb: &[u8] = if tx.channel.2 {
                unescape(&line[tx.channel.0..tx.channel.1], &mut owned);
                &owned[..]
            } else {
                &line[tx.channel.0..tx.channel.1]
            };
            match channels.iter_mut().find(|(n, _, _)| n.as_slice() == cb) {
                Some((_, c, n)) => {
                    *c += 1;
                    *n += usd;
                }
                None => channels.push((cb.to_vec(), 1, usd)),
            }
        }
        if tx.has_account {
            let ab: &[u8] = if tx.account.2 {
                unescape(&line[tx.account.0..tx.account.1], &mut buf);
                &buf[..]
            } else {
                &line[tx.account.0..tx.account.1]
            };
            match accounts.get_mut(ab) {
                Some(v) => *v += usd,
                None => {
                    accounts.insert(ab.to_vec(), usd);
                }
            }
        }
    }

    channels.sort_by(|a, b| a.0.cmp(&b.0));
    let mut acc_vec: Vec<(Vec<u8>, i64)> = accounts.into_iter().collect();
    acc_vec.sort_by(|a, b| b.1.cmp(&a.1).then_with(|| a.0.cmp(&b.0)));

    let mut out: Vec<u8> = Vec::with_capacity(4096);
    out.extend_from_slice(b"counted ");
    push_i64(&mut out, counted);
    out.push(b'\n');
    out.extend_from_slice(b"net ");
    push_i64(&mut out, net);
    out.push(b'\n');
    for (name, c, n) in &channels {
        out.extend_from_slice(b"channel ");
        out.extend_from_slice(name);
        out.push(b' ');
        push_i64(&mut out, *c);
        out.push(b' ');
        push_i64(&mut out, *n);
        out.push(b'\n');
    }
    for (name, n) in acc_vec.iter().take(10) {
        out.extend_from_slice(b"account ");
        out.extend_from_slice(name);
        out.push(b' ');
        push_i64(&mut out, *n);
        out.push(b'\n');
    }
    let stdout = std::io::stdout();
    let mut lock = stdout.lock();
    let _ = lock.write_all(&out);
}
