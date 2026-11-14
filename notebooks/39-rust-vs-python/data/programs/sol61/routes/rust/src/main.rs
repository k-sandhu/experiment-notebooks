use std::fmt::Write;

const BUCKETS: usize = 1024;

trait Edge: Copy + Default {
    fn pack(value: usize) -> Self;
    fn unpack(self) -> usize;
}

impl Edge for u32 {
    #[inline(always)]
    fn pack(value: usize) -> Self {
        value as u32
    }
    #[inline(always)]
    fn unpack(self) -> usize {
        self as usize
    }
}

impl Edge for usize {
    #[inline(always)]
    fn pack(value: usize) -> Self {
        value
    }
    #[inline(always)]
    fn unpack(self) -> usize {
        self
    }
}

struct Scanner<'a> {
    bytes: &'a [u8],
    pos: usize,
}

impl Scanner<'_> {
    #[inline(always)]
    fn next(&mut self) -> usize {
        while self.pos < self.bytes.len() && self.bytes[self.pos] <= b' ' {
            self.pos += 1;
        }
        let mut value = 0;
        while self.pos < self.bytes.len() {
            let digit = self.bytes[self.pos].wrapping_sub(b'0');
            if digit > 9 {
                break;
            }
            value = value * 10 + digit as usize;
            self.pos += 1;
        }
        value
    }
}

// A circular Dial queue. The two-level bitmap also skips large empty ranges
// in, for example, a long path whose edges all have weight 1000.
struct Queue {
    buckets: Vec<Vec<usize>>,
    words: [u64; 16],
    groups: u64,
}

impl Queue {
    fn new() -> Self {
        Self {
            buckets: (0..BUCKETS).map(|_| Vec::new()).collect(),
            words: [0; 16],
            groups: 0,
        }
    }

    #[inline]
    fn push(&mut self, node: usize, distance: u64) {
        let bucket = distance as usize & (BUCKETS - 1);
        self.buckets[bucket].push(node);
        self.words[bucket >> 6] |= 1u64 << (bucket & 63);
        self.groups |= 1u64 << (bucket >> 6);
    }

    #[inline]
    fn next_bucket(&self, start: usize) -> usize {
        let group = start >> 6;
        let remaining = self.words[group] & (u64::MAX << (start & 63));
        if remaining != 0 {
            return (group << 6) + remaining.trailing_zeros() as usize;
        }
        let later = self.groups & (u64::MAX << (group + 1));
        let next_group = if later != 0 {
            later.trailing_zeros() as usize
        } else {
            self.groups.trailing_zeros() as usize
        };
        (next_group << 6) + self.words[next_group].trailing_zeros() as usize
    }
}

fn shortest_paths<E: Edge>(
    source: usize,
    offsets: &[usize],
    edges: &[E],
    distances: &mut [u64],
    queue: &mut Queue,
) -> (u64, u64, u64, usize) {
    distances.fill(u64::MAX);
    distances[source] = 0;
    queue.push(source, 0);
    let mut current = 0u64;
    let (mut reachable, mut total, mut far, mut far_node) = (0, 0, 0, source);
    while queue.groups != 0 {
        let start = current as usize & (BUCKETS - 1);
        let bucket = queue.next_bucket(start);
        current += ((bucket + BUCKETS - start) & (BUCKETS - 1)) as u64;
        // Positive weights mean that no relaxation inserts into this bucket.
        while let Some(node) = queue.buckets[bucket].pop() {
            if distances[node] != current {
                continue;
            }
            reachable += 1;
            total += current;
            if current > far {
                far = current;
                far_node = node;
            } else if current == far && node < far_node {
                far_node = node;
            }
            for &edge in &edges[offsets[node]..offsets[node + 1]] {
                let edge = edge.unpack();
                let neighbor = edge >> 10;
                let candidate = current + (edge & 1023) as u64;
                if candidate < distances[neighbor] {
                    distances[neighbor] = candidate;
                    queue.push(neighbor, candidate);
                }
            }
        }
        queue.words[bucket >> 6] &= !(1u64 << (bucket & 63));
        if queue.words[bucket >> 6] == 0 {
            queue.groups &= !(1u64 << (bucket >> 6));
        }
    }
    (reachable, total, far, far_node)
}

fn run<E: Edge>(bytes: Vec<u8>) {
    let mut input = Scanner {
        bytes: &bytes,
        pos: 0,
    };
    let n = input.next();
    let m = input.next();
    let q = input.next();
    // Count degrees, then parse the same byte buffer again to construct CSR.
    // This avoids retaining a second copy of all road endpoints.
    let road_start = input.pos;
    let mut offsets = vec![0usize; n + 1];
    for _ in 0..m {
        let u = input.next();
        let v = input.next();
        input.next();
        if u != v {
            offsets[u + 1] += 1;
            offsets[v + 1] += 1;
        }
    }
    let sources: Vec<usize> = (0..q).map(|_| input.next()).collect();
    for i in 1..=n {
        offsets[i] += offsets[i - 1];
    }
    let mut edges = vec![E::default(); offsets[n]];
    let mut cursor = offsets[..n].to_vec();
    input.pos = road_start;
    for _ in 0..m {
        let u = input.next();
        let v = input.next();
        let w = input.next();
        if u != v {
            edges[cursor[u]] = E::pack((v << 10) | w);
            cursor[u] += 1;
            edges[cursor[v]] = E::pack((u << 10) | w);
            cursor[v] += 1;
        }
    }
    drop(cursor);
    drop(bytes);

    let mut distances = vec![u64::MAX; n];
    let mut queue = Queue::new();
    let mut answers = std::collections::HashMap::new();
    let mut output = String::new();
    for source in sources {
        let (r, total, far, node) = *answers.entry(source).or_insert_with(|| {
            shortest_paths(source, &offsets, &edges, &mut distances, &mut queue)
        });
        writeln!(output, "{source} {r} {total} {far} {node}").unwrap();
    }
    print!("{output}");
}

fn main() {
    let path = std::env::args_os().nth(1).expect("input path");
    let bytes = std::fs::read(path).expect("read input");
    let n = Scanner {
        bytes: &bytes,
        pos: 0,
    }
    .next();
    // A 22-bit endpoint plus a 10-bit weight fits a single 32-bit word.
    if n <= 1 << 22 {
        run::<u32>(bytes);
    } else {
        run::<usize>(bytes);
    }
}
