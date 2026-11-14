use std::{env, fs, thread};

#[derive(Clone, Copy)]
struct Totals {
    spread: i64,
    bumps: i64,
    returns: i64,
    farthest_id: usize,
    farthest_distance: i64,
}

impl Totals {
    fn empty() -> Self {
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
            self.farthest_distance = other.farthest_distance;
            self.farthest_id = other.farthest_id;
        }
    }
}

fn simulate(start: usize, end: usize, steps: u64, bound: i64, seed: u64) -> Totals {
    let mut totals = Totals::empty();

    for walker in start..end {
        let mut state = seed.wrapping_add(walker as u64);
        let mut x = 0i64;
        let mut y = 0i64;
        let mut bumps = 0i64;
        let mut returns = 0i64;

        for _ in 0..steps {
            state = state.wrapping_add(0x9E3779B97F4A7C15);
            let mut z = state;
            z = (z ^ (z >> 30)).wrapping_mul(0xBF58476D1CE4E5B9);
            z = (z ^ (z >> 27)).wrapping_mul(0x94D049BB133111EB);

            // The final XOR with z >> 31 does not change the top two bits.
            let axis_mask = -((z >> 63) as i64);
            let sign_mask = -(((z >> 62) & 1) as i64);

            let coordinate = x ^ ((x ^ y) & axis_mask);
            let boundary = (bound ^ sign_mask) - sign_mask;
            let blocked = coordinate == boundary;
            let movement = (sign_mask | 1) & -((!blocked) as i64);

            x += movement & !axis_mask;
            y += movement & axis_mask;

            bumps += blocked as i64;
            // Since bound >= 1, a bump cannot occur at the origin.
            returns += ((x | y) == 0) as i64;
        }

        totals.spread += x * x + y * y;
        totals.bumps += bumps;
        totals.returns += returns;

        let distance = x.abs() + y.abs();
        if distance > totals.farthest_distance {
            totals.farthest_distance = distance;
            totals.farthest_id = walker;
        }
    }

    totals
}

fn main() {
    let mut args = env::args_os().skip(1);
    let path = args.next().unwrap();
    let workers: usize = args.next().unwrap().to_str().unwrap().parse().unwrap();

    let input = fs::read_to_string(path).unwrap();
    let mut fields = input.split_whitespace();
    let walkers: usize = fields.next().unwrap().parse().unwrap();
    let steps: u64 = fields.next().unwrap().parse().unwrap();
    let bound: i64 = fields.next().unwrap().parse().unwrap();
    let seed: u64 = fields.next().unwrap().parse().unwrap();

    let base = walkers / workers;
    let remainder = walkers % workers;
    let partition_start = |worker: usize| base * worker + remainder.min(worker);

    let totals = thread::scope(|scope| {
        let mut handles = Vec::with_capacity(workers - 1);

        for worker in 1..workers {
            let start = partition_start(worker);
            let end = partition_start(worker + 1);
            handles.push(scope.spawn(move || simulate(start, end, steps, bound, seed)));
        }

        // The main thread is also a worker.
        let mut totals = simulate(0, partition_start(1), steps, bound, seed);
        for handle in handles {
            totals.merge(handle.join().unwrap());
        }
        totals
    });

    println!(
        "spread {}\nbumps {}\nreturns {}\nfarthest {} {}",
        totals.spread,
        totals.bumps,
        totals.returns,
        totals.farthest_id,
        totals.farthest_distance
    );
}
