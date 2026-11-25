"""Weighted edit distance for many pairs, NumPy version.

Rows are stored shifted: E[i][j] = D[i][j] - P[j] with P the prefix sum of insertion costs
along t, which turns the recurrence into

    E[i][j] = min(E[i-1][j] + del[s_i], E[i-1][j-1] + sub[s_i][t_j] - ins[t_j], E[i][j-1])

so the horizontal step is a running minimum (np.minimum.accumulate).

Pairs are processed in batches: a batch is a 2D array with one row-of-the-table per pair,
padded to the widest pair. Batches are chosen by a small DP over pairs sorted by width, and
inside a batch pairs are sorted by row count so the pairs still running form a prefix.
"""
import sys

import numpy as np


def main():
    with open(sys.argv[1], "rb") as f:
        lines = f.read().split(b"\n")
    alpha = lines[0].strip()
    A = len(alpha)
    ins = np.array(lines[1].split(), dtype=np.int64)
    dele = np.array(lines[2].split(), dtype=np.int64)
    sub = np.array(b" ".join(lines[3:3 + A]).split(), dtype=np.int64).reshape(A, A)
    P = int(lines[3 + A])
    pairs = [ln.split() for ln in lines[4 + A:4 + A + P]]

    # Letter -> index, applied with bytes.translate.
    trans = bytearray(range(256))
    for i, c in enumerate(alpha):
        trans[c] = i
    trans = bytes(trans)

    # Orientation: the shorter string runs down the rows. The transposed problem swaps
    # ins/del and transposes sub. sw = 1 marks a swapped pair.
    rows = []
    for k, (s, t) in enumerate(pairs):
        if len(s) > len(t):
            rows.append((len(t), len(s), 1, t, s, k))
        else:
            rows.append((len(s), len(t), 0, s, t, k))
    # Profile tables per orientation: prof[s][t] = sub'[s][t] - ins'[t].
    tbls = (sub - ins[None, :], sub.T - dele[None, :])
    dtbls = (dele, ins)
    pms = (ins, dele)
    # Group pairs of similar width; each group is one padded 2D batch.
    rows.sort(key=lambda r: r[1])
    ns = np.array([r[0] for r in rows], dtype=np.float64)
    ms = np.array([r[1] for r in rows], dtype=np.float64)
    out = [0] * P
    for g0, g1 in _groups(ns, ms):
        _solve(rows[g0:g1], A, trans, tbls, dtbls, pms, out)

    total = sum(out)
    sys.stdout.buffer.write(("\n".join(map(str, out)) + "\ntotal " + str(total) + "\n").encode())


def _groups(ns, ms, crow=12e-6, ccell=4e-9):
    """Split pairs (sorted by m ascending) into contiguous groups minimising the
    estimated time: per-row call overhead plus padded cell work."""
    K = len(ms)
    best = np.zeros(K + 1)
    cut = np.zeros(K + 1, dtype=np.int64)
    LB = 512
    for e in range(1, K + 1):
        lo = max(0, e - LB)
        # groups [s, e) for s in lo..e-1
        nmax = np.maximum.accumulate(ns[lo:e][::-1])[::-1]
        nsum = np.cumsum(ns[lo:e][::-1])[::-1]
        c = best[lo:e] + crow * nmax + ccell * nsum * (ms[e - 1] + 1)
        j = int(np.argmin(c))
        best[e] = c[j]
        cut[e] = lo + j
    out = []
    e = K
    while e > 0:
        out.append((int(cut[e]), e))
        e = int(cut[e])
    return out[::-1]


def _solve(rows, A, trans, tbls, dtbls, pms, out):
    """rows: (n, m, sw, s, t, k) for one group. Pads columns to the widest pair; rows
    are sorted by n descending so the pairs still running form a prefix."""
    rows.sort(key=lambda r: -r[0])
    B = len(rows)
    maxn = rows[0][0]
    M = max(r[1] for r in rows)
    dt = np.int32 if 1000 * (maxn + 2 * M + 8) < (1 << 30) else np.int64
    Q = np.zeros((B * A, M + 1), dtype=dt)
    SI = np.full((B, maxn), 0, dtype=np.intp)
    DT = np.zeros((B, maxn), dtype=dt)
    ns = []
    pm = []
    for k, (n, m, sw, s, t, _) in enumerate(rows):
        tk = np.frombuffer(t.translate(trans), dtype=np.uint8)
        Q[k * A:(k + 1) * A, 1:m + 1] = tbls[sw][:, tk]
        sk = np.frombuffer(s.translate(trans), dtype=np.uint8)
        SI[k, :n] = sk
        SI[k, :n] += k * A
        DT[k, :n] = dtbls[sw][sk]
        pm.append(int(pms[sw][tk].sum()))
        ns.append(n)
    SI = np.ascontiguousarray(SI.T)
    DT = np.ascontiguousarray(DT.T)[:, :, None]
    prev = np.zeros((B, M + 1), dtype=dt)
    cur = np.empty_like(prev)
    qbuf = np.empty_like(prev)
    act = B
    for i in range(maxn):
        a = act
        q = np.take(Q, SI[i, :a], axis=0, out=qbuf[:a])
        p = prev[:a]
        c = cur[:a]
        np.add(p, DT[i, :a], out=c)
        np.add(p[:, :-1], q[:, 1:], out=q[:, 1:])
        np.minimum(c[:, 1:], q[:, 1:], out=c[:, 1:])
        np.minimum.accumulate(c, axis=1, out=c)
        prev, cur = cur, prev
        while act > 0 and ns[act - 1] == i + 1:
            act -= 1
            r = rows[act]
            out[r[5]] = int(prev[act, r[1]]) + pm[act]


if __name__ == "__main__":
    main()
