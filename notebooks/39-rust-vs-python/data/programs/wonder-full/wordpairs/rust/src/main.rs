use std::env;
use std::fmt::Write as _;
use std::fs;
use std::process::exit;

const FNV_OFFSET: u64 = 0xcbf2_9ce4_8422_2325;
const FNV_PRIME: u64 = 0x0000_0100_0000_01b3;
const EMPTY_KEY: u64 = u64::MAX;

#[inline(always)]
fn is_letter(b: u8) -> bool {
    (b | 0x20).wrapping_sub(b'a') < 26
}

struct WordInfo {
    off: u32,
    len: u32,
    hash: u64,
}

struct Interner {
    slots: Vec<u32>, // 0 = empty, else id + 1
    mask: usize,
    arena: Vec<u8>,
    words: Vec<WordInfo>,
}

impl Interner {
    fn new(cap_pow: u32) -> Self {
        let cap = 1usize << cap_pow;
        Interner {
            slots: vec![0; cap],
            mask: cap - 1,
            arena: Vec::with_capacity(1 << 16),
            words: Vec::with_capacity(1 << 15),
        }
    }

    #[inline(always)]
    fn start_idx(hash: u64, mask: usize) -> usize {
        ((hash ^ (hash >> 33)) as usize) & mask
    }

    fn grow(&mut self) {
        let new_cap = self.slots.len() * 2;
        let new_mask = new_cap - 1;
        let mut new_slots = vec![0u32; new_cap];
        for (id, w) in self.words.iter().enumerate() {
            let mut idx = Self::start_idx(w.hash, new_mask);
            while new_slots[idx] != 0 {
                idx = (idx + 1) & new_mask;
            }
            new_slots[idx] = (id as u32) + 1;
        }
        self.slots = new_slots;
        self.mask = new_mask;
    }

    #[inline(always)]
    fn intern(&mut self, raw: &[u8], hash: u64) -> u32 {
        if (self.words.len() + 1) * 10 > self.slots.len() * 7 {
            self.grow();
        }
        let mask = self.mask;
        let mut idx = Self::start_idx(hash, mask);
        loop {
            let slot = self.slots[idx];
            if slot == 0 {
                let id = self.words.len() as u32;
                let off = self.arena.len() as u32;
                self.arena.extend(raw.iter().map(|&b| b | 0x20));
                self.words.push(WordInfo {
                    off,
                    len: raw.len() as u32,
                    hash,
                });
                self.slots[idx] = id + 1;
                return id;
            }
            let id = slot - 1;
            let w = &self.words[id as usize];
            if w.hash == hash && w.len as usize == raw.len() {
                let stored = &self.arena[w.off as usize..(w.off + w.len) as usize];
                if stored.iter().zip(raw).all(|(&s, &r)| s == (r | 0x20)) {
                    return id;
                }
            }
            idx = (idx + 1) & mask;
        }
    }

    #[inline(always)]
    fn word(&self, id: u32) -> &[u8] {
        let w = &self.words[id as usize];
        &self.arena[w.off as usize..(w.off + w.len) as usize]
    }
}

#[derive(Clone, Copy)]
struct PairEntry {
    key: u64,
    val: u32,
}

struct PairTable {
    // Key and count in a single array so a probe touches one cache line.
    entries: Vec<PairEntry>,
    mask: usize,
    len: usize,
    grow_at: usize,
}

impl PairTable {
    fn new(cap_pow: u32) -> Self {
        let cap = 1usize << cap_pow;
        PairTable {
            entries: vec![
                PairEntry {
                    key: EMPTY_KEY,
                    val: 0
                };
                cap
            ],
            mask: cap - 1,
            len: 0,
            grow_at: cap * 7 / 10,
        }
    }

    #[inline(always)]
    fn start_idx(key: u64, mask: usize) -> usize {
        let h = key.wrapping_mul(0x9E37_79B9_7F4A_7C15);
        ((h ^ (h >> 32)) as usize) & mask
    }

    fn grow(&mut self) {
        let new_cap = self.entries.len() * 2;
        let new_mask = new_cap - 1;
        let mut new_entries = vec![
            PairEntry {
                key: EMPTY_KEY,
                val: 0
            };
            new_cap
        ];
        for &e in self.entries.iter() {
            if e.key != EMPTY_KEY {
                let mut idx = Self::start_idx(e.key, new_mask);
                while new_entries[idx].key != EMPTY_KEY {
                    idx = (idx + 1) & new_mask;
                }
                new_entries[idx] = e;
            }
        }
        self.entries = new_entries;
        self.mask = new_mask;
        self.grow_at = new_cap * 7 / 10;
    }

    #[inline(always)]
    fn inc(&mut self, key: u64) {
        if self.len >= self.grow_at {
            self.grow();
        }
        let mask = self.mask;
        let mut idx = Self::start_idx(key, mask);
        loop {
            let e = &mut self.entries[idx];
            if e.key == EMPTY_KEY {
                e.key = key;
                e.val = 1;
                self.len += 1;
                return;
            }
            if e.key == key {
                e.val += 1;
                return;
            }
            idx = (idx + 1) & mask;
        }
    }
}

fn main() {
    let path = match env::args().nth(1) {
        Some(p) => p,
        None => exit(2),
    };
    let data = fs::read(&path).unwrap_or_else(|_| exit(1));
    let n = data.len();
    let d = data.as_slice();

    let mut interner = Interner::new(17); // 131072 slots for ~40k vocab
    let mut pairs = PairTable::new(20); // 1M slots, grows as needed

    let mut total_words: u64 = 0;
    let mut total_pairs: u64 = 0;
    let mut prev: u32 = 0;
    let mut have_prev = false;

    let mut i = 0usize;
    while i < n {
        // Skip separators, watching for sentence ends.
        while i < n {
            let b = d[i];
            if is_letter(b) {
                break;
            }
            if b == b'.' || b == b'!' || b == b'?' {
                have_prev = false;
            }
            i += 1;
        }
        if i >= n {
            break;
        }
        // Scan one word, hashing lowercased bytes (FNV-1a).
        let start = i;
        let mut hash = FNV_OFFSET;
        while i < n {
            let c = d[i] | 0x20;
            if c.wrapping_sub(b'a') >= 26 {
                break;
            }
            hash = (hash ^ c as u64).wrapping_mul(FNV_PRIME);
            i += 1;
        }
        let id = interner.intern(&d[start..i], hash);
        total_words += 1;
        if have_prev {
            total_pairs += 1;
            pairs.inc(((prev as u64) << 32) | id as u64);
        }
        prev = id;
        have_prev = true;
    }

    let distinct = pairs.len;

    // Rank of each word id in ascending byte order, for tie-breaking
    // with plain integer compares.
    let vocab = interner.words.len();
    let mut order: Vec<u32> = (0..vocab as u32).collect();
    order.sort_unstable_by(|&a, &b| interner.word(a).cmp(interner.word(b)));
    let mut rank = vec![0u32; vocab];
    for (pos, &id) in order.iter().enumerate() {
        rank[id as usize] = pos as u32;
    }
    let lexkey = |key: u64| -> u64 {
        let id1 = (key >> 32) as u32;
        let id2 = key as u32;
        ((rank[id1 as usize] as u64) << 32) | rank[id2 as usize] as u64
    };

    // Collect (count, key).
    let mut entries: Vec<(u32, u64)> = Vec::with_capacity(distinct);
    for &e in pairs.entries.iter() {
        if e.key != EMPTY_KEY {
            entries.push((e.val, e.key));
        }
    }

    // Select top 20 without sorting everything.
    let mut top: Vec<(u32, u64, u64)> = Vec::with_capacity(20); // (count, lexkey, key)
    if distinct <= 20 {
        top.extend(entries.iter().map(|&(c, k)| (c, lexkey(k), k)));
    } else {
        let mut counts: Vec<u32> = entries.iter().map(|&e| e.0).collect();
        counts.select_nth_unstable_by(19, |a, b| b.cmp(a));
        let thr = counts[19];
        let mut equal: Vec<(u64, u64)> = Vec::new(); // (lexkey, key)
        for &(c, k) in &entries {
            if c > thr {
                top.push((c, lexkey(k), k));
            } else if c == thr {
                equal.push((lexkey(k), k));
            }
        }
        let need = 20 - top.len();
        if need > 0 {
            if equal.len() > need {
                equal.select_nth_unstable_by(need - 1, |a, b| a.0.cmp(&b.0));
                equal.truncate(need);
            }
            top.extend(equal.iter().map(|&(lx, k)| (thr, lx, k)));
        }
    }
    top.sort_unstable_by(|a, b| b.0.cmp(&a.0).then_with(|| a.1.cmp(&b.1)));

    let mut out = String::with_capacity(1024);
    let _ = writeln!(out, "words {}", total_words);
    let _ = writeln!(out, "pairs {}", total_pairs);
    let _ = writeln!(out, "distinct {}", distinct);
    for &(c, _, k) in &top {
        let w1 = interner.word((k >> 32) as u32);
        let w2 = interner.word(k as u32);
        // Words are pure ASCII lowercase.
        let s1 = unsafe { std::str::from_utf8_unchecked(w1) };
        let s2 = unsafe { std::str::from_utf8_unchecked(w2) };
        let _ = writeln!(out, "{} {} {}", c, s1, s2);
    }
    print!("{}", out);
}
