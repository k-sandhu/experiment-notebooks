import sys
import numpy as np


def main():
    with open(sys.argv[1], "rb") as file:
        header = file.readline().split()
        n = int(header[0])
        steps = int(header[1])
        dt = float(header[2])
        circumference = float(header[3])
        data = np.fromiter(
            map(float, file.read().split()),
            dtype=np.float64,
            count=6 * n,
        ).reshape(n, 6).T.copy()

    positions = np.empty(n + 1, dtype=np.float64)
    x = positions[:-1]
    next_x = positions[1:]
    x[:] = data[0]
    v, mass, stiffness, rest, damping = data[1:]

    forces = np.empty(n + 1, dtype=np.float64)
    spring_force = forces[1:]
    previous_force = forces[:-1]
    acceleration = np.empty(n, dtype=np.float64)
    temporary = np.empty(n, dtype=np.float64)

    add = np.add
    subtract = np.subtract
    multiply = np.multiply
    divide = np.divide

    for _ in range(steps):
        positions[n] = positions[0] + circumference
        subtract(next_x, x, out=spring_force)
        subtract(spring_force, rest, out=spring_force)
        multiply(stiffness, spring_force, out=spring_force)

        forces[0] = forces[n]
        subtract(spring_force, previous_force, out=acceleration)
        multiply(damping, v, out=temporary)
        subtract(acceleration, temporary, out=acceleration)
        divide(acceleration, mass, out=acceleration)
        multiply(acceleration, dt, out=acceleration)
        add(v, acceleration, out=v)

        multiply(v, dt, out=temporary)
        add(x, temporary, out=x)

    kinetic = np.sum(((0.5 * mass) * v) * v)

    positions[n] = positions[0] + circumference
    subtract(next_x, x, out=spring_force)
    subtract(spring_force, rest, out=spring_force)
    potential = np.sum(
        ((0.5 * stiffness) * spring_force) * spring_force
    )

    position = np.sum(x)
    fastest = int(np.argmax(np.abs(v)))

    sys.stdout.write(
        f"kinetic {kinetic:.16e}\n"
        f"potential {potential:.16e}\n"
        f"position {position:.16e}\n"
        f"fastest {fastest}\n"
    )


if __name__ == "__main__":
    main()
