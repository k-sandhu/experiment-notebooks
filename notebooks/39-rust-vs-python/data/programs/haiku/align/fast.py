"""Alignment cost, standard library plus NumPy.

Works on the shifted table g[i][j] = D[i][j] - C[j], where C[j] is the sum of
ins[t_1..t_j]. The insertion step becomes a running minimum, so one row update is
two vector minimums and one np.minimum.accumulate.

Pairs are batched: a group of pairs advances together, one row of s at a time, with
arrays shaped (columns, pairs) so each Python-level step does work on many pairs.
Pairs are sorted by length first so that groups waste little padding.
"""
import sys

import numpy as np

GROUP = 20  # pairs advanced together
SLAB = 60  # pairs per length slab; each slab is split into groups by t-length


def solve_group(group, subm, ins, dele):
    """group: list of (pair index, s letter indices, t letter indices).

    Returns {pair index: cost}.
    """
    g = len(group)
    rows = max(len(si) for _, si, _ in group)
    cols = max(len(ti) for _, _, ti in group)
    n_alpha = subm.shape[0]

    # letters[i, c]: letter of s for pair c at row i (padded with 0 past its end).
    letters = np.zeros((rows, g), np.intp)
    # prof[j, a, c] = sub[a][t_{j+1}] - ins[t_{j+1}] for pair c (padded columns hold junk
    # that never reaches a real column, since D[i][j] depends only on columns <= j).
    prof = np.zeros((cols, n_alpha, g), np.int64)
    finish = {}  # row count -> [(pair slot, m)]
    for c, (_, si, ti) in enumerate(group):
        letters[: len(si), c] = si
        m = len(ti)
        tpad = np.zeros(cols, np.intp)
        tpad[:m] = ti
        prof[:, :, c] = (subm[:, tpad] - ins[tpad]).T
        finish.setdefault(len(si), []).append((c, m))

    ar = np.arange(g)
    prev = np.zeros((cols + 1, g), np.int64)  # row 0: g[0][j] = 0 for all j
    cur = np.empty_like(prev)
    pre = np.empty_like(prev)
    diag = np.empty((cols, g), np.int64)
    final = np.zeros(g, np.int64)

    add = np.add
    minimum = np.minimum
    accumulate = np.minimum.accumulate
    for i in range(rows):
        lt = letters[i]
        d = dele[lt]
        p = prof[:, lt, ar]  # (cols, g): profile of each pair's i-th letter
        add(prev, d, out=pre)  # vertical move, all columns (pre[0] is final)
        add(prev[:-1], p, out=diag)  # diagonal move into column j = 1..cols
        minimum(pre[1:], diag, out=pre[1:])
        accumulate(pre, axis=0, out=cur)  # insertions: running minimum down the columns
        prev, cur = cur, prev
        for c, m in finish.get(i + 1, ()):
            final[c] = prev[m, c]

    out = {}
    for c, (k, _, ti) in enumerate(group):
        out[k] = int(final[c]) + int(ins[ti].sum())
    return out


def main():
    with open(sys.argv[1]) as f:
        letters = "".join(f.readline().split())
        tok = f.read().split()

    a = len(letters)
    ins = np.array(list(map(int, tok[:a])), dtype=np.int64)
    dele = np.array(list(map(int, tok[a : 2 * a])), dtype=np.int64)
    base = 2 * a
    subm = np.array(
        [list(map(int, tok[base + i * a : base + (i + 1) * a])) for i in range(a)],
        dtype=np.int64,
    )
    base += a * a

    lut = np.zeros(256, np.intp)
    lut[np.frombuffer(letters.encode(), np.uint8)] = np.arange(a)

    p = int(tok[base])
    base += 1
    pairs = []
    for k in range(p):
        s = tok[base + 2 * k]
        t = tok[base + 2 * k + 1]
        pairs.append(
            (
                k,
                lut[np.frombuffer(s.encode(), np.uint8)],
                lut[np.frombuffer(t.encode(), np.uint8)],
            )
        )

    # Slabs of similar s-length, then groups of similar t-length within each slab.
    pairs.sort(key=lambda x: len(x[1]))
    costs = {}
    for lo in range(0, p, SLAB):
        slab = sorted(pairs[lo : lo + SLAB], key=lambda x: len(x[2]))
        for glo in range(0, len(slab), GROUP):
            costs.update(solve_group(slab[glo : glo + GROUP], subm, ins, dele))

    out = [str(costs[k]) for k in range(p)]
    total = sum(costs.values())
    out.append(f"total {total}")
    sys.stdout.buffer.write(("\n".join(out) + "\n").encode())


if __name__ == "__main__":
    main()
