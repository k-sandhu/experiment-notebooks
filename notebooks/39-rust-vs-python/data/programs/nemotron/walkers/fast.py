"""Random walkers simulation, Python 3.13 + NumPy 2.2.

All J walkers are evolved in lockstep: their generator states, positions and
counters are NumPy arrays, so one Python iteration advances every walker by one
step. SplitMix64 arithmetic on uint64 arrays wraps modulo 2^64 automatically.
Walkers are independent, so the result does not depend on WORKERS (which is
accepted for interface compatibility).

Notes on speed: NumPy's per-call overhead dominates for small walker counts
because the per-step random-number stream is inherently sequential per walker,
so this version runs in a single process and keeps the per-step call count
small.
"""

import sys

import numpy as np

C = np.uint64(0x9E3779B97F4A7C15)
M1 = np.uint64(0xBF58476D1CE4E5B9)
M2 = np.uint64(0x94D049BB133111EB)
# Direction deltas for d = 0, 1, 2, 3: +x, -x, +y, -y
DX = np.array((1, -1, 0, 0), dtype=np.int64)
DY = np.array((0, 0, 1, -1), dtype=np.int64)


def solve(j, l, b, seed):
    states = np.arange(j, dtype=np.uint64) + np.uint64(seed)
    x = np.zeros(j, dtype=np.int64)
    y = np.zeros(j, dtype=np.int64)
    bumps = np.zeros(j, dtype=np.int64)
    returns = np.zeros(j, dtype=np.int64)
    z = np.empty(j, dtype=np.uint64)
    nx = np.empty(j, dtype=np.int64)
    ny = np.empty(j, dtype=np.int64)

    for _ in range(l):
        states += C
        z = states ^ (states >> 30)
        z = z * M1
        z = z ^ (z >> 27)
        z = z * M2
        d = (z ^ (z >> 31)) >> 62

        nx = x + np.take(DX, d)
        ny = y + np.take(DY, d)
        ok = (np.abs(nx) <= b) & (np.abs(ny) <= b)
        np.copyto(x, nx, where=ok)
        np.copyto(y, ny, where=ok)
        moved = ok & (x == 0) & (y == 0)
        returns += moved
        bumps += ~ok

    spread = int((x * x + y * y).sum())
    bump_total = int(bumps.sum())
    return_total = int(returns.sum())
    dist = np.abs(x) + np.abs(y)
    best_j = int(dist.argmax())
    return spread, bump_total, return_total, best_j, int(dist[best_j])


def main():
    path = sys.argv[1]
    workers = int(sys.argv[2])  # accepted; the result is independent of WORKERS
    # Write LF line endings even on Windows (text mode would emit CRLF).
    sys.stdout.reconfigure(newline="\n")
    with open(path) as f:
        j, l, b, seed = map(int, f.read().split())

    spread, bumps, returns, best_j, best_dist = solve(j, l, b, seed)

    print("spread", spread)
    print("bumps", bumps)
    print("returns", returns)
    print("farthest", best_j, best_dist)


if __name__ == "__main__":
    main()
