#include <cstdio>
#include <cstdint>
#include <vector>
#include <string>
#include <fstream>
#include <iostream>

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    std::ifstream in(argv[1]);
    int H, W, S;
    in >> H >> W >> S;
    std::vector<std::string> g(H);
    for (int i = 0; i < H; i++) in >> g[i];

    const int Wp = W + 2, Hp = H + 2;
    const size_t N = (size_t)Wp * Hp;
    std::vector<int32_t> A(N, 0), B(N, 0), C(N, 0), M(N, 0);
    std::vector<unsigned char> kind(N, 0); // 0 wall, 1 open, 2 source

    for (int r = 0; r < H; r++) {
        for (int c = 0; c < W; c++) {
            char ch = g[r][c];
            size_t idx = (size_t)(r + 1) * Wp + (c + 1);
            if (ch == '#') kind[idx] = 0;
            else if (ch == '.') kind[idx] = 1;
            else {
                kind[idx] = 2;
                A[idx] = 1000 * (ch - '0');
            }
        }
    }
    for (int r = 0; r < H; r++) {
        for (int c = 0; c < W; c++) {
            size_t idx = (size_t)(r + 1) * Wp + (c + 1);
            if (kind[idx] == 1) {
                int wc = 0;
                if (kind[idx - Wp] == 0) wc++;
                if (kind[idx + Wp] == 0) wc++;
                if (kind[idx - 1] == 0) wc++;
                if (kind[idx + 1] == 0) wc++;
                C[idx] = 4 + wc;
                M[idx] = -1;
            } else if (kind[idx] == 2) {
                C[idx] = 8;
                M[idx] = 0;
            }
        }
    }
    B = A;

    int32_t* cur = A.data();
    int32_t* nxt = B.data();
    const int32_t* __restrict cc = C.data();
    const int32_t* __restrict mm = M.data();
    const size_t start = (size_t)Wp + 1;
    const size_t end = (size_t)(H + 1) * Wp - 1; // exclusive
    for (int s = 0; s < S; s++) {
        const int32_t* __restrict a = cur;
        int32_t* __restrict b = nxt;
        for (size_t i = start; i < end; i++) {
            int32_t nb = a[i - Wp] + a[i + Wp] + a[i - 1] + a[i + 1];
            b[i] = (cc[i] * a[i] + (nb & mm[i])) >> 3;
        }
        std::swap(cur, nxt);
    }

    int64_t sum = 0, chk = 0;
    int32_t best = -1;
    int br = 0, bc = 0;
    for (int r = 0; r < H; r++) {
        for (int c = 0; c < W; c++) {
            size_t idx = (size_t)(r + 1) * Wp + (c + 1);
            if (kind[idx] != 1) continue;
            int32_t v = cur[idx];
            sum += v;
            chk += (int64_t)v * ((int64_t)r * W + c + 1);
            if (v > best) { best = v; br = r; bc = c; }
        }
    }
    std::printf("sum %lld\nmax %d %d %d\nchecksum %lld\n",
                (long long)sum, best, br, bc, (long long)chk);
    return 0;
}
