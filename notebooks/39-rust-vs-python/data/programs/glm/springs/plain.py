import sys


def main():
    data = open(sys.argv[1], "rb").read().split()
    n = int(data[0])
    steps = int(data[1])
    dt = float(data[2])
    p = float(data[3])
    vals = list(map(float, data[4:4 + 6 * n]))
    x = vals[0::6]
    v = vals[1::6]
    m = vals[2::6]
    k = vals[3::6]
    r = vals[4::6]
    c = vals[5::6]

    # per-mass coefficients: v = v*wb + a*(f[i]-f[i-1])
    a = [dt / mi for mi in m]
    wb = [1.0 - dt * ci / mi for mi, ci in zip(m, c)]

    zip_ = zip
    range_ = range
    kn = k[-1]
    rn = r[-1]
    kx = k  # local aliases

    for _ in range_(steps):
        xs = x[1:]
        xs.append(x[0] + p)
        nx = []
        nv = []
        apx = nx.append
        apv = nv.append
        # f[i-1] for i = 0 is f[N-1], the wrapping spring
        fm = kn * ((x[0] + p) - x[-1] - rn)
        for x0, x1, ri, ki, vi, wi, ai in zip_(x, xs, r, kx, v, wb, a):
            f = ki * (x1 - x0 - ri)
            vn = vi * wi + ai * (f - fm)
            fm = f
            apv(vn)
            apx(x0 + dt * vn)
        x = nx
        v = nv

    kinetic = 0.0
    position = 0.0
    best = -1.0
    fastest = 0
    for i, (vi, xi, mi) in enumerate(zip(v, x, m)):
        kinetic += (0.5 * mi) * vi * vi
        position += xi
        av = abs(vi)
        if av > best:
            best = av
            fastest = i

    # stretches from the final positions (also covers steps == 0)
    xs = x[1:]
    xs.append(x[0] + p)
    potential = 0.0
    for ki, x0, x1, ri in zip(k, x, xs, r):
        si = x1 - x0 - ri
        potential += (0.5 * ki) * si * si

    sys.stdout.write(
        f"kinetic {kinetic:.16e}\n"
        f"potential {potential:.16e}\n"
        f"position {position:.16e}\n"
        f"fastest {fastest}\n"
    )


main()
