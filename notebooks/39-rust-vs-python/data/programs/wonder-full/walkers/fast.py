import sys

import numpy as np

MASK = (1 << 64) - 1
GOLD = np.uint64(0x9E3779B97F4A7C15)
C1 = np.uint64(0xBF58476D1CE4E5B9)
C2 = np.uint64(0x94D049BB133111EB)
XT = np.array([1, -1, 0, 0], dtype=np.int64)
YT = np.array([0, 0, 1, -1], dtype=np.int64)
XT32 = XT.astype(np.int32)
YT32 = YT.astype(np.int32)


def clamp_path(w, a):
    """Turn unbounded positions w (offset so the box is [0, a]) into the
    clamped walk, in place. Returns False if the walk flips between the
    two boundaries so often that a scalar walk would be cheaper.

    Between visits to opposite boundaries the clamped walk is a
    one-sided reflection: after last touching the top it equals
    a - (running max of w - w), and after last touching the bottom it
    equals w - running min of w. Both are cumulative extrema, which
    NumPy computes in blocks; a block is reprocessed from the point
    where the walk reaches the opposite boundary.
    """
    n = len(w)
    if a >= 128:
        block = 65536
    elif a >= 32:
        block = 16384
    else:
        block = 2048
    pos = 0
    mode = 0  # 0 = no boundary touched yet, 1 = top, -1 = bottom
    run_max = 0
    run_min = 0
    switches = 0
    while pos < n:
        end = min(n, pos + block)
        while pos < end:
            seg = w[pos:end]
            if mode == 0:
                if seg.min() >= 0 and seg.max() <= a:
                    pos = end
                else:
                    h = int(np.nonzero((seg < 0) | (seg > a))[0][0])
                    p = pos + h
                    if w[p] > a:
                        mode = 1
                        run_max = int(w[p])
                    else:
                        mode = -1
                        run_min = int(w[p])
                    pos = p
                    switches += 1
            elif mode == 1:
                mx = np.maximum.accumulate(seg)
                np.maximum(mx, run_max, out=mx)
                last = int(mx[-1])
                np.subtract(seg, mx, out=mx)  # now mx = u - a <= 0
                if mx.min() >= -a:
                    mx += a
                    w[pos:end] = mx
                    run_max = last
                    pos = end
                else:
                    h = int(np.nonzero(mx < -a)[0][0])
                    if h:
                        w[pos:pos + h] = mx[:h] + a
                    run_min = int(seg[h])
                    mode = -1
                    pos = pos + h
                    switches += 1
                    if switches > 128:
                        return False
            else:
                mn = np.minimum.accumulate(seg)
                np.minimum(mn, run_min, out=mn)
                last = int(mn[-1])
                np.subtract(seg, mn, out=mn)  # now mn = u >= 0
                if mn.max() <= a:
                    w[pos:end] = mn
                    run_min = last
                    pos = end
                else:
                    h = int(np.nonzero(mn > a)[0][0])
                    if h:
                        w[pos:pos + h] = mn[:h]
                    run_max = int(seg[h])
                    mode = 1
                    pos = pos + h
                    switches += 1
                    if switches > 128:
                        return False
    return True


def walker_from_dirs(dbytes, B):
    x = y = bumps = rets = 0
    for d in dbytes:
        if d < 2:
            if d == 0:
                if x < B:
                    x += 1
                    if x == 0 and y == 0:
                        rets += 1
                else:
                    bumps += 1
            else:
                if x > -B:
                    x -= 1
                    if x == 0 and y == 0:
                        rets += 1
                else:
                    bumps += 1
        else:
            if d == 2:
                if y < B:
                    y += 1
                    if y == 0 and x == 0:
                        rets += 1
                else:
                    bumps += 1
            else:
                if y > -B:
                    y -= 1
                    if y == 0 and x == 0:
                        rets += 1
                else:
                    bumps += 1
    return x, y, bumps, rets


def walker_numpy(seed, j, L, B):
    if L == 0:
        return 0, 0, 0, 0
    # All SplitMix64 states of this walker at once: state_k = seed_j + k*GOLD.
    z = np.arange(1, L + 1, dtype=np.uint64)
    z *= GOLD
    z += np.uint64((seed + j) & MASK)
    tmp = np.empty_like(z)
    np.right_shift(z, np.uint64(30), out=tmp)
    z ^= tmp
    z *= C1
    np.right_shift(z, np.uint64(27), out=tmp)
    z ^= tmp
    z *= C2
    # Top two bits only; the final z ^ (z >> 31) cannot change them.
    z >>= np.uint64(62)
    d = z.astype(np.uint8)
    del z, tmp

    a = 2 * B
    # int32 halves the memory traffic of every path pass when it can
    # hold any partial sum; folding +B into the first step saves a pass.
    if L + B < 2_000_000_000:
        xt, yt, dt = XT32, YT32, np.int32
    else:
        xt, yt, dt = XT, YT, np.int64
    wx = xt[d]
    wx[0] += B
    np.cumsum(wx, out=wx, dtype=dt)
    if not clamp_path(wx, a):
        return walker_from_dirs(d.tobytes(), B)
    wy = yt[d]
    wy[0] += B
    np.cumsum(wy, out=wy, dtype=dt)
    if not clamp_path(wy, a):
        return walker_from_dirs(d.tobytes(), B)

    xf = int(wx[-1]) - B
    yf = int(wy[-1]) - B
    # A step bumps exactly when its axis was meant to move but did not.
    is_x = d[1:] < 2
    bumps = int(np.count_nonzero(is_x & (wx[1:] == wx[:-1])))
    bumps += int(np.count_nonzero(~is_x & (wy[1:] == wy[:-1])))
    if d[0] < 2:
        bumps += int(wx[0] == B)
    else:
        bumps += int(wy[0] == B)
    # After a step the walker is at the origin only if it just moved
    # there (a bump is impossible at the origin since B >= 1).
    rets = int(np.count_nonzero((wx == B) & (wy == B)))
    return xf, yf, bumps, rets


def process_range(task):
    start, end, L, B, seed = task
    spread = bumps = rets = 0
    best_j = start
    best_d = -1
    for j in range(start, end):
        x, y, b, r = walker_numpy(seed, j, L, B)
        spread += x * x + y * y
        bumps += b
        rets += r
        dd = abs(x) + abs(y)
        if dd > best_d:
            best_d = dd
            best_j = j
    return spread, bumps, rets, best_j, best_d


def main():
    with open(sys.argv[1], "rb") as f:
        parts = f.read().split()
    J, L, B, seed = (int(parts[i]) for i in range(4))
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    workers = max(1, min(32, workers))

    if J <= 0:
        sys.stdout.write("spread 0\nbumps 0\nreturns 0\nfarthest 0 0\n")
        return

    workers = min(workers, J)
    q, rem = divmod(J, workers)
    tasks = []
    s = 0
    for w in range(workers):
        e = s + q + (1 if w < rem else 0)
        tasks.append((s, e, L, B, seed))
        s = e

    if workers > 1 and J * L >= 20000:
        if 2 * B < 64 and J * L >= 8_000_000:
            # A narrow box makes the scalar fallback likely; that is
            # GIL-bound, so use processes despite the spawn cost.
            import multiprocessing as mp
            with mp.get_context("spawn").Pool(workers) as pool:
                results = pool.map(process_range, tasks)
        else:
            # NumPy releases the GIL on these large arrays, and threads
            # avoid paying a fresh interpreter + NumPy import per worker.
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=workers) as ex:
                results = list(ex.map(process_range, tasks))
    else:
        results = [process_range(t) for t in tasks]

    spread = bumps = rets = 0
    best_j = 0
    best_d = -1
    for sp, b, r, bj, bd in results:
        spread += sp
        bumps += b
        rets += r
        if bd > best_d or (bd == best_d and bj < best_j):
            best_d = bd
            best_j = bj
    sys.stdout.write(
        f"spread {spread}\nbumps {bumps}\nreturns {rets}\n"
        f"farthest {best_j} {best_d}\n"
    )


if __name__ == "__main__":
    main()
