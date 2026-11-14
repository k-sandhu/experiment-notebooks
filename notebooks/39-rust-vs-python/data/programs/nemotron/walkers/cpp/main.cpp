#include <cstdint>
#include <cstdio>
#include <thread>
#include <vector>

using u64 = uint64_t;

struct Result {
    u64 spread;
    u64 bumps;
    u64 returns;
    u64 farDist;
    u64 farIdx;
};

// Simulate walkers [start, end) and write partial results to out.
// Two independent walker chains are interleaved in the step loop to hide the
// RNG dependency-chain latency; the move is branchless because the random
// direction makes direction branches unpredictable.
static void runChunk(u64 start, u64 end, u64 L, u64 B, u64 seed, Result* out) {
    const long long b = static_cast<long long>(B);
    u64 spread = 0, bumps = 0, returns = 0;
    u64 farDist = 0, farIdx = start;
    auto doStep = [&](u64& state, long long& x, long long& y, u64& b2, u64& r2) {
        state += 0x9E3779B97F4A7C15ULL;
        u64 z = state;
        z ^= z >> 30;
        z *= 0xBF58476D1CE4E5B9ULL;
        z ^= z >> 27;
        z *= 0x94D049BB133111EBULL;
        u64 r = z ^ (z >> 31);
        unsigned d = static_cast<unsigned>(r >> 62);
        int take0 = (d == 0) & (x < b);
        int take1 = (d == 1) & (x > -b);
        int take2 = (d == 2) & (y < b);
        int take3 = (d == 3) & (y > -b);
        int take = take0 | take1 | take2 | take3;
        x += take0 - take1;
        y += take2 - take3;
        b2 += (unsigned)!take;
        r2 += (unsigned)(take & (x == 0) & (y == 0));
    };
    u64 j = start;
    for (; j + 1 < end; j += 2) {
        u64 s0 = seed + j, s1 = seed + j + 1;
        long long x0 = 0, y0 = 0, x1 = 0, y1 = 0;
        u64 b0 = 0, b1 = 0, r0 = 0, r1 = 0;
        for (u64 s = L; s != 0; --s) {
            doStep(s0, x0, y0, b0, r0);
            doStep(s1, x1, y1, b1, r1);
        }
        spread += static_cast<u64>(x0) * x0 + static_cast<u64>(y0) * y0
                + static_cast<u64>(x1) * x1 + static_cast<u64>(y1) * y1;
        bumps += b0 + b1;
        returns += r0 + r1;
        u64 dist0 = static_cast<u64>(x0 < 0 ? -x0 : x0) + static_cast<u64>(y0 < 0 ? -y0 : y0);
        u64 dist1 = static_cast<u64>(x1 < 0 ? -x1 : x1) + static_cast<u64>(y1 < 0 ? -y1 : y1);
        // Strictly greater keeps the smallest walker index on ties.
        if (dist0 > farDist) { farDist = dist0; farIdx = j; }
        if (dist1 > farDist) { farDist = dist1; farIdx = j + 1; }
    }
    if (j < end) {
        u64 state = seed + j;
        long long x = 0, y = 0;
        u64 b2 = 0, r2 = 0;
        for (u64 s = L; s != 0; --s) doStep(state, x, y, b2, r2);
        spread += static_cast<u64>(x) * x + static_cast<u64>(y) * y;
        bumps += b2;
        returns += r2;
        u64 dist = static_cast<u64>(x < 0 ? -x : x) + static_cast<u64>(y < 0 ? -y : y);
        if (dist > farDist) { farDist = dist; farIdx = j; }
    }
    out->spread = spread;
    out->bumps = bumps;
    out->returns = returns;
    out->farDist = farDist;
    out->farIdx = farIdx;
}

static u64 parseU64(const char** p) {
    u64 v = 0;
    while (**p == ' ' || **p == '\t' || **p == '\n' || **p == '\r') ++(*p);
    while (**p >= '0' && **p <= '9') {
        v = v * 10 + (u64)(**p - '0');
        ++(*p);
    }
    return v;
}

int main(int argc, char** argv) {
    if (argc < 3) return 1;
    FILE* f = fopen(argv[1], "rb");
    if (!f) return 1;
    fseek(f, 0, SEEK_END);
    long n = ftell(f);
    fseek(f, 0, SEEK_SET);
    std::vector<char> buf(n + 1);
    if (fread(buf.data(), 1, n, f) != (size_t)n) { fclose(f); return 1; }
    fclose(f);
    buf[n] = '\0';
    const char* p = buf.data();
    u64 J = parseU64(&p);
    u64 L = parseU64(&p);
    u64 B = parseU64(&p);
    u64 seed = parseU64(&p);

    long workers = 0;
    if (argc >= 3) {
        const char* q = argv[2];
        while (*q == ' ' || *q == '\t') ++q;
        while (*q >= '0' && *q <= '9') {
            workers = workers * 10 + (unsigned)(*q - '0');
            ++q;
        }
    }
    if (workers < 1) workers = 1;
    u64 nThreads = (u64)workers;
    if (J != 0 && nThreads > J) nThreads = J;

    std::vector<Result> results(nThreads);
    std::vector<std::thread> threads;
    threads.reserve(nThreads);
    u64 chunk = J != 0 ? (J + nThreads - 1) / nThreads : 0;
    for (u64 i = 0; i < nThreads; ++i) {
        u64 start = i * chunk;
        u64 end = start + chunk;
        if (end > J) end = J;
        if (i + 1 == nThreads) end = J;
        threads.emplace_back(runChunk, start, end, L, B, seed, &results[i]);
    }
    for (auto& t : threads) t.join();

    Result total{0, 0, 0, 0, 0};
    if (!results.empty()) {
        total = results[0];
        for (size_t i = 1; i < results.size(); ++i) {
            const Result& r = results[i];
            total.spread += r.spread;
            total.bumps += r.bumps;
            total.returns += r.returns;
            if (r.farDist > total.farDist ||
                (r.farDist == total.farDist && r.farIdx < total.farIdx)) {
                total.farDist = r.farDist;
                total.farIdx = r.farIdx;
            }
        }
    }

    printf("spread %llu\n", (unsigned long long)total.spread);
    printf("bumps %llu\n", (unsigned long long)total.bumps);
    printf("returns %llu\n", (unsigned long long)total.returns);
    printf("farthest %llu %llu\n", (unsigned long long)total.farIdx, (unsigned long long)total.farDist);
    return 0;
}
