import sys

MASK = (1 << 64) - 1
GOLD = 0x9E3779B97F4A7C15
C1 = 0xBF58476D1CE4E5B9
C2 = 0x94D049BB133111EB

# SWAR block size (steps packed into one big integer).
BLOCK = 1024
_TOP2 = bytes(i >> 6 for i in range(256))
_swar = None  # lazily built (lane mask, packed per-block state increment)


def _swar_constants():
    global _swar
    if _swar is None:
        lane = b"\xff" * 8 + b"\x00" * 8
        maskp = int.from_bytes(lane * BLOCK, "little")
        delta = (BLOCK * GOLD) & MASK
        lane_d = delta.to_bytes(8, "little") + b"\x00" * 8
        deltap = int.from_bytes(lane_d * BLOCK, "little")
        _swar = (maskp, deltap)
    return _swar


def walker_scalar(seed, j, L, B):
    state = (seed + j) & MASK
    x = y = bumps = rets = 0
    gold = GOLD; c1 = C1; c2 = C2; mask = MASK
    for _ in range(L):
        state = (state + gold) & mask
        z = ((state ^ (state >> 30)) * c1) & mask
        # Top two bits are unaffected by the final z ^ (z >> 31).
        d = (((z ^ (z >> 27)) * c2) >> 62) & 3
        if d < 2:
            if d == 0:
                if x < B:
                    x += 1
                    if x == 0 and y == 0:
                        rets += 1
                else:
                    bumps += 1
            else:
                if x > -B:
                    x -= 1
                    if x == 0 and y == 0:
                        rets += 1
                else:
                    bumps += 1
        else:
            if d == 2:
                if y < B:
                    y += 1
                    if y == 0 and x == 0:
                        rets += 1
                else:
                    bumps += 1
            else:
                if y > -B:
                    y -= 1
                    if y == 0 and x == 0:
                        rets += 1
                else:
                    bumps += 1
    return x, y, bumps, rets


def walker_swar(seed, j, L, B):
    """Generate directions BLOCK steps at a time with one big integer.

    Each step's 64-bit state sits in the low half of a 128-bit lane.
    Lane-wise SplitMix64 then works with plain big-int ops: adding a
    replicated constant cannot carry between lanes, multiplying by a
    64-bit constant fills at most the 128-bit lane, and masking to the
    low 64 bits of each lane drops bits that shifts leak in from the
    next lane (they land only in the high half). Directions are the
    top two bits of each lane, read out through bytes.
    """
    maskp, deltap = _swar_constants()
    K = BLOCK
    nblocks, tail = divmod(L, K)
    base = (seed + j) & MASK

    ba = bytearray(16 * K)
    state = base
    for i in range(K):
        state = (state + GOLD) & MASK
        ba[i * 16: i * 16 + 8] = state.to_bytes(8, "little")
    packed = int.from_bytes(ba, "little")
    nbytes = 16 * K

    x = y = bumps = rets = 0
    c1 = C1; c2 = C2; top2 = _TOP2
    for blk in range(nblocks):
        if blk:
            packed = (packed + deltap) & maskp
        z = (packed ^ (packed >> 30)) & maskp
        z = (z * c1) & maskp
        z = (z ^ (z >> 27)) & maskp
        z = z * c2
        dbytes = z.to_bytes(nbytes, "little")[7::16].translate(top2)
        for d in dbytes:
            if d < 2:
                if d == 0:
                    if x < B:
                        x += 1
                        if x == 0 and y == 0:
                            rets += 1
                    else:
                        bumps += 1
                else:
                    if x > -B:
                        x -= 1
                        if x == 0 and y == 0:
                            rets += 1
                    else:
                        bumps += 1
            else:
                if d == 2:
                    if y < B:
                        y += 1
                        if y == 0 and x == 0:
                            rets += 1
                    else:
                        bumps += 1
                else:
                    if y > -B:
                        y -= 1
                        if y == 0 and x == 0:
                            rets += 1
                    else:
                        bumps += 1
    if tail:
        mask = MASK; gold = GOLD
        state = (base + nblocks * K * gold) & mask
        for _ in range(tail):
            state = (state + gold) & mask
            z = ((state ^ (state >> 30)) * c1) & mask
            d = (((z ^ (z >> 27)) * c2) >> 62) & 3
            if d < 2:
                if d == 0:
                    if x < B:
                        x += 1
                        if x == 0 and y == 0:
                            rets += 1
                    else:
                        bumps += 1
                else:
                    if x > -B:
                        x -= 1
                        if x == 0 and y == 0:
                            rets += 1
                    else:
                        bumps += 1
            else:
                if d == 2:
                    if y < B:
                        y += 1
                        if y == 0 and x == 0:
                            rets += 1
                    else:
                        bumps += 1
                else:
                    if y > -B:
                        y -= 1
                        if y == 0 and x == 0:
                            rets += 1
                    else:
                        bumps += 1
    return x, y, bumps, rets


def process_range(task):
    start, end, L, B, seed = task
    walker = walker_swar if L >= 4096 else walker_scalar
    spread = bumps = rets = 0
    best_j = start
    best_d = -1
    for j in range(start, end):
        x, y, b, r = walker(seed, j, L, B)
        spread += x * x + y * y
        bumps += b
        rets += r
        d = abs(x) + abs(y)
        if d > best_d:
            best_d = d
            best_j = j
    return spread, bumps, rets, best_j, best_d


def main():
    with open(sys.argv[1], "rb") as f:
        parts = f.read().split()
    J, L, B, seed = (int(parts[i]) for i in range(4))
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    workers = max(1, min(32, workers))

    if J <= 0:
        sys.stdout.write("spread 0\nbumps 0\nreturns 0\nfarthest 0 0\n")
        return

    workers = min(workers, J)
    # Contiguous, near-equal ranges of walker indices.
    q, rem = divmod(J, workers)
    tasks = []
    s = 0
    for w in range(workers):
        e = s + q + (1 if w < rem else 0)
        tasks.append((s, e, L, B, seed))
        s = e

    # Spawning processes only pays off when there is enough work.
    if workers > 1 and J * L >= 3_000_000:
        import multiprocessing as mp
        with mp.get_context("spawn").Pool(workers) as pool:
            results = pool.map(process_range, tasks)
    else:
        results = [process_range(t) for t in tasks]

    spread = bumps = rets = 0
    best_j = 0
    best_d = -1
    for sp, b, r, bj, bd in results:
        spread += sp
        bumps += b
        rets += r
        if bd > best_d or (bd == best_d and bj < best_j):
            best_d = bd
            best_j = bj
    sys.stdout.write(
        f"spread {spread}\nbumps {bumps}\nreturns {rets}\n"
        f"farthest {best_j} {best_d}\n"
    )


if __name__ == "__main__":
    main()
