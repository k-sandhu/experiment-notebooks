import sys
import numpy as np


def main():
    with open(sys.argv[1], "rb") as source:
        header = source.readline().split()
        n = int(header[0])
        steps = int(header[1])
        dt = float(header[2])
        circumference = float(header[3])
        data = np.array(
            list(map(float, source.read().split())), dtype=np.float64
        ).reshape(n, 6).T.copy()

    initial_x, v, m, k, r, c = data

    positions = np.empty(n + 1, dtype=np.float64)
    x = positions[:-1]
    next_x = positions[1:]
    x[:] = initial_x

    forces = np.empty(n + 1, dtype=np.float64)
    spring_force = forces[1:]
    previous_force = forces[:-1]

    work = np.empty(n, dtype=np.float64)
    damping = np.empty(n, dtype=np.float64)

    subtract = np.subtract
    multiply = np.multiply
    divide = np.divide
    add = np.add

    for _ in range(steps):
        positions[n] = positions[0] + circumference
        subtract(next_x, x, out=spring_force)
        subtract(spring_force, r, out=spring_force)
        multiply(k, spring_force, out=spring_force)

        forces[0] = forces[n]
        subtract(spring_force, previous_force, out=work)
        multiply(c, v, out=damping)
        subtract(work, damping, out=work)
        divide(work, m, out=work)
        multiply(dt, work, out=work)
        add(v, work, out=v)

        multiply(dt, v, out=work)
        add(x, work, out=x)

    multiply(0.5, m, out=work)
    multiply(work, v, out=work)
    multiply(work, v, out=work)
    kinetic = float(work.sum())

    positions[n] = positions[0] + circumference
    subtract(next_x, x, out=spring_force)
    subtract(spring_force, r, out=spring_force)

    multiply(0.5, k, out=work)
    multiply(work, spring_force, out=work)
    multiply(work, spring_force, out=work)
    potential = float(work.sum())

    position = float(x.sum())
    fastest = int(np.argmax(np.abs(v)))

    sys.stdout.write(
        f"kinetic {kinetic:.16e}\n"
        f"potential {potential:.16e}\n"
        f"position {position:.16e}\n"
        f"fastest {fastest}\n"
    )


if __name__ == "__main__":
    main()
