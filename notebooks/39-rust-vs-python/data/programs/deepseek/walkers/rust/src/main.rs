use std::io::{self, Read, Write};

const GAMMA: u64 = 0x9E37_79B9_7F4A_7C15;
const C1: u64 = 0xBF58_476D_1CE4_E5B9;
const C2: u64 = 0x94D0_49BB_1331_11EB;

#[derive(Clone, Copy)]
struct WalkResult {
    x: i64,
    y: i64,
    bumps: u64,
    returns: u64,
}

#[inline]
fn run_walker(j: u64, steps: u64, bound: i64, seed: u64) -> WalkResult {
    let mut state = seed.wrapping_add(j);
    let mut x: i64 = 0;
    let mut y: i64 = 0;
    let mut bumps: u64 = 0;
    let mut returns: u64 = 0;
    let mut remaining = steps;

    while remaining != 0 {
        // Unroll by 4 to let the CPU overlap the independent multiply chains.
        let n = if remaining >= 4 { 4 } else { remaining };
        remaining -= n;
        for _ in 0..n {
            state = state.wrapping_add(GAMMA);
            let mut z = state;
            z = (z ^ (z >> 30)).wrapping_mul(C1);
            z = (z ^ (z >> 27)).wrapping_mul(C2);
            // The final xorshift with >> 31 only touches bits 0..32, so the
            // top two bits of the returned value are the top two bits of z.
            match z >> 62 {
                0 => {
                    if x < bound {
                        x += 1;
                        if x == 0 && y == 0 {
                            returns += 1;
                        }
                    } else {
                        bumps += 1;
                    }
                }
                1 => {
                    if x > -bound {
                        x -= 1;
                        if x == 0 && y == 0 {
                            returns += 1;
                        }
                    } else {
                        bumps += 1;
                    }
                }
                2 => {
                    if y < bound {
                        y += 1;
                        if x == 0 && y == 0 {
                            returns += 1;
                        }
                    } else {
                        bumps += 1;
                    }
                }
                _ => {
                    if y > -bound {
                        y -= 1;
                        if x == 0 && y == 0 {
                            returns += 1;
                        }
                    } else {
                        bumps += 1;
                    }
                }
            }
        }
    }

    WalkResult {
        x,
        y,
        bumps,
        returns,
    }
}

fn main() {
    let mut args = std::env::args_os().skip(1);
    let path = match args.next() {
        Some(p) => p,
        None => {
            eprintln!("usage: solution INPUT_PATH WORKERS");
            std::process::exit(1);
        }
    };
    let workers: usize = args
        .next()
        .and_then(|s| s.to_string_lossy().parse::<usize>().ok())
        .unwrap_or(1)
        .clamp(1, 32);

    let mut data = String::new();
    {
        let mut f = std::fs::File::open(&path).expect("open input");
        f.read_to_string(&mut data).expect("read input");
    }
    let mut it = data.split_ascii_whitespace();
    let walkers: u64 = it.next().expect("J").parse().expect("J");
    let steps: u64 = it.next().expect("L").parse().expect("L");
    let bound: i64 = it.next().expect("B").parse().expect("B");
    let seed: u64 = it.next().expect("SEED").parse().expect("SEED");

    let nthread = workers.min(walkers.max(1) as usize).max(1);
    let mut results: Vec<WalkResult> = vec![
        WalkResult {
            x: 0,
            y: 0,
            bumps: 0,
            returns: 0
        };
        walkers as usize
    ];

    std::thread::scope(|scope| {
        let mut handles = Vec::with_capacity(nthread);
        for w in 0..nthread {
            handles.push(scope.spawn(move || {
                let mut out: Vec<(usize, WalkResult)> = Vec::new();
                let mut j = w as u64;
                while j < walkers {
                    out.push((j as usize, run_walker(j, steps, bound, seed)));
                    j += nthread as u64;
                }
                out
            }));
        }
        for h in handles {
            for (idx, r) in h.join().expect("worker thread panicked") {
                results[idx] = r;
            }
        }
    });

    let mut spread: i64 = 0;
    let mut bumps: u64 = 0;
    let mut returns: u64 = 0;
    let mut best_index: usize = 0;
    let mut best_dist: i64 = -1;
    for (j, r) in results.iter().enumerate() {
        spread += r.x * r.x + r.y * r.y;
        bumps += r.bumps;
        returns += r.returns;
        let d = r.x.abs() + r.y.abs();
        if d > best_dist {
            best_dist = d;
            best_index = j;
        }
    }
    if results.is_empty() {
        best_dist = 0;
    }

    let mut out = String::with_capacity(96);
    out.push_str(&format!(
        "spread {}\nbumps {}\nreturns {}\nfarthest {} {}\n",
        spread, bumps, returns, best_index, best_dist
    ));
    let stdout = io::stdout();
    let mut lock = stdout.lock();
    lock.write_all(out.as_bytes()).unwrap();
}
