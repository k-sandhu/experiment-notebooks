use std::io::Write;

fn num(t: &[u8]) -> i32 {
    let mut v: i32 = 0;
    let mut neg = false;
    for &ch in t {
        if ch == b'-' {
            neg = true;
        } else if ch.is_ascii_digit() {
            v = v * 10 + (ch - b'0') as i32;
        }
    }
    if neg { -v } else { v }
}

fn dp_scalar(
    s: &[u8],
    del: &[i32],
    prof: &[i32],
    m: usize,
    mp: usize,
    a: &mut [i32],
    b: &mut [i32],
) -> i32 {
    let mut prev: &mut [i32] = &mut a[..m + 1];
    let mut cur: &mut [i32] = &mut b[..m + 1];
    let mut col0 = 0i32;
    for &c in s {
        let c = c as usize;
        let d = del[c];
        col0 += d;
        let pr = &prof[c * mp..c * mp + m];
        cur[0] = col0;
        {
            let out = &mut cur[1..];
            let up = &prev[1..];
            let dg = &prev[..m];
            for (((o, &u), &g), &p) in out.iter_mut().zip(up).zip(dg).zip(pr) {
                *o = (u + d).min(g + p);
            }
            let mut run = col0;
            for o in out.iter_mut() {
                run = run.min(*o);
                *o = run;
            }
        }
        std::mem::swap(&mut prev, &mut cur);
    }
    prev[m]
}

#[cfg(target_arch = "x86_64")]
#[target_feature(enable = "avx2")]
unsafe fn dp_avx2(
    s: &[u8],
    del: &[i32],
    prof: &[i32],
    m: usize,
    mp: usize,
    a: &mut [i32],
    b: &mut [i32],
) -> i32 {
    use std::arch::x86_64::*;
    unsafe {
        let maxv = _mm256_set1_epi32(i32::MAX);
        let idx3 = _mm256_set1_epi32(3);
        let idx7 = _mm256_set1_epi32(7);
        let mut prev: *mut i32 = a.as_mut_ptr();
        let mut cur: *mut i32 = b.as_mut_ptr();
        let pbase = prof.as_ptr();
        let mut col0 = 0i32;
        for &c in s {
            let c = c as usize;
            let d = *del.get_unchecked(c);
            col0 += d;
            let dv = _mm256_set1_epi32(d);
            let pr = pbase.add(c * mp);
            *cur = col0;
            let mut carry = _mm256_set1_epi32(col0);
            let mut k = 0usize;
            while k < mp {
                let up = _mm256_loadu_si256(prev.add(k + 1) as *const __m256i);
                let dg = _mm256_loadu_si256(prev.add(k) as *const __m256i);
                let p = _mm256_loadu_si256(pr.add(k) as *const __m256i);
                let w = _mm256_min_epi32(_mm256_add_epi32(up, dv), _mm256_add_epi32(dg, p));
                let w1 = _mm256_min_epi32(w, _mm256_alignr_epi8::<12>(w, maxv));
                let w2 = _mm256_min_epi32(w1, _mm256_alignr_epi8::<8>(w1, maxv));
                let b3 = _mm256_permutevar8x32_epi32(w2, idx3);
                let w3 = _mm256_min_epi32(w2, _mm256_blend_epi32::<0xF0>(maxv, b3));
                let last = _mm256_permutevar8x32_epi32(w3, idx7);
                let out = _mm256_min_epi32(w3, carry);
                carry = _mm256_min_epi32(carry, last);
                _mm256_storeu_si256(cur.add(k + 1) as *mut __m256i, out);
                k += 8;
            }
            std::mem::swap(&mut prev, &mut cur);
        }
        *prev.add(m)
    }
}

#[cfg(target_arch = "x86_64")]
fn detect_avx2() -> bool {
    std::is_x86_feature_detected!("avx2")
}

#[cfg(not(target_arch = "x86_64"))]
fn detect_avx2() -> bool {
    false
}

#[cfg(target_arch = "x86_64")]
fn run_dp(
    use_avx2: bool,
    s: &[u8],
    del: &[i32],
    prof: &[i32],
    m: usize,
    mp: usize,
    a: &mut [i32],
    b: &mut [i32],
) -> i32 {
    if use_avx2 {
        assert!(a.len() >= mp + 1 && b.len() >= mp + 1);
        assert!(prof.len() >= del.len() * mp);
        // SAFETY: avx2 detected; buffers sized as asserted; codes in s are < del.len().
        unsafe { dp_avx2(s, del, prof, m, mp, a, b) }
    } else {
        dp_scalar(s, del, prof, m, mp, a, b)
    }
}

#[cfg(not(target_arch = "x86_64"))]
fn run_dp(
    _use_avx2: bool,
    s: &[u8],
    del: &[i32],
    prof: &[i32],
    m: usize,
    mp: usize,
    a: &mut [i32],
    b: &mut [i32],
) -> i32 {
    dp_scalar(s, del, prof, m, mp, a, b)
}

fn main() {
    let path = std::env::args().nth(1).expect("missing input path");
    let data = std::fs::read(&path).expect("cannot read input");
    let mut it = data
        .split(|b: &u8| b.is_ascii_whitespace())
        .filter(|t| !t.is_empty());

    let alpha = it.next().expect("alphabet");
    let na = alpha.len();
    let mut map = [0u8; 256];
    for (i, &ch) in alpha.iter().enumerate() {
        map[ch as usize] = i as u8;
    }

    let mut ins = vec![0i32; na];
    for v in ins.iter_mut() {
        *v = num(it.next().expect("ins"));
    }
    let mut del = vec![0i32; na];
    for v in del.iter_mut() {
        *v = num(it.next().expect("del"));
    }
    let mut sub = vec![0i32; na * na];
    for v in sub.iter_mut() {
        *v = num(it.next().expect("sub"));
    }
    let p = num(it.next().expect("P")) as usize;

    let use_avx2 = detect_avx2();

    let mut sc: Vec<u8> = Vec::new();
    let mut tc: Vec<u8> = Vec::new();
    let mut prof: Vec<i32> = Vec::new();
    let mut a: Vec<i32> = Vec::new();
    let mut b: Vec<i32> = Vec::new();

    let mut out = String::with_capacity(p * 8 + 32);
    let mut total: i64 = 0;

    for _ in 0..p {
        let s = match it.next() {
            Some(x) => x,
            None => break,
        };
        let t = match it.next() {
            Some(x) => x,
            None => break,
        };
        sc.clear();
        sc.extend(s.iter().map(|&ch| map[ch as usize]));
        tc.clear();
        tc.extend(t.iter().map(|&ch| map[ch as usize]));

        let m = tc.len();
        let mp = (m + 7) & !7usize;

        if prof.len() < na * mp {
            prof.resize(na * mp, 0);
        }
        if a.len() < mp + 1 {
            a.resize(mp + 1, 0);
            b.resize(mp + 1, 0);
        }
        a[..mp + 1].fill(0);

        let mut pm: i64 = 0;
        for &c in tc.iter() {
            pm += ins[c as usize] as i64;
        }

        for c in 0..na {
            let row = &mut prof[c * mp..(c + 1) * mp];
            let srow = &sub[c * na..(c + 1) * na];
            for (r, &tj) in row.iter_mut().zip(tc.iter()) {
                let tj = tj as usize;
                *r = srow[tj] - ins[tj];
            }
            for r in row[m..].iter_mut() {
                *r = 0;
            }
        }

        let e = run_dp(use_avx2, &sc, &del, &prof, m, mp, &mut a, &mut b);
        let cost = e as i64 + pm;
        total += cost;
        out.push_str(&cost.to_string());
        out.push('\n');
    }

    out.push_str("total ");
    out.push_str(&total.to_string());
    out.push('\n');

    let stdout = std::io::stdout();
    let mut lock = stdout.lock();
    lock.write_all(out.as_bytes()).expect("write");
    lock.flush().expect("flush");
}
