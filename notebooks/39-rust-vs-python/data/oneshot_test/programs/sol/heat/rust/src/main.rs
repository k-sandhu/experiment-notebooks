use std::fs;

#[cfg(target_arch = "x86_64")]
use std::arch::x86_64::*;

fn read_usize(input: &[u8], pos: &mut usize) -> usize {
    while input[*pos].is_ascii_whitespace() {
        *pos += 1;
    }
    let mut value = 0usize;
    while *pos < input.len() && input[*pos].is_ascii_digit() {
        value = value * 10 + (input[*pos] - b'0') as usize;
        *pos += 1;
    }
    value
}

fn simulate_scalar(
    a: &mut [u16],
    b: &mut [u16],
    coefficients: &[u16],
    stride: usize,
    end: usize,
    steps: usize,
) -> bool {
    let mut current = a;
    let mut next = b;
    let mut in_second = false;

    for step in 0..steps {
        for i in stride..end {
            let coefficient = coefficients[i];
            next[i] = if coefficient == 0x8000 {
                current[i]
            } else {
                let old = current[i] as u32;
                let neighbors = current[i - stride] as u32
                    + current[i + stride] as u32
                    + current[i - 1] as u32
                    + current[i + 1] as u32;
                (((4 + coefficient as u32) * old + neighbors) >> 3) as u16
            };
        }

        std::mem::swap(&mut current, &mut next);
        in_second = !in_second;

        if step & 63 == 63 && current[..] == next[..] {
            break;
        }
    }

    in_second
}

#[cfg(target_arch = "x86_64")]
#[target_feature(enable = "avx2")]
unsafe fn simulate_avx2(
    a: &mut [u16],
    b: &mut [u16],
    coefficients: &[u16],
    stride: usize,
    end: usize,
    steps: usize,
) -> bool {
    unsafe {
        let mut current = a.as_mut_ptr();
        let mut next = b.as_mut_ptr();
        let second = next;
        let coefficients = coefficients.as_ptr();
        let vector_end = stride + ((end - stride) / 16) * 16;
        let len = a.len();

        for step in 0..steps {
            let mut i = stride;
            while i < vector_end {
                let old = _mm256_loadu_si256(current.add(i).cast());
                let coefficient = _mm256_loadu_si256(coefficients.add(i).cast());

                let up = _mm256_loadu_si256(current.add(i - stride).cast());
                let down = _mm256_loadu_si256(current.add(i + stride).cast());
                let left = _mm256_loadu_si256(current.add(i - 1).cast());
                let right = _mm256_loadu_si256(current.add(i + 1).cast());

                let neighbors =
                    _mm256_add_epi16(_mm256_add_epi16(up, down), _mm256_add_epi16(left, right));
                let reflected = _mm256_mullo_epi16(old, coefficient);
                let surrounding = _mm256_add_epi16(neighbors, reflected);

                // The surrounding sum is at most 36000 for an open cell.
                // floor((4*old + surrounding)/8)
                // = floor((2*old + floor(surrounding/2))/4).
                let value = _mm256_srli_epi16::<2>(_mm256_add_epi16(
                    _mm256_add_epi16(old, old),
                    _mm256_srli_epi16::<1>(surrounding),
                ));

                let fixed_mask = _mm256_srai_epi16::<15>(coefficient);
                let value = _mm256_blendv_epi8(value, old, fixed_mask);
                _mm256_storeu_si256(next.add(i).cast(), value);

                i += 16;
            }

            while i < end {
                let coefficient = *coefficients.add(i);
                let old = *current.add(i);
                *next.add(i) = if coefficient == 0x8000 {
                    old
                } else {
                    let neighbors = *current.add(i - stride) as u32
                        + *current.add(i + stride) as u32
                        + *current.add(i - 1) as u32
                        + *current.add(i + 1) as u32;
                    (((4 + coefficient as u32) * old as u32 + neighbors) >> 3) as u16
                };
                i += 1;
            }

            std::mem::swap(&mut current, &mut next);

            if step & 63 == 63
                && std::slice::from_raw_parts(current, len)
                    == std::slice::from_raw_parts(next, len)
            {
                break;
            }
        }

        current == second
    }
}

fn simulate(
    a: &mut [u16],
    b: &mut [u16],
    coefficients: &[u16],
    stride: usize,
    end: usize,
    steps: usize,
) -> bool {
    #[cfg(target_arch = "x86_64")]
    if is_x86_feature_detected!("avx2") {
        return unsafe { simulate_avx2(a, b, coefficients, stride, end, steps) };
    }

    simulate_scalar(a, b, coefficients, stride, end, steps)
}

fn main() {
    let path = std::env::args_os().nth(1).expect("missing input path");
    let input = fs::read(path).expect("cannot read input");

    let mut pos = 0;
    let h = read_usize(&input, &mut pos);
    let w = read_usize(&input, &mut pos);
    let steps = read_usize(&input, &mut pos);

    let stride = w + 2;
    let len = (h + 2) * stride;
    let end = (h + 1) * stride;

    let mut grid = vec![b'#'; len];
    let mut a = vec![0u16; len];
    let mut coefficients = vec![0x8000u16; len];
    let mut first_open = usize::MAX;
    let mut has_source = false;

    for r in 0..h {
        while input[pos].is_ascii_whitespace() {
            pos += 1;
        }

        let base = (r + 1) * stride + 1;
        grid[base..base + w].copy_from_slice(&input[pos..pos + w]);

        for c in 0..w {
            let ch = input[pos + c];
            if ch == b'.' {
                if first_open == usize::MAX {
                    first_open = r * w + c;
                }
            } else if ch.is_ascii_digit() {
                a[base + c] = (ch - b'0') as u16 * 1000;
                has_source = true;
            }
        }
        pos += w;
    }

    for r in 0..h {
        let base = (r + 1) * stride + 1;
        for c in 0..w {
            let i = base + c;
            if grid[i] == b'.' {
                coefficients[i] = (grid[i - stride] == b'#') as u16
                    + (grid[i + stride] == b'#') as u16
                    + (grid[i - 1] == b'#') as u16
                    + (grid[i + 1] == b'#') as u16;
            }
        }
    }
    drop(grid);
    drop(input);

    let mut b = vec![0u16; len];
    let in_second = steps != 0
        && has_source
        && simulate(&mut a, &mut b, &coefficients, stride, end, steps);
    let result = if in_second { &b } else { &a };

    let mut sum = 0i64;
    let mut checksum = 0i64;
    let mut maximum = 0u16;
    let mut best = first_open;

    for r in 0..h {
        let base = (r + 1) * stride + 1;
        let flat_base = r * w;
        for c in 0..w {
            let i = base + c;
            if coefficients[i] != 0x8000 {
                let value = result[i];
                let flat = flat_base + c;
                sum += value as i64;
                checksum += value as i64 * (flat as i64 + 1);
                if value > maximum {
                    maximum = value;
                    best = flat;
                }
            }
        }
    }

    println!(
        "sum {}\nmax {} {} {}\nchecksum {}",
        sum,
        maximum,
        best / w,
        best % w,
        checksum
    );
}
