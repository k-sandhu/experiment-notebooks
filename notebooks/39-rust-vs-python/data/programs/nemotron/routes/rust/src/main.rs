use std::cmp::Reverse;
use std::collections::BinaryHeap;
use std::env;
use std::fs;
use std::io::{self, BufWriter, Write};

struct Scanner<'a> {
    data: &'a [u8],
    pos: usize,
}

impl<'a> Scanner<'a> {
    fn new(data: &'a [u8]) -> Self {
        Scanner { data, pos: 0 }
    }

    fn next_u32(&mut self) -> u32 {
        let data = self.data;
        while self.pos < data.len() && data[self.pos] <= b' ' {
            self.pos += 1;
        }
        let mut n: u32 = 0;
        while self.pos < data.len() && data[self.pos] > b' ' {
            n = n * 10 + (data[self.pos] - b'0') as u32;
            self.pos += 1;
        }
        n
    }
}

fn main() {
    let path = env::args().nth(1).expect("usage: solution INPUT_PATH");
    let data = fs::read(&path).expect("failed to read input file");
    let mut sc = Scanner::new(&data);

    let n = sc.next_u32() as usize;
    let m = sc.next_u32() as usize;
    let q = sc.next_u32() as usize;

    let mut eu = Vec::with_capacity(m);
    let mut ev = Vec::with_capacity(m);
    let mut ew = Vec::with_capacity(m);
    for _ in 0..m {
        eu.push(sc.next_u32());
        ev.push(sc.next_u32());
        ew.push(sc.next_u32());
    }
    let mut sources = Vec::with_capacity(q);
    for _ in 0..q {
        sources.push(sc.next_u32());
    }

    // Compressed-sparse-rows graph (undirected, so 2M directed arcs).
    let mut deg = vec![0usize; n];
    for i in 0..m {
        deg[eu[i] as usize] += 1;
        deg[ev[i] as usize] += 1;
    }
    let mut head = vec![0usize; n + 1];
    for i in 0..n {
        head[i + 1] = head[i] + deg[i];
    }
    let mut cur = head.clone();
    let mut to = vec![0u32; 2 * m];
    let mut wt = vec![0u32; 2 * m];
    for i in 0..m {
        let u = eu[i] as usize;
        let v = ev[i] as usize;
        let w = ew[i];
        let p = cur[u];
        to[p] = v as u32;
        wt[p] = w;
        cur[u] = p + 1;
        let p = cur[v];
        to[p] = u as u32;
        wt[p] = w;
        cur[v] = p + 1;
    }

    let out = BufWriter::new(io::stdout().lock());
    let mut out = out;

    const INF: i64 = i64::MAX / 4;
    let mut dist = vec![INF; n];
    let mut heap: BinaryHeap<Reverse<(i64, u32)>> = BinaryHeap::new();

    for &s in &sources {
        let s = s as usize;
        for d in dist.iter_mut() {
            *d = INF;
        }
        dist[s] = 0;
        heap.clear();
        heap.push(Reverse((0, s as u32)));

        while let Some(Reverse((d, u))) = heap.pop() {
            let u = u as usize;
            if d > dist[u] {
                continue;
            }
            let start = head[u];
            let end = head[u + 1];
            for i in start..end {
                let v = to[i] as usize;
                let nd = d + wt[i] as i64;
                if nd < dist[v] {
                    dist[v] = nd;
                    heap.push(Reverse((nd, v as u32)));
                }
            }
        }

        let mut reach: u64 = 0;
        let mut total: i64 = 0;
        let mut far: i64 = 0;
        let mut node: u32 = s as u32;
        for (u, &d) in dist.iter().enumerate() {
            if d < INF {
                reach += 1;
                total += d;
                if d > far {
                    far = d;
                    node = u as u32;
                }
            }
        }
        writeln!(out, "{} {} {} {} {}", s as u32, reach, total, far, node).unwrap();
    }

    out.flush().unwrap();
}
