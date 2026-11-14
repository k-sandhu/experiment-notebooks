use std::cmp::Reverse;
use std::collections::BinaryHeap;
use std::io::Write;

struct Parser<'a> {
    d: &'a [u8],
    i: usize,
}

impl<'a> Parser<'a> {
    #[inline(always)]
    fn next(&mut self) -> Option<u64> {
        let d = self.d;
        let len = d.len();
        let mut i = self.i;
        while i < len && !d[i].is_ascii_digit() {
            i += 1;
        }
        if i >= len {
            self.i = i;
            return None;
        }
        let mut x: u64 = 0;
        while i < len {
            let c = d[i].wrapping_sub(b'0');
            if c > 9 {
                break;
            }
            x = x.wrapping_mul(10).wrapping_add(c as u64);
            i += 1;
        }
        self.i = i;
        Some(x)
    }
}

fn build<T: Copy + Default>(
    n: usize,
    edges: &[u32],
    off: &[u32],
    f: impl Fn(u32, u32) -> T,
) -> Vec<T> {
    let total = off[n] as usize;
    let mut adj: Vec<T> = vec![T::default(); total];
    let mut pos: Vec<u32> = off[..n].to_vec();
    for c in edges.chunks_exact(3) {
        let (u, v, w) = (c[0], c[1], c[2]);
        let pu = &mut pos[u as usize];
        adj[*pu as usize] = f(v, w);
        *pu += 1;
        let pv = &mut pos[v as usize];
        adj[*pv as usize] = f(u, w);
        *pv += 1;
    }
    adj
}

#[inline(always)]
fn next_bucket(bm: &[u64; 16], start: usize) -> Option<usize> {
    let w = (start >> 6) & 15;
    let m = bm[w] & (!0u64 << (start & 63));
    if m != 0 {
        return Some((w << 6) + m.trailing_zeros() as usize);
    }
    for i in 1..=16usize {
        let ww = (w + i) & 15;
        let m = bm[ww];
        if m != 0 {
            return Some((ww << 6) + m.trailing_zeros() as usize);
        }
    }
    None
}

// Dial's algorithm with 1024 circular buckets; requires weights in 1..=1023
// and n <= 2^22 (edges packed as target | weight << 22).
fn dial(
    off: &[u32],
    adj: &[u32],
    src: usize,
    dist: &mut [u32],
    buckets: &mut [Vec<u32>; 1024],
    cur_vec: &mut Vec<u32>,
) -> (u64, u64, u64, u32) {
    dist.fill(u32::MAX);
    dist[src] = 0;
    let mut bm = [0u64; 16];
    buckets[0].push(src as u32);
    bm[0] |= 1;
    let mut cur: u32 = 0;
    let mut r: u64 = 0;
    let mut total: u64 = 0;
    let mut far: u32 = 0;
    let mut node: u32 = src as u32;
    loop {
        let b = (cur & 1023) as usize;
        std::mem::swap(cur_vec, &mut buckets[b]);
        bm[b >> 6] &= !(1u64 << (b & 63));
        for &v in cur_vec.iter() {
            let vi = v as usize;
            if dist[vi] != cur {
                continue;
            }
            r += 1;
            total += cur as u64;
            if cur > far {
                far = cur;
                node = v;
            } else if v < node {
                node = v;
            }
            let s = off[vi] as usize;
            let e = off[vi + 1] as usize;
            for &pe in &adj[s..e] {
                let t = (pe & 0x3F_FFFF) as usize;
                let nd = cur + (pe >> 22);
                let dt = &mut dist[t];
                if nd < *dt {
                    *dt = nd;
                    let nb = (nd & 1023) as usize;
                    buckets[nb].push(t as u32);
                    bm[nb >> 6] |= 1u64 << (nb & 63);
                }
            }
        }
        cur_vec.clear();
        match next_bucket(&bm, b) {
            None => break,
            Some(nb) => {
                cur += ((nb + 1024 - b) & 1023) as u32;
            }
        }
    }
    (r, total, far as u64, node)
}

// General fallback (unexpected weights or very large n).
fn heap_dijkstra(off: &[u32], adj: &[u64], src: usize, dist: &mut [u64]) -> (u64, u64, u64, u32) {
    dist.fill(u64::MAX);
    dist[src] = 0;
    let mut h: BinaryHeap<Reverse<(u64, u32)>> = BinaryHeap::new();
    h.push(Reverse((0u64, src as u32)));
    let mut r: u64 = 0;
    let mut total: u64 = 0;
    let mut far: u64 = 0;
    let mut node: u32 = src as u32;
    while let Some(Reverse((d, v))) = h.pop() {
        let vi = v as usize;
        if dist[vi] != d {
            continue;
        }
        r += 1;
        total += d;
        if d > far {
            far = d;
            node = v;
        } else if v < node {
            node = v;
        }
        let s = off[vi] as usize;
        let e = off[vi + 1] as usize;
        for &pe in &adj[s..e] {
            let t = (pe & 0xFFFF_FFFF) as usize;
            let nd = d + (pe >> 32);
            if nd < dist[t] {
                dist[t] = nd;
                h.push(Reverse((nd, t as u32)));
            }
        }
    }
    (r, total, far, node)
}

fn main() {
    let path = std::env::args().nth(1).expect("missing input path");
    let data = std::fs::read(&path).expect("cannot read input");
    let mut p = Parser { d: &data, i: 0 };

    let n = p.next().unwrap_or(0) as usize;
    let m = p.next().unwrap_or(0) as usize;
    let q = p.next().unwrap_or(0) as usize;

    let mut edges: Vec<u32> = Vec::with_capacity(m.saturating_mul(3).min(data.len()));
    let mut off: Vec<u32> = vec![0u32; n + 2];
    let mut small_w = true;

    for _ in 0..m {
        let (Some(u), Some(v), Some(w)) = (p.next(), p.next(), p.next()) else {
            break;
        };
        if u >= n as u64 || v >= n as u64 || u == v {
            continue;
        }
        if w < 1 || w > 1023 {
            small_w = false;
        }
        let w = w.min(u32::MAX as u64) as u32;
        off[u as usize + 1] += 1;
        off[v as usize + 1] += 1;
        edges.push(u as u32);
        edges.push(v as u32);
        edges.push(w);
    }

    for i in 0..n {
        off[i + 1] += off[i];
    }

    let mut sources: Vec<u64> = Vec::with_capacity(q.min(data.len()));
    for _ in 0..q {
        match p.next() {
            Some(s) => sources.push(s),
            None => break,
        }
    }

    let mut out: Vec<u8> = Vec::with_capacity(64 * (sources.len() + 1));

    if small_w && n <= (1usize << 22) {
        let adj: Vec<u32> = build(n, &edges, &off, |v, w| v | (w << 22));
        drop(edges);
        let mut dist: Vec<u32> = vec![u32::MAX; n];
        let mut bucket_store: Vec<Vec<u32>> = (0..1024).map(|_| Vec::new()).collect();
        let buckets: &mut [Vec<u32>; 1024] = (&mut bucket_store[..]).try_into().unwrap();
        let mut cur_vec: Vec<u32> = Vec::new();
        for &s in &sources {
            if s >= n as u64 {
                let _ = writeln!(out, "{} 1 0 0 {}", s, s);
                continue;
            }
            let (r, total, far, node) =
                dial(&off, &adj, s as usize, &mut dist, buckets, &mut cur_vec);
            let _ = writeln!(out, "{} {} {} {} {}", s, r, total, far, node);
        }
    } else {
        let adj: Vec<u64> = build(n, &edges, &off, |v, w| (v as u64) | ((w as u64) << 32));
        drop(edges);
        let mut dist: Vec<u64> = vec![u64::MAX; n];
        for &s in &sources {
            if s >= n as u64 {
                let _ = writeln!(out, "{} 1 0 0 {}", s, s);
                continue;
            }
            let (r, total, far, node) = heap_dijkstra(&off, &adj, s as usize, &mut dist);
            let _ = writeln!(out, "{} {} {} {} {}", s, r, total, far, node);
        }
    }

    let stdout = std::io::stdout();
    let mut lock = stdout.lock();
    let _ = lock.write_all(&out);
    let _ = lock.flush();
}
