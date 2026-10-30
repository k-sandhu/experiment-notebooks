import os
import sys
from multiprocessing import Pool

G = 0x9E3779B97F4A7C15

# numpy is imported lazily so the parent process of a multi-worker run never loads it
np = None
C1 = C2 = S30 = S27 = S62 = _uclip = None
_ctx = {}


def _setup(L, B):
    """Per-process constants: block layout, dtype and the (k+1)*G offsets."""
    global np, C1, C2, S30, S27, S62, _uclip
    import numpy
    np = numpy
    _uclip = np._core.umath.clip
    C1 = np.uint64(0xBF58476D1CE4E5B9)
    C2 = np.uint64(0x94D049BB133111EB)
    S30 = np.uint64(30)
    S27 = np.uint64(27)
    S62 = np.uint64(62)
    S = 128 if L >= 16384 else max(1, int(L ** 0.5))
    T = -(-L // S)
    if B <= 16000:
        dt = np.int16
    elif B <= 1 << 30:
        dt = np.int32
    else:
        dt = np.int64
    k = (np.arange(T, dtype=np.uint64) * np.uint64(S))[None, :] + np.arange(1, S + 1, dtype=np.uint64)[:, None]
    kg = k * np.uint64(G)
    _ctx.update(
        S=S, T=T, dt=dt, kg=kg,
        tx=np.array([1, -1, 0, 0], dtype=dt),
        ty=np.array([0, 0, 1, -1], dtype=dt),
        Q=np.empty((2, S, T), dtype=dt),
        z=np.empty((S, T), dtype=np.uint64),
        t=np.empty((S, T), dtype=np.uint64),
        ne=np.empty((S, 2, T), dtype=np.bool_),
        ze=np.empty((S, 2, T), dtype=np.bool_),
    )


def walk(args):
    j, L, B, seed = args
    if not _ctx:
        _setup(L, B)
    c = _ctx
    S, T, dt = c["S"], c["T"], c["dt"]
    Q, z, t, ne, ze = c["Q"], c["z"], c["t"], c["ne"], c["ze"]
    # random numbers for every step of this walker, laid out as (step in block, block)
    np.add(c["kg"], np.uint64((seed + j) & 0xFFFFFFFFFFFFFFFF), out=z)
    np.right_shift(z, S30, out=t)
    np.bitwise_xor(z, t, out=z)
    np.multiply(z, C1, out=z)
    np.right_shift(z, S27, out=t)
    np.bitwise_xor(z, t, out=z)
    np.multiply(z, C2, out=z)
    np.right_shift(z, S62, out=z)
    zi = z.view(np.int64)
    np.take(c["tx"], zi, out=Q[0], mode="clip")
    np.take(c["ty"], zi, out=Q[1], mode="clip")
    pad = S * T - L
    if pad:
        Q[:, S - pad:, T - 1] = 0
    clip = _uclip
    lb, ub = dt(-B), dt(B)
    add = np.add
    # pass 1: each block as a function of its start: clamp(x + a, lo, hi)
    lo = np.full((2, T), -B, dtype=dt)
    hi = np.full((2, T), B, dtype=dt)
    for i in range(S):
        st = Q[:, i, :]
        add(lo, st, out=lo)
        clip(lo, lb, ub, out=lo)
        add(hi, st, out=hi)
        clip(hi, lb, ub, out=hi)
    a = np.add.reduce(Q, axis=1, dtype=dt)
    # pass 2: chain the blocks to get each block's true start position
    starts = np.empty((2, T), dtype=dt)
    for ax in range(2):
        al = a[ax].tolist()
        ll = lo[ax].tolist()
        hl = hi[ax].tolist()
        out = [0] * T
        p = 0
        for b in range(T):
            out[b] = p
            p += al[b]
            l = ll[b]
            h = hl[b]
            p = l if p < l else (h if p > h else p)
        starts[ax] = out
    # pass 3: replay every block from its true start and record bumps / visits to the origin
    P = starts
    tmp = np.empty_like(P)
    for i in range(S):
        add(P, Q[:, i, :], out=tmp)
        clip(tmp, lb, ub, out=P)
        np.not_equal(tmp, P, out=ne[i])
        np.equal(P, 0, out=ze[i])
    bumps = int(np.count_nonzero(ne))
    r = ze[:, 0, :] & ze[:, 1, :]
    if pad:
        r[S - pad:, T - 1] = False
    rets = int(np.count_nonzero(r))
    x = int(P[0, T - 1])
    y = int(P[1, T - 1])
    return j, x, y, bumps, rets


def safe_walk(args):
    try:
        return walk(args)
    except Exception:
        return None


def main():
    with open(sys.argv[1]) as f:
        J, L, B, seed = map(int, f.read().split())
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    workers = max(1, min(workers, J, 8))
    B = min(B, L)
    tot = [0, 0, 0, -1, 0]  # spread, bumps, returns, best distance, best walker

    def absorb(res):
        j, x, y, bu, re = res
        tot[0] += x * x + y * y
        tot[1] += bu
        tot[2] += re
        d = abs(x) + abs(y)
        if d > tot[3] or (d == tot[3] and j < tot[4]):
            tot[3] = d
            tot[4] = j

    if L > 0:
        tasks = [(j, L, B, seed) for j in range(J)]
        if workers == 1:
            for task in tasks:
                absorb(walk(task))
        else:
            done = set()
            with Pool(workers) as pool:
                for res in pool.imap_unordered(safe_walk, tasks, chunksize=1):
                    if res is not None:
                        done.add(res[0])
                        absorb(res)
            # any walker a worker failed on (e.g. out of memory) is redone here
            for task in tasks:
                if task[0] not in done:
                    absorb(walk(task))
    sys.stdout.buffer.write(
        ("spread %d\nbumps %d\nreturns %d\nfarthest %d %d\n" % (tot[0], tot[1], tot[2], tot[4], max(tot[3], 0))).encode()
    )


if __name__ == "__main__":
    main()
