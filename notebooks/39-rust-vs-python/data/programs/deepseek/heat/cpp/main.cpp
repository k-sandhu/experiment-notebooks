#include <cstdio>
#include <cstdint>
#include <cstdlib>
#include <vector>
#include <io.h>
#include <fcntl.h>

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    _setmode(_fileno(stdout), _O_BINARY);
    FILE* f = std::fopen(argv[1], "rb");
    if (!f) return 1;
    std::fseek(f, 0, SEEK_END);
    long len = std::ftell(f);
    std::fseek(f, 0, SEEK_SET);
    std::vector<char> filebuf((size_t)len + 1);
    size_t got = std::fread(filebuf.data(), 1, (size_t)len, f);
    filebuf[got] = '\0';
    std::fclose(f);

    char* p = filebuf.data();
    auto readInt = [&]() -> int {
        while (*p == ' ' || *p == '\n' || *p == '\r' || *p == '\t') ++p;
        int x = 0;
        while (*p >= '0' && *p <= '9') { x = x * 10 + (*p - '0'); ++p; }
        return x;
    };

    const int H = readInt();
    const int W = readInt();
    const int S = readInt();
    while (*p && *p != '\n') ++p;
    if (*p == '\n') ++p;

    const int W2 = W + 2;
    const size_t N = (size_t)(H + 2) * (size_t)W2;

    std::vector<int32_t> cur(N, 0), nxt(N, 0);
    std::vector<uint8_t> kind(N, 0); // 0 = wall, 1 = open, 2 = source
    std::vector<int32_t> open;
    open.reserve((size_t)H * (size_t)W);

    for (int r = 0; r < H; ++r) {
        const char* row = p;
        const int32_t base = (r + 1) * W2 + 1;
        for (int c = 0; c < W; ++c) {
            char ch = row[c];
            int32_t idx = base + c;
            if (ch == '.') {
                kind[idx] = 1;
                open.push_back(idx);
            } else if (ch >= '1' && ch <= '9') {
                kind[idx] = 2;
                int32_t v = (ch - '0') * 1000;
                cur[idx] = v;
                nxt[idx] = v;
            }
        }
        p += W;
        while (*p && *p != '\n') ++p;
        if (*p == '\n') ++p;
    }

    const int nOpen = (int)open.size();

    // Walls and the outside border stay 0 forever, so a wall neighbour simply
    // contributes 0; coef = 4 + (number of wall/outside neighbours) adds the
    // cell's own old value back for each of them. Sources are never written.
    std::vector<uint8_t> coef(nOpen, 0);
    for (int j = 0; j < nOpen; ++j) {
        int i = open[j];
        int a = kind[i - W2] != 0;
        int b = kind[i + W2] != 0;
        int l = kind[i - 1] != 0;
        int r = kind[i + 1] != 0;
        coef[j] = (uint8_t)(4 + (1 - a) + (1 - b) + (1 - l) + (1 - r));
    }

    int32_t* c = cur.data();
    int32_t* n = nxt.data();
    const int32_t* idxs = open.data();
    const uint8_t* cf = coef.data();

    for (int s = 0; s < S; ++s) {
        for (int j = 0; j < nOpen; ++j) {
            int i = idxs[j];
            n[i] = ((int32_t)cf[j] * c[i]
                  + c[i - W2] + c[i + W2] + c[i - 1] + c[i + 1]) >> 3;
        }
        int32_t* tmp = c; c = n; n = tmp;
    }

    int64_t sum = 0, chk = 0;
    int32_t maxv = -1;
    int bestR = 0, bestC = 0;
    for (int j = 0; j < nOpen; ++j) {
        int i = open[j];
        int32_t v = c[i];
        int r = i / W2 - 1;
        int col = i % W2 - 1;
        sum += v;
        chk += (int64_t)v * ((int64_t)r * W + col + 1);
        if (v > maxv) { maxv = v; bestR = r; bestC = col; }
    }

    std::printf("sum %lld\nmax %d %d %d\nchecksum %lld\n",
                (long long)sum, (int)maxv, bestR, bestC, (long long)chk);
    return 0;
}
