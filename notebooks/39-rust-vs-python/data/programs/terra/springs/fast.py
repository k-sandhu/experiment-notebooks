import sys
import numpy as np


def main():
    with open(sys.argv[1], 'rb') as file:
        tokens = file.read().split()
    n, steps = int(tokens[0]), int(tokens[1])
    dt, p = float(tokens[2]), float(tokens[3])
    values = np.array(list(map(float, tokens[4:])), dtype=np.float64).reshape(n, 6)
    x, v, m, k, r, c = (values[:, i].copy() for i in range(6))
    f = np.empty(n)
    work = np.empty(n)
    damping = np.empty(n)
    sub, mul, div, add = np.subtract, np.multiply, np.divide, np.add
    for _ in range(steps):
        sub(x[1:], x[:-1], out=f[:-1])
        sub(f[:-1], r[:-1], out=f[:-1])
        f[-1] = ((x[0] + p) - x[-1]) - r[-1]
        mul(f, k, out=f)
        sub(f[1:], f[:-1], out=work[1:])
        work[0] = f[0] - f[-1]
        mul(c, v, out=damping)
        sub(work, damping, out=work)
        div(work, m, out=work)
        mul(work, dt, out=work)
        add(v, work, out=v)
        mul(v, dt, out=work)
        add(x, work, out=x)
    kinetic = np.sum(((0.5 * m) * v) * v)
    sub(x[1:], x[:-1], out=f[:-1])
    sub(f[:-1], r[:-1], out=f[:-1])
    f[-1] = ((x[0] + p) - x[-1]) - r[-1]
    potential = np.sum(((0.5 * k) * f) * f)
    position = np.sum(x)
    fastest = int(np.argmax(np.abs(v)))
    print(f'kinetic {kinetic:.15e}\npotential {potential:.15e}\nposition {position:.15e}\nfastest {fastest}')


if __name__ == '__main__':
    main()
