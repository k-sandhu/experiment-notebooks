use std::fmt::Write as _;
use std::io::Write as _;

const EMPTY: u32 = u32::MAX;

struct Interner {
    table: Vec<u32>, // id + 1, 0 means empty
    mask: usize,
    hashes: Vec<u64>,
    starts: Vec<u32>,
    lens: Vec<u32>,
    arena: Vec<u8>,
}

impl Interner {
    fn new() -> Self {
        let cap = 1usize << 14;
        Interner {
            table: vec![0u32; cap],
            mask: cap - 1,
            hashes: Vec::with_capacity(65536),
            starts: Vec::with_capacity(65536),
            lens: Vec::with_capacity(65536),
            arena: Vec::with_capacity(1 << 20),
        }
    }

    #[inline]
    fn hash(bytes: &[u8]) -> u64 {
        let mut h: u64 = 0xcbf2_9ce4_8422_2325;
        for &b in bytes {
            h ^= (b | 0x20) as u64;
            h = h.wrapping_mul(0x1000_0000_01b3);
        }
        h
    }

    #[inline]
    fn intern(&mut self, bytes: &[u8]) -> u32 {
        let h = Self::hash(bytes);
        let len = bytes.len();
        let mut idx = (h as usize) & self.mask;
        loop {
            let e = self.table[idx];
            if e == 0 {
                break;
            }
            let id = (e - 1) as usize;
            if self.hashes[id] == h {
                let l = self.lens[id] as usize;
                if l == len {
                    let s = self.starts[id] as usize;
                    let stored = &self.arena[s..s + l];
                    if stored.iter().zip(bytes).all(|(x, y)| *x == (*y | 0x20)) {
                        return id as u32;
                    }
                }
            }
            idx = (idx + 1) & self.mask;
        }

        let id = self.hashes.len() as u32;
        self.starts.push(self.arena.len() as u32);
        self.lens.push(len as u32);
        self.arena.extend(bytes.iter().map(|&b| b | 0x20));
        self.hashes.push(h);
        self.table[idx] = id + 1;

        if self.hashes.len() * 3 > self.table.len() * 2 {
            self.grow();
        }
        id
    }

    fn grow(&mut self) {
        let newcap = self.table.len() * 2;
        let mut t = vec![0u32; newcap];
        let mask = newcap - 1;
        for id in 0..self.hashes.len() {
            let mut idx = (self.hashes[id] as usize) & mask;
            while t[idx] != 0 {
                idx = (idx + 1) & mask;
            }
            t[idx] = id as u32 + 1;
        }
        self.table = t;
        self.mask = mask;
    }

    #[inline]
    fn word(&self, id: u32) -> &[u8] {
        let s = self.starts[id as usize] as usize;
        let l = self.lens[id as usize] as usize;
        &self.arena[s..s + l]
    }
}

#[derive(Clone, Copy)]
struct Rec {
    c: u32,
    a: u32,
    b: u32,
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let data = std::fs::read(&args[1]).unwrap();
    let n = data.len();

    let mut intern = Interner::new();
    let mut pairs: Vec<u64> = Vec::with_capacity(n / 6 + 16);
    let mut prev: u32 = EMPTY;
    let mut words: u64 = 0;

    let mut i = 0usize;
    while i < n {
        let c = data[i];
        if c == b'.' || c == b'!' || c == b'?' {
            prev = EMPTY;
            i += 1;
        } else if c.is_ascii_alphabetic() {
            let s = i;
            i += 1;
            while i < n && data[i].is_ascii_alphabetic() {
                i += 1;
            }
            let id = intern.intern(&data[s..i]);
            words += 1;
            if prev != EMPTY {
                pairs.push(((prev as u64) << 32) | id as u64);
            }
            prev = id;
        } else {
            i += 1;
        }
    }
    drop(data);

    pairs.sort_unstable();

    let v = intern.hashes.len();
    let mut rank = vec![0u32; v];
    {
        let mut order: Vec<u32> = (0..v as u32).collect();
        order.sort_unstable_by(|&a, &b| intern.word(a).cmp(intern.word(b)));
        for (r, &id) in order.iter().enumerate() {
            rank[id as usize] = r as u32;
        }
    }

    let better = |x: &Rec, y: &Rec| -> bool {
        if x.c != y.c {
            x.c > y.c
        } else {
            let xr = rank[x.a as usize];
            let yr = rank[y.a as usize];
            if xr != yr {
                xr < yr
            } else {
                rank[x.b as usize] < rank[y.b as usize]
            }
        }
    };

    let plen = pairs.len();
    let mut distinct: u64 = 0;
    let mut best: Vec<Rec> = Vec::with_capacity(20);

    let mut idx = 0usize;
    while idx < plen {
        let key = pairs[idx];
        let mut j = idx + 1;
        while j < plen && pairs[j] == key {
            j += 1;
        }
        let rec = Rec {
            c: (j - idx) as u32,
            a: (key >> 32) as u32,
            b: (key & 0xffff_ffff) as u32,
        };
        distinct += 1;

        if best.len() < 20 {
            let pos = best
                .iter()
                .position(|x| better(&rec, x))
                .unwrap_or(best.len());
            best.insert(pos, rec);
        } else if better(&rec, &best[19]) {
            let pos = best[..19]
                .iter()
                .position(|x| better(&rec, x))
                .unwrap_or(19);
            best.insert(pos, rec);
            best.pop();
        }
        idx = j;
    }

    let mut out = String::with_capacity(2048);
    write!(
        &mut out,
        "words {}\npairs {}\ndistinct {}\n",
        words, plen, distinct
    )
    .unwrap();
    for r in &best {
        let a = std::str::from_utf8(intern.word(r.a)).unwrap();
        let b = std::str::from_utf8(intern.word(r.b)).unwrap();
        writeln!(&mut out, "{} {} {}", r.c, a, b).unwrap();
    }

    let stdout = std::io::stdout();
    let mut lock = stdout.lock();
    lock.write_all(out.as_bytes()).unwrap();
}
