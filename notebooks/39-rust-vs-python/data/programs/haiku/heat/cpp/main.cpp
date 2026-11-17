// Heat on a grid (see SPEC.md).
//
// The grid is stored padded with a one-cell border of zeros, row stride W + 2, so every
// neighbour lookup is a plain offset. Walls and border cells always hold 0, so a wall
// neighbour contributes 0 and the "use own old value" rule becomes (8 - valid) * old.
// A flat, branch-free loop over all rows then updates the grid; MSVC vectorises it.

#include <cstdint>
#include <cstdio>
#include <fcntl.h>
#include <io.h>
#include <utility>
#include <vector>

namespace {

// One simulation step over the flat index range [begin, end).
// mask is -1 for open cells and 0 otherwise; fixed holds the constant value of sources.
void step(const int32_t* __restrict cur, int32_t* __restrict nxt, const int32_t* __restrict mult,
          const int32_t* __restrict mask, const int32_t* __restrict fixed, int begin, int end,
          int stride) {
    for (int i = begin; i < end; ++i) {
        int32_t sum = mult[i] * cur[i] + cur[i - 1] + cur[i + 1] + cur[i - stride] + cur[i + stride];
        nxt[i] = ((sum >> 3) & mask[i]) | fixed[i];
    }
}

bool isCell(char ch) {
    return ch == '.' || ch == '#' || (ch >= '1' && ch <= '9');
}

}  // namespace

int main(int argc, char** argv) {
    if (argc < 2) {
        std::fputs("usage: solution INPUT_PATH\n", stderr);
        return 2;
    }
    FILE* f = std::fopen(argv[1], "rb");
    if (!f) {
        std::fprintf(stderr, "cannot open %s\n", argv[1]);
        return 1;
    }
    std::fseek(f, 0, SEEK_END);
    long size = std::ftell(f);
    std::fseek(f, 0, SEEK_SET);
    std::vector<char> buf(static_cast<size_t>(size));
    size_t got = std::fread(buf.data(), 1, buf.size(), f);
    std::fclose(f);

    const char* p = buf.data();
    const char* end = p + got;
    auto readInt = [&]() -> long long {
        while (p < end && (*p < '0' || *p > '9')) ++p;
        long long v = 0;
        while (p < end && *p >= '0' && *p <= '9') v = v * 10 + (*p++ - '0');
        return v;
    };
    const int H = static_cast<int>(readInt());
    const int W = static_cast<int>(readInt());
    const long long S = readInt();

    const int P = W + 2;
    const int N = (H + 2) * P;
    std::vector<uint8_t> kind(N, 0);  // 0 = wall or border, 1 = open, 2 = source
    std::vector<int32_t> mult(N, 0), mask(N, 0), fixed(N, 0);

    for (int r = 1; r <= H; ++r) {
        for (int c = 1; c <= W; ++c) {
            while (p < end && !isCell(*p)) ++p;
            if (p >= end) break;
            const char ch = *p++;
            const int i = r * P + c;
            if (ch == '.') {
                kind[i] = 1;
            } else if (ch != '#') {
                kind[i] = 2;
                fixed[i] = 1000 * (ch - '0');
            }
        }
    }

    for (int r = 1; r <= H; ++r) {
        for (int c = 1; c <= W; ++c) {
            const int i = r * P + c;
            if (kind[i] == 1) {
                const int valid = (kind[i - 1] != 0) + (kind[i + 1] != 0) + (kind[i - P] != 0) +
                                  (kind[i + P] != 0);
                mult[i] = 8 - valid;
                mask[i] = -1;
            }
        }
    }

    std::vector<int32_t> bufA(fixed), bufB(fixed);  // sources start at their fixed value
    int32_t* cur = bufA.data();
    int32_t* nxt = bufB.data();
    const int32_t* multP = mult.data();
    const int32_t* maskP = mask.data();
    const int32_t* fixedP = fixed.data();
    const int rowsBegin = P;
    const int rowsEnd = (H + 1) * P;
    for (long long s = 0; s < S; ++s) {
        step(cur, nxt, multP, maskP, fixedP, rowsBegin, rowsEnd, P);
        std::swap(cur, nxt);
    }

    long long total = 0, checksum = 0;
    long long bestV = -1;
    int bestR = -1, bestC = -1;
    for (int r = 0; r < H; ++r) {
        for (int c = 0; c < W; ++c) {
            const int i = (r + 1) * P + c + 1;
            if (kind[i] != 1) continue;
            const long long v = cur[i];
            total += v;
            if (v > bestV) {
                bestV = v;
                bestR = r;
                bestC = c;
            }
            checksum += v * (static_cast<long long>(r) * W + c + 1);
        }
    }

    // Binary mode so the output uses plain "\n" line endings, as in the samples.
    _setmode(_fileno(stdout), _O_BINARY);
    std::printf("sum %lld\nmax %lld %d %d\nchecksum %lld\n", total, bestV, bestR, bestC, checksum);
    return 0;
}
