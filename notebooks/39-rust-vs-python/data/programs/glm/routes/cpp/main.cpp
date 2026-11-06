#include <cstdio>
#include <cstdint>
#include <cstring>
#include <climits>
#include <vector>
#include <io.h>
#include <fcntl.h>

using namespace std;

static inline long long nextInt(const unsigned char*& p, const unsigned char* end) {
    while (p < end && (*p < '0' || *p > '9')) ++p;
    long long v = 0;
    while (p < end && *p >= '0' && *p <= '9') {
        v = v * 10 + (*p - '0');
        ++p;
    }
    return v;
}

static unsigned char* obuf;
static size_t opos = 0, ocap = 0;

static inline void ensure(size_t need) {
    if (opos + need > ocap) {
        ocap = ocap ? ocap * 2 : (1u << 20);
        while (opos + need > ocap) ocap *= 2;
        obuf = (unsigned char*)realloc(obuf, ocap);
    }
}

static inline void writeU64(unsigned long long v, char sep) {
    ensure(24);
    char tmp[20];
    int n = 0;
    do { tmp[n++] = char('0' + v % 10); v /= 10; } while (v);
    while (n) obuf[opos++] = tmp[--n];
    obuf[opos++] = sep;
}

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    _setmode(_fileno(stdout), _O_BINARY);
    FILE* f = fopen(argv[1], "rb");
    if (!f) return 1;
    fseek(f, 0, SEEK_END);
    long sz = ftell(f);
    fseek(f, 0, SEEK_SET);
    vector<unsigned char> data((size_t)sz + 1);
    size_t got = fread(data.data(), 1, (size_t)sz, f);
    fclose(f);
    const unsigned char* p = data.data();
    const unsigned char* end = p + got;

    const long long N = nextInt(p, end);
    const long long M = nextInt(p, end);
    const long long Q = nextInt(p, end);

    vector<int> eu(M), ev(M), ew(M);
    for (long long i = 0; i < M; ++i) {
        eu[i] = (int)nextInt(p, end);
        ev[i] = (int)nextInt(p, end);
        ew[i] = (int)nextInt(p, end);
    }
    vector<int> src(Q);
    for (long long i = 0; i < Q; ++i) src[i] = (int)nextInt(p, end);

    // CSR adjacency (self-loops are useless, skip them)
    vector<int> off(N + 1, 0);
    for (long long i = 0; i < M; ++i) {
        if (eu[i] != ev[i]) { ++off[eu[i]]; ++off[ev[i]]; }
    }
    int run = 0;
    for (long long v = 0; v < N; ++v) { int d = off[v]; off[v] = run; run += d; }
    off[N] = run;
    vector<int> adj(run), wt(run);
    {
        vector<int> pos(off.begin(), off.end() - 1);
        for (long long i = 0; i < M; ++i) {
            int u = eu[i], v = ev[i], w = ew[i];
            if (u == v) continue;
            adj[pos[u]] = v; wt[pos[u]] = w; ++pos[u];
            adj[pos[v]] = u; wt[pos[v]] = w; ++pos[v];
        }
    }

    const long long INF = LLONG_MAX / 4;
    vector<long long> dist(N, INF);
    const size_t hcap = (size_t)(2 * M + 16);
    vector<long long> hd;
    vector<int> hn;
    hd.reserve(hcap);
    hn.reserve(hcap);

    auto hpush = [&](long long d, int v) {
        size_t i = hd.size();
        hd.push_back(d);
        hn.push_back(v);
        while (i > 0) {
            size_t par = (i - 1) >> 2;
            if (hd[par] <= d) break;
            hd[i] = hd[par]; hn[i] = hn[par];
            i = par;
        }
        hd[i] = d; hn[i] = v;
    };

    ensure(1u << 20);

    for (long long qi = 0; qi < Q; ++qi) {
        int s = src[qi];
        for (long long v = 0; v < N; ++v) dist[v] = INF;
        hd.clear(); hn.clear();
        dist[s] = 0;
        hpush(0, s);
        long long total = 0, far = -1;
        long long cnt = 0, farNode = s;
        while (!hd.empty()) {
            long long d = hd[0];
            int v = hn[0];
            size_t last = hd.size() - 1;
            long long d0 = hd[last]; int v0 = hn[last];
            hd[0] = d0; hn[0] = v0;
            hd.pop_back(); hn.pop_back();
            size_t i = 0, n = hd.size();
            while (n > 0) {
                size_t c = 4 * i + 1, m = i;
                long long mv = d0;
                size_t e = c + 4 < n ? c + 4 : n;
                for (size_t j = c; j < e; ++j) {
                    if (hd[j] < mv) { mv = hd[j]; m = j; }
                }
                if (m == i) break;
                hd[i] = mv; hn[i] = hn[m];
                i = m;
            }
            if (n > 0) { hd[i] = d0; hn[i] = v0; }
            if (d != dist[v]) continue;
            // v is finalized
            ++cnt;
            total += d;
            if (d > far || (d == far && v < farNode)) { far = d; farNode = v; }
            for (int e = off[v]; e < off[v + 1]; ++e) {
                int to = adj[e];
                long long nd = d + wt[e];
                if (nd < dist[to]) {
                    dist[to] = nd;
                    hpush(nd, to);
                }
            }
        }
        writeU64((unsigned long long)s, ' ');
        writeU64((unsigned long long)cnt, ' ');
        writeU64((unsigned long long)total, ' ');
        writeU64((unsigned long long)far, ' ');
        writeU64((unsigned long long)farNode, '\n');
    }

    fwrite(obuf, 1, opos, stdout);
    return 0;
}
