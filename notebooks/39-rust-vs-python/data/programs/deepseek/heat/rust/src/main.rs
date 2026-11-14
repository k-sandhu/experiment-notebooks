use std::fmt::Write as FmtWrite;
use std::fs;
use std::io::Write;

#[inline]
fn parse_num(b: &[u8], i: &mut usize) -> usize {
    while *i < b.len() && (b[*i] < b'0' || b[*i] > b'9') {
        *i += 1;
    }
    let mut x = 0usize;
    while *i < b.len() && b[*i] >= b'0' && b[*i] <= b'9' {
        x = x * 10 + (b[*i] - b'0') as usize;
        *i += 1;
    }
    x
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let data = fs::read(&args[1]).expect("read input");

    let mut p = 0usize;
    let h = parse_num(&data, &mut p);
    let w = parse_num(&data, &mut p);
    let s = parse_num(&data, &mut p);
    while p < data.len() && data[p] != b'\n' {
        p += 1;
    }
    p += 1;

    // One-cell zero border around the grid simplifies the neighbour lookups.
    let stride = w + 2;
    let size = (h + 2) * stride;
    let mut a = vec![0i32; size];
    let mut b = vec![0i32; size];
    let mut coef = vec![0i32; size];
    let mut wallmask = vec![false; size];
    let mut srcs: Vec<(usize, i32)> = Vec::with_capacity(64);
    let mut walls: Vec<usize> = Vec::new();
    let mut open: Vec<usize> = Vec::with_capacity(h * w);

    for r in 0..h {
        while p < data.len() && (data[p] == b'\n' || data[p] == b'\r') {
            p += 1;
        }
        let base = (r + 1) * stride + 1;
        for c in 0..w {
            let ch = data[p];
            p += 1;
            let i = base + c;
            if ch == b'#' {
                wallmask[i] = true;
                walls.push(i);
            } else if ch == b'.' {
                open.push(i);
            } else {
                let v = (ch - b'0') as i32 * 1000;
                a[i] = v;
                srcs.push((i, v));
            }
        }
    }

    // coef = 4 + number of neighbours that are walls or outside the grid;
    // such a neighbour contributes the cell's own old value instead.
    for r in 0..h {
        let row = (r + 1) * stride;
        for c in 0..w {
            let i = row + 1 + c;
            let mut miss = 0i32;
            if r == 0 || wallmask[i - stride] {
                miss += 1;
            }
            if r + 1 == h || wallmask[i + stride] {
                miss += 1;
            }
            if c == 0 || wallmask[i - 1] {
                miss += 1;
            }
            if c + 1 == w || wallmask[i + 1] {
                miss += 1;
            }
            coef[i] = 4 + miss;
        }
    }

    for _ in 0..s {
        for r in 1..=h {
            let row = r * stride;
            unsafe {
                let mut i = row + 1;
                let end = row + 1 + w;
                while i < end {
                    *b.get_unchecked_mut(i) = (*a.get_unchecked(i) * *coef.get_unchecked(i)
                        + *a.get_unchecked(i - 1)
                        + *a.get_unchecked(i + 1)
                        + *a.get_unchecked(i - stride)
                        + *a.get_unchecked(i + stride))
                        >> 3;
                    i += 1;
                }
            }
        }
        for &(si, sv) in srcs.iter() {
            b[si] = sv;
        }
        for &wi in walls.iter() {
            b[wi] = 0;
        }
        std::mem::swap(&mut a, &mut b);
    }

    let mut total: i64 = 0;
    let mut checksum: i64 = 0;
    let mut best: i32 = -1;
    let mut best_i: usize = 0;
    for &i in open.iter() {
        let val = unsafe { *a.get_unchecked(i) };
        total += val as i64;
        let r = i / stride - 1;
        let c = i % stride - 1;
        let flat = r * w + c;
        checksum += val as i64 * (flat as i64 + 1);
        if val > best {
            best = val;
            best_i = flat;
        }
    }

    let mut out = String::with_capacity(80);
    let _ = writeln!(out, "sum {}", total);
    let _ = writeln!(out, "max {} {} {}", best, best_i / w, best_i % w);
    let _ = writeln!(out, "checksum {}", checksum);
    let stdout = std::io::stdout();
    let mut lock = stdout.lock();
    let _ = lock.write_all(out.as_bytes());
}
