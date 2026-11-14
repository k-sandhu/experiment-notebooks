#include <cstdio>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <thread>
#include <vector>
#include <algorithm>
#include <io.h>
#include <fcntl.h>

namespace {

constexpr uint64_t GAMMA = 0x9E3779B97F4A7C15ULL;
constexpr uint64_t C1    = 0xBF58476D1CE4E5B9ULL;
constexpr uint64_t C2    = 0x94D049BB133111EBULL;

struct Stat {
    uint64_t spread;
    uint64_t bumps;
    uint64_t returns;
    int64_t x, y;
};

// Branchless single move.  B and nb must be in scope.
#define MOVE(z, x, y, bumps, returns)                                    \
    do {                                                                 \
        const int64_t d_  = (int64_t)((z) >> 62);                        \
        const int64_t dir = 1 - 2 * (d_ & 1);                            \
        const int64_t m_  = -(int64_t)(d_ < 2);                          \
        int64_t nx = (x) + (dir & m_);                                   \
        int64_t ny = (y) + (dir & ~m_);                                  \
        const int64_t ox = (int64_t)(nx > B) - (int64_t)(nx < nb);       \
        const int64_t oy = (int64_t)(ny > B) - (int64_t)(ny < nb);       \
        nx -= ox;                                                        \
        ny -= oy;                                                        \
        (bumps)   += (uint64_t)((ox | oy) != 0);                         \
        (returns) += (uint64_t)((nx | ny) == 0);                         \
        (x) = nx;                                                        \
        (y) = ny;                                                        \
    } while (0)

#define MIX(state, z)                                                    \
    do {                                                                 \
        (state) += GAMMA;                                                \
        uint64_t zz = (state);                                           \
        zz = (zz ^ (zz >> 30)) * C1;                                     \
        zz = (zz ^ (zz >> 27)) * C2;                                     \
        (z) = zz ^ (zz >> 31);                                           \
    } while (0)

inline void run1(uint64_t state, uint64_t steps, int64_t B, Stat* out) {
    int64_t x = 0, y = 0;
    uint64_t bumps = 0, returns = 0;
    const int64_t nb = -B;
    for (uint64_t k = 0; k < steps; ++k) {
        uint64_t z;
        MIX(state, z);
        MOVE(z, x, y, bumps, returns);
    }
    out->spread  = (uint64_t)(x * x + y * y);
    out->bumps   = bumps;
    out->returns = returns;
    out->x = x;
    out->y = y;
}

// Two independent walkers interleaved in the same loop: hides the latency of
// the serial SplitMix64 dependency chain.
inline void run2(uint64_t s0, uint64_t s1, uint64_t steps, int64_t B,
                 Stat* o0, Stat* o1) {
    int64_t x0 = 0, y0 = 0, x1 = 0, y1 = 0;
    uint64_t b0 = 0, r0 = 0, b1 = 0, r1 = 0;
    const int64_t nb = -B;
    for (uint64_t k = 0; k < steps; ++k) {
        uint64_t z0, z1;
        MIX(s0, z0);
        MIX(s1, z1);
        MOVE(z0, x0, y0, b0, r0);
        MOVE(z1, x1, y1, b1, r1);
    }
    o0->spread  = (uint64_t)(x0 * x0 + y0 * y0);
    o0->bumps   = b0;
    o0->returns = r0;
    o0->x = x0;
    o0->y = y0;
    o1->spread  = (uint64_t)(x1 * x1 + y1 * y1);
    o1->bumps   = b1;
    o1->returns = r1;
    o1->x = x1;
    o1->y = y1;
}

inline void run_range(uint64_t seed, uint64_t steps, int64_t B, int64_t j0,
                      int64_t j1, Stat* stats) {
    int64_t j = j0;
    for (; j + 1 < j1; j += 2)
        run2(seed + (uint64_t)j, seed + (uint64_t)(j + 1), steps, B,
             &stats[j], &stats[j + 1]);
    if (j < j1)
        run1(seed + (uint64_t)j, steps, B, &stats[j]);
}

} // namespace

int main(int argc, char** argv) {
    _setmode(_fileno(stdout), _O_BINARY);
    if (argc < 3) {
        std::fprintf(stderr, "usage: %s INPUT_PATH WORKERS\n", argv[0]);
        return 1;
    }

    std::FILE* f = std::fopen(argv[1], "rb");
    if (!f) return 1;
    char buf[256];
    size_t n = std::fread(buf, 1, sizeof(buf) - 1, f);
    std::fclose(f);
    buf[n] = '\0';

    unsigned long long J = 0, L = 0, SEED = 0;
    long long B = 0;
    if (std::sscanf(buf, "%llu %llu %lld %llu", &J, &L, &B, &SEED) != 4) return 1;

    long long workers = std::strtoll(argv[2], nullptr, 10);
    if (workers < 1) workers = 1;
    if ((unsigned long long)workers > J) workers = (long long)J;
    if (workers < 1) workers = 1;

    std::vector<Stat> stats(J);

    if (J > 0) {
        if (workers == 1) {
            run_range((uint64_t)SEED, L, B, 0, (int64_t)J, stats.data());
        } else {
            std::vector<std::thread> threads;
            threads.reserve((size_t)workers);
            unsigned long long base = J / (unsigned long long)workers;
            unsigned long long rem  = J % (unsigned long long)workers;
            unsigned long long start = 0;
            for (long long t = 0; t < workers; ++t) {
                unsigned long long cnt = base + ((unsigned long long)t < rem ? 1 : 0);
                unsigned long long s = start;
                unsigned long long e = start + cnt;
                start = e;
                threads.emplace_back([s, e, L, B, &stats, SEED]() {
                    run_range((uint64_t)SEED, L, B, (int64_t)s, (int64_t)e,
                              stats.data());
                });
            }
            for (auto& th : threads) th.join();
        }
    }

    uint64_t spread = 0, bumps = 0, returns = 0;
    int64_t bestDist = 0;
    unsigned long long bestJ = 0;
    for (unsigned long long j = 0; j < J; ++j) {
        const Stat& s = stats[j];
        spread  += s.spread;
        bumps   += s.bumps;
        returns += s.returns;
        int64_t ax = s.x < 0 ? -s.x : s.x;
        int64_t ay = s.y < 0 ? -s.y : s.y;
        int64_t d = ax + ay;
        if (d > bestDist) { bestDist = d; bestJ = j; }
    }

    std::printf("spread %llu\nbumps %llu\nreturns %llu\nfarthest %llu %lld\n",
                (unsigned long long)spread,
                (unsigned long long)bumps,
                (unsigned long long)returns,
                bestJ, (long long)bestDist);
    return 0;
}
