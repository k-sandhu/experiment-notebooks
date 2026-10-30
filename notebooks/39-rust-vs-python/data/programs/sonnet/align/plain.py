import sys
from itertools import accumulate
from operator import add


def main():
    with open(sys.argv[1], "rb") as f:
        tok = f.read().split()
    alpha = tok[0].decode()
    a = len(alpha)
    pos = 1
    ins = [int(x) for x in tok[pos:pos + a]]
    pos += a
    dele = [int(x) for x in tok[pos:pos + a]]
    pos += a
    sub = []
    for _ in range(a):
        sub.append([int(x) for x in tok[pos:pos + a]])
        pos += a
    p = int(tok[pos])
    pos += 1
    amap = {ord(c): i for i, c in enumerate(alpha)}

    out = []
    total = 0
    # F[i][j] = D[i][j] - C_i - P_j (C = prefix sum of deletions of s, P = of insertions of t):
    #   F[i][j] = min(F[i-1][j], F[i][j-1], F[i-1][j-1] + sub - ins[t_j] - del[s_i])
    # so a row is a prefix minimum over min(old[1:], old[:-1] + w).
    cache = {}
    for _ in range(p):
        s = tok[pos]
        t = tok[pos + 1]
        pos += 2
        key = (s, t)
        r = cache.get(key)
        if r is None:
            ti = [amap[c] for c in t]
            ps = sum([ins[b] for b in ti])
            cs = 0
            prof = {}
            row = [0] * (len(ti) + 1)
            for ch in s:
                c = amap[ch]
                cs += dele[c]
                w = prof.get(c)
                if w is None:
                    sr = sub[c]
                    d = dele[c]
                    w = prof[c] = [sr[b] - ins[b] - d for b in ti]
                row = list(accumulate(map(min, row[1:], map(add, row, w)), min, initial=0))
            r = row[-1] + cs + ps
            cache[key] = r
        out.append(r)
        total += r
    out.append("total %d" % total)
    sys.stdout.buffer.write(("\n".join(map(str, out)) + "\n").encode())


main()
