"""Ring of N masses and N springs, simulated with plain Python lists (see SPEC.md).

Each time step is three list comprehensions over the masses. The expressions keep the
operation order of SPEC.md, so the results match the other versions.
"""
import math
import sys
from itertools import chain


def main():
    with open(sys.argv[1]) as handle:
        tokens = handle.read().split()
    n, steps = int(tokens[0]), int(tokens[1])
    dt, p = float(tokens[2]), float(tokens[3])
    values = list(map(float, tokens[4:4 + 6 * n]))
    x = values[0::6]
    v = values[1::6]
    m = values[2::6]
    k = values[3::6]
    r = values[4::6]
    c = values[5::6]

    for _ in range(steps):
        # Steps 1 and 2: spring forces from the old positions. Spring n-1 ends at x[0] + p.
        f = [ki * ((xn - xi) - ri)
             for xi, xn, ki, ri in zip(x, chain(x[1:], (x[0] + p,)), k, r)]
        # Steps 3 and 4: force on each mass (f[-1] is f[n-1]), then the new velocity.
        v = [vi + dt * (((fi - fp) - ci * vi) / mi)
             for vi, fi, fp, ci, mi in zip(v, f, chain(f[-1:], f), c, m)]
        # Step 5: new positions from the new velocities.
        x = [xi + dt * vi for xi, vi in zip(x, v)]

    # Energies use the final state.
    kinetic = math.fsum([0.5 * mi * vi * vi for mi, vi in zip(m, v)])
    s = [(xn - xi) - ri for xi, xn, ri in zip(x, chain(x[1:], (x[0] + p,)), r)]
    potential = math.fsum([0.5 * ki * si * si for ki, si in zip(k, s)])
    position = math.fsum(x)
    fastest = max(range(n), key=lambda i: abs(v[i]))

    print(f"kinetic {kinetic:.12e}")
    print(f"potential {potential:.12e}")
    print(f"position {position:.12e}")
    print(f"fastest {fastest}")


if __name__ == "__main__":
    main()
