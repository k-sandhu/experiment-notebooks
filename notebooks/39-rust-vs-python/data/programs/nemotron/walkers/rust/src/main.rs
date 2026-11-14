use rayon::prelude::*;

const C: u64 = 0x9E3779B97F4A7C15;
const M1: u64 = 0xBF58476D1CE4E5B9;
const M2: u64 = 0x94D049BB133111EB;

struct Agg {
    spread: i64,
    bumps: i64,
    returns: i64,
    best_dist: i64,
    best_j: u64,
}

fn walk(mut state: u64, steps: u64, b: i64) -> (i64, i64, i64, i64) {
    let mut x: i64 = 0;
    let mut y: i64 = 0;
    let mut bumps: i64 = 0;
    let mut rets: i64 = 0;
    let neg_b = -b;
    for _ in 0..steps {
        state = state.wrapping_add(C);
        let mut z = state;
        z ^= z >> 30;
        z = z.wrapping_mul(M1);
        z ^= z >> 27;
        z = z.wrapping_mul(M2);
        let r = z ^ (z >> 31);
        let d = (r >> 62) as i64;
        let mut nx = x;
        let mut ny = y;
        if d == 0 {
            nx += 1;
        } else if d == 1 {
            nx -= 1;
        } else if d == 2 {
            ny += 1;
        } else {
            ny -= 1;
        }
        if nx >= neg_b && nx <= b && ny >= neg_b && ny <= b {
            x = nx;
            y = ny;
            if x == 0 && y == 0 {
                rets += 1;
            }
        } else {
            bumps += 1;
        }
    }
    (x * x + y * y, bumps, rets, x.abs() + y.abs())
}

fn process_range(start: u64, end: u64, seed: u64, steps: u64, b: i64) -> Agg {
    let mut spread = 0i64;
    let mut bumps = 0i64;
    let mut rets = 0i64;
    let mut best_dist = -1i64;
    let mut best_j: u64 = 0;
    let mut j = start;
    while j < end {
        let state = seed.wrapping_add(j);
        let (s, bu, re, dist) = walk(state, steps, b);
        spread += s;
        bumps += bu;
        rets += re;
        if dist > best_dist {
            best_dist = dist;
            best_j = j;
        }
        j += 1;
    }
    Agg {
        spread,
        bumps,
        returns: rets,
        best_dist,
        best_j,
    }
}

fn combine(a: Agg, b: Agg) -> Agg {
    let mut r = a;
    r.spread += b.spread;
    r.bumps += b.bumps;
    r.returns += b.returns;
    if b.best_dist > r.best_dist || (b.best_dist == r.best_dist && b.best_j < r.best_j) {
        r.best_dist = b.best_dist;
        r.best_j = b.best_j;
    }
    r
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let path = &args[1];
    let workers: usize = args[2].parse().expect("WORKERS must be an integer");

    let contents = std::fs::read_to_string(path).expect("unable to read input file");
    let mut tokens = contents.split_whitespace();
    let j: u64 = tokens.next().expect("missing J").parse().expect("invalid J");
    let l: u64 = tokens.next().expect("missing L").parse().expect("invalid L");
    let b: i64 = tokens.next().expect("missing B").parse().expect("invalid B");
    let seed: u64 = tokens.next().expect("missing SEED").parse().expect("invalid SEED");

    let nworkers = workers.min(j as usize);
    let mut ranges = Vec::with_capacity(nworkers);
    if nworkers > 0 {
        let base = (j / nworkers as u64) as usize;
        let rem = (j % nworkers as u64) as usize;
        let mut start: usize = 0;
        for w in 0..nworkers {
            let size = base + if w < rem { 1 } else { 0 };
            ranges.push((start as u64, (start + size) as u64));
            start += size;
        }
    }

    let agg = if ranges.is_empty() {
        Agg {
            spread: 0,
            bumps: 0,
            returns: 0,
            best_dist: 0,
            best_j: 0,
        }
    } else {
        ranges
            .into_par_iter()
            .map(|(s, e)| process_range(s, e, seed, l, b))
            .reduce(
                || Agg {
                    spread: 0,
                    bumps: 0,
                    returns: 0,
                    best_dist: -1,
                    best_j: 0,
                },
                combine,
            )
    };

    println!("spread {}", agg.spread);
    println!("bumps {}", agg.bumps);
    println!("returns {}", agg.returns);
    println!("farthest {} {}", agg.best_j, agg.best_dist);
}
