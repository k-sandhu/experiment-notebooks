use std::env;
use std::fs;
use std::io::{self, BufWriter, Write};
use std::process::ExitCode;

// ---------- word interning table ----------
#[derive(Clone, Copy)]
struct WEntry {
    hash: u64,
    id: u32, // u32::MAX = empty
}

struct WordTable {
    entries: Vec<WEntry>,
    mask: usize,
    len: usize,
}

impl WordTable {
    fn new(cap: usize) -> Self {
        Self {
            entries: vec![WEntry { hash: 0, id: u32::MAX }; cap],
            mask: cap - 1,
            len: 0,
        }
    }
    fn grow(&mut self) {
        let ncap = self.entries.len() * 2;
        let mut ne = vec![WEntry { hash: 0, id: u32::MAX }; ncap];
        let nmask = ncap - 1;
        for e in self.entries.iter() {
            if e.id != u32::MAX {
                let mut i = (e.hash as usize) & nmask;
                while ne[i].id != u32::MAX {
                    i = (i + 1) & nmask;
                }
                ne[i] = *e;
            }
        }
        self.entries = ne;
        self.mask = nmask;
    }
    #[inline]
    fn get_or_insert(
        &mut self,
        hash: u64,
        word: &[u8], // original case slice from input
        arena: &mut Vec<u8>,
        words: &mut Vec<(u32, u32)>, // (offset, len) per id
    ) -> u32 {
        if (self.len + 1) * 10 > self.entries.len() * 7 {
            self.grow();
        }
        let wlen = word.len();
        let mut i = (hash as usize) & self.mask;
        loop {
            let e = self.entries[i];
            if e.id == u32::MAX {
                let id = words.len() as u32;
                let off = arena.len() as u32;
                arena.reserve(wlen);
                for &b in word {
                    arena.push(b | 0x20);
                }
                words.push((off, wlen as u32));
                self.entries[i] = WEntry { hash, id };
                self.len += 1;
                return id;
            }
            if e.hash == hash {
                let (off, ln) = words[e.id as usize];
                if ln as usize == wlen {
                    let stored = &arena[off as usize..off as usize + wlen];
                    let mut same = true;
                    for k in 0..wlen {
                        if stored[k] != (word[k] | 0x20) {
                            same = false;
                            break;
                        }
                    }
                    if same {
                        return e.id;
                    }
                }
            }
            i = (i + 1) & self.mask;
        }
    }
}

// ---------- pair counting table ----------
#[derive(Clone, Copy)]
struct PEntry {
    key: u64, // u64::MAX = empty
    cnt: u32,
}

struct PairTable {
    entries: Vec<PEntry>,
    mask: usize,
    len: usize,
}

#[inline(always)]
fn mix64(mut x: u64) -> u64 {
    x ^= x >> 33;
    x = x.wrapping_mul(0xff51_afd7_ed55_8ccd);
    x ^= x >> 33;
    x = x.wrapping_mul(0xc4ce_b9fe_1a85_ec53);
    x ^= x >> 33;
    x
}

impl PairTable {
    fn new(cap: usize) -> Self {
        Self {
            entries: vec![PEntry { key: u64::MAX, cnt: 0 }; cap],
            mask: cap - 1,
            len: 0,
        }
    }
    fn grow(&mut self) {
        let ncap = self.entries.len() * 2;
        let mut ne = vec![PEntry { key: u64::MAX, cnt: 0 }; ncap];
        let nmask = ncap - 1;
        for e in self.entries.iter() {
            if e.key != u64::MAX {
                let mut i = (mix64(e.key) as usize) & nmask;
                while ne[i].key != u64::MAX {
                    i = (i + 1) & nmask;
                }
                ne[i] = *e;
            }
        }
        self.entries = ne;
        self.mask = nmask;
    }
    #[inline]
    fn increment(&mut self, key: u64) {
        if (self.len + 1) * 10 > self.entries.len() * 7 {
            self.grow();
        }
        let mut i = (mix64(key) as usize) & self.mask;
        loop {
            if self.entries[i].key == u64::MAX {
                self.entries[i] = PEntry { key, cnt: 1 };
                self.len += 1;
                return;
            }
            if self.entries[i].key == key {
                self.entries[i].cnt += 1;
                return;
            }
            i = (i + 1) & self.mask;
        }
    }
}

fn main() -> ExitCode {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        return ExitCode::from(2);
    }
    let data = match fs::read(&args[1]) {
        Ok(d) => d,
        Err(_) => return ExitCode::from(1),
    };
    let n = data.len();
    let ptr = data.as_ptr();

    let mut wt = WordTable::new(1 << 16);
    let mut pt = PairTable::new(1 << 16);
    let mut arena: Vec<u8> = Vec::with_capacity(1 << 16);
    let mut words: Vec<(u32, u32)> = Vec::with_capacity(1 << 15);

    let mut total_words: u64 = 0;
    let mut total_pairs: u64 = 0;
    let mut prev: u32 = 0;
    let mut has_prev = false;

    let mut i: usize = 0;
    while i < n {
        // SAFETY: i < n
        let b = unsafe { *ptr.add(i) };
        if b.is_ascii_alphabetic() {
            let start = i;
            // FNV-1a over lowercased bytes
            let mut hash: u64 = 0xcbf2_9ce4_8422_2325;
            while i < n {
                let c = unsafe { *ptr.add(i) };
                if !c.is_ascii_alphabetic() {
                    break;
                }
                hash ^= (c | 0x20) as u64;
                hash = hash.wrapping_mul(0x0100_0000_01b3);
                i += 1;
            }
            // final mix for table index distribution
            let hash = mix64(hash ^ (i - start) as u64);
            let word = &data[start..i];
            let id = wt.get_or_insert(hash, word, &mut arena, &mut words);
            total_words += 1;
            if has_prev {
                pt.increment(((prev as u64) << 32) | id as u64);
                total_pairs += 1;
            }
            prev = id;
            has_prev = true;
        } else if b == b'.' || b == b'!' || b == b'?' {
            has_prev = false;
            i += 1;
        } else {
            i += 1;
        }
    }

    let distinct = pt.len as u64;

    fn word_bytes<'a>(id: u32, words: &[(u32, u32)], arena: &'a [u8]) -> &'a [u8] {
        let (off, ln) = words[id as usize];
        &arena[off as usize..off as usize + ln as usize]
    }

    // Lexicographic rank of each word id (vocab is small compared to pairs).
    let vocab = words.len();
    let mut rank = vec![0u32; vocab];
    {
        let mut order: Vec<u32> = (0..vocab as u32).collect();
        order.sort_unstable_by(|&a, &b| {
            word_bytes(a, &words, &arena).cmp(word_bytes(b, &words, &arena))
        });
        for (r, id) in order.into_iter().enumerate() {
            rank[id as usize] = r as u32;
        }
    }

    // Select top 20 without sorting all pairs.
    // Entries are (cnt, rank_first, rank_second, first, second).
    let mut top: Vec<(u32, u32, u32, u32, u32)> = Vec::with_capacity(20);
    if distinct <= 20 {
        for e in pt.entries.iter() {
            if e.key != u64::MAX {
                let f = (e.key >> 32) as u32;
                let s = e.key as u32;
                top.push((e.cnt, rank[f as usize], rank[s as usize], f, s));
            }
        }
    } else {
        // Threshold = 20th largest count.
        let mut counts: Vec<u32> = Vec::with_capacity(pt.len);
        for e in pt.entries.iter() {
            if e.key != u64::MAX {
                counts.push(e.cnt);
            }
        }
        let (_, &mut thr, _) =
            counts.select_nth_unstable_by(19, |a, b| b.cmp(a));
        drop(counts);
        let mut ties: Vec<(u64, u32, u32)> = Vec::new(); // (lex_key, first, second)
        for e in pt.entries.iter() {
            if e.key != u64::MAX {
                let f = (e.key >> 32) as u32;
                let s = e.key as u32;
                if e.cnt > thr {
                    top.push((e.cnt, rank[f as usize], rank[s as usize], f, s));
                } else if e.cnt == thr {
                    let lex = ((rank[f as usize] as u64) << 32) | rank[s as usize] as u64;
                    ties.push((lex, f, s));
                }
            }
        }
        let need = 20usize.saturating_sub(top.len());
        if ties.len() > need && need > 0 {
            ties.select_nth_unstable_by(need - 1, |a, b| a.0.cmp(&b.0));
            ties.truncate(need);
        } else if need == 0 {
            ties.clear();
        }
        for (_, f, s) in ties {
            top.push((thr, rank[f as usize], rank[s as usize], f, s));
        }
    }
    drop(pt);
    top.sort_unstable_by(|a, b| {
        b.0.cmp(&a.0).then_with(|| a.1.cmp(&b.1)).then_with(|| a.2.cmp(&b.2))
    });
    let pairs = top;

    let stdout = io::stdout();
    let mut out = BufWriter::with_capacity(1 << 16, stdout.lock());
    let _ = writeln!(out, "words {}", total_words);
    let _ = writeln!(out, "pairs {}", total_pairs);
    let _ = writeln!(out, "distinct {}", distinct);
    for (cnt, _, _, f, s) in pairs.iter().take(20) {
        let _ = write!(out, "{} ", cnt);
        let _ = out.write_all(word_bytes(*f, &words, &arena));
        let _ = out.write_all(b" ");
        let _ = out.write_all(word_bytes(*s, &words, &arena));
        let _ = out.write_all(b"\n");
    }
    let _ = out.flush();
    ExitCode::SUCCESS
}
