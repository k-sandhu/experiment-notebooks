use std::env;
use std::fs::read_to_string;
use std::io::{self, Write};

fn main() {
    let path = env::args().nth(1).expect("usage: solution <input>");
    let content = read_to_string(&path).expect("failed to read input file");
    let mut nums = content.split_whitespace();

    let n: usize = nums.next().expect("missing N").parse().expect("invalid N");
    let steps: usize = nums.next().expect("missing S").parse().expect("invalid S");
    let dt: f64 = nums.next().expect("missing dt").parse().expect("invalid dt");
    let p: f64 = nums.next().expect("missing P").parse().expect("invalid P");

    let mut x: Vec<f64> = Vec::with_capacity(n);
    let mut v: Vec<f64> = Vec::with_capacity(n);
    let mut m: Vec<f64> = Vec::with_capacity(n);
    let mut k: Vec<f64> = Vec::with_capacity(n);
    let mut r: Vec<f64> = Vec::with_capacity(n);
    let mut c: Vec<f64> = Vec::with_capacity(n);

    for _ in 0..n {
        x.push(nums.next().expect("missing x").parse().expect("invalid x"));
        v.push(nums.next().expect("missing v").parse().expect("invalid v"));
        m.push(nums.next().expect("missing m").parse().expect("invalid m"));
        k.push(nums.next().expect("missing k").parse().expect("invalid k"));
        r.push(nums.next().expect("missing r").parse().expect("invalid r"));
        c.push(nums.next().expect("missing c").parse().expect("invalid c"));
    }

    let mut f = vec![0.0; n];
    let last = n - 1;

    for _ in 0..steps {
        // Stretches and spring forces from the old positions.
        for i in 0..last {
            let s = (x[i + 1] - x[i]) - r[i];
            f[i] = k[i] * s;
        }
        let s_last = ((x[0] + p) - x[last]) - r[last];
        f[last] = k[last] * s_last;

        // Force on each mass, then velocity and position updates.
        // f[-1] means f[n-1], which is still the old spring force here.
        let mut fprev = f[last];
        for i in 0..n {
            let force = (f[i] - fprev) - c[i] * v[i];
            fprev = f[i];
            v[i] = v[i] + dt * (force / m[i]);
            x[i] = x[i] + dt * v[i];
        }
    }

    // Final quantities from the final state.
    let mut kinetic = 0.0;
    let mut potential = 0.0;
    let mut position = 0.0;
    for i in 0..last {
        let s = (x[i + 1] - x[i]) - r[i];
        kinetic += ((0.5 * m[i]) * v[i]) * v[i];
        potential += ((0.5 * k[i]) * s) * s;
        position += x[i];
    }
    let s_last = ((x[0] + p) - x[last]) - r[last];
    kinetic += ((0.5 * m[last]) * v[last]) * v[last];
    potential += ((0.5 * k[last]) * s_last) * s_last;
    position += x[last];

    let mut j = 0;
    let mut best = v[0].abs();
    for i in 1..n {
        let a = v[i].abs();
        if a > best {
            best = a;
            j = i;
        }
    }

    let out = format!(
        "kinetic {:.12e}\npotential {:.12e}\nposition {:.12e}\nfastest {}\n",
        kinetic, potential, position, j
    );
    let mut handle = io::stdout().lock();
    handle.write_all(out.as_bytes()).unwrap();
}
