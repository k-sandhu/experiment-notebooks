import sys
import numpy as np


def main():
    with open(sys.argv[1]) as fh:
        tok = fh.read().split()
    n = int(tok[0])
    steps = int(tok[1])
    dt = float(tok[2])
    P = float(tok[3])
    a = np.array(list(map(float, tok[4:4 + 6 * n])), dtype=np.float64).reshape(n, 6)
    xe = np.empty(n + 1)
    xe[:n] = a[:, 0]
    x = xe[:n]
    v = a[:, 1].copy()
    m = a[:, 2].copy()
    k = a[:, 3].copy()
    r = a[:, 4].copy()
    c = a[:, 5].copy()
    fe = np.zeros(n + 1)
    s = np.empty(n)
    F = np.empty(n)
    t = np.empty(n)
    xa, xb = xe[1:], xe[:n]
    fa, fb = fe[1:], fe[:n]
    sub, mul, div, add = np.subtract, np.multiply, np.divide, np.add
    for _ in range(steps):
        xe[n] = xe[0] + P
        sub(xa, xb, out=s)
        sub(s, r, out=s)
        mul(s, k, out=fa)
        fe[0] = fe[n]
        sub(fa, fb, out=F)
        mul(c, v, out=t)
        sub(F, t, out=F)
        div(F, m, out=F)
        mul(F, dt, out=F)
        add(v, F, out=v)
        mul(v, dt, out=t)
        add(x, t, out=x)
    xe[n] = xe[0] + P
    s = (xe[1:] - xe[:n]) - r
    ke = float(np.sum(((0.5 * m) * v) * v))
    pe = float(np.sum(((0.5 * k) * s) * s))
    xs = float(np.sum(x))
    j = int(np.argmax(np.abs(v)))
    print(f"kinetic {ke:.12e}\npotential {pe:.12e}\nposition {xs:.12e}\nfastest {j}")


main()
