#include <cstdio>
#include <cstdint>
#include <cstdlib>
#include <vector>
#include <string>
#include <io.h>
#include <fcntl.h>

typedef unsigned long long u64;

static const unsigned char* p;

static inline int readInt() {
    while (*p < '0') p++;
    int x = 0;
    while (*p >= '0') { x = x * 10 + (*p - '0'); p++; }
    return x;
}

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    FILE* f = fopen(argv[1], "rb");
    if (!f) return 1;
    fseek(f, 0, SEEK_END);
    long sz = ftell(f);
    fseek(f, 0, SEEK_SET);
    unsigned char* buf = (unsigned char*)malloc(sz + 2);
    size_t got = fread(buf, 1, sz, f);
    fclose(f);
    buf[got] = 0;
    p = buf;
    int n = readInt(), m = readInt(), q = readInt();
    std::vector<int> eu(m), ev(m), ew(m);
    std::vector<int> start(n + 2, 0);
    for (int i = 0; i < m; i++) {
        int u = readInt(), v = readInt(), w = readInt();
        eu[i] = u; ev[i] = v; ew[i] = w;
        if (u != v) { start[u + 2]++; start[v + 2]++; }
    }
    for (int i = 2; i <= n + 1; i++) start[i] += start[i - 1];
    std::vector<int> adj(start[n + 1]);
    for (int i = 0; i < m; i++) {
        int u = eu[i], v = ev[i], w = ew[i];
        if (u == v) continue;
        adj[start[u + 1]++] = v * 1024 + w;
        adj[start[v + 1]++] = u * 1024 + w;
    }
    // now start[u]..start[u+1] is the range of u
    std::vector<long long> dist(n);
    std::vector<u64> heap(adj.size() + 2);
    std::string out;
    const long long INF = 0x7fffffffffffffffLL;
    for (int qi = 0; qi < q; qi++) {
        int s = readInt();
        for (int i = 0; i < n; i++) dist[i] = INF;
        u64* h = heap.data();
        size_t hs = 0;
        dist[s] = 0;
        h[hs++] = (u64)s;
        const int* A = adj.data();
        const int* S = start.data();
        long long* D = dist.data();
        while (hs) {
            u64 top = h[0];
            u64 last = h[--hs];
            if (hs) {
                size_t i = 0;
                for (;;) {
                    size_t c = 2 * i + 1;
                    if (c >= hs) break;
                    if (c + 1 < hs && h[c + 1] < h[c]) c++;
                    if (h[c] >= last) break;
                    h[i] = h[c];
                    i = c;
                }
                h[i] = last;
            }
            int u = (int)(top & 0xffffffffULL);
            long long d = (long long)(top >> 32);
            if (d != D[u]) continue;
            for (int e = S[u], ee = S[u + 1]; e < ee; e++) {
                int x = A[e];
                int v = x >> 10;
                long long nd = d + (x & 1023);
                if (nd < D[v]) {
                    D[v] = nd;
                    u64 key = ((u64)nd << 32) | (u64)v;
                    size_t i = hs++;
                    while (i > 0) {
                        size_t par = (i - 1) >> 1;
                        if (h[par] <= key) break;
                        h[i] = h[par];
                        i = par;
                    }
                    h[i] = key;
                }
            }
        }
        long long total = 0, far = 0;
        long long cnt = 0;
        for (int i = 0; i < n; i++) {
            long long d = D[i];
            if (d != INF) {
                cnt++;
                total += d;
                if (d > far) far = d;
            }
        }
        int node = 0;
        for (int i = 0; i < n; i++) if (D[i] == far) { node = i; break; }
        out += std::to_string(s) + " " + std::to_string(cnt) + " " + std::to_string(total) + " " +
               std::to_string(far) + " " + std::to_string(node) + "\n";
    }
    _setmode(_fileno(stdout), _O_BINARY);
    fwrite(out.data(), 1, out.size(), stdout);
    return 0;
}
