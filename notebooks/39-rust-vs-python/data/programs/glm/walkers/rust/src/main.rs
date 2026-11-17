use rayon::iter::IntoParallelIterator;
use rayon::iter::ParallelIterator;
use std::env;
use std::fs;

const G: u64 = 0x9E3779B97F4A7C15;
const K1: u64 = 0xBF58476D1CE4E5B9;
const K2: u64 = 0x94D049BB133111EB;

// Simulate one walker. Returns (spread, bumps, returns, manhattan distance).
fn walk(seed0: u64, j: u64, l: u64, b: i32) -> (i64, u64, u64, i64) {
    let mut s = seed0.wrapping_add(j);
    let mut x: i32 = 0;
    let mut y: i32 = 0;
    let mut bumps: u64 = 0;
    let mut returns: u64 = 0;
    for _ in 0..l {
        s = s.wrapping_add(G);
        let mut z = s ^ (s >> 30);
        z = z.wrapping_mul(K1);
        z ^= z >> 27;
        z = z.wrapping_mul(K2);
        z ^= z >> 31;
        match z >> 62 {
            0 => {
                if x == b {
                    bumps += 1;
                } else {
                    x += 1;
                    if x == 0 && y == 0 {
                        returns += 1;
                    }
                }
            }
            1 => {
                if x == -b {
                    bumps += 1;
                } else {
                    x -= 1;
                    if x == 0 && y == 0 {
                        returns += 1;
                    }
                }
            }
            2 => {
                if y == b {
                    bumps += 1;
                } else {
                    y += 1;
                    if x == 0 && y == 0 {
                        returns += 1;
                    }
                }
            }
            _ => {
                if y == -b {
                    bumps += 1;
                } else {
                    y -= 1;
                    if x == 0 && y == 0 {
                        returns += 1;
                    }
                }
            }
        }
    }
    let (xf, yf) = (x as i64, y as i64);
    (xf * xf + yf * yf, bumps, returns, xf.abs() + yf.abs())
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("usage: solution INPUT_PATH [WORKERS]");
        std::process::exit(2);
    }
    let text = fs::read_to_string(&args[1]).expect("cannot read input");
    let mut it = text.split_whitespace();
    let j: u64 = it.next().expect("missing J").parse().expect("bad J");
    let l: u64 = it.next().expect("missing L").parse().expect("bad L");
    let b: i64 = it.next().expect("missing B").parse().expect("bad B");
    let seed: u64 = it.next().expect("missing SEED").parse().expect("bad SEED");
    let workers: usize = args
        .get(2)
        .and_then(|w| w.parse().ok())
        .filter(|&w| w >= 1)
        .unwrap_or(1);

    let pool = rayon::ThreadPoolBuilder::new()
        .num_threads(workers)
        .build()
        .expect("thread pool");

    let results: Vec<(i64, u64, u64, i64)> = pool.install(|| {
        (0..j)
            .into_par_iter()
            .map(|jj| walk(seed, jj, l, b as i32))
            .collect()
    });

    let mut spread: i64 = 0;
    let mut bumps: u64 = 0;
    let mut returns: u64 = 0;
    let mut best_d: i64 = -1;
    let mut best_j: u64 = 0;
    for (idx, r) in results.iter().enumerate() {
        spread += r.0;
        bumps += r.1;
        returns += r.2;
        if r.3 > best_d {
            best_d = r.3;
            best_j = idx as u64;
        }
    }
    if results.is_empty() {
        best_d = 0;
    }
    println!("spread {}", spread);
    println!("bumps {}", bumps);
    println!("returns {}", returns);
    println!("farthest {} {}", best_j, best_d);
}
