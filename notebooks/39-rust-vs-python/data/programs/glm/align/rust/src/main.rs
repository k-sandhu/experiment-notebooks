use std::env;
use std::fs;
use std::io::Write;

/// Integer type used for DP cells. Values of D[i][j] are bounded by
/// (n + m) * max_cost, so i32 suffices for reasonable inputs; i64 is the
/// fallback for very long strings.
trait Cell: Copy + std::ops::Add<Output = Self> + PartialOrd {
    fn zero() -> Self;
}

impl Cell for i32 {
    fn zero() -> Self {
        0
    }
}

impl Cell for i64 {
    fn zero() -> Self {
        0
    }
}

/// Weighted edit distance. Rows run over `s`, columns over `t`.
/// The sequential dependency cur[j-1] -> cur[j] is carried in the register
/// variable `left` (never stored/reloaded), giving a 2-cycle chain per cell:
/// an add and a min, with the other two min terms computed in parallel.
fn solve<C: Cell>(
    s: &[u8],
    t: &[u8],
    lut: &[usize; 256],
    sub: &[Vec<C>],
    ins: &[C],
    del: &[C],
) -> C {
    let m = t.len();
    let mut ti = vec![0usize; m];
    let mut insrow = Vec::with_capacity(m);
    for (j, &b) in t.iter().enumerate() {
        let k = lut[b as usize];
        ti[j] = k;
        insrow.push(ins[k]);
    }
    // Row 0: D[0][j] = sum of ins[t_1..t_j]
    let mut pin: Vec<C> = Vec::with_capacity(m + 1);
    pin.push(C::zero());
    let mut acc = C::zero();
    for &c in &insrow {
        acc = acc + c;
        pin.push(acc);
    }
    let mut prev = pin;
    let mut cur = vec![C::zero(); m + 1];
    for &b in s {
        let k = lut[b as usize];
        let d = del[k];
        let subrow = &sub[k];
        let mut left = prev[0] + d;
        cur[0] = left;
        // cur[j] = min(prev[j] + d, prev[j-1] + sub[s_i][t_j], cur[j-1] + ins[t_j])
        for (((out, &p0), &p1), (&k, &inj)) in cur[1..]
            .iter_mut()
            .zip(prev[..m].iter())
            .zip(prev[1..].iter())
            .zip(ti.iter().zip(insrow.iter()))
        {
            let xy = (p0 + subrow[k]).min(p1 + d);
            left = (left + inj).min(xy);
            *out = left;
        }
        std::mem::swap(&mut prev, &mut cur);
    }
    prev[m]
}

fn main() {
    let path = env::args().nth(1).expect("usage: solution INPUT_PATH");
    let data = fs::read(&path).expect("cannot read input file");
    let text = std::str::from_utf8(&data).expect("input is not UTF-8");
    let mut it = text.split_ascii_whitespace().peekable();

    // Alphabet: leading tokens made of uppercase ASCII letters. Either one
    // concatenated token ("ABC") or A single-letter tokens ("A B C").
    let mut letters: Vec<u8> = Vec::new();
    while let Some(tok) = it.peek() {
        let b = tok.as_bytes();
        if !b.is_empty() && b.iter().all(|&c| c.is_ascii_uppercase()) {
            letters.extend_from_slice(b);
            it.next();
        } else {
            break;
        }
    }
    let a = letters.len();
    let mut lut = [0usize; 256];
    for (i, &b) in letters.iter().enumerate() {
        lut[b as usize] = i;
    }

    let mut next_i64 = || it.next().expect("truncated input").parse::<i64>().unwrap();
    let ins64: Vec<i64> = (0..a).map(|_| next_i64()).collect();
    let del64: Vec<i64> = (0..a).map(|_| next_i64()).collect();
    let sub64: Vec<Vec<i64>> = (0..a)
        .map(|_| (0..a).map(|_| next_i64()).collect())
        .collect();
    let p: usize = next_i64() as usize;

    let pairs: Vec<&str> = it.collect();
    let mut max_len = 0usize;
    for tok in &pairs {
        max_len += tok.len();
    }
    // Max possible cell value: (n + m) * 1000 for any single pair.
    let max_cell = (max_len as i64) * 1000 + 1000;
    let use_i32 = max_cell < i32::MAX as i64;

    let stdout = std::io::stdout();
    let mut out = std::io::BufWriter::new(stdout.lock());
    let mut buf = String::with_capacity(16 * 1024);
    let mut total: i64 = 0;
    if use_i32 {
        let ins: Vec<i32> = ins64.iter().map(|&v| v as i32).collect();
        let del: Vec<i32> = del64.iter().map(|&v| v as i32).collect();
        let sub: Vec<Vec<i32>> = sub64
            .iter()
            .map(|r| r.iter().map(|&v| v as i32).collect())
            .collect();
        for chunk in pairs.chunks(2).take(p) {
            let cost = solve::<i32>(chunk[0].as_bytes(), chunk[1].as_bytes(), &lut, &sub, &ins, &del) as i64;
            total += cost;
            use std::fmt::Write as _;
            let _ = writeln!(buf, "{}", cost);
            if buf.len() > 32 * 1024 {
                let _ = out.write_all(buf.as_bytes());
                buf.clear();
            }
        }
    } else {
        for chunk in pairs.chunks(2).take(p) {
            let cost = solve::<i64>(chunk[0].as_bytes(), chunk[1].as_bytes(), &lut, &sub64, &ins64, &del64);
            total += cost;
            use std::fmt::Write as _;
            let _ = writeln!(buf, "{}", cost);
            if buf.len() > 32 * 1024 {
                let _ = out.write_all(buf.as_bytes());
                buf.clear();
            }
        }
    }
    let _ = writeln!(buf, "total {}", total);
    let _ = out.write_all(buf.as_bytes());
}
