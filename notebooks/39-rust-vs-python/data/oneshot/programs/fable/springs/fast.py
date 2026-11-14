import sys
import numpy as np


def main():
    with open(sys.argv[1], "rb") as fh:
        data = fh.read().split()

    N = int(data[0])
    S = int(data[1])
    dt = float(data[2])
    P = float(data[3])

    arr = np.array(list(map(float, data[4:4 + 6 * N])), dtype=np.float64)
    cols = np.ascontiguousarray(arr.reshape(N, 6).T)

    np.seterr(all="ignore")

    # Extended position buffer: xe[N] holds x[0] + P
    xe = np.empty(N + 1, dtype=np.float64)
    xe[:N] = cols[0]
    xe[N] = xe[0] + P
    x = xe[:N]
    x_hi = xe[1:]

    v = cols[1].copy()
    m = cols[2].copy()
    k = cols[3].copy()
    r = cols[4].copy()
    c = cols[5].copy()

    # Extended force buffer: fe[i+1] = f[i], fe[0] = f[N-1]
    fe = np.zeros(N + 1, dtype=np.float64)
    f_hi = fe[1:]
    f_lo = fe[:N]

    s = np.empty(N, dtype=np.float64)
    F = np.empty(N, dtype=np.float64)
    t = np.empty(N, dtype=np.float64)

    sub = np.subtract
    mul = np.multiply
    div = np.divide
    add = np.add

    for _ in range(S):
        xe[N] = xe[0] + P
        sub(x_hi, x, s)
        sub(s, r, s)
        mul(k, s, f_hi)
        fe[0] = fe[N]
        sub(f_hi, f_lo, F)
        mul(c, v, t)
        sub(F, t, F)
        div(F, m, F)
        mul(F, dt, F)
        add(v, F, v)
        mul(v, dt, t)
        add(x, t, x)

    # Final quantities
    xe[N] = xe[0] + P
    sub(x_hi, x, s)
    sub(s, r, s)

    K = float(np.sum(((0.5 * m) * v) * v))
    U = float(np.sum(((0.5 * k) * s) * s))
    X = float(np.sum(x))
    J = int(np.argmax(np.abs(v)))

    sys.stdout.write(
        f"kinetic {K:.16e}\npotential {U:.16e}\nposition {X:.16e}\nfastest {J}\n"
    )


if __name__ == "__main__":
    main()
