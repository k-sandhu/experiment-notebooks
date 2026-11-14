use std::env;
use std::fs;
use std::io::{self, Write};
use std::str::SplitAsciiWhitespace;

#[inline]
fn next_f64(tokens: &mut SplitAsciiWhitespace<'_>) -> f64 {
    tokens.next().unwrap().parse::<f64>().unwrap()
}

fn main() {
    let path = env::args_os().nth(1).unwrap();
    let input = fs::read_to_string(path).unwrap();
    let mut tokens = input.split_ascii_whitespace();

    let n: usize = tokens.next().unwrap().parse().unwrap();
    let steps: usize = tokens.next().unwrap().parse().unwrap();
    let dt = next_f64(&mut tokens);
    let circumference = next_f64(&mut tokens);

    let mut x = Vec::with_capacity(n);
    let mut v = Vec::with_capacity(n);
    let mut m = Vec::with_capacity(n);
    let mut k = Vec::with_capacity(n);
    let mut r = Vec::with_capacity(n);
    let mut c = Vec::with_capacity(n);

    for _ in 0..n {
        x.push(next_f64(&mut tokens));
        v.push(next_f64(&mut tokens));
        m.push(next_f64(&mut tokens));
        k.push(next_f64(&mut tokens));
        r.push(next_f64(&mut tokens));
        c.push(next_f64(&mut tokens));
    }

    let last = n - 1;

    // force[i + 1] holds spring i's force; force[0] duplicates the last.
    let mut force = vec![0.0_f64; n + 1];

    for _ in 0..steps {
        let stretch = ((x[0] + circumference) - x[last]) - r[last];
        let closing_force = k[last] * stretch;
        force[0] = closing_force;
        force[n] = closing_force;

        for ((out, positions), (&stiffness, &rest)) in force[1..n]
            .iter_mut()
            .zip(x.windows(2))
            .zip(k[..last].iter().zip(r[..last].iter()))
        {
            let stretch = (positions[1] - positions[0]) - rest;
            *out = stiffness * stretch;
        }

        for (((position, velocity), (&mass, &damping)), springs) in x
            .iter_mut()
            .zip(v.iter_mut())
            .zip(m.iter().zip(c.iter()))
            .zip(force.windows(2))
        {
            let net_force = (springs[1] - springs[0]) - (damping * *velocity);
            let new_velocity = *velocity + dt * (net_force / mass);
            *velocity = new_velocity;
            *position = *position + dt * new_velocity;
        }
    }

    let mut kinetic = 0.0_f64;
    let mut potential = 0.0_f64;
    let mut position_sum = 0.0_f64;
    let mut fastest = 0_usize;
    let mut greatest_speed = v[0].abs();

    for i in 0..n {
        kinetic += ((0.5 * m[i]) * v[i]) * v[i];
        position_sum += x[i];

        let stretch = if i == last {
            ((x[0] + circumference) - x[i]) - r[i]
        } else {
            (x[i + 1] - x[i]) - r[i]
        };
        potential += ((0.5 * k[i]) * stretch) * stretch;

        let speed = v[i].abs();
        if speed > greatest_speed {
            greatest_speed = speed;
            fastest = i;
        }
    }

    let stdout = io::stdout();
    let mut output = io::BufWriter::new(stdout.lock());
    writeln!(output, "kinetic {:.16e}", kinetic).unwrap();
    writeln!(output, "potential {:.16e}", potential).unwrap();
    writeln!(output, "position {:.16e}", position_sum).unwrap();
    writeln!(output, "fastest {}", fastest).unwrap();
}
