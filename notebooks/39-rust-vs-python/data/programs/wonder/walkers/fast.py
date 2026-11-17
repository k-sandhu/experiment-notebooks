import sys

import numpy as np

MASK = (1 << 64) - 1
GOLD = 0x9E3779B97F4A7C15
M1 = 0xBF58476D1CE4E5B9
M2 = 0x94D049BB133111EB

_LUTX = np.array((1, -1, 0, 0), dtype=np.int64)
_LUTY = np.array((0, 0, 1, -1), dtype=np.int64)
_UGOLD = np.uint64(GOLD)
_UM1 = np.uint64(M1)
_UM2 = np.uint64(M2)


def _directions(init, start, end):
    """Direction codes (top 2 bits of SplitMix64 output) for steps start..end-1."""
    idx = np.arange(start + 1, end + 1, dtype=np.uint64)
    z = np.uint64(init) + idx * _UGOLD
    z = (z ^ (z >> np.uint64(30))) * _UM1
    z = (z ^ (z >> np.uint64(27))) * _UM2
    return z >> np.uint64(62)


def _sim_direct(init, L, B):
    """Per-step loop over precomputed direction bytes (dense-bump cases)."""
    dbytes = _directions(init, 0, L).astype(np.uint8).tobytes()
    x = 0
    y = 0
    bumps = 0
    returns = 0
    nB = -B
    for d in dbytes:
        if d == 0:
            if x == B:
                bumps += 1
            else:
                x += 1
                if x == 0 and y == 0:
                    returns += 1
        elif d == 1:
            if x == nB:
                bumps += 1
            else:
                x -= 1
                if x == 0 and y == 0:
                    returns += 1
        elif d == 2:
            if y == B:
                bumps += 1
            else:
                y += 1
                if x == 0 and y == 0:
                    returns += 1
        else:
            if y == nB:
                bumps += 1
            else:
                y -= 1
                if x == 0 and y == 0:
                    returns += 1
    return x, y, bumps, returns


def _sim_block(init, L, B):
    """Vectorised cumsum blocks; rescanning a block segment per bump.

    Inside a block the unconstrained positions are x0 + cumsum(dx).
    A bump only shifts the offset for the rest of the block, so the
    next segment of the same block is rescanned with a new offset.
    Bumps are rare for the B values this path is used for.
    """
    if B < 100:
        bs = 4096
    elif B < 250:
        bs = 8192
    else:
        bs = 16384
    x = 0
    y = 0
    bumps = 0
    returns = 0
    lutx = _LUTX
    luty = _LUTY
    for start in range(0, L, bs):
        end = start + bs
        if end > L:
            end = L
        d = _directions(init, start, end).astype(np.intp)
        cumx = np.cumsum(lutx[d])
        cumy = np.cumsum(luty[d])
        cnt = end - start
        s = 0
        base_x = 0
        base_y = 0
        while s < cnt:
            cx = cumx[s:]
            cy = cumy[s:]
            # Position at t is (x + cx[t]-base_x, y + cy[t]-base_y).
            tx = base_x - x
            ty = base_y - y
            viol = (cx > tx + B) | (cx < tx - B) | (cy > ty + B) | (cy < ty - B)
            if not viol.any():
                returns += int(np.count_nonzero((cx == tx) & (cy == ty)))
                x += int(cx[-1]) - base_x
                y += int(cy[-1]) - base_y
                break
            vrel = int(np.argmax(viol))
            if vrel:
                returns += int(np.count_nonzero((cx[:vrel] == tx) & (cy[:vrel] == ty)))
                x += int(cx[vrel - 1]) - base_x
                y += int(cy[vrel - 1]) - base_y
            bumps += 1
            v = s + vrel
            base_x = int(cumx[v])
            base_y = int(cumy[v])
            s = v + 1
    return x, y, bumps, returns


def sim_walker(args):
    j, L, B, seed = args
    if L == 0:
        return (0, 0, 0, j, 0)
    init = (seed + j) & MASK
    if B < 50:
        x, y, bumps, returns = _sim_direct(init, L, B)
    else:
        x, y, bumps, returns = _sim_block(init, L, B)
    return (x * x + y * y, bumps, returns, j, abs(x) + abs(y))


def main():
    argv = sys.argv
    with open(argv[1], "r") as f:
        parts = f.read().split()
    J = int(parts[0]); L = int(parts[1]); B = int(parts[2]); seed = int(parts[3])
    workers = int(argv[2]) if len(argv) > 2 else 1
    if workers < 1:
        workers = 1
    elif workers > 32:
        workers = 32

    if J == 0:
        sys.stdout.buffer.write(b"spread 0\nbumps 0\nreturns 0\nfarthest 0 0\n")
        return

    tasks = [(j, L, B, seed) for j in range(J)]
    if workers == 1 or J == 1:
        results = [sim_walker(t) for t in tasks]
    else:
        import multiprocessing as mp
        w = workers if workers < J else J
        with mp.Pool(processes=w) as pool:
            results = pool.map(sim_walker, tasks, chunksize=1)

    spread = 0; bumps = 0; returns = 0; best_j = 0; best_d = -1
    for sp, bu, re_, bj, bd in results:
        spread += sp; bumps += bu; returns += re_
        if bd > best_d:
            best_d = bd; best_j = bj
    if best_d < 0:
        best_d = 0
    sys.stdout.buffer.write(f"spread {spread}\nbumps {bumps}\nreturns {returns}\nfarthest {best_j} {best_d}\n".encode())


if __name__ == "__main__":
    main()
