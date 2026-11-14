use std::sync::atomic::{AtomicU64, Ordering};

const GAMMA: u64 = 0x9E3779B97F4A7C15;
const C1: u64 = 0xBF58476D1CE4E5B9;
const C2: u64 = 0x94D049BB133111EB;

/// Words (64 steps each) generated per batch.
const W: usize = 64;

type GenFn = unsafe fn(u64, &mut [u64; W], &mut [u64; W], usize);

#[derive(Clone, Copy)]
struct Res {
    x: i64,
    y: i64,
    bumps: u64,
    rets: u64,
}

struct Agg {
    spread: i64,
    bumps: u64,
    rets: u64,
    best_d: i64,
    best_j: u64,
}

impl Agg {
    fn new() -> Self {
        Agg {
            spread: 0,
            bumps: 0,
            rets: 0,
            best_d: -1,
            best_j: 0,
        }
    }

    fn consider(&mut self, d: i64, j: u64) {
        if d > self.best_d || (d == self.best_d && j < self.best_j) {
            self.best_d = d;
            self.best_j = j;
        }
    }

    fn add(&mut self, j: u64, r: Res) {
        let sq = r.x.wrapping_mul(r.x).wrapping_add(r.y.wrapping_mul(r.y));
        self.spread = self.spread.wrapping_add(sq);
        self.bumps += r.bumps;
        self.rets += r.rets;
        self.consider(r.x.abs() + r.y.abs(), j);
    }

    fn merge(&mut self, o: Agg) {
        self.spread = self.spread.wrapping_add(o.spread);
        self.bumps += o.bumps;
        self.rets += o.rets;
        if o.best_d >= 0 {
            self.consider(o.best_d, o.best_j);
        }
    }
}

/// Scalar direction generator: for each step, bit in `hs` = axis (0 = x, 1 = y),
/// bit in `ls` = sign (0 = +1, 1 = -1).
fn gen_scalar(base: u64, hs: &mut [u64; W], ls: &mut [u64; W], nwords: usize) {
    let mut s = base;
    for w in 0..nwords.min(W) {
        let mut h = 0u64;
        let mut l = 0u64;
        for bit in 0..64u32 {
            s = s.wrapping_add(GAMMA);
            let mut z = s;
            z = (z ^ (z >> 30)).wrapping_mul(C1);
            z = (z ^ (z >> 27)).wrapping_mul(C2);
            // The top two bits of z ^ (z >> 31) equal the top two bits of z.
            h |= (z >> 63) << bit;
            l |= ((z >> 62) & 1) << bit;
        }
        hs[w] = h;
        ls[w] = l;
    }
}

#[cfg(target_arch = "x86_64")]
#[target_feature(enable = "avx2")]
unsafe fn gen_avx2(base: u64, hs: &mut [u64; W], ls: &mut [u64; W], nwords: usize) {
    use std::arch::x86_64::*;
    let mut s = _mm256_set_epi64x(
        base.wrapping_add(GAMMA.wrapping_mul(4)) as i64,
        base.wrapping_add(GAMMA.wrapping_mul(3)) as i64,
        base.wrapping_add(GAMMA.wrapping_mul(2)) as i64,
        base.wrapping_add(GAMMA) as i64,
    );
    let step = _mm256_set1_epi64x(GAMMA.wrapping_mul(4) as i64);
    let c1 = _mm256_set1_epi64x(C1 as i64);
    let c1h = _mm256_set1_epi64x((C1 >> 32) as i64);
    let c2 = _mm256_set1_epi64x(C2 as i64);
    let c2h = _mm256_set1_epi64x((C2 >> 32) as i64);
    for w in 0..nwords.min(W) {
        let mut h = 0u64;
        let mut l = 0u64;
        for it in 0..16u32 {
            let mut z = s;
            s = _mm256_add_epi64(s, step);

            z = _mm256_xor_si256(z, _mm256_srli_epi64(z, 30));
            let lo1 = _mm256_mul_epu32(z, c1);
            let cr1 = _mm256_add_epi64(
                _mm256_mul_epu32(_mm256_srli_epi64(z, 32), c1),
                _mm256_mul_epu32(z, c1h),
            );
            z = _mm256_add_epi64(lo1, _mm256_slli_epi64(cr1, 32));

            z = _mm256_xor_si256(z, _mm256_srli_epi64(z, 27));
            let lo2 = _mm256_mul_epu32(z, c2);
            let cr2 = _mm256_add_epi64(
                _mm256_mul_epu32(_mm256_srli_epi64(z, 32), c2),
                _mm256_mul_epu32(z, c2h),
            );
            z = _mm256_add_epi64(lo2, _mm256_slli_epi64(cr2, 32));

            let mh = _mm256_movemask_pd(_mm256_castsi256_pd(z)) as u32 as u64;
            let ml =
                _mm256_movemask_pd(_mm256_castsi256_pd(_mm256_add_epi64(z, z))) as u32 as u64;
            h |= mh << (4 * it);
            l |= ml << (4 * it);
        }
        hs[w] = h;
        ls[w] = l;
    }
}

#[inline(always)]
fn walker_impl(start: u64, l: u64, b: i64, genf: GenFn) -> Res {
    let mut hs = [0u64; W];
    let mut ls = [0u64; W];
    let mut x = 0i64;
    let mut y = 0i64;
    let mut bumps = 0u64;
    let mut rets = 0u64;
    let mut done = 0u64;
    while done < l {
        let base = start.wrapping_add(done.wrapping_mul(GAMMA));
        let batch = (l - done).min(64 * W as u64);
        let nwords = ((batch + 63) / 64) as usize;
        unsafe { genf(base, &mut hs, &mut ls, nwords) };
        let mut rem = batch;
        let mut w = 0usize;
        while rem > 0 {
            let nbits = rem.min(64) as u32;
            let h = hs[w];
            let lo = ls[w];
            let mut i = 0u32;
            while i < nbits {
                let ax = x.abs();
                let ay = y.abs();
                // Number of steps that can neither bump nor return.
                let n = (b - ax.max(ay)).min(ax + ay - 1);
                if n >= 4 {
                    let k = n.min((nbits - i) as i64) as u32; // 1..=64
                    let m = (u64::MAX >> (64 - k)) << i;
                    let xm = !h & m;
                    let ym = h & m;
                    let xtot = xm.count_ones() as i64;
                    let xneg = (xm & lo).count_ones() as i64;
                    let yneg = (ym & lo).count_ones() as i64;
                    let ytot = k as i64 - xtot;
                    x += xtot - 2 * xneg;
                    y += ytot - 2 * yneg;
                    i += k;
                } else {
                    let hb = ((h >> i) & 1) as i64;
                    let sb = ((lo >> i) & 1) as i64;
                    let delta = 1 - 2 * sb;
                    let dx = delta & (hb - 1);
                    let dy = delta & -hb;
                    let nx = x + dx;
                    let ny = y + dy;
                    if nx.abs() > b || ny.abs() > b {
                        bumps += 1;
                    } else {
                        x = nx;
                        y = ny;
                        rets += ((nx | ny) == 0) as u64;
                    }
                    i += 1;
                }
            }
            rem -= nbits as u64;
            w += 1;
        }
        done += batch;
    }
    Res { x, y, bumps, rets }
}

#[cfg(target_arch = "x86_64")]
#[target_feature(enable = "avx2,popcnt,bmi1,bmi2,lzcnt")]
unsafe fn walker_avx2(start: u64, l: u64, b: i64) -> Res {
    walker_impl(start, l, b, gen_avx2)
}

fn walker_scalar(start: u64, l: u64, b: i64) -> Res {
    walker_impl(start, l, b, gen_scalar)
}

#[cfg(target_arch = "x86_64")]
fn detect_fast() -> bool {
    std::is_x86_feature_detected!("avx2")
        && std::is_x86_feature_detected!("popcnt")
        && std::is_x86_feature_detected!("bmi1")
        && std::is_x86_feature_detected!("bmi2")
        && std::is_x86_feature_detected!("lzcnt")
}

#[cfg(not(target_arch = "x86_64"))]
fn detect_fast() -> bool {
    false
}

#[cfg(target_arch = "x86_64")]
fn run_walker(start: u64, l: u64, b: i64, fast: bool) -> Res {
    if fast {
        unsafe { walker_avx2(start, l, b) }
    } else {
        walker_scalar(start, l, b)
    }
}

#[cfg(not(target_arch = "x86_64"))]
fn run_walker(start: u64, l: u64, b: i64, _fast: bool) -> Res {
    walker_scalar(start, l, b)
}

fn worker(ctr: &AtomicU64, j_total: u64, l: u64, b: i64, seed: u64, fast: bool) -> Agg {
    let mut agg = Agg::new();
    loop {
        let j = ctr.fetch_add(1, Ordering::Relaxed);
        if j >= j_total {
            break;
        }
        let r = run_walker(seed.wrapping_add(j), l, b, fast);
        agg.add(j, r);
    }
    agg
}

fn main() {
    let mut args = std::env::args().skip(1);
    let path = args.next().expect("missing input path");
    let workers: usize = args
        .next()
        .and_then(|s| s.trim().parse().ok())
        .unwrap_or(1)
        .clamp(1, 64);

    let text = std::fs::read_to_string(&path).expect("cannot read input");
    let mut it = text.split_whitespace();
    let j_total: u64 = it.next().expect("J").parse().expect("J");
    let l: u64 = it.next().expect("L").parse().expect("L");
    let b_raw: u64 = it.next().expect("B").parse().expect("B");
    let seed: u64 = it.next().expect("SEED").parse().expect("SEED");

    // A walker can never be farther than L from the origin, so clamping B to L
    // does not change the result and keeps the arithmetic safely in range.
    let b = b_raw.min(l).min(1u64 << 62) as i64;

    let fast = detect_fast();
    let nthreads = workers
        .min(usize::try_from(j_total).unwrap_or(usize::MAX))
        .max(1);

    let ctr = AtomicU64::new(0);
    let agg = std::thread::scope(|sc| {
        let handles: Vec<_> = (1..nthreads)
            .map(|_| sc.spawn(|| worker(&ctr, j_total, l, b, seed, fast)))
            .collect();
        let mut a = worker(&ctr, j_total, l, b, seed, fast);
        for h in handles {
            a.merge(h.join().expect("worker panicked"));
        }
        a
    });

    let best_d = if agg.best_d < 0 { 0 } else { agg.best_d };
    print!(
        "spread {}\nbumps {}\nreturns {}\nfarthest {} {}\n",
        agg.spread, agg.bumps, agg.rets, agg.best_j, best_d
    );
}
