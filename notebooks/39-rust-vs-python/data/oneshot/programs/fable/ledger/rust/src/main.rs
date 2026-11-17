use std::fmt::Write as _;
use std::fs::File;
use std::io::{Read, Write};

const CHUNK: usize = 1 << 18;
const EMPTY: u32 = u32::MAX;

const K_NONE: u8 = 0;
const K_TYPE: u8 = 1;
const K_AMOUNT: u8 = 2;
const K_CURRENCY: u8 = 3;
const K_ACCOUNT: u8 = 4;
const K_TAGS: u8 = 5;
const K_META: u8 = 6;

const W_TYPE: u32 = u32::from_le_bytes(*b"type");
const W_TAGS: u32 = u32::from_le_bytes(*b"tags");
const W_META: u32 = u32::from_le_bytes(*b"meta");

const M_TYPE: u32 = 1;
const M_AMOUNT: u32 = 2;
const M_CURRENCY: u32 = 4;
const M_ACCOUNT: u32 = 8;
const M_TAGS: u32 = 16;
const M_CHANNEL: u32 = 32;
const M_ALL: u32 = 63;
const M_REQ: u32 = M_TYPE | M_AMOUNT | M_CURRENCY | M_ACCOUNT | M_CHANNEL;

const fn build_class() -> [u8; 256] {
    let mut t = [0u8; 256];
    t[b'"' as usize] = 1;
    t[b'{' as usize] = 2;
    t[b'[' as usize] = 2;
    t[b'}' as usize] = 3;
    t[b']' as usize] = 3;
    t
}
static CLASS: [u8; 256] = build_class();

#[inline(always)]
fn eq(a: &[u8], b: &[u8]) -> bool {
    a == b
}

#[inline(always)]
fn mix(a: u64, k: u64) -> u64 {
    let m = (a as u128).wrapping_mul(k as u128);
    (m as u64) ^ ((m >> 64) as u64)
}

#[inline(always)]
fn hash_bytes(s: &[u8]) -> u64 {
    const K: u64 = 0x517c_c1b7_2722_0a95;
    let mut h: u64 = (s.len() as u64).wrapping_mul(0x9E37_79B9_7F4A_7C15);
    let mut p = s;
    while p.len() >= 8 {
        let v = u64::from_le_bytes([p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7]]);
        h = mix(h ^ v, K);
        p = &p[8..];
    }
    if !p.is_empty() {
        let mut v = 0u64;
        for (k, &b) in p.iter().enumerate() {
            v |= (b as u64) << (8 * k);
        }
        h = mix(h ^ v, K);
    }
    h
}

struct Entry {
    hash: u64,
    off: u32,
    len: u32,
    count: u64,
    net: i64,
}

struct StrMap {
    slots: Vec<u32>,
    entries: Vec<Entry>,
    arena: Vec<u8>,
    shift: u32,
    mask: usize,
}

impl StrMap {
    fn new(bits: u32) -> Self {
        StrMap {
            slots: vec![EMPTY; 1usize << bits],
            entries: Vec::new(),
            arena: Vec::new(),
            shift: 64 - bits,
            mask: (1usize << bits) - 1,
        }
    }

    fn key(&self, e: &Entry) -> &[u8] {
        &self.arena[e.off as usize..e.off as usize + e.len as usize]
    }

    #[inline]
    fn entry(&mut self, key: &[u8]) -> usize {
        let h = hash_bytes(key);
        let mut idx = (h >> self.shift) as usize;
        loop {
            let s = self.slots[idx];
            if s == EMPTY {
                break;
            }
            let e = &self.entries[s as usize];
            if e.hash == h && e.len as usize == key.len() {
                let off = e.off as usize;
                if eq(&self.arena[off..off + key.len()], key) {
                    return s as usize;
                }
            }
            idx = (idx + 1) & self.mask;
        }
        let off = self.arena.len() as u32;
        self.arena.extend_from_slice(key);
        let id = self.entries.len();
        self.slots[idx] = id as u32;
        self.entries.push(Entry {
            hash: h,
            off,
            len: key.len() as u32,
            count: 0,
            net: 0,
        });
        if self.entries.len() * 2 > self.slots.len() {
            self.grow();
        }
        id
    }

    #[inline]
    fn get(&self, key: &[u8]) -> Option<i64> {
        let h = hash_bytes(key);
        let mut idx = (h >> self.shift) as usize;
        loop {
            let s = self.slots[idx];
            if s == EMPTY {
                return None;
            }
            let e = &self.entries[s as usize];
            if e.hash == h && e.len as usize == key.len() {
                let off = e.off as usize;
                if eq(&self.arena[off..off + key.len()], key) {
                    return Some(e.net);
                }
            }
            idx = (idx + 1) & self.mask;
        }
    }

    fn grow(&mut self) {
        let bits = (64 - self.shift) + 1;
        self.shift = 64 - bits;
        self.mask = (1usize << bits) - 1;
        self.slots = vec![EMPTY; 1usize << bits];
        for (i, e) in self.entries.iter().enumerate() {
            let mut idx = (e.hash >> self.shift) as usize;
            while self.slots[idx] != EMPTY {
                idx = (idx + 1) & self.mask;
            }
            self.slots[idx] = i as u32;
        }
    }
}

#[cfg(target_arch = "x86_64")]
#[inline(always)]
fn find_quote_or_bs(buf: &[u8], mut i: usize) -> usize {
    use std::arch::x86_64::*;
    let n = buf.len();
    let p = buf.as_ptr();
    while i + 16 <= n {
        // SAFETY: i + 16 <= n, so the 16-byte unaligned load is in bounds.
        let m = unsafe {
            let v = _mm_loadu_si128(p.add(i) as *const __m128i);
            let q = _mm_cmpeq_epi8(v, _mm_set1_epi8(0x22));
            let b = _mm_cmpeq_epi8(v, _mm_set1_epi8(0x5C));
            _mm_movemask_epi8(_mm_or_si128(q, b)) as u32
        };
        if m != 0 {
            return i + m.trailing_zeros() as usize;
        }
        i += 16;
    }
    while i < n {
        let c = buf[i];
        if c == b'"' || c == b'\\' {
            break;
        }
        i += 1;
    }
    i
}

#[cfg(not(target_arch = "x86_64"))]
#[inline(always)]
fn find_quote_or_bs(buf: &[u8], mut i: usize) -> usize {
    let n = buf.len();
    while i < n {
        let c = buf[i];
        if c == b'"' || c == b'\\' {
            break;
        }
        i += 1;
    }
    i
}

#[cfg(target_arch = "x86_64")]
#[inline]
fn find_newline(buf: &[u8], mut i: usize) -> usize {
    use std::arch::x86_64::*;
    let n = buf.len();
    let p = buf.as_ptr();
    while i + 16 <= n {
        // SAFETY: i + 16 <= n, so the 16-byte unaligned load is in bounds.
        let m = unsafe {
            let v = _mm_loadu_si128(p.add(i) as *const __m128i);
            _mm_movemask_epi8(_mm_cmpeq_epi8(v, _mm_set1_epi8(0x0A))) as u32
        };
        if m != 0 {
            return i + m.trailing_zeros() as usize;
        }
        i += 16;
    }
    while i < n {
        if buf[i] == b'\n' {
            break;
        }
        i += 1;
    }
    i
}

#[cfg(not(target_arch = "x86_64"))]
#[inline]
fn find_newline(buf: &[u8], i: usize) -> usize {
    match buf[i..].iter().position(|&b| b == b'\n') {
        Some(p) => i + p,
        None => buf.len(),
    }
}

#[inline(always)]
fn skip_ws(buf: &[u8], mut i: usize) -> usize {
    while buf[i] <= b' ' {
        i += 1;
    }
    i
}

/// `start` is the index just after the opening quote.
/// Returns (index of closing quote, whether an escape was seen).
#[inline(always)]
fn scan_string(buf: &[u8], start: usize) -> (usize, bool) {
    let mut i = start;
    let mut esc = false;
    loop {
        i = find_quote_or_bs(buf, i);
        if buf[i] == b'"' {
            return (i, esc);
        }
        esc = true;
        i += 2;
    }
}

#[inline(always)]
fn skip_string(buf: &[u8], start: usize) -> usize {
    let mut i = start;
    loop {
        i = find_quote_or_bs(buf, i);
        if buf[i] == b'"' {
            return i;
        }
        i += 2;
    }
}

#[inline]
fn skip_value(buf: &[u8], mut i: usize) -> usize {
    match buf[i] {
        b'"' => skip_string(buf, i + 1) + 1,
        b'{' | b'[' => {
            let mut depth = 1u32;
            i += 1;
            loop {
                let c = buf[i];
                i += 1;
                let k = CLASS[c as usize];
                if k == 0 {
                    continue;
                }
                if k == 1 {
                    i = skip_string(buf, i) + 1;
                } else if k == 2 {
                    depth += 1;
                } else {
                    depth -= 1;
                    if depth == 0 {
                        return i;
                    }
                }
            }
        }
        _ => {
            i += 1;
            loop {
                let c = buf[i];
                if c <= b' ' || c == b',' || c == b'}' || c == b']' {
                    return i;
                }
                i += 1;
            }
        }
    }
}

fn hex4(raw: &[u8], i: usize) -> u32 {
    let mut v = 0u32;
    for k in 0..4 {
        let c = if i + k < raw.len() { raw[i + k] } else { b'0' };
        let d = match c {
            b'0'..=b'9' => c - b'0',
            b'a'..=b'f' => c - b'a' + 10,
            b'A'..=b'F' => c - b'A' + 10,
            _ => 0,
        };
        v = (v << 4) | d as u32;
    }
    v
}

#[cold]
#[inline(never)]
fn decode(raw: &[u8], out: &mut Vec<u8>) {
    out.clear();
    let n = raw.len();
    let mut i = 0usize;
    while i < n {
        let c = raw[i];
        if c != b'\\' {
            out.push(c);
            i += 1;
            continue;
        }
        i += 1;
        if i >= n {
            break;
        }
        let e = raw[i];
        i += 1;
        match e {
            b'n' => out.push(b'\n'),
            b't' => out.push(b'\t'),
            b'r' => out.push(b'\r'),
            b'b' => out.push(8),
            b'f' => out.push(12),
            b'u' => {
                let mut cp = hex4(raw, i);
                i += 4;
                if (0xD800..0xDC00).contains(&cp)
                    && i + 6 <= n
                    && raw[i] == b'\\'
                    && raw[i + 1] == b'u'
                {
                    let lo = hex4(raw, i + 2);
                    if (0xDC00..0xE000).contains(&lo) {
                        cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
                        i += 6;
                    }
                }
                let ch = char::from_u32(cp).unwrap_or('\u{FFFD}');
                let mut tmp = [0u8; 4];
                out.extend_from_slice(ch.encode_utf8(&mut tmp).as_bytes());
            }
            other => out.push(other),
        }
    }
}

#[inline(always)]
fn key_id(k: &[u8]) -> u8 {
    match k.len() {
        4 => {
            let v = u32::from_le_bytes([k[0], k[1], k[2], k[3]]);
            if v == W_TYPE {
                K_TYPE
            } else if v == W_TAGS {
                K_TAGS
            } else if v == W_META {
                K_META
            } else {
                K_NONE
            }
        }
        6 => {
            if eq(k, b"amount") {
                K_AMOUNT
            } else {
                K_NONE
            }
        }
        7 => {
            if eq(k, b"account") {
                K_ACCOUNT
            } else {
                K_NONE
            }
        }
        8 => {
            if eq(k, b"currency") {
                K_CURRENCY
            } else {
                K_NONE
            }
        }
        _ => K_NONE,
    }
}

#[inline(always)]
fn parse_amount(v: &[u8]) -> i64 {
    let n = v.len();
    let mut whole: i64 = 0;
    let mut j = 0usize;
    while j < n {
        let d = v[j].wrapping_sub(b'0');
        if d > 9 {
            break;
        }
        whole = whole.wrapping_mul(10).wrapping_add(d as i64);
        j += 1;
    }
    let mut frac: i64 = 0;
    if j < n && v[j] == b'.' {
        if j + 1 < n {
            let d = v[j + 1].wrapping_sub(b'0');
            if d <= 9 {
                frac = d as i64 * 10;
            }
        }
        if j + 2 < n {
            let d = v[j + 2].wrapping_sub(b'0');
            if d <= 9 {
                frac += d as i64;
            }
        }
    }
    whole.wrapping_mul(100).wrapping_add(frac)
}

struct State {
    rates: StrMap,
    channels: StrMap,
    accounts: StrMap,
    have_rates: bool,
    counted: u64,
    net: i64,
    scratch: Vec<u8>,
}

impl State {
    fn new() -> Self {
        State {
            rates: StrMap::new(6),
            channels: StrMap::new(6),
            accounts: StrMap::new(16),
            have_rates: false,
            counted: 0,
            net: 0,
            scratch: Vec::with_capacity(256),
        }
    }

    fn process(&mut self, data: &[u8]) {
        let end = data.len();
        let mut pos = 0usize;
        if !self.have_rates && data.starts_with(&[0xEF, 0xBB, 0xBF]) {
            pos = 3;
        }
        loop {
            while pos < end && data[pos] <= b' ' {
                pos += 1;
            }
            if pos >= end {
                break;
            }
            if self.have_rates {
                pos = self.parse_tx(data, pos);
            } else {
                pos = self.parse_rates(data, pos);
                self.have_rates = true;
            }
        }
    }

    fn parse_rates(&mut self, buf: &[u8], pos: usize) -> usize {
        let n = buf.len();
        let mut i = pos;
        if buf[i] == b'{' {
            i += 1;
            loop {
                i = skip_ws(buf, i);
                if buf[i] != b'"' {
                    break;
                }
                let ks = i + 1;
                let (ke, kesc) = scan_string(buf, ks);
                i = skip_ws(buf, ke + 1);
                i = skip_ws(buf, i + 1);
                let is_rates = if kesc {
                    decode(&buf[ks..ke], &mut self.scratch);
                    eq(&self.scratch[..], b"rates")
                } else {
                    eq(&buf[ks..ke], b"rates")
                };
                if is_rates && buf[i] == b'{' {
                    i += 1;
                    loop {
                        i = skip_ws(buf, i);
                        let c = buf[i];
                        if c == b'}' {
                            i += 1;
                            break;
                        }
                        if c != b'"' {
                            i += 1;
                            continue;
                        }
                        let cs = i + 1;
                        let (ce, cesc) = scan_string(buf, cs);
                        i = skip_ws(buf, ce + 1);
                        i = skip_ws(buf, i + 1);
                        let mut neg = false;
                        if buf[i] == b'-' {
                            neg = true;
                            i += 1;
                        }
                        let mut v: i64 = 0;
                        while i < n {
                            let d = buf[i].wrapping_sub(b'0');
                            if d > 9 {
                                break;
                            }
                            v = v.wrapping_mul(10).wrapping_add(d as i64);
                            i += 1;
                        }
                        while i < n {
                            let c2 = buf[i];
                            if c2 <= b' ' || c2 == b',' || c2 == b'}' || c2 == b']' {
                                break;
                            }
                            i += 1;
                        }
                        if neg {
                            v = -v;
                        }
                        let name: &[u8] = if cesc {
                            decode(&buf[cs..ce], &mut self.scratch);
                            &self.scratch[..]
                        } else {
                            &buf[cs..ce]
                        };
                        let id = self.rates.entry(name);
                        self.rates.entries[id].net = v;
                    }
                } else {
                    i = skip_value(buf, i);
                }
                i = skip_ws(buf, i);
                if buf[i] != b',' {
                    break;
                }
                i += 1;
            }
        }
        let nl = find_newline(buf, i);
        if nl < n { nl + 1 } else { n }
    }

    #[inline]
    fn parse_tx(&mut self, buf: &[u8], pos: usize) -> usize {
        let mut i = pos;
        let mut mask = 0u32;
        let mut neg = false;
        let mut hundredths = 0i64;
        let mut rate = 0i64;
        let (mut acc_s, mut acc_e, mut acc_esc) = (0usize, 0usize, false);
        let (mut ch_s, mut ch_e, mut ch_esc) = (0usize, 0usize, false);
        let mut skip = false;

        if buf[i] == b'{' {
            i += 1;
            'line: loop {
                i = skip_ws(buf, i);
                if buf[i] != b'"' {
                    break;
                }
                let ks = i + 1;
                let (ke, kesc) = scan_string(buf, ks);
                i = skip_ws(buf, ke + 1);
                i = skip_ws(buf, i + 1);
                let kid = if kesc {
                    decode(&buf[ks..ke], &mut self.scratch);
                    key_id(&self.scratch[..])
                } else {
                    key_id(&buf[ks..ke])
                };
                let c = buf[i];
                match kid {
                    K_TYPE if c == b'"' => {
                        let s = i + 1;
                        let (e, esc) = scan_string(buf, s);
                        i = e + 1;
                        let t: &[u8] = if esc {
                            decode(&buf[s..e], &mut self.scratch);
                            &self.scratch[..]
                        } else {
                            &buf[s..e]
                        };
                        if eq(t, b"void") {
                            skip = true;
                            break 'line;
                        }
                        neg = eq(t, b"debit");
                        mask |= M_TYPE;
                    }
                    K_AMOUNT if c == b'"' => {
                        let s = i + 1;
                        let (e, esc) = scan_string(buf, s);
                        i = e + 1;
                        let t: &[u8] = if esc {
                            decode(&buf[s..e], &mut self.scratch);
                            &self.scratch[..]
                        } else {
                            &buf[s..e]
                        };
                        hundredths = parse_amount(t);
                        mask |= M_AMOUNT;
                    }
                    K_CURRENCY if c == b'"' => {
                        let s = i + 1;
                        let (e, esc) = scan_string(buf, s);
                        i = e + 1;
                        let t: &[u8] = if esc {
                            decode(&buf[s..e], &mut self.scratch);
                            &self.scratch[..]
                        } else {
                            &buf[s..e]
                        };
                        rate = self.rates.get(t).unwrap_or(0);
                        mask |= M_CURRENCY;
                    }
                    K_ACCOUNT if c == b'"' => {
                        let s = i + 1;
                        let (e, esc) = scan_string(buf, s);
                        i = e + 1;
                        acc_s = s;
                        acc_e = e;
                        acc_esc = esc;
                        mask |= M_ACCOUNT;
                    }
                    K_TAGS if c == b'[' => {
                        i += 1;
                        loop {
                            i = skip_ws(buf, i);
                            let c2 = buf[i];
                            if c2 == b'"' {
                                let s = i + 1;
                                let (e, esc) = scan_string(buf, s);
                                i = e + 1;
                                let is_test = if esc {
                                    decode(&buf[s..e], &mut self.scratch);
                                    eq(&self.scratch[..], b"test")
                                } else {
                                    e - s == 4 && eq(&buf[s..e], b"test")
                                };
                                if is_test {
                                    skip = true;
                                    break 'line;
                                }
                            } else if c2 == b']' {
                                i += 1;
                                break;
                            } else if c2 == b',' {
                                i += 1;
                            } else {
                                i = skip_value(buf, i);
                            }
                        }
                        mask |= M_TAGS;
                    }
                    K_META if c == b'{' => {
                        i += 1;
                        loop {
                            i = skip_ws(buf, i);
                            let c2 = buf[i];
                            if c2 == b'}' {
                                i += 1;
                                break;
                            }
                            if c2 != b'"' {
                                i += 1;
                                continue;
                            }
                            let mks = i + 1;
                            let (mke, mkesc) = scan_string(buf, mks);
                            i = skip_ws(buf, mke + 1);
                            i = skip_ws(buf, i + 1);
                            let is_channel = if mkesc {
                                decode(&buf[mks..mke], &mut self.scratch);
                                eq(&self.scratch[..], b"channel")
                            } else {
                                mke - mks == 7 && eq(&buf[mks..mke], b"channel")
                            };
                            if is_channel && buf[i] == b'"' {
                                let s = i + 1;
                                let (e, esc) = scan_string(buf, s);
                                i = e + 1;
                                ch_s = s;
                                ch_e = e;
                                ch_esc = esc;
                                mask |= M_CHANNEL;
                                if mask == M_ALL {
                                    break 'line;
                                }
                            } else {
                                i = skip_value(buf, i);
                            }
                        }
                    }
                    _ => {
                        i = skip_value(buf, i);
                    }
                }
                if mask == M_ALL {
                    break;
                }
                i = skip_ws(buf, i);
                if buf[i] != b',' {
                    break;
                }
                i += 1;
            }
        }

        let n = buf.len();
        let nl = find_newline(buf, i);
        let next = if nl < n { nl + 1 } else { n };

        if !skip && (mask & M_REQ) == M_REQ {
            let usd = hundredths.wrapping_mul(rate).div_euclid(1_000_000);
            let val = if neg { -usd } else { usd };
            self.counted += 1;
            self.net += val;
            {
                let ch: &[u8] = if ch_esc {
                    decode(&buf[ch_s..ch_e], &mut self.scratch);
                    &self.scratch[..]
                } else {
                    &buf[ch_s..ch_e]
                };
                let id = self.channels.entry(ch);
                let e = &mut self.channels.entries[id];
                e.count += 1;
                e.net += val;
            }
            {
                let ac: &[u8] = if acc_esc {
                    decode(&buf[acc_s..acc_e], &mut self.scratch);
                    &self.scratch[..]
                } else {
                    &buf[acc_s..acc_e]
                };
                let id = self.accounts.entry(ac);
                let e = &mut self.accounts.entries[id];
                e.count += 1;
                e.net += val;
            }
        }
        next
    }
}

fn main() {
    let path = std::env::args_os().nth(1).expect("missing input path");
    let mut file = File::open(path).expect("cannot open input");
    let mut st = State::new();
    let mut buf = vec![0u8; CHUNK];
    let mut filled = 0usize;

    loop {
        let n = match file.read(&mut buf[filled..]) {
            Ok(n) => n,
            Err(e) if e.kind() == std::io::ErrorKind::Interrupted => continue,
            Err(e) => panic!("read error: {}", e),
        };
        if n == 0 {
            if filled > 0 {
                st.process(&buf[..filled]);
            }
            break;
        }
        let old = filled;
        filled += n;
        if let Some(p) = buf[old..filled].iter().rposition(|&b| b == b'\n') {
            let p = old + p;
            st.process(&buf[..p + 1]);
            buf.copy_within(p + 1..filled, 0);
            filled -= p + 1;
        }
        if filled == buf.len() {
            let l = buf.len();
            buf.resize(l * 2, 0);
        }
    }

    let mut out = String::new();
    let _ = writeln!(out, "counted {}", st.counted);
    let _ = writeln!(out, "net {}", st.net);

    let mut chans: Vec<(&[u8], u64, i64)> = st
        .channels
        .entries
        .iter()
        .map(|e| (st.channels.key(e), e.count, e.net))
        .collect();
    chans.sort_unstable_by(|a, b| a.0.cmp(b.0));
    for (name, c, nt) in &chans {
        let _ = writeln!(out, "channel {} {} {}", String::from_utf8_lossy(name), c, nt);
    }

    let mut accs: Vec<(i64, &[u8])> = st
        .accounts
        .entries
        .iter()
        .map(|e| (e.net, st.accounts.key(e)))
        .collect();
    let cmp = |a: &(i64, &[u8]), b: &(i64, &[u8])| b.0.cmp(&a.0).then_with(|| a.1.cmp(b.1));
    if accs.len() > 10 {
        accs.select_nth_unstable_by(9, cmp);
        accs.truncate(10);
    }
    accs.sort_unstable_by(cmp);
    for (nt, name) in &accs {
        let _ = writeln!(out, "account {} {}", String::from_utf8_lossy(name), nt);
    }

    let stdout = std::io::stdout();
    let mut lock = stdout.lock();
    let _ = lock.write_all(out.as_bytes());
    let _ = lock.flush();
}
