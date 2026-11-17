// Word pairs: count adjacent word pairs within sentences, report top 20.
//
// Single pass over the lowercased input. Words are interned into ids with an
// open-addressing table keyed by (hash, bytes); pairs are counted in an
// open-addressing table keyed by (id1 << 32 | id2).

use std::fs;
use std::io::{BufWriter, Write};

const EMPTY: u32 = u32::MAX;

struct Interner<'a> {
    data: &'a [u8],
    mask: u64,
    slots: Vec<u32>,              // entry index per slot, EMPTY = free
    words: Vec<(u32, u32)>,       // (offset, len) in data, index = word id
    hashes: Vec<u64>,
}

impl<'a> Interner<'a> {
    fn new(data: &'a [u8]) -> Self {
        Interner {
            data,
            mask: 0,
            slots: Vec::new(),
            words: Vec::new(),
            hashes: Vec::new(),
        }
    }

    fn grow(&mut self) {
        // Double the slot array and rehash every word in id order.
        let new_cap = if self.slots.is_empty() { 1 << 12 } else { self.slots.len() * 2 };
        self.mask = (new_cap - 1) as u64;
        self.slots = vec![EMPTY; new_cap];
        for id in 0..self.words.len() {
            let mut idx = (self.hashes[id] & self.mask) as usize;
            while self.slots[idx] != EMPTY {
                idx = (idx + 1) & self.mask as usize;
            }
            self.slots[idx] = id as u32;
        }
    }

    fn intern(&mut self, h: u64, off: u32, len: u32) -> u32 {
        if self.words.len() + 1 >= self.slots.len() * 3 / 4 {
            self.grow();
        }
        let word = &self.data[off as usize..(off + len) as usize];
        let mut idx = (h & self.mask) as usize;
        loop {
            let slot = self.slots[idx];
            if slot == EMPTY {
                let id = self.words.len() as u32;
                self.words.push((off, len));
                self.hashes.push(h);
                self.slots[idx] = id;
                return id;
            }
            let s = slot as usize;
            if self.hashes[s] == h {
                let (o, l) = self.words[s];
                if len == l && &self.data[o as usize..(o + l) as usize] == word {
                    return s as u32;
                }
            }
            idx = (idx + 1) & self.mask as usize;
        }
    }
}

struct PairTable {
    mask: u64,
    keys: Vec<u64>,
    counts: Vec<u32>,
    used: usize,
    total: u64,
}

impl PairTable {
    fn new() -> Self {
        PairTable {
            mask: 0,
            keys: Vec::new(),
            counts: Vec::new(),
            used: 0,
            total: 0,
        }
    }

    fn add(&mut self, key: u64) {
        if self.used + 1 >= self.keys.len() * 3 / 4 {
            let old_keys = std::mem::take(&mut self.keys);
            let old_counts = std::mem::take(&mut self.counts);
            let new_cap = if old_keys.is_empty() { 1 << 12 } else { old_keys.len() * 2 };
            self.mask = (new_cap - 1) as u64;
            self.keys = vec![0; new_cap];
            self.counts = vec![0; new_cap];
            for (k, c) in old_keys.into_iter().zip(old_counts) {
                if c == 0 {
                    continue;
                }
                let mut idx = (mix(k) & self.mask) as usize;
                while self.counts[idx] != 0 {
                    idx = (idx + 1) & self.mask as usize;
                }
                self.keys[idx] = k;
                self.counts[idx] = c;
            }
        }
        let mut idx = (mix(key) & self.mask) as usize;
        loop {
            if self.counts[idx] == 0 {
                self.keys[idx] = key;
                self.counts[idx] = 1;
                self.used += 1;
                self.total += 1;
                return;
            }
            if self.keys[idx] == key {
                self.counts[idx] += 1;
                self.total += 1;
                return;
            }
            idx = (idx + 1) & self.mask as usize;
        }
    }
}

#[inline]
fn mix(mut h: u64) -> u64 {
    h = h.wrapping_mul(0x9E3779B97F4A7C15);
    h ^= h >> 29;
    h = h.wrapping_mul(0xBF58476D1CE4E5B9);
    h ^ (h >> 32)
}

#[inline]
fn hash_word(word: &[u8]) -> u64 {
    let mut h: u64 = 0xCBF29CE484222325;
    for &b in word {
        h = (h ^ b as u64).wrapping_mul(0x100000001B3);
    }
    h
}

fn main() {
    let path = std::env::args().nth(1).expect("usage: solution INPUT");
    let data = fs::read(&path).expect("cannot read input");

    // Lowercased copy; word slices are borrowed from it.
    let mut low = data;
    for b in low.iter_mut() {
        if b.is_ascii_uppercase() {
            *b += 32;
        }
    }

    // Byte classes: 0 = separator, 1 = letter, 2 = sentence end.
    let mut cls = [0u8; 256];
    for (i, c) in cls.iter_mut().enumerate() {
        let b = i as u8;
        *c = if b.is_ascii_alphabetic() {
            1
        } else if b == b'.' || b == b'!' || b == b'?' {
            2
        } else {
            0
        };
    }

    let mut interner = Interner::new(&low);
    let mut pairs = PairTable::new();
    let mut total_words: u64 = 0;
    let mut prev: Option<u32> = None;

    let n = low.len();
    let mut i = 0usize;
    while i < n {
        let c = cls[low[i] as usize];
        if c == 1 {
            let start = i;
            i += 1;
            while i < n && cls[low[i] as usize] == 1 {
                i += 1;
            }
            let id = interner.intern(hash_word(&low[start..i]), start as u32, (i - start) as u32);
            total_words += 1;
            if let Some(p) = prev {
                pairs.add(((p as u64) << 32) | id as u64);
            }
            prev = Some(id);
        } else {
            if c == 2 {
                prev = None;
            }
            i += 1;
        }
    }

    // Collect distinct pairs.
    let mut items: Vec<(u64, u32, u32, u32)> = Vec::with_capacity(pairs.used);
    for idx in 0..pairs.keys.len() {
        let cnt = pairs.counts[idx];
        if cnt != 0 {
            let key = pairs.keys[idx];
            items.push((key, cnt, (key >> 32) as u32, (key & 0xFFFF_FFFF) as u32));
        }
    }

    // Sort by count desc, then first word asc, then second word asc.
    let words = &interner.words;
    let lowbuf = &low;
    let cmp = |x: &(u64, u32, u32, u32), y: &(u64, u32, u32, u32)| -> std::cmp::Ordering {
        y.1.cmp(&x.1)
            .then_with(|| {
                let (ox, oy) = (words[x.2 as usize], words[y.2 as usize]);
                lowbuf[ox.0 as usize..ox.0 as usize + ox.1 as usize]
                    .cmp(&lowbuf[oy.0 as usize..oy.0 as usize + oy.1 as usize])
            })
            .then_with(|| {
                let (ox, oy) = (words[x.3 as usize], words[y.3 as usize]);
                lowbuf[ox.0 as usize..ox.0 as usize + ox.1 as usize]
                    .cmp(&lowbuf[oy.0 as usize..oy.0 as usize + oy.1 as usize])
            })
    };
    let top = items.len().min(20);
    if items.len() > top {
        items.select_nth_unstable_by(top - 1, cmp);
    }
    items[..top].sort_unstable_by(cmp);

    let out = std::io::stdout();
    let mut w = BufWriter::with_capacity(1 << 16, out.lock());
    let _ = writeln!(w, "words {}", total_words);
    let _ = writeln!(w, "pairs {}", pairs.total);
    let _ = writeln!(w, "distinct {}", items.len());
    let mut nbuf = [0u8; 20];
    for it in &items[..top] {
        let (o1, l1) = words[it.2 as usize];
        let (o2, l2) = words[it.3 as usize];
        let _ = w.write_all(itoa(it.1 as u64, &mut nbuf));
        let _ = w.write_all(b" ");
        let _ = w.write_all(&lowbuf[o1 as usize..o1 as usize + l1 as usize]);
        let _ = w.write_all(b" ");
        let _ = w.write_all(&lowbuf[o2 as usize..o2 as usize + l2 as usize]);
        let _ = w.write_all(b"\n");
    }
    let _ = w.flush();
}

// Write u64 as decimal digits, return the printable slice.
fn itoa(mut v: u64, buf: &mut [u8; 20]) -> &[u8] {
    let mut i = buf.len();
    loop {
        i -= 1;
        buf[i] = b'0' + (v % 10) as u8;
        v /= 10;
        if v == 0 {
            break;
        }
    }
    &buf[i..]
}
