// Routes: shortest road distances from several sources.
// Multi-source Dijkstra (one run per source) over an undirected graph.
// MSVC C++20, /O2 /GL /LTCG.
//
// This translation unit includes no standard headers and links only kernel32:
// it calls the Windows API directly and implements its own buffers and
// integer formatting. This keeps the build dependency-free and lets the same
// source be compiled and linked with the benchmark's exact cl flags.
//
// Graph is stored in CSR form: start[node..node+1) indexes into gto/gw.
// Distances are int32: any simple path has at most N-1 edges of weight <= 1000,
// so a distance never exceeds (N-1)*1000 < 2^31. Totals need int64.

#pragma comment(linker, "/entry:routesMain")
#pragma comment(linker, "/subsystem:console")
#pragma comment(lib, "msvcrt.lib")

using i32 = int;
using i64 = long long;
using u64 = unsigned long long;
using usize = unsigned long long;

static const i32 INF = 2147483647;

extern "C" {
__declspec(dllimport) void* GetProcessHeap();
__declspec(dllimport) void* HeapAlloc(void* h, unsigned long flags, usize size);
__declspec(dllimport) void* HeapReAlloc(void* h, unsigned long flags, void* p, usize size);
__declspec(dllimport) int HeapFree(void* h, unsigned long flags, void* p);
__declspec(dllimport) void* CreateFileA(const char* name, unsigned long access,
                                        unsigned long share, void* sa,
                                        unsigned long disp, unsigned long attrs, void* tmpl);
__declspec(dllimport) unsigned long GetFileSize(void* h, unsigned long* high);
__declspec(dllimport) int ReadFile(void* h, void* buf, unsigned long n,
                                   unsigned long* read, void* ov);
__declspec(dllimport) int WriteFile(void* h, const void* buf, unsigned long n,
                                    unsigned long* written, void* ov);
__declspec(dllimport) int CloseHandle(void* h);
__declspec(dllimport) void* GetStdHandle(unsigned long n);
__declspec(dllimport) char* GetCommandLineA();
__declspec(dllimport) void ExitProcess(unsigned long code);
}

static void* heap;

static void* alloc(usize bytes) {
    void* p = HeapAlloc(heap, 0, bytes);
    if (!p) ExitProcess(1);
    return p;
}

static void* allocZ(usize bytes) {
    void* p = HeapAlloc(heap, 0x00000008u, bytes); // HEAP_ZERO_MEMORY
    if (!p) ExitProcess(1);
    return p;
}

static void* grow(void* p, usize bytes) {
    void* np = HeapReAlloc(heap, 0, p, bytes);
    if (!np) ExitProcess(1);
    return np;
}

static void appendU64(char*& p, u64 v) {
    char tmp[24];
    int n = 0;
    if (v == 0) { *p++ = '0'; return; }
    while (v > 0) { tmp[n++] = (char)('0' + (int)(v % 10)); v /= 10; }
    while (n > 0) *p++ = tmp[--n];
}

static void appendI64(char*& p, i64 v) {
    if (v < 0) { *p++ = '-'; appendU64(p, (u64)(-(v + 1)) + 1); return; }
    appendU64(p, (u64)v);
}

// Parse the input path from the command line (second whitespace token).
static const char* findArg() {
    char* cmd = GetCommandLineA();
    char* p = cmd;
    while (*p == ' ') ++p;
    if (*p == '"') {
        ++p;
        while (*p && *p != '"') ++p;
        if (*p) ++p;
    } else {
        while (*p && *p != ' ') ++p;
    }
    while (*p == ' ') ++p;
    return p; // may point at NUL if missing
}

static i64 nextInt(const char*& p, const char* end) {
    while (p < end && (*p < '0' || *p > '9') && *p != '-') ++p;
    bool neg = false;
    if (p < end && *p == '-') { neg = true; ++p; }
    i64 v = 0;
    while (p < end && *p >= '0' && *p <= '9') { v = v * 10 + (*p - '0'); ++p; }
    return neg ? -v : v;
}

void routesMain() {
    heap = GetProcessHeap();
    const char* arg = findArg();
    if (!*arg) ExitProcess(1);

    void* h = CreateFileA(arg, 0x80000000u, 0u, 0, 3u, 0u, 0);
    if (h == (void*)-1) ExitProcess(1);
    unsigned long size = GetFileSize(h, 0);
    char* buf = (char*)alloc((usize)size + 1);
    unsigned long read = 0;
    if (!ReadFile(h, buf, size, &read, 0) || (unsigned long long)read != (unsigned long long)size) {
        ExitProcess(1);
    }
    buf[size] = '\0';
    CloseHandle(h);

    const char* p = buf;
    const char* end = buf + size;

    i32 N = (i32)nextInt(p, end);
    i32 M = (i32)nextInt(p, end);
    i32 Q = (i32)nextInt(p, end);

    i32* deg = (i32*)allocZ((usize)(N + 1) * sizeof(i32));
    i32* eu = (i32*)alloc((usize)M * sizeof(i32));
    i32* ev = (i32*)alloc((usize)M * sizeof(i32));
    i32* ew = (i32*)alloc((usize)M * sizeof(i32));
    for (i32 i = 0; i < M; ++i) {
        i32 u = (i32)nextInt(p, end);
        i32 v = (i32)nextInt(p, end);
        i32 w = (i32)nextInt(p, end);
        eu[i] = u; ev[i] = v; ew[i] = w;
        ++deg[u];
        ++deg[v];
    }

    i32* start = (i32*)alloc((usize)(N + 1) * sizeof(i32));
    start[0] = 0;
    for (i32 i = 0; i < N; ++i) start[i + 1] = start[i] + deg[i];

    i32 totalEdges = 2 * M;
    i32* gto = (i32*)alloc((usize)totalEdges * sizeof(i32));
    i32* gw = (i32*)alloc((usize)totalEdges * sizeof(i32));
    {
        i32* cur = (i32*)alloc((usize)N * sizeof(i32));
        for (i32 i = 0; i < N; ++i) cur[i] = start[i];
        for (i32 i = 0; i < M; ++i) {
            i32 u = eu[i], v = ev[i], w = ew[i];
            i32 pos = cur[u]++; gto[pos] = v; gw[pos] = w;
            pos = cur[v]++; gto[pos] = u; gw[pos] = w;
        }
        HeapFree(heap, 0, cur);
    }
    HeapFree(heap, 0, eu);
    HeapFree(heap, 0, ev);
    HeapFree(heap, 0, ew);
    HeapFree(heap, 0, deg);

    i32* dist = (i32*)alloc((usize)N * sizeof(i32));

    // Binary heap over (distance, node) pairs in two parallel arrays.
    i32 hcap = M + 1;
    i32* hd = (i32*)alloc((usize)hcap * sizeof(i32));
    i32* hn = (i32*)alloc((usize)hcap * sizeof(i32));
    i32 hsize = 0;

    void* outh = GetStdHandle(0xFFFFFFF5u); // STD_OUTPUT_HANDLE
    char line[128];
    unsigned long written = 0;

    for (i32 q = 0; q < Q; ++q) {
        i32 s = (i32)nextInt(p, end);
        for (i32 i = 0; i < N; ++i) dist[i] = INF;
        dist[s] = 0;
        hsize = 0;
        hd[0] = 0; hn[0] = s; hsize = 1;
        while (hsize > 0) {
            i32 d = hd[0];
            i32 u = hn[0];
            --hsize;
            if (hsize > 0) {
                i32 lastD = hd[hsize];
                i32 lastN = hn[hsize];
                i32 i = 0;
                for (;;) {
                    i32 l = 2 * i + 1;
                    i32 r = l + 1;
                    if (l >= hsize) break;
                    i32 child = l;
                    if (r < hsize && hd[r] < hd[l]) child = r;
                    if (hd[child] >= lastD) break;
                    hd[i] = hd[child];
                    hn[i] = hn[child];
                    i = child;
                }
                hd[i] = lastD;
                hn[i] = lastN;
            }
            if (d > dist[u]) continue;
            for (i32 e = start[u]; e < start[u + 1]; ++e) {
                i32 v = gto[e];
                i32 nd = d + gw[e];
                if (nd < dist[v]) {
                    dist[v] = nd;
                    if (hsize == hcap) {
                        hcap *= 2;
                        hd = (i32*)grow(hd, (usize)hcap * sizeof(i32));
                        hn = (i32*)grow(hn, (usize)hcap * sizeof(i32));
                    }
                    i32 i = hsize++;
                    hd[i] = nd; hn[i] = v;
                    while (i > 0) {
                        i32 par = (i - 1) / 2;
                        if (hd[par] <= nd) break;
                        hd[i] = hd[par];
                        hn[i] = hn[par];
                        i = par;
                    }
                    hd[i] = nd;
                    hn[i] = v;
                }
            }
        }

        i32 R = 0;
        i64 total = 0;
        i32 far = -1;
        i32 node = -1;
        for (i32 i = 0; i < N; ++i) {
            i32 d = dist[i];
            if (d != INF) {
                ++R;
                total += d;
                if (d > far) {
                    far = d;
                    node = i;
                }
            }
        }

        char* qq = line;
        appendI64(qq, (i64)s); *qq++ = ' ';
        appendI64(qq, (i64)R); *qq++ = ' ';
        appendI64(qq, total); *qq++ = ' ';
        appendI64(qq, (i64)far); *qq++ = ' ';
        appendI64(qq, (i64)node); *qq++ = '\n';
        WriteFile(outh, line, (unsigned long)(qq - line), &written, 0);
    }

    ExitProcess(0);
}
