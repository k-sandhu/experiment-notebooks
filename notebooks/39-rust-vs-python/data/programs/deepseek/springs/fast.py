import sys

import numpy as np


def main():
    with open(sys.argv[1], "rb") as fh:
        raw = fh.read()

    vals = np.fromstring(raw.decode("ascii"), sep=" ")
    n = int(vals[0])
    steps = int(vals[1])
    dt = float(vals[2])
    p = float(vals[3])

    data = vals[4:4 + 6 * n].reshape(n, 6)
    x = data[:, 0].copy()
    v = data[:, 1].copy()
    m = data[:, 2].copy()
    k = data[:, 3].copy()
    r = data[:, 4].copy()
    c = data[:, 5].copy()

    nm1 = n - 1

    # Working arrays and views, allocated once.
    f = np.empty(n)
    fprev = np.empty(n)
    F = np.empty(n)
    tmp = np.empty(n)

    x0 = x[:-1]
    x1 = x[1:]
    f0 = f[:-1]
    f0v = f[:-1]
    r0 = r[:-1]
    fp1 = fprev[1:]

    for _ in range(steps):
        # Stretch and force of the non-wrap springs, from the old positions.
        np.subtract(x1, x0, out=f0)
        np.subtract(f0, r0, out=f0)
        # Wrap-around spring.
        f[nm1] = ((x[0] + p) - x[nm1]) - r[nm1]
        np.multiply(f, k, out=f)

        # Shift forces: fprev[i] = f[i-1], fprev[0] = f[n-1].
        fprev[0] = f[nm1]
        np.copyto(fp1, f0v)

        # F = (f[i] - f[i-1]) - c[i]*v[i]
        np.subtract(f, fprev, out=F)
        np.multiply(c, v, out=tmp)
        np.subtract(F, tmp, out=F)
        np.divide(F, m, out=F)
        np.multiply(F, dt, out=F)
        np.add(v, F, out=v)
        # x += dt * new_v
        np.multiply(v, dt, out=tmp)
        np.add(x, tmp, out=x)

    kinetic = float(np.sum(((0.5 * m) * v) * v))

    s = np.empty(n)
    np.subtract(x1, x0, out=s[:-1])
    np.subtract(s[:-1], r0, out=s[:-1])
    s[nm1] = ((x[0] + p) - x[nm1]) - r[nm1]
    potential = float(np.sum(((0.5 * k) * s) * s))

    position = float(np.sum(x))
    fastest = int(np.argmax(np.abs(v)))

    sys.stdout.write(
        "kinetic %.12e\npotential %.12e\nposition %.12e\nfastest %d\n"
        % (kinetic, potential, position, fastest)
    )


main()
