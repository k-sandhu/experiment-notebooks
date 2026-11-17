use std::cmp::Ordering;
use std::collections::HashMap;
use std::hash::{BuildHasherDefault, Hasher};
use std::io::{self, Write};

#[derive(Default)]
struct WordHasher(u64);

impl Hasher for WordHasher {
    #[inline]
    fn write(&mut self, bytes: &[u8]) {
        let mut h = self.0;
        for &byte in bytes {
            h = (h ^ byte as u64).wrapping_mul(0x100000001b3);
        }
        self.0 = h;
    }
    #[inline]
    fn finish(&self) -> u64 {
        self.0
    }
}

// Eight bytes per occurrence for ordinary files, with no vocabulary-size cap.
trait Pair: Copy + Ord {
    fn pack(first: usize, second: usize) -> Self;
    fn unpack(self) -> (usize, usize);
}

impl Pair for u64 {
    #[inline]
    fn pack(first: usize, second: usize) -> Self {
        ((first as u64) << 32) | second as u64
    }
    #[inline]
    fn unpack(self) -> (usize, usize) {
        ((self >> 32) as usize, (self as u32) as usize)
    }
}

impl Pair for u128 {
    #[inline]
    fn pack(first: usize, second: usize) -> Self {
        ((first as u128) << 64) | second as u128
    }
    #[inline]
    fn unpack(self) -> (usize, usize) {
        ((self >> 64) as usize, (self as u64) as usize)
    }
}

fn solve<K: Pair>(data: &[u8]) -> io::Result<()> {
    let mut vocabulary: HashMap<&[u8], usize, BuildHasherDefault<WordHasher>> =
        HashMap::with_capacity_and_hasher(4096, BuildHasherDefault::default());
    let mut words: Vec<&[u8]> = Vec::new();
    let mut pairs: Vec<K> = Vec::with_capacity(data.len() / 6);
    let mut word_count = 0usize;
    let mut previous = None;
    let mut i = 0;
    while i < data.len() {
        let byte = data[i];
        if byte.is_ascii_lowercase() {
            let start = i;
            i += 1;
            while i < data.len() && data[i].is_ascii_lowercase() {
                i += 1;
            }
            let word = &data[start..i];
            let next_id = words.len();
            let id = *vocabulary.entry(word).or_insert_with(|| {
                words.push(word);
                next_id
            });
            word_count += 1;
            if let Some(first) = previous {
                pairs.push(K::pack(first, id));
            }
            previous = Some(id);
        } else {
            if matches!(byte, b'.' | b'!' | b'?') {
                previous = None;
            }
            i += 1;
        }
    }
    drop(vocabulary);
    let total = pairs.len();
    pairs.sort_unstable();
    let compare = |a: &(usize, usize, usize), b: &(usize, usize, usize)| {
        b.0.cmp(&a.0)
            .then_with(|| words[a.1].cmp(words[b.1]))
            .then_with(|| words[a.2].cmp(words[b.2]))
    };
    let mut best = Vec::with_capacity(20);
    let mut distinct = 0usize;
    let mut pos = 0;
    let mut cutoff = 0;
    while pos < pairs.len() {
        let key = pairs[pos];
        let start = pos;
        pos += 1;
        while pos < pairs.len() && pairs[pos] == key {
            pos += 1;
        }
        distinct += 1;
        let count = pos - start;
        if count < cutoff {
            continue;
        }
        let (first, second) = key.unpack();
        let item = (count, first, second);
        if best.len() < 20 {
            best.push(item);
            if best.len() == 20 {
                best.sort_unstable_by(&compare);
                cutoff = best[19].0;
            }
        } else if compare(&item, &best[19]) == Ordering::Less {
            best[19] = item;
            best.sort_unstable_by(&compare);
            cutoff = best[19].0;
        }
    }
    best.sort_unstable_by(compare);
    let mut out = io::BufWriter::new(io::stdout().lock());
    writeln!(
        out,
        "words {word_count}\npairs {total}\ndistinct {distinct}"
    )?;
    for (count, first, second) in best {
        write!(out, "{count} ")?;
        out.write_all(words[first])?;
        out.write_all(b" ")?;
        out.write_all(words[second])?;
        out.write_all(b"\n")?;
    }
    out.flush()
}

fn main() -> io::Result<()> {
    let path = std::env::args_os().nth(1).expect("expected input path");
    let mut data = std::fs::read(path)?;
    data.make_ascii_lowercase();
    // At most ceil(bytes / 2) distinct words fit in an ASCII input.
    if data.len() as u128 <= 2 * u32::MAX as u128 {
        solve::<u64>(&data)
    } else {
        solve::<u128>(&data)
    }
}
