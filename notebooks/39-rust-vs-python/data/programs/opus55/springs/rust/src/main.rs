use std::io::Write;

struct Ring {
    n: usize,
    dt: f64,
    p: f64,
    x: Vec<f64>,
    v: Vec<f64>,
    m: Vec<f64>,
    k: Vec<f64>,
    r: Vec<f64>,
    c: Vec<f64>,
    // fe[0] = f[N-1], fe[1..=N] = f[0..N]
    fe: Vec<f64>,
}

#[inline(always)]
fn simulate_impl(ring: &mut Ring, steps: usize) {
    let n = ring.n;
    let dt = ring.dt;
    let p = ring.p;
    let x = &mut ring.x[..n];
    let v = &mut ring.v[..n];
    let m = &ring.m[..n];
    let k = &ring.k[..n];
    let r = &ring.r[..n];
    let c = &ring.c[..n];
    let fe = &mut ring.fe[..n + 1];
    for _ in 0..steps {
        // Spring forces from old positions.
        {
            let f = &mut fe[1..n];
            let xa = &x[..n - 1];
            let xb = &x[1..n];
            let kk = &k[..n - 1];
            let rr = &r[..n - 1];
            for i in 0..n - 1 {
                f[i] = kk[i] * ((xb[i] - xa[i]) - rr[i]);
            }
            let fl = k[n - 1] * (((x[0] + p) - x[n - 1]) - r[n - 1]);
            fe[n] = fl;
            fe[0] = fl;
        }
        // Velocity and position update.
        let fa = &fe[..n];
        let fb = &fe[1..n + 1];
        for i in 0..n {
            let force = (fb[i] - fa[i]) - c[i] * v[i];
            let nv = v[i] + dt * (force / m[i]);
            v[i] = nv;
            x[i] += dt * nv;
        }
    }
}

#[cfg(target_arch = "x86_64")]
#[target_feature(enable = "avx2")]
unsafe fn simulate_avx2(ring: &mut Ring, steps: usize) {
    simulate_impl(ring, steps)
}

#[cfg(target_arch = "x86_64")]
#[target_feature(enable = "avx512f")]
unsafe fn simulate_avx512(ring: &mut Ring, steps: usize) {
    simulate_impl(ring, steps)
}

fn simulate(ring: &mut Ring, steps: usize) {
    #[cfg(target_arch = "x86_64")]
    {
        if std::is_x86_feature_detected!("avx512f") {
            return unsafe { simulate_avx512(ring, steps) };
        }
        if std::is_x86_feature_detected!("avx2") {
            return unsafe { simulate_avx2(ring, steps) };
        }
    }
    simulate_impl(ring, steps)
}

fn main() {
    let path = std::env::args().nth(1).expect("input path");
    let data = std::fs::read_to_string(&path).expect("read input");
    let mut it = data.split_ascii_whitespace();
    let n: usize = it.next().unwrap().parse().unwrap();
    let steps: usize = it.next().unwrap().parse().unwrap();
    let dt: f64 = it.next().unwrap().parse().unwrap();
    let p: f64 = it.next().unwrap().parse().unwrap();
    let mut x = Vec::with_capacity(n);
    let mut v = Vec::with_capacity(n);
    let mut m = Vec::with_capacity(n);
    let mut k = Vec::with_capacity(n);
    let mut r = Vec::with_capacity(n);
    let mut c = Vec::with_capacity(n);
    for _ in 0..n {
        let mut g = || -> f64 { it.next().unwrap().parse().unwrap() };
        x.push(g());
        v.push(g());
        m.push(g());
        k.push(g());
        r.push(g());
        c.push(g());
    }
    let mut ring = Ring { n, dt, p, x, v, m, k, r, c, fe: vec![0.0; n + 1] };
    if n > 0 {
        simulate(&mut ring, steps);
    }

    let (x, v, m, k, r) = (&ring.x, &ring.v, &ring.m, &ring.k, &ring.r);
    let mut ke = 0.0;
    let mut pe = 0.0;
    let mut xs = 0.0;
    let mut best = 0usize;
    let mut bestv = f64::NEG_INFINITY;
    for i in 0..n {
        ke += ((0.5 * m[i]) * v[i]) * v[i];
        let s = if i + 1 < n { (x[i + 1] - x[i]) - r[i] } else { ((x[0] + p) - x[i]) - r[i] };
        pe += ((0.5 * k[i]) * s) * s;
        xs += x[i];
        let a = v[i].abs();
        if a > bestv {
            bestv = a;
            best = i;
        }
    }
    let out = std::io::stdout();
    let mut out = out.lock();
    writeln!(out, "kinetic {:.16e}", ke).unwrap();
    writeln!(out, "potential {:.16e}", pe).unwrap();
    writeln!(out, "position {:.16e}", xs).unwrap();
    writeln!(out, "fastest {}", best).unwrap();
}
