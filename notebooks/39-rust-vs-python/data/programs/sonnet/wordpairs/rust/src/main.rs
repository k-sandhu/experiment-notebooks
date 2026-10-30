use std::io::Write;

const EMPTY: u32 = u32::MAX;

struct Interner {
    slots: Vec<u32>,
    hashes: Vec<u32>,
    starts: Vec<u32>,
    lens: Vec<u32>,
    mask: usize,
}

impl Interner {
    fn new() -> Self {
        let cap = 1 << 17;
        Interner {
            slots: vec![EMPTY; cap],
            hashes: Vec::new(),
            starts: Vec::new(),
            lens: Vec::new(),
            mask: cap - 1,
        }
    }

    fn grow(&mut self) {
        let cap = (self.mask + 1) * 2;
        self.mask = cap - 1;
        self.slots = vec![EMPTY; cap];
        for (id, &h) in self.hashes.iter().enumerate() {
            let mut i = (h as usize) & self.mask;
            while self.slots[i] != EMPTY {
                i = (i + 1) & self.mask;
            }
            self.slots[i] = id as u32;
        }
    }

    #[inline]
    fn intern(&mut self, buf: &[u8], start: usize, end: usize, h: u32) -> u32 {
        let w = &buf[start..end];
        let mut i = (h as usize) & self.mask;
        loop {
            let s = self.slots[i];
            if s == EMPTY {
                break;
            }
            let su = s as usize;
            if self.hashes[su] == h && self.lens[su] as usize == w.len() {
                let st = self.starts[su] as usize;
                if &buf[st..st + w.len()] == w {
                    return s;
                }
            }
            i = (i + 1) & self.mask;
        }
        let id = self.hashes.len() as u32;
        self.slots[i] = id;
        self.hashes.push(h);
        self.starts.push(start as u32);
        self.lens.push(w.len() as u32);
        if self.hashes.len() * 2 > self.mask + 1 {
            self.grow();
        }
        id
    }
}

struct PairTable {
    slots: Vec<(u64, u32)>,
    mask: usize,
    len: usize,
}

#[inline]
fn mix(k: u64) -> usize {
    (k.wrapping_mul(0x9E37_79B9_7F4A_7C15) >> 32) as usize
}

impl PairTable {
    fn new() -> Self {
        let cap = 1 << 20;
        PairTable { slots: vec![(0, 0); cap], mask: cap - 1, len: 0 }
    }

    fn grow(&mut self) {
        let cap = (self.mask + 1) * 2;
        let old = std::mem::replace(&mut self.slots, vec![(0, 0); cap]);
        self.mask = cap - 1;
        for &(k, c) in old.iter() {
            if k != 0 {
                let mut i = mix(k) & self.mask;
                while self.slots[i].0 != 0 {
                    i = (i + 1) & self.mask;
                }
                self.slots[i] = (k, c);
            }
        }
    }

    #[inline]
    fn add(&mut self, k: u64) {
        let mut i = mix(k) & self.mask;
        loop {
            let s = &mut self.slots[i];
            if s.0 == k {
                s.1 += 1;
                return;
            }
            if s.0 == 0 {
                *s = (k, 1);
                self.len += 1;
                if self.len * 2 > self.mask + 1 {
                    self.grow();
                }
                return;
            }
            i = (i + 1) & self.mask;
        }
    }
}

#[inline(always)]
fn prefetch(slots: &[(u64, u32)], i: usize) {
    #[cfg(target_arch = "x86_64")]
    unsafe {
        use std::arch::x86_64::{_MM_HINT_T0, _mm_prefetch};
        _mm_prefetch::<_MM_HINT_T0>(slots.as_ptr().add(i) as *const i8);
    }
}

fn main() {
    let path = std::env::args().nth(1).expect("usage: solution INPUT");
    let mut buf = std::fs::read(&path).expect("read input");

    // class table: 0 = separator, 1 = sentence end, 2 = letter
    let mut class = [0u8; 256];
    for c in b'a'..=b'z' {
        class[c as usize] = 2;
        class[(c - 32) as usize] = 2;
    }
    for &c in b".!?" {
        class[c as usize] = 1;
    }
    buf.make_ascii_lowercase();

    let mut interner = Interner::new();
    let mut pairs = PairTable::new();
    let mut ids: Vec<u32> = Vec::with_capacity(buf.len() / 4 + 16);
    let mut words: u64 = 0;
    let mut total_pairs: u64 = 0;

    let n = buf.len();
    let mut i = 0;
    while i < n {
        let c = class[buf[i] as usize];
        if c == 2 {
            let start = i;
            let mut h: u32 = 0x811C_9DC5;
            while i < n && class[buf[i] as usize] == 2 {
                h = (h ^ buf[i] as u32).wrapping_mul(0x0100_0193);
                i += 1;
            }
            h ^= h >> 15;
            let id = interner.intern(&buf, start, i, h);
            words += 1;
            ids.push(id);
        } else {
            if c == 1 {
                ids.push(EMPTY);
            }
            i += 1;
        }
    }

    // Count pairs in a second pass so the table slot can be prefetched ahead of use.
    const AHEAD: usize = 12;
    let m = ids.len();
    let mut prev: u32 = EMPTY;
    for j in 0..m {
        if j + AHEAD + 1 < m {
            let a = ids[j + AHEAD];
            let b = ids[j + AHEAD + 1];
            if a != EMPTY && b != EMPTY {
                let k = ((a as u64 + 1) << 32) | (b as u64 + 1);
                prefetch(&pairs.slots, mix(k) & pairs.mask);
            }
        }
        let id = ids[j];
        if id != EMPTY && prev != EMPTY {
            total_pairs += 1;
            pairs.add(((prev as u64 + 1) << 32) | (id as u64 + 1));
        }
        prev = id;
    }

    let distinct = pairs.len as u64;
    let word = |id: u64| -> &[u8] {
        let id = (id - 1) as usize;
        let s = interner.starts[id] as usize;
        &buf[s..s + interner.lens[id] as usize]
    };

    let mut entries: Vec<(u32, u64)> = Vec::with_capacity(pairs.len);
    for &(k, c) in pairs.slots.iter() {
        if k != 0 {
            entries.push((c, k));
        }
    }
    let cmp = |a: &(u32, u64), b: &(u32, u64)| {
        b.0.cmp(&a.0)
            .then_with(|| word(a.1 >> 32).cmp(word(b.1 >> 32)))
            .then_with(|| word(a.1 & 0xFFFF_FFFF).cmp(word(b.1 & 0xFFFF_FFFF)))
    };
    let top = 20.min(entries.len());
    if top > 0 && entries.len() > top {
        // cheap pre-filter on count alone, then exact ordering of the candidates
        entries.select_nth_unstable_by_key(top - 1, |e| std::cmp::Reverse(e.0));
        let thr = entries[top - 1].0;
        entries.retain(|e| e.0 >= thr);
    }
    entries.sort_by(cmp);
    entries.truncate(top);

    let mut out = Vec::new();
    writeln!(out, "words {}\npairs {}\ndistinct {}", words, total_pairs, distinct).unwrap();
    for e in &entries {
        write!(out, "{} ", e.0).unwrap();
        out.extend_from_slice(word(e.1 >> 32));
        out.push(b' ');
        out.extend_from_slice(word(e.1 & 0xFFFF_FFFF));
        out.push(b'\n');
    }
    std::io::stdout().write_all(&out).unwrap();
}
