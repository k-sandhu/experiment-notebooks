use std::io::Write;

fn main() {
    let path = std::env::args().nth(1).expect("usage: solution INPUT");
    let data = std::fs::read(path).expect("cannot read input");
    let mut lines = data.split(|&b| b == b'\n');
    let header = std::str::from_utf8(lines.next().unwrap()).unwrap();
    let mut it = header.split_ascii_whitespace().map(|t| t.parse::<usize>().unwrap());
    let (h, w, s) = (it.next().unwrap(), it.next().unwrap(), it.next().unwrap());

    // Padded layout: a wall row above and below, and one wall column after
    // each row (also serving as the left pad of the next row). Stride p.
    let p = w + 1;
    let total = (h + 2) * p;
    let mut cell = vec![b'#'; total];
    for r in 0..h {
        let row = lines.next().unwrap().trim_ascii();
        let base = (r + 1) * p;
        cell[base..base + w].copy_from_slice(&row[..w]);
    }

    let n = h * p;
    let lo = p;
    // Values stay in [0, 9000]. With E = sum of the four neighbour terms
    // (own value for wall neighbours), E <= 36000 and
    // (4*old + E) / 8 == (old + E / 4) / 2 (floor), so everything fits u16.
    let wall = |i: usize| (cell[i] == b'#') as u16;
    // Per interior cell: wall-neighbour count, keep mask, fixed value.
    let mut k = vec![0u16; n];
    let mut keep = vec![0u16; n];
    let mut fixed = vec![0u16; n];
    let mut a = vec![0u16; total];
    for j in 0..n {
        let i = lo + j;
        match cell[i] {
            b'.' => {
                k[j] = wall(i - p) + wall(i + p) + wall(i - 1) + wall(i + 1);
                keep[j] = u16::MAX;
            }
            b'#' => {}
            d => {
                fixed[j] = 1000 * (d - b'0') as u16;
                a[i] = fixed[j];
            }
        }
    }
    let mut b = a.clone();

    for _ in 0..s {
        let up = &a[lo - p..lo - p + n];
        let down = &a[lo + p..lo + p + n];
        let left = &a[lo - 1..lo - 1 + n];
        let right = &a[lo + 1..lo + 1 + n];
        let mid = &a[lo..lo + n];
        let out = &mut b[lo..lo + n];
        for j in 0..n {
            let e = k[j] * mid[j] + up[j] + down[j] + left[j] + right[j];
            out[j] = (((mid[j] + (e >> 2)) >> 1) & keep[j]) | fixed[j];
        }
        std::mem::swap(&mut a, &mut b);
    }

    let mut sum: i64 = 0;
    let mut chk: i64 = 0;
    let mut best: Option<(u16, usize, usize)> = None;
    for r in 0..h {
        let base = (r + 1) * p;
        for c in 0..w {
            if cell[base + c] != b'.' {
                continue;
            }
            let v = a[base + c];
            sum += v as i64;
            chk += v as i64 * (r * w + c + 1) as i64;
            if best.is_none_or(|(bv, _, _)| v > bv) {
                best = Some((v, r, c));
            }
        }
    }
    let (bv, br, bc) = best.unwrap();
    let mut out = std::io::stdout().lock();
    write!(out, "sum {sum}\nmax {bv} {br} {bc}\nchecksum {chk}\n").unwrap();
}
