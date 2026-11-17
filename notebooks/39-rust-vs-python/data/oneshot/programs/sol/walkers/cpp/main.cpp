#include <algorithm>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <thread>
#include <vector>

using u64 = std::uint64_t;
using i64 = std::int64_t;

struct Walker {
    u64 state = 0;
    i64 position[2] = {0, 0};
    u64 bumps = 0;
    u64 returns = 0;
};

struct alignas(64) Result {
    u64 spread = 0;
    u64 bumps = 0;
    u64 returns = 0;
    u64 farthestIndex = std::numeric_limits<u64>::max();
    u64 farthestDistance = 0;
};

static inline void takeStep(Walker& w, i64 bound) noexcept {
    w.state += 0x9E3779B97F4A7C15ULL;
    u64 r = w.state;
    r = (r ^ (r >> 30)) * 0xBF58476D1CE4E5B9ULL;
    r = (r ^ (r >> 27)) * 0x94D049BB133111EBULL;
    r ^= r >> 31;

    const unsigned axis = static_cast<unsigned>(r >> 63);
    const i64 negative = static_cast<i64>((r >> 62) & 1ULL);
    const i64 delta = 1 - 2 * negative;

    // Select +bound or -bound without a direction-dependent branch.
    const i64 wall = (bound ^ (-negative)) + negative;
    i64& coordinate = w.position[axis];
    const bool moved = coordinate != wall;

    coordinate += delta & (-static_cast<i64>(moved));
    w.bumps += static_cast<u64>(!moved);

    // Since bound >= 1, a bump cannot occur at the origin.
    w.returns += static_cast<u64>(
        (w.position[0] | w.position[1]) == 0);
}

template<unsigned N>
static void simulateBatch(
    u64 first, u64 steps, i64 bound, u64 seed, Result& result) noexcept {

    Walker walkers[N];
    for (unsigned k = 0; k < N; ++k) {
        walkers[k].state = seed + first + static_cast<u64>(k);
    }

    for (u64 step = 0; step < steps; ++step) {
        takeStep(walkers[0], bound);
        if constexpr (N >= 2) takeStep(walkers[1], bound);
        if constexpr (N >= 3) takeStep(walkers[2], bound);
        if constexpr (N >= 4) takeStep(walkers[3], bound);
    }

    for (unsigned k = 0; k < N; ++k) {
        const Walker& w = walkers[k];
        const i64 x = w.position[0];
        const i64 y = w.position[1];

        const u64 ax = x < 0 ? u64(0) - static_cast<u64>(x)
                             : static_cast<u64>(x);
        const u64 ay = y < 0 ? u64(0) - static_cast<u64>(y)
                             : static_cast<u64>(y);
        const u64 distance = ax + ay;
        const u64 index = first + static_cast<u64>(k);

        result.spread += ax * ax + ay * ay;
        result.bumps += w.bumps;
        result.returns += w.returns;

        if (distance > result.farthestDistance ||
            (distance == result.farthestDistance &&
             index < result.farthestIndex)) {
            result.farthestDistance = distance;
            result.farthestIndex = index;
        }
    }
}

int main(int argc, char* argv[]) {
    if (argc != 3) return 0;

    std::ifstream input(argv[1]);
    u64 walkerCount, steps, seed;
    i64 bound;
    if (!(input >> walkerCount >> steps >> bound >> seed)) return 0;

    unsigned workerCount = 0;
    for (const char* p = argv[2]; *p != '\0'; ++p) {
        workerCount = workerCount * 10 + static_cast<unsigned>(*p - '0');
    }
    if (workerCount < 1 || workerCount > 32) return 0;

    std::vector<Result> results(workerCount);
    std::vector<std::thread> threads;
    threads.reserve(workerCount - 1);

    const u64 quotient = walkerCount / workerCount;
    const u64 remainder = walkerCount % workerCount;

    const auto work = [&](unsigned worker) {
        const u64 first =
            quotient * worker + std::min<u64>(worker, remainder);
        u64 remaining = quotient + static_cast<u64>(worker < remainder);
        u64 index = first;
        Result local;

        while (remaining >= 4) {
            simulateBatch<4>(index, steps, bound, seed, local);
            index += 4;
            remaining -= 4;
        }

        switch (remaining) {
        case 3:
            simulateBatch<3>(index, steps, bound, seed, local);
            break;
        case 2:
            simulateBatch<2>(index, steps, bound, seed, local);
            break;
        case 1:
            simulateBatch<1>(index, steps, bound, seed, local);
            break;
        default:
            break;
        }

        results[worker] = local;
    };

    for (unsigned worker = 1; worker < workerCount; ++worker) {
        threads.emplace_back(work, worker);
    }
    work(0);

    for (std::thread& thread : threads) {
        thread.join();
    }

    Result total;
    for (const Result& result : results) {
        total.spread += result.spread;
        total.bumps += result.bumps;
        total.returns += result.returns;

        if (result.farthestDistance > total.farthestDistance ||
            (result.farthestDistance == total.farthestDistance &&
             result.farthestIndex < total.farthestIndex)) {
            total.farthestDistance = result.farthestDistance;
            total.farthestIndex = result.farthestIndex;
        }
    }

    std::cout << "spread " << total.spread << '\n'
              << "bumps " << total.bumps << '\n'
              << "returns " << total.returns << '\n'
              << "farthest " << total.farthestIndex << ' '
              << total.farthestDistance << '\n';
    return 0;
}
