use std::fmt::Write as FmtWrite;
use std::io::{self, Write as IoWrite};
use std::ops::Add;

struct Scanner<'a> {
    data: &'a [u8],
    pos: usize,
}

impl<'a> Scanner<'a> {
    fn next(&mut self) -> &'a [u8] {
        while self.pos < self.data.len() && self.data[self.pos].is_ascii_whitespace() {
            self.pos += 1;
        }
        let start = self.pos;
        while self.pos < self.data.len() && !self.data[self.pos].is_ascii_whitespace() {
            self.pos += 1;
        }
        &self.data[start..self.pos]
    }

    fn number(&mut self) -> usize {
        self.next()
            .iter()
            .fold(0, |value, &digit| value * 10 + (digit - b'0') as usize)
    }
}

struct Costs {
    ins: [u16; 26],
    del: [u16; 26],
    sub: [[u16; 26]; 26],
}

fn alignment<T>(s: &[u8], t: &[u8], costs: &Costs, alphabet_size: usize) -> T
where
    T: Copy + Ord + From<u16> + Add<Output = T>,
{
    let m = t.len();
    let zero = T::from(0u16);

    let mut insertion = Vec::with_capacity(m);
    let mut dp = Vec::with_capacity(m + 1);
    dp.push(zero);

    let mut cumulative = zero;
    for &letter in t {
        let cost = T::from(costs.ins[letter as usize]);
        insertion.push(cost);
        cumulative = cumulative + cost;
        dp.push(cumulative);
    }

    // Expand substitution rows into target order for sequential inner-loop reads.
    let mut substitutions = Vec::with_capacity(alphabet_size * m);
    for row in &costs.sub[..alphabet_size] {
        for &letter in t {
            substitutions.push(T::from(row[letter as usize]));
        }
    }

    for &letter in s {
        let deletion = T::from(costs.del[letter as usize]);
        let start = letter as usize * m;
        let row = &substitutions[start..start + m];

        let mut diagonal = dp[0];
        let mut left = diagonal + deletion;
        dp[0] = left;

        for ((cell, &insert_cost), &substitute_cost) in dp[1..]
            .iter_mut()
            .zip(insertion.iter())
            .zip(row.iter())
        {
            let above = *cell;
            let best = (above + deletion)
                .min(left + insert_cost)
                .min(diagonal + substitute_cost);
            *cell = best;
            diagonal = above;
            left = best;
        }
    }

    dp[m]
}

fn main() {
    let path = std::env::args_os().nth(1).unwrap();
    let data = std::fs::read(path).unwrap();
    let mut input = Scanner {
        data: &data,
        pos: 0,
    };

    let alphabet = input.next();
    let alphabet_size = alphabet.len();
    let mut mapping = [0u8; 256];
    for (index, &letter) in alphabet.iter().enumerate() {
        mapping[letter as usize] = index as u8;
    }

    let mut forward = Costs {
        ins: [0; 26],
        del: [0; 26],
        sub: [[0; 26]; 26],
    };

    for value in &mut forward.ins[..alphabet_size] {
        *value = input.number() as u16;
    }
    for value in &mut forward.del[..alphabet_size] {
        *value = input.number() as u16;
    }
    for row in &mut forward.sub[..alphabet_size] {
        for value in &mut row[..alphabet_size] {
            *value = input.number() as u16;
        }
    }

    // Transposing the recurrence lets the shorter string define the DP width.
    let mut reverse = Costs {
        ins: forward.del,
        del: forward.ins,
        sub: [[0; 26]; 26],
    };
    for i in 0..alphabet_size {
        for j in 0..alphabet_size {
            reverse.sub[i][j] = forward.sub[j][i];
        }
    }

    let pairs = input.number();
    let mut output = String::new();
    let mut total = 0u64;

    for _ in 0..pairs {
        let raw_s = input.next();
        let raw_t = input.next();

        if raw_s == raw_t {
            output.push_str("0\n");
            continue;
        }

        let s: Vec<u8> = raw_s.iter().map(|&c| mapping[c as usize]).collect();
        let t: Vec<u8> = raw_t.iter().map(|&c| mapping[c as usize]).collect();

        let (source, target, costs) = if s.len() >= t.len() {
            (s.as_slice(), t.as_slice(), &forward)
        } else {
            (t.as_slice(), s.as_slice(), &reverse)
        };

        let upper_bound = source
            .iter()
            .map(|&c| costs.del[c as usize] as u64)
            .sum::<u64>()
            + target
                .iter()
                .map(|&c| costs.ins[c as usize] as u64)
                .sum::<u64>();

        let answer = if upper_bound <= u32::MAX as u64 - 1000 {
            alignment::<u32>(source, target, costs, alphabet_size) as u64
        } else {
            alignment::<u64>(source, target, costs, alphabet_size)
        };

        total += answer;
        writeln!(&mut output, "{answer}").unwrap();
    }

    writeln!(&mut output, "total {total}").unwrap();
    let stdout = io::stdout();
    stdout.lock().write_all(output.as_bytes()).unwrap();
}
