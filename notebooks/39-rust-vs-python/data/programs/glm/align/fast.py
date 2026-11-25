import sys
import numpy as np


def main():
    data = open(sys.argv[1], 'rb').read()
    toks = data.split()
    alpha = toks[0]
    a = len(alpha)
    tr = bytes.maketrans(alpha, bytes(range(a)))
    head = 1 + 2 * a + a * a
    nums = list(map(int, toks[1:head]))
    ins = np.array(nums[:a], dtype=np.int32)
    dele = np.array(nums[a:2 * a], dtype=np.int32)
    sub = np.array(nums[2 * a:], dtype=np.int32).reshape(a, a)
    subT = sub.T
    p = int(toks[head])
    pos = head + 1
    ins_l = ins.tolist()
    del_l = dele.tolist()

    out = []
    total = 0
    # preallocated row buffers (row length = longest pair string + 1)
    maxl = max(map(len, toks[head + 1:]), default=0) + 1
    S = np.zeros(maxl, dtype=np.int32)
    X = np.empty(maxl, dtype=np.int32)
    Y = np.empty(maxl, dtype=np.int32)

    for _ in range(p):
        s = toks[pos]
        t = toks[pos + 1]
        pos += 2
        sidx = np.frombuffer(s.translate(tr), dtype=np.uint8)
        tidx = np.frombuffer(t.translate(tr), dtype=np.uint8)
        ini, dli, subm = ins, del_l, sub
        if sidx.size > tidx.size:
            # rows over the shorter string; swapping (s,t) maps ins<->del,
            # sub -> sub^T and leaves the cost unchanged
            sidx, tidx = tidx, sidx
            ini, dli, subm = dele, ins_l, subT
        m = tidx.size
        if sidx.size == 0:
            c = int(ini[tidx].sum())
            total += c
            out.append(str(c))
            continue
        if m == 0:
            c = int(sum(map(dli.__getitem__, sidx.tolist())))
            total += c
            out.append(str(c))
            continue

        ins_t = ini[tidx]
        sci = subm[:, tidx] - ins_t          # (A, m): sub(s_i,t_j) - ins(t_j)
        Sv = S[:m + 1]
        Xv = X[:m]
        Yv = Y[:m]
        Sv[:m + 1] = 0                        # stored row 0: D[0][j] - I_j = 0
        s0 = 0                                # stored row value at j = 0
        for c in sidx.tolist():
            dc = dli[c]
            np.add(Sv[:m], sci[c], out=Xv)     # X_q = S[q-1] + sci_q
            np.minimum.accumulate(Xv, out=Xv)  # running min over q
            np.add(Sv[1:], dc, out=Yv)         # S[q] + del(s_i)
            np.minimum(Xv, Yv, out=Sv[1:])
            s0 += dc
            Sv[0] = s0
        c = int(Sv[m]) + int(ins_t.sum())
        total += c
        out.append(str(c))

    out.append("total %d" % total)
    sys.stdout.buffer.write(("\n".join(out) + "\n").encode())


main()
