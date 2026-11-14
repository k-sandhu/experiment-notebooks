import sys


def main():
    with open(sys.argv[1], "r") as fh:
        toks = fh.read().split()
    if not toks:
        return
    n = int(toks[0])
    steps = int(toks[1])
    dt = float(toks[2])
    period = float(toks[3])
    if n == 0:
        sys.stdout.write(
            "kinetic 0.000000000000e0\npotential 0.000000000000e0\n"
            "position 0.000000000000e0\nfastest 0\n"
        )
        return
    vals = list(map(float, toks[4:4 + 6 * n]))
    x = vals[0::6]
    v = vals[1::6]
    m = vals[2::6]
    k = vals[3::6]
    r = vals[4::6]
    c = vals[5::6]

    # v_new = b*v + a*(f[i]-f[i-1]); a=dt/m, b=1-a*c
    a = [0.0] * n
    b = [0.0] * n
    for i in range(n):
        ai = dt / m[i]
        a[i] = ai
        b[i] = 1.0 - ai * c[i]
    del c

    if steps and dt != 0.0:
        # Local bindings for the hot loop.
        xx = x
        vv = v
        kk = k
        rr = r
        aa = a
        bb = b
        nm1 = n - 1
        rng = range(nm1)
        k_last = kk[nm1]
        r_last = rr[nm1]
        a_last = aa[nm1]
        b_last = bb[nm1]
        for _ in range(steps):
            x0 = xx[0]
            f_last = k_last * (((x0 + period) - xx[nm1]) - r_last)
            prev = f_last
            xi = x0
            for i in rng:
                xn = xx[i + 1]
                fi = kk[i] * ((xn - xi) - rr[i])
                vi = bb[i] * vv[i] + aa[i] * (fi - prev)
                vv[i] = vi
                xx[i] = xi + dt * vi
                xi = xn
                prev = fi
            vi = b_last * vv[nm1] + a_last * (f_last - prev)
            vv[nm1] = vi
            xx[nm1] = xi + dt * vi

    kinetic = 0.0
    pos_sum = 0.0
    best = -1.0
    fastest = 0
    for i in range(n):
        vi = v[i]
        kinetic += ((0.5 * m[i]) * vi) * vi
        pos_sum += x[i]
        av = vi if vi >= 0.0 else -vi
        if av > best:
            best = av
            fastest = i

    potential = 0.0
    for i in range(n - 1):
        si = (x[i + 1] - x[i]) - r[i]
        potential += ((0.5 * k[i]) * si) * si
    sn = ((x[0] + period) - x[n - 1]) - r[n - 1]
    potential += ((0.5 * k[n - 1]) * sn) * sn

    sys.stdout.write(
        f"kinetic {kinetic:.12e}\npotential {potential:.12e}\n"
        f"position {pos_sum:.12e}\nfastest {fastest}\n"
    )


if __name__ == "__main__":
    main()
