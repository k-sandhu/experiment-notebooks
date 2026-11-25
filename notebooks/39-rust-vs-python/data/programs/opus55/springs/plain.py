import sys


def main():
    with open(sys.argv[1], "rb") as fh:
        tok = fh.read().split()
    n = int(tok[0])
    steps = int(tok[1])
    dt = float(tok[2])
    P = float(tok[3])
    vals = list(map(float, tok[4:4 + 6 * n]))
    x = vals[0::6]
    v = vals[1::6]
    m = vals[2::6]
    k = vals[3::6]
    r = vals[4::6]
    c = vals[5::6]

    for _ in range(steps):
        # xn[i] is the far end of spring i (mass 0 shifted by P for the last spring).
        xn = x[1:]
        xn.append(x[0] + P)
        f = [ki * ((b - a) - ri) for ki, a, b, ri in zip(k, x, xn, r)]
        # fp[i] = f[i-1], wrapping around.
        fp = [f[-1]]
        fp += f[:-1]
        v = [vi + dt * (((fi - fq) - ci * vi) / mi) for vi, fi, fq, ci, mi in zip(v, f, fp, c, m)]
        x = [xi + dt * vi for xi, vi in zip(x, v)]

    xn = x[1:]
    xn.append(x[0] + P)
    ke = sum([((0.5 * mi) * vi) * vi for mi, vi in zip(m, v)])
    pe = 0.0
    for ki, a, b, ri in zip(k, x, xn, r):
        s = (b - a) - ri
        pe += ((0.5 * ki) * s) * s
    xs = sum(x)
    av = list(map(abs, v))
    j = av.index(max(av))
    sys.stdout.write(
        f"kinetic {ke:.16e}\npotential {pe:.16e}\nposition {xs:.16e}\nfastest {j}\n"
    )


main()
