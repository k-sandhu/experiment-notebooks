//! Ring of N masses joined by N springs, simulated for S steps (see SPEC.md).
//!
//! Structure of arrays. `xe` holds the positions plus one spare slot, `xe[n]`, that
//! is set to the wrapped neighbour `x[0] + P` before each step, so every spring
//! stretch is a subtraction of two shifted views. `fe` holds the spring forces the
//! same way: `fe[1 + i] = f[i]` and `fe[0]` mirrors `f[n - 1]`. Each step is two
//! branch-free linear passes that the compiler can vectorise. The operation order
//! matches SPEC.md exactly, so every mass follows the same trajectory as the spec.

use std::str::FromStr;

fn next<'a, T: FromStr>(tokens: &mut impl Iterator<Item = &'a str>) -> T
where
    T::Err: std::fmt::Debug,
{
    tokens.next().expect("input too short").parse().expect("bad number")
}

/// Neumaier-compensated sum, so the result barely depends on summation order.
fn sum(values: impl Iterator<Item = f64>) -> f64 {
    let (mut total, mut comp) = (0.0f64, 0.0f64);
    for value in values {
        let t = total + value;
        if total.abs() >= value.abs() {
            comp += (total - t) + value;
        } else {
            comp += (value - t) + total;
        }
        total = t;
    }
    total + comp
}

fn main() {
    let path = std::env::args().nth(1).expect("usage: solution INPUT_PATH");
    let text = std::fs::read_to_string(&path).expect("cannot read input file");
    let mut tokens = text.split_ascii_whitespace();

    let n: usize = next(&mut tokens);
    let steps: usize = next(&mut tokens);
    let dt: f64 = next(&mut tokens);
    let p: f64 = next(&mut tokens);

    let mut xe = vec![0.0f64; n + 1];
    let mut v = vec![0.0f64; n];
    let mut m = vec![0.0f64; n];
    let mut k = vec![0.0f64; n];
    let mut r = vec![0.0f64; n];
    let mut c = vec![0.0f64; n];
    for i in 0..n {
        xe[i] = next(&mut tokens);
        v[i] = next(&mut tokens);
        m[i] = next(&mut tokens);
        k[i] = next(&mut tokens);
        r[i] = next(&mut tokens);
        c[i] = next(&mut tokens);
    }

    let mut fe = vec![0.0f64; n + 1];
    for _ in 0..steps {
        xe[n] = xe[0] + p;

        // Steps 1 and 2: spring forces from the old positions.
        for ((((fi, &a), &b), &ki), &ri) in fe[1..]
            .iter_mut()
            .zip(&xe[1..])
            .zip(&xe[..n])
            .zip(&k)
            .zip(&r)
        {
            *fi = ki * ((a - b) - ri);
        }
        fe[0] = fe[n];

        // Steps 3 to 5: force, new velocity, then new position from that velocity.
        for (((((vi, xi), &mi), &ci), &fc), &fp) in v
            .iter_mut()
            .zip(xe[..n].iter_mut())
            .zip(&m)
            .zip(&c)
            .zip(&fe[1..])
            .zip(&fe[..n])
        {
            let force = (fc - fp) - ci * *vi;
            *vi += dt * (force / mi);
            *xi += dt * *vi;
        }
    }

    // Energies use the final state. Spring n-1 ends at x[0] + P.
    xe[n] = xe[0] + p;
    let kinetic = sum((0..n).map(|i| ((0.5 * m[i]) * v[i]) * v[i]));
    let potential = sum((0..n).map(|i| {
        let s = (xe[i + 1] - xe[i]) - r[i];
        ((0.5 * k[i]) * s) * s
    }));
    let position = sum(xe[..n].iter().copied());

    let mut fastest = 0;
    let mut best = -1.0f64;
    for (i, vi) in v.iter().enumerate() {
        let speed = vi.abs();
        if speed > best {
            best = speed;
            fastest = i;
        }
    }

    println!("kinetic {kinetic:.12e}");
    println!("potential {potential:.12e}");
    println!("position {position:.12e}");
    println!("fastest {fastest}");
}
