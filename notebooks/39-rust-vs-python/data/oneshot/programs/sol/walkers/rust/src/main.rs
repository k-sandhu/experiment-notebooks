use std::env;
use std::fs;
use std::io::{self, Write};
use std::thread;

struct Totals {
    spread: i64,
    bumps: i64,
    returns: i64,
    farthest_id: usize,
    farthest_distance: i64,
}

impl Totals {
    fn new() -> Self {
        Self {
            spread: 0,
            bumps: 0,
            returns: 0,
            farthest_id: usize::MAX,
            farthest_distance: -1,
        }
    }

    fn merge(&mut self, other: Self) {
        self.spread += other.spread;
        self.bumps += other.bumps;
        self.returns += other.returns;

        if other.farthest_distance > self.farthest_distance
            || (other.farthest_distance == self.farthest_distance
                && other.farthest_id < self.farthest_id)
        {
            self.farthest_id = other.farthest_id;
            self.farthest_distance = other.farthest_distance;
        }
    }
}

fn run_worker(
    worker: usize,
    workers: usize,
    walkers: usize,
    steps: u64,
    bound: i64,
    seed: u64,
) -> Totals {
    let mut totals = Totals::new();
    let negative_bound = -bound;

    for j in (worker..walkers).step_by(workers) {
        let mut state = seed.wrapping_add(j as u64);
        let mut x = 0i64;
        let mut y = 0i64;
        let mut bumps = 0i64;
        let mut returns = 0i64;

        for _ in 0..steps {
            state = state.wrapping_add(0x9E3779B97F4A7C15);
            let mut r = state;
            r = (r ^ (r >> 30)).wrapping_mul(0xBF58476D1CE4E5B9);
            r = (r ^ (r >> 27)).wrapping_mul(0x94D049BB133111EB);
            r ^= r >> 31;

            // All zeroes for an x move, all ones for a y move.
            let axis_mask = -((r >> 63) as i64);
            let position = x ^ ((x ^ y) & axis_mask);
            let delta = 1 - ((r >> 61) & 2) as i64;
            let edge = if r & (1u64 << 62) == 0 {
                bound
            } else {
                negative_bound
            };

            let bumped = (position == edge) as i64;
            let movement = delta & (bumped - 1);

            x += movement & !axis_mask;
            y += movement & axis_mask;
            bumps += bumped;

            // Since bound >= 1, a bump cannot occur at the origin.
            returns += ((x | y) == 0) as i64;
        }

        totals.spread += x * x + y * y;
        totals.bumps += bumps;
        totals.returns += returns;

        let distance = x.abs() + y.abs();
        if distance > totals.farthest_distance
            || (distance == totals.farthest_distance && j < totals.farthest_id)
        {
            totals.farthest_distance = distance;
            totals.farthest_id = j;
        }
    }

    totals
}

fn main() {
    let mut args = env::args_os().skip(1);
    let input_path = args.next().unwrap();
    let workers: usize = args.next().unwrap().to_str().unwrap().parse().unwrap();

    let input = fs::read_to_string(input_path).unwrap();
    let mut fields = input.split_whitespace();
    let walkers: usize = fields.next().unwrap().parse().unwrap();
    let steps: u64 = fields.next().unwrap().parse().unwrap();
    let bound: i64 = fields.next().unwrap().parse().unwrap();
    let seed: u64 = fields.next().unwrap().parse().unwrap();

    let totals = thread::scope(|scope| {
        let mut handles = Vec::with_capacity(workers - 1);

        for worker in 1..workers {
            handles.push(scope.spawn(move || {
                run_worker(worker, workers, walkers, steps, bound, seed)
            }));
        }

        let mut totals = run_worker(0, workers, walkers, steps, bound, seed);
        for handle in handles {
            totals.merge(handle.join().unwrap());
        }
        totals
    });

    let stdout = io::stdout();
    let mut output = stdout.lock();
    write!(
        output,
        "spread {}\nbumps {}\nreturns {}\nfarthest {} {}\n",
        totals.spread,
        totals.bumps,
        totals.returns,
        totals.farthest_id,
        totals.farthest_distance
    )
    .unwrap();
}
