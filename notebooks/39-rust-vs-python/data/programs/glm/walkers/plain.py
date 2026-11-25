"""Random walkers - standard library only.

Walker j uses SplitMix64 with state (SEED + j) mod 2^64.  Two speed tricks:

1. The `state` only ever accumulates `+ GOLDEN` (the mixing is a pure
   function of the state, not fed back), so step t draws mix(s0 + t*G).
   The whole stream is computed with big-integer arithmetic: a walker's
   states are packed into 128-bit lanes of one large integer (lane values
   are < 2^64, and products of two 64-bit numbers stay inside a 128-bit
   lane), so the mixer runs on all steps at C speed.  The top two bits of
   every lane are then gathered into a compact bytes object, one byte per
   step.

2. The walk itself iterates over that bytes object (iterating bytes yields
   small ints) with the branch logic kept flat.

Walkers are independent, so they are split over WORKERS processes (output
does not depend on WORKERS).
"""

import sys
import multiprocessing as mp
from struct import pack

G = 0x9E3779B97F4A7C15
M = (1 << 64) - 1
K1 = 0xBF58476D1CE4E5B9
K2 = 0x94D049BB133111EB
CHUNK = 512  # big-int lane count; tuned empirically

_TB = None


def _tables():
    global _TB
    if _TB is None:
        c = CHUNK
        ones = int.from_bytes((b"\x01" + b"\x00" * 15) * c, "little")
        mask = M * ones                      # low 64 bits of every lane
        a = int.from_bytes(
            b"".join(pack("<Q", t) + b"\x00" * 8 for t in range(1, c + 1)),
            "little",
        )
        _TB = (ones, mask, a)
    return _TB


def d_stream(s0, l):
    """All L draws of walker with seed s0 as bytes (top 2 bits per step)."""
    ones, mask, a = _tables()
    out = bytearray()
    for base in range(0, l, CHUNK):
        # state for local step t is (s0 + (base + t + 1) * G) mod 2^64
        s = (((a * G) & mask) + ((s0 + base * G) & M) * ones) & mask
        z = ((s >> 30) ^ s) & mask
        z = z * K1 & mask
        z = (z ^ (z >> 27)) & mask
        z = z * K2 & mask
        # keep bits 62-63 of each lane, moved to the low bits of byte 15t+7
        z = ((z ^ (z >> 31)) & (3 * (ones << 62))) >> 6
        out += z.to_bytes(16 * CHUNK, "little")[7::16]
    return bytes(out[:l])


def walk(task):
    j, l, b, seed = task
    x = 0
    y = 0
    bumps = 0
    returns = 0
    bp1 = b + 1
    nb1 = -b - 1
    for d in d_stream((seed + j) & M, l):
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
    spread = x * x + y * y
    dist = (x if x >= 0 else -x) + (y if y >= 0 else -y)
    return spread, bumps, returns, dist


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: plain.py INPUT_PATH [WORKERS]")
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
    # Process spawning has a fixed cost; only pay it when there is real work.
    if workers > 1 and jj * ll >= 1_000_000:
        with mp.Pool(workers) as pool:
            results = pool.map(walk, tasks, chunksize=(jj + workers - 1) // workers)
    else:
        results = [walk(t) for t in tasks]

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
