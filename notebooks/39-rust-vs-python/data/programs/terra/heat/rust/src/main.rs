use std::env;
use std::fs;

struct Cell { i: usize, up: usize, down: usize, left: usize, right: usize }

fn main() {
    let input = fs::read(env::args_os().nth(1).expect("input path")).expect("read input");
    let mut lines = input.split(|&b| b == b'\n');
    let header = std::str::from_utf8(lines.next().unwrap()).unwrap();
    let mut numbers = header.split_whitespace().map(|s| s.parse::<usize>().unwrap());
    let (h, w, steps) = (numbers.next().unwrap(), numbers.next().unwrap(), numbers.next().unwrap());
    let mut grid = Vec::with_capacity(h * w);
    for _ in 0..h { grid.extend_from_slice(&lines.next().unwrap()[..w]); }
    let mut a = vec![0i32; h * w];
    let mut cells = Vec::new();
    for i in 0..grid.len() {
        match grid[i] {
            b'.' => {
                let (r, c) = (i / w, i % w);
                cells.push(Cell { i,
                    up: if r > 0 && grid[i-w] != b'#' { i-w } else { i },
                    down: if r+1 < h && grid[i+w] != b'#' { i+w } else { i },
                    left: if c > 0 && grid[i-1] != b'#' { i-1 } else { i },
                    right: if c+1 < w && grid[i+1] != b'#' { i+1 } else { i },
                });
            }
            b'1'..=b'9' => a[i] = i32::from(grid[i] - b'0') * 1000,
            _ => {}
        }
    }
    let mut b = a.clone();
    for _ in 0..steps {
        let mut changed = false;
        for cell in &cells {
            let v = (4 * a[cell.i] + a[cell.up] + a[cell.down] + a[cell.left] + a[cell.right]) >> 3;
            b[cell.i] = v;
            changed |= v != a[cell.i];
        }
        std::mem::swap(&mut a, &mut b);
        if !changed { break; }
    }
    let (mut sum, mut checksum) = (0i64, 0i64);
    let (mut max, mut max_i) = (-1, 0);
    for cell in &cells {
        let v = a[cell.i];
        sum += i64::from(v);
        checksum += i64::from(v) * (cell.i as i64 + 1);
        if v > max { max = v; max_i = cell.i; }
    }
    println!("sum {sum}\nmax {max} {} {}\nchecksum {checksum}", max_i / w, max_i % w);
}
