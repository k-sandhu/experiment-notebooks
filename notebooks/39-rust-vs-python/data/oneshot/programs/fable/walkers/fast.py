import sys
import threading
import numpy as np

MASK = (1 << 64) - 1
GOLDEN = 0x9E3779B97F4A7C15


def clamp(S, B):
    """S: unclamped positions (start within box, at least one violation).
    Rewrites S in place with the clamped walk, returns number of bumps."""
    a = np.abs(S) > B
    t = int(a.argmax())
    seg = S[t:]
    up = bool(seg[0] > B)
    nB = -B
    bumps = 0
    while True:
        if up:
            c = np.maximum.accumulate(seg)
            seg -= c
            seg += B
            v = seg < nB
        else:
            c = np.minimum.accumulate(seg)
            seg -= c
            seg -= B
            v = seg > B
        u = int(v.argmax())
        if not v[u]:
            last = int(c[-1])
            bumps += (last - B) if up else (-last - B)
            return bumps
        last = int(c[u - 1])
        bumps += (last - B) if up else (-last - B)
        c = c[u:]
        seg = seg[u:]
        seg += c
        seg -= last
        up = not up


def main():
    with open(sys.argv[1], 'rb') as f:
        parts = f.read().split()
    J = int(parts[0])
    L = int(parts[1])
    B = int(parts[2])
    SEED = int(parts[3])
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    if workers < 1:
        workers = 1
    if workers > 32:
        workers = 32

    if B > L:
        B = L + 1  # boundary unreachable; equivalent
    nB = -B

    C = 16384
    if L < C:
        C = L
    GK = np.arange(1, C + 1, dtype=np.uint64) * np.uint64(GOLDEN)
    STEP = (C * GOLDEN) & MASK

    lim = B + C + 2
    if lim <= 32767:
        dt = np.int16
    elif lim <= 2147483647:
        dt = np.int32
    else:
        dt = np.int64

    lutx = np.zeros(256, dtype=dt)
    lutx[:64] = 1
    lutx[64:128] = -1
    luty = np.zeros(256, dtype=dt)
    luty[128:192] = 1
    luty[192:] = -1

    scalar_mode = B < 8

    nfull = L // C
    rem = L % C
    nchunks = nfull + (1 if rem else 0)

    res = [None] * J
    it = iter(range(J))

    C1 = np.uint64(0xBF58476D1CE4E5B9)
    C2 = np.uint64(0x94D049BB133111EB)
    S30 = np.uint64(30)
    S27 = np.uint64(27)

    def work():
        z = np.empty(C, np.uint64)
        t = np.empty(C, np.uint64)
        top = z.view(np.uint8)[7::8]
        idx = np.empty(C, np.intp)
        d8 = np.empty(C, np.uint8)
        sx = np.empty(C, dt)
        sy = np.empty(C, dt)
        X = np.empty(C, dt)
        Y = np.empty(C, dt)
        tmp = np.empty(C, dt)
        full = (GK, z, t, top, idx, d8, sx, sy, X, Y, tmp)
        if rem:
            part = tuple(a[:rem] for a in full)
        else:
            part = full

        add = np.add
        rshift = np.right_shift
        xor = np.bitwise_xor
        mul = np.multiply
        copyto = np.copyto
        bor = np.bitwise_or
        cnz = np.count_nonzero
        u64 = np.uint64
        lx_take = lutx.take
        ly_take = luty.take
        _clamp = clamp

        while True:
            j = next(it, None)
            if j is None:
                break
            x = 0
            y = 0
            bumps = 0
            rets = 0
            base = (SEED + j) & MASK
            for ci in range(nchunks):
                if ci < nfull:
                    n = C
                    gk, zz, tt, tp, ix, dd, ax, ay, PX, PY, tm = full
                else:
                    n = rem
                    gk, zz, tt, tp, ix, dd, ax, ay, PX, PY, tm = part
                add(gk, u64(base), zz)
                base = (base + STEP) & MASK
                rshift(zz, S30, tt)
                xor(zz, tt, zz)
                mul(zz, C1, zz)
                rshift(zz, S27, tt)
                xor(zz, tt, zz)
                mul(zz, C2, zz)
                if scalar_mode:
                    rshift(tp, 6, dd)
                    for d in dd.tobytes():
                        if d == 0:
                            if x < B:
                                x += 1
                                if x == 0 and y == 0:
                                    rets += 1
                            else:
                                bumps += 1
                        elif d == 1:
                            if x > nB:
                                x -= 1
                                if x == 0 and y == 0:
                                    rets += 1
                            else:
                                bumps += 1
                        elif d == 2:
                            if y < B:
                                y += 1
                                if x == 0 and y == 0:
                                    rets += 1
                            else:
                                bumps += 1
                        else:
                            if y > nB:
                                y -= 1
                                if x == 0 and y == 0:
                                    rets += 1
                            else:
                                bumps += 1
                    continue
                copyto(ix, tp)
                lx_take(ix, out=ax, mode='clip')
                ly_take(ix, out=ay, mode='clip')
                ax[0] += x
                ay[0] += y
                ax.cumsum(dtype=dt, out=PX)
                ay.cumsum(dtype=dt, out=PY)
                hx = PX.max()
                lx = PX.min()
                hy = PY.max()
                ly = PY.min()
                clamped = False
                if hx > B or lx < nB:
                    bumps += _clamp(PX, B)
                    clamped = True
                if hy > B or ly < nB:
                    bumps += _clamp(PY, B)
                    clamped = True
                if clamped or (lx <= 0 <= hx and ly <= 0 <= hy):
                    bor(PX, PY, tm)
                    rets += n - cnz(tm)
                x = int(PX[n - 1])
                y = int(PY[n - 1])
            res[j] = (x, y, bumps, rets)

    nt = min(workers, J)
    ths = [threading.Thread(target=work) for _ in range(nt - 1)]
    for th in ths:
        th.start()
    work()
    for th in ths:
        th.join()

    spread = 0
    bumps = 0
    rets = 0
    bj = 0
    bd = -1
    for j in range(J):
        x, y, b, r = res[j]
        spread += x * x + y * y
        bumps += b
        rets += r
        dist = abs(x) + abs(y)
        if dist > bd:
            bd = dist
            bj = j
    sys.stdout.write(
        "spread %d\nbumps %d\nreturns %d\nfarthest %d %d\n"
        % (spread, bumps, rets, bj, bd)
    )
    sys.stdout.flush()


if __name__ == "__main__":
    main()
