#include <cstdio>
#include <cstdint>
#include <cstdlib>
#include <thread>
#include <vector>
#include <atomic>
#include <algorithm>

#if defined(_MSC_VER) && defined(_M_X64)
#define WALK_HAVE_AVX2 1
#include <intrin.h>
#include <immintrin.h>
#else
#define WALK_HAVE_AVX2 0
#endif

#if defined(_MSC_VER)
#define WALK_FORCEINLINE __forceinline
#define WALK_NOINLINE __declspec(noinline)
#else
#define WALK_FORCEINLINE inline
#define WALK_NOINLINE
#endif

namespace {

constexpr uint64_t G = 0x9E3779B97F4A7C15ULL;
constexpr uint64_t C1 = 0xBF58476D1CE4E5B9ULL;
constexpr uint64_t C2 = 0x94D049BB133111EBULL;

const int64_t DXT[4] = {1, -1, 0, 0};
const int64_t DYT[4] = {0, 0, 1, -1};

struct WalkOut {
    int64_t x, y, bumps, returns;
};

struct Result {
    int64_t spread = 0;
    int64_t bumps = 0;
    int64_t returns = 0;
    int64_t bestD = -1;
    uint64_t bestJ = 0;
};

WALK_FORCEINLINE void slowSteps(uint64_t& s_, int64_t& x_, int64_t& y_, int64_t B, uint64_t n,
                                int64_t& bumps_, int64_t& returns_) {
    uint64_t s = s_;
    int64_t x = x_, y = y_, bumps = bumps_, rets = returns_;
    const int64_t nB = -B;
    for (uint64_t i = 0; i < n; ++i) {
        s += G;
        uint64_t z = s;
        z = (z ^ (z >> 30)) * C1;
        z = (z ^ (z >> 27)) * C2;
        unsigned d = (unsigned)(z >> 62);
        int64_t nx = x + DXT[d];
        int64_t ny = y + DYT[d];
        if (nx > B || nx < nB || ny > B || ny < nB) {
            ++bumps;
        } else {
            x = nx;
            y = ny;
            if ((x | y) == 0) ++rets;
        }
    }
    s_ = s;
    x_ = x;
    y_ = y;
    bumps_ = bumps;
    returns_ = rets;
}

WALK_NOINLINE void walkScalar(uint64_t s, uint64_t L, int64_t B, WalkOut& out) {
    int64_t x = 0, y = 0, bumps = 0, rets = 0;
    uint64_t rem = L;
    while (rem) {
        int64_t ax = x < 0 ? -x : x;
        int64_t ay = y < 0 ? -y : y;
        int64_t m = std::min(B - ax, B - ay);
        int64_t o = ax + ay - 1;
        int64_t k = std::min(m, o);
        uint64_t ku = k > 0 ? (uint64_t)k : 0;
        if (ku > rem) ku = rem;
        if (ku > 32768) ku = 32768;
        if (ku >= 8) {
            uint64_t acc = 0;
            for (uint64_t i = 0; i < ku; ++i) {
                s += G;
                uint64_t z = s;
                z = (z ^ (z >> 30)) * C1;
                z = (z ^ (z >> 27)) * C2;
                acc += 1ULL << ((z >> 58) & 48);
            }
            x += (int64_t)(acc & 0xffff) - (int64_t)((acc >> 16) & 0xffff);
            y += (int64_t)((acc >> 32) & 0xffff) - (int64_t)(acc >> 48);
            rem -= ku;
        } else {
            uint64_t n = rem < 8 ? rem : 8;
            slowSteps(s, x, y, B, n, bumps, rets);
            rem -= n;
        }
    }
    out.x = x;
    out.y = y;
    out.bumps = bumps;
    out.returns = rets;
}

#if WALK_HAVE_AVX2
bool detectAVX2() {
    int info[4];
    __cpuid(info, 0);
    if (info[0] < 7) return false;
    __cpuid(info, 1);
    bool osxsave = (info[2] & (1 << 27)) != 0;
    bool avx = (info[2] & (1 << 28)) != 0;
    if (!osxsave || !avx) return false;
    unsigned long long xcr = _xgetbv(0);
    if ((xcr & 6) != 6) return false;
    __cpuidex(info, 7, 0);
    return (info[1] & (1 << 5)) != 0;
}

WALK_FORCEINLINE __m256i mul64c(__m256i a, __m256i clo, __m256i chi) {
    __m256i lo = _mm256_mul_epu32(a, clo);
    __m256i t1 = _mm256_mul_epu32(_mm256_srli_epi64(a, 32), clo);
    __m256i t2 = _mm256_mul_epu32(a, chi);
    return _mm256_add_epi64(lo, _mm256_slli_epi64(_mm256_add_epi64(t1, t2), 32));
}

WALK_NOINLINE void walkAVX2(uint64_t s, uint64_t L, int64_t B, WalkOut& out) {
    const __m256i c1lo = _mm256_set1_epi64x((long long)C1);
    const __m256i c1hi = _mm256_set1_epi64x((long long)(C1 >> 32));
    const __m256i c2lo = _mm256_set1_epi64x((long long)C2);
    const __m256i c2hi = _mm256_set1_epi64x((long long)(C2 >> 32));
    const __m256i offs = _mm256_set_epi64x((long long)(G * 4ULL), (long long)(G * 3ULL),
                                           (long long)(G * 2ULL), (long long)G);
    const __m256i inc = _mm256_set1_epi64x((long long)(G * 4ULL));
    const __m256i one = _mm256_set1_epi64x(1);
    const __m256i m48 = _mm256_set1_epi64x(48);

    int64_t x = 0, y = 0, bumps = 0, rets = 0;
    uint64_t rem = L;
    while (rem) {
        int64_t ax = x < 0 ? -x : x;
        int64_t ay = y < 0 ? -y : y;
        int64_t m = std::min(B - ax, B - ay);
        int64_t o = ax + ay - 1;
        int64_t k = std::min(m, o);
        uint64_t ku = k > 0 ? (uint64_t)k : 0;
        if (ku > rem) ku = rem;
        if (ku > 32768) ku = 32768;
        ku &= ~3ULL;
        if (ku >= 12) {
            uint64_t n = ku >> 2;
            __m256i vs = _mm256_add_epi64(_mm256_set1_epi64x((long long)s), offs);
            __m256i acc = _mm256_setzero_si256();
            for (uint64_t i = 0; i < n; ++i) {
                __m256i z = vs;
                vs = _mm256_add_epi64(vs, inc);
                z = _mm256_xor_si256(z, _mm256_srli_epi64(z, 30));
                z = mul64c(z, c1lo, c1hi);
                z = _mm256_xor_si256(z, _mm256_srli_epi64(z, 27));
                z = mul64c(z, c2lo, c2hi);
                __m256i sh = _mm256_and_si256(_mm256_srli_epi64(z, 58), m48);
                acc = _mm256_add_epi64(acc, _mm256_sllv_epi64(one, sh));
            }
            s += ku * G;
            alignas(32) uint64_t arr[4];
            _mm256_store_si256((__m256i*)arr, acc);
            uint64_t tot = arr[0] + arr[1] + arr[2] + arr[3];
            x += (int64_t)(tot & 0xffff) - (int64_t)((tot >> 16) & 0xffff);
            y += (int64_t)((tot >> 32) & 0xffff) - (int64_t)(tot >> 48);
            rem -= ku;
        } else {
            uint64_t n = rem < 8 ? rem : 8;
            slowSteps(s, x, y, B, n, bumps, rets);
            rem -= n;
        }
    }
    _mm256_zeroupper();
    out.x = x;
    out.y = y;
    out.bumps = bumps;
    out.returns = rets;
}
#endif

} // namespace

int main(int argc, char** argv) {
    uint64_t vals[4] = {0, 0, 0, 0};
    if (argc >= 2) {
        FILE* f = std::fopen(argv[1], "rb");
        if (f) {
            char buf[512];
            size_t len = std::fread(buf, 1, sizeof(buf), f);
            std::fclose(f);
            size_t p = 0;
            for (int i = 0; i < 4; ++i) {
                while (p < len && (buf[p] < '0' || buf[p] > '9')) ++p;
                uint64_t v = 0;
                while (p < len && buf[p] >= '0' && buf[p] <= '9') {
                    v = v * 10ULL + (uint64_t)(buf[p] - '0');
                    ++p;
                }
                vals[i] = v;
            }
        }
    }
    const uint64_t J = vals[0];
    const uint64_t L = vals[1];
    int64_t B = vals[2] > (uint64_t)INT64_MAX ? INT64_MAX : (int64_t)vals[2];
    if (B < 1) B = 1;
    const uint64_t SEED = vals[3];

    long workersArg = 1;
    if (argc >= 3) workersArg = std::strtol(argv[2], nullptr, 10);
    if (workersArg < 1) workersArg = 1;
    if (workersArg > 32) workersArg = 32;
    uint64_t W = (uint64_t)workersArg;
    if (W > J) W = J;
    if (W < 1) W = 1;

    bool useAvx2 = false;
#if WALK_HAVE_AVX2
    useAvx2 = detectAVX2();
#endif

    uint64_t maxBatch = J / (W * 4);
    if (maxBatch < 1) maxBatch = 1;
    uint64_t batch = 1;
    if (L == 0) batch = maxBatch;
    else if (L < 65536) batch = 65536 / L;
    if (batch > maxBatch) batch = maxBatch;
    if (batch < 1) batch = 1;

    std::vector<Result> results((size_t)W);
    std::atomic<uint64_t> nextWalker{0};

    auto worker = [&](size_t tid) {
        Result r;
        for (;;) {
            uint64_t start = nextWalker.fetch_add(batch, std::memory_order_relaxed);
            if (start >= J) break;
            uint64_t end = (J - start < batch) ? J : start + batch;
            for (uint64_t j = start; j < end; ++j) {
                WalkOut o;
                uint64_t s = SEED + j;
#if WALK_HAVE_AVX2
                if (useAvx2) walkAVX2(s, L, B, o);
                else walkScalar(s, L, B, o);
#else
                walkScalar(s, L, B, o);
#endif
                r.spread += o.x * o.x + o.y * o.y;
                r.bumps += o.bumps;
                r.returns += o.returns;
                int64_t d = (o.x < 0 ? -o.x : o.x) + (o.y < 0 ? -o.y : o.y);
                if (d > r.bestD || (d == r.bestD && j < r.bestJ)) {
                    r.bestD = d;
                    r.bestJ = j;
                }
            }
        }
        results[tid] = r;
    };

    std::vector<std::thread> threads;
    threads.reserve((size_t)W);
    for (size_t t = 1; t < (size_t)W; ++t) {
        try {
            threads.emplace_back(worker, t);
        } catch (...) {
            break;
        }
    }
    worker(0);
    for (auto& th : threads) th.join();

    Result total;
    for (const Result& r : results) {
        total.spread += r.spread;
        total.bumps += r.bumps;
        total.returns += r.returns;
        if (r.bestD > total.bestD || (r.bestD == total.bestD && r.bestD >= 0 && r.bestJ < total.bestJ)) {
            total.bestD = r.bestD;
            total.bestJ = r.bestJ;
        }
    }
    if (total.bestD < 0) {
        total.bestD = 0;
        total.bestJ = 0;
    }

    std::printf("spread %lld\nbumps %lld\nreturns %lld\nfarthest %llu %lld\n",
                (long long)total.spread, (long long)total.bumps, (long long)total.returns,
                (unsigned long long)total.bestJ, (long long)total.bestD);
    std::fflush(stdout);
    return 0;
}
