use std::fmt::Write as _;
use std::io::Write as _;

/// One simulation step: `out[i]` is the new value of the cell whose old value
/// is `cur[lr + i]`.  Walls hold 0, so a wall neighbour adds nothing and is
/// accounted for in the centre weight `coef` = 4 + k (k = walled neighbours).
/// Walls, sources and fully enclosed open cells (always 0) have `coef` 0 and
/// keep their value.
///
/// Values are at most 9000 < 2^14, so everything is done in 16-bit lanes:
/// `coef * mid` <= 7 * 9000 and the neighbour sum <= 4 * 9000 each fit, and
/// only their total (< 2^17) can overflow; the lost bit 16 becomes bit 13
/// after the division by 8.
#[inline(always)]
fn step_body(cur: &[u16], out: &mut [u16], coef: &[u16], lr: usize) {
    let n = out.len();
    let up = &cur[..n];
    let left = &cur[lr - 1..lr - 1 + n];
    let mid = &cur[lr..lr + n];
    let right = &cur[lr + 1..lr + 1 + n];
    let down = &cur[2 * lr..2 * lr + n];
    let coef = &coef[..n];
    for i in 0..n {
        let c = coef[i];
        let m = mid[i];
        let s1 = m.wrapping_mul(c);
        let s2 = up[i].wrapping_add(down[i]).wrapping_add(left[i]).wrapping_add(right[i]);
        let t = s1.wrapping_add(s2);
        let carry = (t < s1) as u16;
        let v = (t >> 3) | (carry << 13);
        // All ones where the cell is updated, 0 where it keeps its value.
        let upd = 0u16.wrapping_sub((c != 0) as u16);
        out[i] = (v & upd) | (m & !upd);
    }
}

#[cfg(target_arch = "x86_64")]
#[target_feature(enable = "avx2")]
unsafe fn step_avx2(cur: &[u16], out: &mut [u16], coef: &[u16], lr: usize) {
    step_body(cur, out, coef, lr)
}

fn main() {
    let path = std::env::args().nth(1).expect("input path");
    let data = std::fs::read(path).expect("read input");
    let mut tokens = data
        .split(|b| b.is_ascii_whitespace())
        .filter(|t| !t.is_empty());
    let mut num = || -> usize {
        std::str::from_utf8(tokens.next().unwrap()).unwrap().parse().unwrap()
    };
    let (h, w, s) = (num(), num(), num());
    drop(num);

    // Flat padded layout: row stride lr = w + 1 (one wall column shared by
    // neighbouring rows) and a wall row above and below.  Cell (r, c) is at
    // index (r + 1) * lr + c + 1.
    let lr = w + 1;
    let n = (h + 2) * lr;
    let mut kind = vec![b'#'; n];
    for r in 0..h {
        let row = tokens.next().unwrap();
        let base = (r + 1) * lr + 1;
        kind[base..base + w].copy_from_slice(&row[..w]);
    }
    let is_wall = |p: usize| kind[p] == b'#';

    // Interior range [lo, hi) between the pad rows.
    let lo = lr;
    let hi = n - lr;
    let m = hi - lo;
    let mut coef = vec![0u16; m];
    let mut a = vec![0u16; n];
    for p in lo..hi {
        match kind[p] {
            b'.' => {
                let k = is_wall(p - 1) as u16
                    + is_wall(p + 1) as u16
                    + is_wall(p - lr) as u16
                    + is_wall(p + lr) as u16;
                if k < 4 {
                    coef[p - lo] = 4 + k;
                }
            }
            b'#' => {}
            d => a[p] = 1000 * (d - b'0') as u16,
        }
    }
    let mut b = a.clone();

    #[cfg(target_arch = "x86_64")]
    let avx2 = std::is_x86_feature_detected!("avx2");
    #[cfg(not(target_arch = "x86_64"))]
    let avx2 = false;

    for _ in 0..s {
        let out = &mut b[lo..hi];
        if avx2 {
            #[cfg(target_arch = "x86_64")]
            unsafe {
                step_avx2(&a, out, &coef, lr)
            }
        } else {
            step_body(&a, out, &coef, lr);
        }
        std::mem::swap(&mut a, &mut b);
    }

    let mut total: i64 = 0;
    let mut chk: i64 = 0;
    let mut best: i64 = -1;
    let mut best_p = 0usize;
    for r in 0..h {
        let base = (r + 1) * lr + 1;
        for c in 0..w {
            let p = base + c;
            if kind[p] == b'.' {
                let v = a[p] as i64;
                total += v;
                chk += v * (r * w + c + 1) as i64;
                if v > best {
                    best = v;
                    best_p = p;
                }
            }
        }
    }
    let (r, c) = (best_p / lr - 1, best_p % lr - 1);
    let mut outs = String::new();
    write!(outs, "sum {total}\nmax {best} {r} {c}\nchecksum {chk}\n").unwrap();
    std::io::stdout().write_all(outs.as_bytes()).unwrap();
}
