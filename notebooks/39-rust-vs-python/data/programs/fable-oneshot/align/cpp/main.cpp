#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cstdint>
#include <string>
#include <vector>
#include <charconv>
#include <algorithm>
#include <malloc.h>
#include <intrin.h>
#include <immintrin.h>

static bool hasAVX2() {
    int info[4];
    __cpuid(info, 0);
    if (info[0] < 7) return false;
    __cpuid(info, 1);
    if (!(info[2] & (1 << 27)) || !(info[2] & (1 << 28))) return false;
    if ((_xgetbv(0) & 6) != 6) return false;
    __cpuidex(info, 7, 0);
    return (info[1] & (1 << 5)) != 0;
}

// Transformed DP: H[i][j] = C - D[i][j] + P[j], where P is the prefix sum of insertion costs of t.
// Then H[i][j] = max(H[i-1][j] - del, H[i-1][j-1] - (sub - ins_j), H[i][j-1])  -> prefix max along a row.
static int32_t kernelAVX2(const uint8_t* sc, size_t n, size_t m, size_t stride,
                          const int32_t* prof, const int32_t* delc,
                          int32_t* prev, int32_t* cur, int32_t C) {
    const __m256i idxFix = _mm256_setr_epi32(0, 1, 2, 3, 3, 3, 3, 3);
    const __m256i idx7 = _mm256_set1_epi32(7);
    {
        __m256i cv = _mm256_set1_epi32(C);
        prev[0] = C;
        for (size_t k = 0; k < stride; k += 8)
            _mm256_store_si256((__m256i*)(prev + 1 + k), cv);
    }
    int32_t h0 = C;
    for (size_t i = 0; i < n; ++i) {
        unsigned c = sc[i];
        int32_t d = delc[c];
        h0 -= d;
        cur[0] = h0;
        __m256i carry = _mm256_set1_epi32(h0);
        const __m256i dv = _mm256_set1_epi32(d);
        const int32_t* q = prof + (size_t)c * stride;
        for (size_t k = 0; k < stride; k += 8) {
            __m256i a = _mm256_sub_epi32(_mm256_load_si256((const __m256i*)(prev + 1 + k)), dv);
            __m256i b = _mm256_sub_epi32(_mm256_loadu_si256((const __m256i*)(prev + k)),
                                         _mm256_load_si256((const __m256i*)(q + k)));
            __m256i v = _mm256_max_epi32(a, b);
            v = _mm256_max_epi32(v, _mm256_slli_si256(v, 4));
            v = _mm256_max_epi32(v, _mm256_slli_si256(v, 8));
            v = _mm256_max_epi32(v, _mm256_permutevar8x32_epi32(v, idxFix));
            _mm256_store_si256((__m256i*)(cur + 1 + k), _mm256_max_epi32(v, carry));
            carry = _mm256_max_epi32(carry, _mm256_permutevar8x32_epi32(v, idx7));
        }
        int32_t* tmp = prev; prev = cur; cur = tmp;
    }
    int32_t res = prev[m];
    _mm256_zeroupper();
    return res;
}

int main(int argc, char** argv) {
    if (argc < 2) return 0;
    FILE* f = fopen(argv[1], "rb");
    if (!f) return 0;
    fseek(f, 0, SEEK_END);
    long fsz = ftell(f);
    fseek(f, 0, SEEK_SET);
    if (fsz < 0) fsz = 0;
    std::vector<char> data((size_t)fsz + 1);
    size_t got = fread(data.data(), 1, (size_t)fsz, f);
    fclose(f);
    data[got] = 0;
    const char* p = data.data();
    const char* end = p + got;

    auto skipWs = [&]() {
        while (p < end && (unsigned char)*p <= ' ') ++p;
    };
    auto readToken = [&](const char*& start, size_t& len) {
        skipWs();
        start = p;
        while (p < end && (unsigned char)*p > ' ') ++p;
        len = (size_t)(p - start);
    };
    auto readInt = [&]() -> long long {
        skipWs();
        bool neg = false;
        if (p < end && (*p == '-' || *p == '+')) { neg = (*p == '-'); ++p; }
        long long v = 0;
        while (p < end && *p >= '0' && *p <= '9') { v = v * 10 + (*p - '0'); ++p; }
        return neg ? -v : v;
    };

    const char* alpha; size_t A;
    readToken(alpha, A);
    if (A > 32) A = 32;
    uint8_t idx[256];
    memset(idx, 0, sizeof(idx));
    for (size_t i = 0; i < A; ++i) idx[(unsigned char)alpha[i]] = (uint8_t)i;

    int32_t insc[32] = {0}, delc[32] = {0};
    static int32_t subc[32 * 32];
    static int32_t subins[32 * 32];
    for (size_t i = 0; i < A; ++i) insc[i] = (int32_t)readInt();
    for (size_t i = 0; i < A; ++i) delc[i] = (int32_t)readInt();
    for (size_t i = 0; i < A; ++i)
        for (size_t j = 0; j < A; ++j) {
            int32_t v = (int32_t)readInt();
            subc[i * 32 + j] = v;
            subins[i * 32 + j] = v - insc[j];
        }
    long long P = readInt();

    const bool avx2 = hasAVX2();

    size_t cap = 0;
    int32_t* rowRaw0 = nullptr;
    int32_t* rowRaw1 = nullptr;
    int32_t* prof = nullptr;
    long long builtStamp[32];
    for (int i = 0; i < 32; ++i) builtStamp[i] = -1;

    std::vector<uint8_t> sc, tc;
    std::vector<long long> r0, r1;

    std::string out;
    out.reserve((size_t)(P > 0 ? P : 0) * 12 + 64);
    long long total = 0;
    char numbuf[32];

    for (long long pi = 0; pi < P; ++pi) {
        const char* s; size_t n;
        const char* t; size_t m;
        readToken(s, n);
        readToken(t, m);
        if (n == 0 && m == 0 && p >= end) break;

        if (sc.size() < n + 1) sc.resize(n + 1);
        if (tc.size() < m + 1) tc.resize(m + 1);
        long long sumDel = 0, sumIns = 0;
        for (size_t i = 0; i < n; ++i) {
            uint8_t c = idx[(unsigned char)s[i]];
            sc[i] = c;
            sumDel += delc[c];
        }
        for (size_t j = 0; j < m; ++j) {
            uint8_t c = idx[(unsigned char)t[j]];
            tc[j] = c;
            sumIns += insc[c];
        }
        long long bound = sumDel + sumIns;
        long long cost;

        if (avx2 && n > 0 && m > 0 && 2 * bound + 4000 < 2147483647LL) {
            size_t stride = (m + 7) & ~(size_t)7;
            if (stride > cap) {
                if (rowRaw0) _aligned_free(rowRaw0);
                if (rowRaw1) _aligned_free(rowRaw1);
                if (prof) _aligned_free(prof);
                cap = std::max(stride, cap * 2);
                rowRaw0 = (int32_t*)_aligned_malloc((cap + 32) * sizeof(int32_t), 32);
                rowRaw1 = (int32_t*)_aligned_malloc((cap + 32) * sizeof(int32_t), 32);
                prof = (int32_t*)_aligned_malloc((size_t)32 * cap * sizeof(int32_t), 32);
                if (!rowRaw0 || !rowRaw1 || !prof) return 1;
            }
            // build profile rows lazily for letters occurring in s
            const uint8_t* tcp = tc.data();
            for (size_t i = 0; i < n; ++i) {
                unsigned c = sc[i];
                if (builtStamp[c] != pi) {
                    builtStamp[c] = pi;
                    int32_t* row = prof + (size_t)c * stride;
                    const int32_t* tab = subins + c * 32;
                    for (size_t j = 0; j < m; ++j) row[j] = tab[tcp[j]];
                    for (size_t j = m; j < stride; ++j) row[j] = 0;
                }
            }
            int32_t C = (int32_t)(bound + 1);
            int32_t h = kernelAVX2(sc.data(), n, m, stride, prof, delc,
                                   rowRaw0 + 7, rowRaw1 + 7, C);
            cost = (long long)C - (long long)h + sumIns;
        } else {
            if (r0.size() < m + 1) { r0.resize(m + 1); r1.resize(m + 1); }
            long long* prev = r0.data();
            long long* cur = r1.data();
            prev[0] = 0;
            for (size_t j = 1; j <= m; ++j) prev[j] = prev[j - 1] + insc[tc[j - 1]];
            for (size_t i = 0; i < n; ++i) {
                unsigned c = sc[i];
                long long d = delc[c];
                const int32_t* tab = subc + c * 32;
                cur[0] = prev[0] + d;
                long long left = cur[0];
                for (size_t j = 1; j <= m; ++j) {
                    unsigned tcj = tc[j - 1];
                    long long v = prev[j] + d;
                    long long w = left + insc[tcj];
                    long long x = prev[j - 1] + tab[tcj];
                    if (w < v) v = w;
                    if (x < v) v = x;
                    cur[j] = v;
                    left = v;
                }
                std::swap(prev, cur);
            }
            cost = prev[m];
        }

        total += cost;
        auto r = std::to_chars(numbuf, numbuf + sizeof(numbuf), cost);
        out.append(numbuf, (size_t)(r.ptr - numbuf));
        out.push_back('\n');
    }

    out.append("total ");
    {
        auto r = std::to_chars(numbuf, numbuf + sizeof(numbuf), total);
        out.append(numbuf, (size_t)(r.ptr - numbuf));
    }
    out.push_back('\n');
    fwrite(out.data(), 1, out.size(), stdout);
    fflush(stdout);

    if (rowRaw0) _aligned_free(rowRaw0);
    if (rowRaw1) _aligned_free(rowRaw1);
    if (prof) _aligned_free(prof);
    return 0;
}
