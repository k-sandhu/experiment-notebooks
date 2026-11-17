#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <limits>
#include <thread>
#include <vector>

using U64 = std::uint64_t;
using I64 = std::int64_t;

struct alignas(64) Result {
    U64 spread = 0;
    U64 bumps = 0;
    U64 returns = 0;
    U64 farthestId = std::numeric_limits<U64>::max();
    U64 farthestDistance = 0;
};

static __forceinline U64 nextRandom(U64& state) noexcept {
    state += UINT64_C(0x9E3779B97F4A7C15);
    U64 z = state;
    z = (z ^ (z >> 30)) * UINT64_C(0xBF58476D1CE4E5B9);
    z = (z ^ (z >> 27)) * UINT64_C(0x94D049BB133111EB);
    return z ^ (z >> 31);
}

template<class Coordinate>
static __forceinline void interiorStep(
    U64 random, Coordinate& x, Coordinate& y, U64& returns) noexcept
{
    const unsigned direction = static_cast<unsigned>(random >> 62);
    x += static_cast<Coordinate>(direction == 0)
       - static_cast<Coordinate>(direction == 1);
    y += static_cast<Coordinate>(direction == 2)
       - static_cast<Coordinate>(direction == 3);
    returns += static_cast<U64>((x == 0) & (y == 0));
}

template<class Coordinate>
static void simulate(
    U64 first, U64 last, U64 length, Coordinate bound,
    U64 seed, Result& output) noexcept
{
    Result result;

    for (U64 walker = first; walker < last; ++walker) {
        U64 state = seed + walker;
        U64 remaining = length;
        Coordinate x = 0;
        Coordinate y = 0;
        U64 returns = 0;
        U64 bumps = 0;

        while (remaining != 0) {
            const Coordinate ax = x < 0 ? -x : x;
            const Coordinate ay = y < 0 ? -y : y;
            const U64 room = static_cast<U64>(
                bound - (ax > ay ? ax : ay));

            if (room != 0) {
                // Every move in this batch is guaranteed to remain in the box.
                U64 count = std::min(room, remaining);
                remaining -= count;

                while (count >= 4) {
                    const U64 r0 = nextRandom(state);
                    const U64 r1 = nextRandom(state);
                    const U64 r2 = nextRandom(state);
                    const U64 r3 = nextRandom(state);

                    interiorStep(r0, x, y, returns);
                    interiorStep(r1, x, y, returns);
                    interiorStep(r2, x, y, returns);
                    interiorStep(r3, x, y, returns);
                    count -= 4;
                }

                while (count != 0) {
                    interiorStep(nextRandom(state), x, y, returns);
                    --count;
                }
            } else {
                const unsigned direction =
                    static_cast<unsigned>(nextRandom(state) >> 62);

                switch (direction) {
                case 0:
                    if (x == bound) {
                        ++bumps;
                    } else {
                        ++x;
                    }
                    break;
                case 1:
                    if (x == -bound) {
                        ++bumps;
                    } else {
                        --x;
                    }
                    break;
                case 2:
                    if (y == bound) {
                        ++bumps;
                    } else {
                        ++y;
                    }
                    break;
                default:
                    if (y == -bound) {
                        ++bumps;
                    } else {
                        --y;
                    }
                    break;
                }

                // Since bound >= 1, a bump cannot occur at the origin.
                returns += static_cast<U64>((x == 0) & (y == 0));
                --remaining;
            }
        }

        const U64 ax = static_cast<U64>(x < 0 ? -x : x);
        const U64 ay = static_cast<U64>(y < 0 ? -y : y);
        const U64 distance = ax + ay;

        result.spread += ax * ax + ay * ay;
        result.bumps += bumps;
        result.returns += returns;

        if (distance > result.farthestDistance ||
            (distance == result.farthestDistance &&
             walker < result.farthestId)) {
            result.farthestDistance = distance;
            result.farthestId = walker;
        }
    }

    output = result;
}

int main(int argc, char* argv[]) {
    if (argc != 3) {
        return 0;
    }

    std::ifstream input(argv[1]);
    U64 walkers, length, seed;
    I64 bound;

    if (!(input >> walkers >> length >> bound >> seed)) {
        return 0;
    }

    const unsigned workers = static_cast<unsigned>(std::atoi(argv[2]));
    if (workers < 1 || workers > 32) {
        return 0;
    }

    std::array<Result, 32> results{};
    std::vector<std::thread> threads;
    threads.reserve(workers - 1);

    const U64 quotient = walkers / workers;
    const U64 remainder = walkers % workers;

    const auto runWorker = [&](unsigned worker) {
        const U64 first =
            quotient * worker + std::min<U64>(worker, remainder);
        const U64 last = first + quotient + (worker < remainder ? 1 : 0);

        if (bound <= std::numeric_limits<std::int32_t>::max()) {
            simulate<std::int32_t>(
                first, last, length, static_cast<std::int32_t>(bound),
                seed, results[worker]);
        } else {
            simulate<I64>(
                first, last, length, bound, seed, results[worker]);
        }
    };

    for (unsigned worker = 1; worker < workers; ++worker) {
        threads.emplace_back(runWorker, worker);
    }

    runWorker(0);

    for (std::thread& thread : threads) {
        thread.join();
    }

    Result total;
    for (unsigned worker = 0; worker < workers; ++worker) {
        const Result& result = results[worker];
        total.spread += result.spread;
        total.bumps += result.bumps;
        total.returns += result.returns;

        if (result.farthestDistance > total.farthestDistance ||
            (result.farthestDistance == total.farthestDistance &&
             result.farthestId < total.farthestId)) {
            total.farthestDistance = result.farthestDistance;
            total.farthestId = result.farthestId;
        }
    }

    std::cout << "spread " << total.spread << '\n'
              << "bumps " << total.bumps << '\n'
              << "returns " << total.returns << '\n'
              << "farthest " << total.farthestId << ' '
              << total.farthestDistance << '\n';

    return 0;
}
