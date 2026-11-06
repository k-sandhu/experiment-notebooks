import sys
from itertools import islice

import numpy as np


def main() -> None:
    path = sys.argv[1]
    with open(path, "rb") as f:
        data = f.read()
    toks = data.split()
    if not toks:
        return
    alphabet = toks[0]
    A = len(alphabet)
    pos = 1
    n_ints = 2 * A + A * A + 1
    nums = list(map(int, islice(toks, pos, pos + n_ints)))
    pos += n_ints
    ins0 = np.array(nums[0:A], dtype=np.int32)
    del0 = np.array(nums[A:2 * A], dtype=np.int32)
    sub0 = np.array(nums[2 * A:2 * A + A * A], dtype=np.int32).reshape(A, A)
    P = nums[-1]

    trans = bytearray(range(256))
    for i, ch in enumerate(alphabet):
        trans[ch] = i
    table = bytes(trans)

    out_lines = []
    total = 0

    for _ in range(P):
        s_tok = toks[pos]
        t_tok = toks[pos + 1]
        pos += 2
        if s_tok == t_tok:
            out_lines.append("0")
            continue
        s = np.frombuffer(s_tok.translate(table), dtype=np.uint8).copy()
        t = np.frombuffer(t_tok.translate(table), dtype=np.uint8).copy()
        # Shorter string as rows (fewer, longer vectorised rows);
        # transpose costs if swapped.
        if len(s) > len(t):
            ins_c = del0
            del_c = ins0
            sub = np.ascontiguousarray(sub0.T)
            s, t = t, s
        else:
            ins_c = ins0
            del_c = del0
            sub = sub0

        n = len(s)
        m = len(t)
        # Pc[j] = cost of inserting t[:j], shape (m+1,)
        Pc = np.empty(m + 1, dtype=np.int32)
        Pc[0] = 0
        np.cumsum(ins_c[t], out=Pc[1:])
        Pc1 = Pc[1:]
        # sub-vector for every possible source letter: shape (A, m)
        subv_all = sub[:, t]

        prev = Pc.copy()
        cur = np.empty(m + 1, dtype=np.int32)
        buf = np.empty(m, dtype=np.int32)
        buf2 = np.empty(m, dtype=np.int32)

        del_list = del_c  # numpy array; scalar index below
        for i in range(n):
            si = int(s[i])
            d = del_c[si]
            cur0 = prev[0] + d
            cur[0] = cur0
            # A_j = min(prev[j+1] + d, prev[j] + sub[si][t_j])
            np.add(prev[1:], d, out=buf)
            np.add(prev[:-1], subv_all[si], out=buf2)
            np.minimum(buf, buf2, out=buf)
            # Row recurrence D_j = min(A_j, D_{j-1} + ins_j) unrolls to
            # D_j = Pc[j] + min(cur0, min_{k<j} (A_k - Pc[k+1])),
            # i.e. a cumulative minimum, computable in vectorised C.
            np.subtract(buf, Pc1, out=buf)
            np.minimum.accumulate(buf, out=buf)
            np.minimum(buf, cur0, out=buf)
            np.add(buf, Pc1, out=cur[1:])
            prev, cur = cur, prev
        cost = int(prev[m])
        total += cost
        out_lines.append(str(cost))

    out_lines.append(f"total {total}")
    sys.stdout.write("\n".join(out_lines) + "\n")


if __name__ == "__main__":
    main()
