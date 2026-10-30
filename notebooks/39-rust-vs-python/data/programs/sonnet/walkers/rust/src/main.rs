use std::sync::atomic::{AtomicUsize, Ordering};

const G: u64 = 0x9E3779B97F4A7C15;
const C1: u64 = 0xBF58476D1CE4E5B9;
const C2: u64 = 0x94D049BB133111EB;

#[derive(Clone, Copy)]
struct Acc {
    spread: i64,
    bumps: i64,
    returns: i64,
    best_d: i64,
    best_j: u64,
}

fn walk(j: u64, l: u64, b: i64, seed: u64) -> (i64, i64, i64, i64) {
    const DX: [i64; 4] = [1, -1, 0, 0];
    const DY: [i64; 4] = [0, 0, 1, -1];
    let mut s = seed.wrapping_add(j);
    let (mut x, mut y) = (0i64, 0i64);
    let (mut bumps, mut rets) = (0i64, 0i64);
    for _ in 0..l {
        s = s.wrapping_add(G);
        let mut z = s;
        z = (z ^ (z >> 30)).wrapping_mul(C1);
        z = (z ^ (z >> 27)).wrapping_mul(C2);
        let d = (z >> 62) as usize;
        let nx = x + DX[d];
        let ny = y + DY[d];
        let oob = (nx.abs() > b) | (ny.abs() > b);
        bumps += oob as i64;
        rets += ((!oob) & (nx == 0) & (ny == 0)) as i64;
        x = if oob { x } else { nx };
        y = if oob { y } else { ny };
    }
    (x, y, bumps, rets)
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let text = std::fs::read_to_string(&args[1]).unwrap();
    let mut it = text.split_whitespace();
    let jn: u64 = it.next().unwrap().parse().unwrap();
    let l: u64 = it.next().unwrap().parse().unwrap();
    let b: i64 = it.next().unwrap().parse().unwrap();
    let seed: u64 = it.next().unwrap().parse().unwrap();
    let workers: usize = args.get(2).and_then(|w| w.parse().ok()).unwrap_or(1).max(1);
    let nthreads = workers.min(jn.max(1) as usize);

    let next = AtomicUsize::new(0);
    let run = || {
        let mut a = Acc { spread: 0, bumps: 0, returns: 0, best_d: -1, best_j: 0 };
        loop {
            let j = next.fetch_add(1, Ordering::Relaxed) as u64;
            if j >= jn {
                break;
            }
            let (x, y, bu, re) = walk(j, l, b, seed);
            a.spread += x * x + y * y;
            a.bumps += bu;
            a.returns += re;
            let d = x.abs() + y.abs();
            if d > a.best_d || (d == a.best_d && j < a.best_j) {
                a.best_d = d;
                a.best_j = j;
            }
        }
        a
    };
    let parts: Vec<Acc> = if nthreads <= 1 {
        vec![run()]
    } else {
        std::thread::scope(|sc| {
            let hs: Vec<_> = (0..nthreads).map(|_| sc.spawn(&run)).collect();
            hs.into_iter().map(|h| h.join().unwrap()).collect()
        })
    };
    let mut t = Acc { spread: 0, bumps: 0, returns: 0, best_d: -1, best_j: 0 };
    for p in parts {
        t.spread += p.spread;
        t.bumps += p.bumps;
        t.returns += p.returns;
        if p.best_d > t.best_d || (p.best_d == t.best_d && p.best_j < t.best_j) {
            t.best_d = p.best_d;
            t.best_j = p.best_j;
        }
    }
    println!("spread {}\nbumps {}\nreturns {}\nfarthest {} {}", t.spread, t.bumps, t.returns, t.best_j, t.best_d.max(0));
}
