use std::{env, fs, thread};

const GAMMA: u64 = 0x9e3779b97f4a7c15;

#[derive(Clone, Copy, Default)]
struct Totals {
    spread: u64,
    bumps: u64,
    returns: u64,
    farthest: usize,
    distance: u64,
}

impl Totals {
    fn merge(&mut self, other: Self) {
        self.spread += other.spread;
        self.bumps += other.bumps;
        self.returns += other.returns;
        if other.distance > self.distance
            || (other.distance == self.distance && other.farthest < self.farthest)
        {
            self.farthest = other.farthest;
            self.distance = other.distance;
        }
    }
}

// Rare boundary hits use a predictable branch. Tiny boxes use clamps instead.
fn run_range_impl<const RARE_BUMPS: bool>(
    first: usize,
    end: usize,
    steps: u64,
    bound: i64,
    seed: u64,
) -> Totals {
    let mut total = Totals {
        farthest: first,
        ..Totals::default()
    };
    for walker in first..end {
        let mut state = seed.wrapping_add(walker as u64);
        let (mut x, mut y) = (0i64, 0i64);
        let (mut bumps, mut returns) = (0u64, 0u64);
        for _ in 0..steps {
            state = state.wrapping_add(GAMMA);
            let mut z = state;
            z = (z ^ (z >> 30)).wrapping_mul(0xbf58476d1ce4e5b9);
            z = (z ^ (z >> 27)).wrapping_mul(0x94d049bb133111eb);
            // The final xor only changes the bottom 33 bits.
            let d = z >> 62;
            let sign = 1 - 2 * (d as i64 & 1);
            let nx = x + i64::from(d < 2) * sign;
            let ny = y + i64::from(d >= 2) * sign;
            if RARE_BUMPS {
                if nx > bound || nx < -bound || ny > bound || ny < -bound {
                    bumps += 1;
                } else {
                    x = nx;
                    y = ny;
                }
            } else {
                x = nx.clamp(-bound, bound);
                y = ny.clamp(-bound, bound);
                bumps += u64::from(nx != x || ny != y);
            }
            // A blocked move cannot be at the origin because B >= 1.
            returns += u64::from((nx | ny) == 0);
        }
        let ax = x.unsigned_abs();
        let ay = y.unsigned_abs();
        total.spread += ax * ax + ay * ay;
        total.bumps += bumps;
        total.returns += returns;
        let distance = ax + ay;
        if distance > total.distance {
            total.distance = distance;
            total.farthest = walker;
        }
    }
    total
}

fn run_range(first: usize, end: usize, steps: u64, bound: i64, seed: u64) -> Totals {
    if bound >= 32 {
        run_range_impl::<true>(first, end, steps, bound, seed)
    } else {
        run_range_impl::<false>(first, end, steps, bound, seed)
    }
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let input = fs::read_to_string(&args[1]).expect("cannot read input");
    let mut fields = input.split_whitespace();
    let walkers: usize = fields.next().unwrap().parse().unwrap();
    let steps: u64 = fields.next().unwrap().parse().unwrap();
    // No walk can reach farther than L along either axis.
    let bound: u64 = fields.next().unwrap().parse().unwrap();
    let bound = bound.min(steps).min(i64::MAX as u64) as i64;
    let seed: u64 = fields.next().unwrap().parse().unwrap();
    let workers = args[2].parse::<usize>().unwrap();
    let total = if workers == 1 {
        run_range(0, walkers, steps, bound, seed)
    } else {
        thread::scope(|scope| {
            let handles: Vec<_> = (0..workers)
                .map(|worker| {
                    let first = walkers / workers * worker + (walkers % workers).min(worker);
                    let end = first + walkers / workers + usize::from(worker < walkers % workers);
                    scope.spawn(move || run_range(first, end, steps, bound, seed))
                })
                .collect();
            let mut total = Totals::default();
            for handle in handles {
                total.merge(handle.join().unwrap());
            }
            total
        })
    };
    println!(
        "spread {}\nbumps {}\nreturns {}\nfarthest {} {}",
        total.spread, total.bumps, total.returns, total.farthest, total.distance
    );
}
