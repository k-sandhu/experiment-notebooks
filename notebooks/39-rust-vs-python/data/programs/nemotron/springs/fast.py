"""NumPy-accelerated ring-spring simulator (standard library + NumPy)."""

import sys

import numpy as np


def main() -> None:
    path = sys.argv[1]
    with open(path, "r", encoding="utf-8") as fh:
        header = fh.readline().split()
        data = np.loadtxt(fh, dtype=np.float64)
    if data.ndim == 1:
        data = data.reshape(1, -1)
    n = int(header[0])
    steps = int(header[1])
    dt = float(header[2])
    p = float(header[3])
    x = data[:, 0].copy()
    v = data[:, 1].copy()
    m = data[:, 2]
    k = data[:, 3]
    r = data[:, 4]
    c = data[:, 5]

    last = n - 1
    s = np.empty(n, dtype=np.float64)
    f = np.empty(n, dtype=np.float64)
    fprev = np.empty(n, dtype=np.float64)
    force = np.empty(n, dtype=np.float64)
    tmp = np.empty(n, dtype=np.float64)
    dv = np.empty(n, dtype=np.float64)

    for _ in range(steps):
        # Stretches and spring forces from the old positions.
        np.subtract(x[1:], x[:-1], out=s[:last])
        s[:last] -= r[:last]
        s[last] = (x[0] + p) - x[last] - r[last]
        np.multiply(k, s, out=f)

        # Force on each mass: F[i] = (f[i] - f[i-1]) - c[i] * v[i],
        # where f[-1] means f[n-1].
        fprev[0] = f[last]
        np.copyto(fprev[1:], f[:-1])
        np.subtract(f, fprev, out=force)
        np.multiply(c, v, out=tmp)
        force -= tmp
        np.divide(force, m, out=force)
        force *= dt
        v += force
        np.multiply(dt, v, out=dv)
        x += dv

    # Final stretches (from the final positions) for the potential energy.
    np.subtract(x[1:], x[:-1], out=s[:last])
    s[:last] -= r[:last]
    s[last] = (x[0] + p) - x[last] - r[last]

    kinetic = float(np.sum((((0.5 * m) * v) * v)))
    potential = float(np.sum((((0.5 * k) * s) * s)))
    position = float(np.sum(x))

    j = int(np.argmax(np.abs(v)))  # first index on a tie

    sys.stdout.write(
        f"kinetic {kinetic:.12e}\n"
        f"potential {potential:.12e}\n"
        f"position {position:.12e}\n"
        f"fastest {j}\n"
    )


main()
