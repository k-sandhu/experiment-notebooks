use std::io::Write;

#[inline(always)]
fn read_int(data: &[u8], pos: &mut usize) -> u32 {
    let n = data.len();
    let mut i = *pos;
    while i < n && data[i] <= b' ' {
        i += 1;
    }
    let mut x: u32 = 0;
    while i < n {
        let c = data[i];
        if c < b'0' || c > b'9' {
            break;
        }
        x = x * 10 + (c - b'0') as u32;
        i += 1;
    }
    *pos = i;
    x
}

fn main() {
    let path = std::env::args().nth(1).expect("usage: solution INPUT");
    let data = std::fs::read(&path).expect("cannot read input");

    let mut pos = 0usize;
    let n = read_int(&data, &mut pos) as usize;
    let m = read_int(&data, &mut pos) as usize;
    let q = read_int(&data, &mut pos) as usize;

    let mut eu = Vec::with_capacity(m);
    let mut ev = Vec::with_capacity(m);
    let mut ew = Vec::with_capacity(m);
    let mut deg = vec![0u32; n];

    for _ in 0..m {
        let u = read_int(&data, &mut pos);
        let v = read_int(&data, &mut pos);
        let w = read_int(&data, &mut pos);
        eu.push(u);
        ev.push(v);
        ew.push(w);
        deg[u as usize] += 1;
        deg[v as usize] += 1;
    }

    let mut sources = Vec::with_capacity(q);
    for _ in 0..q {
        sources.push(read_int(&data, &mut pos) as usize);
    }
    drop(data);

    // CSR offsets
    let mut off = vec![0u32; n + 1];
    let mut acc: u32 = 0;
    for i in 0..n {
        off[i] = acc;
        acc += deg[i];
    }
    off[n] = acc;
    drop(deg);

    let total_edges = acc as usize;
    let mut adj_v = vec![0u32; total_edges];
    let mut adj_w = vec![0u32; total_edges];
    let mut cur = off[..n].to_vec();

    for i in 0..m {
        let u = eu[i] as usize;
        let v = ev[i] as usize;
        let w = ew[i];
        let p = cur[u] as usize;
        adj_v[p] = v as u32;
        adj_w[p] = w;
        cur[u] = p as u32 + 1;
        let p = cur[v] as usize;
        adj_v[p] = u as u32;
        adj_w[p] = w;
        cur[v] = p as u32 + 1;
    }
    drop(eu);
    drop(ev);
    drop(ew);
    drop(cur);

    // Dial's algorithm.  All roads are at most maxw long, so every queued
    // distance lies within a window of maxw + 1 values; a circular bucket
    // array of size b > maxw suffices, and a bitset jumps to the next
    // non-empty distance instead of scanning empty ones.
    let mut maxw: u32 = 1;
    for &w in adj_w.iter() {
        if w > maxw {
            maxw = w;
        }
    }
    let mut b: usize = 1;
    while b <= maxw as usize {
        b <<= 1;
    }
    let bm = b - 1;
    let nwords = b.div_ceil(64);

    let mut out = String::with_capacity(q * 48);
    let mut dist = vec![u32::MAX; n];
    let mut buckets: Vec<Vec<u32>> = (0..b).map(|_| Vec::with_capacity(8)).collect();
    let mut bits = vec![0u64; nwords];

    for &s in &sources {
        if !buckets.iter().all(|x| x.is_empty()) {
            for x in buckets.iter_mut() {
                x.clear();
            }
        }
        bits.iter_mut().for_each(|x| *x = 0);
        dist.fill(u32::MAX);
        dist[s] = 0;
        buckets[0].push(s as u32);
        bits[0] = 1;
        let mut cur: u32 = 0;
        let mut pos: usize = 0;
        let mut reach: i64 = 0;
        let mut total: i64 = 0;
        let mut far: u32 = 0;
        let mut node: u32 = s as u32;

        loop {
            let u = match buckets[pos].pop() {
                Some(u) => {
                    if buckets[pos].is_empty() {
                        bits[pos >> 6] &= !(1u64 << (pos & 63));
                    }
                    u as usize
                }
                None => {
                    // Find the next occupied circular position.
                    let q = (pos + 1) & bm;
                    let start_word = q >> 6;
                    let low = q & 63;
                    let mut found: usize = usize::MAX;
                    for k in 0..nwords {
                        let wi = (start_word + k) & (nwords - 1);
                        let w = bits[wi] & (u64::MAX << if k == 0 { low } else { 0 });
                        if w != 0 {
                            found = (wi << 6) | w.trailing_zeros() as usize;
                            break;
                        }
                    }
                    if found == usize::MAX && low != 0 {
                        let w = bits[start_word] & ((1u64 << low) - 1);
                        if w != 0 {
                            found = (start_word << 6) | w.trailing_zeros() as usize;
                        }
                    }
                    if found == usize::MAX {
                        break;
                    }
                    cur += ((found + b - pos) & bm) as u32;
                    pos = found;
                    continue;
                }
            };
            if dist[u] != cur {
                continue;
            }
            reach += 1;
            total += cur as i64;
            if cur > far {
                far = cur;
                node = u as u32;
            } else if cur == far && (u as u32) < node {
                node = u as u32;
            }
            let a = off[u] as usize;
            let b_end = off[u + 1] as usize;
            for e in a..b_end {
                let v = adj_v[e] as usize;
                let nd = cur + adj_w[e];
                if nd < dist[v] {
                    dist[v] = nd;
                    let p2 = nd as usize & bm;
                    buckets[p2].push(v as u32);
                    bits[p2 >> 6] |= 1u64 << (p2 & 63);
                }
            }
        }

        out.push_str(&format!(
            "{} {} {} {} {}\n",
            s, reach, total, far, node
        ));
    }

    let stdout = std::io::stdout();
    let mut w = std::io::BufWriter::new(stdout.lock());
    w.write_all(out.as_bytes()).unwrap();
    w.flush().unwrap();
}
