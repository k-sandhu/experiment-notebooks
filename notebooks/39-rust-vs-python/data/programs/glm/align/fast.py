import sys

import numpy as np


def solve_pair(sb, tb, lut, ins, dele, sub):
    """Weighted edit distance for one pair of byte strings.

    Rows run over the shorter string (the DP is symmetric when the roles of
    ins/del are swapped and sub is transposed), which minimizes the number of
    Python-level row iterations. Per row, the sequential dependency
    cur[j-1] -> cur[j] is unrolled into a prefix-sum plus running minimum:

        cur[j] = pin[j] + min_{k<=j} ( G[k] - pin[k] )

    with G[k] = min(prev[k] + del, prev[k-1] + sub), so each row is a handful
    of whole-array NumPy operations with preallocated outputs.
    """
    if len(sb) > len(tb):
        sb, tb = tb, sb
        ins, dele = dele, ins
        sub = sub.T
    n = len(sb)
    m = len(tb)

    # Cell values are bounded by (n + m) * max_cost.
    dt = np.int32 if (n + m) * 1000 + 1000 < 2**31 else np.int64
    ins = ins.astype(dt, copy=False)
    dele = dele.astype(dt, copy=False)
    sub = sub.astype(dt, copy=False)

    ridx = lut[np.frombuffer(sb, np.uint8)]
    cidx = lut[np.frombuffer(tb, np.uint8)]
    insrow = ins[cidx]
    pin = np.empty(m + 1, dt)
    pin[0] = 0
    np.cumsum(insrow, out=pin[1:], dtype=dt)
    pin1 = pin[1:]

    buf_g = np.empty(m, dt)   # G values
    buf_v = np.empty(m, dt)   # prev[j-1] + sub
    buf_h = np.empty(m + 1, dt)  # running-minimum input / output
    buf_h1 = buf_h[1:]

    prev = pin.copy()  # row 0
    subrows = {}
    for k in ridx.tolist():
        d = int(dele[k])
        sr = subrows.get(k)
        if sr is None:
            sr = sub[k].take(cidx)
            subrows[k] = sr
        np.add(prev[1:], d, out=buf_g)          # prev[j] + d
        np.add(prev[:m], sr, out=buf_v)         # prev[j-1] + sub
        np.minimum(buf_g, buf_v, out=buf_g)     # G
        np.subtract(buf_g, pin1, out=buf_h1)    # G - pin, j = 1..m
        buf_h[0] = prev[0] + d
        np.minimum.accumulate(buf_h, out=buf_h)
        np.add(buf_h, pin, out=prev)            # cur = RM + pin
    return int(prev[-1])


def main():
    data = open(sys.argv[1], "rb").read()
    toks = data.split()
    pos = 0
    # Alphabet: leading tokens made of uppercase ASCII letters; either one
    # concatenated token ("ABC") or A single-letter tokens ("A B C").
    letters = []
    while pos < len(toks) and toks[pos].isalpha():
        letters.append(toks[pos])
        pos += 1
    alpha = b"".join(letters)
    a = len(alpha)
    lut = np.zeros(256, np.intp)
    for i, ch in enumerate(alpha):
        lut[ch] = i
    ins = np.array(toks[pos : pos + a], np.int64)
    pos += a
    dele = np.array(toks[pos : pos + a], np.int64)
    pos += a
    sub = np.array(toks[pos : pos + a * a], np.int64).reshape(a, a)
    pos += a * a
    p = int(toks[pos])
    pos += 1

    out = []
    total = 0
    for _ in range(p):
        s = toks[pos]
        t = toks[pos + 1]
        pos += 2
        cost = solve_pair(s, t, lut, ins, dele, sub)
        out.append(str(cost))
        total += cost
    out.append(f"total {total}")
    sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
