import os
import sys
from multiprocessing import Pool

M = 0xFFFFFFFFFFFFFFFF
G = 0x9E3779B97F4A7C15
C1 = 0xBF58476D1CE4E5B9
C2 = 0x94D049BB133111EB


def walk(args):
    j, L, B, seed = args
    s = (seed + j) & M
    x = y = 0
    bumps = rets = 0
    K = 2 * B + 1
    MV = (K, -K, 1, -1)
    DX = (1, -1, 0, 0)
    DY = (0, 0, 1, -1)
    rem = L
    while rem > 0:
        m = B - max(abs(x), abs(y))
        if m >= 4:
            # no bump is possible within the next m steps
            if m > rem:
                m = rem
            rem -= m
            p = x * K + y
            for _ in range(m):
                s = (s + G) & M
                z = ((s ^ (s >> 30)) * C1) & M
                p += MV[((z ^ (z >> 27)) * C2 >> 62) & 3]
                if not p:
                    rets += 1
            y = (p + B) % K - B
            x = (p - y) // K
        else:
            s = (s + G) & M
            z = ((s ^ (s >> 30)) * C1) & M
            d = ((z ^ (z >> 27)) * C2 >> 62) & 3
            nx = x + DX[d]
            ny = y + DY[d]
            if -B <= nx <= B and -B <= ny <= B:
                x = nx
                y = ny
                if not (x or y):
                    rets += 1
            else:
                bumps += 1
            rem -= 1
    return j, x, y, bumps, rets


def main():
    with open(sys.argv[1]) as f:
        J, L, B, seed = map(int, f.read().split())
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    workers = max(1, min(workers, J, os.cpu_count() or 1))
    tasks = [(j, L, B, seed) for j in range(J)]
    if workers == 1:
        results = map(walk, tasks)
    else:
        pool = Pool(workers)
        results = pool.imap_unordered(walk, tasks, chunksize=1)
    spread = bumps = rets = 0
    best_d = -1
    best_j = 0
    for j, x, y, bu, re in results:
        spread += x * x + y * y
        bumps += bu
        rets += re
        d = abs(x) + abs(y)
        if d > best_d or (d == best_d and j < best_j):
            best_d = d
            best_j = j
    if workers > 1:
        pool.close()
        pool.join()
    sys.stdout.buffer.write((
        "spread %d\nbumps %d\nreturns %d\nfarthest %d %d\n"
        % (spread, bumps, rets, best_j, max(best_d, 0))).encode()
    )


if __name__ == "__main__":
    main()
