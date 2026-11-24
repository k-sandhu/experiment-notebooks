use std::cmp::Reverse;
use std::collections::{BinaryHeap, HashMap};
use std::fmt::Write as _;
use std::fs;

fn number(input: &[u8], pos: &mut usize) -> usize {
    while *pos < input.len() && input[*pos].is_ascii_whitespace() { *pos += 1; }
    let mut value = 0;
    while *pos < input.len() && input[*pos].is_ascii_digit() {
        value = value * 10 + (input[*pos] - b'0') as usize;
        *pos += 1;
    }
    value
}

fn main() {
    let input = fs::read(std::env::args_os().nth(1).expect("input path")).expect("read input");
    let mut p = 0;
    let n = number(&input, &mut p);
    let m = number(&input, &mut p);
    let q = number(&input, &mut p);
    let mut edges = Vec::with_capacity(m);
    let mut offsets = vec![0usize; n + 1];
    for _ in 0..m {
        let u = number(&input, &mut p);
        let v = number(&input, &mut p);
        let w = number(&input, &mut p) as u64;
        edges.push((u, v, w));
        offsets[u + 1] += 1;
        offsets[v + 1] += 1;
    }
    for i in 1..=n { offsets[i] += offsets[i - 1]; }
    let mut next = offsets[..n].to_vec();
    let mut adj = vec![(0usize, 0u64); 2 * m];
    for (u, v, w) in edges {
        adj[next[u]] = (v, w); next[u] += 1;
        adj[next[v]] = (u, w); next[v] += 1;
    }
    drop(next);
    let mut output = String::new();
    let mut results = HashMap::new();
    let mut dist = vec![u64::MAX; n];
    let mut heap = BinaryHeap::new();
    for _ in 0..q {
        let source = number(&input, &mut p);
        let result = results.entry(source).or_insert_with(|| {
            dist.fill(u64::MAX);
            dist[source] = 0;
            heap.clear();
            heap.push(Reverse((0u64, source)));
            let (mut count, mut total, mut far, mut far_node) = (0u64, 0u64, 0u64, source);
            while let Some(Reverse((d, u))) = heap.pop() {
                if d != dist[u] { continue; }
                count += 1;
                total += d;
                if d > far || (d == far && u < far_node) { far = d; far_node = u; }
                for &(v, w) in &adj[offsets[u]..offsets[u + 1]] {
                    let nd = d + w;
                    if nd < dist[v] {
                        dist[v] = nd;
                        heap.push(Reverse((nd, v)));
                    }
                }
            }
            (count, total, far, far_node)
        });
        writeln!(output, "{} {} {} {} {}", source, result.0, result.1, result.2, result.3).unwrap();
    }
    print!("{output}");
}
