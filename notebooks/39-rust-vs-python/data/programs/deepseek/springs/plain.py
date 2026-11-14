import sys


def main():
    with open(sys.argv[1], "rb") as fh:
        tok = fh.read().split()

    n = int(tok[0])
    steps = int(tok[1])
    dt = float(tok[2])
    p = float(tok[3])

    vals = [float(t) for t in tok[4:4 + 6 * n]]
    x = vals[0::6]
    v = vals[1::6]
    m = vals[2::6]
    k = vals[3::6]
    r = vals[4::6]
    c = vals[5::6]

    nm1 = n - 1
    xp = x
    vp = v
    mp = m
    kp = k
    rp = r
    cp = c

    for _ in range(steps):
        # Wrap-around spring force from the positions at the start of the step.
        flast = kp[nm1] * (((xp[0] + p) - xp[nm1]) - rp[nm1])
        fprev = flast
        for i in range(nm1):
            xi = xp[i]
            fi = kp[i] * ((xp[i + 1] - xi) - rp[i])
            vi = vp[i]
            f = (fi - fprev) - cp[i] * vi
            vn = vi + dt * (f / mp[i])
            vp[i] = vn
            xp[i] = xi + dt * vn
            fprev = fi
        vi = vp[nm1]
        f = (flast - fprev) - cp[nm1] * vi
        vn = vi + dt * (f / mp[nm1])
        vp[nm1] = vn
        xp[nm1] = xp[nm1] + dt * vn

    kinetic = 0.0
    for i in range(n):
        kinetic += ((0.5 * mp[i]) * vp[i]) * vp[i]

    potential = 0.0
    for i in range(nm1):
        s = (xp[i + 1] - xp[i]) - rp[i]
        potential += ((0.5 * kp[i]) * s) * s
    s = ((xp[0] + p) - xp[nm1]) - rp[nm1]
    potential += ((0.5 * kp[nm1]) * s) * s

    position = sum(xp)

    fastest = 0
    best = abs(vp[0])
    for i in range(1, n):
        a = abs(vp[i])
        if a > best:
            best = a
            fastest = i

    out = []
    out.append("kinetic %.12e" % kinetic)
    out.append("potential %.12e" % potential)
    out.append("position %.12e" % position)
    out.append("fastest %d" % fastest)
    sys.stdout.write("\n".join(out) + "\n")


main()
