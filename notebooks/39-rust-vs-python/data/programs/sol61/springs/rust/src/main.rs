use std::{env, fs};

// Contiguous arrays let LLVM vectorize without changing arithmetic order.
#[inline(always)]
fn simulate(
    x: &mut [f64],
    v: &mut [f64],
    m: &[f64],
    k: &[f64],
    rest: &[f64],
    damping: &[f64],
    steps: usize,
    dt: f64,
    circumference: f64,
) {
    let n = x.len();
    let mut forces = vec![0.0; n + 1];
    for _ in 0..steps {
        for (((force, pair), &ki), &ri) in
            forces[1..n].iter_mut().zip(x.windows(2)).zip(k).zip(rest)
        {
            *force = ki * ((pair[1] - pair[0]) - ri);
        }
        forces[n] = k[n - 1] * (((x[0] + circumference) - x[n - 1]) - rest[n - 1]);
        forces[0] = forces[n];
        for (((((xi, vi), &mi), &ci), &right), &left) in x
            .iter_mut()
            .zip(v.iter_mut())
            .zip(m)
            .zip(damping)
            .zip(&forces[1..])
            .zip(&forces[..n])
        {
            let force = (right - left) - ci * *vi;
            *vi = *vi + dt * (force / mi);
            *xi = *xi + dt * *vi;
        }
    }
}

#[cfg(target_arch = "x86_64")]
#[target_feature(enable = "avx2")]
unsafe fn simulate_avx2(
    x: &mut [f64],
    v: &mut [f64],
    m: &[f64],
    k: &[f64],
    rest: &[f64],
    damping: &[f64],
    steps: usize,
    dt: f64,
    circumference: f64,
) {
    simulate(x, v, m, k, rest, damping, steps, dt, circumference);
}

fn main() {
    let path = env::args_os().nth(1).expect("input path required");
    let input = fs::read_to_string(path).expect("cannot read input");
    let mut tokens = input.split_ascii_whitespace();
    let n: usize = tokens.next().unwrap().parse().unwrap();
    let steps: usize = tokens.next().unwrap().parse().unwrap();
    let dt: f64 = tokens.next().unwrap().parse().unwrap();
    let circumference: f64 = tokens.next().unwrap().parse().unwrap();
    let mut x = Vec::with_capacity(n);
    let mut v = Vec::with_capacity(n);
    let mut m = Vec::with_capacity(n);
    let mut k = Vec::with_capacity(n);
    let mut rest = Vec::with_capacity(n);
    let mut damping = Vec::with_capacity(n);
    for _ in 0..n {
        x.push(tokens.next().unwrap().parse::<f64>().unwrap());
        v.push(tokens.next().unwrap().parse::<f64>().unwrap());
        m.push(tokens.next().unwrap().parse::<f64>().unwrap());
        k.push(tokens.next().unwrap().parse::<f64>().unwrap());
        rest.push(tokens.next().unwrap().parse::<f64>().unwrap());
        damping.push(tokens.next().unwrap().parse::<f64>().unwrap());
    }
    drop(input);

    #[cfg(target_arch = "x86_64")]
    if is_x86_feature_detected!("avx2") {
        // Detection guarantees the enabled instructions exist on this CPU.
        unsafe {
            simulate_avx2(
                &mut x,
                &mut v,
                &m,
                &k,
                &rest,
                &damping,
                steps,
                dt,
                circumference,
            );
        }
    } else {
        simulate(
            &mut x,
            &mut v,
            &m,
            &k,
            &rest,
            &damping,
            steps,
            dt,
            circumference,
        );
    }
    #[cfg(not(target_arch = "x86_64"))]
    simulate(
        &mut x,
        &mut v,
        &m,
        &k,
        &rest,
        &damping,
        steps,
        dt,
        circumference,
    );

    let mut kinetic = 0.0;
    let mut potential = 0.0;
    let mut position = 0.0;
    let mut fastest = 0;
    let mut speed = -1.0;
    for i in 0..n {
        kinetic += ((0.5 * m[i]) * v[i]) * v[i];
        let stretch = if i + 1 < n {
            (x[i + 1] - x[i]) - rest[i]
        } else {
            ((x[0] + circumference) - x[i]) - rest[i]
        };
        potential += ((0.5 * k[i]) * stretch) * stretch;
        position += x[i];
        let magnitude = v[i].abs();
        if magnitude > speed {
            speed = magnitude;
            fastest = i;
        }
    }
    println!(
        "kinetic {kinetic:.16e}\npotential {potential:.16e}\nposition {position:.16e}\nfastest {fastest}"
    );
}
