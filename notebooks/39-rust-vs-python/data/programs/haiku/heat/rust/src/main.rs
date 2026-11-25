use std::io::Write;

// Cell kinds. Walls and the one-cell ring around the floor are 0.
const OPEN: u8 = 1;
const SOURCE: u8 = 2;

fn parse_usize(token: Option<&[u8]>) -> usize {
    std::str::from_utf8(token.expect("missing header field"))
        .expect("header is not UTF-8")
        .parse()
        .expect("header field is not a number")
}

// One update of every open cell. The grid is flat with stride W + 2, so the four
// neighbours of cell i are at i-1, i+1, i-stride and i+stride. Walls and sources store
// their fixed value, so a neighbour's stored value is already right for sources and 0 for
// walls. `coef` is 4 plus the number of walls around the cell, which covers the rule that
// a wall neighbour contributes the cell's own old value. `open` is -1 for open cells and 0
// otherwise, so the blend keeps walls and sources unchanged. Both buffers start equal and
// only open cells are written, so the non-open entries stay correct in both.
#[inline(always)]
fn step_body(cur: &[i32], nxt: &mut [i32], coef: &[i32], open: &[i32], stride: usize) {
    let (lo, hi) = (stride, cur.len() - stride);
    let it = nxt[lo..hi]
        .iter_mut()
        .zip(&cur[lo..hi])
        .zip(&cur[lo - 1..hi - 1])
        .zip(&cur[lo + 1..hi + 1])
        .zip(&cur[lo - stride..hi - stride])
        .zip(&cur[lo + stride..hi + stride])
        .zip(&coef[lo..hi])
        .zip(&open[lo..hi]);
    for (((((((out, &c), &l), &r), &u), &d), &k), &m) in it {
        let acc = (k * c + l + r + u + d) >> 3;
        *out = (acc & m) | (c & !m);
    }
}

#[inline(always)]
fn simulate_body(
    mut cur: Vec<i32>,
    mut nxt: Vec<i32>,
    coef: &[i32],
    open: &[i32],
    stride: usize,
    steps: usize,
) -> Vec<i32> {
    for _ in 0..steps {
        step_body(&cur, &mut nxt, coef, open, stride);
        std::mem::swap(&mut cur, &mut nxt);
    }
    cur
}

// Same code compiled with AVX2 enabled. It is chosen at run time, so the binary still runs
// on CPUs without AVX2.
#[cfg(target_arch = "x86_64")]
#[target_feature(enable = "avx2")]
unsafe fn simulate_avx2(
    cur: Vec<i32>,
    nxt: Vec<i32>,
    coef: &[i32],
    open: &[i32],
    stride: usize,
    steps: usize,
) -> Vec<i32> {
    simulate_body(cur, nxt, coef, open, stride, steps)
}

fn simulate(
    cur: Vec<i32>,
    nxt: Vec<i32>,
    coef: &[i32],
    open: &[i32],
    stride: usize,
    steps: usize,
) -> Vec<i32> {
    #[cfg(target_arch = "x86_64")]
    {
        if is_x86_feature_detected!("avx2") {
            // SAFETY: the CPU supports AVX2, as checked just above.
            return unsafe { simulate_avx2(cur, nxt, coef, open, stride, steps) };
        }
    }
    simulate_body(cur, nxt, coef, open, stride, steps)
}

fn main() {
    let path = std::env::args_os().nth(1).expect("usage: solution INPUT_PATH");
    let data = std::fs::read(&path).expect("cannot read input file");
    let mut tokens = data
        .split(|b| b.is_ascii_whitespace())
        .filter(|t| !t.is_empty());

    let h = parse_usize(tokens.next());
    let w = parse_usize(tokens.next());
    let steps = parse_usize(tokens.next());

    let stride = w + 2;
    let n = stride * (h + 2);
    let mut kind = vec![0u8; n];
    let mut heat = vec![0i32; n];
    for r in 0..h {
        let row = tokens.next().expect("missing grid row");
        let base = (r + 1) * stride + 1;
        for (c, &ch) in row.iter().take(w).enumerate() {
            match ch {
                b'.' => kind[base + c] = OPEN,
                b'1'..=b'9' => {
                    kind[base + c] = SOURCE;
                    heat[base + c] = 1000 * i32::from(ch - b'0');
                }
                _ => {}
            }
        }
    }

    let mut coef = vec![0i32; n];
    let mut open = vec![0i32; n];
    for i in stride..n - stride {
        if kind[i] == OPEN {
            let walls = [i - 1, i + 1, i - stride, i + stride]
                .iter()
                .filter(|&&j| kind[j] == 0)
                .count();
            coef[i] = 4 + walls as i32;
            open[i] = -1;
        }
    }

    let nxt = heat.clone();
    let cur = simulate(heat, nxt, &coef, &open, stride, steps);

    let (mut total, mut checksum) = (0i64, 0i64);
    let (mut best, mut best_r, mut best_c) = (-1i32, 0usize, 0usize);
    for r in 0..h {
        let base = (r + 1) * stride + 1;
        for c in 0..w {
            let i = base + c;
            if open[i] == 0 {
                continue;
            }
            let v = cur[i];
            total += i64::from(v);
            if v > best {
                best = v;
                best_r = r;
                best_c = c;
            }
            checksum += i64::from(v) * (r * w + c + 1) as i64;
        }
    }

    let stdout = std::io::stdout();
    let mut out = stdout.lock();
    writeln!(out, "sum {total}").unwrap();
    writeln!(out, "max {best} {best_r} {best_c}").unwrap();
    writeln!(out, "checksum {checksum}").unwrap();
}
