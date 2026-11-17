#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <thread>
#include <vector>
#include <algorithm>
#include <io.h>
#include <fcntl.h>

struct Partial {
    alignas(64) long long spread = 0;
    long long bumps = 0;
    long long returns = 0;
    long long bestD = -1;
    long long bestJ = 0;
    char pad[64 - 40 > 0 ? 64 - 40 : 1];
};

static long long Jg;
static long long Lg;
static int Bg;
static uint64_t SEEDg;

static void run_chunk(long long start, long long end, Partial* out) {
    static const int DX[4] = {1, -1, 0, 0};
    static const int DY[4] = {0, 0, 1, -1};
    const int B = Bg;
    const long long L = Lg;
    long long spread = 0, bumps = 0, returns = 0;
    long long bestD = -1, bestJ = start;
    for (long long j = start; j < end; ++j) {
        uint64_t state = SEEDg + (uint64_t)j;
        int x = 0, y = 0;
        long long b = 0, r = 0;
        for (long long i = 0; i < L; ++i) {
            state += 0x9E3779B97F4A7C15ULL;
            uint64_t z = state;
            z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
            z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
            uint64_t rr = z ^ (z >> 31);
            unsigned d = (unsigned)(rr >> 62);
            int nx = x + DX[d];
            int ny = y + DY[d];
            bool outb = (nx > B) | (nx < -B) | (ny > B) | (ny < -B);
            b += outb;
            x = outb ? x : nx;
            y = outb ? y : ny;
            r += (!outb) & (x == 0) & (y == 0);
        }
        bumps += b; returns += r;
        spread += (long long)x * x + (long long)y * y;
        long long dist = (long long)(x >= 0 ? x : -x) + (y >= 0 ? y : -y);
        if (dist > bestD) { bestD = dist; bestJ = j; }
    }
    out->spread = spread; out->bumps = bumps; out->returns = returns;
    out->bestD = bestD; out->bestJ = bestJ;
}

int main(int argc, char** argv) {
    _setmode(_fileno(stdout), _O_BINARY);
    if (argc < 2) return 1;
    int workers = 1;
    if (argc >= 3) workers = std::atoi(argv[2]);
    if (workers < 1) workers = 1;
    if (workers > 32) workers = 32;

    FILE* f = nullptr;
    fopen_s(&f, argv[1], "rb");
    if (!f) return 1;
    char buf[4096];
    size_t n = std::fread(buf, 1, sizeof(buf) - 1, f);
    std::fclose(f);
    buf[n] = 0;
    // parse J L B SEED : first three signed, seed unsigned
    const char* p = buf;
    auto parseSigned = [&]() -> long long {
        while (*p==' '||*p=='\n'||*p=='\r'||*p=='\t') ++p;
        bool neg=false; if(*p=='-'){neg=true;++p;}
        long long v=0; while(*p>='0'&&*p<='9'){v=v*10+(*p-'0');++p;}
        return neg?-v:v;
    };
    Jg = parseSigned(); Lg = parseSigned(); long long Bll = parseSigned();
    Bg = (int)Bll;
    while (*p==' '||*p=='\n'||*p=='\r'||*p=='\t') ++p;
    uint64_t seed=0; while(*p>='0'&&*p<='9'){seed=seed*10+(uint64_t)(*p-'0');++p;}
    SEEDg = seed;

    if (Jg <= 0) {
        std::printf("spread 0\nbumps 0\nreturns 0\nfarthest 0 0\n");
        return 0;
    }
    if (workers > Jg) workers = (int)Jg;
    std::vector<Partial> parts((size_t)workers);
    if (workers == 1) {
        run_chunk(0, Jg, &parts[0]);
    } else {
        std::vector<std::thread> th;
        th.reserve((size_t)workers-1);
        long long base = Jg / workers, rem = Jg % workers;
        long long s = 0;
        for (int w = 0; w < workers; ++w) {
            long long cnt = base + (w < rem ? 1 : 0);
            long long st = s, en = s + cnt; s = en;
            if (w == workers - 1) {
                run_chunk(st, en, &parts[(size_t)w]);
            } else {
                th.emplace_back([st,en,w,&parts]{ run_chunk(st,en,&parts[(size_t)w]); });
            }
        }
        for (auto& t: th) t.join();
    }
    long long spread=0, bumps=0, returns=0, bestD=-1, bestJ=0;
    for (int w=0;w<workers;++w){
        spread+=parts[(size_t)w].spread; bumps+=parts[(size_t)w].bumps; returns+=parts[(size_t)w].returns;
        if (parts[(size_t)w].bestD > bestD) { bestD=parts[(size_t)w].bestD; bestJ=parts[(size_t)w].bestJ; }
    }
    if (bestD<0) bestD=0;
    std::printf("spread %lld\nbumps %lld\nreturns %lld\nfarthest %lld %lld\n", spread, bumps, returns, bestJ, bestD);
    return 0;
}
