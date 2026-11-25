import sys
import numpy as np


def main():
    with open(sys.argv[1], 'rb') as f:
        data = f.read()
    tok = data.split()
    H = int(tok[0])
    W = int(tok[1])
    S = int(tok[2])
    g = np.frombuffer(b''.join(tok[3:3 + H]), dtype=np.uint8).reshape(H, W)

    Wp = W + 1                 # one shared pad column per row
    N = (H + 2) * Wp           # pad row on top and bottom
    lo = Wp
    hi = (H + 1) * Wp
    n_in = hi - lo

    openg = g == 46

    # Value array (flat, padded). Walls / pads hold 0, sources hold 1000*d.
    A = np.zeros(N, dtype=np.int32)
    A.reshape(H + 2, Wp)[1:H + 1, :W] = np.where(
        g >= 48, (g.astype(np.int32) - 48) * 1000, 0)

    # Wall indicator (pads count as walls).
    wl = np.ones(N, dtype=np.int32)
    wl.reshape(H + 2, Wp)[1:H + 1, :W] = (g == 35)

    coef = wl[0:hi - Wp] + wl[lo + Wp:hi + Wp]
    coef += wl[lo - 1:hi - 1]
    coef += wl[lo + 1:hi + 1]
    coef += 4

    open_p = np.zeros(N, dtype=np.bool_)
    open_p.reshape(H + 2, Wp)[1:H + 1, :W] = openg
    oin = open_p[lo:hi]

    src = A[lo:hi].copy()
    B = A.copy()
    t = np.empty(n_in, dtype=np.int32)

    def views(X):
        return (X[0:hi - Wp], X[lo + Wp:hi + Wp], X[lo - 1:hi - 1],
                X[lo + 1:hi + 1], X[lo:hi])

    cur = views(A)
    nxt = views(B)

    add = np.add
    multiply = np.multiply
    right_shift = np.right_shift
    bitwise_and = np.bitwise_and

    nfix = n_in - int(np.count_nonzero(oin))

    if nfix * 20 <= n_in:
        fidx = np.flatnonzero(~oin)
        fval = src[fidx]
        for _ in range(S):
            up, dn, lf, rt, ce = cur
            out = nxt[4]
            add(up, dn, out=out)
            add(out, lf, out=out)
            add(out, rt, out=out)
            multiply(ce, coef, out=t)
            add(out, t, out=out)
            right_shift(out, 3, out=out)
            out[fidx] = fval
            cur, nxt = nxt, cur
    else:
        mask = -(oin.astype(np.int32))
        for _ in range(S):
            up, dn, lf, rt, ce = cur
            out = nxt[4]
            add(up, dn, out=out)
            add(out, lf, out=out)
            add(out, rt, out=out)
            multiply(ce, coef, out=t)
            add(out, t, out=out)
            right_shift(out, 3, out=out)
            bitwise_and(out, mask, out=out)
            add(out, src, out=out)
            cur, nxt = nxt, cur

    fin = cur[4].reshape(H, Wp)[:, :W]

    vo = np.where(openg, fin, 0).astype(np.int64)
    T = int(vo.sum(dtype=np.int64))

    vm = np.where(openg, fin, -1)
    idx = int(vm.argmax())
    V = int(vm.ravel()[idx])
    R, C = divmod(idx, W)

    weights = np.arange(1, H * W + 1, dtype=np.int64)
    K = int(np.dot(vo.ravel(), weights))

    sys.stdout.write(f"sum {T}\nmax {V} {R} {C}\nchecksum {K}\n")
    sys.stdout.flush()


main()
