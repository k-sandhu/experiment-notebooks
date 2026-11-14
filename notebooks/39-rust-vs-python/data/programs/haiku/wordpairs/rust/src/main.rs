use std::collections::HashMap;
use std::fs::File;
use std::hash::{BuildHasherDefault, Hasher};
use std::io::{self, BufWriter, Read, Write};

const NO_WORD: u32 = u32::MAX;
const TOP: usize = 20;
const DIGIT_BITS: u32 = 11;

/// Cheap multiplicative hasher for word keys. The keys are short letter strings,
/// so SipHash would only add cost.
#[derive(Default)]
struct WordHasher(u64);

impl Hasher for WordHasher {
    #[inline]
    fn finish(&self) -> u64 {
        self.0
    }

    #[inline]
    fn write(&mut self, bytes: &[u8]) {
        let mut chunks = bytes.chunks_exact(8);
        for c in &mut chunks {
            self.write_u64(u64::from_le_bytes(c.try_into().unwrap()));
        }
        let mut tail = [0u8; 8];
        let rest = chunks.remainder();
        tail[..rest.len()].copy_from_slice(rest);
        self.write_u64(u64::from_le_bytes(tail));
    }

    #[inline]
    fn write_u64(&mut self, x: u64) {
        let h = (self.0 ^ x).wrapping_mul(0x9E37_79B9_7F4A_7C15);
        self.0 = h ^ (h >> 29);
    }
}

type FastMap<K, V> = HashMap<K, V, BuildHasherDefault<WordHasher>>;

/// Streaming scanner. It keeps only the previous word id and the current word,
/// so the input never has to be held in memory.
struct Scanner {
    /// Words of up to 8 letters, packed into one u64 (letters are never zero).
    short_ids: FastMap<u64, u32>,
    /// Longer words, keyed by their lower-case bytes.
    long_ids: FastMap<Box<[u8]>, u32>,
    /// Lower-case text of each word id.
    words: Vec<Box<[u8]>>,
    /// One entry per pair: (first id << 32) | second id.
    pairs: Vec<u64>,
    word_total: u64,
    /// Id of the previous word in the current sentence, or NO_WORD.
    prev: u32,
    /// The current word: packed first 8 letters, and all letters in `buf`.
    packed: u64,
    len: usize,
    buf: Vec<u8>,
}

impl Scanner {
    fn new() -> Self {
        Scanner {
            short_ids: FastMap::default(),
            long_ids: FastMap::default(),
            words: Vec::new(),
            pairs: Vec::new(),
            word_total: 0,
            prev: NO_WORD,
            packed: 0,
            len: 0,
            buf: Vec::new(),
        }
    }

    fn feed(&mut self, chunk: &[u8]) {
        for &b in chunk {
            if b.is_ascii_alphabetic() {
                self.letter(b);
            } else {
                if self.len > 0 {
                    self.end_word();
                }
                if matches!(b, b'.' | b'!' | b'?') {
                    self.prev = NO_WORD;
                }
            }
        }
    }

    #[inline]
    fn letter(&mut self, b: u8) {
        let c = b | 0x20;
        if self.len < 8 {
            self.packed |= (c as u64) << (8 * self.len);
        }
        self.buf.push(c);
        self.len += 1;
    }

    fn end_word(&mut self) {
        let id = self.intern();
        self.word_total += 1;
        if self.prev != NO_WORD {
            self.pairs.push(((self.prev as u64) << 32) | id as u64);
        }
        self.prev = id;
        self.packed = 0;
        self.len = 0;
        self.buf.clear();
    }

    #[inline]
    fn intern(&mut self) -> u32 {
        if self.len <= 8 {
            if let Some(&id) = self.short_ids.get(&self.packed) {
                return id;
            }
            let id = self.new_word();
            self.short_ids.insert(self.packed, id);
            id
        } else {
            if let Some(&id) = self.long_ids.get(self.buf.as_slice()) {
                return id;
            }
            let id = self.new_word();
            self.long_ids.insert(self.buf.as_slice().into(), id);
            id
        }
    }

    #[cold]
    fn new_word(&mut self) -> u32 {
        self.words.push(self.buf.as_slice().into());
        (self.words.len() - 1) as u32
    }
}

/// LSD radix sort on the low `bits` bits of each key.
fn radix_sort(mut a: Vec<u64>, bits: u32) -> Vec<u64> {
    const BUCKETS: usize = 1 << DIGIT_BITS;
    let mut b = vec![0u64; a.len()];
    let mut shift: u32 = 0;
    while shift < bits {
        let mut next = [0usize; BUCKETS];
        for &k in &a {
            next[((k >> shift) as usize) & (BUCKETS - 1)] += 1;
        }
        let mut sum = 0;
        for slot in next.iter_mut() {
            let c = *slot;
            *slot = sum;
            sum += c;
        }
        for &k in &a {
            let d = ((k >> shift) as usize) & (BUCKETS - 1);
            b[next[d]] = k;
            next[d] += 1;
        }
        std::mem::swap(&mut a, &mut b);
        shift += DIGIT_BITS;
    }
    a
}

fn main() -> io::Result<()> {
    let path = std::env::args_os()
        .nth(1)
        .ok_or_else(|| io::Error::other("usage: solution INPUT_PATH"))?;
    let mut file = File::open(path)?;

    let mut scan = Scanner::new();
    let mut chunk = vec![0u8; 1 << 20];
    loop {
        let n = file.read(&mut chunk)?;
        if n == 0 {
            break;
        }
        scan.feed(&chunk[..n]);
    }
    if scan.len > 0 {
        scan.end_word();
    }
    let Scanner {
        words,
        pairs: mut keys,
        word_total,
        ..
    } = scan;

    // Give each word its rank in byte order, so that a pair key built from
    // ranks sorts exactly as the output requires: first word, then second.
    let vocab = words.len();
    let rank_bits = (usize::BITS - vocab.saturating_sub(1).leading_zeros()).max(1);
    let mut lex: Vec<u32> = (0..vocab as u32).collect();
    lex.sort_unstable_by(|&a, &b| words[a as usize].cmp(&words[b as usize]));
    let mut rank = vec![0u64; vocab];
    for (r, &id) in lex.iter().enumerate() {
        rank[id as usize] = r as u64;
    }
    for k in keys.iter_mut() {
        let a = rank[(*k >> 32) as usize];
        let b = rank[(*k & 0xFFFF_FFFF) as usize];
        *k = (a << rank_bits) | b;
    }
    let keys = radix_sort(keys, 2 * rank_bits);

    // Runs of equal keys are the distinct pairs. Keys are visited in ascending
    // order, so a later run never beats an earlier one with the same count.
    let mut top: Vec<(u64, u64)> = Vec::with_capacity(TOP + 1);
    let mut distinct = 0u64;
    for run in keys.chunk_by(|a, b| a == b) {
        distinct += 1;
        let count = run.len() as u64;
        if top.len() == TOP && count <= top[TOP - 1].0 {
            continue;
        }
        let pos = top.partition_point(|&(c, _)| c >= count);
        top.insert(pos, (count, run[0]));
        top.truncate(TOP);
    }

    let stdout = io::stdout();
    let mut out = BufWriter::new(stdout.lock());
    writeln!(out, "words {word_total}")?;
    writeln!(out, "pairs {}", keys.len())?;
    writeln!(out, "distinct {distinct}")?;
    let mask = (1u64 << rank_bits) - 1;
    for &(count, key) in &top {
        let first = &words[lex[(key >> rank_bits) as usize] as usize];
        let second = &words[lex[(key & mask) as usize] as usize];
        write!(out, "{count} ")?;
        out.write_all(first)?;
        out.write_all(b" ")?;
        out.write_all(second)?;
        out.write_all(b"\n")?;
    }
    out.flush()
}
