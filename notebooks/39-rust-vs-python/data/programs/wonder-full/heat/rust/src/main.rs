use std::env;
use std::fs;
use std::process::ExitCode;

fn main() -> ExitCode {
    let path = match env::args_os().nth(1) {
        Some(p) => p,
        None => return ExitCode::FAILURE,
    };
    let data = match fs::read(&path) {
        Ok(d) => d,
        Err(_) => return ExitCode::FAILURE,
    };

    // Parse H W S from the first line.
    let mut nums = [0usize; 3];
    let mut ni = 0usize;
    let mut i = 0usize;
    while i < data.len() && ni < 3 {
        let b = data[i];
        if b.is_ascii_digit() {
            let mut v: usize = 0;
            while i < data.len() && data[i].is_ascii_digit() {
                v = v * 10 + (data[i] - b'0') as usize;
                i += 1;
            }
            nums[ni] = v;
            ni += 1;
        } else {
            i += 1;
            if b == b'\n' && ni == 3 {
                break;
            }
        }
    }
    // Skip to just after the first newline.
    while i < data.len() && data[i] != b'\n' {
        i += 1;
    }
    if i < data.len() {
        i += 1;
    }
    let (h, w, steps) = (nums[0], nums[1], nums[2]);

    // Grid characters, ignoring any line-ending bytes.
    let mut cells: Vec<u8> = Vec::with_capacity(h * w);
    for &b in &data[i..] {
        if b == b'.' || b == b'#' || b.is_ascii_digit() {
            cells.push(b);
            if cells.len() == h * w {
                break;
            }
        }
    }

    let wp = w + 2;
    let hp = h + 2;
    let n = wp * hp;

    let mut cur = vec![0i32; n];
    let mut nxt = vec![0i32; n];
    let mut coeff = vec![4i32; n];
    // (padded flat index, fixed value) for walls (0) and sources.
    let mut nonopen: Vec<(u32, i32)> = Vec::new();

    // Wall-or-outside test in the unpadded grid.
    let is_block = |r: isize, c: isize, cells: &[u8]| -> bool {
        if r < 0 || c < 0 || r >= h as isize || c >= w as isize {
            true
        } else {
            cells[r as usize * w + c as usize] == b'#'
        }
    };

    for r in 0..h {
        for c in 0..w {
            let ch = cells[r * w + c];
            let p = (r + 1) * wp + (c + 1);
            if ch == b'.' {
                let mut k = 4i32;
                if is_block(r as isize - 1, c as isize, &cells) {
                    k += 1;
                }
                if is_block(r as isize + 1, c as isize, &cells) {
                    k += 1;
                }
                if is_block(r as isize, c as isize - 1, &cells) {
                    k += 1;
                }
                if is_block(r as isize, c as isize + 1, &cells) {
                    k += 1;
                }
                coeff[p] = k;
            } else if ch == b'#' {
                nonopen.push((p as u32, 0));
            } else {
                let v = 1000 * (ch - b'0') as i32;
                cur[p] = v;
                nonopen.push((p as u32, v));
            }
        }
    }

    // Stencil steps. Walls hold 0 in `cur`, so a wall neighbour contributes
    // nothing through the neighbour sum and `coeff` (4 + wall count) makes
    // it contribute the cell's own value instead. Padded border is 0 and
    // counts as wall via coeff. All values stay in 0..=9000, sums <= 72000.
    for _ in 0..steps {
        for r in 1..=h {
            let base = r * wp;
            let up = &cur[base - wp + 1..base - wp + 1 + w];
            let mid = &cur[base + 1..base + 1 + w];
            let down = &cur[base + wp + 1..base + wp + 1 + w];
            let left = &cur[base..base + w];
            let right = &cur[base + 2..base + 2 + w];
            let cf = &coeff[base + 1..base + 1 + w];
            let out = &mut nxt[base + 1..base + 1 + w];
            for j in 0..w {
                out[j] = (cf[j] * mid[j] + up[j] + down[j] + left[j] + right[j]) >> 3;
            }
        }
        for &(p, v) in &nonopen {
            nxt[p as usize] = v;
        }
        if cur == nxt {
            break;
        }
        std::mem::swap(&mut cur, &mut nxt);
    }
    // `cur` holds the final state: either the loop swapped it in, or it
    // broke out because `nxt` was identical to it (a fixed point).

    let mut sum: i64 = 0;
    let mut checksum: i64 = 0;
    let mut best: i32 = -1;
    let mut best_r = 0usize;
    let mut best_c = 0usize;
    for r in 0..h {
        let base = (r + 1) * wp + 1;
        let idx_base = (r * w) as i64;
        for c in 0..w {
            if cells[r * w + c] == b'.' {
                let v = cur[base + c] as i64;
                sum += v;
                checksum += v * (idx_base + c as i64 + 1);
                if cur[base + c] > best {
                    best = cur[base + c];
                    best_r = r;
                    best_c = c;
                }
            }
        }
    }

    print!("sum {sum}\nmax {best} {best_r} {best_c}\nchecksum {checksum}\n");
    ExitCode::SUCCESS
}
