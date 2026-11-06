use std::fmt::Write as FmtWrite;
use std::io::Write as IoWrite;

struct Scanner<'a> {
    data: &'a [u8],
    pos: usize,
}

impl<'a> Scanner<'a> {
    #[inline]
    fn token(&mut self) -> &'a [u8] {
        let d = self.data;
        let n = d.len();
        let mut p = self.pos;
        while p < n && d[p] <= b' ' {
            p += 1;
        }
        let start = p;
        while p < n && d[p] > b' ' {
            p += 1;
        }
        self.pos = p;
        &d[start..p]
    }

    #[inline]
    fn int(&mut self) -> i32 {
        let d = self.data;
        let n = d.len();
        let mut p = self.pos;
        while p < n && d[p] <= b' ' {
            p += 1;
        }
        let mut v: i32 = 0;
        while p < n && d[p] > b' ' {
            v = v * 10 + (d[p] - b'0') as i32;
            p += 1;
        }
        self.pos = p;
        v
    }
}

fn main() {
    let path = std::env::args_os().nth(1).expect("usage: solution INPUT_PATH");
    let data = std::fs::read(path).expect("cannot read input");
    let mut sc = Scanner { data: &data, pos: 0 };

    let alpha = sc.token().to_vec();
    let ac = alpha.len();
    let mut map = [0u8; 256];
    for (i, &c) in alpha.iter().enumerate() {
        map[c as usize] = i as u8;
    }

    let mut ins = [0i32; 26];
    let mut del = [0i32; 26];
    let mut sub = [[0i32; 26]; 26];
    for i in 0..ac {
        ins[i] = sc.int();
    }
    for i in 0..ac {
        del[i] = sc.int();
    }
    for i in 0..ac {
        for j in 0..ac {
            sub[i][j] = sc.int();
        }
    }
    let pairs = sc.int() as usize;

    let mut colidx: Vec<u8> = Vec::new();
    let mut wbuf: Vec<i32> = Vec::new();
    let mut qbuf: Vec<i32> = Vec::new();
    let mut insv: Vec<i32> = Vec::new();
    let mut ins_e = [0i32; 26];
    let mut del_e = [0i32; 26];
    let mut sub_e = [[0i32; 26]; 26];

    let mut out = String::with_capacity(pairs * 8 + 32);
    let mut total: i64 = 0;

    for _ in 0..pairs {
        let a = sc.token();
        let b = sc.token();
        // Use the shorter string as the row dimension so the row loop
        // (which is inherently serial) runs fewer times.
        let swapped = a.len() > b.len();
        let (rows, cols) = if swapped { (b, a) } else { (a, b) };

        if swapped {
            ins_e[..ac].copy_from_slice(&del[..ac]);
            del_e[..ac].copy_from_slice(&ins[..ac]);
            for i in 0..ac {
                for j in 0..ac {
                    sub_e[i][j] = sub[j][i];
                }
            }
        } else {
            ins_e[..ac].copy_from_slice(&ins[..ac]);
            del_e[..ac].copy_from_slice(&del[..ac]);
            for i in 0..ac {
                sub_e[i][..ac].copy_from_slice(&sub[i][..ac]);
            }
        }

        let m = cols.len();
        let stride = m + 1;

        colidx.clear();
        colidx.extend(cols.iter().map(|&c| map[c as usize]));

        insv.clear();
        insv.resize(stride, 0);
        let mut ins_total: i32 = 0;
        for j in 0..m {
            let v = ins_e[colidx[j] as usize];
            ins_total += v;
            insv[j + 1] = v;
        }

        // Work in "R space": R[i][j] = D[i][j] - I[j] - J[i], where I is the
        // prefix sum of insertion costs of t and J the prefix sum of deletion
        // costs of s.  Both cancel out of the recurrence, giving
        //   R'[j] = min(R'[j-1], R[j], R[j-1] + sub[s_i][t_j] - ins[t_j] - del[s_i])
        // with R[i][0] = 0 for every row.  The answer is R[n][m] + I[m] + J[n].
        wbuf.clear();
        wbuf.resize(ac * stride, 0);
        for ai in 0..ac {
            let row = &sub_e[ai];
            let dv = del_e[ai];
            let base = ai * stride;
            let w = &mut wbuf[base + 1..base + stride];
            for j in 0..m {
                w[j] = row[colidx[j] as usize] - insv[j + 1] - dv;
            }
        }

        qbuf.clear();
        qbuf.resize(stride, 0);

        let mut last: i32 = 0;
        let mut del_total: i32 = 0;
        for &rc in rows.iter() {
            let ai = map[rc as usize] as usize;
            let w = &wbuf[ai * stride..(ai + 1) * stride];
            del_total += del_e[ai];
            let mut left: i32 = 0;
            let mut qp: i32 = 0;
            for (qi, &wj) in qbuf[1..].iter_mut().zip(w[1..].iter()) {
                let qj = *qi;
                let mut c = qj;
                if left < c {
                    c = left;
                }
                let x = qp + wj;
                if x < c {
                    c = x;
                }
                *qi = c;
                left = c;
                qp = qj;
            }
            last = left;
        }

        let ans = (last + ins_total + del_total) as i64;
        total += ans;
        let _ = writeln!(out, "{}", ans);
    }
    let _ = writeln!(out, "total {}", total);

    let stdout = std::io::stdout();
    let mut lock = stdout.lock();
    let _ = lock.write_all(out.as_bytes());
}
