"""Plain-Python (standard library only) ring-spring simulator."""

import sys
from itertools import chain
from math import fsum


def main() -> None:
    path = sys.argv[1]
    with open(path, "r", encoding="utf-8") as fh:
        tokens = fh.read().split()

    n = int(tokens[0])
    steps = int(tokens[1])
    dt = float(tokens[2])
    p = float(tokens[3])

    x = [0.0] * n
    v = [0.0] * n
    m = [0.0] * n
    k = [0.0] * n
    r = [0.0] * n
    c = [0.0] * n

    base = 4
    for i in range(n):
        o = base + 6 * i
        x[i] = float(tokens[o])
        v[i] = float(tokens[o + 1])
        m[i] = float(tokens[o + 2])
        k[i] = float(tokens[o + 3])
        r[i] = float(tokens[o + 4])
        c[i] = float(tokens[o + 5])

    last = n - 1
    z = zip
    ch = chain

    for _ in range(steps):
        # Spring forces from the old positions:
        # f[i] = k[i] * ((x[i+1] - x[i]) - r[i]); the last spring wraps with P.
        x1 = x[1:]
        f = [ki * (((b - a) - ri)) for ki, a, b, ri in z(k, x, x1, r)]
        f.append(k[last] * ((((x[0] + p) - x[last]) - r[last])))

        # Force on each mass with f[-1] = f[n-1], then update velocity
        # and position using the new velocity.
        fprev = ch([f[last]], f[:-1])
        v = [
            vi + dt * (((fi - fm1) - (ci * vi)) / mi)
            for fi, fm1, ci, vi, mi in z(f, fprev, c, v, m)
        ]
        x = [xi + dt * vi for xi, vi in z(x, v)]

    # Final stretches (from the final positions) for the potential energy.
    s = [((b - a) - ri) for a, b, ri in z(x, x[1:], r)]
    s.append(((x[0] + p) - x[last]) - r[last])

    kinetic = fsum((((0.5 * mi) * vi) * vi) for mi, vi in z(m, v))
    potential = fsum((((0.5 * ki) * si) * si) for ki, si in z(k, s))
    position = fsum(x)

    j = 0
    best = abs(v[0])
    for i in range(1, n):
        ai = abs(v[i])
        if ai > best:
            best = ai
            j = i

    sys.stdout.write(
        f"kinetic {kinetic:.12e}\n"
        f"potential {potential:.12e}\n"
        f"position {position:.12e}\n"
        f"fastest {j}\n"
    )


main()
