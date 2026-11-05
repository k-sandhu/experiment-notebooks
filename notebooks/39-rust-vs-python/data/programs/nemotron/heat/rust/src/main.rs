use std::env;
use std::fs;
use std::io::Write;

struct Cell {
    idx: usize,
    o_up: isize,
    o_down: isize,
    o_left: isize,
    o_right: isize,
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("usage: solution <input-file>");
        std::process::exit(2);
    }
    let text = fs::read_to_string(&args[1]).expect("failed to read input file");
    let mut lines = text.split('\n');
    let header = lines.next().unwrap_or("").trim_end_matches('\r');
    let mut nums = header.split_whitespace();
    let H: usize = nums.next().unwrap_or("0").parse().expect("invalid H");
    let W: usize = nums.next().unwrap_or("0").parse().expect("invalid W");
    let S: usize = nums.next().unwrap_or("0").parse().expect("invalid S");

    let mut grid: Vec<u8> = Vec::with_capacity(H * W);
    let mut cur: Vec<i32> = Vec::with_capacity(H * W);
    for r in 0..H {
        let line = lines.next().unwrap_or("").trim_end_matches('\r');
        let b = line.as_bytes();
        for c in 0..W {
            let ch = *b.get(c).unwrap_or(&b'#');
            grid.push(ch);
            cur.push(match ch {
                b'.' => 0,
                b'#' => 0,
                d @ b'1'..=b'9' => 1000 * (d - b'0') as i32,
                _ => 0,
            });
        }
    }

    // Precompute, for every open cell, the flat index of each of its four
    // neighbours. A neighbour that is a wall or outside the grid is replaced
    // by the cell itself, which implements "use the cell's own old value".
    let mut cells: Vec<Cell> = Vec::new();
    for r in 0..H {
        let base = r * W;
        for c in 0..W {
            let i = base + c;
            if grid[i] != b'.' {
                continue;
            }
            let o_up = if r > 0 && grid[i - W] != b'#' {
                (i - W) as isize
            } else {
                i as isize
            };
            let o_down = if r + 1 < H && grid[i + W] != b'#' {
                (i + W) as isize
            } else {
                i as isize
            };
            let o_left = if c > 0 && grid[i - 1] != b'#' {
                (i - 1) as isize
            } else {
                i as isize
            };
            let o_right = if c + 1 < W && grid[i + 1] != b'#' {
                (i + 1) as isize
            } else {
                i as isize
            };
            cells.push(Cell {
                idx: i,
                o_up,
                o_down,
                o_left,
                o_right,
            });
        }
    }

    let mut nxt = cur.clone();
    for _ in 0..S {
        for cell in &cells {
            let i = cell.idx;
            let v = cur[i];
            let acc = 4 * v
                + cur[cell.o_up as usize]
                + cur[cell.o_down as usize]
                + cur[cell.o_left as usize]
                + cur[cell.o_right as usize];
            nxt[i] = acc >> 3;
        }
        std::mem::swap(&mut cur, &mut nxt);
    }

    let mut total: i64 = 0;
    let mut maxv: i32 = -1;
    let mut maxr: usize = 0;
    let mut maxc: usize = 0;
    let mut chk: i64 = 0;
    for r in 0..H {
        let base = r * W;
        for c in 0..W {
            let i = base + c;
            if grid[i] != b'.' {
                continue;
            }
            let v = cur[i];
            total += v as i64;
            chk += v as i64 * (i + 1) as i64;
            if v > maxv {
                maxv = v;
                maxr = r;
                maxc = c;
            }
        }
    }

    let mut out = std::io::stdout().lock();
    writeln!(out, "sum {}", total).unwrap();
    writeln!(out, "max {} {} {}", maxv, maxr, maxc).unwrap();
    writeln!(out, "checksum {}", chk).unwrap();
}
