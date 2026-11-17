// Random walkers: J independent SplitMix64-driven walks inside a box, spread over WORKERS threads.
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <fcntl.h>
#include <io.h>
#include <string>
#include <thread>
#include <vector>

namespace {

constexpr uint64_t kGamma = 0x9E3779B97F4A7C15ULL;

struct Params {
    int64_t walkers;
    int64_t steps;
    int64_t box;
    uint64_t seed;
};

// Totals for one contiguous range of walkers.
struct Partial {
    uint64_t spread = 0;
    int64_t bumps = 0;
    int64_t returns = 0;
    int64_t farDist = -1;
    int64_t farWalker = 0;
};

// Runs walker j to the end of its steps and folds its result into acc.
// The direction is computed arithmetically rather than with a switch, so the
// unpredictable random choice never causes a branch misprediction.
void walkOne(const Params& p, int64_t j, Partial& acc) {
    const int64_t box = p.box;
    uint64_t state = p.seed + static_cast<uint64_t>(j);
    int64_t x = 0;
    int64_t y = 0;
    int64_t bumps = 0;
    int64_t returns = 0;
    for (int64_t i = 0; i < p.steps; ++i) {
        state += kGamma;
        uint64_t z = state;
        z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
        z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
        // z ^ (z >> 31) has the same top two bits as z, so the final mix is skipped.
        const uint64_t d = z >> 62;
        const int64_t isY = static_cast<int64_t>(d >> 1);
        const int64_t sign = 1 - 2 * static_cast<int64_t>(d & 1);
        const int64_t dx = sign * (1 - isY);
        const int64_t dy = sign * isY;
        const int64_t nx = x + dx;
        const int64_t ny = y + dy;
        if (nx < -box || nx > box || ny < -box || ny > box) {
            ++bumps;
        } else {
            x = nx;
            y = ny;
            returns += (x | y) == 0;
        }
    }
    const int64_t dist = (x < 0 ? -x : x) + (y < 0 ? -y : y);
    acc.spread += static_cast<uint64_t>(x * x + y * y);
    acc.bumps += bumps;
    acc.returns += returns;
    // Walkers are visited in increasing order, so a strict comparison keeps the smallest index on a tie.
    if (dist > acc.farDist) {
        acc.farDist = dist;
        acc.farWalker = j;
    }
}

Partial walkRange(const Params& p, int64_t first, int64_t last) {
    Partial acc;
    for (int64_t j = first; j < last; ++j) {
        walkOne(p, j, acc);
    }
    return acc;
}

}  // namespace

int main(int argc, char** argv) {
    if (argc < 2) {
        std::fprintf(stderr, "usage: solution INPUT_PATH [WORKERS]\n");
        return 2;
    }
    std::FILE* f = std::fopen(argv[1], "rb");
    if (!f) {
        std::fprintf(stderr, "cannot open %s\n", argv[1]);
        return 1;
    }
    std::string text;
    char chunk[4096];
    size_t n;
    while ((n = std::fread(chunk, 1, sizeof chunk, f)) > 0) {
        text.append(chunk, n);
    }
    std::fclose(f);

    Params p{};
    char* end = nullptr;
    const char* cur = text.c_str();
    p.walkers = std::strtoll(cur, &end, 10);
    cur = end;
    p.steps = std::strtoll(cur, &end, 10);
    cur = end;
    p.box = std::strtoll(cur, &end, 10);
    cur = end;
    p.seed = std::strtoull(cur, &end, 10);

    long workers = argc >= 3 ? std::strtol(argv[2], nullptr, 10) : 1;
    if (workers < 1) {
        workers = 1;
    }
    if (workers > p.walkers) {
        workers = p.walkers > 0 ? static_cast<long>(p.walkers) : 1;
    }

    // Worker w handles the contiguous walkers [bound(w), bound(w + 1)).
    auto bound = [&](long w) { return p.walkers * w / workers; };
    std::vector<Partial> parts(static_cast<size_t>(workers));
    std::vector<std::thread> threads;
    threads.reserve(static_cast<size_t>(workers));
    for (long w = 1; w < workers; ++w) {
        threads.emplace_back([&, w] { parts[static_cast<size_t>(w)] = walkRange(p, bound(w), bound(w + 1)); });
    }
    parts[0] = walkRange(p, bound(0), bound(1));
    for (std::thread& t : threads) {
        t.join();
    }

    // Parts are in walker order, so the first part holding the maximum also holds the smallest index.
    Partial total;
    for (const Partial& part : parts) {
        total.spread += part.spread;
        total.bumps += part.bumps;
        total.returns += part.returns;
        if (part.farDist > total.farDist) {
            total.farDist = part.farDist;
            total.farWalker = part.farWalker;
        }
    }
    if (total.farDist < 0) {
        total.farDist = 0;
    }

    // Binary mode keeps the output as plain LF line endings.
    _setmode(_fileno(stdout), _O_BINARY);
    char out[256];
    const int len = std::snprintf(out, sizeof out, "spread %llu\nbumps %lld\nreturns %lld\nfarthest %lld %lld\n",
                                  static_cast<unsigned long long>(total.spread),
                                  static_cast<long long>(total.bumps),
                                  static_cast<long long>(total.returns),
                                  static_cast<long long>(total.farWalker),
                                  static_cast<long long>(total.farDist));
    std::fwrite(out, 1, static_cast<size_t>(len), stdout);
    return 0;
}
