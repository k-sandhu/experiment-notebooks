import sys

import numpy as np


def main():
    data = open(sys.argv[1], "rb").read().split()
    n = int(data[0])
    steps = int(data[1])
    dt = float(data[2])
    p = float(data[3])
    vals = np.array(data[4:4 + 6 * n], dtype=np.float64).reshape(n, 6)
    x = np.ascontiguousarray(vals[:, 0])
    v = np.ascontiguousarray(vals[:, 1])
    m = np.ascontiguousarray(vals[:, 2])
    k = np.ascontiguousarray(vals[:, 3])
    r = np.ascontiguousarray(vals[:, 4])
    c = np.ascontiguousarray(vals[:, 5])

    a = dt / m                 # dt/m
    wb = 1.0 - dt * c / m      # 1 - dt*c/m

    # preallocated scratch buffers
    s = np.empty(n)
    f = np.empty(n)
    d = np.empty(n)
    tmp = np.empty(n)
    s_body = s[:-1]
    x_body = x[:-1]
    x_shift = x[1:]
    f_body = f[1:]
    f_prev = f[:-1]

    for _ in range(steps):
        # stretches from the old positions
        np.subtract(x_shift, x_body, out=s_body)
        s_body -= r[:-1]
        s[-1] = x[0] + p - x[-1] - r[-1]
        # spring forces and their differences
        np.multiply(k, s, out=f)
        d[0] = f[0] - f[-1]
        np.subtract(f_body, f_prev, out=d[1:])
        # v = v*wb + a*d ; x += dt*v
        np.multiply(a, d, out=tmp)
        np.multiply(v, wb, out=v)
        v += tmp
        np.multiply(v, dt, out=tmp)
        x += tmp

    # stretches from the final positions (also covers steps == 0)
    np.subtract(x_shift, x_body, out=s_body)
    s_body -= r[:-1]
    s[-1] = x[0] + p - x[-1] - r[-1]

    kinetic = float(np.sum((0.5 * m) * v * v))
    potential = float(np.sum((0.5 * k) * s * s))
    position = float(np.sum(x))
    fastest = int(np.argmax(np.abs(v)))

    out = (
        f"kinetic {kinetic:.16e}\n"
        f"potential {potential:.16e}\n"
        f"position {position:.16e}\n"
        f"fastest {fastest}\n"
    )
    sys.stdout.write(out)


main()
