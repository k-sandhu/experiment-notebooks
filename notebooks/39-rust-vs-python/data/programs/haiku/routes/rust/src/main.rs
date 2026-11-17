// Shortest paths from each source with Dial's algorithm: the weights are small
// integers, so distances are processed in order using a ring of buckets
// instead of a heap.

use std::fmt::Write as _;
use std::io::Write as _;

const INF: u64 = u64::MAX;

/// Reads unsigned decimal integers from a byte buffer, skipping any separators.
struct Scanner<'a> {
    buf: &'a [u8],
    pos: usize,
}

impl Scanner<'_> {
    fn next(&mut self) -> u64 {
        let buf = self.buf;
        let mut p = self.pos;
        while p < buf.len() && !buf[p].is_ascii_digit() {
            p += 1;
        }
        let mut x = 0u64;
        while p < buf.len() && buf[p].is_ascii_digit() {
            x = x * 10 + (buf[p] - b'0') as u64;
            p += 1;
        }
        self.pos = p;
        x
    }
}

fn main() {
    let path = std::env::args().nth(1).expect("usage: solution INPUT_PATH");
    let data = std::fs::read(&path).expect("cannot read input file");
    let mut sc = Scanner { buf: &data, pos: 0 };

    let n = sc.next() as usize;
    let m = sc.next() as usize;
    let q = sc.next() as usize;

    // Self-loops never shorten a path, so they are dropped.
    let mut edges: Vec<(u32, u32, u32)> = Vec::with_capacity(m);
    let mut max_w = 1u32;
    for _ in 0..m {
        let u = sc.next() as u32;
        let v = sc.next() as u32;
        let w = sc.next() as u32;
        max_w = max_w.max(w);
        if u != v {
            edges.push((u, v, w));
        }
    }

    // Compressed adjacency (CSR): the neighbours of v are adj[start[v]..start[v + 1]].
    let mut start = vec![0u32; n + 1];
    for &(u, v, _) in &edges {
        start[u as usize + 1] += 1;
        start[v as usize + 1] += 1;
    }
    for i in 0..n {
        start[i + 1] += start[i];
    }
    let mut cursor = start.clone();
    let mut adj = vec![(0u32, 0u32); edges.len() * 2];
    for &(u, v, w) in &edges {
        let (u, v) = (u as usize, v as usize);
        adj[cursor[u] as usize] = (v as u32, w);
        cursor[u] += 1;
        adj[cursor[v] as usize] = (u as u32, w);
        cursor[v] += 1;
    }
    drop(cursor);
    drop(edges);

    // A ring larger than the largest weight means a node pushed while scanning
    // bucket d never lands back in bucket d itself.
    let ring = (max_w as usize + 1).next_power_of_two();
    let mask = ring - 1;
    let mut buckets: Vec<Vec<u32>> = vec![Vec::new(); ring];
    let mut dist = vec![INF; n];

    let mut out = String::new();
    for _ in 0..q {
        let s = sc.next() as usize;
        dist.fill(INF);
        dist[s] = 0;
        buckets[0].push(s as u32);
        let mut pending = 1usize;

        let mut d = 0u64;
        let mut reach = 0u64;
        let mut total = 0u64;
        let mut far = 0u64;
        let mut far_node = s as u32;

        while pending > 0 {
            let idx = (d as usize) & mask;
            let cur = std::mem::take(&mut buckets[idx]);
            for &v in &cur {
                // Stale entries were superseded by a shorter distance.
                if dist[v as usize] != d {
                    continue;
                }
                reach += 1;
                total += d;
                if d > far {
                    far = d;
                    far_node = v;
                } else if d == far && v < far_node {
                    far_node = v;
                }
                let v = v as usize;
                for &(to, w) in &adj[start[v] as usize..start[v + 1] as usize] {
                    let nd = d + w as u64;
                    let t = to as usize;
                    if nd < dist[t] {
                        dist[t] = nd;
                        buckets[(nd as usize) & mask].push(to);
                        pending += 1;
                    }
                }
            }
            pending -= cur.len();
            let mut cur = cur;
            cur.clear();
            buckets[idx] = cur;
            d += 1;
        }

        writeln!(out, "{} {} {} {} {}", s, reach, total, far, far_node).unwrap();
    }
    print!("{}", out);
    std::io::stdout().flush().unwrap();
}
