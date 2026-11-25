use std::{env, fs};

fn main() {
    let path = env::args_os().nth(1).expect("missing input path");
    let input = fs::read_to_string(path).expect("cannot read input");
    let mut it = input.split_whitespace();
    let n: usize = it.next().unwrap().parse().unwrap();
    let steps: usize = it.next().unwrap().parse().unwrap();
    let dt: f64 = it.next().unwrap().parse().unwrap();
    let p: f64 = it.next().unwrap().parse().unwrap();
    let (mut x, mut v, mut m, mut k, mut r, mut c) = (
        Vec::with_capacity(n), Vec::with_capacity(n), Vec::with_capacity(n),
        Vec::with_capacity(n), Vec::with_capacity(n), Vec::with_capacity(n),
    );
    for _ in 0..n {
        x.push(it.next().unwrap().parse::<f64>().unwrap());
        v.push(it.next().unwrap().parse::<f64>().unwrap());
        m.push(it.next().unwrap().parse::<f64>().unwrap());
        k.push(it.next().unwrap().parse::<f64>().unwrap());
        r.push(it.next().unwrap().parse::<f64>().unwrap());
        c.push(it.next().unwrap().parse::<f64>().unwrap());
    }
    let mut f = vec![0.0; n];
    for _ in 0..steps {
        for i in 0..n-1 {
            f[i] = k[i] * ((x[i+1] - x[i]) - r[i]);
        }
        f[n-1] = k[n-1] * (((x[0] + p) - x[n-1]) - r[n-1]);
        let mut prev = f[n-1];
        for i in 0..n {
            let force = (f[i] - prev) - (c[i] * v[i]);
            prev = f[i];
            v[i] = v[i] + dt * (force / m[i]);
            x[i] = x[i] + dt * v[i];
        }
    }
    let (mut kinetic, mut potential, mut position) = (0.0, 0.0, 0.0);
    let mut fastest = 0;
    for i in 0..n {
        kinetic += ((0.5 * m[i]) * v[i]) * v[i];
        let stretch = if i + 1 == n { ((x[0] + p) - x[i]) - r[i] } else { (x[i+1] - x[i]) - r[i] };
        potential += ((0.5 * k[i]) * stretch) * stretch;
        position += x[i];
        if v[i].abs() > v[fastest].abs() { fastest = i; }
    }
    println!("kinetic {:.15e}\npotential {:.15e}\nposition {:.15e}\nfastest {}", kinetic, potential, position, fastest);
}
