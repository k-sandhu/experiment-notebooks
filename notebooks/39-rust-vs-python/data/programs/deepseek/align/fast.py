import sys

import numpy as np


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

    ins_a = np.array([int(x) for x in toks[p:p + A]], dtype=np.int32)
    p += A
    del_a = np.array([int(x) for x in toks[p:p + A]], dtype=np.int32)
    p += A
    sub_flat = [int(x) for x in toks[p:p + A * A]]
    sub_a = np.array(sub_flat, dtype=np.int32).reshape(A, A)
    p += A * A
    P = int(toks[p])
    p += 1

    sub_T = np.ascontiguousarray(sub_a.T)

    # DP in the "shifted" representation:
    #   H_o[j] = D[o][j] - prefix_icost[j]
    # where o indexes the outer string and j the vector (inner) dimension.
    # Then per outer letter with cost oc and sub row cs[j] = sub - icost[j]:
    #   base[0] = H[0] + oc
    #   base[j] = min(H[j] + oc, H[j-1] + cs[j-1])   (j >= 1)
    #   H' = cumulative_min(base)
    # and the final answer is H'[last] + sum(icost).

    out = []
    total = 0
    for _ in range(P):
        sb = toks[p].translate(tbl)
        tb = toks[p + 1].translate(tbl)
        p += 2
        n = len(sb)
        m = len(tb)

        if n <= m:
            s_idx = np.frombuffer(sb, dtype=np.uint8).astype(np.intp)
            t_idx = np.frombuffer(tb, dtype=np.uint8).astype(np.intp)
            outer = sb
            inner_idx = t_idx
            icost_pos = ins_a[t_idx]
            submat = sub_a
        else:
            s_idx = np.frombuffer(sb, dtype=np.uint8).astype(np.intp)
            t_idx = np.frombuffer(tb, dtype=np.uint8).astype(np.intp)
            outer = tb
            inner_idx = s_idx
            icost_pos = del_a[s_idx]
            submat = sub_T

        olen = len(outer)
        vlen = len(inner_idx) + 1
        ic_total = int(icost_pos.sum())

        # cs for every outer letter at once
        CS = submat[:, inner_idx] - icost_pos[None, :]

        H = np.zeros(vlen, dtype=np.int32)
        Hn = np.empty(vlen, dtype=np.int32)

        ocost = del_a if submat is sub_a else ins_a
        for o in outer:
            cs = CS[o]
            oc = int(ocost[o])
            Hn[0] = H[0] + oc
            np.minimum(H[:-1] + cs, H[1:] + oc, out=Hn[1:])
            np.minimum.accumulate(Hn, out=Hn)
            H = Hn
            Hn = np.empty(vlen, dtype=np.int32)

        cost = int(H[vlen - 1]) + ic_total
        out.append(str(cost))
        total += cost

    out.append("total " + str(total))
    sys.stdout.buffer.write(("\n".join(out) + "\n").encode())


main()
