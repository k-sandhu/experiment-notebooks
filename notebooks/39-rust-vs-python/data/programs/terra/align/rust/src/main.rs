use std::{env, fs, fmt::Write};

fn main() {
    let input = fs::read(env::args_os().nth(1).unwrap()).unwrap();
    let mut tokens = input.split(|b| b.is_ascii_whitespace()).filter(|x| !x.is_empty());
    let alphabet = tokens.next().unwrap();
    let a = alphabet.len();
    let number = |v: &[u8]| -> i64 { v.iter().fold(0, |n, b| n * 10 + (b - b'0') as i64) };
    let mut ins = vec![0; a];
    let mut del = vec![0; a];
    for x in &mut ins { *x = number(tokens.next().unwrap()); }
    for x in &mut del { *x = number(tokens.next().unwrap()); }
    let mut sub = vec![vec![0; a]; a];
    for row in &mut sub { for x in row { *x = number(tokens.next().unwrap()); } }
    let mut transpose = vec![vec![0; a]; a];
    for i in 0..a { for j in 0..a { transpose[j][i] = sub[i][j]; } }
    let count = number(tokens.next().unwrap()) as usize;
    let mut lookup = [0usize; 256];
    for (i, &c) in alphabet.iter().enumerate() { lookup[c as usize] = i; }
    let mut out = String::new();
    let mut total = 0i64;
    for _ in 0..count {
        let mut s = tokens.next().unwrap();
        let mut t = tokens.next().unwrap();
        let (row_cost, col_cost, matrix) = if t.len() > s.len() {
            std::mem::swap(&mut s, &mut t);
            (&ins, &del, &transpose)
        } else { (&del, &ins, &sub) };
        let ti: Vec<usize> = t.iter().map(|&c| lookup[c as usize]).collect();
        let costs: Vec<i64> = ti.iter().map(|&c| col_cost[c]).collect();
        let mut prev = vec![0i64; t.len() + 1];
        for j in 0..t.len() { prev[j+1] = prev[j] + costs[j]; }
        let subs: Vec<Vec<i64>> = matrix.iter().map(|row| ti.iter().map(|&c| row[c]).collect()).collect();
        for &c in s {
            let index = lookup[c as usize];
            let d = row_cost[index];
            let mut diagonal = prev[0];
            let mut left = diagonal + d;
            prev[0] = left;
            for j in 0..t.len() {
                let above = prev[j+1];
                left = (above + d).min(left + costs[j]).min(diagonal + subs[index][j]);
                prev[j+1] = left;
                diagonal = above;
            }
        }
        let result = prev[t.len()];
        total += result;
        writeln!(out, "{result}").unwrap();
    }
    writeln!(out, "total {total}").unwrap();
    print!("{out}");
}
