use std::env;
use std::fs;
use std::io::{self, Write};
use std::process::ExitCode;

fn parse_usize(bytes: &[u8], pos: &mut usize) -> usize {
    // skip whitespace
    while *pos < bytes.len() && bytes[*pos].is_ascii_whitespace() {
        *pos += 1;
    }
    let mut v: usize = 0;
    while *pos < bytes.len() && bytes[*pos].is_ascii_digit() {
        v = v * 10 + (bytes[*pos] - b'0') as usize;
        *pos += 1;
    }
    v
}

fn main() -> ExitCode {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        return ExitCode::from(2);
    }
    let data = match fs::read(&args[1]) {
        Ok(d) => d,
        Err(_) => return ExitCode::from(2),
    };

    let mut pos = 0usize;
    let h = parse_usize(&data, &mut pos);
    let w = parse_usize(&data, &mut pos);
    let s = parse_usize(&data, &mut pos);

    if h == 0 || w == 0 {
        return ExitCode::from(2);
    }

    // Padded layout: stride = w+2, rows h+2, border cells are 0 and never written.
    let stride = w + 2;
    let padded_size = stride * (h + 2);

    let mut cur = vec![0i32; padded_size];
    let mut nxt = vec![0i32; padded_size];

    // is_wall for unpadded cells, needed only while building coef.
    let mut is_wall = vec![false; h * w];

    // First pass: read grid characters.
    // pos is after the S token; grid rows follow. Skip line endings, then take w chars per row.
    // Store raw chars in a temporary buffer to classify after wall info is known?
    // We classify in one pass, storing source values directly into cur/nxt, and
    // remember wall positions. Open-cell list & coef need wall neighbours, so
    // collect cell kinds first in a compact array.
    // kind: 0 open, 1 wall, 2 source (value in src_val)
    let mut kind = vec![0u8; h * w];
    let mut src_val = vec![0i32; h * w];

    {
        let mut idx = 0usize;
        let n = h * w;
        let mut p = pos;
        while idx < n && p < data.len() {
            let b = data[p];
            // Skip whitespace between / inside rows (newlines, CRLF, spaces are not
            // valid cell chars, so skipping whitespace is safe).
            if b == b'\n' || b == b'\r' {
                p += 1;
                continue;
            }
            match b {
                b'.' => {
                    kind[idx] = 0;
                }
                b'#' => {
                    kind[idx] = 1;
                    is_wall[idx] = true;
                }
                b'1'..=b'9' => {
                    kind[idx] = 2;
                    src_val[idx] = 1000 * (b - b'0') as i32;
                }
                _ => {
                    // Unexpected byte: treat as separator and move on.
                    p += 1;
                    continue;
                }
            }
            idx += 1;
            p += 1;
        }
    }

    // Fill padded buffers with fixed values (sources), walls stay 0.
    for r in 0..h {
        let base_padded = (r + 1) * stride + 1;
        let base = r * w;
        for c in 0..w {
            let k = kind[base + c];
            if k == 2 {
                let v = src_val[base + c];
                cur[base_padded + c] = v;
                nxt[base_padded + c] = v;
            }
        }
    }

    // coef[i] = 4 + (number of invalid neighbours) for open cells, stored
    // at padded index. Neighbour sum uses raw padded values (walls/border = 0),
    // so total = coef*old + up+down+left+right, new = total >> 3 (values >= 0).
    let mut open_idx: Vec<u32> = Vec::new();
    let mut open_coef: Vec<u8> = Vec::new();
    // open_orig: original flat index r*w+c for output phase, in row-major order
    let mut open_orig: Vec<u32> = Vec::new();

    for r in 0..h {
        for c in 0..w {
            let i = r * w + c;
            if kind[i] != 0 {
                continue;
            }
            let mut invalid: u8 = 0;
            // up
            if r == 0 || is_wall[i - w] {
                invalid += 1;
            }
            // down
            if r + 1 == h || is_wall[i + w] {
                invalid += 1;
            }
            // left
            if c == 0 || is_wall[i - 1] {
                invalid += 1;
            }
            // right
            if c + 1 == w || is_wall[i + 1] {
                invalid += 1;
            }
            let padded = (r + 1) * stride + (c + 1);
            open_idx.push(padded as u32);
            open_coef.push(4 + invalid);
            open_orig.push(i as u32);
        }
    }

    let stride_i = stride as i32;
    for _ in 0..s {
        // SAFETY: open_idx contains only valid padded indices for interior
        // cells (1..=h rows, 1..=w cols), so i-stride, i+stride, i-1, i+1
        // are all within the padded allocation. cur/nxt have padded_size elems.
        unsafe {
            let cur_ptr = cur.as_ptr();
            let nxt_ptr = nxt.as_mut_ptr();
            for k in 0..open_idx.len() {
                let i = *open_idx.get_unchecked(k) as usize;
                let coef = *open_coef.get_unchecked(k) as i32;
                let center = *cur_ptr.add(i);
                let sum = coef * center
                    + *cur_ptr.add(i.wrapping_sub(stride))
                    + *cur_ptr.add(i + stride)
                    + *cur_ptr.add(i - 1)
                    + *cur_ptr.add(i + 1);
                *nxt_ptr.add(i) = sum >> 3;
            }
        }
        std::mem::swap(&mut cur, &mut nxt);
        let _ = stride_i;
    }

    // Output stats over open cells in row-major order.
    let mut sum: i64 = 0;
    let mut checksum: i64 = 0;
    let mut best: i32 = -1;
    let mut best_r: usize = 0;
    let mut best_c: usize = 0;

    for k in 0..open_idx.len() {
        let padded = open_idx[k] as usize;
        let orig = open_orig[k] as usize;
        let v = cur[padded] as i64;
        sum += v;
        checksum += v * (orig as i64 + 1);
        if (v as i32) > best {
            best = v as i32;
            best_r = orig / w;
            best_c = orig % w;
        }
    }
    if open_idx.is_empty() {
        // Spec guarantees at least one open cell, but avoid nonsense output.
        best = 0;
    }

    let stdout = io::stdout();
    let mut out = io::BufWriter::new(stdout.lock());
    let _ = writeln!(out, "sum {}", sum);
    let _ = writeln!(out, "max {} {} {}", best, best_r, best_c);
    let _ = writeln!(out, "checksum {}", checksum);
    ExitCode::SUCCESS
}
