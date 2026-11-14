use std::collections::HashMap;
use std::env;
use std::fs;
use std::io::{self, Write};

struct Scanner<'a> {
    data: &'a [u8],
    pos: usize,
}

impl<'a> Scanner<'a> {
    #[inline]
    fn next_u64(&mut self) -> u64 {
        let d = self.data;
        let mut p = self.pos;
        while p < d.len() && d[p] <= b' ' {
            p += 1;
        }
        let mut val: u64 = 0;
        while p < d.len() && d[p] >= b'0' && d[p] <= b'9' {
            val = val * 10 + (d[p] - b'0') as u64;
            p += 1;
        }
        self.pos = p;
        val
    }
}

#[inline]
fn find_next(words: &[u64], idx: usize) -> usize {
    let wi = idx >> 6;
    let bi = idx & 63;
    let w = words[wi] & (u64::MAX << bi);
    if w != 0 {
        return (wi << 6) + w.trailing_zeros() as usize;
    }
    for j in (wi + 1)..words.len() {
        if words[j] != 0 {
            return (j << 6) + words[j].trailing_zeros() as usize;
        }
    }
    for j in 0..words.len() {
        if words[j] != 0 {
            return (j << 6) + words[j].trailing_zeros() as usize;
        }
    }
    unreachable!("find_next called with empty bitmap")
}

fn main() {
    let path = env::args().nth(1).expect("input path argument");
    let data = fs::read(&path).expect("read input");
    if data.is_empty() {
        return;
    }
    let mut sc = Scanner { data: &data, pos: 0 };
    let n = sc.next_u64() as usize;
    let m = sc.next_u64() as usize;
    let q = sc.next_u64() as usize;

    // Build CSR adjacency. Edge packed as (weight << 32) | neighbor.
    let mut deg = vec![0usize; n];
    let mut raw: Vec<(u32, u32, u32)> = Vec::with_capacity(m);
    let mut max_w: u32 = 0;
    for _ in 0..m {
        let u = sc.next_u64() as u32;
        let v = sc.next_u64() as u32;
        let w = sc.next_u64() as u32;
        if u == v {
            continue; // self-loop can never improve a distance
        }
        deg[u as usize] += 1;
        deg[v as usize] += 1;
        if w > max_w {
            max_w = w;
        }
        raw.push((u, v, w));
    }
    let mut sources: Vec<u32> = Vec::with_capacity(q);
    for _ in 0..q {
        sources.push(sc.next_u64() as u32);
    }
    drop(data);

    let mut start = vec![0usize; n + 1];
    for i in 0..n {
        start[i + 1] = start[i] + deg[i];
    }
    let total_e = start[n];
    let mut edges = vec![0u64; total_e];
    let mut cursor = start[..n].to_vec();
    for &(u, v, w) in &raw {
        let wv = ((w as u64) << 32) | v as u64;
        let p = cursor[u as usize];
        edges[p] = wv;
        cursor[u as usize] = p + 1;
        let wu = ((w as u64) << 32) | u as u64;
        let p = cursor[v as usize];
        edges[p] = wu;
        cursor[v as usize] = p + 1;
    }
    drop(raw);
    drop(cursor);
    drop(deg);

    // Dial's algorithm: circular buckets, size max_w + 1, bitmap to skip
    // empty distance levels.
    let bsize: usize = if max_w == 0 { 1 } else { max_w as usize + 1 };
    let mut buckets: Vec<Vec<u32>> = vec![Vec::new(); bsize];
    let mut words = vec![0u64; (bsize + 63) / 64];
    let mut dist = vec![u64::MAX; n];
    let mut stamp = vec![0u32; n];
    let mut mark: u32 = 0;

    let mut out = String::with_capacity(q * 32);
    let mut cache: HashMap<u32, (u64, i64, u64, u32)> = HashMap::new();

    for &s in &sources {
        if let Some(&(r, total, far, node)) = cache.get(&s) {
            out.push_str(&format!("{} {} {} {} {}\n", s, r, total, far, node));
            continue;
        }
        mark += 1;
        dist.fill(u64::MAX);
        dist[s as usize] = 0;
        buckets[0].push(s);
        words[0] |= 1;
        let mut active: usize = 1;

        let mut cur: u64 = 0;
        let mut idx: usize = 0;
        let mut r: u64 = 0;
        let mut total: i64 = 0;
        let mut far: u64 = 0;
        let mut far_node: u32 = s;

        while active > 0 {
            let pos = find_next(&words, idx);
            let delta = if pos >= idx {
                pos - idx
            } else {
                pos + bsize - idx
            };
            cur += delta as u64;
            idx = pos;
            words[idx >> 6] &= !(1u64 << (idx & 63));
            active -= 1;

            let mut stack = std::mem::take(&mut buckets[idx]);
            let mut bucket_min: u32 = u32::MAX;
            for &u in &stack {
                let ui = u as usize;
                if stamp[ui] == mark || dist[ui] != cur {
                    continue;
                }
                stamp[ui] = mark;
                r += 1;
                total += cur as i64;
                if u < bucket_min {
                    bucket_min = u;
                }
                for &e in &edges[start[ui]..start[ui + 1]] {
                    let v = (e & 0xffff_ffff) as usize;
                    if stamp[v] == mark {
                        continue;
                    }
                    let w = (e >> 32) as usize;
                    let nd = cur + w as u64;
                    if nd < dist[v] {
                        dist[v] = nd;
                        let mut nb = idx + w;
                        if nb >= bsize {
                            nb -= bsize;
                        }
                        if buckets[nb].is_empty() {
                            words[nb >> 6] |= 1u64 << (nb & 63);
                            active += 1;
                        }
                        buckets[nb].push(v as u32);
                    }
                }
            }
            if bucket_min != u32::MAX {
                far = cur;
                far_node = bucket_min;
            }
            stack.clear();
            buckets[idx] = stack;
        }

        cache.insert(s, (r, total, far, far_node));
        out.push_str(&format!("{} {} {} {} {}\n", s, r, total, far, far_node));
    }

    let stdout = io::stdout();
    let mut lock = stdout.lock();
    let _ = lock.write_all(out.as_bytes());
}
