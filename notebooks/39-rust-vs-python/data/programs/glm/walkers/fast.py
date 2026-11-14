"""Random walkers - NumPy version.

Key observations:

1. The SplitMix64 `state` only ever accumulates `+ GOLDEN` (the mixing is a
   pure function of the state and is not fed back), so step t of walker j
   draws  mix(s0 + t*GOLDEN)  with s0 = (SEED + j) mod 2^64.  The whole
   stream of raw random words for a walker is therefore an elementwise
   computation over an arithmetic progression - fully vectorizable.

2. Each step moves only one axis, so x follows an independent 1D "sticky"
   walk (a move that would leave the box is dropped) over its own increment
   subsequence, and likewise y.  Between dropped steps the true position
   equals the free cumulative sum plus a constant offset, and the exact
   one-sided correction against the wall at +b is (cummax(free) - b)+,
   against -b it is (cummin(free) + b)-.  So the axis is processed in
   blocks: compute the free cumsum of a block, apply the upper correction,
   then the lower one, and repeat until a round changes nothing (a lower
   correction can re-open the upper wall and vice versa).  For a box much
   wider than sqrt(block) this converges in about one round, and camping
   on a wall costs nothing extra.  Everything stays inside numpy ufuncs,
   which release the GIL.

Walkers are independent, so they are spread over WORKERS threads (output
does not depend on WORKERS).  Tiny boxes fall back to a scalar loop, which
is faster when bumps are extremely dense.
"""

import sys
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from struct import pack
import multiprocessing as mp

G = np.uint64(0x9E3779B97F4A7C15)
K1 = np.uint64(0xBF58476D1CE4E5B9)
K2 = np.uint64(0x94D049BB133111EB)
M64 = (1 << 64) - 1

# step -> (dx, dy)
LUT_X = np.array([1, -1, 0, 0], dtype=np.int32)
LUT_Y = np.array([0, 0, 1, -1], dtype=np.int32)

_SCALAR_B = 12  # boxes this narrow bump too often for the block method

# --- tiny-box fallback: same big-int packed generator + byte walk as
# --- plain.py (toy boxes bump far too often for the block method, and the
# --- walk is then fastest as a plain scalar loop over precomputed bytes)

Gx = 0x9E3779B97F4A7C15
Mx = (1 << 64) - 1
K1x = 0xBF58476D1CE4E5B9
K2x = 0x94D049BB133111EB
_CHUNK = 512
_TB = None


def _tables():
    global _TB
    if _TB is None:
        c = _CHUNK
        ones = int.from_bytes((b"\x01" + b"\x00" * 15) * c, "little")
        mask = Mx * ones
        a = int.from_bytes(
            b"".join(pack("<Q", t) + b"\x00" * 8 for t in range(1, c + 1)),
            "little",
        )
        _TB = (ones, mask, a)
    return _TB


def _d_stream(s0, l):
    ones, mask, a = _tables()
    out = bytearray()
    for base in range(0, l, _CHUNK):
        s = (((a * Gx) & mask) + ((s0 + base * Gx) & Mx) * ones) & mask
        z = ((s >> 30) ^ s) & mask
        z = z * K1x & mask
        z = (z ^ (z >> 27)) & mask
        z = z * K2x & mask
        z = ((z ^ (z >> 31)) & (3 * (ones << 62))) >> 6
        out += z.to_bytes(16 * _CHUNK, "little")[7::16]
    return bytes(out[:l])


def walker_scalar(task):
    j, l, b, seed = task
    x = 0
    y = 0
    bumps = 0
    returns = 0
    bp1 = b + 1
    nb1 = -b - 1
    for d in _d_stream((seed + j) & Mx, l):
        if d < 2:
            nx = x + 1 if d == 0 else x - 1
            if nx != bp1 and nx != nb1:
                x = nx
                if not nx and not y:
                    returns += 1
            else:
                bumps += 1
        else:
            ny = y + 1 if d == 2 else y - 1
            if ny != bp1 and ny != nb1:
                y = ny
                if not x and not ny:
                    returns += 1
            else:
                bumps += 1
    return x * x + y * y, bumps, returns, abs(x) + abs(y)


def axis_scalar(inc, b, out):
    """Scalar 1D sticky walk; used only for very narrow boxes."""
    x = 0
    bumps = 0
    k = 0
    for v in inc.tolist():
        nx = x + v
        if nx > b or nx < -b:
            bumps += 1
            out[k] = x
        else:
            x = nx
            out[k] = x
        k += 1
    return bumps


def axis_blocks(pos, b):
    """Turn per-block free-walk positions (rows of `pos`) into the true
    sticky-walk positions, in place.  Each row must start from the true
    position of the previous row's end.  Returns the number of bumps."""
    bumps = 0
    x0 = 0
    for row in pos:
        row += x0
        while True:
            over = np.maximum.accumulate(row)
            over -= b
            last = int(over[-1])
            if last > 0:  # over is non-decreasing, so [-1] is its max
                np.maximum(over, 0, out=over)
                row -= over
                bumps += last
            under = np.minimum.accumulate(row)
            under += b
            last = int(under[-1])
            if last < 0:
                np.minimum(under, 0, out=under)
                row -= under
                bumps -= last
                continue  # lower fix may have re-opened the upper wall
            break
        x0 = int(row[-1])
    return bumps


def walker_result(task):
    j, l, b, seed = task
    if l == 0:
        return 0, 0, 0, 0
    # raw words: mix(s0 + t*G) for t = 1..l  (state only ever adds G)
    s = np.arange(1, l + 1, dtype=np.uint64)
    s *= G
    s += np.uint64((seed + j) & M64)
    z = s >> np.uint64(30)
    z ^= s
    z *= K1
    z ^= z >> np.uint64(27)
    z *= K2
    z ^= z >> np.uint64(31)
    d = (z >> np.uint64(62)).astype(np.uint8)
    del z, s

    inc_x = LUT_X[d]
    inc_y = LUT_Y[d]
    del d

    if b < l and b >= _SCALAR_B:
        w = 32768 if b >= 128 else (16384 if b >= 32 else 4096)
        nb = (l + w - 1) // w
        pad = nb * w - l
        if pad:
            inc_x = np.concatenate((inc_x, np.zeros(pad, dtype=np.int32)))
            inc_y = np.concatenate((inc_y, np.zeros(pad, dtype=np.int32)))
        x_pos = inc_x.reshape(nb, w)
        x_pos.cumsum(axis=1, out=x_pos)
        y_pos = inc_y.reshape(nb, w)
        y_pos.cumsum(axis=1, out=y_pos)
        del inc_x, inc_y
        bumps = axis_blocks(x_pos, b)
        bumps += axis_blocks(y_pos, b)
    else:
        # free walk never leaves a box this wide (b >= l), or the box is so
        # narrow that the scalar loop wins
        x_pos = np.cumsum(inc_x, dtype=np.int32)
        y_pos = np.cumsum(inc_y, dtype=np.int32)
        if b < l:
            bumps = axis_scalar(inc_x, b, x_pos)
            bumps += axis_scalar(inc_y, b, y_pos)
        else:
            bumps = 0
        del inc_x, inc_y

    x_flat = x_pos.reshape(-1)
    y_flat = y_pos.reshape(-1)
    xf = int(x_flat[l - 1])
    yf = int(y_flat[l - 1])
    returns = int(np.count_nonzero((x_flat[:l] == 0) & (y_flat[:l] == 0)))
    return xf * xf + yf * yf, bumps, returns, abs(xf) + abs(yf)


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: fast.py INPUT_PATH [WORKERS]")
    with open(sys.argv[1]) as f:
        jj, ll, bb, seed = (int(t) for t in f.read().split())

    workers = 1
    if len(sys.argv) > 2:
        try:
            workers = int(sys.argv[2])
        except ValueError:
            workers = 1
    workers = max(1, min(workers, jj if jj > 0 else 1))

    tasks = [(j, ll, bb, seed) for j in range(jj)]
    chunk = (jj + workers - 1) // workers
    if bb < _SCALAR_B and bb < ll:
        # toy box: scalar byte-walk, GIL-bound, so use processes
        if workers > 1 and jj * ll >= 1_000_000:
            with mp.Pool(workers) as pool:
                results = pool.map(walker_scalar, tasks, chunksize=chunk)
        else:
            results = [walker_scalar(t) for t in tasks]
    elif workers > 1 and jj * ll >= 1_000_000:
        # Threads beat processes here: numpy releases the GIL and there is
        # no interpreter startup cost per worker.
        with ThreadPoolExecutor(max_workers=workers) as ex:
            results = list(ex.map(walker_result, tasks, chunksize=chunk))
    else:
        results = [walker_result(t) for t in tasks]

    spread = 0
    bumps = 0
    returns = 0
    best_d = -1
    best_j = 0
    if not results:
        best_d = 0
    for idx, (sp, bp, rt, dist) in enumerate(results):
        spread += sp
        bumps += bp
        returns += rt
        if dist > best_d:
            best_d = dist
            best_j = idx
    sys.stdout.buffer.write(
        (
            f"spread {spread}\n"
            f"bumps {bumps}\n"
            f"returns {returns}\n"
            f"farthest {best_j} {best_d}\n"
        ).encode()
    )


if __name__ == "__main__":
    main()
