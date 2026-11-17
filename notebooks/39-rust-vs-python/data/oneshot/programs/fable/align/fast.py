import sys
from itertools import accumulate as _iacc

import numpy as np


def main():
    with open(sys.argv[1], 'rb') as f:
        data = f.read().split()

    alpha = data[0]
    A = len(alpha)
    ins = np.array(list(map(int, data[1:1 + A])), dtype=np.int64)
    dele = np.array(list(map(int, data[1 + A:1 + 2 * A])), dtype=np.int64)
    base = 1 + 2 * A
    sub = np.array(list(map(int, data[base:base + A * A])), dtype=np.int64).reshape(A, A)
    pos = base + A * A
    P = int(data[pos]) if pos < len(data) else 0
    pos += 1

    # letter -> index lookup; byte 0 maps to the dummy column A
    lut = np.zeros(256, dtype=np.intp)
    lut[np.frombuffer(alpha, dtype=np.uint8)] = np.arange(A, dtype=np.intp)
    lut[0] = A
    insx = np.zeros(A + 1, dtype=np.int64)
    insx[:A] = ins

    ns = [0] * P
    ms = [0] * P
    Rs = [0] * P
    scs = [None] * P
    tcxs = [None] * P
    frombuffer = np.frombuffer
    u8 = np.uint8
    for p in range(P):
        sb = data[pos + 2 * p]
        tb = data[pos + 2 * p + 1]
        sc = lut[frombuffer(sb, dtype=u8)]
        tcx = lut[frombuffer(b'\x00' + tb, dtype=u8)]
        scs[p] = sc
        tcxs[p] = tcx
        ns[p] = len(sb)
        ms[p] = len(tb)
        Rs[p] = int(dele[sc].sum()) + int(insx[tcx].sum())

    maxR = max(Rs) if P else 0
    if maxR + 1 > 2000000000:
        dt = np.int64
        lim = 1 << 62
    else:
        dt = np.int32
        lim = 2000000000

    # W[c][d] = sub[c][d] - ins[d] - del[c]; extra column A is 0
    Wext = np.zeros((A, A + 1), dtype=dt)
    Wext[:, :A] = (sub - ins[None, :] - dele[:, None]).astype(dt)

    WMAX = 1 << 15
    GC = 1 << 22

    order = sorted(range(P), key=ns.__getitem__, reverse=True)
    groups = []
    cur = []
    cw = 0
    cr = 0
    for p in order:
        w = ms[p] + 1
        r = Rs[p] + 1
        if cur and (cw + w > WMAX or cr + r > lim):
            groups.append(cur)
            cur = []
            cw = 0
            cr = 0
        cur.append(p)
        cw += w
        cr += r
    if cur:
        groups.append(cur)

    res = np.zeros(P, dtype=np.int64)
    Gbuf = np.empty(0, dtype=dt)
    Sbuf = np.empty(0, dtype=dt)

    add = np.add
    mn = np.minimum
    acc = np.minimum.accumulate
    take = np.take

    for grp in groups:
        k = len(grp)
        gn = [ns[p] for p in grp]
        widths = [ms[p] + 1 for p in grp]
        ends = list(_iacc(widths))
        starts = [e - w for e, w in zip(ends, widths)]
        Wg = ends[-1]
        nmax = gn[0]
        Rg = np.array([Rs[p] for p in grp], dtype=np.int64)
        offs = np.zeros(k, dtype=np.int64)
        if k > 1:
            offs[1:] = -np.cumsum(Rg[:-1] + 1)
        F = np.repeat(offs, widths).astype(dt)
        T = np.empty(Wg, dtype=dt)
        T[0] = 0

        Wl = [take(Wext, tcxs[p], axis=1) for p in grp]
        scl = [scs[p] for p in grp]

        CH = GC // Wg
        if CH < 1:
            CH = 1
        if CH > nmax:
            CH = nmax
        need = CH * Wg
        if Gbuf.size < need:
            Gbuf = np.empty(need, dtype=dt)
        G = Gbuf[:need].reshape(CH, Wg)
        need = CH * max(widths)
        if Sbuf.size < need:
            Sbuf = np.empty(need, dtype=dt)

        q = k - 1
        for r0 in range(0, nmax, CH):
            r1 = r0 + CH
            if r1 > nmax:
                r1 = nmax
            for x in range(k):
                n = gn[x]
                if n <= r0:
                    break
                e = n if n < r1 else r1
                cnt = e - r0
                m1 = widths[x]
                sv = Sbuf[:cnt * m1].reshape(cnt, m1)
                take(Wl[x], scl[x][r0:e], axis=0, out=sv, mode='clip')
                G[:cnt, starts[x]:ends[x]] = sv
            i = r0
            while i < r1:
                while gn[q] <= i:
                    q -= 1
                w = ends[q]
                j = gn[q]
                if j > r1:
                    j = r1
                F1 = F[:w - 1]
                T1 = T[1:w]
                Fw = F[:w]
                Tw = T[:w]
                for row in G[i - r0:j - r0, 1:w]:
                    add(F1, row, T1)
                    mn(Fw, Tw, Tw)
                    acc(Tw, out=Fw)
                i = j

        idx = np.array(ends, dtype=np.intp) - 1
        ans = F[idx].astype(np.int64) - offs + Rg
        res[grp] = ans

    vals = res.tolist()
    total = sum(vals)
    out = []
    if vals:
        out.append('\n'.join(map(str, vals)))
        out.append('\n')
    out.append('total %d\n' % total)
    sys.stdout.write(''.join(out))


if __name__ == '__main__':
    main()
