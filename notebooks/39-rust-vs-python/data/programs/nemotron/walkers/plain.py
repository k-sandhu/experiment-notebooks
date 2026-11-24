"""Random walkers simulation, plain Python 3.13 (stdlib only).

Walkers are split into WORKERS contiguous chunks and each chunk is processed in
its own process via multiprocessing. The reduction (sums, and a farthest-walker
max with smallest-index tie-break) is order-independent, so the output does not
depend on WORKERS.
"""

import sys
from multiprocessing import Pool

MASK = 0xFFFFFFFFFFFFFFFF
C = 0x9E3779B97F4A7C15
M1 = 0xBF58476D1CE4E5B9
M2 = 0x94D049BB133111EB
DX = (1, -1, 0, 0)
DY = (0, 0, 1, -1)


def walk_range(args):
    start, end, steps, b, seed = args
    spread = 0
    bumps = 0
    returns = 0
    best_dist = -1
    best_j = 0
    neg_b = -b
    mask = MASK
    c = C
    m1 = M1
    m2 = M2
    for j in range(start, end):
        state = (seed + j) & mask
        x = 0
        y = 0
        bu = 0
        re = 0
        for _ in range(steps):
            state = (state + c) & mask
            z = state
            z = ((z ^ (z >> 30)) * m1) & mask
            z = ((z ^ (z >> 27)) * m2) & mask
            d = (z ^ (z >> 31)) >> 62
            nx = x + DX[d]
            ny = y + DY[d]
            if neg_b <= nx <= b and neg_b <= ny <= b:
                x = nx
                y = ny
                if x == 0 and y == 0:
                    re += 1
            else:
                bu += 1
        spread += x * x + y * y
        bumps += bu
        returns += re
        dist = abs(x) + abs(y)
        if dist > best_dist:
            best_dist = dist
            best_j = j
    return spread, bumps, returns, best_dist, best_j


def main():
    path = sys.argv[1]
    workers = int(sys.argv[2])
    # Write LF line endings even on Windows (text mode would emit CRLF).
    sys.stdout.reconfigure(newline="\n")
    with open(path) as f:
        j, l, b, seed = map(int, f.read().split())

    nworkers = min(workers, j)
    base, rem = divmod(j, nworkers)
    args = []
    start = 0
    for w in range(nworkers):
        size = base + (1 if w < rem else 0)
        args.append((start, start + size, l, b, seed))
        start += size

    if nworkers == 1:
        results = [walk_range(args[0])]
    else:
        with Pool(nworkers) as pool:
            results = pool.map(walk_range, args)

    spread = 0
    bumps = 0
    returns = 0
    best_dist = -1
    best_j = 0
    for s, bu, re_, dist, jj in results:
        spread += s
        bumps += bu
        returns += re_
        if dist > best_dist:
            best_dist = dist
            best_j = jj

    print("spread", spread)
    print("bumps", bumps)
    print("returns", returns)
    print("farthest", best_j, best_dist)


if __name__ == "__main__":
    main()
