use std::io::Read;

fn main() {
    let path = std::env::args().nth(1).expect("input path");
    let mut text = String::new();
    std::fs::File::open(path).unwrap().read_to_string(&mut text).unwrap();
    let mut it = text.split_ascii_whitespace();
    let n: usize = it.next().unwrap().parse().unwrap();
    let steps: usize = it.next().unwrap().parse().unwrap();
    let dt: f64 = it.next().unwrap().parse().unwrap();
    let p: f64 = it.next().unwrap().parse().unwrap();
    let mut x = vec![0.0f64; n];
    let mut v = vec![0.0f64; n];
    let mut m = vec![0.0f64; n];
    let mut k = vec![0.0f64; n];
    let mut r = vec![0.0f64; n];
    let mut c = vec![0.0f64; n];
    for i in 0..n {
        let mut g = || it.next().unwrap().parse::<f64>().unwrap();
        x[i] = g();
        v[i] = g();
        m[i] = g();
        k[i] = g();
        r[i] = g();
        c[i] = g();
    }
    // f[0] holds the force of spring n-1 (f[-1]); f[1..=n] hold springs 0..n-1.
    let mut f = vec![0.0f64; n + 1];
    for _ in 0..steps {
        {
            let (fs, _) = f[1..].split_at_mut(n);
            for i in 0..n - 1 {
                fs[i] = k[i] * ((x[i + 1] - x[i]) - r[i]);
            }
            fs[n - 1] = k[n - 1] * (((x[0] + p) - x[n - 1]) - r[n - 1]);
        }
        f[0] = f[n];
        let (fp, fc) = (&f[..n], &f[1..]);
        for i in 0..n {
            let force = (fc[i] - fp[i]) - (c[i] * v[i]);
            let nv = v[i] + dt * (force / m[i]);
            v[i] = nv;
            x[i] += dt * nv;
        }
    }
    let mut ke = 0.0;
    let mut pe = 0.0;
    let mut xs = 0.0;
    let mut best = -1.0f64;
    let mut j = 0usize;
    for i in 0..n {
        ke += ((0.5 * m[i]) * v[i]) * v[i];
        let s = if i < n - 1 { (x[i + 1] - x[i]) - r[i] } else { ((x[0] + p) - x[n - 1]) - r[n - 1] };
        pe += ((0.5 * k[i]) * s) * s;
        xs += x[i];
        let a = v[i].abs();
        if a > best {
            best = a;
            j = i;
        }
    }
    println!("kinetic {:.12e}\npotential {:.12e}\nposition {:.12e}\nfastest {}", ke, pe, xs, j);
}
