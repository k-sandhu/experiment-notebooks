import sys

MASK = (1 << 64) - 1
GAMMA = 0x9E3779B97F4A7C15
C1 = 0xBF58476D1CE4E5B9
C2 = 0x94D049BB133111EB

# ---------------------------------------------------------------------------
# Random numbers are produced in bulk with "SWAR" inside Python's big
# integers: 1024 counters are packed into one integer, one per 128-bit lane.
# A lane value stays below 2^128 after every multiply, so the scalar
# multiplication acts on all lanes independently at C speed.  The final
# xorshift (>> 31) of SplitMix64 never changes the top two bits, so only the
# second multiply's result is needed to obtain d = r >> 62.
# ---------------------------------------------------------------------------

_BATCH = 1024
_LANE = 128
_BYTES = 16 * _BATCH

_M64R = int.from_bytes((b"\xff" * 8 + b"\x00" * 8) * _BATCH, "little")
_R = ((1 << (_LANE * _BATCH)) - 1) // ((1 << _LANE) - 1)
_X = 1 << _LANE
_K = (
    _X
    * (
        1
        - _BATCH * (1 << (_LANE * (_BATCH - 1)))
        + (_BATCH - 1) * (1 << (_LANE * _BATCH))
    )
) // ((1 - _X) ** 2)
_D_TABLE = bytes(i >> 6 for i in range(256))


def _draw_d(steps, seed):
    """Return a bytes object with the d = r >> 62 value of each step."""
    out = bytearray(steps)
    m = MASK
    g = GAMMA
    c1 = C1
    c2 = C2
    mask = _M64R
    r = _R
    k = _K
    table = _D_TABLE
    base = (seed + g) & m
    pos = 0
    full = (steps // _BATCH) * _BATCH
    while pos < full:
        p = (base * r + g * k) & mask
        a = (p ^ (p >> 30)) & mask
        b = (a * c1) & mask
        c = (b ^ (b >> 27)) & mask
        e = (c * c2) & mask
        out[pos : pos + _BATCH] = e.to_bytes(_BYTES, "little")[7::16].translate(table)
        pos += _BATCH
        base = (base + g * _BATCH) & m
    if pos < steps:
        s = (base - g) & m
        for i in range(pos, steps):
            s = (s + g) & m
            z = s
            z = ((z ^ (z >> 30)) * c1) & m
            z = ((z ^ (z >> 27)) * c2) & m
            out[i] = z >> 62
    return out


def run_walker(args):
    j, steps, bound, seed = args
    ds = _draw_d(steps, (seed + j) & MASK)
    x = 0
    y = 0
    bumps = 0
    returns = 0
    b = bound
    for d in ds:
        if d == 0:
            if x < b:
                x += 1
                if x == 0 and y == 0:
                    returns += 1
            else:
                bumps += 1
        elif d == 1:
            if x > -b:
                x -= 1
                if x == 0 and y == 0:
                    returns += 1
            else:
                bumps += 1
        elif d == 2:
            if y < b:
                y += 1
                if x == 0 and y == 0:
                    returns += 1
            else:
                bumps += 1
        else:
            if y > -b:
                y -= 1
                if x == 0 and y == 0:
                    returns += 1
            else:
                bumps += 1
    return j, x, y, bumps, returns


def run_chunk(jobs):
    return [run_walker(a) for a in jobs]


def main():
    if len(sys.argv) < 2:
        sys.stderr.write("usage: plain.py INPUT_PATH WORKERS\n")
        return 1
    path = sys.argv[1]
    workers = 1
    if len(sys.argv) > 2:
        try:
            workers = int(sys.argv[2])
        except ValueError:
            workers = 1
    workers = max(1, min(32, workers))

    with open(path, "rb") as f:
        parts = f.read().split()
    j_count = int(parts[0])
    steps = int(parts[1])
    bound = int(parts[2])
    seed = int(parts[3]) & MASK

    if j_count <= 0:
        sys.stdout.buffer.write(b"spread 0\nbumps 0\nreturns 0\nfarthest 0 0\n")
        return 0

    jobs = [(j, steps, bound, seed) for j in range(j_count)]

    if workers == 1 or j_count == 1:
        results = run_chunk(jobs)
    else:
        from multiprocessing import Pool

        n = min(workers, j_count)
        chunks = [jobs[w::n] for w in range(n)]
        with Pool(processes=n) as pool:
            chunks_out = pool.map(run_chunk, chunks)
        results = [r for chunk in chunks_out for r in chunk]

    results.sort(key=lambda r: r[0])

    spread = 0
    bumps = 0
    returns = 0
    best_j = 0
    best_d = -1
    for j, x, y, bmp, ret in results:
        spread += x * x + y * y
        bumps += bmp
        returns += ret
        d = abs(x) + abs(y)
        if d > best_d:
            best_d = d
            best_j = j

    sys.stdout.buffer.write(
        (
            "spread %d\nbumps %d\nreturns %d\nfarthest %d %d\n"
            % (spread, bumps, returns, best_j, best_d)
        ).encode()
    )
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
