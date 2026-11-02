use std::collections::HashMap;
use std::hash::{BuildHasherDefault, Hasher};
use std::io::{self, Write};

#[derive(Default)]
struct FastHasher(u64);
impl Hasher for FastHasher {
    fn finish(&self) -> u64 { self.0 }
    fn write(&mut self, bytes: &[u8]) {
        let mut h = 0xcbf29ce484222325u64;
        for &b in bytes { h = (h ^ b as u64).wrapping_mul(0x100000001b3); }
        self.0 = h;
    }
    fn write_u64(&mut self, mut x: u64) {
        x ^= x >> 30;
        x = x.wrapping_mul(0xbf58476d1ce4e5b9);
        x ^= x >> 27;
        x = x.wrapping_mul(0x94d049bb133111eb);
        self.0 = x ^ (x >> 31);
    }
}
type Map<K, V> = HashMap<K, V, BuildHasherDefault<FastHasher>>;

fn main() {
    let path = std::env::args_os().nth(1).expect("input path");
    let mut data = std::fs::read(path).expect("read input");
    data.make_ascii_lowercase();
    let mut ids: Map<&[u8], u32> = Map::default();
    let mut words: Vec<&[u8]> = Vec::new();
    let mut counts: Map<u64, u64> = Map::default();
    let (mut i, mut total_words, mut total_pairs) = (0, 0u64, 0u64);
    let mut previous: Option<u32> = None;
    while i < data.len() {
        let c = data[i];
        if c.is_ascii_lowercase() {
            let start = i;
            i += 1;
            while i < data.len() && data[i].is_ascii_lowercase() { i += 1; }
            let word = &data[start..i];
            let id = match ids.get(word) {
                Some(&id) => id,
                None => {
                    let id = u32::try_from(words.len()).expect("too many distinct words");
                    ids.insert(word, id);
                    words.push(word);
                    id
                }
            };
            total_words += 1;
            if let Some(prev) = previous {
                let key = ((prev as u64) << 32) | id as u64;
                *counts.entry(key).or_insert(0) += 1;
                total_pairs += 1;
            }
            previous = Some(id);
        } else {
            if c == b'.' || c == b'!' || c == b'?' { previous = None; }
            i += 1;
        }
    }
    let mut best: Vec<(u64, u64)> = Vec::with_capacity(20);
    let order = |a: &(u64, u64), b: &(u64, u64)| {
        b.1.cmp(&a.1)
            .then_with(|| words[(a.0 >> 32) as usize].cmp(words[(b.0 >> 32) as usize]))
            .then_with(|| words[a.0 as u32 as usize].cmp(words[b.0 as u32 as usize]))
    };
    for (&pair, &count) in &counts {
        let candidate = (pair, count);
        let pos = best.binary_search_by(|item| order(item, &candidate)).unwrap_or_else(|p| p);
        if pos < 20 {
            best.insert(pos, candidate);
            if best.len() > 20 { best.pop(); }
        }
    }
    let mut out = io::BufWriter::new(io::stdout().lock());
    writeln!(out, "words {total_words}\npairs {total_pairs}\ndistinct {}", counts.len()).unwrap();
    for (pair, count) in best {
        writeln!(out, "{} {} {}", count,
            std::str::from_utf8(words[(pair >> 32) as usize]).unwrap(),
            std::str::from_utf8(words[pair as u32 as usize]).unwrap()).unwrap();
    }
}
