use std::env;
use std::fs;

#[derive(Clone, Copy)]
struct Partial {
    spread: i64,
    bumps: i64,
    returns: i64,
    best_j: usize,
    best_d: i64,
}

impl Partial {
    fn new() -> Self {
        Self { spread: 0, bumps: 0, returns: 0, best_j: 0, best_d: -1 }
    }
}

fn run_range_wide(start: usize, end: usize, l: u64, b: i64, seed: u64) -> Partial {
    let mut p = Partial::new();
    for j in start..end {
        let mut state = seed.wrapping_add(j as u64);
        let (mut x, mut y): (i64, i64) = (0, 0);
        let (mut bumps, mut returns): (i64, i64) = (0, 0);
        let mut i: u64 = 0;
        while i < l {
            i += 1;
            state = state.wrapping_add(0x9E3779B97F4A7C15u64);
            let mut z = state;
            z = (z ^ (z >> 30)).wrapping_mul(0xBF58476D1CE4E5B9u64);
            z = (z ^ (z >> 27)).wrapping_mul(0x94D049BB133111EB_u64);
            match z >> 62 {
                0 => if x == b { bumps += 1; } else { x += 1; if x == 0 && y == 0 { returns += 1; } },
                1 => if x == -b { bumps += 1; } else { x -= 1; if x == 0 && y == 0 { returns += 1; } },
                2 => if y == b { bumps += 1; } else { y += 1; if x == 0 && y == 0 { returns += 1; } },
                _ => if y == -b { bumps += 1; } else { y -= 1; if x == 0 && y == 0 { returns += 1; } },
            }
        }
        p.spread += x * x + y * y;
        p.bumps += bumps;
        p.returns += returns;
        let d = x.abs() + y.abs();
        if d > p.best_d { p.best_d = d; p.best_j = j; }
    }
    p
}

#[inline(always)]
fn run_range(start: usize, end: usize, l: u64, b: i64, seed: u64) -> Partial {
    if b > i32::MAX as i64 || b < i32::MIN as i64 {
        return run_range_wide(start, end, l, b, seed);
    }
    let mut p = Partial::new();
    let bi = b as i32;
    let nb = -bi;
    for j in start..end {
        let mut state = seed.wrapping_add(j as u64);
        let mut x: i32 = 0;
        let mut y: i32 = 0;
        let mut bumps: i64 = 0;
        let mut returns: i64 = 0;
        let mut i: u64 = 0;
        while i < l {
            i += 1;
            state = state.wrapping_add(0x9E3779B97F4A7C15u64);
            let mut z = state;
            z = (z ^ (z >> 30)).wrapping_mul(0xBF58476D1CE4E5B9u64);
            z = (z ^ (z >> 27)).wrapping_mul(0x94D049BB133111EB_u64);
            // Top two bits of (z ^ (z >> 31)) equal top two bits of z.
            match z >> 62 {
                0 => {
                    if x == bi {
                        bumps += 1;
                    } else {
                        x += 1;
                        if x == 0 && y == 0 { returns += 1; }
                    }
                }
                1 => {
                    if x == nb {
                        bumps += 1;
                    } else {
                        x -= 1;
                        if x == 0 && y == 0 { returns += 1; }
                    }
                }
                2 => {
                    if y == bi {
                        bumps += 1;
                    } else {
                        y += 1;
                        if x == 0 && y == 0 { returns += 1; }
                    }
                }
                _ => {
                    if y == nb {
                        bumps += 1;
                    } else {
                        y -= 1;
                        if x == 0 && y == 0 { returns += 1; }
                    }
                }
            }
        }
        let xi = x as i64;
        let yi = y as i64;
        p.spread += xi * xi + yi * yi;
        p.bumps += bumps;
        p.returns += returns;
        let d = xi.abs() + yi.abs();
        if d > p.best_d {
            p.best_d = d;
            p.best_j = j;
        }
    }
    let _ = b;
    p
}

fn main() {
    let mut args = env::args();
    let _ = args.next();
    let input = args.next().expect("INPUT_PATH");
    let workers: usize = args
        .next()
        .map(|s| s.parse::<usize>().unwrap_or(1))
        .unwrap_or(1)
        .clamp(1, 32);
    let data = fs::read(&input).expect("read input");
    let text = std::str::from_utf8(&data).expect("utf8");
    let mut it = text.split_ascii_whitespace();
    let j_total: usize = it.next().unwrap_or("0").parse().unwrap_or(0);
    let l: u64 = it.next().unwrap_or("0").parse().unwrap_or(0);
    let b: i64 = it.next().unwrap_or("0").parse().unwrap_or(0);
    let seed: u64 = it.next().unwrap_or("0").parse().unwrap_or(0);

    let mut result = Partial::new();
    if j_total == 0 {
        result.best_d = 0;
        result.best_j = 0;
    } else if workers <= 1 || j_total == 1 {
        result = run_range(0, j_total, l, b, seed);
        if result.best_d < 0 { result.best_d = 0; }
    } else {
        let w = workers.min(j_total);
        // Contiguous chunks, merged in order -> deterministic tie-break.
        let chunk = (j_total + w - 1) / w;
        let partials: Vec<Partial> = std::thread::scope(|s| {
            let mut handles = Vec::with_capacity(w);
            let mut start = 0usize;
            while start < j_total {
                let end = (start + chunk).min(j_total);
                handles.push(s.spawn(move || run_range(start, end, l, b, seed)));
                start = end;
            }
            handles
                .into_iter()
                .map(|h| h.join().expect("worker panicked"))
                .collect()
        });
        for part in &partials {
            // Merge manually to keep smallest-j tie handling exact.
            result.spread += part.spread;
            result.bumps += part.bumps;
            result.returns += part.returns;
            if part.best_d > result.best_d {
                result.best_d = part.best_d;
                result.best_j = part.best_j;
            }
        }
        if result.best_d < 0 { result.best_d = 0; }
    }
    print!(
        "spread {}\nbumps {}\nreturns {}\nfarthest {} {}\n",
        result.spread, result.bumps, result.returns, result.best_j, result.best_d
    );
}
