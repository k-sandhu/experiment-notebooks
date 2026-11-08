#include <cstdio>
#include <cstdint>
#include <cstring>
#include <vector>
#include <cstdlib>
#include <fcntl.h>
#include <io.h>

using namespace std;

static char* g_buf;
static const char* g_p;

static inline int readInt() {
    // skip any non-digit separators (space, \r, \n)
    while (*g_p < '0' || *g_p > '9') ++g_p;
    unsigned x = 0;
    while (*g_p >= '0' && *g_p <= '9') x = x * 10u + unsigned(*g_p++ - '0');
    return int(x);
}

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    _setmode(_fileno(stdout), _O_BINARY);
    FILE* f = nullptr;
    fopen_s(&f, argv[1], "rb");
    if (!f) return 1;
    fseek(f, 0, SEEK_END);
    long sz = ftell(f);
    fseek(f, 0, SEEK_SET);
    g_buf = (char*)malloc(size_t(sz) + 1);
    size_t rd = fread(g_buf, 1, size_t(sz), f);
    g_buf[rd] = 0;
    fclose(f);
    g_p = g_buf;

    const int N = readInt();
    const int M = readInt();
    const int Q = readInt();

    vector<int> eu(M), ev(M), ew(M);
    vector<int> start(N + 1, 0);
    for (int i = 0; i < M; ++i) {
        int u = readInt(), v = readInt(), w = readInt();
        eu[i] = u; ev[i] = v; ew[i] = w;
        ++start[u + 1]; ++start[v + 1];
    }
    for (int i = 0; i < N; ++i) start[i + 1] += start[i];
    const int E2 = start[N];
    vector<int> adjV(E2), adjW(E2);
    {
        vector<int> pos(start.begin(), start.end() - 1);
        for (int i = 0; i < M; ++i) {
            adjV[pos[eu[i]]] = ev[i]; adjW[pos[eu[i]]] = ew[i]; ++pos[eu[i]];
            adjV[pos[ev[i]]] = eu[i]; adjW[pos[ev[i]]] = ew[i]; ++pos[ev[i]];
        }
    }

    // Dial's bucket queue: weights are 1..1000, so a circular array of 1001
    // buckets holds every pending distance. Each bucket is a singly linked
    // list threaded through the arena array.
    const int NB = 1001;
    const int CAP = 2 * M + 2;
    vector<int> arena(CAP), nextIn(CAP), head(NB, -1);

    vector<int32_t> dist(N);
    vector<uint8_t> settled(N);

    char* ob = (char*)malloc(size_t(Q) * 80 + 16);
    char* op = ob;

    for (int qi = 0; qi < Q; ++qi) {
        const int s = readInt();
        memset(dist.data(), 0xFF, size_t(N) * 4); // -1
        memset(settled.data(), 0, size_t(N));
        memset(head.data(), 0xFF, NB * sizeof(int)); // -1
        int cnt = 0;
        dist[s] = 0;
        arena[cnt] = s; nextIn[cnt] = -1; head[0] = cnt; ++cnt;
        int remaining = 1;
        long long d = 0;
        int idx = 0;
        while (remaining) {
            int e = head[idx];
            if (e < 0) { idx = idx + 1 == NB ? 0 : idx + 1; ++d; continue; }
            head[idx] = nextIn[e];
            --remaining;
            const int v = arena[e];
            if (settled[v] || dist[v] != (int32_t)d) continue;
            settled[v] = 1;
            const int eEnd = start[v + 1];
            for (int i = start[v]; i < eEnd; ++i) {
                const int u = adjV[i];
                if (settled[u]) continue;
                const int32_t nd = int32_t(d) + adjW[i];
                const int32_t du = dist[u];
                if (du < 0 || nd < du) {
                    dist[u] = nd;
                    const int b = nd % NB;
                    arena[cnt] = u; nextIn[cnt] = head[b]; head[b] = cnt; ++cnt;
                    ++remaining;
                }
            }
        }
        long long total = 0;
        int64_t far = 0;
        int farNode = s;
        int R = 0;
        for (int v = 0; v < N; ++v) {
            int64_t dd = dist[v];
            if (dd >= 0) {
                ++R;
                total += dd;
                if (dd > far || (dd == far && v < farNode)) { far = dd; farNode = v; }
            }
        }
        op += sprintf(op, "%d %d %lld %lld %d\n", s, R, total, (long long)far, farNode);
    }

    fwrite(ob, 1, size_t(op - ob), stdout);
    return 0;
}
