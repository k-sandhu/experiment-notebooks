#include <cstdio>
#include <cstdint>
#include <string>
#include <vector>
#include <utility>

// One simulation step on a padded grid (row stride Wp = W + 2).
// cur/nxt: current and next values. Walls and padding hold 0 and sources hold
// their fixed value; both are copied through unchanged (fm == 0 there).
// cf[i] = 4 + (number of wall/outside neighbours) for free cells.
// Neighbour sums use 0 for walls/outside, so the self-substitution term is
// k * old, which is folded into cf.
static void stepGrid(const int32_t* __restrict cur, int32_t* __restrict nxt,
                     const int32_t* __restrict cf, const int32_t* __restrict fm,
                     int H, int Wp) {
    for (int r = 1; r <= H; ++r) {
        const int base = r * Wp;
        const int end = base + Wp - 1;
        for (int i = base + 1; i < end; ++i) {
            const int32_t comp =
                (cf[i] * cur[i] + cur[i - 1] + cur[i + 1] + cur[i - Wp] + cur[i + Wp]) >> 3;
            nxt[i] = (comp & fm[i]) | (cur[i] & ~fm[i]);
        }
    }
}

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    FILE* f = std::fopen(argv[1], "rb");
    if (!f) return 1;
    std::string data;
    {
        char buf[1 << 16];
        size_t n;
        while ((n = std::fread(buf, 1, sizeof buf, f)) > 0) data.append(buf, n);
    }
    std::fclose(f);

    size_t p = 0;
    const size_t sz = data.size();
    auto readInt = [&]() -> long long {
        while (p < sz && !((data[p] >= '0' && data[p] <= '9') || data[p] == '-')) ++p;
        bool neg = false;
        if (p < sz && data[p] == '-') { neg = true; ++p; }
        long long v = 0;
        while (p < sz && data[p] >= '0' && data[p] <= '9') {
            v = v * 10 + (data[p] - '0');
            ++p;
        }
        return neg ? -v : v;
    };

    const int H = static_cast<int>(readInt());
    const int W = static_cast<int>(readInt());
    const long long S = readInt();

    const int Hp = H + 2;
    const int Wp = W + 2;
    const int total = Hp * Wp;

    // Grid characters; padding and unknown characters are treated as walls.
    std::vector<char> g(total, '#');
    for (int r = 1; r <= H; ++r) {
        for (int c = 1; c <= W; ++c) {
            while (p < sz && static_cast<unsigned char>(data[p]) <= ' ') ++p;
            char ch = '#';
            if (p < sz) ch = data[p++];
            g[r * Wp + c] = ch;
        }
    }

    std::vector<int32_t> bufA(total, 0), bufB(total, 0), cf(total, 0), fm(total, 0);

    for (int r = 1; r <= H; ++r) {
        for (int c = 1; c <= W; ++c) {
            const int i = r * Wp + c;
            const char ch = g[i];
            if (ch == '.') {
                int k = 0;
                k += (g[i - 1] == '#');
                k += (g[i + 1] == '#');
                k += (g[i - Wp] == '#');
                k += (g[i + Wp] == '#');
                cf[i] = 4 + k;
                fm[i] = -1;
                bufA[i] = 0;
            } else if (ch >= '1' && ch <= '9') {
                cf[i] = 0;
                fm[i] = 0;
                bufA[i] = 1000 * (ch - '0');
            } else {
                // wall (or unexpected character): stays 0 forever
                cf[i] = 0;
                fm[i] = 0;
                bufA[i] = 0;
            }
        }
    }
    bufB = bufA;

    int32_t* a = bufA.data();
    int32_t* b = bufB.data();
    for (long long s = 0; s < S; ++s) {
        stepGrid(a, b, cf.data(), fm.data(), H, Wp);
        std::swap(a, b);
    }

    // Final statistics.
    long long T = 0;
    for (int r = 1; r <= H; ++r) {
        const int base = r * Wp;
        for (int c = 1; c <= W; ++c) T += a[base + c];
    }

    long long bestV = -1;
    int bestR = 0, bestC = 0;
    for (int r = 1; r <= H; ++r) {
        for (int c = 1; c <= W; ++c) {
            const int i = r * Wp + c;
            if (g[i] == '#') continue;
            if (static_cast<long long>(a[i]) > bestV) {
                bestV = a[i];
                bestR = r - 1;
                bestC = c - 1;
            }
        }
    }

    long long K = 0;
    for (int r = 1; r <= H; ++r) {
        for (int c = 1; c <= W; ++c) {
            const int i = r * Wp + c;
            if (g[i] == '#') continue;
            const long long idx = static_cast<long long>(r - 1) * W + (c - 1) + 1;
            K += static_cast<long long>(a[i]) * idx;
        }
    }

    std::printf("sum %lld\n", T);
    std::printf("max %lld %d %d\n", bestV < 0 ? 0LL : bestV, bestR, bestC);
    std::printf("checksum %lld\n", K);
    return 0;
}
