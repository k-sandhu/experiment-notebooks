use std::collections::HashMap;
use std::io::{self, Write};

const NONE: usize = usize::MAX;
const BUCKET_COUNT: usize = 1024;
const BUCKET_MASK: usize = BUCKET_COUNT - 1;

struct Scanner<'a> {
    data: &'a [u8],
    pos: usize,
}

impl Scanner<'_> {
    #[inline(always)]
    fn next(&mut self) -> usize {
        while self.pos < self.data.len() && self.data[self.pos] <= b' ' {
            self.pos += 1;
        }

        let mut value = 0usize;
        while self.pos < self.data.len() {
            let digit = self.data[self.pos].wrapping_sub(b'0');
            if digit > 9 {
                break;
            }
            value = value * 10 + digit as usize;
            self.pos += 1;
        }
        value
    }
}

struct BucketQueue {
    heads: [usize; BUCKET_COUNT],
    occupied: [u64; BUCKET_COUNT / 64],
    summary: u64,
    cursor: usize,
    previous: Vec<usize>,
    next: Vec<usize>,
}

impl BucketQueue {
    fn new(n: usize) -> Self {
        Self {
            heads: [NONE; BUCKET_COUNT],
            occupied: [0; BUCKET_COUNT / 64],
            summary: 0,
            cursor: 0,
            previous: vec![0; n],
            next: vec![0; n],
        }
    }

    fn clear(&mut self) {
        self.heads.fill(NONE);
        self.occupied.fill(0);
        self.summary = 0;
        self.cursor = 0;
    }

    #[inline(always)]
    fn insert(&mut self, node: usize, distance: u64) {
        let bucket = distance as usize & BUCKET_MASK;
        let head = self.heads[bucket];

        self.previous[node] = NONE;
        self.next[node] = head;

        if head != NONE {
            self.previous[head] = node;
        } else {
            let word = bucket >> 6;
            self.occupied[word] |= 1u64 << (bucket & 63);
            self.summary |= 1u64 << word;
        }

        self.heads[bucket] = node;
    }

    #[inline(always)]
    fn remove(&mut self, node: usize, bucket: usize) {
        let previous = self.previous[node];
        let next = self.next[node];

        if previous == NONE {
            self.heads[bucket] = next;
        } else {
            self.next[previous] = next;
        }

        if next != NONE {
            self.previous[next] = previous;
        }

        if self.heads[bucket] == NONE {
            let word = bucket >> 6;
            self.occupied[word] &= !(1u64 << (bucket & 63));
            if self.occupied[word] == 0 {
                self.summary &= !(1u64 << word);
            }
        }
    }

    #[inline(always)]
    fn pop(&mut self) -> Option<usize> {
        if self.summary == 0 {
            return None;
        }

        if self.heads[self.cursor] == NONE {
            let word = self.cursor >> 6;
            let remaining =
                self.occupied[word] & (u64::MAX << (self.cursor & 63));

            if remaining != 0 {
                self.cursor = (word << 6) + remaining.trailing_zeros() as usize;
            } else {
                let later_words = self.summary & (u64::MAX << (word + 1));
                let next_word = if later_words != 0 {
                    later_words.trailing_zeros() as usize
                } else {
                    self.summary.trailing_zeros() as usize
                };

                self.cursor = (next_word << 6)
                    + self.occupied[next_word].trailing_zeros() as usize;
            }
        }

        let node = self.heads[self.cursor];
        self.remove(node, self.cursor);
        Some(node)
    }
}

#[derive(Clone, Copy)]
struct Answer {
    reachable: usize,
    total: u64,
    farthest: u64,
    node: usize,
}

fn shortest_paths(
    source: usize,
    offsets: &[usize],
    destinations: &[usize],
    weights: &[u16],
    distances: &mut [u64],
    queue: &mut BucketQueue,
) -> Answer {
    distances.fill(u64::MAX);
    queue.clear();

    distances[source] = 0;
    queue.insert(source, 0);

    let mut answer = Answer {
        reachable: 0,
        total: 0,
        farthest: 0,
        node: source,
    };

    // All queued distances lie within 1000 of the current minimum.
    // Thus 1024 circular buckets never mix different active distances.
    while let Some(u) = queue.pop() {
        let distance = distances[u];
        answer.reachable += 1;
        answer.total += distance;

        if distance > answer.farthest {
            answer.farthest = distance;
            answer.node = u;
        } else if distance == answer.farthest && u < answer.node {
            answer.node = u;
        }

        let begin = offsets[u];
        let end = offsets[u + 1];
        let neighbors = &destinations[begin..end];
        let lengths = &weights[begin..end];

        for (&v, &weight) in neighbors.iter().zip(lengths.iter()) {
            let candidate = distance + weight as u64;
            let old_distance = distances[v];

            if candidate < old_distance {
                if old_distance != u64::MAX {
                    queue.remove(v, old_distance as usize & BUCKET_MASK);
                }
                distances[v] = candidate;
                queue.insert(v, candidate);
            }
        }
    }

    answer
}

fn main() {
    let path = std::env::args_os().nth(1).unwrap();
    let input = std::fs::read(path).unwrap();
    let mut scanner = Scanner {
        data: &input,
        pos: 0,
    };

    let n = scanner.next();
    let m = scanner.next();
    let q = scanner.next();
    let roads_start = scanner.pos;

    let mut cursors = vec![0usize; n];

    for _ in 0..m {
        let u = scanner.next();
        let v = scanner.next();
        let _weight = scanner.next();

        if u != v {
            cursors[u] += 1;
            cursors[v] += 1;
        }
    }

    let mut offsets = vec![0usize; n + 1];
    for u in 0..n {
        offsets[u + 1] = offsets[u] + cursors[u];
        cursors[u] = offsets[u];
    }

    let edge_count = offsets[n];
    let mut destinations = vec![0usize; edge_count];
    let mut weights = vec![0u16; edge_count];

    scanner.pos = roads_start;

    for _ in 0..m {
        let u = scanner.next();
        let v = scanner.next();
        let weight = scanner.next() as u16;

        if u != v {
            let a = cursors[u];
            destinations[a] = v;
            weights[a] = weight;
            cursors[u] += 1;

            let b = cursors[v];
            destinations[b] = u;
            weights[b] = weight;
            cursors[v] += 1;
        }
    }

    let mut sources = Vec::with_capacity(q);
    for _ in 0..q {
        sources.push(scanner.next());
    }

    drop(scanner);
    drop(input);
    drop(cursors);

    let mut distances = vec![u64::MAX; n];
    let mut queue = BucketQueue::new(n);
    let mut cache: HashMap<usize, Answer> = HashMap::new();

    let stdout = io::stdout();
    let mut output = io::BufWriter::new(stdout.lock());

    for source in sources {
        let answer = if let Some(&answer) = cache.get(&source) {
            answer
        } else {
            let answer = shortest_paths(
                source,
                &offsets,
                &destinations,
                &weights,
                &mut distances,
                &mut queue,
            );
            cache.insert(source, answer);
            answer
        };

        writeln!(
            output,
            "{} {} {} {} {}",
            source, answer.reachable, answer.total, answer.farthest, answer.node
        )
        .unwrap();
    }

    output.flush().unwrap();
}
