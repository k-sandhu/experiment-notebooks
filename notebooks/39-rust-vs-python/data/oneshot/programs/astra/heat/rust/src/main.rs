use std::io::{self, Write};

fn parse_usize(bytes: &[u8]) -> usize {
    bytes.iter().fold(0, |n, &b| n * 10 + usize::from(b - b'0'))
}

#[inline]
fn step(src: &[u16], dst: &mut [u16], tags: &[u16], stride: usize) {
    let end = src.len() - stride;

    // Both buffers and tags have identical padded dimensions.
    for i in stride..end {
        unsafe {
            let old = *src.get_unchecked(i);
            let tag = *tags.get_unchecked(i);
            let blocked = tag & 7;

            // The four effective neighbours total at most 36000.
            // Splitting 4*old this way keeps all arithmetic within u16.
            let neighbours = *src.get_unchecked(i - stride)
                + *src.get_unchecked(i + stride)
                + *src.get_unchecked(i - 1)
                + *src.get_unchecked(i + 1)
                + old * blocked;

            let next = (old >> 1) + ((neighbours + ((old & 1) << 2)) >> 3);
            let open_mask = ((tag as i16) >> 15) as u16;

            *dst.get_unchecked_mut(i) =
                (next & open_mask) | (old & !open_mask);
        }
    }
}

fn main() {
    let path = std::env::args_os().nth(1).unwrap();
    let input = std::fs::read(path).unwrap();
    let mut tokens = input
        .split(|b| b.is_ascii_whitespace())
        .filter(|s| !s.is_empty());

    let h = parse_usize(tokens.next().unwrap());
    let w = parse_usize(tokens.next().unwrap());
    let steps = parse_usize(tokens.next().unwrap());

    let stride = w + 2;
    let size = (h + 2) * stride;
    let mut grid = vec![b'#'; size];

    for r in 0..h {
        let row = tokens.next().unwrap();
        let start = (r + 1) * stride + 1;
        grid[start..start + w].copy_from_slice(row);
    }

    let mut current = vec![0u16; size];
    let mut tags = vec![0u16; size];
    let mut has_source = false;

    for r in 0..h {
        for c in 0..w {
            let i = (r + 1) * stride + c + 1;
            match grid[i] {
                b'.' => {
                    let blocked = u16::from(grid[i - stride] == b'#')
                        + u16::from(grid[i + stride] == b'#')
                        + u16::from(grid[i - 1] == b'#')
                        + u16::from(grid[i + 1] == b'#');
                    tags[i] = 0x8000 | blocked;
                }
                b'1'..=b'9' => {
                    current[i] = u16::from(grid[i] - b'0') * 1000;
                    has_source = true;
                }
                _ => {}
            }
        }
    }

    if has_source && steps != 0 {
        let mut next = current.clone();
        for _ in 0..steps {
            step(&current, &mut next, &tags, stride);
            std::mem::swap(&mut current, &mut next);
        }
    }

    let mut total = 0i64;
    let mut checksum = 0i64;
    let mut maximum = -1i64;
    let mut best_row = 0usize;
    let mut best_col = 0usize;

    for r in 0..h {
        for c in 0..w {
            let i = (r + 1) * stride + c + 1;
            if grid[i] == b'.' {
                let value = i64::from(current[i]);
                total += value;
                checksum += value * ((r * w + c + 1) as i64);

                if value > maximum {
                    maximum = value;
                    best_row = r;
                    best_col = c;
                }
            }
        }
    }

    let stdout = io::stdout();
    let mut out = io::BufWriter::new(stdout.lock());
    writeln!(out, "sum {total}").unwrap();
    writeln!(out, "max {maximum} {best_row} {best_col}").unwrap();
    writeln!(out, "checksum {checksum}").unwrap();
}
