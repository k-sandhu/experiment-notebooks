import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np

M64 = 0xFFFFFFFFFFFFFFFF
GOLDEN = 0x9E3779B97F4A7C15
MIX1 = np.uint64(0xBF58476D1CE4E5B9)
MIX2 = np.uint64(0x94D049BB133111EB)

BLOCK = 1024  # longest block, in steps
SUB = 120  # sub-block length: running sums within a sub-block fit in int8
# Steps (walkers * time steps) handled per chunk. Small chunks stay in cache, which is best
# for one thread; with several threads, larger chunks keep NumPy outside the GIL for longer.
CHUNK_ONE_THREAD = 1 << 16
CHUNK_THREADS = 1 << 18

# How the walk is vectorised
# --------------------------
# x and y never interact: a step moves one axis, and whether it bumps depends only on
# that axis. Each axis is a +-1 walk clamped to [-b, b]. The steps are cut into blocks of
# K. Starting a block at position p, with c_k the running sum of its steps and
# M_k / m_k the running max / min of c (including 0):
#   * if max(c) - min(c) <= 2b, the walker can touch at most one wall in the block, and
#     the clamped path is   p + c_k - max(0, p + M_k - b) + max(0, -b - p - m_k)
#     (one-sided reflection); the bumps are the final values of the two corrections.
#   * the block maps the start p to the end   clamp(p + a, lo, hi)   with a = c_K and
#     lo / hi the ends of the walks that start at -b / +b.
# So: summarise all blocks at once, chain the block maps in a short Python loop to get
# every block's start, and count bumps from the block summaries. Positions are only
# rebuilt for blocks in which both coordinates may pass through 0, as only those can
# contain a return. Blocks whose range is wider than 2b (only possible when K > 2b) are
# walked column by column instead.
#
# Running sums are taken in int8 over sub-blocks of SUB steps (much faster than wider
# types); a block's summary is assembled from those of its sub-blocks.


class Layout:
    def __init__(self, steps, b, chunk):
        k = max(1, min(BLOCK, max(32, 2 * b), steps))
        self.sub = sub = min(SUB, k)
        self.subs = k // sub  # sub-blocks per block
        self.k = k = sub * self.subs
        chunks = -(-steps // chunk)
        per_chunk = -(-steps // chunks)
        self.t = t = k * -(-per_chunk // k)  # steps per chunk, a multiple of k
        self.chunks = -(-steps // t)
        self.group = max(1, chunk // t)  # walkers handled together
        # (i + 1) * GOLDEN for the steps of one chunk
        self.offsets = np.arange(1, t + 1, dtype=np.uint64) * np.uint64(GOLDEN)


def directions(states):
    """Top two bits of SplitMix64 for every state (in place on `states`)."""
    z = states
    t = z >> np.uint64(30)
    z ^= t
    z *= MIX1
    np.right_shift(z, np.uint64(27), out=t)
    z ^= t
    z *= MIX2
    # The final z ^ (z >> 31) leaves the top two bits alone; take them from the top byte
    # (byte 7 on a little-endian machine).
    top = z.view(np.uint8)[..., 7::8] if sys.byteorder == "little" else z.view(np.uint8)[..., ::8]
    return np.right_shift(top, 6)


def walk_columns(steps, start, b, path=None):
    """Walk the rows of `steps` one step at a time from `start`.
    Stores positions in `path` if given; returns (end positions, bumps)."""
    cols = np.ascontiguousarray(steps.T)
    p = start.astype(np.int64)
    bumps = 0
    for k in range(cols.shape[0]):
        q = p + cols[k]
        np.clip(q, -b, b, out=p)
        bumps += int(np.count_nonzero(q != p))
        if path is not None:
            path[:, k] = p
    return p, bumps


def axis_summary(steps, b, lay):
    """steps: (rows, K) int8. Returns the sub-block running sums and the block maps."""
    rows = steps.shape[0]
    c1 = np.cumsum(steps.reshape(-1, lay.sub), axis=1, dtype=np.int8)
    a1 = c1[:, -1].reshape(rows, lay.subs).astype(np.int16)
    before = np.cumsum(a1, axis=1, dtype=np.int16)  # block running sum after each sub-block
    a = before[:, -1].astype(np.int64)
    before -= a1  # ... and before it
    top = c1.max(axis=1).reshape(rows, lay.subs) + before
    bottom = c1.min(axis=1).reshape(rows, lay.subs) + before
    hi_c = np.maximum(top.max(axis=1), 0).astype(np.int64)
    lo_c = np.minimum(bottom.min(axis=1), 0).astype(np.int64)
    lo = a - lo_c - b
    hi = a - hi_c + b
    wide = np.flatnonzero(hi_c - lo_c > 2 * b)
    if wide.size:
        lo[wide] = walk_columns(steps[wide], np.full(wide.size, -b), b)[0]
        hi[wide] = walk_columns(steps[wide], np.full(wide.size, b), b)[0]
    return (c1.reshape(rows, lay.subs, lay.sub), before), a, lo, hi, hi_c, lo_c, wide


def running_sums(sums, idx):
    """Running sums within each block, for the blocks `idx`."""
    c1, before = sums
    c = c1[idx].astype(np.int64)
    c += before[idx][:, :, None]
    return c.reshape(idx.size, -1)


def axis_bumps(steps, starts, hi_c, lo_c, wide, b):
    """Bumps of every row, and a mask of the rows whose path may pass through 0."""
    over = starts + hi_c - b
    under = -b - starts - lo_c
    np.maximum(over, 0, out=over)
    np.maximum(under, 0, out=under)
    bumps = 0
    if wide.size:
        over[wide] = 0
        under[wide] = 0
        bumps = walk_columns(steps[wide], starts[wide], b)[1]
    # the path stays within [starts + lo_c - over, starts + hi_c + under]
    may_cross = (starts + lo_c <= over) & (starts + hi_c + under >= 0)
    if wide.size:
        may_cross[wide] = True
    return bumps + int(over.sum()) + int(under.sum()), may_cross


def axis_path(steps, c, starts, hi_c, lo_c, b):
    """Positions after every step of the given rows; c: their running sums (int64)."""
    path = c.copy()
    path += starts[:, None]
    narrow = hi_c - lo_c <= 2 * b
    up = np.flatnonzero((starts + hi_c > b) & narrow)
    if up.size:
        excess = np.maximum.accumulate(c[up], axis=1)
        excess += (starts[up] - b)[:, None]
        np.maximum(excess, 0, out=excess)
        path[up] -= excess
    down = np.flatnonzero((starts + lo_c < -b) & narrow)
    if down.size:
        excess = np.minimum.accumulate(c[down], axis=1)
        excess += (starts[down] + b)[:, None]
        np.negative(excess, out=excess)
        np.maximum(excess, 0, out=excess)
        path[down] += excess
    wide = np.flatnonzero(~narrow)
    if wide.size:
        sub = np.empty((wide.size, steps.shape[1]), dtype=np.int64)
        walk_columns(steps[wide], starts[wide], b, sub)
        path[wide] = sub
    return path


def walk_group(first, count, seed, steps, b, lay):
    """Walk walkers first .. first+count-1. Returns a list of (x, y, bumps, returns);
    only the totals of bumps and returns are needed, so they are booked on the first walker."""
    k, t = lay.k, lay.t
    nb = t // k
    x = [0] * count
    y = [0] * count
    bumps = returns = 0
    base = (np.arange(first, first + count, dtype=np.uint64) + np.uint64(seed & M64))[:, None]
    for chunk in range(lay.chunks):
        t0 = chunk * t
        states = lay.offsets[None, :] + (base + np.uint64(t0 * GOLDEN & M64))
        d = directions(states)
        valid = steps - t0
        if valid < t:
            d[:, valid:] = 4  # padding past the last step: no move
        rows = count * nb
        dx = np.subtract((d == 0).view(np.int8), (d == 1).view(np.int8)).reshape(rows, k)
        dy = np.subtract((d == 2).view(np.int8), (d == 3).view(np.int8)).reshape(rows, k)
        cx, ax, lox, hix, hicx, locx, widex = axis_summary(dx, b, lay)
        cy, ay, loy, hiy, hicy, locy, widey = axis_summary(dy, b, lay)

        # chain the block maps of each walker to find where every block starts
        starts_x = []
        starts_y = []
        add_x = starts_x.append
        add_y = starts_y.append
        maps = list(zip(ax.tolist(), lox.tolist(), hix.tolist(), ay.tolist(), loy.tolist(), hiy.tolist()))
        for w in range(count):
            px, py = x[w], y[w]
            for a1, l1, h1, a2, l2, h2 in maps[w * nb : (w + 1) * nb]:
                add_x(px)
                add_y(py)
                px += a1
                if px < l1:
                    px = l1
                elif px > h1:
                    px = h1
                py += a2
                if py < l2:
                    py = l2
                elif py > h2:
                    py = h2
            x[w], y[w] = px, py
        sx = np.array(starts_x, dtype=np.int64)
        sy = np.array(starts_y, dtype=np.int64)

        bx, cross_x = axis_bumps(dx, sx, hicx, locx, widex, b)
        by, cross_y = axis_bumps(dy, sy, hicy, locy, widey, b)
        bumps += bx + by

        # only blocks in which both coordinates may pass through 0 can hold a return
        near = np.flatnonzero(cross_x & cross_y)
        if near.size:
            px = axis_path(dx[near], running_sums(cx, near), sx[near], hicx[near], locx[near], b)
            py = axis_path(dy[near], running_sums(cy, near), sy[near], hicy[near], locy[near], b)
            px |= py
            returns += int(np.count_nonzero(px == 0))
        if valid < t:
            for w in range(count):
                if x[w] == 0 and y[w] == 0:
                    returns -= t - valid  # padding steps sitting at the origin
    out = [(x[w], y[w], 0, 0) for w in range(count)]
    out[0] = (x[0], y[0], bumps, returns)
    return out


def run_group(g, seed, total, steps, b, lay):
    first = g * lay.group
    return walk_group(first, min(lay.group, total - first), seed, steps, b, lay)


def main():
    with open(sys.argv[1]) as f:
        j, steps, b, seed = map(int, f.read().split()[:4])
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    # A walker never gets farther than `steps` from the origin, so a larger box acts the same.
    b = min(b, steps + 1)

    results = []
    if j > 0 and steps > 0:
        workers = max(1, min(workers, j))
        lay = Layout(steps, b, CHUNK_ONE_THREAD if workers == 1 else CHUNK_THREADS)
        groups = -(-j // lay.group)
        workers = min(workers, groups)
        if workers == 1:
            parts = [run_group(g, seed, j, steps, b, lay) for g in range(groups)]
        else:
            # Threads, not processes: NumPy releases the GIL inside its array loops, which
            # are most of the work, and threads start instantly while a process on Windows
            # needs a fresh interpreter plus a NumPy import. Groups are taken dynamically.
            with ThreadPoolExecutor(workers) as pool:
                parts = list(pool.map(lambda g: run_group(g, seed, j, steps, b, lay), range(groups)))
        for part in parts:
            results.extend(part)
    else:
        results = [(0, 0, 0, 0)] * j

    spread = bumps = returns = 0
    best_j, best_d = 0, -1
    for w, (x, y, bu, re) in enumerate(results):
        spread += x * x + y * y
        bumps += bu
        returns += re
        d = abs(x) + abs(y)
        if d > best_d:
            best_d, best_j = d, w
    if best_d < 0:
        best_d = 0
    sys.stdout.buffer.write(
        f"spread {spread}\nbumps {bumps}\nreturns {returns}\nfarthest {best_j} {best_d}\n".encode()
    )


if __name__ == "__main__":
    main()
