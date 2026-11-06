"""Alignment cost, standard library only.

Works on the shifted table g[i][j] = D[i][j] - C[j], where C[j] is the sum of
ins[t_1..t_j]. In these terms the insertion step is a running minimum along the
row, so each row is one list comprehension plus one itertools.accumulate call.
"""
import sys
from itertools import accumulate
from operator import add


def pair_cost(s, t, dele, ins_sum, prof_by_letter):
    m = len(t)
    prof = {c: list(map(prof_by_letter[c].__getitem__, t)) for c in set(s)}
    prev = [0] * (m + 1)
    for c in s:
        d = dele[c]
        p = prof[c]
        up = [x + d for x in prev]
        diag = map(add, prev, p)
        pre = [up[0]]
        pre += [u if u < v else v for u, v in zip(up[1:], diag)]
        prev = list(accumulate(pre, min))
    return prev[m] + ins_sum(t)


def main():
    with open(sys.argv[1]) as f:
        letters = "".join(f.readline().split())
        tok = f.read().split()

    a = len(letters)
    ins = dict(zip(letters, map(int, tok[:a])))
    dele = dict(zip(letters, map(int, tok[a : 2 * a])))
    base = 2 * a
    sub = {}
    for i, ci in enumerate(letters):
        row = map(int, tok[base + i * a : base + (i + 1) * a])
        sub[ci] = dict(zip(letters, row))
    base += a * a

    # prof_by_letter[c][x] = sub[c][x] - ins[x]: the per-letter profile without t.
    prof_by_letter = {
        c: {x: sub[c][x] - ins[x] for x in letters} for c in letters
    }

    def ins_sum(t):
        return sum(map(ins.__getitem__, t))

    p = int(tok[base])
    base += 1
    out = []
    total = 0
    for k in range(p):
        s = tok[base + 2 * k]
        t = tok[base + 2 * k + 1]
        cost = pair_cost(s, t, dele, ins_sum, prof_by_letter)
        total += cost
        out.append(str(cost))
    out.append(f"total {total}")
    sys.stdout.buffer.write(("\n".join(out) + "\n").encode())


if __name__ == "__main__":
    main()
