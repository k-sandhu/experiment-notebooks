use std::collections::HashMap;
use std::fs::File;
use std::io::{Read, Write};

const ONES: u64 = 0x0101_0101_0101_0101;
const HIGH: u64 = 0x8080_8080_8080_8080;
const LOWER: u64 = 0x2020_2020_2020_2020;
const MM: u64 = 0x0002_0408_1020_4081;
const FLAG: u32 = 1 << 31;

#[derive(Clone, Copy)]
struct Entry {
    lo: u64, // 0 means empty slot (a real word always has a nonzero first byte)
    hi: u64,
    id: u32,
}

struct Vocab {
    table: Vec<Entry>,
    mask: usize,
    n_short: usize,
    next_id: u32,
    arena: Vec<u8>,
    offs: Vec<(usize, usize)>,
    first_cnt: Vec<u32>,
    long: HashMap<Vec<u8>, u32>,
    scratch: Vec<u8>,
}

#[inline(always)]
fn hash(lo: u64, hi: u64) -> u64 {
    let x = lo ^ hi.wrapping_mul(0x9E37_79B9_7F4A_7C15);
    let m = (x as u128) * (0xD6E8_FEB8_6659_FD93u64 as u128);
    ((m >> 64) as u64) ^ (m as u64)
}

impl Vocab {
    fn new() -> Self {
        let cap = 1usize << 16;
        Vocab {
            table: vec![Entry { lo: 0, hi: 0, id: 0 }; cap],
            mask: cap - 1,
            n_short: 0,
            next_id: 0,
            arena: Vec::with_capacity(1 << 20),
            offs: Vec::with_capacity(1 << 16),
            first_cnt: Vec::with_capacity(1 << 16),
            long: HashMap::new(),
            scratch: Vec::new(),
        }
    }

    #[inline(always)]
    fn word(&self, id: usize) -> &[u8] {
        let (o, l) = self.offs[id];
        &self.arena[o..o + l]
    }

    #[inline(always)]
    fn get_short(&mut self, lo: u64, hi: u64) -> u32 {
        let mut i = (hash(lo, hi) as usize) & self.mask;
        loop {
            // SAFETY: i <= mask = table.len() - 1
            let e = unsafe { *self.table.get_unchecked(i) };
            if e.lo == lo && e.hi == hi {
                return e.id;
            }
            if e.lo == 0 {
                return self.insert_short(i, lo, hi);
            }
            i = (i + 1) & self.mask;
        }
    }

    #[cold]
    #[inline(never)]
    fn insert_short(&mut self, i: usize, lo: u64, hi: u64) -> u32 {
        let id = self.next_id;
        self.next_id += 1;
        self.table[i] = Entry { lo, hi, id };
        self.n_short += 1;
        let start = self.arena.len();
        let mut len = 0usize;
        let lb = lo.to_le_bytes();
        let hb = hi.to_le_bytes();
        for &b in lb.iter().chain(hb.iter()) {
            if b != 0 {
                self.arena.push(b);
                len += 1;
            }
        }
        self.offs.push((start, len));
        self.first_cnt.push(0);
        if self.n_short * 4 > self.table.len() * 3 {
            self.grow();
        }
        id
    }

    fn grow(&mut self) {
        let new_len = self.table.len() * 2;
        let mask = new_len - 1;
        let mut t = vec![Entry { lo: 0, hi: 0, id: 0 }; new_len];
        for e in &self.table {
            if e.lo != 0 {
                let mut i = (hash(e.lo, e.hi) as usize) & mask;
                while t[i].lo != 0 {
                    i = (i + 1) & mask;
                }
                t[i] = *e;
            }
        }
        self.table = t;
        self.mask = mask;
    }

    #[cold]
    #[inline(never)]
    fn get_long(&mut self, w: &[u8]) -> u32 {
        self.scratch.clear();
        self.scratch.extend(w.iter().map(|b| b | 0x20));
        if let Some(&id) = self.long.get(self.scratch.as_slice()) {
            return id;
        }
        let id = self.next_id;
        self.next_id += 1;
        let start = self.arena.len();
        self.arena.extend_from_slice(&self.scratch);
        self.offs.push((start, self.scratch.len()));
        self.first_cnt.push(0);
        self.long.insert(self.scratch.clone(), id);
        id
    }
}

#[inline(always)]
fn block_masks(b: &[u8; 64]) -> (u64, u64) {
    let mut l = 0u64;
    let mut e = 0u64;
    for k in 0..8 {
        let v = u64::from_le_bytes(b[k * 8..k * 8 + 8].try_into().unwrap());
        let x7 = v & !HIGH;
        let ascii = !v & HIGH;
        let x = x7 | LOWER;
        let letter = x.wrapping_add(0x1F * ONES) & !x.wrapping_add(0x05 * ONES) & ascii;
        let n1 = (x7 ^ (0x2E * ONES)).wrapping_add(0x7F * ONES);
        let n2 = (x7 ^ (0x21 * ONES)).wrapping_add(0x7F * ONES);
        let n3 = (x7 ^ (0x3F * ONES)).wrapping_add(0x7F * ONES);
        let end = !(n1 & n2 & n3) & ascii;
        l |= (letter.wrapping_mul(MM) >> 56) << (k * 8);
        e |= (end.wrapping_mul(MM) >> 56) << (k * 8);
    }
    (l, e)
}

#[inline(always)]
fn rd(d: &[u8], p: usize) -> u64 {
    u64::from_le_bytes(d[p..p + 8].try_into().unwrap())
}

#[cold]
#[inline(never)]
fn prune(cand: &mut Vec<(u32, u32, u32)>) {
    cand.sort_unstable_by(|x, y| y.cmp(x));
    cand.truncate(20);
}

fn main() {
    let path = std::env::args_os().nth(1).expect("missing input path");
    let mut f = File::open(&path).expect("cannot open input");
    let flen = f.metadata().map(|m| m.len() as usize).unwrap_or(0);
    let mut data: Vec<u8> = Vec::with_capacity(flen + 256);
    f.read_to_end(&mut data).expect("cannot read input");
    drop(f);
    let n = data.len();
    let padded = (n / 64 + 2) * 64;
    data.resize(padded, 0);
    let data = data;
    let nblocks = padded / 64 - 1;

    let mut vocab = Vocab::new();
    let mut seq: Vec<u32> = Vec::with_capacity(n / 2 + 16);

    let mut in_word = false;
    let mut start = 0usize;
    let mut brk = true;
    let mut prev = 0usize;
    let mut carry = 0u64;

    for (bi, chunk) in data.chunks_exact(64).take(nblocks).enumerate() {
        let base = bi * 64;
        let (l, mut e) = block_masks(chunk.try_into().unwrap());
        let mut t = l ^ ((l << 1) | carry);
        carry = l >> 63;
        loop {
            if !in_word {
                if t == 0 {
                    break;
                }
                let s = t.trailing_zeros();
                t &= t - 1;
                brk |= (e & ((1u64 << s) - 1)) != 0;
                start = base + s as usize;
                in_word = true;
            }
            if t == 0 {
                break;
            }
            let p = t.trailing_zeros();
            t &= t - 1;
            e &= !0u64 << p;
            in_word = false;
            let end = base + p as usize;
            let len = end - start;
            let id = if len <= 16 {
                let mut lo = rd(&data, start) | LOWER;
                let mut hi = 0u64;
                if len <= 8 {
                    lo &= !0u64 >> (64 - 8 * len);
                } else {
                    hi = (rd(&data, start + 8) | LOWER) & (!0u64 >> (128 - 8 * len));
                }
                vocab.get_short(lo, hi)
            } else {
                vocab.get_long(&data[start..end])
            };
            let nb = (!brk) as u32;
            vocab.first_cnt[prev] += nb;
            seq.push(id | ((brk as u32) << 31));
            prev = id as usize;
            brk = false;
        }
        brk |= e != 0;
    }

    let w = seq.len();
    let v = vocab.next_id as usize;
    let total: u64 = vocab.first_cnt.iter().map(|&c| c as u64).sum();

    // Bucket second words by first word.
    let mut pos = vec![0u32; v + 1];
    let mut acc = 0u32;
    for i in 0..v {
        pos[i] = acc;
        acc = acc.wrapping_add(vocab.first_cnt[i]);
    }
    pos[v] = acc;
    let dummy = total as usize;
    let mut buf = vec![0u32; dummy + 1];
    let mut prev = 0usize;
    for &x in &seq {
        let id = x & !FLAG;
        let nb = (x >> 31) ^ 1;
        let p = pos[prev];
        let idx = if nb != 0 { p as usize } else { dummy };
        buf[idx] = id;
        pos[prev] = p + nb;
        prev = id as usize;
    }
    drop(seq);

    // Lexicographic rank of each word.
    let mut order: Vec<u32> = (0..v as u32).collect();
    order.sort_unstable_by(|&a, &b| vocab.word(a as usize).cmp(vocab.word(b as usize)));
    let mut rank = vec![0u32; v];
    for (r, &id) in order.iter().enumerate() {
        rank[id as usize] = r as u32;
    }

    // Count pairs per first-word bucket.
    let mut cntb = vec![0u32; v];
    let mut cand: Vec<(u32, u32, u32)> = Vec::with_capacity(1100);
    let mut thr = (0u32, 0u32, 0u32);
    let mut distinct = 0u64;
    let mut bstart = 0usize;
    for a in 0..v {
        let bend = pos[a] as usize;
        if bend == bstart {
            continue;
        }
        let slice = &buf[bstart..bend];
        bstart = bend;
        for &b in slice {
            cntb[b as usize] += 1;
        }
        let ka = !rank[a];
        for &b in slice {
            let c = cntb[b as usize];
            if c != 0 {
                cntb[b as usize] = 0;
                distinct += 1;
                if c >= thr.0 {
                    let key = (c, ka, !rank[b as usize]);
                    if key > thr {
                        cand.push(key);
                        if cand.len() >= 1024 {
                            prune(&mut cand);
                            thr = cand[19];
                        }
                    }
                }
            }
        }
    }

    cand.sort_unstable_by(|x, y| y.cmp(x));
    cand.truncate(20);

    let mut out: Vec<u8> = Vec::with_capacity(4096);
    write!(out, "words {}\npairs {}\ndistinct {}\n", w, total, distinct).unwrap();
    for &(c, ka, kb) in &cand {
        let a = order[(!ka) as usize] as usize;
        let b = order[(!kb) as usize] as usize;
        write!(out, "{} ", c).unwrap();
        out.extend_from_slice(vocab.word(a));
        out.push(b' ');
        out.extend_from_slice(vocab.word(b));
        out.push(b'\n');
    }
    let stdout = std::io::stdout();
    let mut lock = stdout.lock();
    lock.write_all(&out).unwrap();
    lock.flush().unwrap();
}
