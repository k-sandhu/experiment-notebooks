use std::env;
use std::fs;
use std::io::{self, BufWriter, Write};

/// Reads the next whitespace-delimited token from `data`, advancing `pos`.
fn next_token<'a>(data: &'a [u8], pos: &mut usize) -> &'a [u8] {
    while *pos < data.len() && data[*pos].is_ascii_whitespace() {
        *pos += 1;
    }
    let start = *pos;
    while *pos < data.len() && !data[*pos].is_ascii_whitespace() {
        *pos += 1;
    }
    &data[start..*pos]
}

/// Reads the next token as a non-negative integer.
fn next_int(data: &[u8], pos: &mut usize) -> i64 {
    let tok = next_token(data, pos);
    let mut v: i64 = 0;
    for &b in tok {
        v = v * 10 + (b - b'0') as i64;
    }
    v
}

fn main() -> io::Result<()> {
    let path = env::args().nth(1).expect("usage: solution INPUT_PATH");
    let data = fs::read(&path).expect("failed to read input file");

    let mut pos = 0;

    // Alphabet: distinct upper-case letters; their order defines letter indices 0..A.
    let alphabet = next_token(&data, &mut pos);
    let mut idx = [255u8; 256];
    for (i, &b) in alphabet.iter().enumerate() {
        idx[b as usize] = i as u8;
    }
    let a = alphabet.len();

    let mut ins = [0i64; 26];
    let mut del_cost = [0i64; 26];
    let mut sub = [[0i64; 26]; 26];
    for i in 0..a {
        ins[i] = next_int(&data, &mut pos);
    }
    for i in 0..a {
        del_cost[i] = next_int(&data, &mut pos);
    }
    for i in 0..a {
        for j in 0..a {
            sub[i][j] = next_int(&data, &mut pos);
        }
    }

    let p = next_int(&data, &mut pos) as usize;

    let mut prev: Vec<i64> = Vec::new();
    let mut curr: Vec<i64> = Vec::new();
    let mut out = String::new();
    let mut total: i64 = 0;

    for _ in 0..p {
        let s_tok = next_token(&data, &mut pos);
        let t_tok = next_token(&data, &mut pos);

        let cost = if s_tok == t_tok {
            // All costs are non-negative, so equal strings cost 0.
            0
        } else {
            let n = s_tok.len();
            let m = t_tok.len();

            // Indexed, per-pair views: removes per-cell alphabet lookups in the hot loop.
            let s_idx: Vec<u8> = s_tok.iter().map(|&b| idx[b as usize]).collect();
            let t_idx: Vec<u8> = t_tok.iter().map(|&b| idx[b as usize]).collect();
            let s_del: Vec<i64> = s_idx.iter().map(|&i| del_cost[i as usize] as i64).collect();
            let t_ins: Vec<i64> = t_idx.iter().map(|&i| ins[i as usize] as i64).collect();

            prev.resize(m + 1, 0);
            curr.resize(m + 1, 0);

            // D[0][j] = D[0][j-1] + ins[t_j]
            {
                let mut acc: i64 = 0;
                prev[0] = 0;
                for j in 0..m {
                    acc += t_ins[j];
                    prev[j + 1] = acc;
                }
            }

            for i in 0..n {
                let d = s_del[i];
                let sub_row = sub[s_idx[i] as usize];

                let mut cur = prev[0] + d;
                curr[0] = cur;
                let mut prev_j = prev[0]; // prev[j - 1]

                for j in 1..=m {
                    let tj = t_idx[j - 1] as usize;
                    let del_val = prev[j] + d;
                    let ins_val = cur + t_ins[j - 1];
                    let sub_val = prev_j + sub_row[tj];
                    cur = del_val.min(ins_val).min(sub_val);
                    curr[j] = cur;
                    prev_j = prev[j];
                }

                std::mem::swap(&mut prev, &mut curr);
            }

            prev[m]
        };

        total += cost;
        out.push_str(&cost.to_string());
        out.push('\n');
    }

    out.push_str("total ");
    out.push_str(&total.to_string());
    out.push('\n');

    let stdout = io::stdout();
    let mut handle = BufWriter::new(stdout.lock());
    handle.write_all(out.as_bytes())?;
    handle.flush()?;
    Ok(())
}
