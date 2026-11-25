use std::io::Write;

/// Number of circular buckets; must exceed the largest edge weight (1000).
const NB: usize = 1024;
const MASK: u64 = NB as u64 - 1;
const WORDS: usize = NB / 64;

struct Parser<'a> {
    buf: &'a [u8],
    pos: usize,
}

impl Parser<'_> {
    /// Reads the next unsigned integer. The buffer ends with a non-digit sentinel, and
    /// callers only ask for numbers that are present, so neither loop can run off the end.
    #[inline(always)]
    fn next(&mut self) -> u64 {
        let b = self.buf;
        let mut p = self.pos;
        unsafe {
            while !b.get_unchecked(p).is_ascii_digit() {
                p += 1;
            }
            let mut x = 0u64;
            loop {
                let d = b.get_unchecked(p).wrapping_sub(b'0');
                if d > 9 {
                    break;
                }
                x = x * 10 + d as u64;
                p += 1;
            }
            self.pos = p;
            x
        }
    }
}

/// Dial's algorithm: a circular array of buckets indexed by distance mod NB, plus a
/// bitmap of non-empty buckets so the next distance is found in a few word scans.
/// All pending entries lie within [cur, cur + 1000], so the slot identifies the distance,
/// and an entry is stale exactly when dist[v] differs from the bucket's distance.
struct Dial {
    buckets: Vec<Vec<u32>>,
    bits: [u64; WORDS],
}

impl Dial {
    fn new() -> Self {
        Dial { buckets: (0..NB).map(|_| Vec::new()).collect(), bits: [0; WORDS] }
    }

    #[inline(always)]
    fn push(&mut self, d: u64, v: u32) {
        let s = (d & MASK) as usize;
        self.buckets[s].push(v);
        self.bits[s >> 6] |= 1u64 << (s & 63);
    }

    /// Smallest non-empty slot at or after `from` in circular order.
    #[inline]
    fn next_slot(&self, from: usize) -> Option<usize> {
        let w0 = from >> 6;
        let first = self.bits[w0] & (!0u64 << (from & 63));
        if first != 0 {
            return Some((w0 << 6) | first.trailing_zeros() as usize);
        }
        for i in 1..=WORDS {
            let w = (w0 + i) % WORDS;
            let mut bits = self.bits[w];
            if i == WORDS {
                bits &= !(!0u64 << (from & 63));
            }
            if bits != 0 {
                return Some((w << 6) | bits.trailing_zeros() as usize);
            }
        }
        None
    }
}

#[inline(always)]
fn prefetch<T>(p: *const T) {
    #[cfg(target_arch = "x86_64")]
    unsafe {
        std::arch::x86_64::_mm_prefetch::<{ std::arch::x86_64::_MM_HINT_T0 }>(p as *const i8);
    }
}

struct Stats {
    reached: u64,
    total: u64,
    far: u64,
    node: u32,
}

trait Dist: Copy + Eq + Ord {
    const INF: Self;
    fn from_u64(x: u64) -> Self;
    fn to_u64(self) -> u64;
}

impl Dist for u32 {
    const INF: Self = u32::MAX;
    #[inline(always)]
    fn from_u64(x: u64) -> Self {
        x as u32
    }
    #[inline(always)]
    fn to_u64(self) -> u64 {
        self as u64
    }
}

impl Dist for u64 {
    const INF: Self = u64::MAX;
    #[inline(always)]
    fn from_u64(x: u64) -> Self {
        x
    }
    #[inline(always)]
    fn to_u64(self) -> u64 {
        self
    }
}

/// Runs Dijkstra from `src`. `D` is u32 when every possible distance fits, which halves
/// the size of the randomly accessed distance array.
fn dijkstra<D: Dist>(
    src: u32,
    offs: &[u32],
    adj: &[(u32, u32)],
    dist: &mut [D],
    q: &mut Dial,
    scratch: &mut Vec<u32>,
) -> Stats {
    dist.fill(D::INF);
    dist[src as usize] = D::from_u64(0);
    q.push(0, src);
    let mut st = Stats { reached: 0, total: 0, far: 0, node: src };
    let mut cur: u64 = 0;
    while let Some(slot) = q.next_slot((cur & MASK) as usize) {
        cur += ((slot as u64).wrapping_sub(cur & MASK)) & MASK;
        std::mem::swap(scratch, &mut q.buckets[slot]);
        q.bits[slot >> 6] &= !(1u64 << (slot & 63));
        let mut best = u32::MAX;
        let len = scratch.len();
        for i in 0..len {
            // The bucket order is effectively random, so fetch the per-node data of
            // upcoming entries early: offsets and distance for i + 16, edges for i + 8.
            unsafe {
                if i + 16 < len {
                    let x = *scratch.get_unchecked(i + 16) as usize;
                    prefetch(offs.as_ptr().add(x));
                    prefetch(dist.as_ptr().add(x));
                }
                if i + 8 < len {
                    let x = *scratch.get_unchecked(i + 8) as usize;
                    prefetch(adj.as_ptr().add(*offs.get_unchecked(x) as usize));
                }
            }
            let v = unsafe { *scratch.get_unchecked(i) };
            if unsafe { *dist.get_unchecked(v as usize) } != D::from_u64(cur) {
                continue;
            }
            st.reached += 1;
            st.total += cur;
            best = best.min(v);
            let (a, b) = unsafe { (*offs.get_unchecked(v as usize), *offs.get_unchecked(v as usize + 1)) };
            for &(u, w) in unsafe { adj.get_unchecked(a as usize..b as usize) } {
                let nd = cur + w as u64;
                let du = unsafe { dist.get_unchecked_mut(u as usize) };
                if nd < du.to_u64() {
                    *du = D::from_u64(nd);
                    q.push(nd, u);
                }
            }
        }
        if best != u32::MAX {
            st.far = cur;
            st.node = best;
        }
        scratch.clear();
    }
    st
}

fn main() {
    let path = std::env::args().nth(1).expect("input path");
    let mut data = std::fs::read(path).expect("read input");
    data.push(b'\n');
    let mut p = Parser { buf: &data, pos: 0 };
    let n = p.next() as usize;
    let m = p.next() as usize;
    let qn = p.next() as usize;

    let mut edges: Vec<(u32, u32, u32)> = Vec::with_capacity(m);
    let mut deg = vec![0u32; n + 1];
    for _ in 0..m {
        let u = p.next() as u32;
        let v = p.next() as u32;
        let w = p.next() as u32;
        if u != v {
            deg[u as usize] += 1;
            deg[v as usize] += 1;
            edges.push((u, v, w));
        }
    }
    let mut offs = vec![0u32; n + 1];
    let mut acc = 0u32;
    for i in 0..n {
        offs[i] = acc;
        acc += deg[i];
    }
    offs[n] = acc;
    let mut fill: Vec<u32> = offs[..n].to_vec();
    let mut adj = vec![(0u32, 0u32); acc as usize];
    for &(u, v, w) in &edges {
        let fu = &mut fill[u as usize];
        adj[*fu as usize] = (v, w);
        *fu += 1;
        let fv = &mut fill[v as usize];
        adj[*fv as usize] = (u, w);
        *fv += 1;
    }
    drop(edges);
    drop(fill);

    // Every shortest distance is at most (n - 1) * 1000.
    let small = (n as u64).saturating_sub(1) * 1000 < u32::MAX as u64;
    let mut dist32 = vec![0u32; if small { n } else { 0 }];
    let mut dist64 = vec![0u64; if small { 0 } else { n }];
    let mut q = Dial::new();
    let mut scratch = Vec::new();
    let mut out = String::with_capacity(qn * 64);
    for _ in 0..qn {
        let s = p.next() as u32;
        let st = if small {
            dijkstra(s, &offs, &adj, &mut dist32, &mut q, &mut scratch)
        } else {
            dijkstra(s, &offs, &adj, &mut dist64, &mut q, &mut scratch)
        };
        use std::fmt::Write as _;
        let _ = writeln!(out, "{} {} {} {} {}", s, st.reached, st.total, st.far, st.node);
    }
    std::io::stdout().lock().write_all(out.as_bytes()).unwrap();
}
