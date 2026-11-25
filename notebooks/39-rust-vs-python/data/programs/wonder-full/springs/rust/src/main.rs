use std::io::Write;

fn main() {
    let path = std::env::args_os().nth(1).expect("input path argument");
    let text = std::fs::read_to_string(path).expect("read input file");
    let mut it = text.split_ascii_whitespace();
    let n: usize = it.next().unwrap().parse().unwrap();
    let steps: usize = it.next().unwrap().parse().unwrap();
    let dt: f64 = it.next().unwrap().parse().unwrap();
    let period: f64 = it.next().unwrap().parse().unwrap();

    let mut x = vec![0.0f64; n];
    let mut v = vec![0.0f64; n];
    let mut m = vec![0.0f64; n];
    let mut k = vec![0.0f64; n];
    let mut r = vec![0.0f64; n];
    let mut c = vec![0.0f64; n];
    for i in 0..n {
        x[i] = it.next().unwrap().parse().unwrap();
        v[i] = it.next().unwrap().parse().unwrap();
        m[i] = it.next().unwrap().parse().unwrap();
        k[i] = it.next().unwrap().parse().unwrap();
        r[i] = it.next().unwrap().parse().unwrap();
        c[i] = it.next().unwrap().parse().unwrap();
    }
    drop(text);

    if n == 1 {
        let (m0, k0, r0, c0) = (m[0], k[0], r[0], c[0]);
        let (mut x0, mut v0) = (x[0], v[0]);
        for _ in 0..steps {
            let f = k0 * (((x0 + period) - x0) - r0);
            v0 = v0 + dt * (((f - f) - (c0 * v0)) / m0);
            x0 = x0 + dt * v0;
        }
        x[0] = x0;
        v[0] = v0;
    } else if n > 1 {
        simulate(&mut x, &mut v, &m, &k, &r, &c, steps, dt, period);
    }

    let mut kinetic = 0.0f64;
    let mut potential = 0.0f64;
    let mut pos_sum = 0.0f64;
    let mut fastest = 0usize;
    let mut best = -1.0f64;
    for i in 0..n {
        let vi = v[i];
        kinetic += ((0.5 * m[i]) * vi) * vi;
        pos_sum += x[i];
        let av = vi.abs();
        if av > best {
            best = av;
            fastest = i;
        }
        let s = if i + 1 < n {
            (x[i + 1] - x[i]) - r[i]
        } else {
            ((x[0] + period) - x[i]) - r[i]
        };
        potential += ((0.5 * k[i]) * s) * s;
    }

    let stdout = std::io::stdout();
    let mut out = std::io::BufWriter::new(stdout.lock());
    let _ = writeln!(out, "kinetic {:.12e}", kinetic);
    let _ = writeln!(out, "potential {:.12e}", potential);
    let _ = writeln!(out, "position {:.12e}", pos_sum);
    let _ = writeln!(out, "fastest {}", fastest);
}

fn simulate(
    x: &mut [f64],
    v: &mut [f64],
    m: &[f64],
    k: &[f64],
    r: &[f64],
    c: &[f64],
    steps: usize,
    dt: f64,
    period: f64,
) {
    // dt / m[i] is constant across steps; precomputing it replaces a
    // division per mass per step with a multiplication. (This rounds
    // dt * (F / m) as (dt / m) * F instead, a ~1 ulp difference.)
    let a: Vec<f64> = m.iter().map(|&mi| dt / mi).collect();
    #[cfg(target_arch = "x86_64")]
    {
        if std::is_x86_feature_detected!("avx2") {
            // SAFETY: AVX2 availability was just checked at runtime.
            unsafe { simulate_avx2(x, v, &a, k, r, c, steps, dt, period) };
            return;
        }
    }
    simulate_scalar(x, v, &a, k, r, c, steps, dt, period);
}

fn simulate_scalar(
    x: &mut [f64],
    v: &mut [f64],
    a: &[f64],
    k: &[f64],
    r: &[f64],
    c: &[f64],
    steps: usize,
    dt: f64,
    period: f64,
) {
    let n = x.len();
    let last = n - 1;
    let (kl, rl, al, cl) = (k[last], r[last], a[last], c[last]);
    for _ in 0..steps {
        // Force in the last spring, from the old positions; it is both
        // f[N-1] for the last mass and f[-1] for mass 0. Computing it
        // first lets the whole step run in one forward pass: when mass i
        // is updated, f[i] (just computed from still-old x[i], x[i+1])
        // and f[i-1] are both known, and writing x[i] cannot disturb
        // any f still to be computed.
        let f_last = kl * (((x[0] + period) - x[last]) - rl);
        let mut f_prev = f_last;
        for i in 0..last {
            let xi = x[i];
            let f = k[i] * ((x[i + 1] - xi) - r[i]);
            let vi = v[i] + a[i] * ((f - f_prev) - (c[i] * v[i]));
            v[i] = vi;
            x[i] = xi + dt * vi;
            f_prev = f;
        }
        let xl = x[last];
        let vl = v[last] + al * ((f_last - f_prev) - (cl * v[last]));
        v[last] = vl;
        x[last] = xl + dt * vl;
    }
}

/// AVX2 version: two vectorized passes per step. Spring forces go into
/// `fbuf` shifted by one (`fbuf[i + 1] = f[i]`, with `fbuf[0] = fbuf[n]
/// = f[n - 1]`), so the force pass can load `f[i]` and `f[i - 1]` as
/// two plain offset vectors, wrap included. Every lane performs the
/// same operations in the same order as the scalar version (no FMA).
#[cfg(target_arch = "x86_64")]
#[target_feature(enable = "avx2")]
unsafe fn simulate_avx2(
    x: &mut [f64],
    v: &mut [f64],
    a: &[f64],
    k: &[f64],
    r: &[f64],
    c: &[f64],
    steps: usize,
    dt: f64,
    period: f64,
) {
    use std::arch::x86_64::*;
    let n = x.len();
    let last = n - 1;
    let mut fbuf = vec![0.0f64; n + 1];
    // SAFETY: all loads/stores below stay inside the slices: pass 1
    // chunks require i + 4 <= last, pass 2 chunks require i + 4 <= n,
    // and fbuf has n + 1 entries.
    unsafe {
        let dtv = _mm256_set1_pd(dt);
        for _ in 0..steps {
            let f_last = k[last] * (((x[0] + period) - x[last]) - r[last]);
            fbuf[0] = f_last;
            fbuf[n] = f_last;
            // Pass 1: fbuf[i + 1] = k[i] * ((x[i + 1] - x[i]) - r[i]).
            let mut i = 0;
            while i + 4 <= last {
                let xi = _mm256_loadu_pd(x.as_ptr().add(i));
                let xn = _mm256_loadu_pd(x.as_ptr().add(i + 1));
                let s = _mm256_sub_pd(_mm256_sub_pd(xn, xi), _mm256_loadu_pd(r.as_ptr().add(i)));
                let f = _mm256_mul_pd(_mm256_loadu_pd(k.as_ptr().add(i)), s);
                _mm256_storeu_pd(fbuf.as_mut_ptr().add(i + 1), f);
                i += 4;
            }
            while i < last {
                fbuf[i + 1] = k[i] * ((x[i + 1] - x[i]) - r[i]);
                i += 1;
            }
            // Pass 2: update v from fbuf[i + 1] - fbuf[i], then x.
            let mut i = 0;
            while i + 4 <= n {
                let f = _mm256_loadu_pd(fbuf.as_ptr().add(i + 1));
                let fp = _mm256_loadu_pd(fbuf.as_ptr().add(i));
                let vi = _mm256_loadu_pd(v.as_ptr().add(i));
                let force = _mm256_sub_pd(
                    _mm256_sub_pd(f, fp),
                    _mm256_mul_pd(_mm256_loadu_pd(c.as_ptr().add(i)), vi),
                );
                let vn = _mm256_add_pd(
                    vi,
                    _mm256_mul_pd(_mm256_loadu_pd(a.as_ptr().add(i)), force),
                );
                _mm256_storeu_pd(v.as_mut_ptr().add(i), vn);
                let xi = _mm256_loadu_pd(x.as_ptr().add(i));
                _mm256_storeu_pd(x.as_mut_ptr().add(i), _mm256_add_pd(xi, _mm256_mul_pd(dtv, vn)));
                i += 4;
            }
            while i < n {
                let vi = v[i] + a[i] * ((fbuf[i + 1] - fbuf[i]) - (c[i] * v[i]));
                v[i] = vi;
                x[i] = x[i] + dt * vi;
                i += 1;
            }
        }
    }
}
