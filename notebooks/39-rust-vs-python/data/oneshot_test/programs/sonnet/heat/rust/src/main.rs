use std::io::Write;

fn main() {
    let path = std::env::args().nth(1).expect("path");
    let text = std::fs::read_to_string(path).expect("read");
    let mut it = text.split_whitespace();
    let h: usize = it.next().unwrap().parse().unwrap();
    let w: usize = it.next().unwrap().parse().unwrap();
    let steps: usize = it.next().unwrap().parse().unwrap();
    let wp = w + 2;
    let hp = h + 2;
    let n = wp * hp;

    // kind: 0 wall/outside, 1 open, 2 source
    let mut kind = vec![0u8; n];
    let mut cur = vec![0i32; n];
    for y in 0..h {
        let row = it.next().unwrap().as_bytes();
        for x in 0..w {
            let idx = (y + 1) * wp + x + 1;
            match row[x] {
                b'.' => kind[idx] = 1,
                b'#' => {}
                d => {
                    kind[idx] = 2;
                    cur[idx] = 1000 * (d - b'0') as i32;
                }
            }
        }
    }
    let mut mu = vec![0i32; n];
    let mut md = vec![0i32; n];
    let mut ml = vec![0i32; n];
    let mut mr = vec![0i32; n];
    for y in 1..=h {
        for x in 1..=w {
            let i = y * wp + x;
            if kind[i] == 1 {
                if kind[i - wp] != 0 {
                    mu[i] = -1;
                }
                if kind[i + wp] != 0 {
                    md[i] = -1;
                }
                if kind[i - 1] != 0 {
                    ml[i] = -1;
                }
                if kind[i + 1] != 0 {
                    mr[i] = -1;
                }
            }
        }
    }
    let mut nxt = cur.clone();

    for _ in 0..steps {
        for y in 1..=h {
            let i = y * wp + 1;
            let c = &cur[i..i + w];
            let up = &cur[i - wp..i - wp + w];
            let dn = &cur[i + wp..i + wp + w];
            let lf = &cur[i - 1..i - 1 + w];
            let rt = &cur[i + 1..i + 1 + w];
            let a = &mu[i..i + w];
            let b = &md[i..i + w];
            let cc = &ml[i..i + w];
            let d = &mr[i..i + w];
            let out = &mut nxt[i..i + w];
            for x in 0..w {
                let o = c[x];
                let u = o + ((up[x] - o) & a[x]);
                let dd = o + ((dn[x] - o) & b[x]);
                let l = o + ((lf[x] - o) & cc[x]);
                let r = o + ((rt[x] - o) & d[x]);
                out[x] = (4 * o + u + dd + l + r) >> 3;
            }
        }
        std::mem::swap(&mut cur, &mut nxt);
    }

    let mut sum: i64 = 0;
    let mut best: i64 = -1;
    let mut br = 0usize;
    let mut bc = 0usize;
    let mut chk: i64 = 0;
    for y in 0..h {
        for x in 0..w {
            let i = (y + 1) * wp + x + 1;
            if kind[i] == 1 {
                let v = cur[i] as i64;
                sum += v;
                if v > best {
                    best = v;
                    br = y;
                    bc = x;
                }
                chk += v * ((y * w + x + 1) as i64);
            }
        }
    }
    let stdout = std::io::stdout();
    let mut o = stdout.lock();
    writeln!(o, "sum {}", sum).unwrap();
    writeln!(o, "max {} {} {}", best, br, bc).unwrap();
    writeln!(o, "checksum {}", chk).unwrap();
}
