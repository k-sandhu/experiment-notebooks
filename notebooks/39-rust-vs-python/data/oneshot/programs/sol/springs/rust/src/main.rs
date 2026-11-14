use std::fs;
use std::io::{self, Write};

fn main() {
    let path = std::env::args_os().nth(1).unwrap();
    let input = fs::read_to_string(path).unwrap();
    let mut tokens = input.split_ascii_whitespace();

    let n: usize = tokens.next().unwrap().parse().unwrap();
    let steps: usize = tokens.next().unwrap().parse().unwrap();
    let dt: f64 = tokens.next().unwrap().parse().unwrap();
    let circumference: f64 = tokens.next().unwrap().parse().unwrap();

    let mut x = Vec::<f64>::with_capacity(n);
    let mut v = Vec::<f64>::with_capacity(n);
    let mut m = Vec::<f64>::with_capacity(n);
    let mut k = Vec::<f64>::with_capacity(n);
    let mut r = Vec::<f64>::with_capacity(n);
    let mut c = Vec::<f64>::with_capacity(n);

    for _ in 0..n {
        x.push(tokens.next().unwrap().parse().unwrap());
        v.push(tokens.next().unwrap().parse().unwrap());
        m.push(tokens.next().unwrap().parse().unwrap());
        k.push(tokens.next().unwrap().parse().unwrap());
        r.push(tokens.next().unwrap().parse().unwrap());
        c.push(tokens.next().unwrap().parse().unwrap());
    }

    // forces[i + 1] holds spring i's force; forces[0] duplicates the last.
    let mut forces = vec![0.0_f64; n + 1];

    for _ in 0..steps {
        for (((force, (&current, &next)), &stiffness), &rest) in forces[1..n]
            .iter_mut()
            .zip(x[..n - 1].iter().zip(x[1..].iter()))
            .zip(k.iter())
            .zip(r.iter())
        {
            let stretch = (next - current) - rest;
            *force = stiffness * stretch;
        }

        let last_stretch = ((x[0] + circumference) - x[n - 1]) - r[n - 1];
        let last_force = k[n - 1] * last_stretch;
        forces[n] = last_force;
        forces[0] = last_force;

        for ((((position, velocity), &mass), &damping), (&right, &left)) in x
            .iter_mut()
            .zip(v.iter_mut())
            .zip(m.iter())
            .zip(c.iter())
            .zip(forces[1..].iter().zip(forces[..n].iter()))
        {
            let net_force = (right - left) - (damping * *velocity);
            *velocity = *velocity + dt * (net_force / mass);
            *position = *position + dt * *velocity;
        }
    }

    let mut kinetic = 0.0_f64;
    let mut potential = 0.0_f64;
    let mut position_sum = 0.0_f64;
    let mut fastest = 0_usize;
    let mut fastest_speed = v[0].abs();

    for i in 0..n {
        kinetic += ((0.5 * m[i]) * v[i]) * v[i];
        position_sum += x[i];

        let speed = v[i].abs();
        if speed > fastest_speed {
            fastest_speed = speed;
            fastest = i;
        }
    }

    for i in 0..n - 1 {
        let stretch = (x[i + 1] - x[i]) - r[i];
        potential += ((0.5 * k[i]) * stretch) * stretch;
    }

    let stretch = ((x[0] + circumference) - x[n - 1]) - r[n - 1];
    potential += ((0.5 * k[n - 1]) * stretch) * stretch;

    let stdout = io::stdout();
    let mut output = io::BufWriter::new(stdout.lock());
    writeln!(output, "kinetic {:.16e}", kinetic).unwrap();
    writeln!(output, "potential {:.16e}", potential).unwrap();
    writeln!(output, "position {:.16e}", position_sum).unwrap();
    writeln!(output, "fastest {}", fastest).unwrap();
}
