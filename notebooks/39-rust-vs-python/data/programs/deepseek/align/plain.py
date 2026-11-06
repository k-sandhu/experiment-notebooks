import sys


def main():
    path = sys.argv[1]
    with open(path, 'rb') as f:
        data = f.read()
    toks = data.split()
    alpha = toks[0]
    a_count = len(alpha)

    lut = bytearray(256)
    for i in range(a_count):
        lut[alpha[i]] = i
    lut = bytes(lut)

    p = 1
    ins = [int(x) for x in toks[p:p + a_count]]
    p += a_count
    dele = [int(x) for x in toks[p:p + a_count]]
    p += a_count
    sub = []
    for _ in range(a_count):
        sub.append([int(x) for x in toks[p:p + a_count]])
        p += a_count
    pairs = int(toks[p])
    p += 1

    sub_t = None
    res = []
    total = 0

    for _ in range(pairs):
        s = toks[p]
        t = toks[p + 1]
        p += 2

        # The alignment cost is symmetric: use the shorter string for the
        # (serial) row loop, the longer one for the inner loop.
        if len(s) > len(t):
            rows = t.translate(lut)
            cols = s.translate(lut)
            ins_e = dele
            del_e = ins
            if sub_t is None:
                sub_t = [list(r) for r in zip(*sub)]
            sub_e = sub_t
        else:
            rows = s.translate(lut)
            cols = t.translate(lut)
            ins_e = ins
            del_e = dele
            sub_e = sub

        m = len(cols)

        # Work in "R space": R[i][j] = D[i][j] - I[j] - J[i], where I[j] is the
        # prefix sum of the insertion costs of t and J[i] the prefix sum of the
        # deletion costs of s.  Both cancel out of the recurrence, leaving
        #   R'[j] = min(R'[j-1], R[j], R[j-1] + sub[s_i][t_j] - ins[t_j] - del[s_i])
        # with R[i][0] = 0 for every i.  The answer is R[n][m] + I[m] + J[n].
        insv = [ins_e[c] for c in cols]
        tot = sum(insv)

        vcache = {}
        for a in set(rows):
            row = sub_e[a]
            dv = del_e[a]
            vcache[a] = [row[c] - iv - dv for c, iv in zip(cols, insv)]

        q = [0] * (m + 1)
        for a in rows:
            v = vcache[a]
            tot += del_e[a]
            qp = 0          # R[j-1], starting with R[0] = 0
            left = 0        # R'[j-1], starting with R'[0] = 0
            acc = [0]
            ap = acc.append
            for qj, vj in zip(q[1:], v):
                c = qj
                if left < c:
                    c = left
                x = qp + vj
                if x < c:
                    c = x
                ap(c)
                left = c
                qp = qj
            q = acc

        ans = q[m] + tot
        total += ans
        res.append(str(ans))

    res.append('total ' + str(total))
    sys.stdout.buffer.write(('\n'.join(res) + '\n').encode())


main()
