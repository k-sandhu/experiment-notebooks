use std::{env, fs};

fn main() {
    let data = fs::read(env::args_os().nth(1).expect("input path")).expect("read input");
    let mut tokens = data
        .split(|c| c.is_ascii_whitespace())
        .filter(|s| !s.is_empty());
    let h: usize = std::str::from_utf8(tokens.next().unwrap())
        .unwrap()
        .parse()
        .unwrap();
    let w: usize = std::str::from_utf8(tokens.next().unwrap())
        .unwrap()
        .parse()
        .unwrap();
    let steps: usize = std::str::from_utf8(tokens.next().unwrap())
        .unwrap()
        .parse()
        .unwrap();
    let stride = w + 2;
    let size = (h + 2) * stride;
    let mut cells = vec![b'#'; size];
    let mut old = vec![0u16; size];
    let mut fixed = Vec::new();
    let mut open = Vec::new();
    let mut has_source = false;
    for r in 0..h {
        let row = tokens.next().unwrap();
        let start = (r + 1) * stride + 1;
        cells[start..start + w].copy_from_slice(row);
        for (c, &cell) in row.iter().enumerate() {
            let i = start + c;
            match cell {
                b'.' => open.push((i, r * w + c)),
                b'#' => fixed.push((i, 0)),
                _ => {
                    let value = u16::from(cell - b'0') * 1000;
                    old[i] = value;
                    fixed.push((i, value));
                    has_source = true;
                }
            }
        }
    }
    if steps != 0 && has_source {
        let mut weights = vec![0u16; size];
        for &(i, _) in &open {
            weights[i] += u16::from(cells[i - stride] == b'#')
                + u16::from(cells[i + stride] == b'#')
                + u16::from(cells[i - 1] == b'#')
                + u16::from(cells[i + 1] == b'#');
        }
        let mut new = old.clone();
        for step in 0..steps {
            for r in 1..=h {
                let start = r * stride + 1;
                let centre = &old[start..start + w];
                let up = &old[start - stride..start - stride + w];
                let down = &old[start + stride..start + stride + w];
                let left = &old[start - 1..start - 1 + w];
                let right = &old[start + 1..start + 1 + w];
                let weight = &weights[start..start + w];
                let out = &mut new[start..start + w];
                for c in 0..w {
                    // The neighbour sum is at most 36,000. Splitting off
                    // half the centre keeps every intermediate within u16.
                    let neighbours = centre[c] * weight[c] + up[c] + down[c] + left[c] + right[c];
                    out[c] = (centre[c] >> 1) + ((neighbours + ((centre[c] & 1) << 2)) >> 3);
                }
            }
            for &(i, value) in &fixed {
                new[i] = value;
            }
            let converged = step & 31 == 31 && new == old;
            std::mem::swap(&mut old, &mut new);
            if converged {
                break;
            }
        }
    }

    let mut total = 0i64;
    let mut checksum = 0i64;
    let mut maximum = 0u16;
    let mut best = open[0].1;
    for &(i, pos) in &open {
        let value = old[i];
        total += i64::from(value);
        checksum += i64::from(value) * (pos as i64 + 1);
        if value > maximum {
            maximum = value;
            best = pos;
        }
    }
    println!(
        "sum {total}\nmax {maximum} {} {}\nchecksum {checksum}",
        best / w,
        best % w
    );
}
