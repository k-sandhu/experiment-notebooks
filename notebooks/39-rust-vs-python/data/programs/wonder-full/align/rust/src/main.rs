use std::env;
use std::fs;
use std::io::{self, Write};
use std::ops::{Add, Sub};

struct Scanner<'a> {
    data: &'a [u8],
    pos: usize,
}

impl<'a> Scanner<'a> {
    fn next_token(&mut self) -> &'a [u8] {
        let d = self.data;
        let mut p = self.pos;
        while p < d.len() && d[p] <= b' ' {
            p += 1;
        }
        let start = p;
        while p < d.len() && d[p] > b' ' {
            p += 1;
        }
        self.pos = p;
        &d[start..p]
    }

    fn next_i32(&mut self) -> i32 {
        let tok = self.next_token();
        let mut v: i32 = 0;
        for &b in tok {
            v = v * 10 + (b - b'0') as i32;
        }
        v
    }
}

/// Weighted alignment cost in "reduced coordinates".
///
/// Let pref[j] be the cost of inserting the first j column characters and
/// P[j] = Dprev[j] - pref[j] for the previous DP row (row 0 is all zero).
/// For a row character with deletion cost `d`, the candidates ignoring the
/// left (insertion) edge are C[j] = min(P[j+1] + d, P[j] + sub - ins_j),
/// and the new row in reduced coordinates is the prefix minimum of
/// [cur0, C[0], C[1], ...], which folds in all the left edges. This makes
/// the candidate computation a straight-line, vectorizable pass followed
/// by a one-min-per-cell scan.
fn pair_cost<T>(
    rows: &[u8],
    cols: &[u8],
    rowcost: &[i32],
    // smi[r * m + j] = sub_cost(r, cols[j]) - insert_cost(cols[j])
    smi: &[i32],
    pref_m: i64,
    prev: &mut Vec<T>,
    cur: &mut Vec<T>,
) -> i64
where
    T: Copy + Ord + Add<Output = T> + Sub<Output = T> + From<i32>,
    i64: From<T>,
{
    let m = cols.len();
    prev.clear();
    prev.resize(m + 1, T::from(0));
    cur.clear();
    cur.resize(m + 1, T::from(0));
    let mut cur0 = T::from(0);
    for &rc in rows {
        let r = rc as usize;
        let d = T::from(rowcost[r]);
        cur0 = cur0 + d;
        let smi_row = &smi[r * m..r * m + m];
        cur[0] = cur0;
        // Candidate pass: no dependencies between columns, so this
        // iterator loop vectorizes.
        for (((dst, &diag), &up), &sm) in cur[1..=m]
            .iter_mut()
            .zip(&prev[..m])
            .zip(&prev[1..=m])
            .zip(smi_row)
        {
            let a = up + d;
            let b = diag + T::from(sm);
            *dst = if a < b { a } else { b };
        }
        // Prefix-minimum scan folds in the insertion edges.
        let mut run = cur[0];
        for x in &mut cur[1..=m] {
            if *x < run {
                run = *x;
            } else {
                *x = run;
            }
        }
        std::mem::swap(prev, cur);
    }
    i64::from(prev[m]) + pref_m
}

fn main() {
    let path = env::args_os().nth(1).expect("usage: solution INPUT");
    let data = fs::read(&path).expect("cannot read input file");
    let mut sc = Scanner { data: &data, pos: 0 };

    let alphabet = sc.next_token().to_vec();
    let a = alphabet.len();
    let mut table = [0u8; 256];
    for (i, &ch) in alphabet.iter().enumerate() {
        table[ch as usize] = i as u8;
    }
    let ins: Vec<i32> = (0..a).map(|_| sc.next_i32()).collect();
    let del: Vec<i32> = (0..a).map(|_| sc.next_i32()).collect();
    let sub: Vec<i32> = (0..a * a).map(|_| sc.next_i32()).collect();
    let p = sc.next_i32() as usize;

    let mut out = String::new();
    let mut total: i64 = 0;

    let mut s_idx: Vec<u8> = Vec::new();
    let mut t_idx: Vec<u8> = Vec::new();
    let mut smi: Vec<i32> = Vec::new();
    let mut prev32: Vec<i32> = Vec::new();
    let mut cur32: Vec<i32> = Vec::new();
    let mut prev64: Vec<i64> = Vec::new();
    let mut cur64: Vec<i64> = Vec::new();

    for _ in 0..p {
        let sb = sc.next_token();
        let tb = sc.next_token();
        if sb == tb {
            out.push_str("0\n");
            continue;
        }
        s_idx.clear();
        s_idx.extend(sb.iter().map(|&b| table[b as usize]));
        t_idx.clear();
        t_idx.extend(tb.iter().map(|&b| table[b as usize]));

        // Orient so the row count is the smaller length. Swapping s and t
        // transposes the DP grid: deletion <-> insertion costs swap and
        // the substitution table transposes; the cost is unchanged.
        let (rows, cols, rowcost, colins, swapped): (&[u8], &[u8], &[i32], &[i32], bool) =
            if s_idx.len() <= t_idx.len() {
                (&s_idx, &t_idx, &del, &ins, false)
            } else {
                (&t_idx, &s_idx, &ins, &del, true)
            };
        let m = cols.len();

        smi.clear();
        smi.resize(a * m, 0);
        let mut pref_m: i64 = 0;
        for &cc in cols {
            pref_m += colins[cc as usize] as i64;
        }
        for r in 0..a {
            let base = r * m;
            for (j, &cc) in cols.iter().enumerate() {
                let c = cc as usize;
                let s = if swapped { sub[c * a + r] } else { sub[r * a + c] };
                smi[base + j] = s - colins[c];
            }
        }

        // |reduced values| stay below roughly 1000 * (n + m + 2).
        let cost = if (rows.len() as i64 + m as i64 + 2) * 1000 < i32::MAX as i64 {
            pair_cost::<i32>(rows, cols, rowcost, &smi, pref_m, &mut prev32, &mut cur32)
        } else {
            pair_cost::<i64>(rows, cols, rowcost, &smi, pref_m, &mut prev64, &mut cur64)
        };
        total += cost;
        out.push_str(&cost.to_string());
        out.push('\n');
    }
    out.push_str(&format!("total {total}\n"));

    let stdout = io::stdout();
    let mut lock = stdout.lock();
    let _ = lock.write_all(out.as_bytes());
}
