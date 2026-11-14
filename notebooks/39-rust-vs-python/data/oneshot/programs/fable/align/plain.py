import sys


def main():
    with open(sys.argv[1], 'rb') as f:
        tok = f.read().split()

    alpha = tok[0]
    A = len(alpha)
    p = 1
    ins = [int(x) for x in tok[p:p + A]]
    p += A
    dele = [int(x) for x in tok[p:p + A]]
    p += A

    # Gain tables indexed by byte code.
    # gain(a, b) = max(0, ins[b] + del[a] - sub[a][b])
    # D[n][m] = sum(ins over t) + sum(del over s) - (max total gain of a monotone matching)
    g = [None] * 256    # g[a][b]
    gt = [None] * 256   # gt[b][a]
    for b in alpha:
        gt[b] = [0] * 256
    for i in range(A):
        a = alpha[i]
        row = [0] * 256
        d = dele[i]
        for j in range(A):
            h = ins[j] + d - int(tok[p + j])
            if h > 0:
                b = alpha[j]
                row[b] = h
                gt[b][a] = h
        g[a] = row
        p += A

    P = int(tok[p])
    p += 1

    out = []
    total = 0
    alpha_list = list(alpha)
    rngA = range(A)

    for _ in range(P):
        s = tok[p]
        t = tok[p + 1]
        p += 2

        if s == t:
            out.append(0)
            continue

        base = 0
        for i in rngA:
            c = alpha_list[i]
            base += dele[i] * s.count(c) + ins[i] * t.count(c)

        if len(s) <= len(t):
            rows = s
            cols = t
            tab = g
        else:
            rows = t
            cols = s
            tab = gt

        Wd = {}
        for c in set(rows):
            Wd[c] = list(map(tab[c].__getitem__, cols))

        prev = [0] * len(cols)
        v = 0
        for W in map(Wd.__getitem__, rows):
            dg = v = 0
            prev = [
                (v := (x if (x := dg + w) > (y := (up if (dg := up) > v else v)) else y))
                for w, up in zip(W, prev)
            ]

        cost = base - v
        out.append(cost)
        total += cost

    lines = [str(c) for c in out]
    lines.append('total ' + str(total))
    sys.stdout.write('\n'.join(lines) + '\n')


if __name__ == '__main__':
    main()
