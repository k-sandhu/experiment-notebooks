use std::collections::HashMap;
use std::io::{Read, Write};

const BREAK: u32 = u32::MAX;
const PAD: usize = 80;

#[inline(always)]
fn is_letter(c: u8) -> bool {
    (c | 0x20).wrapping_sub(b'a') < 26
}

/// Open-addressing table for words of at most 16 bytes, keyed by the
/// lower-cased bytes packed into a u128 (zero means empty slot).
struct ShortTable {
    keys: Vec<u128>,
    vals: Vec<u32>,
    shift: u32,
    len: usize,
}

impl ShortTable {
    fn new(bits: u32) -> Self {
        let cap = 1usize << bits;
        ShortTable { keys: vec![0; cap], vals: vec![0; cap], shift: 64 - bits, len: 0 }
    }

    #[inline(always)]
    fn hash(&self, k: u128) -> usize {
        let x = (k as u64) ^ ((k >> 64) as u64).wrapping_mul(0x9E37_79B9_7F4A_7C15);
        (x.wrapping_mul(0xD6E8_FEB8_6659_FD93) >> self.shift) as usize
    }

    fn grow(&mut self) {
        let bits = 64 - self.shift + 1;
        let mut t = ShortTable::new(bits);
        let mask = t.keys.len() - 1;
        for (&k, &v) in self.keys.iter().zip(&self.vals) {
            if k != 0 {
                let mut h = t.hash(k);
                while t.keys[h] != 0 {
                    h = (h + 1) & mask;
                }
                t.keys[h] = k;
                t.vals[h] = v;
            }
        }
        t.len = self.len;
        *self = t;
    }
}

struct Vocab {
    short: ShortTable,
    long: HashMap<Vec<u8>, u32>,
    /// Lower-cased bytes of every word, indexed by id.
    arena: Vec<u8>,
    spans: Vec<(u32, u32)>,
}

impl Vocab {
    fn add_word(&mut self, w: &[u8]) -> u32 {
        let id = self.spans.len() as u32;
        let start = self.arena.len();
        self.arena.extend(w.iter().map(|c| c | 0x20));
        self.spans.push((start as u32, w.len() as u32));
        id
    }

    /// Interns the word starting at `s` and returns its id.
    #[inline(always)]
    fn intern(&mut self, data: &[u8], s: usize) -> u32 {
        // SAFETY: data has PAD zero bytes after the text, so 16 bytes from s are readable.
        let raw = u128::from_le(unsafe { std::ptr::read_unaligned(data.as_ptr().add(s) as *const u128) });
        let low = raw | 0x2020_2020_2020_2020_2020_2020_2020_2020;
        // Per-byte high bit set where the byte is a letter (all bytes are < 0x80).
        const H: u128 = 0x8080_8080_8080_8080_8080_8080_8080_8080;
        const B: u128 = 0x0101_0101_0101_0101_0101_0101_0101_0101;
        let letter = low.wrapping_add(B * (0x80 - 0x61)) & !low.wrapping_add(B * (0x80 - 0x7b)) & H;
        let non = !letter & H;
        if non != 0 {
            let len = (non.trailing_zeros() / 8) as usize;
            let k = low & ((1u128 << (8 * len)) - 1);
            let t = &mut self.short;
            let m = t.keys.len() - 1;
            let mut h = t.hash(k);
            loop {
                let kk = t.keys[h];
                if kk == k {
                    return t.vals[h];
                }
                if kk == 0 {
                    break;
                }
                h = (h + 1) & m;
            }
            let id = self.add_word(&data[s..s + len]);
            let t = &mut self.short;
            t.keys[h] = k;
            t.vals[h] = id;
            t.len += 1;
            if t.len * 2 > t.keys.len() {
                t.grow();
            }
            id
        } else {
            let mut e = s + 16;
            while is_letter(data[e]) {
                e += 1;
            }
            let lw: Vec<u8> = data[s..e].iter().map(|c| c | 0x20).collect();
            if let Some(&id) = self.long.get(&lw) {
                return id;
            }
            let id = self.add_word(&data[s..e]);
            self.long.insert(lw, id);
            id
        }
    }

    fn word(&self, id: u32) -> &[u8] {
        let (s, l) = self.spans[id as usize];
        &self.arena[s as usize..(s + l) as usize]
    }
}

/// Bit masks of the letters and of the sentence ends in a 64-byte block.
#[inline(always)]
fn block_masks(b: &[u8]) -> (u64, u64) {
    use std::arch::x86_64::*;
    assert!(b.len() >= 64);
    let mut letters = 0u64;
    let mut terms = 0u64;
    // SAFETY: SSE2 is part of the x86_64 baseline and the loads stay inside `b`.
    unsafe {
        let case = _mm_set1_epi8(0x20);
        let bias = _mm_set1_epi8((0x80u8 - b'a') as i8);
        let limit = _mm_set1_epi8((0x80u8 + 26) as i8);
        let dot = _mm_set1_epi8(b'.' as i8);
        let bang = _mm_set1_epi8(b'!' as i8);
        let ques = _mm_set1_epi8(b'?' as i8);
        for q in 0..4 {
            let v = _mm_loadu_si128(b.as_ptr().add(16 * q) as *const __m128i);
            let x = _mm_add_epi8(_mm_or_si128(v, case), bias);
            let l = _mm_cmplt_epi8(x, limit);
            let t = _mm_or_si128(
                _mm_or_si128(_mm_cmpeq_epi8(v, dot), _mm_cmpeq_epi8(v, bang)),
                _mm_cmpeq_epi8(v, ques),
            );
            letters |= (_mm_movemask_epi8(l) as u32 as u64) << (16 * q);
            terms |= (_mm_movemask_epi8(t) as u32 as u64) << (16 * q);
        }
    }
    (letters, terms)
}

/// Builds the key of every pair of adjacent words not split by a BREAK.
/// `rank` has one extra slot at the end that BREAK tokens are clamped to.
fn pair_keys<T: Copy>(tokens: &[u32], rank: &[u32], pairs: usize, key: impl Fn(u32, u32) -> T) -> Vec<T> {
    let vb = (rank.len() - 1) as u32;
    let mut keys: Vec<T> = Vec::with_capacity(pairs + 1);
    let kp = keys.as_mut_ptr();
    let mut nk = 0usize;
    for w in tokens.windows(2) {
        let ok = w[0] != BREAK && w[1] != BREAK;
        let k = key(rank[w[0].min(vb) as usize], rank[w[1].min(vb) as usize]);
        // Written unconditionally, kept only when valid: at most `pairs` valid
        // keys plus one scratch slot.
        unsafe { kp.add(nk).write(k) };
        nk += ok as usize;
    }
    assert!(nk <= pairs);
    unsafe { keys.set_len(nk) };
    keys
}

/// LSD radix sort on the low `bits` bits of each key.
fn radix_sort<T: Copy + Default + Into<u64>>(v: &mut Vec<T>, bits: u32) {
    const D: u32 = 11;
    let n = v.len();
    let mut buf: Vec<T> = vec![T::default(); n];
    let passes = bits.div_ceil(D).max(1);
    let mut shift = 0;
    for _ in 0..passes {
        let mut cnt = vec![0usize; 1 << D];
        for &x in v.iter() {
            cnt[((x.into() >> shift) as usize) & ((1 << D) - 1)] += 1;
        }
        let mut sum = 0;
        for c in cnt.iter_mut() {
            let t = *c;
            *c = sum;
            sum += t;
        }
        for &x in v.iter() {
            let d = ((x.into() >> shift) as usize) & ((1 << D) - 1);
            // SAFETY: cnt[d] < n by construction of the prefix sums.
            unsafe { *buf.get_unchecked_mut(cnt[d]) = x };
            cnt[d] += 1;
        }
        std::mem::swap(v, &mut buf);
        shift += D;
    }
}

/// Returns (distinct, top) where top holds up to 20 (count, key) sorted by
/// count descending, key ascending. `v` must be sorted.
fn top_runs<T: Copy + PartialEq + Into<u64>>(v: &[T]) -> (u64, Vec<(u64, u64)>) {
    let mut top: Vec<(u64, u64)> = Vec::with_capacity(21);
    let mut distinct = 0u64;
    let mut i = 0;
    let n = v.len();
    while i < n {
        let k = v[i];
        let mut j = i + 1;
        while j < n && v[j] == k {
            j += 1;
        }
        distinct += 1;
        let c = (j - i) as u64;
        // Keys arrive in ascending order, so a tie never displaces an earlier entry.
        if top.len() < 20 || c > top[top.len() - 1].0 {
            let pos = top.iter().position(|&(tc, _)| tc < c).unwrap_or(top.len());
            top.insert(pos, (c, k.into()));
            top.truncate(20);
        }
        i = j;
    }
    (distinct, top)
}

fn main() {
    let path = std::env::args().nth(1).expect("usage: solution INPUT");
    let mut file = std::fs::File::open(path).expect("cannot open input");
    let size = file.metadata().map(|m| m.len() as usize).unwrap_or(0);
    let mut data: Vec<u8> = Vec::with_capacity(size.next_multiple_of(64) + PAD);
    file.read_to_end(&mut data).expect("cannot read input");
    let n = data.len();
    // Zero padding: whole 64-byte blocks plus room for 16-byte word loads.
    data.resize(n.next_multiple_of(64) + PAD, 0);

    let mut vocab = Vocab {
        short: ShortTable::new(16),
        long: HashMap::new(),
        arena: Vec::new(),
        spans: Vec::new(),
    };
    // Each word adds at most two tokens (a sentence break and itself), and a
    // word takes at least two bytes including its separator.
    let mut tokens: Vec<u32> = Vec::with_capacity(n + 2);
    let tp = tokens.as_mut_ptr();
    let mut nt = 0usize;
    let mut words = 0u64;
    let mut pairs = 0u64;

    let mut have_word = false;
    let mut pending = false;
    let mut prev_letter = 0u64;
    let mut block = 0;
    while block < n {
        let (letters, terms) = block_masks(&data[block..block + 64]);
        let mut starts = letters & !((letters << 1) | prev_letter);
        prev_letter = letters >> 63;
        let mut terms = terms;
        while starts != 0 {
            let j = starts.trailing_zeros();
            let below = (1u64 << j) - 1;
            pending |= terms & below != 0;
            terms &= !below;
            starts &= starts - 1;
            let id = vocab.intern(&data, block + j as usize);
            let brk = pending & have_word;
            pairs += (have_word & !pending) as u64;
            // SAFETY: nt + 2 <= capacity, see above.
            unsafe {
                *tp.add(nt) = BREAK;
                nt += brk as usize;
                *tp.add(nt) = id;
            }
            nt += 1;
            pending = false;
            have_word = true;
            words += 1;
        }
        pending |= terms != 0;
        block += 64;
    }

    unsafe { tokens.set_len(nt) };
    // Rank words lexicographically so pair keys sort in output tie-break order.
    let v = vocab.spans.len();
    let mut order: Vec<u32> = (0..v as u32).collect();
    order.sort_unstable_by(|&a, &b| vocab.word(a).cmp(vocab.word(b)));
    // One extra slot so that BREAK tokens (clamped to v) index safely.
    let mut rank = vec![0u32; v + 1];
    for (r, &id) in order.iter().enumerate() {
        rank[id as usize] = r as u32;
    }
    let bits = (usize::BITS - v.max(1).leading_zeros()).max(1);

    let (distinct, top) = if 2 * bits <= 32 {
        let mut keys = pair_keys(&tokens, &rank, pairs as usize, |a, b| (a << bits) | b);
        drop(tokens);
        radix_sort(&mut keys, 2 * bits);
        top_runs(&keys)
    } else {
        let mut keys = pair_keys(&tokens, &rank, pairs as usize, |a, b| ((a as u64) << bits) | b as u64);
        drop(tokens);
        radix_sort(&mut keys, 2 * bits);
        top_runs(&keys)
    };

    let mut out = Vec::with_capacity(2048);
    writeln!(out, "words {}", words).unwrap();
    writeln!(out, "pairs {}", pairs).unwrap();
    writeln!(out, "distinct {}", distinct).unwrap();
    let low = (1u64 << bits) - 1;
    for (c, k) in top {
        let a = order[(k >> bits) as usize];
        let b = order[(k & low) as usize];
        write!(out, "{} ", c).unwrap();
        out.extend_from_slice(vocab.word(a));
        out.push(b' ');
        out.extend_from_slice(vocab.word(b));
        out.push(b'\n');
    }
    std::io::stdout().write_all(&out).unwrap();
}
