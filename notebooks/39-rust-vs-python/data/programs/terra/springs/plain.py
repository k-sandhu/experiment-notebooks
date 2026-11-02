import sys


def main():
    with open(sys.argv[1], 'rb') as file:
        tokens = file.read().split()
    n, steps = int(tokens[0]), int(tokens[1])
    dt, p = float(tokens[2]), float(tokens[3])
    values = list(map(float, tokens[4:]))
    x, v, m, k, r, c = (values[i::6] for i in range(6))
    f = [0.0] * n
    last = n - 1
    for _ in range(steps):
        for i in range(last):
            f[i] = k[i] * ((x[i + 1] - x[i]) - r[i])
        f[last] = k[last] * (((x[0] + p) - x[last]) - r[last])
        prev = f[last]
        for i in range(n):
            force = (f[i] - prev) - (c[i] * v[i])
            prev = f[i]
            vi = v[i] + dt * (force / m[i])
            v[i] = vi
            x[i] = x[i] + dt * vi
    kinetic = potential = position = 0.0
    fastest = 0
    for i in range(n):
        kinetic += ((0.5 * m[i]) * v[i]) * v[i]
        stretch = ((x[0] + p) - x[i]) - r[i] if i == last else (x[i + 1] - x[i]) - r[i]
        potential += ((0.5 * k[i]) * stretch) * stretch
        position += x[i]
        if abs(v[i]) > abs(v[fastest]):
            fastest = i
    print(f'kinetic {kinetic:.15e}\npotential {potential:.15e}\nposition {position:.15e}\nfastest {fastest}')


if __name__ == '__main__':
    main()
