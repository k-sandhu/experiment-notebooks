use std::collections::HashMap;
use std::hash::{BuildHasherDefault, Hasher};
use std::io::{self, BufWriter, Write};

#[derive(Default)]
struct WordHasher {
    state: u64,
}

impl Hasher for WordHasher {
    #[inline]
    fn finish(&self) -> u64 {
        let mut x = self.state;
        x ^= x >> 30;
        x = x.wrapping_mul(0xbf58476d1ce4e5b9);
        x ^= x >> 27;
        x = x.wrapping_mul(0x94d049bb133111eb);
        x ^ (x >> 31)
    }

    #[inline]
    fn write_usize(&mut self, value: usize) {
        self.state = (value as u64) ^ 0x9e3779b97f4a7c15;
    }

    #[inline]
    fn write(&mut self, mut bytes: &[u8]) {
        const K: u64 = 0x517cc1b727220a95;
        let mut h = self.state;

        while bytes.len() >= 8 {
            let value =
                unsafe { std::ptr::read_unaligned(bytes.as_ptr().cast::<u64>()) };
            h = (h ^ value).rotate_left(27).wrapping_mul(K);
            bytes = &bytes[8..];
        }

        let mut tail = 0u64;
        for (i, &byte) in bytes.iter().enumerate() {
            tail |= (byte as u64) << (i * 8);
        }
        self.state = (h ^ tail).wrapping_mul(K);
    }
}

fn radix_sort(values: &mut Vec<usize>, maximum: usize) {
    if values.len() < 2 || maximum == 0 {
        return;
    }

    const BITS: u32 = 11;
    const BUCKETS: usize = 1 << BITS;
    const MASK: usize = BUCKETS - 1;

    let mut scratch = vec![0usize; values.len()];
    let mut shift = 0u32;

    while shift < usize::BITS && (maximum >> shift) != 0 {
        let mut offsets = [0usize; BUCKETS];

        for &value in values.iter() {
            offsets[(value >> shift) & MASK] += 1;
        }

        if offsets.iter().any(|&count| count == values.len()) {
            shift += BITS;
            continue;
        }

        let mut sum = 0usize;
        for offset in &mut offsets {
            let count = *offset;
            *offset = sum;
            sum += count;
        }

        for &value in values.iter() {
            let bucket = (value >> shift) & MASK;
            unsafe {
                let offset = offsets.get_unchecked_mut(bucket);
                *scratch.get_unchecked_mut(*offset) = value;
                *offset += 1;
            }
        }

        std::mem::swap(values, &mut scratch);
        shift += BITS;
    }
}

fn summarize<T: Copy + Eq>(
    sorted: &[T],
    to_code: impl Fn(T) -> u128,
) -> (usize, Vec<(usize, u128)>) {
    let mut distinct = 0usize;
    let mut top: Vec<(usize, u128)> = Vec::with_capacity(20);
    let mut start = 0usize;

    while start < sorted.len() {
        let value = sorted[start];
        let mut end = start + 1;
        while end < sorted.len() && sorted[end] == value {
            end += 1;
        }

        distinct += 1;
        let count = end - start;

        // Codes arrive in ascending lexical order, so later ties lose.
        if top.len() < 20 || count > top[19].0 {
            let position = top.partition_point(|&(existing, _)| existing >= count);
            if top.len() == 20 {
                top.pop();
            }
            top.insert(position, (count, to_code(value)));
        }

        start = end;
    }

    (distinct, top)
}

fn main() {
    let path = std::env::args_os().nth(1).unwrap();
    let mut data = std::fs::read(path).unwrap();
    data.make_ascii_lowercase();

    let initial_capacity = (data.len() / 32).min(32_768);
    let mut dictionary: HashMap<&[u8], usize, BuildHasherDefault<WordHasher>> =
        HashMap::with_capacity_and_hasher(
            initial_capacity,
            BuildHasherDefault::default(),
        );

    let mut words: Vec<&[u8]> = Vec::new();
    let mut tokens: Vec<usize> = Vec::with_capacity(data.len() / 6);
    let mut sentence_start = true;
    let mut total_pairs = 0usize;
    let mut position = 0usize;

    while position < data.len() {
        let byte = data[position];

        if byte.is_ascii_lowercase() {
            let start = position;
            position += 1;
            while position < data.len() && data[position].is_ascii_lowercase() {
                position += 1;
            }

            let word = &data[start..position];
            let id = *dictionary.entry(word).or_insert_with(|| {
                let id = words.len();
                words.push(word);
                id
            });

            tokens.push((id << 1) | usize::from(sentence_start));
            if !sentence_start {
                total_pairs += 1;
            }
            sentence_start = false;
        } else {
            if matches!(byte, b'.' | b'!' | b'?') {
                sentence_start = true;
            }
            position += 1;
        }
    }

    let total_words = tokens.len();
    drop(dictionary);

    if total_pairs == 0 {
        println!("words {total_words}\npairs 0\ndistinct 0");
        return;
    }

    let vocabulary_size = words.len();
    let mut lexical_order: Vec<usize> = (0..vocabulary_size).collect();
    lexical_order.sort_unstable_by(|&a, &b| words[a].cmp(words[b]));

    let mut ranks = vec![0usize; vocabulary_size];
    for (rank, &id) in lexical_order.iter().enumerate() {
        ranks[id] = rank;
    }

    let (distinct, top) = if vocabulary_size.checked_mul(vocabulary_size).is_some() {
        let mut previous = 0usize;
        let mut written = 0usize;
        let mut minimum = usize::MAX;
        let mut maximum = 0usize;

        for read in 0..tokens.len() {
            let token = tokens[read];
            let rank = ranks[token >> 1];

            if token & 1 == 0 {
                let code = previous * vocabulary_size + rank;
                tokens[written] = code;
                written += 1;
                minimum = minimum.min(code);
                maximum = maximum.max(code);
            }
            previous = rank;
        }

        tokens.truncate(written);
        if minimum != maximum {
            radix_sort(&mut tokens, maximum);
        }
        summarize(&tokens, |value| value as u128)
    } else {
        let base = vocabulary_size as u128;
        let mut codes = Vec::with_capacity(total_pairs);
        let mut previous = 0usize;

        for token in tokens {
            let rank = ranks[token >> 1];
            if token & 1 == 0 {
                codes.push((previous as u128) * base + rank as u128);
            }
            previous = rank;
        }

        codes.sort_unstable();
        summarize(&codes, |value| value)
    };

    let stdout = io::stdout();
    let mut output = BufWriter::new(stdout.lock());

    writeln!(output, "words {total_words}").unwrap();
    writeln!(output, "pairs {total_pairs}").unwrap();
    writeln!(output, "distinct {distinct}").unwrap();

    let base = vocabulary_size as u128;
    for (count, code) in top {
        let first_rank = (code / base) as usize;
        let second_rank = (code % base) as usize;
        let first = std::str::from_utf8(words[lexical_order[first_rank]]).unwrap();
        let second = std::str::from_utf8(words[lexical_order[second_rank]]).unwrap();
        writeln!(output, "{count} {first} {second}").unwrap();
    }

    output.flush().unwrap();
}
