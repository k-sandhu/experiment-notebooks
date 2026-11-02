use std::{env, fs};

// Contiguous input/output slices let LLVM vectorize this simultaneous stencil.
#[inline(always)]
fn simulate(a: &mut Vec<u32>, b: &mut Vec<u32>, weights: &[u32], stride: usize, steps: usize) {
    let n = weights.len();
    for step in 0..steps {
        let center = &a[stride..stride + n];
        let up = &a[..n];
        let down = &a[2 * stride..2 * stride + n];
        let left = &a[stride - 1..stride - 1 + n];
        let right = &a[stride + 1..stride + 1 + n];
        let out = &mut b[stride..stride + n];
        for i in 0..n {
            out[i] = if weights[i] != 0 {
                (center[i] * weights[i] + up[i] + down[i] + left[i] + right[i]) >> 3
            } else {
                center[i]
            };
        }
        std::mem::swap(a, b);
        // Equality after one complete step proves that all future steps agree.
        // Check occasionally to keep the regular stencil loop inexpensive.
        if step & 31 == 0 && a == b {
            break;
        }
    }
}

#[cfg(target_arch = "x86_64")]
#[target_feature(enable = "avx2")]
unsafe fn simulate_avx2(
    a: &mut Vec<u32>,
    b: &mut Vec<u32>,
    weights: &[u32],
    stride: usize,
    steps: usize,
) {
    simulate(a, b, weights, stride, steps);
}

fn main() {
    let input = fs::read(env::args_os().nth(1).expect("input path required")).expect("read input");
    let mut tokens = input
        .split(|c| c.is_ascii_whitespace())
        .filter(|s| !s.is_empty());
    let mut number = || -> usize {
        tokens
            .next()
            .unwrap()
            .iter()
            .fold(0, |n, &c| n * 10 + (c - b'0') as usize)
    };
    let h = number();
    let w = number();
    let steps = number();
    let stride = w + 2;
    let size = (h + 2) * stride;
    let mut cells = vec![b'#'; size];
    let mut a = vec![0u32; size];
    let mut has_source = false;
    for r in 0..h {
        let row = tokens.next().unwrap();
        let start = (r + 1) * stride + 1;
        cells[start..start + w].copy_from_slice(row);
        for (c, &ch) in row.iter().enumerate() {
            if ch.is_ascii_digit() {
                a[start + c] = (ch - b'0') as u32 * 1000;
                has_source = true;
            }
        }
    }
    let mut weights = vec![0u32; h * stride];
    for r in 0..h {
        for c in 0..w {
            let i = (r + 1) * stride + c + 1;
            if cells[i] == b'.' {
                weights[i - stride] = 4
                    + u32::from(cells[i - stride] == b'#')
                    + u32::from(cells[i + stride] == b'#')
                    + u32::from(cells[i - 1] == b'#')
                    + u32::from(cells[i + 1] == b'#');
            }
        }
    }
    if has_source && steps != 0 {
        let mut b = a.clone();
        #[cfg(target_arch = "x86_64")]
        if std::is_x86_feature_detected!("avx2") {
            // The runtime check guarantees AVX2 support; indexing remains safe.
            unsafe { simulate_avx2(&mut a, &mut b, &weights, stride, steps) };
        } else {
            simulate(&mut a, &mut b, &weights, stride, steps);
        }
        #[cfg(not(target_arch = "x86_64"))]
        simulate(&mut a, &mut b, &weights, stride, steps);
    }
    let mut total = 0i64;
    let mut checksum = 0i64;
    let mut maximum = None;
    let mut best = (0, 0);
    for r in 0..h {
        for c in 0..w {
            let i = (r + 1) * stride + c + 1;
            if cells[i] == b'.' {
                let value = a[i] as i64;
                total += value;
                checksum += value * (r * w + c + 1) as i64;
                if maximum.is_none_or(|m| value > m) {
                    maximum = Some(value);
                    best = (r, c);
                }
            }
        }
    }
    println!(
        "sum {total}\nmax {} {} {}\nchecksum {checksum}",
        maximum.unwrap(),
        best.0,
        best.1
    );
}
