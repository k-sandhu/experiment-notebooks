import sys


def main():
    with open(sys.argv[1], "r") as fh:
        data = fh.read().split()
    n = int(data[0])
    steps = int(data[1])
    dt = float(data[2])
    period = float(data[3])
    vals = list(map(float, data[4:4 + 6 * n]))
    x = vals[0::6]
    v = vals[1::6]
    m = vals[2::6]
    k = vals[3::6]
    r = vals[4::6]
    c = vals[5::6]

    if n == 1:
        k0 = k[0]; r0 = r[0]; m0 = m[0]; c0 = c[0]
        x0 = x[0]; v0 = v[0]
        for _ in range(steps):
            f = k0 * (((x0 + period) - x0) - r0)
            force = (f - f) - (c0 * v0)
            v0 = v0 + dt * (force / m0)
            x0 = x0 + dt * v0
        x[0] = x0; v[0] = v0
    elif n > 1:
        # One forward pass per step: f[last] is computed first (it is
        # also f[-1] for mass 0), then at mass i the just-computed f[i]
        # (from still-old x[i], x[i+1]) and f[i-1] are both known, and
        # writing x[i] cannot disturb any f still to be computed.
        # The velocity update v + dt*((f[i]-f[i-1] - c*v)/m) is
        # regrouped as b*v + a*(f[i]-f[i-1]) with a = dt/m and
        # b = 1 - a*c precomputed once; this only reorders rounding
        # (the stretch subtraction is kept exact).
        a = [dt / mi for mi in m]
        b = [1.0 - ai * ci for ai, ci in zip(a, c)]
        last = n - 1
        kl = k[last]; rl = r[last]; al = a[last]; bl = b[last]
        rng = range(last)
        for _ in range(steps):
            f_prev = kl * (((x[0] + period) - x[last]) - rl)
            f_last = f_prev
            for i in rng:
                xi = x[i]
                f = k[i] * ((x[i + 1] - xi) - r[i])
                vi = b[i] * v[i] + a[i] * (f - f_prev)
                v[i] = vi
                x[i] = xi + dt * vi
                f_prev = f
            xl = x[last]
            vl = bl * v[last] + al * (f_last - f_prev)
            v[last] = vl
            x[last] = xl + dt * vl

    kinetic = 0.0
    potential = 0.0
    pos_sum = 0.0
    fastest = 0
    best = -1.0
    for i in range(n):
        vi = v[i]
        kinetic += ((0.5 * m[i]) * vi) * vi
        pos_sum += x[i]
        av = vi if vi >= 0.0 else -vi
        if av > best:
            best = av
            fastest = i
        if i + 1 < n:
            s = (x[i + 1] - x[i]) - r[i]
        else:
            s = ((x[0] + period) - x[i]) - r[i]
        potential += ((0.5 * k[i]) * s) * s

    sys.stdout.write(
        f"kinetic {kinetic:.12e}\n"
        f"potential {potential:.12e}\n"
        f"position {pos_sum:.12e}\n"
        f"fastest {fastest}\n"
    )


if __name__ == "__main__":
    main()
