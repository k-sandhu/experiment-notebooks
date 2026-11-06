#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <thread>
#include <vector>

#ifdef _WIN32
#include <fcntl.h>
#include <io.h>
#endif

using u64 = std::uint64_t;
using i64 = std::int64_t;

namespace {

constexpr u64 kGamma = 0x9E3779B97F4A7C15ull;
constexpr u64 kMul1 = 0xBF58476D1CE4E5B9ull;
constexpr u64 kMul2 = 0x94D049BB133111EBull;

constexpr i64 kDx[4] = {1, -1, 0, 0};
constexpr i64 kDy[4] = {0, 0, 1, -1};

// Steps shorter than this are not worth a trip through the unchecked loop.
constexpr i64 kMinFastRun = 4;

struct WalkResult {
    i64 x, y, bumps, returns;
};

// Top two bits of the next SplitMix64 output. The final z ^ (z >> 31) never changes them.
inline unsigned direction(u64 s) {
    u64 z = (s ^ (s >> 30)) * kMul1;
    z = (z ^ (z >> 27)) * kMul2;
    return static_cast<unsigned>(z >> 62);
}

WalkResult walk(u64 s, i64 steps, i64 bound) {
    const u64 span = static_cast<u64>(2 * bound);
    i64 x = 0, y = 0, bumps = 0, returns = 0;
    i64 left = steps;
    while (left > 0) {
        i64 ax = x < 0 ? -x : x, ay = y < 0 ? -y : y;
        // Within `run` steps the walker can neither reach a wall nor the origin,
        // so those steps need no checks at all.
        i64 run = std::min(bound - std::max(ax, ay), ax + ay - 1);
        if (run >= kMinFastRun) {
            run = std::min(run, left);
            left -= run;
            for (i64 i = 0; i < run; ++i) {
                s += kGamma;
                unsigned d = direction(s);
                x += kDx[d];
                y += kDy[d];
            }
            continue;
        }
        // Checked steps near a wall or the origin, until the walker is clear again.
        i64 end = left > kMinFastRun ? left - kMinFastRun : 0;
        do {
            s += kGamma;
            unsigned d = direction(s);
            i64 nx = x + kDx[d], ny = y + kDy[d];
            bool ok = (static_cast<u64>(nx + bound) <= span) & (static_cast<u64>(ny + bound) <= span);
            x = ok ? nx : x;
            y = ok ? ny : y;
            bumps += !ok;
            returns += (x | y) == 0;
        } while (--left > end);
    }
    return {x, y, bumps, returns};
}

void walkRange(i64 from, i64 to, u64 seed, i64 steps, i64 bound, WalkResult* out) {
    for (i64 j = from; j < to; ++j) out[j] = walk(seed + static_cast<u64>(j), steps, bound);
}

}  // namespace

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    FILE* f = std::fopen(argv[1], "rb");
    if (!f) return 1;
    char buf[256] = {};
    std::size_t n = std::fread(buf, 1, sizeof(buf) - 1, f);
    std::fclose(f);
    buf[n] = 0;

    char* p = buf;
    i64 walkers = std::strtoll(p, &p, 10);
    i64 steps = std::strtoll(p, &p, 10);
    i64 bound = std::strtoll(p, &p, 10);
    u64 seed = std::strtoull(p, &p, 10);
    int workers = argc >= 3 ? std::atoi(argv[2]) : 1;
    if (workers < 1) workers = 1;

    // A walker never gets farther than `steps` from the origin, so a larger box behaves the same.
    if (bound > steps) bound = steps;

    std::vector<WalkResult> results(static_cast<std::size_t>(walkers > 0 ? walkers : 0));
    i64 threads = std::min<i64>(workers, walkers);
    if (threads > 0) {
        auto rangeStart = [&](i64 t) { return walkers * t / threads; };
        std::vector<std::thread> pool;
        pool.reserve(static_cast<std::size_t>(threads - 1));
        for (i64 t = 1; t < threads; ++t)
            pool.emplace_back(walkRange, rangeStart(t), rangeStart(t + 1), seed, steps, bound, results.data());
        walkRange(0, rangeStart(1), seed, steps, bound, results.data());
        for (auto& th : pool) th.join();
    }

    i64 spread = 0, bumps = 0, returns = 0, bestJ = 0, bestD = -1;
    for (i64 j = 0; j < walkers; ++j) {
        const WalkResult& r = results[static_cast<std::size_t>(j)];
        spread += r.x * r.x + r.y * r.y;
        bumps += r.bumps;
        returns += r.returns;
        i64 d = (r.x < 0 ? -r.x : r.x) + (r.y < 0 ? -r.y : r.y);
        if (d > bestD) bestD = d, bestJ = j;
    }
    if (bestD < 0) bestD = 0;
#ifdef _WIN32
    // Text-mode stdout would write each newline as CR LF.
    _setmode(_fileno(stdout), _O_BINARY);
#endif
    std::printf("spread %lld\nbumps %lld\nreturns %lld\nfarthest %lld %lld\n", spread, bumps, returns, bestJ, bestD);
    return 0;
}
