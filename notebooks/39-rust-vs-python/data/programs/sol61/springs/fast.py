"""Vectorized double-precision simulation with reusable NumPy work buffers."""
import os
import sys

# Keep native libraries single-threaded, including initialization at import.
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import numpy as np


def solve(path):
    with open(path, "rb") as source:
        header = source.readline().split()
        n, steps = int(header[0]), int(header[1])
        dt, circumference = float(header[2]), float(header[3])
        # The extra position holds the periodic neighbor of the last mass.
        data = np.empty((6, n + 1), dtype=np.float64)
        for i in range(n):
            # Python's float parser correctly rounds every input decimal.
            data[:, i] = tuple(map(float, source.readline().split()))

    positions = data[0]
    x = positions[:n]
    following = positions[1:]
    v, m, k, rest, damping = data[1:, :n]
    forces = np.empty(n + 1, dtype=np.float64)
    right = forces[1:]
    left = forces[:n]
    delta = np.empty(n, dtype=np.float64)
    temporary = np.empty(n, dtype=np.float64)
    add, subtract, multiply, divide = np.add, np.subtract, np.multiply, np.divide

    for _ in range(steps):
        positions[n] = positions[0] + circumference
        subtract(following, x, out=right)
        subtract(right, rest, out=right)
        multiply(k, right, out=right)
        forces[0] = forces[n]
        subtract(right, left, out=delta)
        multiply(damping, v, out=temporary)
        subtract(delta, temporary, out=delta)
        divide(delta, m, out=delta)
        multiply(dt, delta, out=delta)
        add(v, delta, out=v)
        multiply(dt, v, out=temporary)
        add(x, temporary, out=x)

    positions[n] = positions[0] + circumference
    subtract(following, x, out=right)
    subtract(right, rest, out=right)
    multiply(0.5, m, out=delta)
    multiply(delta, v, out=delta)
    multiply(delta, v, out=delta)
    kinetic = np.sum(delta)
    multiply(0.5, k, out=delta)
    multiply(delta, right, out=delta)
    multiply(delta, right, out=delta)
    potential = np.sum(delta)
    total_position = np.sum(x)
    np.abs(v, out=temporary)
    fastest = int(np.argmax(temporary))
    print(f"kinetic {kinetic:.16e}\npotential {potential:.16e}\n"
          f"position {total_position:.16e}\nfastest {fastest}")


if __name__ == "__main__":
    solve(sys.argv[1])
