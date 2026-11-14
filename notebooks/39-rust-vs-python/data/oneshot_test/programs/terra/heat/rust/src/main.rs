use std::env;
use std::fs;

struct Cell {
    pos: usize,
    coefficient: u32,
}

fn main() {
    let path = env::args_os().nth(1).expect("missing input path");
    let input = fs::read(path).expect("failed to read input");
    let mut tokens = input.split(|b| b.is_ascii_whitespace()).filter(|s| !s.is_empty());

    let h: usize = std::str::from_utf8(tokens.next().unwrap()).unwrap().parse().unwrap();
    let w: usize = std::str::from_utf8(tokens.next().unwrap()).unwrap().parse().unwrap();
    let steps: usize = std::str::from_utf8(tokens.next().unwrap()).unwrap().parse().unwrap();

    let stride = w + 2;
    let size = (h + 2) * stride;
    // 0 = wall or outside, 1 = open, 2 = source.
    let mut kind = vec![0u8; size];
    let mut current = vec![0u16; size];
    let mut next = vec![0u16; size];

    for r in 0..h {
        let row = tokens.next().unwrap();
        for c in 0..w {
            let pos = (r + 1) * stride + c + 1;
            match row[c] {
                b'.' => kind[pos] = 1,
                b'#' => {}
                digit @ b'1'..=b'9' => {
                    kind[pos] = 2;
                    let value = u16::from(digit - b'0') * 1000;
                    current[pos] = value;
                    next[pos] = value;
                }
                _ => unreachable!(),
            }
        }
    }

    let mut cells = Vec::new();
    for r in 0..h {
        for c in 0..w {
            let pos = (r + 1) * stride + c + 1;
            if kind[pos] == 1 {
                let walls = u32::from(kind[pos - stride] == 0)
                    + u32::from(kind[pos + stride] == 0)
                    + u32::from(kind[pos - 1] == 0)
                    + u32::from(kind[pos + 1] == 0);
                cells.push(Cell {
                    pos,
                    coefficient: 4 + walls,
                });
            }
        }
    }

    for _ in 0..steps {
        let src = current.as_ptr();
        let dst = next.as_mut_ptr();

        for cell in &cells {
            let p = cell.pos;
            // Padding makes all four neighbor positions valid. Walls contain zero;
            // their contributions are included in the cell's coefficient instead.
            unsafe {
                let value = u32::from(*src.add(p)) * cell.coefficient
                    + u32::from(*src.add(p - stride))
                    + u32::from(*src.add(p + stride))
                    + u32::from(*src.add(p - 1))
                    + u32::from(*src.add(p + 1));
                *dst.add(p) = (value >> 3) as u16;
            }
        }

        std::mem::swap(&mut current, &mut next);
    }

    let mut sum = 0i64;
    let mut checksum = 0i64;
    let mut max_value = -1i64;
    let mut max_row = 0usize;
    let mut max_col = 0usize;

    for cell in &cells {
        let p = cell.pos;
        let row = p / stride - 1;
        let col = p % stride - 1;
        let value = i64::from(current[p]);

        sum += value;
        checksum += value * (row * w + col + 1) as i64;
        if value > max_value {
            max_value = value;
            max_row = row;
            max_col = col;
        }
    }

    println!("sum {sum}");
    println!("max {max_value} {max_row} {max_col}");
    println!("checksum {checksum}");
}
