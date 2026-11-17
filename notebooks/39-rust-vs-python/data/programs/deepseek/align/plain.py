import sys


def main():
    path = sys.argv[1]
    with open(path, "rb") as f:
        data = f.read()

    toks = data.split()
    p = 0
    alpha = toks[p]
    p += 1
    A = len(alpha)
    tbl = bytearray(range(256))
    for k in range(A):
        tbl[alpha[k]] = k
    tbl = bytes(tbl)

    ins = [int(x) for x in toks[p:p + A]]
    p += A
    dele = [int(x) for x in toks[p:p + A]]
    p += A
    sub = []
    for i in range(A):
        sub.append([int(x) for x in toks[p:p + A]])
        p += A
    subT = [[sub[j][i] for j in range(A)] for i in range(A)]
    P = int(toks[p])
    p += 1

    # Shifted representation: H[j] = D[o][j] - prefix(icost)[j].  With
    #   cs[j] = sub[o][inner[j]] - icost[j]
    # one outer step is
    #   base[0] = H[0] + ocost
    #   base[j] = min(H[j] + ocost, H[j-1] + cs[j-1])
    #   H' = running_min(base)
    # and the answer is H'[last] + sum(icost).  The running min removes the
    # sequential left-to-right dependency of the direct recurrence, which lets
    # one row be a single tight loop over zipped lists.
    out = []
    total = 0
    for _ in range(P):
        s = toks[p].translate(tbl)
        t = toks[p + 1].translate(tbl)
        p += 2
        n = len(s)
        m = len(t)

        if n <= m:
            outer, inner = s, t
            ocost = dele
            icost = ins
            submat = sub
        else:
            outer, inner = t, s
            ocost = ins
            icost = dele
            submat = subT
            m = n

        icpos = [icost[x] for x in inner]
        ic_total = sum(icpos)
        mm = m + 1

        prev = [0] * mm
        csrows = [None] * A
        for o in outer:
            cs = csrows[o]
            if cs is None:
                row = submat[o]
                cs = [row[x] - icpos[j] for j, x in enumerate(inner)]
                csrows[o] = cs
            d = ocost[o]
            pv = prev
            cv = []
            ap = cv.append
            run = pv[0] + d
            ap(run)
            w = pv[0]
            for u, c in zip(pv[1:], cs):
                v = u + d
                x = w + c
                if x < v:
                    v = x
                if run < v:
                    v = run
                ap(v)
                run = v
                w = u
            prev = cv

        cost = prev[m] + ic_total
        out.append(str(cost))
        total += cost

    out.append("total " + str(total))
    sys.stdout.buffer.write(("\n".join(out) + "\n").encode())


main()
