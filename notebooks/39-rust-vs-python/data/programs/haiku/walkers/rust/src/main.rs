use std::env;
use std::fs;
use std::process;
use std::thread;

const GAMMA: u64 = 0x9E3779B97F4A7C15;

// Step deltas indexed by d = r >> 62: 0 = x+1, 1 = x-1, 2 = y+1, 3 = y-1.
const DX: [i64; 4] = [1, -1, 0, 0];
const DY: [i64; 4] = [0, 0, 1, -1];

#[derive(Clone, Copy)]
struct Part {
    spread: i64,
    bumps: u64,
    returns: u64,
    best_dist: i64,
    best_walker: u64,
}

impl Part {
    fn new() -> Self {
        Part { spread: 0, bumps: 0, returns: 0, best_dist: -1, best_walker: 0 }
    }
}

fn walk_range(lo: u64, hi: u64, steps: u64, bound: i64, seed: u64) -> Part {
    let mut part = Part::new();
    for walker in lo..hi {
        let mut state = seed.wrapping_add(walker);
        let (mut x, mut y) = (0i64, 0i64);
        let mut bumps = 0u64;
        let mut returns = 0u64;
        for _ in 0..steps {
            state = state.wrapping_add(GAMMA);
            let mut z = state;
            z = (z ^ (z >> 30)).wrapping_mul(0xBF58476D1CE4E5B9);
            z = (z ^ (z >> 27)).wrapping_mul(0x94D049BB133111EB);
            let d = ((z ^ (z >> 31)) >> 62) as usize;

            // Compute the move unconditionally and select, so the walk has no unpredictable branches.
            let nx = x + DX[d];
            let ny = y + DY[d];
            let inside = (nx.abs() <= bound) & (ny.abs() <= bound);
            x = if inside { nx } else { x };
            y = if inside { ny } else { y };
            bumps += (!inside) as u64;
            returns += (inside & (nx == 0) & (ny == 0)) as u64;
        }
        let dist = x.abs() + y.abs();
        part.spread += x * x + y * y;
        part.bumps += bumps;
        part.returns += returns;
        // Walkers are visited in increasing order, so a strict comparison keeps the smallest number on a tie.
        if dist > part.best_dist {
            part.best_dist = dist;
            part.best_walker = walker;
        }
    }
    part
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() != 3 {
        eprintln!("usage: {} INPUT_PATH WORKERS", args[0]);
        process::exit(2);
    }
    let text = fs::read_to_string(&args[1]).unwrap_or_else(|e| {
        eprintln!("cannot read {}: {}", args[1], e);
        process::exit(1);
    });
    let mut fields = text.split_ascii_whitespace();
    let mut next = || fields.next().expect("missing field");
    let walkers: u64 = next().parse().expect("bad J");
    let steps: u64 = next().parse().expect("bad L");
    let bound: i64 = next().parse().expect("bad B");
    let seed: u64 = next().parse().expect("bad SEED");
    let workers: u64 = args[2].parse::<u64>().expect("bad WORKERS").clamp(1, walkers.max(1));

    let parts: Vec<Part> = thread::scope(|scope| {
        let handles: Vec<_> = (0..workers)
            .map(|w| {
                let lo = walkers * w / workers;
                let hi = walkers * (w + 1) / workers;
                scope.spawn(move || walk_range(lo, hi, steps, bound, seed))
            })
            .collect();
        handles.into_iter().map(|h| h.join().expect("worker panicked")).collect()
    });

    let mut total = Part::new();
    for p in &parts {
        total.spread += p.spread;
        total.bumps += p.bumps;
        total.returns += p.returns;
        if p.best_dist > total.best_dist
            || (p.best_dist == total.best_dist && p.best_walker < total.best_walker)
        {
            total.best_dist = p.best_dist;
            total.best_walker = p.best_walker;
        }
    }
    if total.best_dist < 0 {
        total.best_dist = 0;
    }

    println!("spread {}", total.spread);
    println!("bumps {}", total.bumps);
    println!("returns {}", total.returns);
    println!("farthest {} {}", total.best_walker, total.best_dist);
}
