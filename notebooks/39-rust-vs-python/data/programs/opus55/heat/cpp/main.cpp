// Heat on a grid: exact integer diffusion with walls and fixed sources.
//
// Values never exceed 9000 (each new value is a floor-average of values <= the largest source), so
// cells are stored as uint16 in a zero-padded grid. With S = sum of the four neighbour terms (wall or
// outside neighbours replaced by the cell's own value), floor((4*o + S) / 8) == (o + (S >> 2)) >> 1,
// and S <= 36000, so every intermediate fits in 16 bits. Walls hold 0, so S = up+down+left+right + w*o
// where w is the number of wall/outside neighbours. A single per-cell meta word holds w (0..4) for open
// cells, the fixed value for sources, and 0x8000 for walls, so each cell costs only three memory streams.
//
// The iteration is monotone non-decreasing, so a row whose 3x3 neighbourhood of rows did not change in
// the previous step cannot change; such rows are skipped, and a step with no change ends the run.

#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include <fcntl.h>
#include <intrin.h>
#include <io.h>
#include <immintrin.h>

namespace {

constexpr uint16_t kWall = 0x8000;

bool hasAvx2() {
    int r[4];
    __cpuid(r, 0);
    if (r[0] < 7) return false;
    __cpuid(r, 1);
    bool osxsave = (r[2] >> 27) & 1, avx = (r[2] >> 28) & 1;
    if (!osxsave || !avx) return false;
    if ((_xgetbv(0) & 6) != 6) return false;
    __cpuidex(r, 7, 0);
    return (r[1] >> 5) & 1;
}

// Computes one row (cols 1..n) from src into dst; returns true if any value changed.
__declspec(noinline) bool rowAvx2(const uint16_t* __restrict src, uint16_t* __restrict dst,
                                  const uint16_t* __restrict meta, int n, int stride) {
    const __m256i four = _mm256_set1_epi16(4);
    const __m256i low15 = _mm256_set1_epi16(0x7FFF);
    __m256i diff = _mm256_setzero_si256();
    for (int i = 1; i <= n; i += 16) {
        __m256i o = _mm256_loadu_si256((const __m256i*)(src + i));
        __m256i up = _mm256_loadu_si256((const __m256i*)(src + i - stride));
        __m256i dn = _mm256_loadu_si256((const __m256i*)(src + i + stride));
        __m256i l = _mm256_loadu_si256((const __m256i*)(src + i - 1));
        __m256i r = _mm256_loadu_si256((const __m256i*)(src + i + 1));
        __m256i m = _mm256_loadu_si256((const __m256i*)(meta + i));
        __m256i open = _mm256_cmpeq_epi16(_mm256_min_epu16(m, four), m);
        __m256i s = _mm256_add_epi16(_mm256_add_epi16(up, dn), _mm256_add_epi16(l, r));
        s = _mm256_add_epi16(s, _mm256_mullo_epi16(m, o));
        __m256i v = _mm256_srli_epi16(_mm256_add_epi16(o, _mm256_srli_epi16(s, 2)), 1);
        v = _mm256_blendv_epi8(_mm256_and_si256(m, low15), v, open);
        _mm256_storeu_si256((__m256i*)(dst + i), v);
        diff = _mm256_or_si256(diff, _mm256_xor_si256(v, o));
    }
    return !_mm256_testz_si256(diff, diff);
}

__declspec(noinline) bool rowSse2(const uint16_t* __restrict src, uint16_t* __restrict dst,
                                  const uint16_t* __restrict meta, int n, int stride) {
    const __m128i bias = _mm_set1_epi16((short)0x8000);
    const __m128i fiveBiased = _mm_set1_epi16((short)(0x8000 + 5));
    const __m128i low15 = _mm_set1_epi16(0x7FFF);
    __m128i diff = _mm_setzero_si128();
    for (int i = 1; i <= n; i += 8) {
        __m128i o = _mm_loadu_si128((const __m128i*)(src + i));
        __m128i up = _mm_loadu_si128((const __m128i*)(src + i - stride));
        __m128i dn = _mm_loadu_si128((const __m128i*)(src + i + stride));
        __m128i l = _mm_loadu_si128((const __m128i*)(src + i - 1));
        __m128i r = _mm_loadu_si128((const __m128i*)(src + i + 1));
        __m128i m = _mm_loadu_si128((const __m128i*)(meta + i));
        // unsigned m <= 4  <=>  signed (m ^ 0x8000) < (5 ^ 0x8000)
        __m128i open = _mm_cmplt_epi16(_mm_xor_si128(m, bias), fiveBiased);
        __m128i s = _mm_add_epi16(_mm_add_epi16(up, dn), _mm_add_epi16(l, r));
        s = _mm_add_epi16(s, _mm_mullo_epi16(m, o));
        __m128i v = _mm_srli_epi16(_mm_add_epi16(o, _mm_srli_epi16(s, 2)), 1);
        v = _mm_or_si128(_mm_and_si128(open, v), _mm_andnot_si128(open, _mm_and_si128(m, low15)));
        _mm_storeu_si128((__m128i*)(dst + i), v);
        diff = _mm_or_si128(diff, _mm_xor_si128(v, o));
    }
    return _mm_movemask_epi8(_mm_cmpeq_epi8(diff, _mm_setzero_si128())) != 0xFFFF;
}

std::vector<char> readFile(const char* path) {
    std::vector<char> buf;
    FILE* f = std::fopen(path, "rb");
    if (!f) return buf;
    std::fseek(f, 0, SEEK_END);
    long size = std::ftell(f);
    std::fseek(f, 0, SEEK_SET);
    buf.resize((size_t)size + 1);
    size_t got = std::fread(buf.data(), 1, (size_t)size, f);
    buf.resize(got);
    buf.push_back('\0');
    std::fclose(f);
    return buf;
}

} // namespace

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    std::vector<char> in = readFile(argv[1]);
    const char* p = in.data();
    auto readInt = [&]() -> long long {
        while (*p && (*p < '0' || *p > '9')) ++p;
        long long v = 0;
        while (*p >= '0' && *p <= '9') v = v * 10 + (*p++ - '0');
        return v;
    };
    const int H = (int)readInt();
    const int W = (int)readInt();
    const long long S = readInt();
    const int n = ((W + 15) / 16) * 16;  // columns processed per row (1..n)
    const int stride = n + 2;            // padded row length
    const size_t total = (size_t)(H + 2) * stride + 16;
    std::vector<uint16_t> a(total, 0);    // values; walls and padding hold 0
    std::vector<uint16_t> meta(total, kWall);

    for (int r = 0; r < H; ++r) {
        while (*p == '\r' || *p == '\n' || *p == ' ' || *p == '\t') ++p;
        const size_t base = (size_t)(r + 1) * stride + 1;
        for (int c = 0; c < W; ++c) {
            const char ch = p[c];
            const size_t i = base + c;
            if (ch == '#') continue;
            if (ch >= '1' && ch <= '9') {
                meta[i] = (uint16_t)(1000 * (ch - '0'));
                a[i] = meta[i];
            } else {
                meta[i] = 0;
            }
        }
        p += W;
    }
    for (int r = 1; r <= H; ++r) {
        for (int c = 1; c <= W; ++c) {
            const size_t i = (size_t)r * stride + c;
            if (meta[i] == 0) {
                meta[i] = (uint16_t)((meta[i - 1] == kWall) + (meta[i + 1] == kWall) +
                                     (meta[i - stride] == kWall) + (meta[i + stride] == kWall));
            }
        }
    }
    std::vector<uint16_t> b = a;

    const bool avx2 = hasAvx2();
    std::vector<uint8_t> changed(H + 2, 0), nextChanged(H + 2, 0);
    for (int r = 1; r <= H; ++r) changed[r] = 1;
    uint16_t* cur = a.data();
    uint16_t* nxt = b.data();
    const uint16_t* m = meta.data();
    for (long long step = 0; step < S; ++step) {
        bool any = false;
        for (int r = 1; r <= H; ++r) {
            if (!(changed[r - 1] | changed[r] | changed[r + 1])) {
                nextChanged[r] = 0;
                continue;
            }
            const size_t off = (size_t)r * stride;
            const bool ch = avx2 ? rowAvx2(cur + off, nxt + off, m + off, n, stride)
                                 : rowSse2(cur + off, nxt + off, m + off, n, stride);
            nextChanged[r] = ch;
            any |= ch;
        }
        // Skipped rows hold equal values in both buffers, so swapping is safe.
        std::swap(cur, nxt);
        changed.swap(nextChanged);
        if (!any) break;
    }

    long long sum = 0, checksum = 0;
    int best = -1, bestR = 0, bestC = 0;
    for (int r = 0; r < H; ++r) {
        const size_t base = (size_t)(r + 1) * stride + 1;
        const long long idx0 = (long long)r * W + 1;
        for (int c = 0; c < W; ++c) {
            if (m[base + c] > 4) continue;
            const int v = cur[base + c];
            sum += v;
            checksum += (long long)v * (idx0 + c);
            if (v > best) { best = v; bestR = r; bestC = c; }
        }
    }
    _setmode(_fileno(stdout), _O_BINARY);  // LF line endings, not CRLF
    std::printf("sum %lld\nmax %d %d %d\nchecksum %lld\n", sum, best, bestR, bestC, checksum);
    return 0;
}
