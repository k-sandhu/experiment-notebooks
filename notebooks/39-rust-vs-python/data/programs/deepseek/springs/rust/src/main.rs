use std::env;
use std::fmt::Write as _;
use std::fs;

fn main() {
    let args: Vec<String> = env::args().collect();
    let text = fs::read_to_string(&args[1]).unwrap();
    let mut it = text.split_ascii_whitespace();

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
        x.push(it.next().unwrap().parse::<f64>().unwrap());
        v.push(it.next().unwrap().parse::<f64>().unwrap());
        m.push(it.next().unwrap().parse::<f64>().unwrap());
        k.push(it.next().unwrap().parse::<f64>().unwrap());
        r.push(it.next().unwrap().parse::<f64>().unwrap());
        c.push(it.next().unwrap().parse::<f64>().unwrap());
    }

    {
        // One fused pass over the ring per step. Spring i's force only needs x[i]
        // and x[i+1], both of which are still the old values when mass i is
        // updated, except for the wrap-around spring which is pre-computed.
        let xp = x.as_mut_ptr();
        let vp = v.as_mut_ptr();
        let mp = m.as_ptr();
        let kp = k.as_ptr();
        let rp = r.as_ptr();
        let cp = c.as_ptr();
        for _ in 0..steps {
            unsafe {
                // Force of the wrap-around spring from the current (start of step) positions.
                let flast = *kp.add(n - 1) * (((*xp + p) - *xp.add(n - 1)) - *rp.add(n - 1));
                let mut fprev = flast;
                for i in 0..n - 1 {
                    let xi = *xp.add(i);
                    let fi = *kp.add(i) * ((*xp.add(i + 1) - xi) - *rp.add(i));
                    let vi = *vp.add(i);
                    let f = (fi - fprev) - *cp.add(i) * vi;
                    let vn = vi + dt * (f / *mp.add(i));
                    *vp.add(i) = vn;
                    *xp.add(i) = xi + dt * vn;
                    fprev = fi;
                }
                let i = n - 1;
                let vi = *vp.add(i);
                let f = (flast - fprev) - *cp.add(i) * vi;
                let vn = vi + dt * (f / *mp.add(i));
                *vp.add(i) = vn;
                *xp.add(i) = *xp.add(i) + dt * vn;
            }
        }
    }

    let mut kinetic = 0.0f64;
    for i in 0..n {
        kinetic += ((0.5 * m[i]) * v[i]) * v[i];
    }

    let mut potential = 0.0f64;
    for i in 0..n - 1 {
        let s = (x[i + 1] - x[i]) - r[i];
        potential += ((0.5 * k[i]) * s) * s;
    }
    let s = ((x[0] + p) - x[n - 1]) - r[n - 1];
    potential += ((0.5 * k[n - 1]) * s) * s;

    let mut position = 0.0f64;
    for i in 0..n {
        position += x[i];
    }

    let mut fastest = 0usize;
    let mut best = v[0].abs();
    for i in 1..n {
        let a = v[i].abs();
        if a > best {
            best = a;
            fastest = i;
        }
    }

    let mut out = String::with_capacity(128);
    let _ = writeln!(out, "kinetic {:.12e}", kinetic);
    let _ = writeln!(out, "potential {:.12e}", potential);
    let _ = writeln!(out, "position {:.12e}", position);
    let _ = writeln!(out, "fastest {}", fastest);
    print!("{}", out);
}
