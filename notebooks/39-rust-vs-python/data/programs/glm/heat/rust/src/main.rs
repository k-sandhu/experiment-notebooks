use std::env;
use std::fs;

fn main() {
    let path = env::args().nth(1).expect("usage: solution INPUT");
    let data = fs::read_to_string(&path).expect("cannot read input");

    let mut lines = data.lines();
    let first = lines.next().unwrap_or("");
    let mut it = first.split_whitespace();
    let h: usize = it.next().expect("missing H").parse().expect("bad H");
    let w: usize = it.next().expect("missing W").parse().expect("bad W");
    let steps: u64 = it.next().expect("missing S").parse().expect("bad S");

    let wp = w + 2; // padded row width
    let n = (h + 2) * wp;

    let mut cur = vec![0i32; n];
    let mut nxt = vec![0i32; n];
    let mut m = vec![0i32; n]; // per-cell multiplier, 0 for walls/padding/sources
    let mut is_open = vec![false; n];
    let mut is_src = vec![false; n];
    let mut sources: Vec<(usize, i32)> = Vec::new();

    for r in 0..h {
        let line = lines.next().unwrap_or("");
        let bytes = line.as_bytes();
        let base = (r + 1) * wp + 1;
        for c in 0..w.min(bytes.len()) {
            let i = base + c;
            match bytes[c] {
                b'#' => {}
                b'1'..=b'9' => {
                    let v = 1000 * (bytes[c] - b'0') as i32;
                    is_open[i] = true;
                    is_src[i] = true;
                    cur[i] = v;
                    sources.push((i, v));
                }
                _ => is_open[i] = true, // '.'
            }
        }
    }

    // Multiplier m = 4 + number of blocked neighbours (wall or outside).
    for r in 1..=h {
        for c in 1..=w {
            let i = r * wp + c;
            if is_open[i] && !is_src[i] {
                let mut mm = 4i32;
                if !is_open[i - 1] { mm += 1; }
                if !is_open[i + 1] { mm += 1; }
                if !is_open[i - wp] { mm += 1; }
                if !is_open[i + wp] { mm += 1; }
                m[i] = mm;
            }
        }
    }

    // Fixup list: walls/padding must stay 0, sources keep their value.
    // Written after the (branch-free) update pass each step.
    let mut fixes: Vec<(usize, i32)> = Vec::with_capacity(sources.len() + n / 4);
    for i in 0..n {
        if !is_open[i] {
            fixes.push((i, 0));
        }
    }
    for &s in &sources {
        fixes.push(s);
    }

    for _ in 0..steps {
        for r in 1..=h {
            let base = r * wp;
            let up = base - wp;
            let dn = base + wp;
            for c in 0..wp {
                let i = base + c;
                // SAFETY: i is in [wp, n - wp), so i-1, i+1, up+c, dn+c are
                // all valid indices into the padded arrays of length n.
                unsafe {
                    let v = *cur.get_unchecked(i);
                    let t = *m.get_unchecked(i) * v
                        + *cur.get_unchecked(i - 1)
                        + *cur.get_unchecked(i + 1)
                        + *cur.get_unchecked(up + c)
                        + *cur.get_unchecked(dn + c);
                    *nxt.get_unchecked_mut(i) = t >> 3;
                }
            }
        }
        for &(i, v) in &fixes {
            nxt[i] = v;
        }
        std::mem::swap(&mut cur, &mut nxt);
    }

    // Stats over all open cells (sources included), row-major order.
    let mut total: i64 = 0;
    let mut best: i64 = -1;
    let mut br = 0usize;
    let mut bc = 0usize;
    let mut chk: i64 = 0;
    for r in 0..h {
        let base = (r + 1) * wp;
        let wk = r * w;
        for c in 0..w {
            let i = base + c + 1;
            if is_open[i] && !is_src[i] {
                let v = cur[i] as i64;
                total += v;
                chk += v * (wk + c + 1) as i64;
                if v > best {
                    best = v;
                    br = r;
                    bc = c;
                }
            }
        }
    }

    use std::io::Write;
    let out = format!("sum {total}\nmax {best} {br} {bc}\nchecksum {chk}\n");
    std::io::stdout().write_all(out.as_bytes()).unwrap();
}
