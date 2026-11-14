use std::io::Write;

fn simulate_scalar(
    xe: &mut [f64],
    v: &mut [f64],
    m: &[f64],
    k: &[f64],
    r: &[f64],
    c: &[f64],
    dt: f64,
    p: f64,
    steps: u64,
) {
    let n = v.len();
    if n == 0 {
        return;
    }
    let xe = &mut xe[..n + 1];
    let m = &m[..n];
    let k = &k[..n];
    let r = &r[..n];
    let c = &c[..n];
    for _ in 0..steps {
        xe[n] = xe[0] + p;
        let mut fprev = k[n - 1] * ((xe[n] - xe[n - 1]) - r[n - 1]);
        for i in 0..n {
            let f = k[i] * ((xe[i + 1] - xe[i]) - r[i]);
            let force = (f - fprev) - c[i] * v[i];
            let vn = v[i] + dt * (force / m[i]);
            v[i] = vn;
            xe[i] += dt * vn;
            fprev = f;
        }
    }
}

#[cfg(target_arch = "x86_64")]
#[target_feature(enable = "avx2")]
unsafe fn simulate_avx2(
    xe: &mut [f64],
    v: &mut [f64],
    m: &[f64],
    k: &[f64],
    r: &[f64],
    c: &[f64],
    dt: f64,
    p: f64,
    steps: u64,
) {
    use std::arch::x86_64::*;
    let n = v.len();
    if n == 0 {
        return;
    }
    assert!(xe.len() == n + 1 && m.len() == n && k.len() == n && r.len() == n && c.len() == n);
    let xp = xe.as_mut_ptr();
    let vp = v.as_mut_ptr();
    let mp = m.as_ptr();
    let kp = k.as_ptr();
    let rp = r.as_ptr();
    let cp = c.as_ptr();
    let nv = n & !3usize;
    unsafe {
        let dtv = _mm256_set1_pd(dt);
        for _ in 0..steps {
            let x0 = *xp;
            *xp.add(n) = x0 + p;
            let flast = *kp.add(n - 1) * ((*xp.add(n) - *xp.add(n - 1)) - *rp.add(n - 1));
            let mut carry = _mm256_set1_pd(flast);
            let mut i = 0usize;
            while i < nv {
                let xa = _mm256_loadu_pd(xp.add(i));
                let xb = _mm256_loadu_pd(xp.add(i + 1));
                let s = _mm256_sub_pd(_mm256_sub_pd(xb, xa), _mm256_loadu_pd(rp.add(i)));
                let f = _mm256_mul_pd(_mm256_loadu_pd(kp.add(i)), s);
                // [f0, f0, f1, f2], then element 0 replaced by previous block's f3
                let sh = _mm256_permute4x64_pd::<0x90>(f);
                let fprev = _mm256_blend_pd::<1>(sh, carry);
                carry = _mm256_permute4x64_pd::<0xFF>(f);
                let vv = _mm256_loadu_pd(vp.add(i));
                let force = _mm256_sub_pd(
                    _mm256_sub_pd(f, fprev),
                    _mm256_mul_pd(_mm256_loadu_pd(cp.add(i)), vv),
                );
                let acc = _mm256_div_pd(force, _mm256_loadu_pd(mp.add(i)));
                let vn = _mm256_add_pd(vv, _mm256_mul_pd(dtv, acc));
                _mm256_storeu_pd(vp.add(i), vn);
                _mm256_storeu_pd(xp.add(i), _mm256_add_pd(xa, _mm256_mul_pd(dtv, vn)));
                i += 4;
            }
            if i < n {
                let mut tmp = [0.0f64; 4];
                _mm256_storeu_pd(tmp.as_mut_ptr(), carry);
                let mut fprev = tmp[0];
                while i < n {
                    let xi = *xp.add(i);
                    let f = *kp.add(i) * ((*xp.add(i + 1) - xi) - *rp.add(i));
                    let vi = *vp.add(i);
                    let force = (f - fprev) - *cp.add(i) * vi;
                    let vn = vi + dt * (force / *mp.add(i));
                    *vp.add(i) = vn;
                    *xp.add(i) = xi + dt * vn;
                    fprev = f;
                    i += 1;
                }
            }
        }
    }
}

fn simulate(
    xe: &mut [f64],
    v: &mut [f64],
    m: &[f64],
    k: &[f64],
    r: &[f64],
    c: &[f64],
    dt: f64,
    p: f64,
    steps: u64,
) {
    #[cfg(target_arch = "x86_64")]
    {
        if is_x86_feature_detected!("avx2") {
            unsafe { simulate_avx2(xe, v, m, k, r, c, dt, p, steps) };
            return;
        }
    }
    simulate_scalar(xe, v, m, k, r, c, dt, p, steps);
}

fn main() {
    let path = std::env::args().nth(1).expect("missing input path");
    let data = std::fs::read_to_string(path).expect("cannot read input");
    let mut it = data.split_ascii_whitespace();
    let n: usize = it.next().unwrap().parse().unwrap();
    let steps: u64 = it.next().unwrap().parse().unwrap();
    let dt: f64 = it.next().unwrap().parse().unwrap();
    let p: f64 = it.next().unwrap().parse().unwrap();

    let mut xe: Vec<f64> = Vec::with_capacity(n + 1);
    let mut v: Vec<f64> = Vec::with_capacity(n);
    let mut m: Vec<f64> = Vec::with_capacity(n);
    let mut k: Vec<f64> = Vec::with_capacity(n);
    let mut r: Vec<f64> = Vec::with_capacity(n);
    let mut c: Vec<f64> = Vec::with_capacity(n);
    for _ in 0..n {
        xe.push(it.next().unwrap().parse().unwrap());
        v.push(it.next().unwrap().parse().unwrap());
        m.push(it.next().unwrap().parse().unwrap());
        k.push(it.next().unwrap().parse().unwrap());
        r.push(it.next().unwrap().parse().unwrap());
        c.push(it.next().unwrap().parse().unwrap());
    }
    xe.push(0.0);

    simulate(&mut xe, &mut v, &m, &k, &r, &c, dt, p, steps);

    let mut kin = 0.0f64;
    let mut pot = 0.0f64;
    let mut xsum = 0.0f64;
    let mut best = 0usize;
    let mut best_abs = f64::NEG_INFINITY;
    if n > 0 {
        xe[n] = xe[0] + p;
        for i in 0..n {
            kin += ((0.5 * m[i]) * v[i]) * v[i];
            let s = (xe[i + 1] - xe[i]) - r[i];
            pot += ((0.5 * k[i]) * s) * s;
            xsum += xe[i];
            let a = v[i].abs();
            if a > best_abs {
                best_abs = a;
                best = i;
            }
        }
    }

    let out = format!(
        "kinetic {:.16e}\npotential {:.16e}\nposition {:.16e}\nfastest {}\n",
        kin, pot, xsum, best
    );
    let stdout = std::io::stdout();
    let mut lock = stdout.lock();
    lock.write_all(out.as_bytes()).unwrap();
    lock.flush().unwrap();
}
