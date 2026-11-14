use std::io::Write;

fn parse_num(t: &[u8]) -> usize {
    let mut n: usize = 0;
    for &b in t {
        if b.is_ascii_digit() {
            n = n * 10 + (b - b'0') as usize;
        }
    }
    n
}

fn main() {
    let path = match std::env::args().nth(1) {
        Some(p) => p,
        None => {
            eprintln!("usage: solution INPUT_PATH");
            std::process::exit(1);
        }
    };
    let data = match std::fs::read(&path) {
        Ok(d) => d,
        Err(e) => {
            eprintln!("cannot read {}: {}", path, e);
            std::process::exit(1);
        }
    };

    let mut tokens = data
        .split(|b| b.is_ascii_whitespace())
        .filter(|t| !t.is_empty());

    let h = parse_num(tokens.next().unwrap_or_default());
    let w = parse_num(tokens.next().unwrap_or_default());
    let s = parse_num(tokens.next().unwrap_or_default());

    // Padded grid: one-cell border of walls around the real grid.
    let stride = w + 2;
    let total = (h + 2) * stride;

    // kind: 0 = wall / outside, 1 = open cell, 2 = heat source
    let mut kind = vec![0u8; total];
    // Initial values: sources hold 1000*d, everything else 0.
    let mut val = vec![0i32; total];

    for r in 0..h {
        let row: &[u8] = tokens.next().unwrap_or_default();
        for c in 0..w {
            let b = if c < row.len() { row[c] } else { b'#' };
            let i = (r + 1) * stride + c + 1;
            match b {
                b'.' => kind[i] = 1,
                b'1'..=b'9' => {
                    kind[i] = 2;
                    val[i] = 1000 * (b - b'0') as i32;
                }
                _ => {}
            }
        }
    }

    // List of open cells in row-major order, each with its weight a = 4 + (number of
    // neighbours that are walls/outside). A wall/outside neighbour contributes the cell's
    // own old value, so the update is (a*old + sum of valid neighbour values) >> 3.
    // Walls and outside cells hold 0, so summing all four neighbours yields exactly the
    // sum over valid neighbours (open cells and sources).
    let mut open: Vec<(u32, i32)> = Vec::with_capacity(h * w);
    for r in 1..=h {
        for c in 1..=w {
            let i = r * stride + c;
            if kind[i] != 1 {
                continue;
            }
            let mut inv = 0i32;
            for j in [i - 1, i + 1, i - stride, i + stride] {
                if kind[j] == 0 {
                    inv += 1;
                }
            }
            open.push((i as u32, 4 + inv));
        }
    }

    // Both buffers start identical; sources and walls are never written, so they stay
    // correct in both. Only open cells are rewritten each step.
    let mut cur = val;
    let mut nxt = cur.clone();

    for _ in 0..s {
        for &(i, a) in &open {
            let i = i as usize;
            // SAFETY: open cells lie strictly inside the padded grid, so i-1, i+1,
            // i-stride and i+stride are all valid indices into `cur` / `nxt`.
            unsafe {
                let o = *cur.get_unchecked(i);
                let sum = *cur.get_unchecked(i - 1)
                    + *cur.get_unchecked(i + 1)
                    + *cur.get_unchecked(i - stride)
                    + *cur.get_unchecked(i + stride);
                *nxt.get_unchecked_mut(i) = (a * o + sum) >> 3;
            }
        }
        std::mem::swap(&mut cur, &mut nxt);
    }

    let mut t: i64 = 0;
    let mut best: i32 = -1;
    let mut br: usize = 0;
    let mut bc: usize = 0;
    let mut k: i64 = 0;

    for &(i, _) in &open {
        let i = i as usize;
        let v = cur[i];
        let r = i / stride - 1;
        let c = i % stride - 1;
        t += v as i64;
        if v > best {
            best = v;
            br = r;
            bc = c;
        }
        k += v as i64 * ((r * w + c + 1) as i64);
    }
    if best < 0 {
        best = 0;
    }

    let stdout = std::io::stdout();
    let mut out = stdout.lock();
    let _ = writeln!(out, "sum {}", t);
    let _ = writeln!(out, "max {} {} {}", best, br, bc);
    let _ = writeln!(out, "checksum {}", k);
}
