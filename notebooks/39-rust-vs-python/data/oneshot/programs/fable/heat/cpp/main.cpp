#include <cstdio>
#include <cstdlib>
#include <cstdint>
#include <cstring>
#include <vector>
#include <intrin.h>
#include <immintrin.h>
#include <malloc.h>

static const size_t PADL = 16; // left padding (in cells) of every grid row

static bool has_avx2() {
    int info[4];
    __cpuid(info, 0);
    if (info[0] < 7) return false;
    __cpuid(info, 1);
    bool osxsave = (info[2] & (1 << 27)) != 0;
    bool avx = (info[2] & (1 << 28)) != 0;
    if (!osxsave || !avx) return false;
    unsigned long long x = _xgetbv(0);
    if ((x & 6) != 6) return false;
    __cpuidex(info, 7, 0);
    return (info[1] & (1 << 5)) != 0;
}

// In-place update, one row buffer A holding the old values of the row above.
// new = (old + ((up+down+left+right + old*cnt) >> 2)) >> 1  (== (4*old + sum) / 8 floor)
static void run_avx2(uint16_t* grid, const int8_t* meta, uint16_t* A,
                     int H, int NV, size_t stride, size_t mstride, long long S) {
    const __m256i seven = _mm256_set1_epi16(7);
    const __m256i zero = _mm256_setzero_si256();
    for (long long st = 0; st < S; ++st) {
        for (int k = 0; k < NV; ++k)
            _mm256_storeu_si256((__m256i*)(A + 16 * (size_t)k), zero);
        uint16_t* g = grid + PADL;
        const int8_t* m = meta;
        for (int r = 0; r < H; ++r) {
            __m256i left = _mm256_loadu_si256((const __m256i*)(g - 1));
            for (int k = 0; k < NV; ++k) {
                uint16_t* p = g + 16 * (size_t)k;
                uint16_t* a = A + 16 * (size_t)k;
                __m256i cur = _mm256_loadu_si256((const __m256i*)p);
                __m256i right = _mm256_loadu_si256((const __m256i*)(p + 1));
                __m256i nleft = _mm256_loadu_si256((const __m256i*)(p + 15));
                __m256i down = _mm256_loadu_si256((const __m256i*)(p + stride));
                __m256i up = _mm256_loadu_si256((const __m256i*)a);
                _mm256_storeu_si256((__m256i*)a, cur);
                __m256i lane = _mm256_cvtepi8_epi16(_mm256_castsi256_si128(
                    _mm256_loadu_si256((const __m256i*)(m + 16 * (size_t)k))));
                __m256i sum = _mm256_add_epi16(_mm256_add_epi16(up, down),
                                               _mm256_add_epi16(left, right));
                sum = _mm256_add_epi16(sum, _mm256_mullo_epi16(cur, _mm256_and_si256(lane, seven)));
                __m256i nw = _mm256_srli_epi16(_mm256_add_epi16(cur, _mm256_srli_epi16(sum, 2)), 1);
                _mm256_storeu_si256((__m256i*)p, _mm256_blendv_epi8(cur, nw, lane));
                left = nleft;
            }
            g += stride;
            m += mstride;
        }
    }
    _mm256_zeroupper();
}

static void run_scalar(uint16_t* grid, const int8_t* meta, uint16_t* A,
                       int H, int W, size_t stride, size_t mstride, long long S) {
    for (long long st = 0; st < S; ++st) {
        for (int c = 0; c < W; ++c) A[c] = 0;
        uint16_t* g = grid + PADL;
        const int8_t* m = meta;
        for (int r = 0; r < H; ++r) {
            uint32_t left = g[-1];
            for (int c = 0; c < W; ++c) {
                uint32_t cur = g[c];
                uint32_t up = A[c];
                A[c] = (uint16_t)cur;
                int8_t mm = m[c];
                if (mm) {
                    uint32_t s = up + (uint32_t)g[stride + c] + left + (uint32_t)g[c + 1]
                               + cur * (uint32_t)(mm & 7);
                    g[c] = (uint16_t)((cur + (s >> 2)) >> 1);
                }
                left = cur;
            }
            g += stride;
            m += mstride;
        }
    }
}

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    FILE* f = fopen(argv[1], "rb");
    if (!f) return 1;
    fseek(f, 0, SEEK_END);
    long fsz = ftell(f);
    fseek(f, 0, SEEK_SET);
    if (fsz < 0) fsz = 0;
    std::vector<char> buf((size_t)fsz + 1);
    size_t n = fread(buf.data(), 1, (size_t)fsz, f);
    fclose(f);
    buf[n] = 0;

    const char* p = buf.data();
    const char* end = p + n;
    auto readInt = [&]() -> long long {
        while (p < end && (*p < '0' || *p > '9')) ++p;
        long long v = 0;
        while (p < end && *p >= '0' && *p <= '9') { v = v * 10 + (*p - '0'); ++p; }
        return v;
    };
    int H = (int)readInt();
    int W = (int)readInt();
    long long S = readInt();
    if (H <= 0 || W <= 0) return 1;

    std::vector<char> cells((size_t)H * (size_t)W, '#');
    for (int r = 0; r < H; ++r) {
        while (p < end && (unsigned char)*p <= ' ') ++p;
        char* row = cells.data() + (size_t)r * W;
        int c = 0;
        while (c < W && p < end && (unsigned char)*p > ' ') { row[c++] = *p++; }
        // skip any excess characters on the line
        while (p < end && *p != '\n') ++p;
    }

    int NV = (W + 15) / 16;
    size_t stride = PADL + (size_t)NV * 16 + 16;
    size_t mstride = (size_t)NV * 16;

    size_t gridCells = (size_t)(H + 1) * stride + 64;
    size_t metaBytes = (size_t)H * mstride + 64;
    size_t aCells = (size_t)NV * 16 + 32;

    uint16_t* grid = (uint16_t*)_aligned_malloc(gridCells * sizeof(uint16_t), 64);
    int8_t* meta = (int8_t*)_aligned_malloc(metaBytes, 64);
    uint16_t* A = (uint16_t*)_aligned_malloc(aCells * sizeof(uint16_t), 64);
    if (!grid || !meta || !A) return 1;
    memset(grid, 0, gridCells * sizeof(uint16_t));
    memset(meta, 0, metaBytes);
    memset(A, 0, aCells * sizeof(uint16_t));

    auto blocked = [&](int r, int c) -> int {
        if (r < 0 || r >= H || c < 0 || c >= W) return 1;
        return cells[(size_t)r * W + c] == '#' ? 1 : 0;
    };

    for (int r = 0; r < H; ++r) {
        for (int c = 0; c < W; ++c) {
            char ch = cells[(size_t)r * W + c];
            if (ch == '.') {
                int cnt = blocked(r - 1, c) + blocked(r + 1, c) + blocked(r, c - 1) + blocked(r, c + 1);
                meta[(size_t)r * mstride + c] = (int8_t)(0x80 | cnt);
            } else if (ch >= '1' && ch <= '9') {
                grid[(size_t)r * stride + PADL + c] = (uint16_t)(1000 * (ch - '0'));
            }
        }
    }

    if (S > 0) {
        if (has_avx2())
            run_avx2(grid, meta, A, H, NV, stride, mstride, S);
        else
            run_scalar(grid, meta, A, H, W, stride, mstride, S);
    }

    long long T = 0, K = 0;
    long long V = -1;
    int R = 0, C = 0;
    for (int r = 0; r < H; ++r) {
        const uint16_t* g = grid + (size_t)r * stride + PADL;
        const int8_t* m = meta + (size_t)r * mstride;
        long long base = (long long)r * W + 1;
        for (int c = 0; c < W; ++c) {
            if (m[c]) {
                long long v = g[c];
                T += v;
                K += v * (base + c);
                if (v > V) { V = v; R = r; C = c; }
            }
        }
    }
    if (V < 0) V = 0;

    printf("sum %lld\nmax %lld %d %d\nchecksum %lld\n", T, V, R, C, K);

    _aligned_free(grid);
    _aligned_free(meta);
    _aligned_free(A);
    return 0;
}
