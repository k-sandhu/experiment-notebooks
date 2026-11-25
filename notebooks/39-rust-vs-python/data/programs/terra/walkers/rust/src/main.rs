use std::{env, fs, thread};
fn main() {
    let args: Vec<String> = env::args().collect();
    let input = fs::read_to_string(&args[1]).unwrap();
    let mut f = input.split_whitespace();
    let walkers: u64 = f.next().unwrap().parse().unwrap();
    let steps: u64 = f.next().unwrap().parse().unwrap();
    let bound: i64 = f.next().unwrap().parse::<u64>().unwrap_or(u64::MAX)
        .min(steps).min(i64::MAX as u64) as i64;
    let seed: u64 = f.next().unwrap().parse().unwrap();
    let workers: u64 = args[2].parse().unwrap();
    let mut handles = Vec::new();
    for worker in 0..workers {
        let start = (walkers as u128 * worker as u128 / workers as u128) as u64;
        let end = (walkers as u128 * (worker + 1) as u128 / workers as u128) as u64;
        handles.push(thread::spawn(move || {
            let (mut spread, mut bumps, mut returns) = (0i64, 0i64, 0i64);
            let (mut best_j, mut best_d) = (u64::MAX, -1i64);
            for j in start..end {
                let (mut x, mut y) = (0i64, 0i64);
                let mut state = seed.wrapping_add(j);
                for _ in 0..steps {
                    state = state.wrapping_add(0x9E3779B97F4A7C15);
                    let mut z = state;
                    z = (z ^ (z >> 30)).wrapping_mul(0xBF58476D1CE4E5B9);
                    z = (z ^ (z >> 27)).wrapping_mul(0x94D049BB133111EB);
                    let d = (z ^ (z >> 31)) >> 62;
                    let moved = match d {
                        0 if x < bound => { x += 1; true },
                        1 if x > -bound => { x -= 1; true },
                        2 if y < bound => { y += 1; true },
                        3 if y > -bound => { y -= 1; true },
                        _ => false,
                    };
                    if !moved { bumps += 1; }
                    else if x == 0 && y == 0 { returns += 1; }
                }
                spread += x * x + y * y;
                let distance = x.abs() + y.abs();
                if distance > best_d { best_d = distance; best_j = j; }
            }
            (spread, bumps, returns, best_j, best_d)
        }));
    }
    let (mut spread, mut bumps, mut returns) = (0i64, 0i64, 0i64);
    let (mut best_j, mut best_d) = (u64::MAX, -1i64);
    for handle in handles {
        let (s, b, r, j, d) = handle.join().unwrap();
        spread += s; bumps += b; returns += r;
        if d > best_d || (d == best_d && j < best_j) { best_j = j; best_d = d; }
    }
    println!("spread {spread}\nbumps {bumps}\nreturns {returns}\nfarthest {best_j} {best_d}");
}
