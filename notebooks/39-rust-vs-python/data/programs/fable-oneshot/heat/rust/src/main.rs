use std::io::Write;

fn aligned_offset(v: &[u16]) -> usize {
    let a = v.as_ptr() as usize;
    ((64 - (a & 63)) & 63) / 2
}

#[cfg(target_arch = "x86_64")]
#[target_feature(enable = "avx2")]
unsafe fn run_avx2(
    cur: *mut u16,
    km: *const u16,
    pend: *mut u16,
    st: usize,
    last_row: usize,
    steps: usize,
) {
    use std::arch::x86_64::*;
    unsafe {
        let zero = _mm256_setzero_si256();
        for _ in 0..steps {
            for r in 1..=last_row {
                let mid = cur.add(r * st);
                let up = mid.sub(st);
                let down = mid.add(st);
                let kr = km.add(r * st);
                let mut j = 0usize;
                while j < st {
                    let o = _mm256_loadu_si256(mid.add(j) as *const __m256i);
                    let u = _mm256_loadu_si256(up.add(j) as *const __m256i);
                    let d = _mm256_loadu_si256(down.add(j) as *const __m256i);
                    let l = _mm256_loadu_si256(mid.add(j).sub(1) as *const __m256i);
                    let rr = _mm256_loadu_si256(mid.add(j + 1) as *const __m256i);
                    let k = _mm256_loadu_si256(kr.add(j) as *const __m256i);
                    let s = _mm256_add_epi16(_mm256_add_epi16(u, d), _mm256_add_epi16(l, rr));
                    let s = _mm256_add_epi16(s, _mm256_mullo_epi16(k, o));
                    let q = _mm256_srli_epi16::<2>(s);
                    let df = _mm256_srai_epi16::<1>(_mm256_sub_epi16(q, o));
                    let nonopen = _mm256_cmpgt_epi16(zero, k);
                    let n = _mm256_add_epi16(o, _mm256_andnot_si256(nonopen, df));
                    let p = _mm256_loadu_si256(pend.add(j) as *const __m256i);
                    _mm256_storeu_si256(up.add(j) as *mut __m256i, p);
                    _mm256_storeu_si256(pend.add(j) as *mut __m256i, n);
                    j += 16;
                }
            }
        }
    }
}

fn run_scalar(cur: &mut [u16], km: &[u16], st: usize, last_row: usize, steps: usize) {
    let mut pend = vec![0u16; st];
    let mut tmp = vec![0u16; st];
    for _ in 0..steps {
        for r in 1..=last_row {
            let base = r * st;
            {
                let up = &cur[base - st..base];
                let mid = &cur[base..base + st];
                let left = &cur[base - 1..base - 1 + st];
                let right = &cur[base + 1..base + 1 + st];
                let down = &cur[base + st..base + 2 * st];
                let kk = &km[base..base + st];
                let out = &mut tmp[..st];
                for i in 0..st {
                    let o = mid[i];
                    let k = kk[i];
                    let s = up[i]
                        .wrapping_add(down[i])
                        .wrapping_add(left[i])
                        .wrapping_add(right[i])
                        .wrapping_add(k.wrapping_mul(o));
                    let q = s >> 2;
                    let d = ((q.wrapping_sub(o)) as i16) >> 1;
                    let m: u16 = if (k as i16) < 0 { 0 } else { 0xFFFF };
                    out[i] = o.wrapping_add((d as u16) & m);
                }
            }
            cur[base - st..base].copy_from_slice(&pend);
            std::mem::swap(&mut pend, &mut tmp);
        }
    }
}

#[cfg(target_arch = "x86_64")]
fn simulate(cur: &mut [u16], km: &[u16], st: usize, last_row: usize, steps: usize) {
    if is_x86_feature_detected!("avx2") {
        let mut pend_vec = vec![0u16; st + 32];
        let poff = aligned_offset(&pend_vec);
        let pend = &mut pend_vec[poff..poff + st];
        unsafe {
            run_avx2(
                cur.as_mut_ptr(),
                km.as_ptr(),
                pend.as_mut_ptr(),
                st,
                last_row,
                steps,
            );
        }
        return;
    }
    run_scalar(cur, km, st, last_row, steps);
}

#[cfg(not(target_arch = "x86_64"))]
fn simulate(cur: &mut [u16], km: &[u16], st: usize, last_row: usize, steps: usize) {
    run_scalar(cur, km, st, last_row, steps);
}

fn main() {
    let path = std::env::args().nth(1).expect("missing input path");
    let data = std::fs::read(&path).expect("cannot read input");
    let len = data.len();
    let mut pos = 0usize;

    let mut nums = [0usize; 3];
    let mut cnt = 0;
    while cnt < 3 && pos < len {
        while pos < len && !data[pos].is_ascii_digit() {
            pos += 1;
        }
        let mut v = 0usize;
        while pos < len && data[pos].is_ascii_digit() {
            v = v * 10 + (data[pos] - b'0') as usize;
            pos += 1;
        }
        nums[cnt] = v;
        cnt += 1;
    }
    while pos < len && data[pos] != b'\n' {
        pos += 1;
    }
    pos += 1;

    let h = nums[0];
    let w = nums[1];
    let steps = nums[2];

    let st = (w + 2 + 15) & !15usize;
    let total = (h + 3) * st;

    let mut cur_vec = vec![0u16; total + 32];
    let coff = aligned_offset(&cur_vec);
    let mut km_vec = vec![0xFFFFu16; total + 32];
    let koff = aligned_offset(&km_vec);
    let mut t = vec![0u8; total];

    {
        let cur = &mut cur_vec[coff..coff + total];
        for r in 0..h {
            if pos > len {
                pos = len;
            }
            let start = pos;
            let end = data[start..]
                .iter()
                .position(|&b| b == b'\n')
                .map(|p| start + p)
                .unwrap_or(len);
            let mut line = &data[start..end];
            if let Some(&b'\r') = line.last() {
                line = &line[..line.len() - 1];
            }
            pos = end + 1;
            let n = w.min(line.len());
            let base = (r + 1) * st + 1;
            for c in 0..n {
                let b = line[c];
                if b == b'.' {
                    t[base + c] = 1;
                } else if (b'1'..=b'9').contains(&b) {
                    t[base + c] = 2;
                    cur[base + c] = 1000 * (b - b'0') as u16;
                }
            }
        }
    }

    {
        let km = &mut km_vec[koff..koff + total];
        for r in 0..h {
            let base = (r + 1) * st + 1;
            for c in 0..w {
                let idx = base + c;
                if t[idx] == 1 {
                    let k = (t[idx - st] == 0) as u16
                        + (t[idx + st] == 0) as u16
                        + (t[idx - 1] == 0) as u16
                        + (t[idx + 1] == 0) as u16;
                    km[idx] = k;
                }
            }
        }
    }

    {
        let cur = &mut cur_vec[coff..coff + total];
        let km = &km_vec[koff..koff + total];
        simulate(cur, km, st, h + 1, steps);
    }

    let cur = &cur_vec[coff..coff + total];
    let mut sum: i64 = 0;
    let mut checksum: i64 = 0;
    let mut best_v: i64 = -1;
    let mut best_r = 0usize;
    let mut best_c = 0usize;
    for r in 0..h {
        let base = (r + 1) * st + 1;
        let row = &cur[base..base + w];
        let trow = &t[base..base + w];
        let wbase = (r * w + 1) as i64;
        for c in 0..w {
            if trow[c] == 1 {
                let v = row[c] as i64;
                sum += v;
                checksum += v * (wbase + c as i64);
                if v > best_v {
                    best_v = v;
                    best_r = r;
                    best_c = c;
                }
            }
        }
    }
    if best_v < 0 {
        best_v = 0;
    }

    let out = format!(
        "sum {}\nmax {} {} {}\nchecksum {}\n",
        sum, best_v, best_r, best_c, checksum
    );
    let stdout = std::io::stdout();
    let mut lock = stdout.lock();
    let _ = lock.write_all(out.as_bytes());
    let _ = lock.flush();
}
