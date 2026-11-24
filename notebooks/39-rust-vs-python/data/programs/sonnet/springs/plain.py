import sys


def main():
    with open(sys.argv[1]) as fh:
        tok = fh.read().split()
    n = int(tok[0])
    steps = int(tok[1])
    dt = float(tok[2])
    P = float(tok[3])
    vals = list(map(float, tok[4:4 + 6 * n]))
    x = vals[0::6]
    v = vals[1::6]
    M = vals[2::6]
    K = vals[3::6]
    R = vals[4::6]
    C = vals[5::6]
    for _ in range(steps):
        x1 = x[1:]
        x1.append(x[0] + P)
        f = [k * ((b - a) - r) for a, b, k, r in zip(x, x1, K, R)]
        fp = [f[-1]]
        fp += f[:-1]
        v = [vi + dt * (((f1 - f0) - c * vi) / m) for vi, f1, f0, c, m in zip(v, f, fp, C, M)]
        x = [a + dt * b for a, b in zip(x, v)]
    ke = 0.0
    pe = 0.0
    xs = 0.0
    best = -1.0
    j = 0
    for i in range(n):
        ke += ((0.5 * M[i]) * v[i]) * v[i]
        if i < n - 1:
            s = (x[i + 1] - x[i]) - R[i]
        else:
            s = ((x[0] + P) - x[n - 1]) - R[n - 1]
        pe += ((0.5 * K[i]) * s) * s
        xs += x[i]
        a = abs(v[i])
        if a > best:
            best = a
            j = i
    print(f"kinetic {ke:.12e}\npotential {pe:.12e}\nposition {xs:.12e}\nfastest {j}")


main()
