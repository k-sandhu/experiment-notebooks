import sys

import numpy as np

MASK64 = (1 << 64) - 1
GAMMA = 0x9E3779B97F4A7C15
C1 = 0xBF58476D1CE4E5B9
C2 = 0x94D049BB133111EB

G64 = np.uint64(GAMMA)
C1_64 = np.uint64(C1)
C2_64 = np.uint64(C2)
S30 = np.uint64(30)
S27 = np.uint64(27)
S62 = np.uint64(62)

# Block length for the one-sided reflection trick.  With this many steps a
# free walk (std ~ sqrt(n)/2 ~ 64 for n = 16384) practically never crosses
# from one wall of the box to the other, so inside a block at most one of the
# two walls is ever touched and the reflection has a closed vectorised form.
BLOCK = 1 << 14


def draw_d(steps, seed):
    """All d = r >> 62 values of a SplitMix64 stream, computed in bulk."""
    d = np.empty(steps, dtype=np.uint8)
    chunk = 1 << 17
    k = np.empty(chunk, dtype=np.uint64)
    z = np.empty(chunk, dtype=np.uint64)
    for a in range(0, steps, chunk):
        b = a + chunk
        if b > steps:
            b = steps
        n = b - a
        kk = k[:n]
        zz = z[:n]
        np.multiply(np.arange(a + 1, b + 1, dtype=np.uint64), G64, out=zz)
        np.add(zz, np.uint64(seed), out=zz)
        np.right_shift(zz, S30, out=kk)
        np.bitwise_xor(zz, kk, out=zz)
        np.multiply(zz, C1_64, out=zz)
        np.right_shift(zz, S27, out=kk)
        np.bitwise_xor(zz, kk, out=zz)
        np.multiply(zz, C2_64, out=zz)
        np.right_shift(zz, S62, out=kk)
        d[a:b] = kk
    return d


def clipped_walk(inc, bound):
    """Positions after each step of a 1-D walk clamped to [-bound, bound].

    Returns (positions, bumps).
    """
    n = inc.size
    dt = np.int32 if bound < (1 << 30) else np.int64
    pos = np.empty(n, dtype=dt)
    if n == 0:
        return pos, 0
    p = 0
    bumps = 0
    a = 0
    while a < n:
        b = a + BLOCK
        if b > n:
            b = n
        sub = inc[a:b]
        s = np.cumsum(sub, dtype=dt)
        s += dt(p)
        hi = int(s.max())
        lo = int(s.min())
        if hi <= bound and lo >= -bound:
            pos[a:b] = s
            p = int(s[-1])
        else:
            ok = False
            if hi > bound:
                # Sticky upper wall only: remove the running excess over it.
                # Each unit of excess is exactly one bumped step.
                e = np.maximum.accumulate(np.maximum(s - dt(bound), dt(0)))
                q = s - e
                if int(q.min()) >= -bound:
                    pos[a:b] = q
                    p = int(q[-1])
                    bumps += int(e[-1])
                    ok = True
            if not ok and lo < -bound:
                u = np.maximum.accumulate(np.maximum(dt(-bound) - s, dt(0)))
                q = s + u
                if int(q.max()) <= bound:
                    pos[a:b] = q
                    p = int(q[-1])
                    bumps += int(u[-1])
                    ok = True
            if not ok:
                # Very small box: both walls inside one block.  Fall back to a
                # direct loop for this block (correct, and only used when the
                # box is small compared with the block length).
                pp = p
                base = a
                for i in range(b - a):
                    v = pp + int(sub[i])
                    if v > bound:
                        v = bound
                        bumps += 1
                    elif v < -bound:
                        v = -bound
                        bumps += 1
                    pos[base + i] = v
                    pp = v
                p = pp
        a = b
    return pos, bumps


_INC_LUT = np.array([1, 255, 1, 255], dtype=np.uint8)


def walker(j, steps, bound, seed):
    d = draw_d(steps, (seed + j) & MASK64)
    xs = np.flatnonzero(d < 2)
    ys = np.flatnonzero(d >= 2)
    inc = _INC_LUT[d]
    dx = inc[xs].view(np.int8)
    dy = inc[ys].view(np.int8)

    nxl = dx.size
    nyl = dy.size
    # Positions can never leave [-n, n]; clamping the bound to n + 1 keeps the
    # numpy arithmetic inside int64 for absurdly large B.
    beff = bound if bound <= steps else steps + 1

    posx, bx = clipped_walk(dx, beff)
    posy, by = clipped_walk(dy, beff)
    bumps = bx + by

    # A step lands on (0, 0) exactly when the coordinate it moved is 0 and the
    # other coordinate is 0 at that moment.  Zeros of a 1-D walk are rare, so
    # only those steps are examined.  For the i-th x step, the number of y
    # steps before it is xs[i] - i.
    returns = 0
    if nxl:
        zi = np.flatnonzero(posx == 0)
        if zi.size:
            yb = xs[zi] - zi
            yv = np.zeros(zi.size, dtype=np.int64)
            m = yb > 0
            if m.any():
                yv[m] = posy[yb[m] - 1]
            returns += int(np.count_nonzero(yv == 0))
    if nyl:
        zi = np.flatnonzero(posy == 0)
        if zi.size:
            xb = ys[zi] - zi
            xv = np.zeros(zi.size, dtype=np.int64)
            m = xb > 0
            if m.any():
                xv[m] = posx[xb[m] - 1]
            returns += int(np.count_nonzero(xv == 0))

    xf = int(posx[-1]) if nxl else 0
    yf = int(posy[-1]) if nyl else 0
    return (j, xf, yf, bumps, returns)


def main():
    if len(sys.argv) < 2:
        sys.stderr.write("usage: fast.py INPUT_PATH WORKERS\n")
        return 1
    path = sys.argv[1]
    workers = 1
    if len(sys.argv) > 2:
        try:
            workers = int(sys.argv[2])
        except ValueError:
            workers = 1
    workers = max(1, min(32, workers))

    with open(path, "rb") as f:
        parts = f.read().split()
    j_count = int(parts[0])
    steps = int(parts[1])
    bound = int(parts[2])
    seed = int(parts[3]) & MASK64

    if j_count <= 0:
        sys.stdout.buffer.write(b"spread 0\nbumps 0\nreturns 0\nfarthest 0 0\n")
        return 0

    n = min(workers, j_count)
    if n <= 1:
        results = [walker(j, steps, bound, seed) for j in range(j_count)]
    else:
        from concurrent.futures import ThreadPoolExecutor

        chunks = [list(range(w, j_count, n)) for w in range(n)]
        with ThreadPoolExecutor(max_workers=n) as ex:
            out = list(ex.map(lambda js: [walker(j, steps, bound, seed) for j in js], chunks))
        results = [r for chunk in out for r in chunk]
        results.sort(key=lambda r: r[0])

    spread = 0
    bumps = 0
    returns = 0
    best_j = 0
    best_d = -1
    for j, x, y, bmp, ret in results:
        spread += x * x + y * y
        bumps += bmp
        returns += ret
        d = abs(x) + abs(y)
        if d > best_d:
            best_d = d
            best_j = j

    sys.stdout.buffer.write(
        (
            "spread %d\nbumps %d\nreturns %d\nfarthest %d %d\n"
            % (spread, bumps, returns, best_j, best_d)
        ).encode()
    )
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
