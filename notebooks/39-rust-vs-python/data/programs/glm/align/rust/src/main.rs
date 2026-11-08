use std::env;
use std::fs;
use std::io::Write;

struct Parser<'a> {
    d: &'a [u8],
    i: usize,
}

impl<'a> Parser<'a> {
    fn token(&mut self) -> &'a [u8] {
        while self.i < self.d.len() && self.d[self.i].is_ascii_whitespace() {
            self.i += 1;
        }
        let s = self.i;
        while self.i < self.d.len() && !self.d[self.i].is_ascii_whitespace() {
            self.i += 1;
        }
        &self.d[s..self.i]
    }
    fn int(&mut self) -> i32 {
        let t = self.token();
        let mut v: i32 = 0;
        for &b in t {
            v = v * 10 + (b - b'0') as i32;
        }
        v
    }
}

fn main() {
    let path = match env::args().nth(1) {
        Some(p) => p,
        None => {
            eprintln!("usage: solution INPUT_PATH");
            std::process::exit(2);
        }
    };
    let data = fs::read(&path).unwrap();
    let mut p = Parser { d: &data, i: 0 };

    let alpha = p.token().to_vec();
    let a = alpha.len();
    let mut lut = [0u8; 256];
    for (i, &b) in alpha.iter().enumerate() {
        lut[b as usize] = i as u8;
    }
    let ins: Vec<i32> = (0..a).map(|_| p.int()).collect();
    let del: Vec<i32> = (0..a).map(|_| p.int()).collect();
    let sub: Vec<i32> = (0..a * a).map(|_| p.int()).collect();
    let npairs = p.int() as usize;

    let mut out = String::with_capacity(npairs * 8 + 32);
    let mut total: i64 = 0;

    // reusable buffers
    let mut prev: Vec<i32> = Vec::new();
    let mut cur: Vec<i32> = Vec::new();
    let mut tidx: Vec<u8> = Vec::new();
    let mut ins_t: Vec<i32> = Vec::new();

    for _ in 0..npairs {
        let s = p.token();
        let t = p.token();
        let m = t.len();

        tidx.clear();
        tidx.extend(t.iter().map(|&b| lut[b as usize]));
        ins_t.clear();
        ins_t.extend(tidx.iter().map(|&ti| ins[ti as usize]));

        prev.clear();
        prev.resize(m + 1, 0);
        let mut acc: i32 = 0;
        for j in 0..m {
            acc += ins_t[j];
            prev[j + 1] = acc;
        }
        cur.clear();
        cur.resize(m + 1, 0);

        for &c in s {
            let ci = lut[c as usize] as usize;
            let dc = del[ci];
            let srow = &sub[ci * a..ci * a + a];
            let mut left = prev[0] + dc;
            let mut diag = prev[0];
            cur[0] = left;
            for (((&up, &ti), out), &ic) in prev[1..]
                .iter()
                .zip(tidx.iter())
                .zip(cur[1..].iter_mut())
                .zip(ins_t.iter())
            {
                // d = min(up + dc, diag + sub, left + ins)
                let mut d = up + dc;
                let dg = diag + unsafe { *srow.get_unchecked(ti as usize) };
                if dg < d {
                    d = dg;
                }
                let lf = left + ic;
                if lf < d {
                    d = lf;
                }
                left = d;
                *out = d;
                diag = up;
            }
            std::mem::swap(&mut prev, &mut cur);
        }

        let cost = prev[m] as i64;
        total += cost;
        out.push_str(&cost.to_string());
        out.push('\n');
    }

    out.push_str("total ");
    out.push_str(&total.to_string());
    out.push('\n');
    std::io::stdout().write_all(out.as_bytes()).unwrap();
}
