import sys

import numpy as np


def main():
    with open(sys.argv[1], "r") as fh:
        text = fh.read()
    toks = text.split()
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
    data = np.array(toks[4:4 + 6 * n], dtype=np.float64).reshape(n, 6)
    x = data[:, 0].copy()
    v0 = data[:, 1].copy()
    m = data[:, 2]
    k = data[:, 3].copy()
    r = data[:, 4].copy()
    c = data[:, 5]

    half_m = 0.5 * m
    half_k = 0.5 * k

    if steps == 0 or dt == 0.0:
        v = v0
    else:
        a_dt = dt / m            # dt/m
        b = 1.0 - a_dt * c       # 1 - (dt/m)*c
        a2 = dt * a_dt           # dt^2/m, for u = dt*v
        u = dt * v0
        nm1 = n - 1
        s = np.empty(n, dtype=np.float64)
        d = np.empty(n, dtype=np.float64)
        # Pre-made views (reused every step).
        s_head = s[:nm1]
        x_head = x[:nm1]
        x_tail = x[1:]
        r_head = r[:nm1]
        s_tail = s[1:]
        s_prev = s[:nm1]
        d_tail = d[1:]
        r_last = r[nm1]
        for _ in range(steps):
            np.subtract(x_tail, x_head, out=s_head)
            s_head -= r_head
            s[nm1] = ((x[0] + period) - x[nm1]) - r_last
            s *= k
            np.subtract(s_tail, s_prev, out=d_tail)
            d[0] = s[0] - s[nm1]
            d *= a2
            u *= b
            u += d
            x += u
        v = u / dt

    kinetic = float(np.dot(half_m, v * v))

    # Final stretch for potential energy.
    s = np.empty(n, dtype=np.float64)
    if n > 1:
        np.subtract(x[1:], x[:n - 1], out=s[:n - 1])
        s[:n - 1] -= r[:n - 1]
    s[n - 1] = ((x[0] + period) - x[n - 1]) - r[n - 1]
    potential = float(np.dot(half_k, s * s))
    pos_sum = float(np.sum(x))
    fastest = int(np.argmax(np.abs(v))) if n else 0

    sys.stdout.write(
        f"kinetic {kinetic:.12e}\npotential {potential:.12e}\n"
        f"position {pos_sum:.12e}\nfastest {fastest}\n"
    )


if __name__ == "__main__":
    main()
