import sys


def main():
    with open(sys.argv[1], "rb") as source:
        header = source.readline().split()
        n = int(header[0])
        steps = int(header[1])
        dt = float(header[2])
        period = float(header[3])

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
        x.append(x[0] + period)

        force = [
            ki * ((right - left) - ri)
            for left, right, ki, ri in zip(x, x[1:], k, r)
        ]

        v = [
            vi + dt * (((fi - previous) - (ci * vi)) / mi)
            for vi, fi, previous, ci, mi in zip(
                v, force, force[-1:] + force, c, m
            )
        ]

        x = [xi + dt * vi for xi, vi in zip(x, v)]

    kinetic = sum(
        ((0.5 * mi) * vi) * vi
        for mi, vi in zip(m, v)
    )
    position = sum(x)
    fastest = max(range(n), key=lambda i: abs(v[i]))

    x.append(x[0] + period)
    potential = 0.0
    for i in range(n):
        stretch = (x[i + 1] - x[i]) - r[i]
        potential += ((0.5 * k[i]) * stretch) * stretch

    sys.stdout.write(
        f"kinetic {kinetic:.16e}\n"
        f"potential {potential:.16e}\n"
        f"position {position:.16e}\n"
        f"fastest {fastest}\n"
    )


if __name__ == "__main__":
    main()
