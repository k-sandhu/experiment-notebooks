#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cstdint>
#include <string>
#include <vector>
#include <intrin.h>
static inline int ctz64(uint64_t x) { unsigned long i; _BitScanForward64(&i, x); return (int)i; }

static inline int parseInt(const unsigned char*& p, const unsigned char* end) {
    while (p < end && (*p < '0' || *p > '9')) ++p;
    int v = 0;
    while (p < end && *p >= '0' && *p <= '9') { v = v * 10 + (*p - '0'); ++p; }
    return v;
}

int main(int argc, char** argv) {
    if (argc < 2) return 0;
    FILE* f = fopen(argv[1], "rb");
    if (!f) return 1;
    fseek(f, 0, SEEK_END);
    long fsz = ftell(f);
    fseek(f, 0, SEEK_SET);
    std::vector<unsigned char> buf((size_t)fsz);
    if (fsz > 0) { if (fread(buf.data(), 1, (size_t)fsz, f) != (size_t)fsz) {} }
    fclose(f);
    const unsigned char* p = buf.data();
    const unsigned char* end = p + buf.size();
    if (p >= end) return 0;
    int N = parseInt(p, end);
    int M = parseInt(p, end);
    int Q = parseInt(p, end);

    std::vector<int> eu((size_t)M), ev((size_t)M), ew((size_t)M);
    std::vector<int> deg((size_t)N, 0);
    int ecnt = 0;
    for (int i = 0; i < M; ++i) {
        int u = parseInt(p, end);
        int v = parseInt(p, end);
        int w = parseInt(p, end);
        if (u == v) continue;
        eu[ecnt] = u; ev[ecnt] = v; ew[ecnt] = w; ++ecnt;
        deg[u]++; deg[v]++;
    }
    std::vector<int> sources((size_t)Q);
    for (int i = 0; i < Q; ++i) sources[i] = parseInt(p, end);
    buf.clear(); buf.shrink_to_fit();

    std::vector<int> off((size_t)N + 1, 0);
    for (int i = 0; i < N; ++i) off[i + 1] = off[i] + deg[i];
    int E2 = off[N];
    std::vector<int> adj((size_t)E2);
    {
        std::vector<int> cur(off.begin(), off.end() - 1);
        // cur size N, copy of off[0..N-1]
        for (int i = 0; i < ecnt; ++i) {
            int u = eu[i], v = ev[i], w = ew[i];
            adj[cur[u]++] = (v << 10) | w;
            adj[cur[v]++] = (u << 10) | w;
        }
    }
    eu.clear(); ev.clear(); ew.clear(); deg.clear();

    const int INF = 0x3f3f3f3f;
    const int B = 1024;
    std::vector<int> dist((size_t)N);
    std::vector<int> nxt((size_t)N), prv((size_t)N);
    std::vector<unsigned char> done((size_t)N);
    int head[B];
    uint64_t words[16];

    int* distP = dist.data();
    int* nxtP = nxt.data();
    int* prvP = prv.data();
    unsigned char* doneP = done.data();
    int* offP = off.data();
    int* adjP = adj.data();

    std::string out;
    out.reserve((size_t)Q * 40);

    // cache for duplicate sources: small Q, linear scan
    struct Res { int s; long long R, tot, far; int node; };
    Res cache[64]; int cacheN = 0;

    char line[128];
    for (int qi = 0; qi < Q; ++qi) {
        int s = sources[qi];
        bool hit = false; Res cr{};
        for (int i = 0; i < cacheN; ++i) if (cache[i].s == s) { cr = cache[i]; hit = true; break; }
        long long R, tot, far; int farNode;
        if (hit) { R = cr.R; tot = cr.tot; far = cr.far; farNode = cr.node; }
        else {
            std::fill(dist.begin(), dist.end(), INF);
            std::fill(done.begin(), done.end(), (unsigned char)0);
            for (int i = 0; i < B; ++i) head[i] = -1;
            for (int i = 0; i < 16; ++i) words[i] = 0;
            distP[s] = 0;
            head[0] = s; nxtP[s] = -1; prvP[s] = -1; words[0] = 1ULL;
            long long inq = 1;
            int curDist = 0, curB = 0;
            R = 0; tot = 0; far = 0; farNode = s;
            while (inq > 0) {
                int node = head[curB];
                head[curB] = -1;
                words[curB >> 6] &= ~(1ULL << (curB & 63));
                while (node != -1) {
                    int nn = nxtP[node];
                    doneP[node] = 1; --inq;
                    ++R; tot += curDist;
                    if (curDist > far) { far = curDist; farNode = node; }
                    else if (curDist == far && node < farNode) farNode = node;
                    int a0 = offP[node], a1 = offP[node + 1];
                    for (int ai = a0; ai < a1; ++ai) {
                        int pk = adjP[ai];
                        int v = pk >> 10;
                        if (doneP[v]) continue;
                        int nd = curDist + (pk & 1023);
                        if (nd < distP[v]) {
                            if (distP[v] != INF) {
                                int ob = distP[v] & 1023;
                                int pv = prvP[v], nv = nxtP[v];
                                if (pv != -1) nxtP[pv] = nv; else head[ob] = nv;
                                if (nv != -1) prvP[nv] = pv;
                                if (head[ob] == -1) words[ob >> 6] &= ~(1ULL << (ob & 63));
                            } else ++inq;
                            distP[v] = nd;
                            int nb = nd & 1023;
                            int oh = head[nb];
                            nxtP[v] = oh; prvP[v] = -1;
                            if (oh != -1) prvP[oh] = v;
                            else words[nb >> 6] |= (1ULL << (nb & 63));
                            head[nb] = v;
                        }
                    }
                    node = nn;
                }
                if (inq == 0) break;
                // find next non-empty bucket
                int wi = curB >> 6, bi = curB & 63;
                int nb = -1;
                uint64_t w0 = (bi == 63) ? 0 : (words[wi] & (~0ULL << (bi + 1)));
                if (w0) { nb = (wi << 6) + ctz64(w0); }
                else {
                    for (int k = 1; k < 16; ++k) {
                        int idx = (wi + k) & 15;
                        uint64_t w = words[idx];
                        if (w) { nb = (idx << 6) + ctz64(w); break; }
                    }
                    if (nb == -1) {
                        uint64_t low = (bi == 63) ? ~0ULL : ((1ULL << (bi + 1)) - 1ULL);
                        uint64_t w = words[wi] & low;
                        if (w) nb = (wi << 6) + ctz64(w);
                    }
                }
                // nb must exist
                int offd = nb - curB; if (offd <= 0) offd += B;
                curDist += offd; curB = nb;
            }
            if (cacheN < 64) cache[cacheN++] = Res{s, R, tot, far, farNode};
        }
        int len = snprintf(line, sizeof(line), "%d %lld %lld %lld %d\n", s, R, tot, far, farNode);
        out.append(line, (size_t)len);
    }
    fwrite(out.data(), 1, out.size(), stdout);
    return 0;
}
