use std::fs;
use std::io::{self, BufWriter, Write};

#[derive(Clone, Copy)]
struct Word {
    start: usize,
    end: usize,
    hash: u64,
}

struct Dictionary {
    words: Vec<Word>,
    slots: Vec<usize>,
    limit: usize,
}

#[inline]
fn mix(mut x: u64) -> u64 {
    x ^= x >> 30;
    x = x.wrapping_mul(0xbf58476d1ce4e5b9);
    x ^= x >> 27;
    x = x.wrapping_mul(0x94d049bb133111eb);
    x ^ (x >> 31)
}

impl Dictionary {
    fn new() -> Self {
        Self {
            words: Vec::with_capacity(1024),
            slots: vec![0; 2048],
            limit: 2048 * 7 / 10,
        }
    }

    fn grow(&mut self) {
        let capacity = self.slots.len() * 2;
        let mut slots = vec![0; capacity];
        let mask = capacity - 1;

        for (id, word) in self.words.iter().enumerate() {
            let mut position = word.hash as usize & mask;
            while slots[position] != 0 {
                position = (position + 1) & mask;
            }
            slots[position] = id + 1;
        }

        self.slots = slots;
        self.limit = capacity * 7 / 10;
    }

    #[inline]
    fn intern(&mut self, text: &[u8], start: usize, end: usize, hash: u64) -> usize {
        let mut mask = self.slots.len() - 1;
        let mut position = hash as usize & mask;

        loop {
            let entry = self.slots[position];
            if entry == 0 {
                break;
            }

            let id = entry - 1;
            let word = self.words[id];
            if word.hash == hash
                && word.end - word.start == end - start
                && text[word.start..word.end] == text[start..end]
            {
                return id;
            }

            position = (position + 1) & mask;
        }

        if self.words.len() >= self.limit {
            self.grow();
            mask = self.slots.len() - 1;
            position = hash as usize & mask;
            while self.slots[position] != 0 {
                position = (position + 1) & mask;
            }
        }

        let id = self.words.len();
        self.words.push(Word { start, end, hash });
        self.slots[position] = id + 1;
        id
    }
}

fn radix_sort<T, F>(values: &mut Vec<T>, passes: usize, digit: F)
where
    T: Copy + Default,
    F: Fn(T, usize) -> usize,
{
    let length = values.len();
    if length < 2 {
        return;
    }

    let mut scratch = vec![T::default(); length];

    for pass in 0..passes {
        let mut positions = [0usize; 2048];

        for &value in values.iter() {
            positions[digit(value, pass)] += 1;
        }

        if positions.iter().any(|&count| count == length) {
            continue;
        }

        let mut offset = 0;
        for position in &mut positions {
            let count = *position;
            *position = offset;
            offset += count;
        }

        for &value in values.iter() {
            let bucket = digit(value, pass);
            let position = positions[bucket];

            // Prefix sums give each bucket a disjoint, in-bounds range.
            unsafe {
                *scratch.get_unchecked_mut(position) = value;
            }

            positions[bucket] = position + 1;
        }

        std::mem::swap(values, &mut scratch);
    }
}

struct Hit {
    count: usize,
    first: usize,
    second: usize,
}

fn summarize<T, F>(values: &[T], decode: F) -> (usize, Vec<Hit>)
where
    T: Copy + Eq,
    F: Fn(T) -> (usize, usize),
{
    let mut distinct = 0;
    let mut best: Vec<Hit> = Vec::with_capacity(21);
    let mut start = 0;

    while start < values.len() {
        let value = values[start];
        let mut end = start + 1;
        while end < values.len() && values[end] == value {
            end += 1;
        }

        distinct += 1;
        let count = end - start;

        // Values arrive in lexical order, so existing equal-count hits win.
        if best.len() < 20 || count > best[19].count {
            let position = best.partition_point(|hit| hit.count >= count);
            let (first, second) = decode(value);
            best.insert(
                position,
                Hit {
                    count,
                    first,
                    second,
                },
            );
            if best.len() > 20 {
                best.pop();
            }
        }

        start = end;
    }

    (distinct, best)
}

fn main() {
    let path = std::env::args_os().nth(1).unwrap();
    let mut text = fs::read(path).unwrap();
    text.make_ascii_lowercase();

    let mut dictionary = Dictionary::new();
    let mut small: Vec<u32> = Vec::with_capacity(text.len() / 5);
    let mut large: Vec<(usize, usize)> = Vec::new();
    let mut large_mode = false;

    let mut word_count = 0usize;
    let mut previous: Option<usize> = None;
    let mut position = 0;

    while position < text.len() {
        let byte = text[position];

        if byte.is_ascii_lowercase() {
            let start = position;
            let mut hash = 0xcbf29ce484222325u64;

            while position < text.len() && text[position].is_ascii_lowercase() {
                hash ^= text[position] as u64;
                hash = hash.wrapping_mul(0x100000001b3);
                position += 1;
            }

            let id = dictionary.intern(&text, start, position, mix(hash));
            word_count += 1;

            if !large_mode && id >= 65536 {
                let old = std::mem::take(&mut small);
                large = Vec::with_capacity(old.len());
                large.extend(
                    old.into_iter()
                        .map(|key| ((key >> 16) as usize, (key & 65535) as usize)),
                );
                large_mode = true;
            }

            if let Some(first) = previous {
                if large_mode {
                    large.push((first, id));
                } else {
                    small.push(((first as u32) << 16) | id as u32);
                }
            }
            previous = Some(id);
        } else {
            if matches!(byte, b'.' | b'!' | b'?') {
                previous = None;
            }
            position += 1;
        }
    }

    let pair_count = if large_mode { large.len() } else { small.len() };
    let stdout = io::stdout();
    let mut output = BufWriter::new(stdout.lock());

    if pair_count == 0 {
        writeln!(output, "words {word_count}").unwrap();
        writeln!(output, "pairs 0").unwrap();
        writeln!(output, "distinct 0").unwrap();
        output.flush().unwrap();
        return;
    }

    let vocabulary = dictionary.words.len();
    let mut lexical_ids: Vec<usize> = (0..vocabulary).collect();
    lexical_ids.sort_unstable_by(|&a, &b| {
        let a = dictionary.words[a];
        let b = dictionary.words[b];
        text[a.start..a.end].cmp(&text[b.start..b.end])
    });

    let mut ranks = vec![0usize; vocabulary];
    for (rank, &id) in lexical_ids.iter().enumerate() {
        ranks[id] = rank;
    }

    let (distinct, best) = if large_mode {
        for pair in &mut large {
            pair.0 = ranks[pair.0];
            pair.1 = ranks[pair.1];
        }

        if large.len() < 4096 {
            large.sort_unstable();
        } else {
            let bits = (usize::BITS - (vocabulary - 1).leading_zeros()) as usize;
            let digits = bits.div_ceil(11);

            radix_sort(&mut large, digits * 2, |pair, pass| {
                if pass < digits {
                    (pair.1 >> (pass * 11)) & 2047
                } else {
                    (pair.0 >> ((pass - digits) * 11)) & 2047
                }
            });
        }

        summarize(&large, |pair| pair)
    } else {
        let base = vocabulary as u32;

        for key in &mut small {
            let first = ranks[(*key >> 16) as usize] as u32;
            let second = ranks[(*key & 65535) as usize] as u32;
            *key = first * base + second;
        }

        if small.len() < 4096 {
            small.sort_unstable();
        } else {
            let maximum = vocabulary as u64 * vocabulary as u64 - 1;
            let bits = (64 - maximum.leading_zeros()) as usize;
            radix_sort(&mut small, bits.div_ceil(11), |key, pass| {
                ((key >> (pass * 11)) & 2047) as usize
            });
        }

        summarize(&small, |key| {
            ((key / base) as usize, (key % base) as usize)
        })
    };

    writeln!(output, "words {word_count}").unwrap();
    writeln!(output, "pairs {pair_count}").unwrap();
    writeln!(output, "distinct {distinct}").unwrap();

    for hit in best {
        let first = dictionary.words[lexical_ids[hit.first]];
        let second = dictionary.words[lexical_ids[hit.second]];

        write!(output, "{} ", hit.count).unwrap();
        output.write_all(&text[first.start..first.end]).unwrap();
        output.write_all(b" ").unwrap();
        output.write_all(&text[second.start..second.end]).unwrap();
        output.write_all(b"\n").unwrap();
    }

    output.flush().unwrap();
}
