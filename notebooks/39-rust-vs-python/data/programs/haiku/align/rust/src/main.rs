use std::cmp::min;
use std::fmt::Write as _;
use std::io::{self, Write};
use std::ops::Add;
use std::str::SplitAsciiWhitespace;

/// Cost tables from the input. `sub` is row-major: `sub[i * a + j]`.
struct Costs {
    a: usize,
    ins: Vec<i64>,
    del: Vec<i64>,
    sub: Vec<i64>,
}

fn parse_next(tokens: &mut SplitAsciiWhitespace) -> i64 {
    tokens
        .next()
        .expect("unexpected end of input")
        .parse()
        .expect("expected a number")
}

/// Cost of one pair, with the DP held in `T`.
///
/// Uses the shifted table `g[i][j] = D[i][j] - C[j]`, where `C[j]` is the sum of
/// `ins[t_1..t_j]`. In these terms the insertion step becomes a running minimum:
///
///   g[i][j] = min(g[i-1][j] + del[s_i], g[i-1][j-1] + sub[s_i][t_j] - ins[t_j], g[i][j-1])
///
/// Each row is therefore a vectorizable pass followed by a prefix minimum, and the
/// serial chain is one `min` per cell. The answer is `g[n][m] + C[m]`.
fn solve<T>(c: &Costs, s: &[usize], t: &[usize]) -> i64
where
    T: Copy + Ord + Add<Output = T> + TryFrom<i64> + Into<i64>,
    <T as TryFrom<i64>>::Error: std::fmt::Debug,
{
    let m = t.len();
    let conv = |x: i64| -> T { T::try_from(x).expect("cost out of range") };

    // prof[a * m + k] = sub[a][t_k] - ins[t_k], so each row reads a contiguous slice.
    let mut prof: Vec<T> = Vec::with_capacity(c.a * m);
    for a in 0..c.a {
        for &tk in t {
            prof.push(conv(c.sub[a * c.a + tk] - c.ins[tk]));
        }
    }
    let del: Vec<T> = c.del.iter().map(|&x| conv(x)).collect();

    // Row g[0] is all zeros because D[0][j] = C[j].
    let mut prev = vec![conv(0); m + 1];
    let mut cur = vec![conv(0); m + 1];

    for &a in s {
        let d = del[a];
        let p = &prof[a * m..(a + 1) * m];

        cur[0] = prev[0] + d;
        {
            let (_, out) = cur.split_at_mut(1);
            let up = &prev[1..];
            let diag = &prev[..m];
            for (((o, &u), &g), &pk) in out.iter_mut().zip(up).zip(diag).zip(p) {
                *o = min(u + d, g + pk);
            }
        }

        // Prefix minimum along the row: the insertion term.
        let mut run = cur[0];
        for x in cur[1..].iter_mut() {
            run = min(run, *x);
            *x = run;
        }

        std::mem::swap(&mut prev, &mut cur);
    }

    let total_ins: i64 = t.iter().map(|&k| c.ins[k]).sum();
    let g: i64 = prev[m].into();
    g + total_ins
}

fn pair_cost(c: &Costs, lut: &[usize; 256], cmax: i64, s: &[u8], t: &[u8]) -> i64 {
    let si: Vec<usize> = s.iter().map(|&b| lut[b as usize]).collect();
    let ti: Vec<usize> = t.iter().map(|&b| lut[b as usize]).collect();

    // Every value in the table is bounded by (n + 2m + 1) * cmax in magnitude.
    let bound = (si.len() as i64 + 2 * ti.len() as i64 + 2) * (cmax + 1);
    if bound < i32::MAX as i64 {
        solve::<i32>(c, &si, &ti)
    } else {
        solve::<i64>(c, &si, &ti)
    }
}

fn main() {
    let path = std::env::args().nth(1).expect("usage: solution INPUT_PATH");
    let text = std::fs::read_to_string(&path).expect("cannot read input");

    // The alphabet is the first line; its letters are not separated by spaces.
    let (first, rest) = text.split_once('\n').unwrap_or((&text, ""));
    let mut lut = [usize::MAX; 256];
    let mut a = 0usize;
    for b in first.bytes().filter(|b| !b.is_ascii_whitespace()) {
        lut[b as usize] = a;
        a += 1;
    }

    let mut tokens = rest.split_ascii_whitespace();
    let ins: Vec<i64> = (0..a).map(|_| parse_next(&mut tokens)).collect();
    let del: Vec<i64> = (0..a).map(|_| parse_next(&mut tokens)).collect();
    let sub: Vec<i64> = (0..a * a).map(|_| parse_next(&mut tokens)).collect();
    let cmax = ins
        .iter()
        .chain(&del)
        .chain(&sub)
        .map(|x| x.abs())
        .max()
        .unwrap_or(0);
    let costs = Costs { a, ins, del, sub };

    let p = parse_next(&mut tokens) as usize;
    let mut out = String::with_capacity(p * 16 + 32);
    let mut total: i64 = 0;
    for _ in 0..p {
        let s = tokens.next().expect("missing string").as_bytes();
        let t = tokens.next().expect("missing string").as_bytes();
        let cost = pair_cost(&costs, &lut, cmax, s, t);
        total += cost;
        writeln!(out, "{cost}").unwrap();
    }
    writeln!(out, "total {total}").unwrap();
    io::stdout().lock().write_all(out.as_bytes()).unwrap();
}
