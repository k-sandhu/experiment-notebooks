use std::collections::HashMap;
use std::fs;
use std::io::{self, BufWriter, Write};

const BUCKET_COUNT: usize = 1024;
const BUCKET_MASK: usize = BUCKET_COUNT - 1;

struct Scanner {
    data: Vec<u8>,
    pos: usize,
}

impl Scanner {
    #[inline(always)]
    fn next(&mut self) -> usize {
        while self.data[self.pos] <= b' ' {
            self.pos += 1;
        }
        let mut value = 0usize;
        while self.data[self.pos].is_ascii_digit() {
            value = value * 10 + (self.data[self.pos] - b'0') as usize;
            self.pos += 1;
        }
        value
    }
}

struct Graph {
    offsets: Vec<usize>,
    targets: Vec<usize>,
    weights: Vec<u16>,
}

fn read_input() -> (Graph, Vec<usize>) {
    let path = std::env::args_os().nth(1).unwrap();
    let mut data = fs::read(path).unwrap();
    data.push(b' ');
    let mut input = Scanner { data, pos: 0 };

    let n = input.next();
    let m = input.next();
    let q = input.next();
    let roads_start = input.pos;

    let mut offsets = vec![0usize; n + 1];
    for _ in 0..m {
        let u = input.next();
        let v = input.next();
        let _w = input.next();
        if u != v {
            offsets[u + 1] += 1;
            offsets[v + 1] += 1;
        }
    }

    for i in 0..n {
        offsets[i + 1] += offsets[i];
    }

    let mut targets = vec![0usize; offsets[n]];
    let mut weights = vec![0u16; offsets[n]];
    let mut cursor = offsets[..n].to_vec();

    input.pos = roads_start;
    for _ in 0..m {
        let u = input.next();
        let v = input.next();
        let w = input.next() as u16;

        // Positive-length self-loops cannot improve a shortest path.
        if u != v {
            let a = cursor[u];
            targets[a] = v;
            weights[a] = w;
            cursor[u] = a + 1;

            let b = cursor[v];
            targets[b] = u;
            weights[b] = w;
            cursor[v] = b + 1;
        }
    }

    let mut sources = Vec::with_capacity(q);
    for _ in 0..q {
        sources.push(input.next());
    }

    (
        Graph {
            offsets,
            targets,
            weights,
        },
        sources,
    )
}

#[derive(Clone, Copy)]
struct Answer {
    reachable: usize,
    total: u64,
    farthest: u64,
    node: usize,
}

struct Workspace {
    distances: Vec<u64>,
    buckets: Vec<Vec<usize>>,
}

impl Workspace {
    fn new(n: usize) -> Self {
        Self {
            distances: vec![u64::MAX; n],
            buckets: (0..BUCKET_COUNT).map(|_| Vec::new()).collect(),
        }
    }

    fn solve(&mut self, graph: &Graph, source: usize) -> Answer {
        self.distances.fill(u64::MAX);
        self.distances[source] = 0;

        let mut occupied = [0u64; BUCKET_COUNT / 64];
        let mut active_groups = 1u64;
        occupied[0] = 1;
        self.buckets[0].push(source);

        let mut current = 0u64;
        let mut bucket_index = 0usize;

        let mut answer = Answer {
            reachable: 0,
            total: 0,
            farthest: 0,
            node: source,
        };

        loop {
            let group = bucket_index >> 6;
            occupied[group] &= !(1u64 << (bucket_index & 63));
            if occupied[group] == 0 {
                active_groups &= !(1u64 << group);
            }

            // Every edge has weight in 1..=1000, so processing this
            // bucket cannot insert another entry into the same bucket.
            while let Some(u) = self.buckets[bucket_index].pop() {
                if self.distances[u] != current {
                    continue;
                }

                answer.reachable += 1;
                answer.total += current;
                if current > answer.farthest {
                    answer.farthest = current;
                    answer.node = u;
                } else if current == answer.farthest && u < answer.node {
                    answer.node = u;
                }

                for edge in graph.offsets[u]..graph.offsets[u + 1] {
                    let v = graph.targets[edge];
                    let candidate = current + graph.weights[edge] as u64;

                    if candidate < self.distances[v] {
                        self.distances[v] = candidate;

                        let index = (candidate & BUCKET_MASK as u64) as usize;
                        self.buckets[index].push(v);

                        let target_group = index >> 6;
                        occupied[target_group] |= 1u64 << (index & 63);
                        active_groups |= 1u64 << target_group;
                    }
                }
            }

            if active_groups == 0 {
                break;
            }

            // Find the next occupied bucket in circular order without
            // scanning through unused distance values.
            let remaining = occupied[group] & (u64::MAX << (bucket_index & 63));
            let next_index = if remaining != 0 {
                (group << 6) + remaining.trailing_zeros() as usize
            } else {
                let later_groups = active_groups & (u64::MAX << (group + 1));
                let next_group = if later_groups != 0 {
                    later_groups.trailing_zeros() as usize
                } else {
                    active_groups.trailing_zeros() as usize
                };
                (next_group << 6) + occupied[next_group].trailing_zeros() as usize
            };

            current += (next_index.wrapping_sub(bucket_index) & BUCKET_MASK) as u64;
            bucket_index = next_index;
        }

        answer
    }
}

fn main() {
    let (graph, sources) = read_input();
    let mut workspace = Workspace::new(graph.offsets.len() - 1);
    let mut cache: HashMap<usize, Answer> = HashMap::new();

    let stdout = io::stdout();
    let mut output = BufWriter::new(stdout.lock());

    for source in sources {
        let answer = match cache.get(&source) {
            Some(&answer) => answer,
            None => {
                let answer = workspace.solve(&graph, source);
                cache.insert(source, answer);
                answer
            }
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
