use std::borrow::Cow;
use std::collections::HashMap;
use std::hash::{BuildHasherDefault, Hasher};
use std::io::Write;

#[derive(Default)]
struct FxHasher {
    h: u64,
}

const FX_K: u64 = 0x517c_c1b7_2722_0a95;

impl FxHasher {
    #[inline(always)]
    fn add(&mut self, w: u64) {
        self.h = (self.h.rotate_left(5) ^ w).wrapping_mul(FX_K);
    }
}

impl Hasher for FxHasher {
    #[inline]
    fn write(&mut self, bytes: &[u8]) {
        let mut b = bytes;
        while b.len() >= 8 {
            self.add(u64::from_le_bytes(b[..8].try_into().unwrap()));
            b = &b[8..];
        }
        if b.len() >= 4 {
            self.add(u32::from_le_bytes(b[..4].try_into().unwrap()) as u64);
            b = &b[4..];
        }
        for &x in b {
            self.add(x as u64);
        }
    }

    #[inline]
    fn write_u8(&mut self, i: u8) {
        self.add(i as u64);
    }

    #[inline]
    fn write_usize(&mut self, i: usize) {
        self.add(i as u64);
    }

    #[inline]
    fn finish(&self) -> u64 {
        let mut x = self.h;
        x ^= x >> 32;
        x = x.wrapping_mul(0x9E37_79B9_7F4A_7C15);
        x ^= x >> 29;
        x
    }
}

type FxMap<K, V> = HashMap<K, V, BuildHasherDefault<FxHasher>>;
type Rates = FxMap<Vec<u8>, i64>;

const EMPTY: &[u8] = &[];

#[derive(Default)]
struct Agg {
    counted: u64,
    net: i64,
    chan: FxMap<Vec<u8>, (u64, i64)>,
    acct: FxMap<Vec<u8>, i64>,
}

struct P<'a> {
    b: &'a [u8],
    i: usize,
}

#[inline(always)]
fn hex4(b: &[u8], j: usize) -> u32 {
    let mut v: u32 = 0;
    for k in 0..4 {
        let c = b.get(j + k).copied().unwrap_or(b'0');
        let d = match c {
            b'0'..=b'9' => c - b'0',
            b'a'..=b'f' => c - b'a' + 10,
            b'A'..=b'F' => c - b'A' + 10,
            _ => 0,
        };
        v = v * 16 + d as u32;
    }
    v
}

// Given j just after an opening quote, returns the index just after the closing quote.
fn str_end(b: &[u8], mut j: usize) -> usize {
    while j < b.len() {
        match b[j] {
            b'"' => return j + 1,
            b'\\' => j += 2,
            _ => j += 1,
        }
    }
    b.len()
}

impl<'a> P<'a> {
    #[inline(always)]
    fn peek(&self) -> u8 {
        if self.i < self.b.len() {
            self.b[self.i]
        } else {
            0
        }
    }

    #[inline(always)]
    fn ws(&mut self) {
        let b = self.b;
        let mut i = self.i;
        while i < b.len() && matches!(b[i], b' ' | b'\n' | b'\r' | b'\t') {
            i += 1;
        }
        self.i = i;
    }

    // Parses a string starting at the opening quote at self.i.
    fn string(&mut self) -> Cow<'a, [u8]> {
        let b = self.b;
        let start = self.i + 1;
        if start > b.len() {
            self.i = b.len();
            return Cow::Borrowed(EMPTY);
        }
        let mut j = start;
        while j < b.len() && b[j] != b'"' && b[j] != b'\\' {
            j += 1;
        }
        if j < b.len() && b[j] == b'"' {
            self.i = j + 1;
            return Cow::Borrowed(&b[start..j]);
        }
        if j >= b.len() {
            self.i = b.len();
            return Cow::Borrowed(&b[start..]);
        }
        self.decode(start)
    }

    // Slow path: string contains escapes. `start` is the first byte after the opening quote.
    fn decode(&mut self, start: usize) -> Cow<'a, [u8]> {
        let b = self.b;
        let n = b.len();
        let mut out: Vec<u8> = Vec::new();
        let mut j = start;
        loop {
            let run = j;
            while j < n && b[j] != b'"' && b[j] != b'\\' {
                j += 1;
            }
            out.extend_from_slice(&b[run..j]);
            if j >= n {
                break;
            }
            if b[j] == b'"' {
                j += 1;
                break;
            }
            // backslash
            j += 1;
            if j >= n {
                break;
            }
            let c = b[j];
            j += 1;
            match c {
                b'n' => out.push(b'\n'),
                b't' => out.push(b'\t'),
                b'r' => out.push(b'\r'),
                b'b' => out.push(8),
                b'f' => out.push(12),
                b'u' => {
                    let mut cp = hex4(b, j);
                    j += 4;
                    if (0xD800..0xDC00).contains(&cp)
                        && j + 6 <= n
                        && b[j] == b'\\'
                        && b[j + 1] == b'u'
                    {
                        let lo = hex4(b, j + 2);
                        if (0xDC00..0xE000).contains(&lo) {
                            cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
                            j += 6;
                        }
                    }
                    let ch = char::from_u32(cp).unwrap_or('\u{FFFD}');
                    let mut tmp = [0u8; 4];
                    out.extend_from_slice(ch.encode_utf8(&mut tmp).as_bytes());
                }
                _ => out.push(c), // " \ /
            }
        }
        self.i = j;
        Cow::Owned(out)
    }

    // Skips one JSON value, starting after optional whitespace.
    fn skip_value(&mut self) {
        self.ws();
        let b = self.b;
        let n = b.len();
        let mut j = self.i;
        let mut depth: usize = 0;
        while j < n {
            let c = b[j];
            match c {
                b'"' => {
                    j = str_end(b, j + 1);
                    if depth == 0 {
                        break;
                    }
                }
                b'{' | b'[' => {
                    depth += 1;
                    j += 1;
                }
                b'}' | b']' => {
                    if depth == 0 {
                        break;
                    }
                    depth -= 1;
                    j += 1;
                    if depth == 0 {
                        break;
                    }
                }
                b',' | b' ' | b'\n' | b'\r' | b'\t' if depth == 0 => break,
                _ => j += 1,
            }
        }
        self.i = j;
    }
}

// Iterates the keys of the object at p; `f` must consume the value.
fn each_key<'a, F>(p: &mut P<'a>, mut f: F)
where
    F: FnMut(&mut P<'a>, &[u8]),
{
    if p.peek() != b'{' {
        p.skip_value();
        return;
    }
    p.i += 1;
    loop {
        p.ws();
        match p.peek() {
            b'}' => {
                p.i += 1;
                return;
            }
            b'"' => {}
            _ => return,
        }
        let key = p.string();
        p.ws();
        if p.peek() == b':' {
            p.i += 1;
        }
        p.ws();
        f(&mut *p, &key[..]);
        p.ws();
        match p.peek() {
            b',' => p.i += 1,
            b'}' => {
                p.i += 1;
                return;
            }
            _ => return,
        }
    }
}

fn val_string<'a>(p: &mut P<'a>) -> Cow<'a, [u8]> {
    p.ws();
    if p.peek() == b'"' {
        p.string()
    } else {
        p.skip_value();
        Cow::Borrowed(EMPTY)
    }
}

fn read_int<'a>(p: &mut P<'a>) -> i64 {
    p.ws();
    let mut neg = false;
    if p.peek() == b'-' {
        neg = true;
        p.i += 1;
    }
    let mut v: i64 = 0;
    while p.peek().is_ascii_digit() {
        v = v * 10 + (p.peek() - b'0') as i64;
        p.i += 1;
    }
    p.skip_value();
    if neg { -v } else { v }
}

// Returns true if the tags array contains "test".
fn parse_tags<'a>(p: &mut P<'a>) -> bool {
    let mut test = false;
    if p.peek() != b'[' {
        p.skip_value();
        return false;
    }
    p.i += 1;
    loop {
        p.ws();
        match p.peek() {
            b']' => {
                p.i += 1;
                break;
            }
            b'"' => {
                let t = p.string();
                match &t[..] {
                    b"test" => test = true,
                    _ => {}
                }
            }
            _ => p.skip_value(),
        }
        p.ws();
        match p.peek() {
            b',' => p.i += 1,
            b']' => {
                p.i += 1;
                break;
            }
            _ => break,
        }
    }
    test
}

fn parse_meta<'a>(p: &mut P<'a>) -> Cow<'a, [u8]> {
    let mut ch: Cow<'a, [u8]> = Cow::Borrowed(EMPTY);
    each_key(p, |p, k| match k {
        b"channel" => ch = val_string(p),
        _ => p.skip_value(),
    });
    ch
}

fn amount_hund(s: &[u8]) -> i64 {
    let mut i = 0usize;
    let mut v: i64 = 0;
    while i < s.len() && s[i].is_ascii_digit() {
        v = v * 10 + (s[i] - b'0') as i64;
        i += 1;
    }
    let mut frac: i64 = 0;
    let mut nd = 0;
    if i < s.len() && s[i] == b'.' {
        i += 1;
        while i < s.len() && s[i].is_ascii_digit() {
            if nd < 2 {
                frac = frac * 10 + (s[i] - b'0') as i64;
                nd += 1;
            }
            i += 1;
        }
    }
    while nd < 2 {
        frac *= 10;
        nd += 1;
    }
    v * 100 + frac
}

fn parse_tx<'a>(p: &mut P<'a>, rates: &Rates, agg: &mut Agg) {
    let mut ty: Cow<'a, [u8]> = Cow::Borrowed(EMPTY);
    let mut amount: Cow<'a, [u8]> = Cow::Borrowed(EMPTY);
    let mut currency: Cow<'a, [u8]> = Cow::Borrowed(EMPTY);
    let mut account: Cow<'a, [u8]> = Cow::Borrowed(EMPTY);
    let mut channel: Cow<'a, [u8]> = Cow::Borrowed(EMPTY);
    let mut test = false;

    each_key(p, |p, k| match k {
        b"type" => ty = val_string(p),
        b"amount" => amount = val_string(p),
        b"currency" => currency = val_string(p),
        b"account" => account = val_string(p),
        b"tags" => test |= parse_tags(p),
        b"meta" => channel = parse_meta(p),
        _ => p.skip_value(),
    });

    if test {
        return;
    }
    let sign: i64 = match &ty[..] {
        b"credit" | b"refund" => 1,
        b"debit" => -1,
        _ => return, // void or unknown
    };

    let hund = amount_hund(&amount[..]);
    let rate = rates.get(&currency[..]).copied().unwrap_or(0);
    let usd = hund * rate / 1_000_000;
    let v = sign * usd;

    agg.counted += 1;
    agg.net += v;

    if let Some(e) = agg.chan.get_mut(&channel[..]) {
        e.0 += 1;
        e.1 += v;
    } else {
        agg.chan.insert(channel.into_owned(), (1, v));
    }

    if let Some(e) = agg.acct.get_mut(&account[..]) {
        *e += v;
    } else {
        agg.acct.insert(account.into_owned(), v);
    }
}

fn main() {
    let path = match std::env::args_os().nth(1) {
        Some(p) => p,
        None => {
            eprintln!("usage: solution INPUT_PATH");
            std::process::exit(2);
        }
    };
    let data = match std::fs::read(&path) {
        Ok(d) => d,
        Err(e) => {
            eprintln!("{e}");
            std::process::exit(1);
        }
    };

    let mut p = P { b: &data, i: 0 };
    let mut rates: Rates = Rates::default();
    let mut agg = Agg::default();

    // First line: rates object.
    p.ws();
    each_key(&mut p, |p, k| match k {
        b"rates" => each_key(p, |p, cur| {
            let v = read_int(p);
            rates.insert(cur.to_vec(), v);
        }),
        _ => p.skip_value(),
    });

    // Transaction lines.
    loop {
        p.ws();
        if p.i >= data.len() {
            break;
        }
        if p.peek() != b'{' {
            p.i += 1;
            continue;
        }
        parse_tx(&mut p, &rates, &mut agg);
    }

    // Output.
    let mut out: Vec<u8> = Vec::with_capacity(4096);
    writeln!(out, "counted {}", agg.counted).unwrap();
    writeln!(out, "net {}", agg.net).unwrap();

    let mut chs: Vec<(&[u8], u64, i64)> = agg
        .chan
        .iter()
        .map(|(k, v)| (&k[..], v.0, v.1))
        .collect();
    chs.sort_unstable_by(|a, b| a.0.cmp(b.0));
    for &(name, c, s) in &chs {
        out.extend_from_slice(b"channel ");
        out.extend_from_slice(name);
        writeln!(out, " {} {}", c, s).unwrap();
    }

    let mut accs: Vec<(&[u8], i64)> = agg
        .acct
        .iter()
        .map(|(k, v)| (&k[..], *v))
        .collect();
    if accs.len() > 10 {
        accs.select_nth_unstable_by(9, |a, b| b.1.cmp(&a.1).then_with(|| a.0.cmp(b.0)));
        accs.truncate(10);
    }
    accs.sort_unstable_by(|a, b| b.1.cmp(&a.1).then_with(|| a.0.cmp(b.0)));
    for &(name, s) in &accs {
        out.extend_from_slice(b"account ");
        out.extend_from_slice(name);
        writeln!(out, " {}", s).unwrap();
    }

    let stdout = std::io::stdout();
    let mut lock = stdout.lock();
    lock.write_all(&out).unwrap();
    lock.flush().unwrap();
}
