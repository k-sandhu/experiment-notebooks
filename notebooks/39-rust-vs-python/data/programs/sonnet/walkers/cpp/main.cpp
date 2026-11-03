#include <cstdio>
#include <cstdlib>
#include <cstdint>
#include <thread>
#include <vector>
#include <algorithm>

struct Res { long long spread, bumps, returns, dist; };

static const int DX[4] = {1, -1, 0, 0};
static const int DY[4] = {0, 0, 1, -1};

static void walk(uint64_t seed, long long j, long long L, int B, Res& out) {
    uint64_t state = seed + (uint64_t)j;
    int x = 0, y = 0;
    long long bumps = 0, returns = 0;
    const unsigned span = 2u * (unsigned)B;
    for (long long i = 0; i < L; i++) {
        state += 0x9E3779B97F4A7C15ULL;
        uint64_t z = state;
        z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
        z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
        unsigned d = (unsigned)(z >> 62);
        int nx = x + DX[d], ny = y + DY[d];
        if ((unsigned)(nx + B) > span || (unsigned)(ny + B) > span) {
            bumps++;
        } else {
            x = nx; y = ny;
            returns += ((x | y) == 0);
        }
    }
    out.spread = (long long)x * x + (long long)y * y;
    out.bumps = bumps;
    out.returns = returns;
    out.dist = std::abs(x) + std::abs(y);
}

int main(int argc, char** argv) {
    if (argc < 3) return 1;
    FILE* f = std::fopen(argv[1], "r");
    if (!f) return 1;
    long long J, L, B;
    unsigned long long seed;
    if (std::fscanf(f, "%lld %lld %lld %llu", &J, &L, &B, &seed) != 4) return 1;
    std::fclose(f);
    int W = std::atoi(argv[2]);
    if (W < 1) W = 1;
    if ((long long)W > J) W = (int)J;
    std::vector<Res> res((size_t)J);
    auto work = [&](int w) {
        for (long long j = w; j < J; j += W) walk(seed, j, L, (int)B, res[(size_t)j]);
    };
    std::vector<std::thread> th;
    for (int w = 1; w < W; w++) th.emplace_back(work, w);
    work(0);
    for (auto& t : th) t.join();
    long long spread = 0, bumps = 0, returns = 0, bestD = -1, bestJ = 0;
    for (long long j = 0; j < J; j++) {
        spread += res[j].spread; bumps += res[j].bumps; returns += res[j].returns;
        if (res[j].dist > bestD) { bestD = res[j].dist; bestJ = j; }
    }
    std::printf("spread %lld\nbumps %lld\nreturns %lld\nfarthest %lld %lld\n", spread, bumps, returns, bestJ, bestD);
    return 0;
}
