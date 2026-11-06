import sys

import numpy as np


def main():
    with open(sys.argv[1], "r") as fh:
        data = fh.read().split()
    n = int(data[0])
    steps = int(data[1])
    dt = float(data[2])
    period = float(data[3])
    vals = np.fromiter(map(float, data[4:4 + 6 * n]), dtype=np.float64, count=6 * n)
    # Slicing a flat array gives strided views; copy to contiguous arrays.
    x = np.ascontiguousarray(vals[0::6])
    v = np.ascontiguousarray(vals[1::6])
    m = np.ascontiguousarray(vals[2::6])
    k = np.ascontiguousarray(vals[3::6])
    r = np.ascontiguousarray(vals[4::6])
    c = np.ascontiguousarray(vals[5::6])

    if n == 1:
        x0 = float(x[0]); v0 = float(v[0])
        m0 = float(m[0]); k0 = float(k[0]); r0 = float(r[0]); c0 = float(c[0])
        for _ in range(steps):
            f = k0 * (((x0 + period) - x0) - r0)
            v0 = v0 + dt * (((f - f) - (c0 * v0)) / m0)
            x0 = x0 + dt * v0
        x[0] = x0; v[0] = v0
    elif n > 1:
        # All work is in-place ufunc calls on reused buffers. The
        # velocity update v + dt*(((f[i]-f[i-1]) - c*v)/m) is regrouped
        # as b*v + a*(f[i]-f[i-1]) with a = dt/m and b = 1 - a*c
        # precomputed once, which saves two passes over the arrays per
        # step; the stretch subtraction itself is kept exact.
        a = dt / m
        b = 1.0 - a * c
        s = np.empty(n, dtype=np.float64)
        tmp = np.empty(n, dtype=np.float64)
        for _ in range(steps):
            # s holds f[i] = k[i] * ((x[i+1] - x[i]) - r[i]) when done.
            np.subtract(x[1:], x[:-1], out=s[:-1])
            s[-1] = (x[0] + period) - x[-1]
            s -= r
            s *= k
            # tmp[i] = a[i] * (f[i] - f[i-1])
            np.subtract(s[1:], s[:-1], out=tmp[1:])
            tmp[0] = s[0] - s[-1]
            tmp *= a
            v *= b
            v += tmp
            # x += dt * v
            np.multiply(v, dt, out=tmp)
            x += tmp

    kinetic = float(np.sum((0.5 * m) * v * v)) if n else 0.0
    pos_sum = float(np.sum(x)) if n else 0.0
    if n > 1:
        s = np.empty(n, dtype=np.float64)
        np.subtract(x[1:], x[:-1], out=s[:-1])
        s[:-1] -= r[:-1]
        s[-1] = ((x[0] + period) - x[-1]) - r[-1]
        potential = float(np.sum((0.5 * k) * s * s))
    elif n == 1:
        s0 = ((float(x[0]) + period) - float(x[0])) - float(r[0])
        potential = ((0.5 * float(k[0])) * s0) * s0
    else:
        potential = 0.0
    fastest = int(np.argmax(np.abs(v))) if n else 0

    sys.stdout.write(
        f"kinetic {kinetic:.12e}\n"
        f"potential {potential:.12e}\n"
        f"position {pos_sum:.12e}\n"
        f"fastest {fastest}\n"
    )


if __name__ == "__main__":
    main()
