import sys

M = 0xFFFFFFFFFFFFFFFF
G = 0x9E3779B97F4A7C15
C1 = 0xBF58476D1CE4E5B9
C2 = 0x94D049BB133111EB
N = 768  # lanes (steps) per big-integer batch


def run(lo, hi, stride, L, B, seed):
    """Simulate walkers lo, lo+stride, ... < hi. Returns aggregated results."""
    nn = N if L > N else L
    NB = 16 * nn
    # 128-bit lanes packed into one big integer; each lane holds a 64-bit value.
    ONES = int.from_bytes((b'\x01' + bytes(15)) * nn, 'little')
    MASK = ONES * M
    KG = int.from_bytes(
        b''.join([k.to_bytes(16, 'little') for k in range(nn)]), 'little') * G
    STEP = ((nn * G) & M) * ONES
    T = bytes([i >> 6 for i in range(256)])
    nB = -B

    spread = 0
    bumps = 0
    rets = 0
    bestD = -1
    bestJ = -1

    for j in range(lo, hi, stride):
        # lane k holds state for step k: s0 + (k+1)*G mod 2^64
        cur = (KG + ((seed + j + G) & M) * ONES) & MASK
        x = 0
        y = 0
        rem = L
        while True:
            z = ((cur ^ (cur >> 30)) & MASK) * C1 & MASK
            z = ((z ^ (z >> 27)) & MASK) * C2
            # top two bits of the low 64 bits of each lane live in byte 7
            if rem >= nn:
                end = nn
                dt = z.to_bytes(NB, 'little')[7::16].translate(T)
            else:
                end = rem
                dt = z.to_bytes(NB, 'little')[7:16 * rem:16].translate(T)
            cnt = dt.count
            pos = 0
            while pos < end:
                ax = x if x >= 0 else -x
                ay = y if y >= 0 else -y
                g = B - (ax if ax > ay else ay)
                r = ax + ay - 1
                if r < g:
                    g = r
                if g >= 8:
                    # optimistic jump of 2g steps, verified by direction counts
                    e = pos + g + g
                    if e > end:
                        e = end
                    c0 = cnt(0, pos, e)
                    c1 = cnt(1, pos, e)
                    c2 = cnt(2, pos, e)
                    c3 = e - pos - c0 - c1 - c2
                    if not (x + c0 <= B and x - c1 >= nB and
                            y + c2 <= B and y - c3 >= nB and
                            (x > c1 or -x > c0 or y > c3 or -y > c2)):
                        # guaranteed-safe jump of g steps
                        e = pos + g
                        c0 = cnt(0, pos, e)
                        c1 = cnt(1, pos, e)
                        c2 = cnt(2, pos, e)
                        c3 = g - c0 - c1 - c2
                    x += c0 - c1
                    y += c2 - c3
                    pos = e
                else:
                    e = pos + 16
                    if e > end:
                        e = end
                    for d in dt[pos:e]:
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
                    pos = e
            rem -= end
            if rem <= 0:
                break
            cur = (cur + STEP) & MASK

        spread += x * x + y * y
        D = (x if x >= 0 else -x) + (y if y >= 0 else -y)
        if D > bestD:
            bestD = D
            bestJ = j

    return (spread, bumps, rets, bestD, bestJ)


def child(conn, lo, hi, stride, L, B, seed):
    try:
        conn.send(run(lo, hi, stride, L, B, seed))
    finally:
        conn.close()


def gather(p, rc):
    try:
        while True:
            if rc.poll(0.25):
                return rc.recv()
            if not p.is_alive():
                if rc.poll(0):
                    return rc.recv()
                return None
    except Exception:
        return None


def main():
    with open(sys.argv[1], 'r') as f:
        parts = f.read().split()
    J = int(parts[0])
    L = int(parts[1])
    B = int(parts[2])
    seed = int(parts[3])
    try:
        W = int(sys.argv[2])
    except Exception:
        W = 1
    k = W if W < J else J
    if k < 1:
        k = 1
    if J * L < 1000000:
        k = 1

    results = []
    jobs = []
    if k > 1:
        try:
            from multiprocessing import Process, Pipe
        except Exception:
            Process = None
        for w in range(1, k):
            p = None
            rc = None
            if Process is not None:
                try:
                    rc, sc = Pipe(False)
                    p = Process(target=child, args=(sc, w, J, k, L, B, seed))
                    p.daemon = True
                    p.start()
                    sc.close()
                except Exception:
                    p = None
            jobs.append((p, rc, w))

    results.append(run(0, J, k, L, B, seed))

    for p, rc, w in jobs:
        res = None
        if p is not None:
            res = gather(p, rc)
        if res is None:
            res = run(w, J, k, L, B, seed)
        results.append(res)

    for p, rc, w in jobs:
        if p is not None:
            try:
                p.join(5)
            except Exception:
                pass

    spread = 0
    bumps = 0
    rets = 0
    bestD = -1
    bestJ = -1
    for s, b, r, d, jj in results:
        spread += s
        bumps += b
        rets += r
        if jj >= 0 and (d > bestD or (d == bestD and jj < bestJ)):
            bestD = d
            bestJ = jj

    sys.stdout.write(
        "spread %d\nbumps %d\nreturns %d\nfarthest %d %d\n"
        % (spread, bumps, rets, bestJ, bestD))
    sys.stdout.flush()


if __name__ == '__main__':
    main()
