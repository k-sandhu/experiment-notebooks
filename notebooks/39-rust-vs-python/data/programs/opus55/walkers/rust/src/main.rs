use rayon::prelude::*;
use std::io::Write;

const GOLDEN: u64 = 0x9E3779B97F4A7C15;
const MIX1: u64 = 0xBF58476D1CE4E5B9;
const MIX2: u64 = 0x94D049BB133111EB;

#[derive(Clone, Copy, Default)]
struct Walk {
    x: i32,
    y: i32,
    bumps: u64,
    returns: u64,
}

/// Top two bits of the SplitMix64 output for the given (already advanced) state.
/// The final `z ^ (z >> 31)` does not touch the top 31 bits, so it is skipped.
#[inline(always)]
fn dir(state: u64) -> usize {
    let mut z = state;
    z = (z ^ (z >> 30)).wrapping_mul(MIX1);
    z = (z ^ (z >> 27)).wrapping_mul(MIX2);
    (z >> 62) as usize
}

const DX: [i32; 4] = [1, -1, 0, 0];
const DY: [i32; 4] = [0, 0, 1, -1];

fn walk(seed: u64, steps: u64, b: i32) -> Walk {
    let mut state = seed;
    let (mut x, mut y) = (0i32, 0i32);
    let mut bumps = 0u64;
    let mut returns = 0u64;
    let span = (2 * b) as u32;
    for _ in 0..steps {
        state = state.wrapping_add(GOLDEN);
        let d = dir(state);
        let nx = x + DX[d];
        let ny = y + DY[d];
        // |nx| <= b and |ny| <= b, as one unsigned range check per axis
        let inside = ((nx + b) as u32 <= span) & ((ny + b) as u32 <= span);
        x = if inside { nx } else { x };
        y = if inside { ny } else { y };
        bumps += (!inside) as u64;
        // landing on the origin implies the move was inside the box (b >= 1)
        returns += ((nx | ny) == 0) as u64;
    }
    Walk { x, y, bumps, returns }
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let text = std::fs::read_to_string(&args[1]).expect("cannot read input");
    let workers: usize = args
        .get(2)
        .and_then(|s| s.trim().parse().ok())
        .unwrap_or(1)
        .max(1);
    let mut it = text.split_ascii_whitespace();
    let j: u64 = it.next().unwrap().parse().unwrap();
    let l: u64 = it.next().unwrap().parse().unwrap();
    let b: i64 = it.next().unwrap().parse().unwrap();
    let seed: u64 = it.next().unwrap().parse().unwrap();
    // A walker can never get farther than L from the origin, so a larger box behaves like this one.
    let b = b.min(l as i64 + 1).min(i32::MAX as i64 / 4) as i32;

    let pool = rayon::ThreadPoolBuilder::new()
        .num_threads(workers.min(j.max(1) as usize))
        .build()
        .unwrap();
    let results: Vec<Walk> = pool.install(|| {
        (0..j as usize)
            .into_par_iter()
            .with_max_len(1)
            .map(|w| walk(seed.wrapping_add(w as u64), l, b))
            .collect()
    });

    let mut spread: i64 = 0;
    let mut bumps: u64 = 0;
    let mut returns: u64 = 0;
    let mut best_j: u64 = 0;
    let mut best_d: i64 = -1;
    for (w, r) in results.iter().enumerate() {
        let (x, y) = (r.x as i64, r.y as i64);
        spread += x * x + y * y;
        bumps += r.bumps;
        returns += r.returns;
        let d = x.abs() + y.abs();
        if d > best_d {
            best_d = d;
            best_j = w as u64;
        }
    }
    if j == 0 {
        best_d = 0;
    }
    let mut out = std::io::stdout().lock();
    writeln!(
        out,
        "spread {}\nbumps {}\nreturns {}\nfarthest {} {}",
        spread, bumps, returns, best_j, best_d
    )
    .unwrap();
}
