#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <string>
#include <thread>
#include <vector>
#include <fcntl.h>
#include <io.h>

struct Result {
    long long spread = 0;
    long long bumps = 0;
    long long returns = 0;
    long long bestD = -1;
    long long bestJ = -1;
};

static inline uint64_t splitmix64(uint64_t& state) {
    state += 0x9E3779B97F4A7C15ULL;
    uint64_t z = state;
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
    z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
    return z ^ (z >> 31);
}

static void walkRange(int j0, int j1, uint64_t seed, int64_t L, int64_t B, Result& r) {
    long long spread = 0, bumps = 0, rets = 0;
    long long bestD = -1, bestJ = -1;
    for (int j = j0; j < j1; ++j) {
        uint64_t state = seed + (uint64_t)j;
        long long x = 0, y = 0;
        for (int64_t s = 0; s < L; ++s) {
            uint64_t d = splitmix64(state) >> 62;
            long long dx = (d == 0) - (d == 1);
            long long dy = (d == 2) - (d == 3);
            long long nx = x + dx, ny = y + dy;
            if ((nx > B || nx < -B || ny > B || ny < -B)) {
                ++bumps;
            } else {
                x = nx; y = ny;
                if (x == 0 && y == 0) ++rets;
            }
        }
        spread += x * x + y * y;
        long long D = (x < 0 ? -x : x) + (y < 0 ? -y : y);
        if (D > bestD) { bestD = D; bestJ = j; }
    }
    r.spread = spread; r.bumps = bumps; r.returns = rets;
    r.bestD = bestD; r.bestJ = bestJ;
}

int main(int argc, char** argv) {
    if (argc < 3) return 1;
    _setmode(_fileno(stdout), _O_BINARY);
    FILE* f = nullptr;
    if (fopen_s(&f, argv[1], "rb") != 0 || !f) return 1;
    unsigned long long J, L, B;
    unsigned long long seed;
    if (fscanf_s(f, "%llu %llu %llu %llu", &J, &L, &B, &seed) != 4) { fclose(f); return 1; }
    fclose(f);

    unsigned workers = (unsigned)atoi(argv[2]);
    if (workers == 0) workers = 1;
    if (workers > J) workers = (unsigned)J;

    std::vector<Result> results(workers);
    std::vector<std::thread> threads;
    threads.reserve(workers - 1);
    unsigned long long chunk = (J + workers - 1) / workers;
    for (unsigned w = 0; w < workers; ++w) {
        unsigned long long j0 = w * chunk;
        unsigned long long j1 = j0 + chunk;
        if (j1 > J) j1 = J;
        if (j0 >= j1) break;
        if (w + 1 == workers) {
            walkRange((int)j0, (int)j1, seed, (int64_t)L, (int64_t)B, results[w]);
        } else {
            threads.emplace_back([&, w, j0, j1] {
                walkRange((int)j0, (int)j1, seed, (int64_t)L, (int64_t)B, results[w]);
            });
        }
    }
    for (auto& t : threads) t.join();

    long long spread = 0, bumps = 0, rets = 0, bestD = -1, bestJ = -1;
    for (unsigned w = 0; w < workers; ++w) {
        const Result& r = results[w];
        spread += r.spread; bumps += r.bumps; rets += r.returns;
        if (r.bestJ >= 0 && (bestJ < 0 || r.bestD > bestD)) { bestD = r.bestD; bestJ = r.bestJ; }
    }

    std::string out;
    out.reserve(128);
    out += "spread " + std::to_string(spread) + "\n";
    out += "bumps " + std::to_string(bumps) + "\n";
    out += "returns " + std::to_string(rets) + "\n";
    out += "farthest " + std::to_string(bestJ) + " " + std::to_string(bestD) + "\n";
    fwrite(out.data(), 1, out.size(), stdout);
    return 0;
}
