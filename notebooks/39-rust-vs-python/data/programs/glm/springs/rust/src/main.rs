use std::env;
use std::fs;

fn main() {
    let path = env::args().nth(1).expect("usage: solution INPUT_PATH");
    let data = fs::read_to_string(&path).expect("cannot read input");
    let mut it = data.split_ascii_whitespace();
    let mut next_f = || -> f64 {
        it.next()
            .unwrap_or_else(|| panic!("unexpected end of input"))
            .parse()
            .expect("bad number")
    };
    let n = next_f() as usize;
    let steps = next_f() as usize;
    let dt = next_f();
    let p = next_f();

    let mut x = Vec::with_capacity(n);
    let mut v = Vec::with_capacity(n);
    let mut m = Vec::with_capacity(n);
    let mut k = Vec::with_capacity(n);
    let mut r = Vec::with_capacity(n);
    let mut wb = Vec::with_capacity(n); // 1 - dt*c/m
    let mut a = Vec::with_capacity(n); // dt/m
    for _ in 0..n {
        let xi = next_f();
        let vi = next_f();
        let mi = next_f();
        let ki = next_f();
        let ri = next_f();
        let ci = next_f();
        x.push(xi);
        v.push(vi);
        m.push(mi);
        k.push(ki);
        r.push(ri);
        a.push(dt / mi);
        wb.push(1.0 - dt * ci / mi);
    }

    let mut s = vec![0.0f64; n];
    for _ in 0..steps {
        // stretches from the old positions
        for i in 0..n - 1 {
            unsafe {
                *s.get_unchecked_mut(i) =
                    *x.get_unchecked(i + 1) - *x.get_unchecked(i) - *r.get_unchecked(i);
            }
        }
        s[n - 1] = x[0] + p - x[n - 1] - r[n - 1];
        // one pass: f[i] = k[i]*s[i], v = v*wb + a*(f[i]-f[i-1]), x += dt*v
        let mut fm = k[n - 1] * s[n - 1];
        for (((((vi, xi), ki), si), wi), ai) in v
            .iter_mut()
            .zip(x.iter_mut())
            .zip(k.iter())
            .zip(s.iter())
            .zip(wb.iter())
            .zip(a.iter())
        {
            let f = ki * si;
            let vn = *vi * wi + ai * (f - fm);
            fm = f;
            *vi = vn;
            *xi += dt * vn;
        }
    }

    // reports
    let mut kinetic = 0.0f64;
    let mut position = 0.0f64;
    let mut fastest = 0usize;
    let mut best = -1.0f64;
    for (i, (vi, xi)) in v.iter().zip(x.iter()).enumerate() {
        kinetic += (0.5 * m[i]) * vi * vi;
        position += xi;
        let av = vi.abs();
        if av > best {
            best = av;
            fastest = i;
        }
    }
    let mut potential = 0.0f64;
    for i in 0..n - 1 {
        let si = x[i + 1] - x[i] - r[i];
        potential += (0.5 * k[i]) * si * si;
    }
    let sl = x[0] + p - x[n - 1] - r[n - 1];
    potential += (0.5 * k[n - 1]) * sl * sl;

    println!("kinetic {:.16e}", kinetic);
    println!("potential {:.16e}", potential);
    println!("position {:.16e}", position);
    println!("fastest {}", fastest);
}
