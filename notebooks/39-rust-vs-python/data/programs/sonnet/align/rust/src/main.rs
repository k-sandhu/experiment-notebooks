use std::io::Write;
use std::ops::Add;

// With C_i = sum of del over s_1..s_i and P_j = sum of ins over t_1..t_j, the table
// F[i][j] = D[i][j] - C_i - P_j obeys
//   F[i][j] = min(F[i-1][j], F[i][j-1], F[i-1][j-1] + sub[s_i][t_j] - ins[t_j] - del[s_i])
// with F[i][0] = F[0][j] = 0, so each row is one in-place pass with a running minimum.
fn solve<T>(
    n_alpha: usize,
    ins: &[i64],
    del: &[i64],
    sub: &[i64],
    pairs: &[(Vec<u8>, Vec<u8>)],
    out: &mut Vec<i64>,
) where
    T: Copy + Ord + Add<Output = T> + TryFrom<i64> + Into<i64>,
    <T as TryFrom<i64>>::Error: std::fmt::Debug,
{
    let z: T = T::try_from(0).unwrap();
    let mut row: Vec<T> = Vec::new();
    let mut w: Vec<T> = Vec::new(); // n_alpha profiles of length m
    for (s, t) in pairs {
        let m = t.len();
        w.clear();
        for c in 0..n_alpha {
            for &b in t {
                let b = b as usize;
                w.push(T::try_from(sub[c * n_alpha + b] - ins[b] - del[c]).unwrap());
            }
        }
        row.clear();
        row.resize(m + 1, z);
        let mut cs: i64 = 0;
        for &a in s {
            let a = a as usize;
            cs += del[a];
            let wr = &w[a * m..(a + 1) * m];
            let mut prev = z;
            let mut carry = z;
            for (cell, &wj) in row[1..].iter_mut().zip(wr.iter()) {
                let cur = *cell;
                let v = cur.min(prev + wj);
                carry = carry.min(v);
                *cell = carry;
                prev = cur;
            }
        }
        let ps: i64 = t.iter().map(|&b| ins[b as usize]).sum();
        let f = row[m];
        let f64v: i64 = f.into();
        out.push(f64v + cs + ps);
    }
}

fn main() {
    let path = std::env::args().nth(1).expect("input path");
    let data = std::fs::read(path).expect("read");
    let mut it = data
        .split(|b| b.is_ascii_whitespace())
        .filter(|x| !x.is_empty());
    let alpha = it.next().unwrap();
    let a = alpha.len();
    let mut idx = [0u8; 256];
    for (i, &c) in alpha.iter().enumerate() {
        idx[c as usize] = i as u8;
    }
    let num = |it: &mut dyn Iterator<Item = &[u8]>| -> i64 {
        let tok = it.next().unwrap();
        tok.iter().fold(0i64, |acc, &d| acc * 10 + (d - b'0') as i64)
    };
    let ins: Vec<i64> = (0..a).map(|_| num(&mut it)).collect();
    let del: Vec<i64> = (0..a).map(|_| num(&mut it)).collect();
    let sub: Vec<i64> = (0..a * a).map(|_| num(&mut it)).collect();
    let p = num(&mut it) as usize;
    let mut pairs = Vec::with_capacity(p);
    let mut maxlen = 0usize;
    for _ in 0..p {
        let s: Vec<u8> = it.next().unwrap().iter().map(|&c| idx[c as usize]).collect();
        let t: Vec<u8> = it.next().unwrap().iter().map(|&c| idx[c as usize]).collect();
        maxlen = maxlen.max(s.len()).max(t.len());
        pairs.push((s, t));
    }
    let maxc = ins
        .iter()
        .chain(del.iter())
        .chain(sub.iter())
        .copied()
        .max()
        .unwrap_or(0);
    // |F| <= maxc * (n + m) * 2 for every intermediate value
    let mut out: Vec<i64> = Vec::with_capacity(p);
    if (maxc as i128) * (2 * maxlen as i128 + 2) * 4 < i32::MAX as i128 {
        solve::<i32>(a, &ins, &del, &sub, &pairs, &mut out);
    } else {
        solve::<i64>(a, &ins, &del, &sub, &pairs, &mut out);
    }
    let mut s = String::with_capacity(p * 8 + 32);
    let mut total: i64 = 0;
    for v in &out {
        total += v;
        s.push_str(&v.to_string());
        s.push('\n');
    }
    s.push_str(&format!("total {}\n", total));
    std::io::stdout().lock().write_all(s.as_bytes()).unwrap();
}
