use std::collections::BinaryHeap;
use std::env;
use std::fs;
use std::io::Write;
use std::process::exit;

const INF: u64 = u64::MAX;

// Dijkstra with a packed binary heap. Edge weights are 1..=1000 and N <= 2^19,
// so distances fit easily; the heap stores (dist << 20) | node as a single u64
// pushed complemented into a max-heap, which makes it a min-heap on (dist, node).
// Distances are bounded by N * 1000 < 2^29, so the packed key fits in 49 bits.

fn main() {
    let path = env::args().nth(1).unwrap_or_else(|| {
        eprintln!("usage: solution INPUT_PATH");
        exit(2);
    });
    let data = fs::read(&path).unwrap_or_else(|e| {
        eprintln!("cannot read {path}: {e}");
        exit(2);
    });

    // Fast integer scan over the raw bytes.
    let mut pos = 0usize;
    let n = next_u32(&data, &mut pos) as usize;
    let m = next_u32(&data, &mut pos) as usize;
    let q = next_u32(&data, &mut pos) as usize;

    // Build a CSR adjacency (both directions) via counting sort.
    let mut deg = vec![0u32; n + 1];
    let mut eu = vec![0u32; m];
    let mut ev = vec![0u32; m];
    let mut ew = vec![0u32; m];
    for i in 0..m {
        let u = next_u32(&data, &mut pos);
        let v = next_u32(&data, &mut pos);
        let w = next_u32(&data, &mut pos);
        eu[i] = u;
        ev[i] = v;
        ew[i] = w;
        deg[u as usize + 1] += 1;
        deg[v as usize + 1] += 1;
    }
    for i in 0..n {
        deg[i + 1] += deg[i];
    }
    let indptr = deg; // now a prefix-sum array of length n+1
    let mut cur = indptr.clone();
    let mut targets = vec![0u32; 2 * m];
    let mut weights = vec![0u32; 2 * m];
    for i in 0..m {
        let (u, v, w) = (eu[i], ev[i], ew[i]);
        targets[cur[u as usize] as usize] = v;
        weights[cur[u as usize] as usize] = w;
        cur[u as usize] += 1;
        targets[cur[v as usize] as usize] = u;
        weights[cur[v as usize] as usize] = w;
        cur[v as usize] += 1;
    }
    drop(eu);
    drop(ev);
    drop(ew);

    let mut dist = vec![INF; n];
    let mut heap: BinaryHeap<u64> = BinaryHeap::with_capacity(n);
    let mut out = String::with_capacity(q * 48);

    for _ in 0..q {
        let s = next_u32(&data, &mut pos) as usize;
        out.push_str(&run_source(
            s,
            &indptr,
            &targets,
            &weights,
            &mut dist,
            &mut heap,
        ));
        out.push('\n');
    }

    let stdout = std::io::stdout();
    let mut lock = stdout.lock();
    let _ = lock.write_all(out.as_bytes());
    let _ = lock.flush();
}

fn run_source(
    s: usize,
    indptr: &[u32],
    targets: &[u32],
    weights: &[u32],
    dist: &mut [u64],
    heap: &mut BinaryHeap<u64>,
) -> String {
    for d in dist.iter_mut() {
        *d = INF;
    }
    heap.clear();
    dist[s] = 0;
    heap.push(!(s as u64)); // !( (0 << 20) | s )

    while let Some(k) = heap.pop() {
        let key = !k;
        let v = (key & 0xF_FFFF) as usize;
        let d = key >> 20;
        if d != dist[v] {
            continue; // stale entry
        }
        let mut i = indptr[v] as usize;
        let end = indptr[v + 1] as usize;
        while i < end {
            let u = targets[i] as usize;
            let nd = d + weights[i] as u64;
            if nd < dist[u] {
                dist[u] = nd;
                heap.push(!(nd << 20 | u as u64));
            }
            i += 1;
        }
    }

    // Aggregate: R, TOTAL, FAR, and the smallest node with dist == FAR.
    let mut total: u64 = 0;
    let mut reached: u64 = 0;
    let mut far: u64 = 0;
    for &d in dist.iter() {
        if d != INF {
            reached += 1;
            total += d;
            if d > far {
                far = d;
            }
        }
    }
    let far_node = dist
        .iter()
        .position(|&d| d == far)
        .unwrap_or(s as usize);

    format!("{s} {reached} {total} {far} {far_node}")
}

#[inline]
fn next_u32(data: &[u8], pos: &mut usize) -> u32 {
    // Skip any non-digit separators.
    while *pos < data.len() && (data[*pos] < b'0' || data[*pos] > b'9') {
        *pos += 1;
    }
    let start = *pos;
    while *pos < data.len() && data[*pos].is_ascii_digit() {
        *pos += 1;
    }
    let mut val: u32 = 0;
    for &b in &data[start..*pos] {
        val = val * 10 + (b - b'0') as u32;
    }
    val
}
