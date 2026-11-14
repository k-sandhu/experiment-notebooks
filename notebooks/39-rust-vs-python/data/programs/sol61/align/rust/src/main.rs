use std::fmt::Write as _;
use std::{
    env, fs,
    io::{self, Write},
};

// D[i,j] equals the delete/insert baseline for the two prefixes minus
// the maximum savings of an order-preserving set of substitutions.
fn savings(source: &[u8], target: &[u8], gain: &[[i64; 26]; 26], baseline: i64) -> i64 {
    #[cfg(target_arch = "x86_64")]
    if baseline <= i32::MAX as i64
        && target.len() >= 16
        && source.len() >= 16
        && std::is_x86_feature_detected!("avx2")
    {
        // Every intermediate score is bounded by the delete/insert baseline.
        return i64::from(unsafe { savings_avx2(source, target, gain) });
    }
    let mut row = vec![0_i64; target.len() + 1];
    for &letter in source {
        let weights = &gain[letter as usize];
        let mut diagonal = 0;
        let mut left = 0;
        for (&c, cell) in target.iter().zip(row[1..].iter_mut()) {
            let above = *cell;
            left = left.max(above).max(diagonal + weights[c as usize]);
            *cell = left;
            diagonal = above;
        }
    }
    row[target.len()]
}

#[cfg(target_arch = "x86_64")]
#[target_feature(enable = "avx2")]
unsafe fn savings_avx2(source: &[u8], target: &[u8], gain: &[[i64; 26]; 26]) -> i32 {
    use std::arch::x86_64::*;
    let width = target.len();
    let profiles: Vec<Vec<i32>> = gain
        .iter()
        .map(|weights| target.iter().map(|&c| weights[c as usize] as i32).collect())
        .collect();
    let mut previous = vec![0_i32; width + 1];
    let mut current = vec![0_i32; width + 1];
    let shift1 = _mm256_setr_epi32(0, 0, 1, 2, 3, 4, 5, 6);
    let shift2 = _mm256_setr_epi32(0, 0, 0, 1, 2, 3, 4, 5);
    let shift4 = _mm256_setr_epi32(0, 0, 0, 0, 0, 1, 2, 3);
    let last_lane = _mm256_set1_epi32(7);
    for &c in source {
        let weights = &profiles[c as usize];
        let mut carry = _mm256_setzero_si256();
        let mut j = 1;
        // All loads and stores cover eight in-bounds elements. The rows are
        // distinct allocations, so previous diagonals cannot be overwritten.
        unsafe {
            while j + 7 <= width {
                let diagonal = _mm256_loadu_si256(previous.as_ptr().add(j - 1).cast());
                let above = _mm256_loadu_si256(previous.as_ptr().add(j).cast());
                let weight = _mm256_loadu_si256(weights.as_ptr().add(j - 1).cast());
                let mut v = _mm256_max_epi32(above, _mm256_add_epi32(diagonal, weight));
                v = _mm256_max_epi32(v, carry);
                v = _mm256_max_epi32(v, _mm256_permutevar8x32_epi32(v, shift1));
                v = _mm256_max_epi32(v, _mm256_permutevar8x32_epi32(v, shift2));
                v = _mm256_max_epi32(v, _mm256_permutevar8x32_epi32(v, shift4));
                _mm256_storeu_si256(current.as_mut_ptr().add(j).cast(), v);
                carry = _mm256_permutevar8x32_epi32(v, last_lane);
                j += 8;
            }
        }
        let mut left = current[j - 1];
        while j <= width {
            left = left.max(previous[j]).max(previous[j - 1] + weights[j - 1]);
            current[j] = left;
            j += 1;
        }
        std::mem::swap(&mut previous, &mut current);
    }
    previous[width]
}

fn main() {
    let input = fs::read(env::args_os().nth(1).expect("input path")).expect("read input");
    let mut tokens = input
        .split(|c| c.is_ascii_whitespace())
        .filter(|s| !s.is_empty());
    let alphabet = tokens.next().unwrap();
    let size = alphabet.len();
    let mut mapping = [0_u8; 256];
    for (i, &c) in alphabet.iter().enumerate() {
        mapping[c as usize] = i as u8;
    }
    let number = |s: &[u8]| -> i64 { s.iter().fold(0, |n, &c| n * 10 + i64::from(c - b'0')) };
    let mut insert = [0_i64; 26];
    let mut delete = [0_i64; 26];
    for cost in &mut insert[..size] {
        *cost = number(tokens.next().unwrap());
    }
    for cost in &mut delete[..size] {
        *cost = number(tokens.next().unwrap());
    }
    let mut gain = [[0_i64; 26]; 26];
    let mut transposed = [[0_i64; 26]; 26];
    for i in 0..size {
        for j in 0..size {
            let w = delete[i] + insert[j] - number(tokens.next().unwrap());
            gain[i][j] = w;
            transposed[j][i] = w;
        }
    }
    let pairs = number(tokens.next().unwrap()) as usize;
    let mut output = String::new();
    let mut total = 0_i64;
    for _ in 0..pairs {
        let s = tokens.next().unwrap();
        let t = tokens.next().unwrap();
        let cost = if s == t {
            0
        } else {
            let source: Vec<u8> = s.iter().map(|&c| mapping[c as usize]).collect();
            let target: Vec<u8> = t.iter().map(|&c| mapping[c as usize]).collect();
            let baseline: i64 = source.iter().map(|&c| delete[c as usize]).sum::<i64>()
                + target.iter().map(|&c| insert[c as usize]).sum::<i64>();
            let best = if baseline == 0 {
                0
            } else if source.len() >= target.len() {
                savings(&source, &target, &gain, baseline)
            } else {
                savings(&target, &source, &transposed, baseline)
            };
            baseline - best
        };
        total += cost;
        writeln!(output, "{cost}").unwrap();
    }
    writeln!(output, "total {total}").unwrap();
    io::BufWriter::new(io::stdout().lock())
        .write_all(output.as_bytes())
        .unwrap();
}
