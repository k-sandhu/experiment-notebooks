"""Ring of N masses and N springs, simulated with NumPy arrays (see SPEC.md).

Positions live in one buffer with a spare slot at the end that holds the wrapped
neighbour x[0] + P, so every spring stretch is one subtraction of two shifted views.
Spring forces use the same trick. Each step is a fixed sequence of whole-array ufuncs
writing into preallocated buffers, so the loop allocates nothing. Every element keeps
the operation order of SPEC.md, so the results match the other versions.
"""
import math
import sys

import numpy as np


def main():
    with open(sys.argv[1]) as handle:
        tokens = handle.read().split()
    n, steps = int(tokens[0]), int(tokens[1])
    dt, p = float(tokens[2]), float(tokens[3])
    values = np.array(list(map(float, tokens[4:4 + 6 * n]))).reshape(n, 6)
    v = values[:, 1].copy()
    m = values[:, 2].copy()
    k = values[:, 3].copy()
    r = values[:, 4].copy()
    c = values[:, 5].copy()

    xe = np.empty(n + 1)  # xe[n] is the wrapped neighbour of mass n-1
    xe[:n] = values[:, 0]
    x = xe[:n]
    fe = np.empty(n + 1)  # fe[1 + i] is f[i]; fe[0] mirrors f[n-1]
    f = fe[1:]
    force = np.empty(n)
    tmp = np.empty(n)

    for _ in range(steps):
        # Steps 1 and 2: spring forces from the old positions.
        xe[n] = xe[0] + p
        np.subtract(xe[1:], xe[:-1], out=tmp)
        np.subtract(tmp, r, out=tmp)
        np.multiply(k, tmp, out=f)
        fe[0] = fe[n]
        # Steps 3 and 4: force on each mass, then the new velocity.
        np.subtract(f, fe[:-1], out=force)
        np.multiply(c, v, out=tmp)
        np.subtract(force, tmp, out=force)
        np.divide(force, m, out=tmp)
        np.multiply(tmp, dt, out=tmp)
        np.add(v, tmp, out=v)
        # Step 5: new positions from the new velocities.
        np.multiply(v, dt, out=tmp)
        np.add(x, tmp, out=x)

    # Energies use the final state.
    kinetic = math.fsum(((0.5 * m) * v * v).tolist())
    xe[n] = xe[0] + p
    s = (xe[1:] - xe[:-1]) - r
    potential = math.fsum(((0.5 * k) * s * s).tolist())
    position = math.fsum(x.tolist())
    fastest = int(np.argmax(np.abs(v)))

    print(f"kinetic {kinetic:.12e}")
    print(f"potential {potential:.12e}")
    print(f"position {position:.12e}")
    print(f"fastest {fastest}")


if __name__ == "__main__":
    main()
