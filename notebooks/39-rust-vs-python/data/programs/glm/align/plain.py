import sys
from itertools import accumulate, islice, repeat
from operator import add


def solve(s, t, idx, ins, dele, subrows, subT):
    # Rows run over s (kept the shorter string), columns over t.
    # Stored row S[j] = D[i][j] - I_j where I_j = prefix sum of insertion
    # costs of t.  S is always non-increasing (it is a running min), hence
    #   S_new[j] = min( S[j] + del(s_i),
    #                   min_{q<=j} ( S[q-1] + sub(s_i,t_q) - ins(t_q) ) )
    # i.e. an elementwise min against S[1:]+del, then a running min; and the
    # pair cost is S_final[m] + I_m.
    if len(s) > len(t):
        s, t = t, s
        ins, dele = dele, ins
        subrows = subT
    m = len(t)
    geti = idx.__getitem__
    tidx = list(map(geti, t))
    ins_t = list(map(ins.__getitem__, tidx))
    total_ins = sum(ins_t)
    if not s:
        return total_ins
    if not t:
        return sum(map(dele.__getitem__, map(geti, s)))

    # Per distinct letter of s: sub(s_i, t_j) - ins(t_j) along the columns.
    sci = {}
    for ci in set(map(geti, s)):
        row = subrows[ci]
        sci[ci] = [row[ti] - ic for ti, ic in zip(tidx, ins_t)]
    rows = [(sci[ci], dele[ci]) for ci in map(geti, s)]

    S = [0] * (m + 1)
    acc = accumulate
    for sc, dc in rows:
        S = list(acc(
            map(min, map(add, S, sc), map(add, islice(S, 1, None), repeat(dc))),
            min, initial=S[0] + dc))
    return S[m] + total_ins


def main():
    data = open(sys.argv[1], 'rb').read()
    toks = data.split()
    alpha = toks[0]
    a = len(alpha)
    idx = {c: i for i, c in enumerate(alpha)}
    head = 1 + 2 * a + a * a
    nums = list(map(int, toks[1:head]))
    ins = nums[:a]
    dele = nums[a:2 * a]
    sub = nums[2 * a:]
    subrows = [sub[i * a:(i + 1) * a] for i in range(a)]
    subT = [[subrows[j][i] for j in range(a)] for i in range(a)]
    p = int(toks[head])
    pos = head + 1
    out = []
    total = 0
    for _ in range(p):
        s = toks[pos]
        t = toks[pos + 1]
        pos += 2
        c = solve(s, t, idx, ins, dele, subrows, subT)
        total += c
        out.append(str(c))
    out.append("total %d" % total)
    sys.stdout.buffer.write(("\n".join(out) + "\n").encode())


main()
