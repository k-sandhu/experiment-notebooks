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

impl Costs {
    fn new() -> Self {
        Self {
            ins: [0; 26],
            del: [0; 26],
            sub: [[0; 26]; 26],
        }
    }
}

struct Workspace<T> {
    dp: Vec<T>,
    insertions: Vec<T>,
    profiles: Vec<T>,
}

impl<T> Workspace<T> {
    fn new() -> Self {
        Self {
            dp: Vec::new(),
            insertions: Vec::new(),
            profiles: Vec::new(),
        }
    }
}

fn distance<T>(
    source: &[u8],
    target: &[u8],
    alphabet_size: usize,
    mapping: &[usize; 256],
    costs: &Costs,
    workspace: &mut Workspace<T>,
) -> u64
where
    T: Copy + Ord + Add<Output = T> + From<u16> + Into<u64>,
{
    let m = target.len();
    let zero = T::from(0u16);

    workspace.dp.resize(m + 1, zero);
    workspace.insertions.resize(m, zero);
    workspace.profiles.resize(alphabet_size * m, zero);

    workspace.dp[0] = zero;
    let mut prefix = zero;
    for (j, &letter) in target.iter().enumerate() {
        let insertion = T::from(costs.ins[mapping[letter as usize]]);
        workspace.insertions[j] = insertion;
        prefix = prefix + insertion;
        workspace.dp[j + 1] = prefix;
    }

    for (letter, profile) in workspace.profiles.chunks_exact_mut(m).enumerate() {
        let substitutions = &costs.sub[letter];
        for (entry, &target_letter) in profile.iter_mut().zip(target.iter()) {
            *entry = T::from(substitutions[mapping[target_letter as usize]]);
        }
    }

    for &source_letter in source {
        let letter = mapping[source_letter as usize];
        let deletion = T::from(costs.del[letter]);
        let start = letter * m;
        let profile = &workspace.profiles[start..start + m];

        let mut diagonal = workspace.dp[0];
        let mut left = diagonal + deletion;
        workspace.dp[0] = left;

        for ((cell, &insertion), &substitution) in workspace.dp[1..]
            .iter_mut()
            .zip(workspace.insertions.iter())
            .zip(profile.iter())
        {
            let above = *cell;
            let value = (above + deletion)
                .min(left + insertion)
                .min(diagonal + substitution);
            *cell = value;
            diagonal = above;
            left = value;
        }
    }

    workspace.dp[m].into()
}

fn main() {
    let path = std::env::args_os().nth(1).unwrap();
    let input = std::fs::read(path).unwrap();
    let mut scanner = Scanner {
        data: &input,
        pos: 0,
    };

    let alphabet = scanner.next();
    let a = alphabet.len();
    let mut mapping = [0usize; 256];
    for (index, &letter) in alphabet.iter().enumerate() {
        mapping[letter as usize] = index;
    }

    let mut forward = Costs::new();
    for i in 0..a {
        forward.ins[i] = scanner.number() as u16;
    }
    for i in 0..a {
        forward.del[i] = scanner.number() as u16;
    }
    for i in 0..a {
        for j in 0..a {
            forward.sub[i][j] = scanner.number() as u16;
        }
    }

    let mut reverse = Costs::new();
    for i in 0..a {
        reverse.ins[i] = forward.del[i];
        reverse.del[i] = forward.ins[i];
        for j in 0..a {
            reverse.sub[i][j] = forward.sub[j][i];
        }
    }

    let pairs = scanner.number();
    let mut small = Workspace::<u32>::new();
    let mut large = Workspace::<u64>::new();
    let mut output = String::new();
    let mut total = 0u64;

    for _ in 0..pairs {
        let s = scanner.next();
        let t = scanner.next();

        let cost = if s == t {
            0
        } else {
            let (source, target, costs) = if s.len() >= t.len() {
                (s, t, &forward)
            } else {
                (t, s, &reverse)
            };

            // Every cell is bounded by deleting its source prefix and
            // inserting its target prefix. Reserve room for one extra cost.
            if source.len().saturating_add(target.len())
                <= ((u32::MAX - 1000) / 1000) as usize
            {
                distance(source, target, a, &mapping, costs, &mut small)
            } else {
                distance(source, target, a, &mapping, costs, &mut large)
            }
        };

        total += cost;
        writeln!(&mut output, "{cost}").unwrap();
    }

    writeln!(&mut output, "total {total}").unwrap();
    let stdout = io::stdout();
    let mut writer = io::BufWriter::new(stdout.lock());
    writer.write_all(output.as_bytes()).unwrap();
    writer.flush().unwrap();
}
