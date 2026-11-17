import sys


def main():
    with open(sys.argv[1], "rb") as source:
        header = source.readline().split()
        n = int(header[0])
        steps = int(header[1])
        dt = float(header[2])
        circumference = float(header[3])

        x = []
        v = []
        m = []
        k = []
        r = []
        c = []

        for _ in range(n):
            xi, vi, mi, ki, ri, ci = map(float, source.readline().split())
            x.append(xi)
            v.append(vi)
            m.append(mi)
            k.append(ki)
            r.append(ri)
            c.append(ci)

    for _ in range(steps):
        forces = [
            ki * ((xn - xi) - ri)
            for xi, xn, ki, ri in zip(x, x[1:], k, r)
        ]
        forces.append(k[-1] * (((x[0] + circumference) - x[-1]) - r[-1]))

        v = [
            vi + dt * (((fi - previous) - ci * vi) / mi)
            for vi, fi, previous, ci, mi in zip(
                v, forces, forces[-1:] + forces[:-1], c, m
            )
        ]
        x = [xi + dt * vi for xi, vi in zip(x, v)]

    kinetic = sum(((0.5 * mi) * vi) * vi for mi, vi in zip(m, v))

    potential = 0.0
    for xi, xn, ki, ri in zip(x, x[1:], k, r):
        stretch = (xn - xi) - ri
        potential += ((0.5 * ki) * stretch) * stretch
    stretch = ((x[0] + circumference) - x[-1]) - r[-1]
    potential += ((0.5 * k[-1]) * stretch) * stretch

    fastest = 0
    maximum_speed = abs(v[0])
    for i in range(1, n):
        speed = abs(v[i])
        if speed > maximum_speed:
            maximum_speed = speed
            fastest = i

    sys.stdout.write(
        f"kinetic {kinetic:.16e}\n"
        f"potential {potential:.16e}\n"
        f"position {sum(x):.16e}\n"
        f"fastest {fastest}\n"
    )


if __name__ == "__main__":
    main()
