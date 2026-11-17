import sys

import numpy as np


def main():
    with open(sys.argv[1], "rb") as fh:
        tok = fh.read().split()
    n = int(tok[0])
    steps = int(tok[1])
    dt = float(tok[2])
    p = float(tok[3])
    data = np.array(list(map(float, tok[4:4 + 6 * n])), dtype=np.float64).reshape(n, 6)
    m = np.ascontiguousarray(data[:, 2])
    k = np.ascontiguousarray(data[:, 3])
    r = np.ascontiguousarray(data[:, 4])
    c = np.ascontiguousarray(data[:, 5])
    v = np.ascontiguousarray(data[:, 1])

    # xe[:n] = x, xe[n] = x[0] + P, so spring i stretches xe[i+1] - xe[i].
    xe = np.empty(n + 1)
    xe[:n] = data[:, 0]
    x = xe[:n]
    xa = xe[1:]
    # fe[0] = f[N-1], fe[1:] = f, so F[i] uses fe[i+1] - fe[i].
    fe = np.empty(n + 1)
    f = fe[1:]
    fl = fe[:n]
    tmp = np.empty(n)

    sub = np.subtract
    mul = np.multiply
    div = np.divide
    add = np.add
    for _ in range(steps):
        xe[n] = xe[0] + p
        sub(xa, x, out=f)
        sub(f, r, out=f)
        mul(k, f, out=f)
        fe[0] = fe[n]
        sub(f, fl, out=tmp)
        mul(c, v, out=fl)          # fe[:n] is no longer needed this step
        sub(tmp, fl, out=tmp)
        div(tmp, m, out=tmp)
        mul(tmp, dt, out=tmp)
        add(v, tmp, out=v)
        mul(v, dt, out=tmp)
        add(x, tmp, out=x)

    xe[n] = xe[0] + p
    s = (xa - x) - r
    ke = float(np.sum(((0.5 * m) * v) * v))
    pe = float(np.sum(((0.5 * k) * s) * s))
    xs = float(np.sum(x))
    j = int(np.argmax(np.abs(v)))
    sys.stdout.write(
        f"kinetic {ke:.16e}\npotential {pe:.16e}\nposition {xs:.16e}\nfastest {j}\n"
    )


main()
