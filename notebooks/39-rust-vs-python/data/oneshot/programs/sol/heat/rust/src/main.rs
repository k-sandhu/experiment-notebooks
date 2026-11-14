use std::{env, fs};

struct Run {
    start: usize,
    len: usize,
    original: usize,
}

fn step(
    current: &[u32],
    next: &mut [u32],
    weights: &[u32],
    runs: &[Run],
    stride: usize,
) {
    let src = current.as_ptr();
    let dst = next.as_mut_ptr();
    let weight = weights.as_ptr();

    for run in runs {
        let end = run.start + run.len;
        let mut p = run.start;

        // Every run contains only open cells inside the padded grid.
        unsafe {
            while p < end {
                let value = *src.add(p) * *weight.add(p)
                    + *src.add(p - stride)
                    + *src.add(p + stride)
                    + *src.add(p - 1)
                    + *src.add(p + 1);
                *dst.add(p) = value >> 3;
                p += 1;
            }
        }
    }
}

fn main() {
    let input = fs::read(env::args_os().nth(1).unwrap()).unwrap();
    let mut tokens = input
        .split(|b| b.is_ascii_whitespace())
        .filter(|token| !token.is_empty());

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
    let mut current = vec![0u32; size];
    let mut has_source = false;

    for r in 0..h {
        let row = tokens.next().unwrap();
        let base = (r + 1) * stride + 1;
        cells[base..base + w].copy_from_slice(row);

        for (c, &cell) in row.iter().enumerate() {
            if cell.is_ascii_digit() {
                current[base + c] = u32::from(cell - b'0') * 1000;
                has_source = true;
            }
        }
    }

    let mut weights = vec![0u32; size];
    let mut runs = Vec::new();

    for r in 0..h {
        let base = (r + 1) * stride + 1;
        let mut c = 0;

        while c < w {
            if cells[base + c] != b'.' {
                c += 1;
                continue;
            }

            let first = c;
            while c < w && cells[base + c] == b'.' {
                let p = base + c;
                weights[p] = 4
                    + u32::from(cells[p - stride] == b'#')
                    + u32::from(cells[p + stride] == b'#')
                    + u32::from(cells[p - 1] == b'#')
                    + u32::from(cells[p + 1] == b'#');
                c += 1;
            }

            runs.push(Run {
                start: base + first,
                len: c - first,
                original: r * w + first,
            });
        }
    }

    if has_source && steps != 0 {
        let mut next = current.clone();
        for _ in 0..steps {
            step(&current, &mut next, &weights, &runs, stride);
            std::mem::swap(&mut current, &mut next);
        }
    }

    let mut sum = 0i64;
    let mut checksum = 0i64;
    let mut maximum = -1i64;
    let mut best_index = 0usize;

    for run in &runs {
        for offset in 0..run.len {
            let value = i64::from(current[run.start + offset]);
            let index = run.original + offset;

            sum += value;
            checksum += value * (index as i64 + 1);

            if value > maximum {
                maximum = value;
                best_index = index;
            }
        }
    }

    println!(
        "sum {}\nmax {} {} {}\nchecksum {}",
        sum,
        maximum,
        best_index / w,
        best_index % w,
        checksum
    );
}
