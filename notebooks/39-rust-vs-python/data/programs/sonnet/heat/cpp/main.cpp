#include <cstdio>
#include <io.h>
#include <fcntl.h>
#include <cstdlib>
#include <cstdint>
#include <vector>
#include <string>

static void step(const int* __restrict a, int* __restrict b, const int* __restrict c, const int* __restrict m,
                 long long lo, long long hi, long long w2) {
    for (long long i = lo; i < hi; i++) {
        b[i] = (c[i] * a[i] + ((a[i - 1] + a[i + 1] + a[i - w2] + a[i + w2]) & m[i])) >> 3;
    }
}

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    FILE* f = std::fopen(argv[1], "rb");
    if (!f) return 1;
    std::fseek(f, 0, SEEK_END);
    long sz = std::ftell(f);
    std::fseek(f, 0, SEEK_SET);
    std::string buf(sz, '\0');
    if (sz > 0 && std::fread(&buf[0], 1, sz, f) != (size_t)sz) return 1;
    std::fclose(f);

    size_t p = 0;
    auto readInt = [&]() {
        while (p < buf.size() && (buf[p] < '0' || buf[p] > '9')) p++;
        long long v = 0;
        while (p < buf.size() && buf[p] >= '0' && buf[p] <= '9') v = v * 10 + (buf[p++] - '0');
        return v;
    };
    long long H = readInt(), W = readInt(), S = readInt();
    long long w2 = W + 2, h2 = H + 2;
    size_t n = (size_t)(w2 * h2);
    std::vector<int> A(n, 0), B(n, 0), C(n, 8), M(n, 0);
    std::vector<char> open(n, 0), wall(n, 1);
    for (long long r = 0; r < H; r++) {
        while (p < buf.size() && buf[p] != '.' && buf[p] != '#' && (buf[p] < '1' || buf[p] > '9')) p++;
        for (long long col = 0; col < W; col++) {
            char ch = buf[p++];
            size_t idx = (size_t)((r + 1) * w2 + col + 1);
            if (ch == '.') { open[idx] = 1; wall[idx] = 0; M[idx] = -1; }
            else if (ch != '#') { A[idx] = 1000 * (ch - '0'); wall[idx] = 0; }
        }
    }
    for (long long r = 1; r <= H; r++)
        for (long long col = 1; col <= W; col++) {
            size_t idx = (size_t)(r * w2 + col);
            if (!open[idx]) continue;
            C[idx] = 4 + wall[idx - 1] + wall[idx + 1] + wall[idx - w2] + wall[idx + w2];
        }
    B = A;
    long long lo = w2 + 1, hi = (H + 1) * w2 - 1;
    int* a = A.data();
    int* b = B.data();
    for (long long s = 0; s < S; s++) {
        step(a, b, C.data(), M.data(), lo, hi, w2);
        int* t = a; a = b; b = t;
    }
    long long sum = 0, best = -1, br = 0, bc = 0, chk = 0;
    for (long long r = 0; r < H; r++)
        for (long long col = 0; col < W; col++) {
            size_t idx = (size_t)((r + 1) * w2 + col + 1);
            if (!open[idx]) continue;
            long long v = a[idx];
            sum += v;
            if (v > best) { best = v; br = r; bc = col; }
            chk += v * (r * W + col + 1);
        }
    _setmode(_fileno(stdout), _O_BINARY);
    std::printf("sum %lld\nmax %lld %lld %lld\nchecksum %lld\n", sum, best, br, bc, chk);
    return 0;
}
