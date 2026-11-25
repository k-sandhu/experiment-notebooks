use std::io::{self, Write};

fn main() {
    let arg = std::env::args_os().nth(1).expect("usage: solution INPUT");
    let data = std::fs::read(arg).expect("read input");
    // Input is plain ASCII numbers separated by whitespace.
    let text = unsafe { std::str::from_utf8_unchecked(&data) };
    let mut it = text.split_ascii_whitespace();
    let n: usize = it.next().unwrap_or("0").parse().unwrap_or(0);
    let s_count: usize = it.next().unwrap_or("0").parse().unwrap_or(0);
    let dt: f64 = it.next().unwrap_or("0").parse().unwrap_or(0.0);
    let p: f64 = it.next().unwrap_or("0").parse().unwrap_or(0.0);

    if n == 0 {
        let out = "kinetic 0.000000000000e0\npotential 0.000000000000e0\nposition 0.000000000000e0\nfastest 0\n";
        let stdout = io::stdout();
        let mut lock = stdout.lock();
        let _ = lock.write_all(out.as_bytes());
        return;
    }

    let mut x = vec![0.0f64; n];
    let mut v = vec![0.0f64; n];
    let mut m = vec![0.0f64; n];
    let mut k = vec![0.0f64; n];
    let mut r = vec![0.0f64; n];
    let mut c = vec![0.0f64; n];
    for i in 0..n {
        x[i] = it.next().unwrap_or("0").parse().unwrap_or(0.0);
        v[i] = it.next().unwrap_or("0").parse().unwrap_or(0.0);
        m[i] = it.next().unwrap_or("0").parse().unwrap_or(0.0);
        k[i] = it.next().unwrap_or("0").parse().unwrap_or(0.0);
        r[i] = it.next().unwrap_or("0").parse().unwrap_or(0.0);
        c[i] = it.next().unwrap_or("0").parse().unwrap_or(0.0);
    }

    // v_new = b*v + a*(f[i]-f[i-1]), a = dt/m, b = 1 - a*c
    let mut a = vec![0.0f64; n];
    let mut b = vec![0.0f64; n];
    for i in 0..n {
        let ai = dt / m[i];
        a[i] = ai;
        b[i] = 1.0 - ai * c[i];
    }
    // c and (temporarily) m no longer needed in loop; m kept for kinetic.
    drop(c);

    let mut f = vec![0.0f64; n];
    let n1 = n - 1;

    for _ in 0..s_count {
        // f[i] = k[i] * ((x[i+1]-x[i]) - r[i]) for i < n-1
        {
            let (f_head, _) = f.split_at_mut(n1);
            for ((((fi, &ki), &ri), &xi), &xn) in f_head
                .iter_mut()
                .zip(k.iter())
                .zip(r.iter())
                .zip(x.iter())
                .zip(x[1..].iter())
            {
                *fi = ki * ((xn - xi) - ri);
            }
        }
        f[n1] = k[n1] * (((x[0] + p) - x[n1]) - r[n1]);

        // Update v and x. First element uses f[n-1] as previous.
        {
            let f_last = f[n1];
            let v0 = b[0] * v[0] + a[0] * (f[0] - f_last);
            v[0] = v0;
            x[0] += dt * v0;
        }
        if n > 1 {
            for (((((vi, xi), &ai), &bi), &fi), &fp) in v[1..]
                .iter_mut()
                .zip(x[1..].iter_mut())
                .zip(a[1..].iter())
                .zip(b[1..].iter())
                .zip(f[1..].iter())
                .zip(f[..n1].iter())
            {
                let nv = bi * (*vi) + ai * (fi - fp);
                *vi = nv;
                *xi += dt * nv;
            }
        }
    }

    // Final energies. Recompute stretch into f.
    {
        let (f_head, _) = f.split_at_mut(n1);
        for ((((fi, &ki), &ri), &xi), &xn) in f_head
            .iter_mut()
            .zip(k.iter())
            .zip(r.iter())
            .zip(x.iter())
            .zip(x[1..].iter())
        {
            let _ = ki;
            *fi = (xn - xi) - ri;
        }
    }
    f[n1] = ((x[0] + p) - x[n1]) - r[n1];

    let mut kinetic = 0.0f64;
    let mut pos_sum = 0.0f64;
    let mut fastest: usize = 0;
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
    }
    let mut potential = 0.0f64;
    for i in 0..n {
        let si = f[i];
        potential += ((0.5 * k[i]) * si) * si;
    }

    let out = format!(
        "kinetic {:.12e}\npotential {:.12e}\nposition {:.12e}\nfastest {}\n",
        kinetic, potential, pos_sum, fastest
    );
    let stdout = io::stdout();
    let mut lock = stdout.lock();
    let _ = lock.write_all(out.as_bytes());
}
