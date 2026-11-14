"""Weighted edit distance for many string pairs.

Python 3.13 with NumPy 2.2. Single thread, single process.

Algorithm: weighted Levenshtein DP with two rolling rows. The row update

    curr[j] = min(prev[j] + d,
                  curr[j-1] + ins_j,
                  prev[j-1] + sub[s_i][t_j])

has a left-to-right dependency through curr[j-1]. Eliminate it by defining

    L[0] = prev[0] + d
    L[j] = min(prev[j] + d, prev[j-1] + sub[s_i][t_j])   (j >= 1)

so that curr[j] = min(L[j], curr[j-1] + ins_j). Unrolling that recurrence

    curr[j] = min_{0 <= k <= j} (L[k] + sum_{r=k+1..j} ins_r)

and with P[j] = sum_{r=1..j} ins_r, P[0] = 0, this becomes

    curr[j] = P[j] + min_{0 <= k <= j} (L[k] - P[k])

which is one subtraction, one running-minimum prefix scan, and one addition -
all vectorisable with NumPy. The reformulation is exact for any costs.
"""

import sys

import numpy as np


def edit_cost(s_idx, t_idx, del_costs, ins_costs, sub_mat):
    n = len(s_idx)
    m = len(t_idx)

    t_idx = np.asarray(t_idx, dtype=np.int64)
    ins_t = ins_costs[t_idx]

    # P[j] = insertion-cost prefix sum over t[1..j], P[0] = 0.
    # Row 0 of the DP table (D[0][j] = cumsum of ins[t_j]) equals P.
    p = np.empty(m + 1, dtype=np.int64)
    p[0] = 0
    np.cumsum(ins_t, out=p[1:])

    prev = p.copy()
    curr = np.empty(m + 1, dtype=np.int64)
    left = np.empty(m + 1, dtype=np.int64)   # L[k]
    scratch = np.empty(m + 1, dtype=np.int64)  # L[k] - P[k]

    for i in range(n):
        d = del_costs[s_idx[i]]
        sub_col = sub_mat[s_idx[i], t_idx]

        left[0] = prev[0] + d
        np.minimum(prev[1:] + d, prev[:-1] + sub_col, out=left[1:])

        np.subtract(left, p, out=scratch)
        np.minimum.accumulate(scratch, out=scratch)
        np.add(scratch, p, out=curr)

        prev, curr = curr, prev

    return int(prev[m])


def main() -> None:
    path = sys.argv[1]
    with open(path, "rb") as f:
        toks = f.read().split()

    pos = 0

    def tok() -> bytes:
        nonlocal pos
        t = toks[pos]
        pos += 1
        return t

    alphabet = tok()
    idx = [255] * 256
    for i, b in enumerate(alphabet):
        idx[b] = i
    a = len(alphabet)

    ins = np.array([int(tok()) for _ in range(a)], dtype=np.int64)
    del_costs = np.array([int(tok()) for _ in range(a)], dtype=np.int64)
    sub_mat = np.array(
        [[int(tok()) for _ in range(a)] for _ in range(a)], dtype=np.int64
    )

    p = int(tok())

    out = []
    total = 0
    append = out.append

    for _ in range(p):
        s_tok = tok()
        t_tok = tok()

        if s_tok == t_tok:
            # All costs are non-negative, so equal strings cost 0.
            cost = 0
        else:
            s_idx = [idx[b] for b in s_tok]
            t_idx = [idx[b] for b in t_tok]
            cost = edit_cost(s_idx, t_idx, del_costs, ins, sub_mat)

        total += cost
        append(str(cost))

    out.append("total " + str(total))
    sys.stdout.buffer.write(("\n".join(out) + "\n").encode("ascii"))


if __name__ == "__main__":
    main()
