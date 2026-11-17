"""Weighted edit distance for many pairs, pure Python version.

Rows are stored shifted: E[i][j] = D[i][j] - P[j] with P the prefix sum of insertion costs
along t, which turns the recurrence into

    E[i][j] = min(E[i-1][j] + del[s_i], E[i-1][j-1] + sub[s_i][t_j] - ins[t_j], E[i][j-1])

so each cell needs two additions and two comparisons, with the profile row
sub[s_i][t_j] - ins[t_j] precomputed per letter of s.
"""
import sys


def cost(s, t, ins, dele, sub):
    m = len(t)
    pm = 0
    for c in t:
        pm += ins[c]
    profs = {}
    for c in set(s):
        row = sub[c]
        profs[c] = [row[y] - ins[y] for y in t]
    prev = [0] * (m + 1)
    for a in s:
        d = dele[a]
        run = prev[0] + d
        cur = [run]
        ap = cur.append
        x = prev[0]
        for y, p in zip(prev[1:], profs[a]):
            u = y + d
            v = x + p
            if v < u:
                u = v
            if u < run:
                run = u
            ap(run)
            x = y
        prev = cur
    return prev[m] + pm


def main():
    with open(sys.argv[1], "rb") as f:
        lines = f.read().split(b"\n")
    alpha = lines[0].strip().decode()
    A = len(alpha)
    ins = list(map(int, lines[1].split()))
    dele = list(map(int, lines[2].split()))
    sub = [list(map(int, lines[3 + i].split())) for i in range(A)]
    subt = [list(col) for col in zip(*sub)]
    P = int(lines[3 + A])
    idx = {ord(c): i for i, c in enumerate(alpha)}
    out = []
    total = 0
    for ln in lines[4 + A:4 + A + P]:
        s, t = ln.split()
        s = [idx[c] for c in s]
        t = [idx[c] for c in t]
        # Keep the longer string along the inner loop; the transposed problem swaps
        # ins/del and transposes sub.
        if len(s) > len(t):
            c = cost(t, s, dele, ins, subt)
        else:
            c = cost(s, t, ins, dele, sub)
        total += c
        out.append(str(c))
    out.append("total " + str(total))
    sys.stdout.buffer.write(("\n".join(out) + "\n").encode())


if __name__ == "__main__":
    main()
