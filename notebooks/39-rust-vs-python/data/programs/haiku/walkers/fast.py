import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np

GAMMA = np.uint64(0x9E3779B97F4A7C15)
MIX1 = np.uint64(0xBF58476D1CE4E5B9)
MIX2 = np.uint64(0x94D049BB133111EB)

WINDOW = 1 << 16  # steps per window: bounds the size of the temporary arrays
BLOCK = 256  # steps per block in the clamped-walk scan
MAX_GROUP = 16  # walkers handled together in one NumPy batch

# Column d holds the (x, y) step for d = r >> 62: 0 = x+1, 1 = x-1, 2 = y+1, 3 = y-1.
STEP_LUT = np.array([[1, -1, 0, 0], [0, 0, 1, -1]])


def walk_group(task):
    """Walk walkers first..last-1 in NumPy batches and return their combined partial result."""
    first, last, steps, bound, seed = task
    parts = [
        walk_batch(np.arange(lo, min(lo + MAX_GROUP, last), dtype=np.int64), steps, bound, seed)
        for lo in range(first, last, MAX_GROUP)
    ]
    return combine(parts)


def combine(parts):
    """Merge (spread, bumps, returns, best_dist, best_walker) tuples; ties go to the smallest walker."""
    spread = bumps = returns = 0
    best_dist, best_walker = -1, 0
    for p_spread, p_bumps, p_returns, p_dist, p_walker in parts:
        spread += p_spread
        bumps += p_bumps
        returns += p_returns
        if p_dist > best_dist or (p_dist == best_dist and p_walker < best_walker):
            best_dist, best_walker = p_dist, p_walker
    return spread, bumps, returns, max(best_dist, 0), best_walker


def walk_batch(walkers, steps, bound, seed):
    """Return (spread, bumps, returns, best_dist, best_walker) for an ascending array of walker numbers."""
    # Each axis is a walk clamped to [-bound, bound]: a step that leaves the box is a no-op.
    # The composition of clamped steps is again a clamp, so each block of steps is summarised by
    # (shift, lo, hi) and the block start positions follow from one short sequential pass.
    # Positions stay within [-bound, bound] and block shifts within BLOCK, so the narrowest safe type is used.
    dtype = np.int16 if bound + BLOCK < 2**15 else np.int32 if bound < 2**30 else np.int64
    lut = STEP_LUT.astype(dtype)
    count = len(walkers)
    base = np.uint64(seed) + walkers.astype(np.uint64)
    pos = np.zeros((2, count), dtype=dtype)
    bumps = 0
    returns = 0

    for w0 in range(0, steps, WINDOW):
        w = min(WINDOW, steps - w0)
        nb = -(-w // BLOCK)
        wp = nb * BLOCK

        # SplitMix64 output for steps w0+1 .. w0+w, all walkers at once (uint64 arithmetic wraps).
        t = np.arange(w0 + 1, w0 + w + 1, dtype=np.uint64)
        z = base[:, None] + t * GAMMA
        z ^= z >> 30
        z *= MIX1
        z ^= z >> 27
        z *= MIX2
        z ^= z >> 31
        d = (z >> 62).astype(np.intp)
        del z

        # Steps per axis, zero-padded so the window splits into whole blocks.
        s = np.zeros((2, count, wp), dtype=dtype)
        s[:, :, :w] = lut[:, d]
        sb = s.reshape(2, count, nb, BLOCK)

        # Pass 1: compose each block into (shift, lo, hi) with x -> clip(x + shift, lo, hi).
        shift = sb[..., 0].copy()
        lo = np.full((2, count, nb), -bound, dtype=dtype)
        hi = np.full((2, count, nb), bound, dtype=dtype)
        for k in range(1, BLOCK):
            sk = sb[..., k]
            shift += sk
            lo += sk
            np.clip(lo, -bound, bound, out=lo)
            hi += sk
            np.clip(hi, -bound, bound, out=hi)

        # Block start positions, from the positions at the start of this window.
        start = np.empty((2, count, nb), dtype=dtype)
        cur = pos
        for k in range(nb):
            start[..., k] = cur
            cur = np.clip(cur + shift[..., k], lo[..., k], hi[..., k])

        # Pass 2: replay every block from its start position, recording each position.
        P = np.empty((2, count, nb, BLOCK), dtype=dtype)
        cur = start
        for k in range(BLOCK):
            cur += sb[..., k]
            np.clip(cur, -bound, bound, out=cur)
            P[..., k] = cur
        P = P.reshape(2, count, wp)[:, :, :w]

        prev = np.empty_like(P)
        prev[..., 0] = pos
        prev[..., 1:] = P[..., :-1]
        moved = prev != P
        # Every non-zero step is an attempt; an attempt that did not move is a bump.
        bumps += int(np.count_nonzero(s[:, :, :w])) - int(np.count_nonzero(moved))
        moved_any = moved[0] | moved[1]
        returns += int(np.count_nonzero(moved_any & (P[0] == 0) & (P[1] == 0)))
        pos = P[..., -1].copy()

    fx = pos[0].astype(np.int64)
    fy = pos[1].astype(np.int64)
    spread = int(np.sum(fx * fx + fy * fy))
    dist = np.abs(fx) + np.abs(fy)
    i = int(np.argmax(dist))  # first maximum, so the smallest walker number on a tie
    return spread, bumps, returns, int(dist[i]), int(walkers[i])


def main():
    path = sys.argv[1]
    workers = int(sys.argv[2])
    with open(path) as f:
        walkers, steps, bound, seed = map(int, f.read().split())
    workers = max(1, min(workers, walkers))
    tasks = [
        (walkers * w // workers, walkers * (w + 1) // workers, steps, bound, seed)
        for w in range(workers)
    ]
    if workers == 1:
        parts = [walk_group(tasks[0])]
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            parts = list(pool.map(walk_group, tasks))
    spread, bumps, returns, best_dist, best_walker = combine(parts)

    report = (
        f"spread {spread}\n"
        f"bumps {bumps}\n"
        f"returns {returns}\n"
        f"farthest {best_walker} {best_dist}\n"
    )
    sys.stdout.buffer.write(report.encode())


if __name__ == "__main__":
    main()
