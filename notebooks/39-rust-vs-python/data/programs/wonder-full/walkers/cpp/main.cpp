#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <thread>
#include <vector>
#include <algorithm>

struct Partial {
    int64_t spread = 0;
    int64_t bumps = 0;
    int64_t returns = 0;
    int64_t farIdx = 0;
    int64_t farDist = -1;
    char pad[24];
};

static inline uint64_t rngDir(uint64_t state) {
    uint64_t z = state;
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ull;
    z = (z ^ (z >> 27)) * 0x94D049BB133111EBull;
    return z >> 62; // top bits of z ^ (z>>31) are z's
}

static void runRange(int64_t begin, int64_t end, int64_t L, int B, uint64_t seed, Partial &out) {
    const uint64_t GOLD = 0x9E3779B97F4A7C15ull;
    int64_t spread = 0, bumps = 0, returns = 0;
    int64_t farIdx = begin, farDist = -1;
    // Direction deltas for d=0..3. Coordinates are offset by +B into
    // unsigned [0, 2B], so one unsigned compare per axis detects a bump.
    static const int DX[4] = {1, -1, 0, 0};
    static const int DY[4] = {0, 0, 1, -1};
    const unsigned UB = (unsigned)B * 2u;
    const unsigned ORG = (unsigned)B;
    for (int64_t j = begin; j < end; ++j) {
        uint64_t state = seed + (uint64_t)j;
        unsigned ux = ORG, uy = ORG;
        int64_t b = 0, r = 0;
        int64_t i = 0;
        // Unrolled by 4: the four RNG chains are independent (states are an
        // arithmetic progression), so the CPU can overlap the multiplies.
        int64_t L4 = L & ~3LL;
        for (; i < L4; i += 4) {
            uint64_t s0 = state + GOLD;
            uint64_t s1 = s0 + GOLD;
            uint64_t s2 = s1 + GOLD;
            uint64_t s3 = s2 + GOLD;
            state = s3;
            unsigned d0 = (unsigned)rngDir(s0);
            unsigned d1 = (unsigned)rngDir(s1);
            unsigned d2 = (unsigned)rngDir(s2);
            unsigned d3 = (unsigned)rngDir(s3);
            // Apply moves in order; the bump branch is well predicted.
            {
                unsigned nx = ux + (unsigned)DX[d0], ny = uy + (unsigned)DY[d0];
                if (nx > UB || ny > UB) ++b;
                else { ux = nx; uy = ny; if (ux == ORG && uy == ORG) ++r; }
            }
            {
                unsigned nx = ux + (unsigned)DX[d1], ny = uy + (unsigned)DY[d1];
                if (nx > UB || ny > UB) ++b;
                else { ux = nx; uy = ny; if (ux == ORG && uy == ORG) ++r; }
            }
            {
                unsigned nx = ux + (unsigned)DX[d2], ny = uy + (unsigned)DY[d2];
                if (nx > UB || ny > UB) ++b;
                else { ux = nx; uy = ny; if (ux == ORG && uy == ORG) ++r; }
            }
            {
                unsigned nx = ux + (unsigned)DX[d3], ny = uy + (unsigned)DY[d3];
                if (nx > UB || ny > UB) ++b;
                else { ux = nx; uy = ny; if (ux == ORG && uy == ORG) ++r; }
            }
        }
        for (; i < L; ++i) {
            state += GOLD;
            unsigned d = (unsigned)rngDir(state);
            unsigned nx = ux + (unsigned)DX[d], ny = uy + (unsigned)DY[d];
            if (nx > UB || ny > UB) ++b;
            else { ux = nx; uy = ny; if (ux == ORG && uy == ORG) ++r; }
        }
        bumps += b; returns += r;
        int64_t x = (int64_t)ux - B, y = (int64_t)uy - B;
        spread += x * x + y * y;
        int64_t dist = (x < 0 ? -x : x) + (y < 0 ? -y : y);
        if (dist > farDist) { farDist = dist; farIdx = j; }
    }
    out.spread = spread; out.bumps = bumps; out.returns = returns;
    out.farIdx = farIdx; out.farDist = farDist;
}

int main(int argc, char **argv) {
    if (argc < 2) return 1;
    FILE *f = std::fopen(argv[1], "rb");
    if (!f) return 1;
    char buf[256];
    size_t n = std::fread(buf, 1, sizeof(buf) - 1, f);
    std::fclose(f);
    buf[n] = 0;
    // Parse "J L B SEED" (SEED unsigned 64).
    const char *p = buf;
    auto parseULL = [&]() -> uint64_t {
        while (*p == ' ' || *p == '\t' || *p == '\r' || *p == '\n') ++p;
        uint64_t v = 0;
        while (*p >= '0' && *p <= '9') { v = v * 10 + (uint64_t)(*p - '0'); ++p; }
        return v;
    };
    int64_t J = (int64_t)parseULL();
    int64_t L = (int64_t)parseULL();
    uint64_t Bv = parseULL();
    uint64_t seed = parseULL();
    int B = Bv > 2147483647ull ? 2147483647 : (int)Bv;

    int workers;
    if (argc >= 3) workers = std::atoi(argv[2]);
    else {
        unsigned hc = std::thread::hardware_concurrency();
        workers = hc ? (int)hc : 1;
    }
    if (workers < 1) workers = 1;
    if (workers > 32) workers = 32;
    if (J > 0 && workers > J) workers = (int)J;
    if (workers < 1) workers = 1;

    std::vector<Partial> parts(workers);
    if (J <= 0) {
        std::printf("spread 0\nbumps 0\nreturns 0\nfarthest 0 0\n");
        return 0;
    }
    if (workers == 1) {
        runRange(0, J, L, B, seed, parts[0]);
    } else {
        std::vector<std::thread> th;
        th.reserve(workers - 1);
        int64_t base = J / workers, rem = J % workers;
        int64_t start = 0;
        std::vector<std::pair<int64_t,int64_t>> ranges(workers);
        for (int w = 0; w < workers; ++w) {
            int64_t cnt = base + (w < rem ? 1 : 0);
            ranges[w] = {start, start + cnt};
            start += cnt;
        }
        for (int w = 1; w < workers; ++w) {
            th.emplace_back([&, w]() { runRange(ranges[w].first, ranges[w].second, L, B, seed, parts[w]); });
        }
        runRange(ranges[0].first, ranges[0].second, L, B, seed, parts[0]);
        for (auto &t : th) t.join();
    }
    int64_t spread = 0, bumps = 0, returns = 0, farIdx = 0, farDist = -1;
    for (auto &pt : parts) {
        spread += pt.spread; bumps += pt.bumps; returns += pt.returns;
        if (pt.farDist > farDist) { farDist = pt.farDist; farIdx = pt.farIdx; }
    }
    if (farDist < 0) farDist = 0;
    std::printf("spread %lld\nbumps %lld\nreturns %lld\nfarthest %lld %lld\n",
                (long long)spread, (long long)bumps, (long long)returns,
                (long long)farIdx, (long long)farDist);
    return 0;
}
