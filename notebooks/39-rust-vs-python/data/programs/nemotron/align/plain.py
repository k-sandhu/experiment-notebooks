"""Weighted edit distance for many string pairs.

Pure Python 3.13, standard library only. Single thread, single process.
"""

import sys


def edit_cost(s_idx, t_idx, s_del, t_ins, sub_rows):
    """Weighted Levenshtein distance D[n][m] using two rolling rows."""
    n = len(s_idx)
    m = len(t_idx)

    prev = [0] * (m + 1)
    acc = 0
    for j in range(m):
        acc += t_ins[j]
        prev[j + 1] = acc

    curr = [0] * (m + 1)
    for i in range(n):
        d = s_del[i]
        sub_row = sub_rows[s_idx[i]]

        cur = prev[0] + d
        curr[0] = cur
        prev_j = prev[0]  # prev[j - 1]
        for j in range(1, m + 1):
            tj = t_idx[j - 1]
            del_val = prev[j] + d
            ins_val = cur + t_ins[j - 1]
            sub_val = prev_j + sub_row[tj]
            cur = del_val if del_val < ins_val else ins_val
            if sub_val < cur:
                cur = sub_val
            curr[j] = cur
            prev_j = prev[j]

        prev, curr = curr, prev

    return prev[m]


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

    ins = [int(tok()) for _ in range(a)]
    del_cost = [int(tok()) for _ in range(a)]
    sub = [[int(tok()) for _ in range(a)] for _ in range(a)]

    p = int(tok())

    out = []
    total = 0
    append = out.append

    for _ in range(p):
        s_tok = tok()
        t_tok = tok()

        if s_tok == t_tok:
            cost = 0
        else:
            s_idx = [idx[b] for b in s_tok]
            t_idx = [idx[b] for b in t_tok]
            s_del = [del_cost[i] for i in s_idx]
            t_ins = [ins[i] for i in t_idx]
            cost = edit_cost(s_idx, t_idx, s_del, t_ins, sub)

        total += cost
        append(str(cost))

    out.append("total " + str(total))
    sys.stdout.buffer.write(("\n".join(out) + "\n").encode("ascii"))


if __name__ == "__main__":
    main()
