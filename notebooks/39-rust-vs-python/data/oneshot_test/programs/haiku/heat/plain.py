import sys


def main():
    with open(sys.argv[1], 'rb') as f:
        data = f.read().split()
    H = int(data[0])
    W = int(data[1])
    S = int(data[2])
    rows = data[3:3 + H]

    # Each cell is a 17-bit field in one big integer. Values never exceed 9000,
    # and the neighbour sum is at most 8 * 9000 = 72000 < 2**17, so fields never carry.
    B = 17
    stride = W + 2
    NF = (H + 2) * stride

    kind = bytearray(NF)  # 0 = wall/outside, 1 = open '.', 2 = source
    srcval = []
    open_idx = []
    for r in range(H):
        row = rows[r]
        base = (r + 1) * stride + 1
        for c in range(W):
            ch = row[c]
            if ch == 46:  # '.'
                kind[base + c] = 1
                open_idx.append(base + c)
            elif ch != 35:  # not '#': a digit source
                kind[base + c] = 2
                srcval.append((base + c, 1000 * (ch - 48)))

    ZERO = '0' * B
    ONE = '1' * B
    ONE14 = '000' + '1' * 14  # keeps the low 14 bits after >>3

    pMO = [ZERO] * NF
    pU = [ZERO] * NF
    pD = [ZERO] * NF
    pL = [ZERO] * NF
    pR = [ZERO] * NF
    for p in open_idx:
        pMO[p] = ONE14
        if not kind[p - stride]:
            pU[p] = ONE
        if not kind[p + stride]:
            pD[p] = ONE
        if not kind[p - 1]:
            pL[p] = ONE
        if not kind[p + 1]:
            pR[p] = ONE

    pS = [ZERO] * NF
    fmt = '0%db' % B
    for p, v in srcval:
        pS[p] = format(v, fmt)

    def pack(pieces):
        # pieces[i] is field i (MSB first within the field); the last piece is most significant.
        pieces.reverse()
        return int(''.join(pieces), 2)

    MO = pack(pMO)
    SRC = pack(pS)
    NU = pack(pU)
    ND = pack(pD)
    NL = pack(pL)
    NR = pack(pR)

    SU = B * stride
    X = SRC
    for _ in range(S):
        # Neighbour terms: shifted value if passable, own value otherwise.
        # Walls and padding hold 0 in X, so the shifted value is 0 there.
        T = ((X << 2) + (X << SU) + (X >> SU) + (X << B) + (X >> B)
             + (X & NU) + (X & ND) + (X & NL) + (X & NR))
        X = ((T >> 3) & MO) | SRC

    NB = B * NF
    s = format(X, 'b').zfill(NB)

    total = 0
    best = -1
    bR = 0
    bC = 0
    chk = 0
    for p in open_idx:
        st = NB - (p + 1) * B
        v = int(s[st:st + B], 2)
        total += v
        r = p // stride - 1
        c = p % stride - 1
        if v > best:
            best = v
            bR = r
            bC = c
        chk += v * (r * W + c + 1)

    sys.stdout.write(
        "sum %d\nmax %d %d %d\nchecksum %d\n" % (total, best, bR, bC, chk)
    )


if __name__ == '__main__':
    main()
