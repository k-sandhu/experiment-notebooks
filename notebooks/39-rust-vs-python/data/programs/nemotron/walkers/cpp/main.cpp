#include <cstdio>
#include <cstdint>
#include <cstdlib>
#include <thread>
#include <vector>

namespace {

constexpr uint64_t C1 = 0x9E3779B97F4A7C15ULL;
constexpr uint64_t C2 = 0xBF58476D1CE4E5B9ULL;
constexpr uint64_t C3 = 0x94D049BB133111EBULL;

struct Result {
    uint64_t spread = 0;
    uint64_t bumps = 0;
    uint64_t returns = 0;
    uint64_t farDist = 0;
    uint64_t farWalker = 0;
};

// SplitMix64: advance state and return the generated 64-bit value.
inline uint64_t next(uint64_t& state) {
    state += C1;
    uint64_t z = state;
    z = (z ^ (z >> 30)) * C2;
    z = (z ^ (z >> 27)) * C3;
    return z ^ (z >> 31);
}

// Simulate walkers [start, end). The reduction is order-independent, so the
// result does not depend on how walkers are split across threads.
Result runRange(uint64_t start, uint64_t end, uint64_t L, uint64_t B, uint64_t seed) {
    Result res;
    if (start < end) res.farWalker = start;  // smallest index in range (tie-break seed)
    static const int DX[4] = {1, -1, 0, 0};
    static const int DY[4] = {0, 0, 1, -1};
    const uint64_t twoB = 2 * B;
    for (uint64_t j = start; j < end; ++j) {
        uint64_t state = seed + j;
        int x = 0, y = 0;
        uint64_t b = 0, r = 0;
        for (uint64_t t = 0; t < L; ++t) {
            uint64_t rnd = next(state);
            unsigned d = static_cast<unsigned>(rnd >> 62);
            int nx = x + DX[d];
            int ny = y + DY[d];
            // |nx| <= B  <=>  0 <= nx + B <= 2B, using one unsigned compare.
            if ((static_cast<uint64_t>(nx + B) <= twoB) &&
                (static_cast<uint64_t>(ny + B) <= twoB)) {
                x = nx;
                y = ny;
                if (x == 0 && y == 0) ++r;
            } else {
                ++b;
            }
        }
        res.spread += static_cast<uint64_t>(x) * x + static_cast<uint64_t>(y) * y;
        res.bumps += b;
        res.returns += r;
        uint64_t dist = static_cast<uint64_t>(x < 0 ? -x : x) +
                        static_cast<uint64_t>(y < 0 ? -y : y);
        if (dist > res.farDist || (dist == res.farDist && j < res.farWalker)) {
            res.farDist = dist;
            res.farWalker = j;
        }
    }
    return res;
}

void merge(Result& into, const Result& other) {
    into.spread += other.spread;
    into.bumps += other.bumps;
    into.returns += other.returns;
    if (other.farDist > into.farDist ||
        (other.farDist == into.farDist && other.farWalker < into.farWalker)) {
        into.farDist = other.farDist;
        into.farWalker = other.farWalker;
    }
}

static const char* skipWs(const char* p) {
    while (*p == ' ' || *p == '\t' || *p == '\n' || *p == '\r' || *p == '\f' || *p == '\v') ++p;
    return p;
}

static uint64_t parseU64(const char*& p) {
    p = skipWs(p);
    uint64_t v = 0;
    while (*p >= '0' && *p <= '9') {
        v = v * 10 + static_cast<uint64_t>(*p - '0');
        ++p;
    }
    return v;
}

}  // namespace

int main(int argc, char** argv) {
    if (argc < 3) {
        std::fputs("usage: solution.exe INPUT_PATH WORKERS\n", stderr);
        return 1;
    }

    FILE* f = std::fopen(argv[1], "rb");
    if (!f) {
        std::fprintf(stderr, "cannot open %s\n", argv[1]);
        return 1;
    }
    std::fseek(f, 0, SEEK_END);
    long size = std::ftell(f);
    std::fseek(f, 0, SEEK_SET);
    char* buf = static_cast<char*>(std::malloc(static_cast<size_t>(size) + 1));
    if (size > 0) std::fread(buf, 1, static_cast<size_t>(size), f);
    buf[size] = '\0';
    std::fclose(f);

    const char* p = buf;
    uint64_t J = parseU64(p);
    uint64_t L = parseU64(p);
    uint64_t B = parseU64(p);
    uint64_t seed = parseU64(p);
    (void)size;
    uint64_t W = static_cast<uint64_t>(std::strtoull(argv[2], nullptr, 10));
    if (W < 1) W = 1;
    if (W > 32) W = 32;

    std::vector<Result> results(W);
    std::vector<std::thread> threads;
    threads.reserve(W);
    for (uint64_t i = 0; i < W; ++i) {
        uint64_t start = i * J / W;
        uint64_t end = (i + 1) * J / W;
        threads.emplace_back([i, start, end, L, B, seed, &results] {
            results[i] = runRange(start, end, L, B, seed);
        });
    }
    for (auto& t : threads) t.join();

    Result total = results[0];
    for (uint64_t i = 1; i < W; ++i) merge(total, results[i]);

    std::printf("spread %llu\nbumps %llu\nreturns %llu\nfarthest %llu %llu\n",
                (unsigned long long)total.spread,
                (unsigned long long)total.bumps,
                (unsigned long long)total.returns,
                (unsigned long long)total.farWalker,
                (unsigned long long)total.farDist);
    std::free(buf);
    return 0;
}
