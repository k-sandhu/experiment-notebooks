use std::fmt::Write as _;
use std::io::Write as _;

struct Parser<'a> {
    d: &'a [u8],
    i: usize,
}

impl<'a> Parser<'a> {
    fn new(d: &'a [u8]) -> Self {
        Parser { d, i: 0 }
    }

    #[inline]
    fn skip_ws(&mut self) {
        let d = self.d;
        let mut i = self.i;
        while i < d.len() && d[i] <= b' ' {
            i += 1;
        }
        self.i = i;
    }

    #[inline]
    fn token(&mut self) -> &'a [u8] {
        self.skip_ws();
        let d = self.d;
        let start = self.i;
        let mut i = start;
        while i < d.len() && d[i] > b' ' {
            i += 1;
        }
        self.i = i;
        &d[start..i]
    }

    #[inline]
    fn int(&mut self) -> i64 {
        self.skip_ws();
        let d = self.d;
        let mut i = self.i;
        let mut neg = false;
        if i < d.len() && d[i] == b'-' {
            neg = true;
            i += 1;
        }
        let mut v: i64 = 0;
        while i < d.len() {
            let c = d[i];
            if c < b'0' || c > b'9' {
                break;
            }
            v = v * 10 + (c - b'0') as i64;
            i += 1;
        }
        self.i = i;
        if neg { -v } else { v }
    }
}

fn main() {
    let path = std::env::args().nth(1).expect("input path");
    let data = std::fs::read(&path).expect("read input");
    let mut ps = Parser::new(&data);

    let alpha = ps.token();
    let a = alpha.len();

    let mut map = [0u8; 256];
    for (k, &ch) in alpha.iter().enumerate() {
        map[ch as usize] = k as u8;
    }

    let mut ins = [0i32; 26];
    let mut del = [0i32; 26];
    for k in 0..a {
        ins[k] = ps.int() as i32;
    }
    for k in 0..a {
        del[k] = ps.int() as i32;
    }
    let mut sub = [0i32; 26 * 26];
    for r in 0..a {
        for c in 0..a {
            sub[r * 26 + c] = ps.int() as i32;
        }
    }

    let npairs = ps.int() as usize;

    let mut s_buf: Vec<u8> = Vec::with_capacity(1024);
    let mut t_buf: Vec<u8> = Vec::with_capacity(1024);
    let mut inc: Vec<i32> = Vec::with_capacity(1024);
    let mut prev: Vec<i32> = Vec::with_capacity(1024);
    let mut cur: Vec<i32> = Vec::with_capacity(1024);

    let mut out = String::with_capacity(npairs * 12 + 32);
    let mut total: i64 = 0;

    for _ in 0..npairs {
        s_buf.clear();
        t_buf.clear();
        {
            let st = ps.token();
            s_buf.extend(st.iter().map(|&ch| map[ch as usize]));
        }
        {
            let tt = ps.token();
            t_buf.extend(tt.iter().map(|&ch| map[ch as usize]));
        }
        let n = s_buf.len();
        let m = t_buf.len();

        inc.clear();
        for &tj in t_buf.iter() {
            inc.push(ins[tj as usize]);
        }

        prev.clear();
        prev.resize(m + 1, 0);
        cur.clear();
        cur.resize(m + 1, 0);
        let mut acc: i32 = 0;
        for j in 0..m {
            acc += inc[j];
            prev[j + 1] = acc;
        }

        for i in 0..n {
            let si = s_buf[i] as usize;
            let d = del[si];
            let srow = &sub[si * 26..si * 26 + 26];
            let mut left = prev[0] + d;
            cur[0] = left;
            let mut diag = prev[0];
            for j in 1..=m {
                let up = prev[j];
                let mut v = up + d;
                let x = diag + srow[t_buf[j - 1] as usize];
                if x < v {
                    v = x;
                }
                let y = left + inc[j - 1];
                if y < v {
                    v = y;
                }
                cur[j] = v;
                left = v;
                diag = up;
            }
            std::mem::swap(&mut prev, &mut cur);
        }

        let cost = prev[m] as i64;
        total += cost;
        let _ = writeln!(out, "{}", cost);
    }

    let _ = writeln!(out, "total {}", total);

    let stdout = std::io::stdout();
    let mut lock = stdout.lock();
    lock.write_all(out.as_bytes()).unwrap();
}
