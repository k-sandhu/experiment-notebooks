use std::env;
use std::fs;
use std::io::{self, Write};

fn is_letter(b: u8) -> bool {
    matches!(b, b'A'..=b'Z' | b'a'..=b'z')
}

fn is_sentence_end(b: u8) -> bool {
    b == b'.' || b == b'!' || b == b'?'
}

// FNV-1a over the (already lowercased) word bytes.
fn hash_bytes(bytes: &[u8]) -> u64 {
    let mut h: u64 = 0xcbf29ce484222325;
    for &b in bytes {
        h ^= b as u64;
        h = h.wrapping_mul(0x100000001b3);
    }
    h
}

// Open-addressing map for interning words. Empty slots carry an empty String;
// words are never empty, so this is a safe sentinel. The table stays small
// (vocabulary-sized) and cache-friendly.
struct WordMap {
    slots: Vec<(String, u32)>,
    count: usize,
    mask: usize,
}

impl WordMap {
    fn with_capacity(cap: usize) -> Self {
        let size = cap.next_power_of_two().max(16);
        Self {
            slots: vec![(String::new(), 0); size],
            count: 0,
            mask: size - 1,
        }
    }

    fn grow(&mut self) {
        let old = std::mem::replace(
            self,
            Self {
                slots: Vec::new(),
                count: 0,
                mask: 0,
            },
        );
        let size = (old.slots.len() * 2).max(16);
        let mut slots = vec![(String::new(), 0); size];
        let mask = size - 1;
        for (word, id) in old.slots {
            if word.is_empty() {
                continue;
            }
            let mut h = hash_bytes(word.as_bytes());
            loop {
                let idx = (h & mask as u64) as usize;
                if slots[idx].0.is_empty() {
                    slots[idx] = (word, id);
                    break;
                }
                h = h.wrapping_add(1);
            }
        }
        *self = Self {
            slots,
            count: old.count,
            mask,
        };
    }

    /// Returns the id of `w`, inserting it with `id` when first seen.
    fn get_or_insert(&mut self, w: &str, id: u32) -> u32 {
        if (self.count + 1) * 10 > self.slots.len() * 7 {
            self.grow();
        }
        let mut h = hash_bytes(w.as_bytes());
        loop {
            let idx = (h & self.mask as u64) as usize;
            if self.slots[idx].0.is_empty() {
                self.slots[idx] = (w.to_owned(), id);
                self.count += 1;
                return id;
            }
            if self.slots[idx].0 == w {
                return self.slots[idx].1;
            }
            h = h.wrapping_add(1);
        }
    }
}

fn main() -> io::Result<()> {
    let path = env::args().nth(1).expect("usage: solution INPUT_PATH");
    let data = fs::read(&path).expect("failed to read input file");

    let mut words: Vec<String> = Vec::new();
    let mut word_ids = WordMap::with_capacity(1 << 16);
    // One packed u64 per pair occurrence; sorted and run-counted instead of
    // hashed, keeping memory access sequential.
    let mut pair_keys: Vec<u64> = Vec::new();

    let mut words_count: u64 = 0;
    let mut pairs_count: u64 = 0;
    let mut prev: Option<u32> = None;

    let mut buf: Vec<u8> = Vec::with_capacity(64);

    let mut i = 0usize;
    let n = data.len();
    while i < n {
        // Skip separators. Sentence enders terminate the current sentence, so
        // the next word starts a new sentence and forms no pair with earlier words.
        while i < n {
            let b = data[i];
            if is_letter(b) {
                break;
            }
            if is_sentence_end(b) {
                prev = None;
            }
            i += 1;
        }
        if i >= n {
            break;
        }

        let start = i;
        while i < n && is_letter(data[i]) {
            i += 1;
        }

        // Lowercase the word into the scratch buffer. All characters here are
        // ASCII letters, so the slice is valid UTF-8 and setting bit 5
        // lowercases them.
        let wstart = buf.len();
        buf.extend_from_slice(&data[start..i]);
        for b in &mut buf[wstart..] {
            *b |= 0x20;
        }
        let w = unsafe { std::str::from_utf8_unchecked(&buf[wstart..]) };

        let id = word_ids.get_or_insert(w, words.len() as u32);
        if id as usize == words.len() {
            words.push(w.to_owned());
        }
        buf.truncate(wstart);

        words_count += 1;
        if let Some(p) = prev {
            pair_keys.push((p as u64) << 32 | id as u64);
            pairs_count += 1;
        }
        prev = Some(id);
    }

    // Remap word ids so that id order is lexicographic by word bytes. Then
    // sorted pair keys are ordered by (first word, second word), and a stable
    // sort by count gives the required total order.
    let vocab = words.len();
    let mut order: Vec<usize> = (0..vocab).collect();
    order.sort_by(|&a, &b| words[a].cmp(&words[b]));
    let mut remap: Vec<u32> = vec![0; vocab];
    for (new_id, &old_id) in order.iter().enumerate() {
        remap[old_id] = new_id as u32;
    }
    // Reorder words so that index == remapped id == lexicographic order.
    let ordered_words: Vec<String> = order.into_iter().map(|i| std::mem::take(&mut words[i])).collect();
    words = ordered_words;

    for key in &mut pair_keys {
        let first = remap[((*key >> 32) as u32) as usize];
        let second = remap[(*key as u32) as usize];
        *key = (first as u64) << 32 | second as u64;
    }
    pair_keys.sort_unstable();

    // Run-count the sorted keys into (count, first_id, second_id) items, which
    // are ordered by (first word, second word) within each count.
    let mut items: Vec<(u32, u32, u32)> = Vec::new();
    let mut idx = 0usize;
    let m = pair_keys.len();
    while idx < m {
        let key = pair_keys[idx];
        let mut nxt = idx + 1;
        while nxt < m && pair_keys[nxt] == key {
            nxt += 1;
        }
        items.push(((nxt - idx) as u32, (key >> 32) as u32, key as u32));
        idx = nxt;
    }

    // Stable sort by count descending; ties keep (first word, second word)
    // ascending because items are already in that order.
    items.sort_by(|a, b| b.0.cmp(&a.0));

    let mut out = String::new();
    out.push_str(&format!(
        "words {}\npairs {}\ndistinct {}\n",
        words_count,
        pairs_count,
        items.len()
    ));
    let limit = items.len().min(20);
    for item in items.iter().take(limit) {
        out.push_str(&format!(
            "{} {} {}\n",
            item.0,
            words[item.1 as usize],
            words[item.2 as usize]
        ));
    }
    io::stdout().lock().write_all(out.as_bytes())?;
    Ok(())
}
