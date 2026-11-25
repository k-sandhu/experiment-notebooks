use std::io::Write;

fn main() {
    let path = std::env::args().nth(1).expect("input path");
    let data = std::fs::read(path).expect("read input");
    let mut it = data.split(|b| b.is_ascii_whitespace()).filter(|t| !t.is_empty());
    let mut num = || -> usize {
        std::str::from_utf8(it.next().unwrap()).unwrap().parse().unwrap()
    };
    let h = num();
    let w = num();
    let steps = num();
    let rows: Vec<&[u8]> = (0..h).map(|_| it.next().unwrap()).collect();

    let wp = w + 2;
    let n = (h + 2) * wp;
    // cur holds values (walls and padding are 0). For each cell:
    // new = (((8 - open_neighbours) * old + sum of neighbour values) >> 3) & mask | fixed
    let mut cur = vec![0i32; n];
    let mut coef = vec![0i32; n];
    let mut mask = vec![0i32; n];
    let mut fixed = vec![0i32; n];
    let open = |r: isize, c: isize| -> bool {
        r >= 0 && c >= 0 && (r as usize) < h && (c as usize) < w && rows[r as usize][c as usize] != b'#'
    };
    for r in 0..h {
        for c in 0..w {
            let ch = rows[r][c];
            if ch == b'#' {
                continue;
            }
            let i = (r + 1) * wp + c + 1;
            if ch.is_ascii_digit() && ch != b'0' {
                let v = 1000 * (ch - b'0') as i32;
                cur[i] = v;
                fixed[i] = v;
            } else {
                mask[i] = -1;
                let (ri, ci) = (r as isize, c as isize);
                let cnt = open(ri - 1, ci) as i32
                    + open(ri + 1, ci) as i32
                    + open(ri, ci - 1) as i32
                    + open(ri, ci + 1) as i32;
                coef[i] = 8 - cnt;
            }
        }
    }
    let mut nxt = vec![0i32; n];
    for _ in 0..steps {
        for r in 1..=h {
            let base = r * wp + 1;
            let o = &cur[base..base + w];
            let up = &cur[base - wp..base - wp + w];
            let dn = &cur[base + wp..base + wp + w];
            let lf = &cur[base - 1..base - 1 + w];
            let rt = &cur[base + 1..base + 1 + w];
            let cf = &coef[base..base + w];
            let mk = &mask[base..base + w];
            let fx = &fixed[base..base + w];
            let out = &mut nxt[base..base + w];
            for j in 0..w {
                let s = cf[j] * o[j] + up[j] + dn[j] + lf[j] + rt[j];
                out[j] = ((s >> 3) & mk[j]) | fx[j];
            }
        }
        std::mem::swap(&mut cur, &mut nxt);
    }

    let mut total: i64 = 0;
    let mut best: i64 = -1;
    let (mut br, mut bc) = (0usize, 0usize);
    let mut checksum: i64 = 0;
    for r in 0..h {
        for c in 0..w {
            if rows[r][c] != b'.' {
                continue;
            }
            let v = cur[(r + 1) * wp + c + 1] as i64;
            total += v;
            if v > best {
                best = v;
                br = r;
                bc = c;
            }
            checksum += v * (r * w + c + 1) as i64;
        }
    }
    let out = std::io::stdout();
    let mut out = out.lock();
    writeln!(out, "sum {}\nmax {} {} {}\nchecksum {}", total, best, br, bc, checksum).unwrap();
}
