use std::fs::File;
use std::io::{Read, Write};

const L: u64 = 0x0101_0101_0101_0101;
const H: u64 = 0x8080_8080_8080_8080;
const M7: u64 = 0x7F7F_7F7F_7F7F_7F7F;
const NIB: u64 = 0x0F0F_0F0F_0F0F_0F0F;

const CHUNK: usize = 1 << 19;
const PAD: usize = 16;

type Pat = (u64, u64, u64);

/// Builds (mask, expect, add) for a pattern of up to 8 bytes; '#' means an ASCII digit.
const fn pat(p: &[u8]) -> Pat {
    let mut m = 0u64;
    let mut e = 0u64;
    let mut a = 0u64;
    let mut j = 0;
    while j < p.len() {
        let sh = 8 * j as u32;
        if p[j] == b'#' {
            m |= 0xF0u64 << sh;
            e |= 0x30u64 << sh;
            a |= 0x06u64 << sh;
        } else {
            m |= 0xFFu64 << sh;
            e |= (p[j] as u64) << sh;
        }
        j += 1;
    }
    (m, e, a)
}

const fn word(s: &[u8]) -> u64 {
    let mut v = 0u64;
    let mut j = 0;
    while j < s.len() {
        v |= (s[j] as u64) << (8 * j as u32);
        j += 1;
    }
    v
}

const TS0: Pat = pat(b"####-##-");
const TS1: Pat = pat(b"##T##:##");
const TS2: Pat = pat(b":##.###Z");
const STATUS: Pat = pat(b"### ");
const TAIL: Pat = pat(b".#ms \"");

const GET: u64 = word(b"GET ");
const PUT: u64 = word(b"PUT ");
const POST: u64 = word(b"POST ");
const PATCH: u64 = word(b"PATCH ");
const DELETE: u64 = word(b"DELETE ");

const SPACES: u64 = 0x20 * L;
const NLS: u64 = 0x0A * L;
const QUOTES: u64 = 0x22 * L;

#[inline(always)]
fn load(d: &[u8], i: usize) -> u64 {
    u64::from_le_bytes(d[i..i + 8].try_into().unwrap())
}

#[inline(always)]
fn mismatch(w: u64, p: Pat) -> u64 {
    ((w & p.0) ^ p.1) | ((w.wrapping_add(p.2) & p.0) ^ p.1)
}

/// 0x80 in every byte that is not an ASCII digit (exact per byte).
#[inline(always)]
fn nondigit(w: u64) -> u64 {
    let b = w & M7;
    (!(b + 0x50 * L) | (b + 0x46 * L) | w) & H
}

/// 0x80 in every byte that is not a-z (exact per byte).
#[inline(always)]
fn nonlower(w: u64) -> u64 {
    let b = w & M7;
    (!(b + 0x1F * L) | (b + 0x05 * L) | w) & H
}

/// 0x80 in every byte that differs from c (exact per byte).
#[inline(always)]
fn noteq(w: u64, c: u8) -> u64 {
    let x = w ^ (c as u64 * L);
    (((x & M7) + M7) | x) & H
}

/// 0x80 in every byte that is not in [A-Za-z0-9_-].
#[inline(always)]
fn nonseg(w: u64, nd: u64) -> u64 {
    nd & nonlower(w | SPACES) & noteq(w, b'_') & noteq(w, b'-')
}

/// Lowest set bit marks the first zero byte.
#[inline(always)]
fn haszero(x: u64) -> u64 {
    x.wrapping_sub(L) & !x & H
}

#[inline(always)]
fn skip_digits(d: &[u8], mut i: usize) -> usize {
    loop {
        let m = nondigit(load(d, i));
        if m != 0 {
            return i + (m.trailing_zeros() >> 3) as usize;
        }
        i += 8;
    }
}

#[inline(always)]
fn skip_lower(d: &[u8], mut i: usize) -> usize {
    loop {
        let m = nonlower(load(d, i));
        if m != 0 {
            return i + (m.trailing_zeros() >> 3) as usize;
        }
        i += 8;
    }
}

#[inline(always)]
fn find_nl(d: &[u8], mut i: usize) -> usize {
    loop {
        let m = haszero(load(d, i) ^ NLS);
        if m != 0 {
            return i + (m.trailing_zeros() >> 3) as usize;
        }
        i += 8;
    }
}

/// Parses 8 digit values (one per byte, most significant in the lowest byte).
#[inline(always)]
fn parse8(v: u64) -> u64 {
    const MASK: u64 = 0x0000_00FF_0000_00FF;
    const MUL1: u64 = 0x000F_4240_0000_0064;
    const MUL2: u64 = 0x0000_2710_0000_0001;
    let v = v.wrapping_mul(10).wrapping_add(v >> 8);
    ((v & MASK)
        .wrapping_mul(MUL1)
        .wrapping_add(((v >> 16) & MASK).wrapping_mul(MUL2)))
        >> 32
}

#[inline(always)]
fn hash_key(k: &[u8]) -> u64 {
    const K: u64 = 0x9E37_79B9_7F4A_7C15;
    let mut h = k.len() as u64;
    let mut it = k.chunks_exact(8);
    for c in &mut it {
        h = (h.rotate_left(5) ^ u64::from_le_bytes(c.try_into().unwrap())).wrapping_mul(K);
    }
    let r = it.remainder();
    if !r.is_empty() {
        let mut t = 0u64;
        for &b in r {
            t = (t << 8) | b as u64;
        }
        h = (h.rotate_left(5) ^ t).wrapping_mul(K);
    }
    h ^ (h >> 32)
}

struct Entry {
    hash: u64,
    key: Box<[u8]>,
    lats: Vec<u64>,
}

struct Table {
    slots: Vec<u32>,
    mask: usize,
    entries: Vec<Entry>,
}

impl Table {
    fn new() -> Self {
        let n = 1024;
        Table {
            slots: vec![0u32; n],
            mask: n - 1,
            entries: Vec::new(),
        }
    }

    #[inline(always)]
    fn record(&mut self, key: &[u8], lat: u64) {
        let h = hash_key(key);
        let mut s = h as usize & self.mask;
        loop {
            let e = self.slots[s];
            if e == 0 {
                break;
            }
            let ent = &mut self.entries[(e - 1) as usize];
            if ent.hash == h && *ent.key == *key {
                ent.lats.push(lat);
                return;
            }
            s = (s + 1) & self.mask;
        }
        self.insert_new(h, s, key, lat);
    }

    #[cold]
    #[inline(never)]
    fn insert_new(&mut self, h: u64, s: usize, key: &[u8], lat: u64) {
        self.entries.push(Entry {
            hash: h,
            key: key.into(),
            lats: vec![lat],
        });
        self.slots[s] = self.entries.len() as u32;
        if self.entries.len() * 2 > self.slots.len() {
            self.grow();
        }
    }

    fn grow(&mut self) {
        let n = self.slots.len() * 2;
        let mask = n - 1;
        let mut slots = vec![0u32; n];
        for (idx, e) in self.entries.iter().enumerate() {
            let mut s = e.hash as usize & mask;
            while slots[s] != 0 {
                s = (s + 1) & mask;
            }
            slots[s] = idx as u32 + 1;
        }
        self.slots = slots;
        self.mask = mask;
    }
}

struct State {
    lines: u64,
    malformed: u64,
    status: [u64; 10],
    tmpl: Vec<u8>,
    table: Table,
}

/// Parses the line starting at `pos`. Requires data[end-1] == b'\n' and data.len() >= end + 8.
/// Returns the index just past the line's newline if the line is well-formed.
#[inline(always)]
fn parse_line(
    data: &[u8],
    pos: usize,
    end: usize,
    tmpl: &mut Vec<u8>,
    table: &mut Table,
    status: &mut [u64; 10],
) -> Option<usize> {
    if pos + 25 > end {
        return None;
    }
    let bad = mismatch(load(data, pos), TS0)
        | mismatch(load(data, pos + 8), TS1)
        | mismatch(load(data, pos + 16), TS2);
    if bad != 0 || data[pos + 24] != b' ' {
        return None;
    }
    let mut i = pos + 25;

    // host: [a-z]+-\d+
    let j = skip_lower(data, i);
    if j == i || data[j] != b'-' {
        return None;
    }
    i = j + 1;
    let j = skip_digits(data, i);
    if j == i || data[j] != b' ' {
        return None;
    }
    i = j + 1;

    // method followed by a space
    let w = load(data, i);
    let w4 = w & 0xFFFF_FFFF;
    let l4 = (w4 == GET) | (w4 == PUT);
    let l5 = (w & 0x0000_00FF_FFFF_FFFF) == POST;
    let l6 = (w & 0x0000_FFFF_FFFF_FFFF) == PATCH;
    let l7 = (w & 0x00FF_FFFF_FFFF_FFFF) == DELETE;
    let mlen = (l4 as usize) * 4 + (l5 as usize) * 5 + (l6 as usize) * 6 + (l7 as usize) * 7;
    if mlen == 0 {
        return None;
    }
    i += mlen;

    // path
    if data[i] != b'/' {
        return None;
    }
    let path_start = i;
    let mut last = i;
    tmpl.clear();
    loop {
        i += 1;
        let seg_start = i;
        let mut alld = true;
        loop {
            let w = load(data, i);
            let nd = nondigit(w);
            let ns = nonseg(w, nd);
            if ns != 0 {
                let t = ns.trailing_zeros();
                alld &= nd.trailing_zeros() == t;
                i += (t >> 3) as usize;
                break;
            }
            alld &= nd == 0;
            i += 8;
        }
        if alld && i != seg_start {
            tmpl.extend_from_slice(&data[last..seg_start]);
            tmpl.extend_from_slice(b"{id}");
            last = i;
        }
        if data[i] != b'/' {
            break;
        }
    }
    let path_end = i;

    // optional query, then a space
    let c = data[i];
    if c == b'?' {
        i += 1;
        loop {
            let w = load(data, i);
            let m = haszero(w ^ SPACES) | haszero(w ^ NLS);
            if m != 0 {
                i += (m.trailing_zeros() >> 3) as usize;
                break;
            }
            i += 8;
        }
        if data[i] != b' ' {
            return None;
        }
    } else if c != b' ' {
        return None;
    }
    i += 1;

    // status: \d{3} and a space
    let w = load(data, i);
    if mismatch(w, STATUS) != 0 {
        return None;
    }
    let class = (w & 0xF) as usize;
    i += 4;

    // size: \d+B and a space
    let j = skip_digits(data, i);
    if j == i || data[j] != b'B' || data[j + 1] != b' ' {
        return None;
    }
    i = j + 2;

    // latency integer part
    let w = load(data, i);
    let m = nondigit(w);
    let v: u64;
    if m != 0 {
        let k = m.trailing_zeros() >> 3;
        if k == 0 {
            return None;
        }
        v = parse8((w << (64 - 8 * k)) & NIB);
        i += k as usize;
    } else {
        let mut x = 0u64;
        while data[i].is_ascii_digit() {
            x = x.wrapping_mul(10).wrapping_add((data[i] - b'0') as u64);
            i += 1;
        }
        v = x;
    }

    // ".<digit>ms " and the opening quote
    let w = load(data, i);
    if mismatch(w, TAIL) != 0 {
        return None;
    }
    let lat = v.wrapping_mul(10).wrapping_add((w >> 8) & 0xF);
    i += 6;

    // user agent up to the closing quote, which must end the line
    loop {
        let w = load(data, i);
        let m = haszero(w ^ QUOTES) | haszero(w ^ NLS);
        if m != 0 {
            i += (m.trailing_zeros() >> 3) as usize;
            break;
        }
        i += 8;
    }
    if data[i] != b'"' || data[i + 1] != b'\n' {
        return None;
    }

    // commit
    status[class] += 1;
    if last == path_start {
        table.record(&data[path_start..path_end], lat);
    } else {
        tmpl.extend_from_slice(&data[last..path_end]);
        table.record(tmpl, lat);
    }
    Some(i + 2)
}

fn process(data: &[u8], end: usize, st: &mut State) {
    assert!(end > 0 && end + 8 <= data.len() && data[end - 1] == b'\n');
    let mut pos = 0;
    while pos < end {
        st.lines += 1;
        match parse_line(data, pos, end, &mut st.tmpl, &mut st.table, &mut st.status) {
            Some(next) => pos = next,
            None => {
                st.malformed += 1;
                pos = find_nl(data, pos) + 1;
            }
        }
    }
}

fn stats(l: &mut [u64]) -> (u64, u64, u64) {
    let n = l.len();
    let max = *l.iter().max().unwrap();
    let r50 = (50 * n + 99) / 100;
    let r95 = (95 * n + 99) / 100;
    if n > 64 && max < (1 << 20) {
        let mut hist = vec![0u32; max as usize + 1];
        for &v in l.iter() {
            hist[v as usize] += 1;
        }
        let mut cum = 0usize;
        let mut p50 = 0u64;
        let mut p95 = 0u64;
        let mut got50 = false;
        for (v, &c) in hist.iter().enumerate() {
            cum += c as usize;
            if !got50 && cum >= r50 {
                p50 = v as u64;
                got50 = true;
            }
            if cum >= r95 {
                p95 = v as u64;
                break;
            }
        }
        (p50, p95, max)
    } else {
        l.sort_unstable();
        (l[r50 - 1], l[r95 - 1], max)
    }
}

fn main() {
    let path = std::env::args_os().nth(1).expect("missing input path");
    let mut f = File::open(path).expect("cannot open input");

    let mut st = State {
        lines: 0,
        malformed: 0,
        status: [0; 10],
        tmpl: Vec::with_capacity(256),
        table: Table::new(),
    };

    let mut cap = CHUNK;
    let mut buf = vec![0u8; cap + PAD];
    let mut have = 0usize;
    loop {
        let mut eof = false;
        while have < cap {
            match f.read(&mut buf[have..cap]) {
                Ok(0) => {
                    eof = true;
                    break;
                }
                Ok(n) => have += n,
                Err(e) if e.kind() == std::io::ErrorKind::Interrupted => {}
                Err(e) => panic!("read error: {e}"),
            }
        }
        if eof {
            if have > 0 {
                if buf[have - 1] != b'\n' {
                    buf[have] = b'\n';
                    have += 1;
                }
                process(&buf, have, &mut st);
            }
            break;
        }
        match buf[..have].iter().rposition(|&b| b == b'\n') {
            Some(p) => {
                let end = p + 1;
                process(&buf, end, &mut st);
                buf.copy_within(end..have, 0);
                have -= end;
            }
            None => {
                cap *= 2;
                buf.resize(cap + PAD, 0);
            }
        }
    }

    let mut out: Vec<u8> = Vec::with_capacity(4096);
    let _ = write!(out, "lines {}\n", st.lines);
    let _ = write!(out, "malformed {}\n", st.malformed);
    for (d, &c) in st.status.iter().enumerate() {
        if c > 0 {
            let _ = write!(out, "status {}xx {}\n", d, c);
        }
    }

    let mut entries = st.table.entries;
    entries.sort_unstable_by(|a, b| {
        b.lats
            .len()
            .cmp(&a.lats.len())
            .then_with(|| a.key.cmp(&b.key))
    });
    for e in entries.iter_mut().take(10) {
        let n = e.lats.len();
        let (p50, p95, max) = stats(&mut e.lats);
        out.extend_from_slice(b"path ");
        out.extend_from_slice(&e.key);
        let _ = write!(
            out,
            " {} {}.{} {}.{} {}.{}\n",
            n,
            p50 / 10,
            p50 % 10,
            p95 / 10,
            p95 % 10,
            max / 10,
            max % 10
        );
    }

    let stdout = std::io::stdout();
    let mut lock = stdout.lock();
    lock.write_all(&out).expect("write failed");
    lock.flush().expect("flush failed");
}
