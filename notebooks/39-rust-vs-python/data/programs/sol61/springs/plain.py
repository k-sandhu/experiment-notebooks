"""Single-pass spring simulation using Python floats and O(N) storage."""
import sys


def solve(path):
    with open(path, "rb") as source:
        header = source.readline().split()
        n, steps = int(header[0]), int(header[1])
        dt, circumference = float(header[2]), float(header[3])
        x, v, m, k, rest, damping = [], [], [], [], [], []
        for _ in range(n):
            xi, vi, mi, ki, ri, ci = map(float, source.readline().split())
            x.append(xi)
            v.append(vi)
            m.append(mi)
            k.append(ki)
            rest.append(ri)
            damping.append(ci)

    last = n - 1
    interior = range(last)
    for _ in range(steps):
        # Save the closing force before changing either end of the ring.
        closing = k[last] * (((x[0] + circumference) - x[last]) - rest[last])
        previous = closing
        xi = x[0]
        for i in interior:
            # The next position is still old; carry it across the in-place update.
            following = x[i + 1]
            force = k[i] * ((following - xi) - rest[i])
            vi = v[i]
            vi = vi + dt * (((force - previous) - damping[i] * vi) / m[i])
            v[i] = vi
            x[i] = xi + dt * vi
            xi = following
            previous = force
        vi = v[last]
        vi = vi + dt * (((closing - previous) - damping[last] * vi) / m[last])
        v[last] = vi
        x[last] = xi + dt * vi

    kinetic = 0.0
    potential = 0.0
    fastest = 0
    speed = -1.0
    for i in interior:
        stretch = (x[i + 1] - x[i]) - rest[i]
        potential += ((0.5 * k[i]) * stretch) * stretch
    stretch = ((x[0] + circumference) - x[last]) - rest[last]
    potential += ((0.5 * k[last]) * stretch) * stretch
    for i in range(n):
        vi = v[i]
        kinetic += ((0.5 * m[i]) * vi) * vi
        magnitude = abs(vi)
        if magnitude > speed:
            speed = magnitude
            fastest = i
    print(f"kinetic {kinetic:.16e}\npotential {potential:.16e}\n"
          f"position {sum(x):.16e}\nfastest {fastest}")


if __name__ == "__main__":
    solve(sys.argv[1])
