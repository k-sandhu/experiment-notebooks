#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <fstream>
#include <string>
#include <thread>
#include <vector>

struct Result {
    std::int64_t spread = 0, bumps = 0, returns = 0;
    std::int64_t walker = 0, distance = -1;
};

static Result simulate(std::int64_t first, std::int64_t end,
                       std::int64_t steps, std::int64_t bound,
                       std::uint64_t seed) {
    Result result;
    for (auto j = first; j < end; ++j) {
        std::uint64_t state = seed + static_cast<std::uint64_t>(j);
        std::int64_t x = 0, y = 0, bumps = 0, returns = 0;
        for (std::int64_t k = 0; k < steps; ++k) {
            auto z = (state += UINT64_C(0x9E3779B97F4A7C15));
            z = (z ^ (z >> 30)) * UINT64_C(0xBF58476D1CE4E5B9);
            z = (z ^ (z >> 27)) * UINT64_C(0x94D049BB133111EB);
            // The final xor shifts by 31, so it cannot change the top two bits.
            const auto d = static_cast<int>(z >> 62);
            const auto axis = d >> 1;
            const auto delta = 1 - 2 * (d & 1);
            // Check before adding, including when bound is INT64_MAX.
            const bool blocked = (axis ? y : x) == (delta > 0 ? bound : -bound);
            bumps += blocked;
            const auto move = delta * !blocked;
            x += move & (axis - 1);
            y += move & -axis;
            returns += (x | y) == 0;
        }
        result.spread += x * x + y * y;
        result.bumps += bumps;
        result.returns += returns;
        const auto distance = (x < 0 ? -x : x) + (y < 0 ? -y : y);
        if (distance > result.distance) {
            result.distance = distance;
            result.walker = j;
        }
    }
    return result;
}

int main(int argc, char** argv) {
    if (argc != 3) return 1;
    std::int64_t walkers, steps, bound;
    std::uint64_t seed;
    std::ifstream input(argv[1]);
    if (!(input >> walkers >> steps >> bound >> seed)) return 1;
    const int workers = std::stoi(argv[2]);
    std::vector<Result> results(workers);
    std::vector<std::thread> threads;
    threads.reserve(workers - 1);
    const auto run = [&](int w) {
        const auto q = walkers / workers, r = walkers % workers;
        const auto first = q * w + std::min<std::int64_t>(w, r);
        results[w] = simulate(first, first + q + (w < r), steps, bound, seed);
    };
    for (int w = 1; w < workers; ++w) threads.emplace_back(run, w);
    run(0);
    for (auto& thread : threads) thread.join();
    Result total;
    for (const auto& result : results) {
        total.spread += result.spread;
        total.bumps += result.bumps;
        total.returns += result.returns;
        if (result.distance > total.distance ||
            (result.distance == total.distance && result.walker < total.walker)) {
            total.distance = result.distance;
            total.walker = result.walker;
        }
    }
    std::printf("spread %lld\nbumps %lld\nreturns %lld\nfarthest %lld %lld\n",
        static_cast<long long>(total.spread), static_cast<long long>(total.bumps),
        static_cast<long long>(total.returns), static_cast<long long>(total.walker),
        static_cast<long long>(std::max<std::int64_t>(0, total.distance)));
}
