// Weighted edit distance for many string pairs.
//
// Rows are stored shifted: E[i][j] = D[i][j] - P[j], with P[j] the prefix sum of insertion
// costs along t. The recurrence then becomes
//     E[i][j] = min(E[i-1][j] + del[s_i], E[i-1][j-1] + sub[s_i][t_j] - ins[t_j], E[i][j-1])
// so the horizontal dependency is a plain running minimum, which is computed with an AVX2
// in-register prefix-min per block of 8 cells.

use std::io::Write;

struct Costs {
    a: usize,
    ins: Vec<i64>,
    del: Vec<i64>,
    sub: Vec<i64>, // row-major a x a
}

trait Cell: Copy + Ord + std::ops::Add<Output = Self> + std::ops::Sub<Output = Self> {
    fn from_i64(v: i64) -> Self;
    fn to_i64(self) -> i64;
}
impl Cell for i32 {
    #[inline(always)]
    fn from_i64(v: i64) -> Self {
        v as i32
    }
    #[inline(always)]
    fn to_i64(self) -> i64 {
        self as i64
    }
}
impl Cell for i64 {
    #[inline(always)]
    fn from_i64(v: i64) -> Self {
        v
    }
    #[inline(always)]
    fn to_i64(self) -> i64 {
        self
    }
}

#[inline(always)]
fn row_scalar<T: Cell>(prev: &[T], cur: &mut [T], prof: &[T], d: T, start: usize) {
    let m = prev.len() - 1;
    let mut run = cur[start - 1];
    for j in start..=m {
        let v = (prev[j] + d).min(prev[j - 1] + prof[j]);
        run = run.min(v);
        cur[j] = run;
    }
}

#[cfg(target_arch = "x86_64")]
#[target_feature(enable = "avx2")]
unsafe fn row_avx2(prev: &[i32], cur: &mut [i32], prof: &[i32], d: i32) {
    use std::arch::x86_64::*;
    let m = prev.len() - 1;
    debug_assert!(cur.len() == m + 1 && prof.len() == m + 1);
    unsafe {
        let pp = prev.as_ptr();
        let pc = cur.as_mut_ptr();
        let pf = prof.as_ptr();
        let dv = _mm256_set1_epi32(d);
        let inf = _mm256_set1_epi32(i32::MAX);
        let sh1 = _mm256_setr_epi32(0, 0, 1, 2, 3, 4, 5, 6);
        let sh2 = _mm256_setr_epi32(0, 0, 0, 1, 2, 3, 4, 5);
        let last = _mm256_set1_epi32(7);
        let mut carry = _mm256_set1_epi32(*pc);
        let mut j = 1usize;
        while j + 8 <= m + 1 {
            let up = _mm256_loadu_si256(pp.add(j) as *const __m256i);
            let dg = _mm256_loadu_si256(pp.add(j - 1) as *const __m256i);
            let pr = _mm256_loadu_si256(pf.add(j) as *const __m256i);
            let mut x = _mm256_min_epi32(_mm256_add_epi32(up, dv), _mm256_add_epi32(dg, pr));
            x = _mm256_min_epi32(
                x,
                _mm256_blend_epi32::<0b0000_0001>(_mm256_permutevar8x32_epi32(x, sh1), inf),
            );
            x = _mm256_min_epi32(
                x,
                _mm256_blend_epi32::<0b0000_0011>(_mm256_permutevar8x32_epi32(x, sh2), inf),
            );
            x = _mm256_min_epi32(x, _mm256_permute2x128_si256::<0x02>(x, inf));
            let blockmin = _mm256_permutevar8x32_epi32(x, last);
            _mm256_storeu_si256(pc.add(j) as *mut __m256i, _mm256_min_epi32(x, carry));
            carry = _mm256_min_epi32(carry, blockmin);
            j += 8;
        }
        if j <= m {
            row_scalar(prev, cur, prof, d, j);
        }
    }
}

fn solve<T: Cell>(s: &[u8], t: &[u8], ins: &[i64], del: &[i64], sub: &[i64], a: usize, simd: bool) -> i64 {
    let m = t.len();
    let mut pm = 0i64;
    for &c in t {
        pm += ins[c as usize];
    }
    // Profile rows only for letters that occur in s.
    let mut prof: Vec<Vec<T>> = (0..a).map(|_| Vec::new()).collect();
    for &c in s {
        let x = c as usize;
        if prof[x].is_empty() {
            let row = &sub[x * a..x * a + a];
            let mut p = Vec::with_capacity(m + 1);
            p.push(T::from_i64(0));
            for &y in t {
                p.push(T::from_i64(row[y as usize] - ins[y as usize]));
            }
            prof[x] = p;
        }
    }
    let mut prev: Vec<T> = vec![T::from_i64(0); m + 1];
    let mut cur: Vec<T> = vec![T::from_i64(0); m + 1];
    for &c in s {
        let d = T::from_i64(del[c as usize]);
        let pr = &prof[c as usize];
        cur[0] = prev[0] + d;
        #[cfg(target_arch = "x86_64")]
        {
            if simd {
                // SAFETY: T is i32 whenever simd is set, and AVX2 was detected at runtime.
                unsafe {
                    let pv = std::slice::from_raw_parts(prev.as_ptr() as *const i32, m + 1);
                    let cv = std::slice::from_raw_parts_mut(cur.as_mut_ptr() as *mut i32, m + 1);
                    let fv = std::slice::from_raw_parts(pr.as_ptr() as *const i32, m + 1);
                    row_avx2(pv, cv, fv, d.to_i64() as i32);
                }
                std::mem::swap(&mut prev, &mut cur);
                continue;
            }
        }
        let _ = simd;
        row_scalar(&prev, &mut cur, pr, d, 1);
        std::mem::swap(&mut prev, &mut cur);
    }
    prev[m].to_i64() + pm
}

fn main() {
    let path = std::env::args().nth(1).expect("usage: solution INPUT");
    let data = std::fs::read(&path).expect("cannot read input");
    let mut tok = data
        .split(|c| c.is_ascii_whitespace())
        .filter(|t| !t.is_empty());
    let alpha = tok.next().unwrap();
    let a = alpha.len();
    let mut map = [0u8; 256];
    for (i, &c) in alpha.iter().enumerate() {
        map[c as usize] = i as u8;
    }
    let mut num = || -> i64 {
        let t = tok.next().unwrap();
        let mut v = 0i64;
        for &b in t {
            v = v * 10 + (b - b'0') as i64;
        }
        v
    };
    let ins: Vec<i64> = (0..a).map(|_| num()).collect();
    let del: Vec<i64> = (0..a).map(|_| num()).collect();
    let sub: Vec<i64> = (0..a * a).map(|_| num()).collect();
    let p = num() as usize;
    let mut subt = vec![0i64; a * a];
    for x in 0..a {
        for y in 0..a {
            subt[y * a + x] = sub[x * a + y];
        }
    }
    let costs = Costs { a, ins, del, sub };

    #[cfg(target_arch = "x86_64")]
    let has_avx2 = is_x86_feature_detected!("avx2");
    #[cfg(not(target_arch = "x86_64"))]
    let has_avx2 = false;

    let mut out = String::with_capacity(p * 10 + 32);
    let mut total = 0i64;
    let mut sbuf = Vec::new();
    let mut tbuf = Vec::new();
    for _ in 0..p {
        let s = tok.next().unwrap();
        let t = tok.next().unwrap();
        sbuf.clear();
        sbuf.extend(s.iter().map(|&c| map[c as usize]));
        tbuf.clear();
        tbuf.extend(t.iter().map(|&c| map[c as usize]));
        // Keep the longer string along the rows; the transposed problem swaps ins/del and
        // transposes sub.
        let (rs, cs, ins, del, sub) = if sbuf.len() > tbuf.len() {
            (&tbuf, &sbuf, &costs.del, &costs.ins, &subt)
        } else {
            (&sbuf, &tbuf, &costs.ins, &costs.del, &costs.sub)
        };
        // |E| <= 1000 * (n + m) plus one cost term; stay well inside i32.
        let small = (rs.len() + cs.len()) < 1_000_000;
        let c = if small {
            solve::<i32>(rs, cs, ins, del, sub, costs.a, has_avx2)
        } else {
            solve::<i64>(rs, cs, ins, del, sub, costs.a, false)
        };
        total += c;
        out.push_str(&c.to_string());
        out.push('\n');
    }
    out.push_str("total ");
    out.push_str(&total.to_string());
    out.push('\n');
    std::io::stdout().lock().write_all(out.as_bytes()).unwrap();
}
