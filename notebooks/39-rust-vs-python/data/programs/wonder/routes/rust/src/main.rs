use std::env;
use std::fmt::Write as _;
use std::fs;
use std::io::{self, Write as _};
use std::process::ExitCode;

fn main() -> ExitCode {
    let Some(path) = env::args_os().nth(1) else {
        return ExitCode::from(2);
    };
    let data = match fs::read(&path) {
        Ok(d) => d,
        Err(_) => return ExitCode::from(1),
    };
    if data.is_empty() {
        return ExitCode::SUCCESS;
    }

    // Fast integer scan: input contains only non-negative integers and whitespace.
    let mut ints: Vec<u32> = Vec::with_capacity(data.len() / 3 + 16);
    let bytes = &data[..];
    let mut i = 0usize;
    let len = bytes.len();
    while i < len {
        while i < len && bytes[i] <= b' ' {
            i += 1;
        }
        if i >= len {
            break;
        }
        let mut val: u32 = 0;
        while i < len && bytes[i] > b' ' {
            val = val.wrapping_mul(10).wrapping_add((bytes[i] - b'0') as u32);
            i += 1;
        }
        ints.push(val);
    }
    if ints.len() < 3 {
        return ExitCode::SUCCESS;
    }
    let n = ints[0] as usize;
    let m = ints[1] as usize;
    let q = ints[2] as usize;
    let edge_base = 3usize;
    let src_base = edge_base + 3 * m;
    if ints.len() < src_base + q {
        // Malformed input; nothing reliable to do.
        return ExitCode::SUCCESS;
    }

    // Build CSR adjacency, skipping self-loops (they can never shorten a path).
    let mut deg: Vec<u32> = vec![0; n];
    let mut maxw: u32 = 0;
    for e in 0..m {
        let o = edge_base + 3 * e;
        let u = ints[o] as usize;
        let v = ints[o + 1] as usize;
        let w = ints[o + 2];
        if u == v || u >= n || v >= n {
            continue;
        }
        if w > maxw {
            maxw = w;
        }
        deg[u] += 1;
        deg[v] += 1;
    }
    let mut start: Vec<u32> = Vec::with_capacity(n + 1);
    start.push(0);
    for d in &deg {
        let next = start[start.len() - 1] + *d;
        start.push(next);
    }
    let total_edges = *start.last().unwrap() as usize;
    let mut nbr: Vec<u32> = vec![0; total_edges];
    let mut wt: Vec<u16> = vec![0; total_edges];
    let mut cursor: Vec<u32> = start[..n].to_vec();
    for e in 0..m {
        let o = edge_base + 3 * e;
        let u = ints[o] as usize;
        let v = ints[o + 1] as usize;
        let w = ints[o + 2];
        if u == v || u >= n || v >= n {
            continue;
        }
        let pu = cursor[u] as usize;
        nbr[pu] = v as u32;
        wt[pu] = w as u16;
        cursor[u] += 1;
        let pv = cursor[v] as usize;
        nbr[pv] = u as u32;
        wt[pv] = w as u16;
        cursor[v] += 1;
    }
    let sources: Vec<u32> = ints[src_base..src_base + q].to_vec();
    drop(ints);
    drop(data);

    let b_size: usize = (maxw as usize) + 1; // Dial bucket count; >= max edge weight + 1
    let inf: u64 = u64::MAX;

    let mut out = String::new();

    // Reused scratch.
    let mut dist: Vec<u64> = vec![inf; n];
    let mut visited: Vec<u8> = vec![0; n];

    for &s_u32 in &sources {
        let s = s_u32 as usize;
        if s >= n {
            let _ = writeln!(out, "{} 0 0 0 {}", s_u32, s_u32);
            continue;
        }
        for d in dist.iter_mut() {
            *d = inf;
        }
        visited.fill(0);

        let mut buckets: Vec<Vec<u32>> = vec![Vec::new(); b_size];
        let mut mask: [u64; 16] = [0; 16];
        dist[s] = 0;
        buckets[0].push(s_u32);
        mask[0] = 1;
        let mut nonempty: usize = 1;

        let mut idx: usize = 0;
        let mut cur: u64 = 0;
        let mut reached: u64 = 0;
        let mut total: u64 = 0;
        let mut far: u64 = 0;
        let mut far_node: u32 = s_u32;

        while nonempty > 0 {
            if buckets[idx].is_empty() {
                // Find next set bit in mask, at or after idx, wrapping around.
                let mut found: Option<usize> = None;
                // Search from idx to b_size-1.
                {
                    let mut pos = idx;
                    while pos < b_size {
                        let word = mask[pos >> 6];
                        let bit = pos & 63;
                        let masked = word & (!0u64 << bit);
                        if masked != 0 {
                            found = Some((pos & !63) + masked.trailing_zeros() as usize);
                            break;
                        }
                        pos = (pos & !63) + 64;
                    }
                }
                if found.is_none() {
                    // Wrap to the first set bit.
                    let mut pos = 0usize;
                    while pos < b_size {
                        let word = mask[pos >> 6];
                        if word != 0 {
                            found = Some((pos & !63) + word.trailing_zeros() as usize);
                            break;
                        }
                        pos += 64;
                    }
                }
                let nxt = match found {
                    Some(p) if p < b_size => p,
                    Some(p) => {
                        // Set bit beyond b_size should not happen; clamp search again.
                        let _ = p;
                        break;
                    }
                    None => break,
                };
                let delta = if nxt >= idx {
                    nxt - idx
                } else {
                    b_size - idx + nxt
                };
                cur += delta as u64;
                idx = nxt;
            }

            // Drain bucket idx. Pushes never target idx (weights are >= 1 and < b_size).
            while let Some(v_u32) = buckets[idx].pop() {
                let v = v_u32 as usize;
                if visited[v] != 0 {
                    continue;
                }
                visited[v] = 1;
                reached += 1;
                total += cur;
                if cur > far {
                    far = cur;
                    far_node = v_u32;
                } else if cur == far && v_u32 < far_node {
                    far_node = v_u32;
                }
                let lo = start[v] as usize;
                let hi = start[v + 1] as usize;
                for p in lo..hi {
                    let to_u32 = nbr[p];
                    let to = to_u32 as usize;
                    if visited[to] != 0 {
                        continue;
                    }
                    let w = wt[p] as u64;
                    let nd = cur + w;
                    if nd < dist[to] {
                        dist[to] = nd;
                        let mut b = idx + (w as usize);
                        if b >= b_size {
                            b -= b_size;
                        }
                        if buckets[b].is_empty() {
                            mask[b >> 6] |= 1u64 << (b & 63);
                            nonempty += 1;
                        }
                        buckets[b].push(to_u32);
                    }
                }
            }
            mask[idx >> 6] &= !(1u64 << (idx & 63));
            nonempty -= 1;
        }

        let _ = writeln!(out, "{} {} {} {} {}", s_u32, reached, total, far, far_node);
    }

    let stdout = io::stdout();
    let mut lock = stdout.lock();
    let _ = lock.write_all(out.as_bytes());
    ExitCode::SUCCESS
}
