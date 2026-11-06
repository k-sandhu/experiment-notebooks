#include <cstdio>
#include <cstdint>
#include <vector>
#include <algorithm>
#include <fcntl.h>
#include <io.h>

static char* g_p;

static inline int nextInt() {
    char* p = g_p;
    while ((unsigned char)(*p - '0') > 9u) ++p;
    int x = 0;
    do {
        x = x * 10 + (*p - '0');
        ++p;
    } while ((unsigned char)(*p - '0') <= 9u);
    g_p = p;
    return x;
}

static std::vector<uint64_t> g_heap;

static inline void heapPush(uint64_t x) {
    g_heap.push_back(x);
    size_t i = g_heap.size() - 1;
    while (i > 0) {
        size_t p = (i - 1) >> 1;
        if (g_heap[p] <= x) break;
        g_heap[i] = g_heap[p];
        i = p;
    }
    g_heap[i] = x;
}

static inline uint64_t heapPop() {
    uint64_t top = g_heap[0];
    uint64_t x = g_heap.back();
    g_heap.pop_back();
    size_t n = g_heap.size();
    if (n) {
        size_t i = 0;
        for (;;) {
            size_t c = (i << 1) + 1;
            if (c >= n) break;
            if (c + 1 < n && g_heap[c + 1] < g_heap[c]) ++c;
            if (g_heap[c] >= x) break;
            g_heap[i] = g_heap[c];
            i = c;
        }
        g_heap[i] = x;
    }
    return top;
}

// Adjacency entry: (node << 10) | weight, weight <= 1000.
// Decoded with an unsigned shift, so it holds for node < 2^22.
int main(int argc, char** argv) {
    if (argc < 2) return 1;
    _setmode(_fileno(stdout), _O_BINARY);
    FILE* f = fopen(argv[1], "rb");
    if (!f) return 1;
    fseek(f, 0, SEEK_END);
    long sz = ftell(f);
    fseek(f, 0, SEEK_SET);
    if (sz < 0) { fclose(f); return 1; }
    std::vector<char> data((size_t)sz + 1);
    size_t got = fread(data.data(), 1, (size_t)sz, f);
    fclose(f);
    data[(size_t)got] = '\0';
    g_p = data.data();

    int N = nextInt();
    int M = nextInt();
    int Q = nextInt();

    std::vector<int> eu((size_t)M), ev((size_t)M), ew((size_t)M);
    std::vector<int> deg((size_t)N + 1, 0);
    for (int i = 0; i < M; ++i) {
        int u = nextInt(), v = nextInt(), w = nextInt();
        eu[i] = u; ev[i] = v; ew[i] = w;
        ++deg[u]; ++deg[v];
    }
    std::vector<int> src((size_t)Q);
    for (int i = 0; i < Q; ++i) src[i] = nextInt();

    std::vector<int> off((size_t)N + 1);
    int acc = 0;
    for (int i = 0; i < N; ++i) { off[i] = acc; acc += deg[i]; }
    off[N] = acc;

    std::vector<int> pos(off.begin(), off.end());
    std::vector<int> adj((size_t)2 * M);
    for (int i = 0; i < M; ++i) {
        int u = eu[i], v = ev[i], w = ew[i];
        adj[pos[u]++] = (v << 10) | w;
        adj[pos[v]++] = (u << 10) | w;
    }
    std::vector<int>().swap(eu);
    std::vector<int>().swap(ev);
    std::vector<int>().swap(ew);
    std::vector<int>().swap(deg);
    std::vector<int>().swap(pos);

    const int INF = 0x3f3f3f3f;
    std::vector<int> dist((size_t)N, INF);

    int shift = 0;
    while ((1u << shift) < (unsigned)N) ++shift;
    const uint32_t mask = (1u << shift) - 1u;

    g_heap.reserve((size_t)2 * M + 16);

    for (int qi = 0; qi < Q; ++qi) {
        int s = src[qi];
        std::fill(dist.begin(), dist.end(), INF);
        g_heap.clear();
        dist[s] = 0;
        heapPush((uint64_t)(uint32_t)s);

        long long total = 0;
        int reach = 0;
        int far = 0;
        int farNode = s;

        while (!g_heap.empty()) {
            uint64_t key = heapPop();
            int v = (int)(key & mask);
            int d = (int)(key >> shift);
            if (d != dist[v]) continue;

            ++reach;
            total += d;
            if (d > far) { far = d; farNode = v; }

            int begin = off[v];
            int end = off[v + 1];
            for (int e = begin; e < end; ++e) {
                unsigned a = (unsigned)adj[e];
                int u = (int)(a >> 10);
                int nd = d + (a & 1023);
                if (nd < dist[u]) {
                    dist[u] = nd;
                    heapPush(((uint64_t)(uint32_t)nd << shift) | (uint32_t)u);
                }
            }
        }

        printf("%d %d %lld %d %d\n", s, reach, total, far, farNode);
    }
    return 0;
}
