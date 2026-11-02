use std::cmp::Reverse;
use std::collections::BinaryHeap;
use std::io::Write;

struct Scanner<'a> {
    b: &'a [u8],
    p: usize,
}

impl<'a> Scanner<'a> {
    #[inline]
    fn next(&mut self) -> u64 {
        let b = self.b;
        let mut p = self.p;
        while p < b.len() && !(b[p] >= b'0' && b[p] <= b'9') {
            p += 1;
        }
        let mut v = 0u64;
        while p < b.len() && b[p] >= b'0' && b[p] <= b'9' {
            v = v * 10 + (b[p] - b'0') as u64;
            p += 1;
        }
        self.p = p;
        v
    }
}

const INF: u64 = u64::MAX;

macro_rules! dijkstra {
    ($name:ident, $t:ty, $shift:expr) => {
        fn $name(start: &[u32], adj: &[(u32, u32)], s: usize, dist: &mut Vec<u64>) {
            const MASK: $t = ((1 as $t) << $shift) - 1;
            for d in dist.iter_mut() {
                *d = INF;
            }
            let mut heap: BinaryHeap<Reverse<$t>> = BinaryHeap::new();
            dist[s] = 0;
            heap.push(Reverse(s as $t));
            while let Some(Reverse(key)) = heap.pop() {
                let u = (key & MASK) as usize;
                let d = (key >> $shift) as u64;
                if d > dist[u] {
                    continue;
                }
                let (a, b) = (start[u] as usize, start[u + 1] as usize);
                for i in a..b {
                    let (v, w) = adj[i];
                    let v = v as usize;
                    let nd = d + w as u64;
                    if nd < dist[v] {
                        dist[v] = nd;
                        heap.push(Reverse(((nd as $t) << $shift) | v as $t));
                    }
                }
            }
        }
    };
}

dijkstra!(dijkstra_small, u64, 32);
dijkstra!(dijkstra_big, u128, 64);

fn dial(start: &[u32], adj: &[(u32, u32)], s: usize, dist: &mut Vec<u64>, buckets: &mut Vec<Vec<u32>>) {
    let mask = buckets.len() - 1;
    for d in dist.iter_mut() {
        *d = INF;
    }
    dist[s] = 0;
    buckets[0].push(s as u32);
    let mut pending = 1usize;
    let mut cur = 0u64;
    while pending > 0 {
        let bi = (cur as usize) & mask;
        let mut list = std::mem::take(&mut buckets[bi]);
        pending -= list.len();
        for &u in list.iter() {
            let u = u as usize;
            if dist[u] != cur {
                continue;
            }
            let (a, b) = (start[u] as usize, start[u + 1] as usize);
            for &(v, w) in &adj[a..b] {
                let nd = cur + w as u64;
                let dv = &mut dist[v as usize];
                if nd < *dv {
                    *dv = nd;
                    buckets[(nd as usize) & mask].push(v);
                    pending += 1;
                }
            }
        }
        list.clear();
        buckets[bi] = list;
        cur += 1;
    }
}

fn main() {
    let path = std::env::args().nth(1).expect("input path");
    let data = std::fs::read(&path).expect("read");
    let mut sc = Scanner { b: &data, p: 0 };
    let n = sc.next() as usize;
    let m = sc.next() as usize;
    let q = sc.next() as usize;
    let mut eu = Vec::with_capacity(m);
    let mut ev = Vec::with_capacity(m);
    let mut ew = Vec::with_capacity(m);
    let mut start = vec![0u32; n + 2];
    for _ in 0..m {
        let u = sc.next() as u32;
        let v = sc.next() as u32;
        let w = sc.next() as u32;
        eu.push(u);
        ev.push(v);
        ew.push(w);
        if u != v {
            start[u as usize + 2] += 1;
            start[v as usize + 2] += 1;
        }
    }
    for i in 2..n + 2 {
        start[i] += start[i - 1];
    }
    // start[i+1] is now the fill pointer for node i
    let total = start[n + 1] as usize;
    let mut adj = vec![(0u32, 0u32); total];
    for i in 0..m {
        let (u, v, w) = (eu[i] as usize, ev[i] as usize, ew[i]);
        if u == v {
            continue;
        }
        let p = start[u + 1] as usize;
        adj[p] = (v as u32, w);
        start[u + 1] += 1;
        let p = start[v + 1] as usize;
        adj[p] = (u as u32, w);
        start[v + 1] += 1;
    }
    drop((eu, ev, ew));
    let start = &start[..n + 1];

    let small = (n as u64).saturating_mul(1000) < (1u64 << 32) && (n as u64) < (1u64 << 32);
    let maxw = adj.iter().map(|e| e.1).max().unwrap_or(1) as usize;
    let use_dial = maxw < (1 << 16);
    let mut buckets: Vec<Vec<u32>> = if use_dial {
        vec![Vec::new(); (maxw + 1).next_power_of_two()]
    } else {
        Vec::new()
    };
    let mut dist = vec![INF; n];
    let mut out = String::new();
    let mut cache: std::collections::HashMap<usize, String> = std::collections::HashMap::new();
    for _ in 0..q {
        let s = sc.next() as usize;
        if let Some(l) = cache.get(&s) {
            out.push_str(l);
            continue;
        }
        if use_dial {
            dial(start, &adj, s, &mut dist, &mut buckets);
        } else if small {
            dijkstra_small(start, &adj, s, &mut dist);
        } else {
            dijkstra_big(start, &adj, s, &mut dist);
        }
        let mut r = 0u64;
        let mut total = 0u64;
        let mut far = 0u64;
        let mut node = s;
        for (i, &d) in dist.iter().enumerate() {
            if d == INF {
                continue;
            }
            r += 1;
            total += d;
            if d > far {
                far = d;
                node = i;
            }
        }
        let line = format!("{} {} {} {} {}\n", s, r, total, far, node);
        out.push_str(&line);
        cache.insert(s, line);
    }
    std::io::stdout().write_all(out.as_bytes()).unwrap();
}
