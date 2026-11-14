#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    FILE* f = std::fopen(argv[1], "rb");
    if (!f) return 1;
    std::fseek(f, 0, SEEK_END);
    long fsize = std::ftell(f);
    std::fseek(f, 0, SEEK_SET);
    std::vector<char> data((size_t)fsize + 1);
    size_t got = std::fread(data.data(), 1, (size_t)fsize, f);
    std::fclose(f);
    data[got] = '\0';

    // Parse header H W S
    const char* p = data.data();
    auto parseInt = [&]() -> long long {
        while (*p==' '||*p=='\t'||*p=='\r'||*p=='\n') ++p;
        long long v = 0;
        while (*p >= '0' && *p <= '9') v = v*10 + (*p++ - '0');
        return v;
    };
    int H = (int)parseInt();
    int W = (int)parseInt();
    int S = (int)parseInt();
    // skip to end of header line
    while (*p && *p != '\n') ++p;
    if (*p=='\n') ++p;

    int N = H * W;
    std::vector<char> grid((size_t)N);
    int gi = 0;
    for (const char* q = p; gi < N && *q; ++q) {
        char c = *q;
        if (c=='.'||c=='#'||(c>='1'&&c<='9')) grid[(size_t)gi++] = c;
    }

    std::vector<int> bufA((size_t)N, 0), bufB((size_t)N, 0);
    for (int i = 0; i < N; ++i) {
        char c = grid[(size_t)i];
        if (c>='1'&&c<='9') { int v = 1000*(c-'0'); bufA[(size_t)i]=v; bufB[(size_t)i]=v; }
    }

    // Classify open cells: interior runs (all 4 neighbours valid) vs specials.
    std::vector<int> runs;    // pairs start,len
    std::vector<int> spec;    // 5 per: idx,up,down,left,right (missing = idx)
    std::vector<int> openIdx;
    openIdx.reserve((size_t)N);
    runs.reserve((size_t)H*4);
    for (int r = 0; r < H; ++r) {
        int runStart = -1;
        for (int c = 0; c < W; ++c) {
            int i = r*W + c;
            if (grid[(size_t)i] != '.') {
                if (runStart >= 0) { runs.push_back(runStart); runs.push_back(i - runStart); runStart = -1; }
                continue;
            }
            openIdx.push_back(i);
            bool interior = r>0 && r<H-1 && c>0 && c<W-1
                && grid[(size_t)(i-W)]!='#' && grid[(size_t)(i+W)]!='#'
                && grid[(size_t)(i-1)]!='#' && grid[(size_t)(i+1)]!='#';
            if (interior) {
                if (runStart < 0) runStart = i;
            } else {
                if (runStart >= 0) { runs.push_back(runStart); runs.push_back(i - runStart); runStart = -1; }
                int up = (r>0   && grid[(size_t)(i-W)]!='#') ? i-W : i;
                int dn = (r<H-1 && grid[(size_t)(i+W)]!='#') ? i+W : i;
                int lf = (c>0   && grid[(size_t)(i-1)]!='#') ? i-1 : i;
                int rt = (c<W-1 && grid[(size_t)(i+1)]!='#') ? i+1 : i;
                spec.push_back(i); spec.push_back(up); spec.push_back(dn); spec.push_back(lf); spec.push_back(rt);
            }
        }
        if (runStart >= 0) { runs.push_back(runStart); runs.push_back(r*W+W - runStart); }
    }

    int* cur = bufA.data();
    int* nxt = bufB.data();
    const int* runPtr = runs.data();
    int nRuns = (int)(runs.size()/2);
    const int* specPtr = spec.data();
    int nSpec = (int)(spec.size()/5);

    for (int step = 0; step < S; ++step) {
        for (int ri = 0; ri < nRuns; ++ri) {
            int start = runPtr[ri*2];
            int len = runPtr[ri*2+1];
            int* __restrict np = nxt + start;
            const int* __restrict cp = cur + start;
            const int* __restrict up = cp - W;
            const int* __restrict dn = cp + W;
            for (int k = 0; k < len; ++k) {
                np[k] = (4*cp[k] + up[k] + dn[k] + cp[k-1] + cp[k+1]) >> 3;
            }
        }
        for (int si = 0; si < nSpec; ++si) {
            const int* s = specPtr + si*5;
            int i = s[0];
            nxt[i] = (4*cur[i] + cur[s[1]] + cur[s[2]] + cur[s[3]] + cur[s[4]]) >> 3;
        }
        int* t = cur; cur = nxt; nxt = t;
    }

    long long sum = 0, checksum = 0;
    int best = -1, bestIdx = openIdx.empty()?0:openIdx[0];
    for (int i : openIdx) {
        int v = cur[i];
        sum += v;
        checksum += (long long)v * (long long)(i + 1);
        if (v > best) { best = v; bestIdx = i; }
    }
    int br = W ? bestIdx / W : 0, bc = W ? bestIdx % W : 0;
    if (best < 0) best = 0;
    std::printf("sum %lld\nmax %d %d %d\nchecksum %lld\n", sum, best, br, bc, checksum);
    return 0;
}
