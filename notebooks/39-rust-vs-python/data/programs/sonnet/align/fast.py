import sys
import numpy as np


def main():
    with open(sys.argv[1], "rb") as f:
        tok = f.read().split()
    alpha = tok[0]
    a = len(alpha)
    pos = 1
    ins = np.array(tok[pos:pos + a], dtype=np.int64)
    pos += a
    dele = np.array(tok[pos:pos + a], dtype=np.int64)
    pos += a
    sub = np.array(tok[pos:pos + a * a], dtype=np.int64).reshape(a, a)
    pos += a * a
    p = int(tok[pos])
    pos += 1

    lut = np.zeros(256, dtype=np.intp)
    lut[np.frombuffer(alpha, dtype=np.uint8)] = np.arange(a)

    pairs = tok[pos:pos + 2 * p]
    maxlen = max((len(x) for x in pairs), default=1)
    maxc = int(max(ins.max(), dele.max(), sub.max()))
    dt = np.int32 if maxc * (2 * maxlen + 2) * 4 < 2**31 else np.int64

    # F[i][j] = D[i][j] - C_i - P_j; F[i][j] = min(F[i-1][j], F[i][j-1], F[i-1][j-1] + w[s_i][t_j])
    # with w = sub - ins[t_j] - del[s_i], F[i][0] = F[0][j] = 0.
    base = sub - ins[None, :] - dele[:, None]
    cumdel = np.cumsum(dele)
    out = []
    total = 0
    add = np.add
    minimum = np.minimum
    macc = np.minimum.accumulate
    cache = {}
    for k in range(p):
        s = pairs[2 * k]
        t = pairs[2 * k + 1]
        key = (s, t)
        r = cache.get(key)
        if r is None:
            sa = lut[np.frombuffer(s, dtype=np.uint8)]
            ta = lut[np.frombuffer(t, dtype=np.uint8)]
            m = len(ta)
            W = np.ascontiguousarray(base[:, ta].astype(dt))
            rows = [W[c] for c in range(a)]
            row = np.zeros(m + 1, dtype=dt)
            tmp = np.empty(m, dtype=dt)
            head = row[:-1]
            tail = row[1:]
            for c in sa.tolist():
                add(head, rows[c], out=tmp)
                minimum(tmp, tail, out=tmp)
                macc(tmp, out=tail)
            cs = int(dele[sa].sum())
            ps = int(ins[ta].sum())
            r = int(row[m]) + cs + ps
            cache[key] = r
        out.append(r)
        total += r
    out.append("total %d" % total)
    sys.stdout.buffer.write(("\n".join(map(str, out)) + "\n").encode())


main()
