#include <cstdio>
#include <cstdint>
#include <vector>
#include <climits>
#include <algorithm>
#include <string>
#include <io.h>
#include <fcntl.h>

using namespace std;

static const char* inData;
static size_t inSize;
static size_t inPos;

static inline int readInt() {
    while (inPos < inSize && (inData[inPos] < '0' || inData[inPos] > '9')) inPos++;
    int x = 0;
    while (inPos < inSize && inData[inPos] >= '0' && inData[inPos] <= '9') {
        x = x * 10 + (inData[inPos] - '0');
        inPos++;
    }
    return x;
}

// Min-heap of packed (distance, node) entries: (d << 32) | v.
// Distances stay below 2^31 and nodes below 2^22, so packing is exact.
struct Heap {
    vector<long long> h;

    void reserve(size_t n) { h.reserve(n); }
    void clear() { h.clear(); }
    bool empty() const { return h.empty(); }

    void push(int d, int v) {
        long long x = ((long long)d << 32) | (unsigned int)v;
        size_t i = h.size();
        h.push_back(x);
        while (i > 0) {
            size_t p = (i - 1) / 2;
            if (h[p] <= x) break;
            h[i] = h[p];
            i = p;
        }
        h[i] = x;
    }

    // Returns packed entry of the minimum; caller must not call on empty.
    long long pop() {
        long long top = h[0];
        long long x = h.back();
        h.pop_back();
        if (!h.empty()) {
            size_t i = 0;
            size_t n = h.size();
            h[0] = x;
            for (;;) {
                size_t c = 2 * i + 1;
                if (c >= n) break;
                if (c + 1 < n && h[c + 1] < h[c]) c++;
                if (h[c] >= x) break;
                h[i] = h[c];
                i = c;
            }
            h[i] = x;
        }
        return top;
    }
};

int main(int argc, char** argv) {
    FILE* f = fopen(argv[1], "rb");
    if (!f) return 1;
    fseek(f, 0, SEEK_END);
    long sz = ftell(f);
    fseek(f, 0, SEEK_SET);
    vector<char> buffer(sz + 1);
    if (sz > 0) fread(buffer.data(), 1, (size_t)sz, f);
    fclose(f);
    buffer[sz] = '\0';
    inData = buffer.data();
    inSize = (size_t)sz;
    inPos = 0;

    int N = readInt();
    int M = readInt();
    int Q = readInt();

    vector<int> eu(M), ev(M), ew(M);
    vector<int> deg(N > 0 ? N : 1, 0);
    for (int i = 0; i < M; i++) {
        int u = readInt(), v = readInt(), w = readInt();
        eu[i] = u; ev[i] = v; ew[i] = w;
        deg[u]++;
        deg[v]++;
    }

    vector<int> off(N + 1, 0);
    for (int i = 0; i < N; i++) off[i + 1] = off[i] + deg[i];
    vector<int> to(2 * M), wt(2 * M);
    vector<int> cur(off.begin(), off.begin() + N);
    for (int i = 0; i < M; i++) {
        int u = eu[i], v = ev[i], w = ew[i];
        int p = cur[u]++; to[p] = v; wt[p] = w;
        int q = cur[v]++; to[q] = u; wt[q] = w;
    }
    // Free edge lists; CSR is all we need from here.
    vector<int>().swap(eu);
    vector<int>().swap(ev);
    vector<int>().swap(ew);
    vector<int>().swap(cur);
    vector<int>().swap(deg);

    vector<int> sources(Q);
    for (int i = 0; i < Q; i++) sources[i] = readInt();

    vector<int> dist(N > 0 ? N : 1);
    const int INF = INT_MAX;
    Heap heap;
    heap.reserve((size_t)M + 1);

    _setmode(_fileno(stdout), _O_BINARY);

    string out;
    out.reserve(256);

    for (int i = 0; i < Q; i++) {
        int s = sources[i];
        fill(dist.begin(), dist.end(), INF);
        dist[s] = 0;
        heap.clear();
        heap.push(0, s);

        while (!heap.empty()) {
            long long packed = heap.pop();
            int d = (int)(packed >> 32);
            int v = (int)(packed & 0xFFFFFFFFu);
            if (d > dist[v]) continue; // stale entry
            int e0 = off[v];
            int e1 = off[v + 1];
            for (int e = e0; e < e1; e++) {
                int t = to[e];
                int nd = d + wt[e];
                if (nd < dist[t]) {
                    dist[t] = nd;
                    heap.push(nd, t);
                }
            }
        }

        long long reach = 0;
        long long total = 0;
        long long far = -1;
        int node = -1;
        for (int v = 0; v < N; v++) {
            if (dist[v] != INF) {
                reach++;
                total += dist[v];
                if (dist[v] > far) {
                    far = dist[v];
                    node = v;
                }
            }
        }

        char line[128];
        int n = snprintf(line, sizeof(line), "%d %lld %lld %lld %d\n", s, reach, total, far, node);
        out.append(line, (size_t)n);
    }

    fputs(out.c_str(), stdout);
    return 0;
}
