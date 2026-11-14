import sys
from gc import disable


def main():
    disable()
    with open(sys.argv[1], "rb") as fh:
        data = fh.read().split()

    n = int(data[0])
    steps = int(data[1])
    dt = float(data[2])
    P = float(data[3])
    vals = list(map(float, data[4:4 + 6 * n]))

    # Original-order constant lists (used for the final report).
    ko = vals[3::6]
    ro = vals[4::6]
    mo = vals[2::6]

    # Working lists are stored in reversed order (index t = n-1-i), so a
    # single pass can carry the previous position and the previous spring
    # force in two local variables.
    x = vals[0::6]
    x.reverse()
    v = vals[1::6]
    v.reverse()
    m = mo[::-1]
    k = ko[::-1]
    r = ro[::-1]
    c = vals[5::6]
    c.reverse()

    kl = k[0]          # spring n-1 (the wrap-around spring)
    rl = r[0]
    k1 = k[1:]         # springs n-2 .. 0
    r1 = r[1:]
    c0 = c[-1]         # mass 0
    m0 = m[-1]

    if any(r):
        for _ in range(steps):
            it = iter(x)
            xp = next(it)                       # x[n-1]
            fp = fl = kl * (((x[-1] + P) - xp) - rl)
            vn = [vq + dt * (((fp - (fp := kj * ((xp - (xp := xj)) - rj))) - cq * vq) / mq)
                  for xj, kj, rj, vq, cq, mq in zip(it, k1, r1, v, c, m)]
            v0 = v[-1]
            vn.append(v0 + dt * (((fp - fl) - c0 * v0) / m0))
            v = vn
            x = [xi + dt * vi for xi, vi in zip(x, v)]
    else:
        # All rest lengths are zero: subtracting 0.0 is an exact identity.
        for _ in range(steps):
            it = iter(x)
            xp = next(it)                       # x[n-1]
            fp = fl = kl * (((x[-1] + P) - xp) - rl)
            vn = [vq + dt * (((fp - (fp := kj * (xp - (xp := xj)))) - cq * vq) / mq)
                  for xj, kj, vq, cq, mq in zip(it, k1, v, c, m)]
            v0 = v[-1]
            vn.append(v0 + dt * (((fp - fl) - c0 * v0) / m0))
            v = vn
            x = [xi + dt * vi for xi, vi in zip(x, v)]

    # Back to original order.
    x.reverse()
    v.reverse()

    K = 0.0
    for mi, vi in zip(mo, v):
        K += ((0.5 * mi) * vi) * vi

    U = 0.0
    xs = x[1:]
    for xi, xn, ki, ri in zip(x, xs, ko, ro):
        s = (xn - xi) - ri
        U += ((0.5 * ki) * s) * s
    s = ((x[0] + P) - x[-1]) - ro[-1]
    U += ((0.5 * ko[-1]) * s) * s

    X = 0.0
    for xi in x:
        X += xi

    J = 0
    best = -1.0
    idx = 0
    for a in map(abs, v):
        if a > best:
            best = a
            J = idx
        idx += 1

    sys.stdout.write(
        f"kinetic {K:.16e}\n"
        f"potential {U:.16e}\n"
        f"position {X:.16e}\n"
        f"fastest {J}\n"
    )
    sys.stdout.flush()


if __name__ == "__main__":
    main()
