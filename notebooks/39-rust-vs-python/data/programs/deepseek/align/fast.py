import sys

import numpy as np


def main():
    with open(sys.argv[1], 'rb') as f:
        data = f.read()
    toks = data.split()
    alpha = toks[0]
    a_count = len(alpha)

    lut = bytearray(256)
    for i in range(a_count):
        lut[alpha[i]] = i
    lut = bytes(lut)

    p = 1
    ins = np.array([int(x) for x in toks[p:p + a_count]], dtype=np.int32)
    p += a_count
    dele = np.array([int(x) for x in toks[p:p + a_count]], dtype=np.int32)
    p += a_count
    sub = np.array([int(x) for x in toks[p:p + a_count * a_count]],
                   dtype=np.int32).reshape(a_count, a_count)
    p += a_count * a_count
    pairs = int(toks[p])
    p += 1

    sub_t = sub.T.copy()

    res = []
    total = 0

    for _ in range(pairs):
        s = toks[p]
        t = toks[p + 1]
        p += 2

        # The cost is symmetric; put the shorter string on the (serial) row
        # axis and vectorise over the longer one.
        if len(s) > len(t):
            rows = t.translate(lut)
            cols = np.frombuffer(s.translate(lut), dtype=np.uint8)
            ins_e = dele
            del_e = ins
            sub_e = sub_t
        else:
            rows = s.translate(lut)
            cols = np.frombuffer(t.translate(lut), dtype=np.uint8)
            ins_e = ins
            del_e = dele
            sub_e = sub

        m = cols.size

        # R-space: R[i][j] = D[i][j] - I[j] - J[i], where I and J are the
        # prefix sums of the insertion costs of t and the deletion costs of s.
        # Both prefix sums cancel out of the recurrence, leaving
        #   R'[j] = min(R'[j-1], R[j], R[j-1] + sub[s_i][t_j] - ins[t_j] - del[s_i])
        # so a whole row is one elementwise minimum plus one prefix minimum,
        # both done by NumPy at C speed.  R[0] stays 0 for every row.
        insv = ins_e[cols]
        ins_total = int(insv.sum(dtype=np.int64))
        del_l = del_e.tolist()

        v = np.empty((a_count, m), dtype=np.int32)
        np.subtract(sub_e[:, cols], insv, out=v)
        v -= del_e[:, None]

        q = np.zeros(m + 1, dtype=np.int32)
        f = np.empty(m + 1, dtype=np.int32)
        f[0] = 0
        tot = ins_total
        for a in rows:
            tot += del_l[a]
            np.minimum(q[1:], q[:-1] + v[a], out=f[1:])
            np.minimum.accumulate(f, out=q)

        ans = int(q[m]) + tot
        total += ans
        res.append(str(ans))

    res.append('total ' + str(total))
    sys.stdout.buffer.write(('\n'.join(res) + '\n').encode())


main()
