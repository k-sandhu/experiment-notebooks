use std::io::Write;

// Fast whitespace token scanner over the whole file bytes.
struct Scanner<'a> {
    b: &'a [u8],
    i: usize,
}

impl<'a> Scanner<'a> {
    #[inline]
    fn next_token(&mut self) -> &'a [u8] {
        let b = self.b;
        let mut i = self.i;
        while i < b.len() && b[i] <= b' ' {
            i += 1;
        }
        let start = i;
        while i < b.len() && b[i] > b' ' {
            i += 1;
        }
        self.i = i;
        &b[start..i]
    }
    #[inline]
    fn next_i32(&mut self) -> i32 {
        let b = self.b;
        let mut i = self.i;
        while i < b.len() && b[i] <= b' ' {
            i += 1;
        }
        let mut neg = false;
        if i < b.len() && b[i] == b'-' {
            neg = true;
            i += 1;
        }
        let mut v: i32 = 0;
        while i < b.len() {
            let c = b[i];
            if c < b'0' || c > b'9' {
                break;
            }
            v = v * 10 + (c - b'0') as i32;
            i += 1;
        }
        self.i = i;
        if neg { -v } else { v }
    }
    #[inline]
    fn next_usize(&mut self) -> usize {
        self.next_i32() as usize
    }
}

/// Edit distance for one pair. `s`/`t` are alphabet indices.
/// ins/del/sub describe the (possibly transposed) problem.
fn pair_cost(
    s: &[u8],
    t: &[u8],
    ins: &[i32],
    del: &[i32],
    sub: &[i32], // A x A row-major
    a: usize,
    prev: &mut Vec<i32>,
    cur: &mut Vec<i32>,
    ins_t: &mut Vec<i32>,
) -> i32 {
    let m = t.len();
    ins_t.clear();
    ins_t.reserve(m);
    for &c in t {
        ins_t.push(ins[c as usize]);
    }
    prev.clear();
    prev.resize(m + 1, 0);
    for j in 0..m {
        prev[j + 1] = prev[j] + ins_t[j];
    }
    cur.clear();
    cur.resize(m + 1, 0);

    for &si_b in s {
        let si = si_b as usize;
        let d = del[si];
        let sub_row = &sub[si * a..si * a + a];
        cur[0] = prev[0] + d;
        // Tight scalar DP; the left-neighbour dependency is inherent.
        // Use unchecked indexing: lengths are m+1 for both rows.
        unsafe {
            let pv = prev.as_ptr();
            let cv = cur.as_mut_ptr();
            let it = ins_t.as_ptr();
            let tp = t.as_ptr();
            let mut left = *cv;
            for j in 1..=m {
                let up = *pv.add(j) + d;
                let dg = *pv.add(j - 1) + sub_row[*tp.add(j - 1) as usize];
                let lf = left + *it.add(j - 1);
                let mut v = if up < dg { up } else { dg };
                if lf < v {
                    v = lf;
                }
                *cv.add(j) = v;
                left = v;
            }
        }
        std::mem::swap(prev, cur);
    }
    prev[m]
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let path = &args[1];
    let data = std::fs::read(path).expect("read input");
    let mut sc = Scanner { b: &data, i: 0 };

    let alphabet = sc.next_token().to_vec();
    let a = alphabet.len();
    let mut idx = [0u8; 256];
    for (i, &ch) in alphabet.iter().enumerate() {
        idx[ch as usize] = i as u8;
    }
    let mut ins = vec![0i32; a];
    for v in ins.iter_mut() {
        *v = sc.next_i32();
    }
    let mut del = vec![0i32; a];
    for v in del.iter_mut() {
        *v = sc.next_i32();
    }
    let mut sub = vec![0i32; a * a];
    for v in sub.iter_mut() {
        *v = sc.next_i32();
    }
    // Transposed substitution table for the swapped orientation.
    let mut sub_t = vec![0i32; a * a];
    for i in 0..a {
        for j in 0..a {
            sub_t[j * a + i] = sub[i * a + j];
        }
    }
    let p = sc.next_usize();

    let mut out = Vec::<u8>::with_capacity(p * 8 + 32);
    let mut total: i64 = 0;
    let mut prev: Vec<i32> = Vec::new();
    let mut cur: Vec<i32> = Vec::new();
    let mut ins_t: Vec<i32> = Vec::new();
    let mut s_idx: Vec<u8> = Vec::new();
    let mut t_idx: Vec<u8> = Vec::new();

    for _ in 0..p {
        let s_tok = sc.next_token();
        let t_tok = sc.next_token();
        let cost: i32 = if s_tok == t_tok {
            0
        } else {
            s_idx.clear();
            s_idx.extend(s_tok.iter().map(|&c| idx[c as usize]));
            t_idx.clear();
            t_idx.extend(t_tok.iter().map(|&c| idx[c as usize]));
            // Shorter string as columns to keep rows cache-resident.
            if t_idx.len() > s_idx.len() {
                pair_cost(&t_idx, &s_idx, &del, &ins, &sub_t, a, &mut prev, &mut cur, &mut ins_t)
            } else {
                pair_cost(&s_idx, &t_idx, &ins, &del, &sub, a, &mut prev, &mut cur, &mut ins_t)
            }
        };
        total += cost as i64;
        out.extend_from_slice(cost.to_string().as_bytes());
        out.push(b'\n');
    }
    out.extend_from_slice(format!("total {}", total).as_bytes());
    out.push(b'\n');
    let stdout = std::io::stdout();
    let mut lock = stdout.lock();
    let _ = lock.write_all(&out);
}
