use rayon::prelude::*;
use std::io::Write as _;

const GOLD: u64 = 0x9E37_79B9_7F4A_7C15;
const C1: u64 = 0xBF58_476D_1CE4_E5B9;
const C2: u64 = 0x94D0_49BB_1331_11EB;

#[derive(Clone, Copy)]
struct Agg {
    spread: i64,
    bumps: i64,
    returns: i64,
    best_j: u64,
    best_d: i64,
}

impl Agg {
    fn empty() -> Self {
        Self { spread: 0, bumps: 0, returns: 0, best_j: 0, best_d: -1 }
    }
    fn add_walker(&mut self, j: u64, x: i64, y: i64, bumps: i64, returns: i64) {
        self.spread += x * x + y * y;
        self.bumps += bumps;
        self.returns += returns;
        let d = x.abs() + y.abs();
        if d > self.best_d {
            self.best_d = d;
            self.best_j = j;
        }
    }
    fn merge(self, other: Self) -> Self {
        let (best_j, best_d) = if other.best_d > self.best_d
            || (other.best_d == self.best_d && other.best_j < self.best_j)
        {
            (other.best_j, other.best_d)
        } else {
            (self.best_j, self.best_d)
        };
        Self {
            spread: self.spread + other.spread,
            bumps: self.bumps + other.bumps,
            returns: self.returns + other.returns,
            best_j,
            best_d,
        }
    }
}

// One step for one walker. Coordinates are offset by +B, so they lie in
// [0, 2B]; the origin is (B, B). Branchless: the direction is random, so
// real branches on it would mispredict constantly. Only the top two bits
// of the SplitMix64 output are needed, and the final `z ^ (z >> 31)`
// cannot change those bits, so it is omitted.
macro_rules! step {
    ($state:ident, $x:ident, $y:ident, $bumps:ident, $rets:ident, $b:ident, $a:ident) => {{
        $state = $state.wrapping_add(GOLD);
        let mut z = $state;
        z = (z ^ (z >> 30)).wrapping_mul(C1);
        z = (z ^ (z >> 27)).wrapping_mul(C2);
        let d = (z >> 62) as i64; // 0..3
        let sign = 1 - ((d & 1) << 1); // +1 for d in {0,2}, -1 for {1,3}
        let is_y = d >> 1; // 0 = x move, 1 = y move
        let nx = $x + sign * (1 - is_y);
        let ny = $y + sign * is_y;
        // As unsigned, a negative value becomes huge, so one compare each.
        let ok = (nx as u64) <= ($a as u64) && (ny as u64) <= ($a as u64);
        $bumps += (!ok) as i64;
        $x = if ok { nx } else { $x };
        $y = if ok { ny } else { $y };
        // A bump leaves the walker on the boundary, never at the origin
        // (B >= 1), so this also correctly excludes bumps.
        $rets += ($x == $b && $y == $b) as i64;
    }};
}

fn run1(seed: u64, start: u64, l: u64, b: i64, a: i64) -> Agg {
    let mut agg = Agg::empty();
    let mut s0 = seed.wrapping_add(start);
    let (mut x0, mut y0) = (b, b);
    let (mut bp0, mut rt0) = (0i64, 0i64);
    for _ in 0..l {
        step!(s0, x0, y0, bp0, rt0, b, a);
    }
    agg.add_walker(start, x0 - b, y0 - b, bp0, rt0);
    agg
}

fn run2(seed: u64, start: u64, l: u64, b: i64, a: i64) -> Agg {
    let mut agg = Agg::empty();
    let mut s0 = seed.wrapping_add(start);
    let mut s1 = seed.wrapping_add(start + 1);
    let (mut x0, mut y0) = (b, b);
    let (mut x1, mut y1) = (b, b);
    let (mut bp0, mut rt0) = (0i64, 0i64);
    let (mut bp1, mut rt1) = (0i64, 0i64);
    for _ in 0..l {
        step!(s0, x0, y0, bp0, rt0, b, a);
        step!(s1, x1, y1, bp1, rt1, b, a);
    }
    agg.add_walker(start, x0 - b, y0 - b, bp0, rt0);
    agg.add_walker(start + 1, x1 - b, y1 - b, bp1, rt1);
    agg
}

// Four walkers stepped in lockstep: the SplitMix64 chain of each walker is
// latency-bound (dependent multiplies), so interleaving independent
// walkers lets the CPU overlap those chains.
fn run4(seed: u64, start: u64, l: u64, b: i64, a: i64) -> Agg {
    let mut agg = Agg::empty();
    let mut s0 = seed.wrapping_add(start);
    let mut s1 = seed.wrapping_add(start + 1);
    let mut s2 = seed.wrapping_add(start + 2);
    let mut s3 = seed.wrapping_add(start + 3);
    let (mut x0, mut y0) = (b, b);
    let (mut x1, mut y1) = (b, b);
    let (mut x2, mut y2) = (b, b);
    let (mut x3, mut y3) = (b, b);
    let (mut bp0, mut rt0) = (0i64, 0i64);
    let (mut bp1, mut rt1) = (0i64, 0i64);
    let (mut bp2, mut rt2) = (0i64, 0i64);
    let (mut bp3, mut rt3) = (0i64, 0i64);
    for _ in 0..l {
        step!(s0, x0, y0, bp0, rt0, b, a);
        step!(s1, x1, y1, bp1, rt1, b, a);
        step!(s2, x2, y2, bp2, rt2, b, a);
        step!(s3, x3, y3, bp3, rt3, b, a);
    }
    agg.add_walker(start, x0 - b, y0 - b, bp0, rt0);
    agg.add_walker(start + 1, x1 - b, y1 - b, bp1, rt1);
    agg.add_walker(start + 2, x2 - b, y2 - b, bp2, rt2);
    agg.add_walker(start + 3, x3 - b, y3 - b, bp3, rt3);
    agg
}

fn run_chunk(seed: u64, start: u64, count: u64, l: u64, b: i64, a: i64) -> Agg {
    match count {
        4 => run4(seed, start, l, b, a),
        3 => run2(seed, start, l, b, a).merge(run1(seed, start + 2, l, b, a)),
        2 => run2(seed, start, l, b, a),
        1 => run1(seed, start, l, b, a),
        _ => Agg::empty(),
    }
}

fn main() {
    let args: Vec<std::ffi::OsString> = std::env::args_os().collect();
    let data = std::fs::read(&args[1]).unwrap();
    let mut it = data
        .split(|c: &u8| c.is_ascii_whitespace())
        .filter(|s| !s.is_empty())
        .map(|s| std::str::from_utf8(s).unwrap().parse::<u64>().unwrap());
    let j = it.next().unwrap_or(0);
    let l = it.next().unwrap_or(0);
    let b = it.next().unwrap_or(0) as i64;
    let seed = it.next().unwrap_or(0);
    let workers: usize = args
        .get(2)
        .and_then(|s| s.to_str())
        .and_then(|s| s.parse().ok())
        .unwrap_or(1)
        .clamp(1, 32);

    let a = 2 * b;
    let agg = if j == 0 {
        Agg { best_d: 0, ..Agg::empty() }
    } else {
        // Group walkers for ILP, but keep at least as many chunks as workers.
        let group: u64 = if j >= 4 * workers as u64 {
            4
        } else if j >= 2 * workers as u64 {
            2
        } else {
            1
        };
        let nchunks = j.div_ceil(group);
        let compute = || {
            (0..nchunks)
                .into_par_iter()
                .map(|c| {
                    let start = c * group;
                    let count = group.min(j - start);
                    run_chunk(seed, start, count, l, b, a)
                })
                .reduce(Agg::empty, Agg::merge)
        };
        if workers == 1 {
            compute()
        } else {
            rayon::ThreadPoolBuilder::new()
                .num_threads(workers)
                .build()
                .unwrap()
                .install(compute)
        }
    };

    let mut out = std::io::stdout().lock();
    let _ = write!(
        out,
        "spread {}\nbumps {}\nreturns {}\nfarthest {} {}\n",
        agg.spread, agg.bumps, agg.returns, agg.best_j, agg.best_d
    );
}
