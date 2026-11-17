#include <cstdio>
#include <cstdlib>
#include <cstdint>
#include <vector>
#include <algorithm>
#include <bit>
#include <limits>
#include <io.h>
#include <fcntl.h>

using std::uint64_t;
using std::int64_t;

struct Parser {
    const unsigned char* p;

    inline int nextInt() {
        while (*p <= ' ') ++p;
        int x = 0;
        while (*p > ' ') {
            x = x * 10 + (*p - '0');
            ++p;
        }
        return x;
    }
};

static char* readAll(const char* path, size_t& len) {
    FILE* f = std::fopen(path, "rb");
    if (!f) {
        std::fprintf(stderr, "cannot open %s\n", path);
        std::exit(1);
    }
    std::fseek(f, 0, SEEK_END);
    long sz = std::ftell(f);
    std::fseek(f, 0, SEEK_SET);
    char* buf = (char*)std::malloc((size_t)sz + 1);
    size_t rd = std::fread(buf, 1, (size_t)sz, f);
    std::fclose(f);
    buf[rd] = '\0';       // parser relies on this sentinel
    len = rd;
    return buf;
}

// Monotone circular bucket queue (Dial).  Keys live in buckets indexed by
// distance mod (maxWeight+1); a bitset is used to jump over empty ranges, so
// large shortest distances cost nothing per unit of distance.
struct DialQueue {
    int nb;
    int words;
    int64_t cur;
    std::vector<uint64_t> bits;
    std::vector<std::vector<int>> buckets;

    void init(int maxW) {
        nb = maxW + 1;
        if (nb < 2) nb = 2;
        words = (nb + 63) >> 6;
        bits.assign((size_t)words, 0);
        buckets.resize((size_t)nb);
        cur = 0;
    }

    void clear() {
        for (auto& b : buckets) b.clear();
        std::fill(bits.begin(), bits.end(), (uint64_t)0);
        cur = 0;
    }

    inline void pushIdx(int node, int idx) {
        auto& b = buckets[idx];
        if (b.empty()) bits[idx >> 6] |= (uint64_t)1 << (idx & 63);
        b.push_back(node);
    }

    // Smallest set bucket index >= p (wrapping), or -1 if the queue is empty.
    inline int nextSetBit(int p) const {
        int wi = p >> 6;
        uint64_t w = bits[wi] & (~(uint64_t)0 << (p & 63));
        if (w) return (wi << 6) + std::countr_zero(w);
        for (int i = wi + 1; i < words; ++i) {
            if (bits[i]) return (i << 6) + std::countr_zero(bits[i]);
        }
        for (int i = 0; i < wi; ++i) {
            if (bits[i]) return (i << 6) + std::countr_zero(bits[i]);
        }
        uint64_t low = bits[wi] & (((uint64_t)1 << (p & 63)) - 1);
        if (low) return (wi << 6) + std::countr_zero(low);
        return -1;
    }
};

template <typename DistT>
static void runAll(int N, int Q, const std::vector<int>& src,
                   const std::vector<int>& off, const std::vector<int>& at,
                   const std::vector<int>& aw, int maxW,
                   std::vector<int64_t>& out) {
    const DistT INF = std::numeric_limits<DistT>::max();
    std::vector<DistT> dist((size_t)N);
    DialQueue dq;
    dq.init(maxW);
    const int nb = dq.nb;

    out.assign((size_t)Q * 5, 0);

    for (int qi = 0; qi < Q; ++qi) {
        int s = src[qi];
        std::fill(dist.begin(), dist.end(), INF);
        dq.clear();
        dist[s] = 0;
        dq.pushIdx(s, 0);

        int64_t reach = 0, total = 0, far = -1;
        int farNode = -1;

        for (;;) {
            int p = (int)(dq.cur % nb);
            int idx = dq.nextSetBit(p);
            if (idx < 0) break;
            int offset = idx - p;
            if (offset < 0) offset += nb;
            dq.cur += offset;
            DistT d = (DistT)dq.cur;

            auto& bk = dq.buckets[idx];
            while (!bk.empty()) {
                int u = bk.back();
                bk.pop_back();
                if (dist[u] != d) continue;

                ++reach;
                total += (int64_t)d;
                if ((int64_t)d > far) { far = (int64_t)d; farNode = u; }
                else if ((int64_t)d == far && u < farNode) farNode = u;

                int e = off[u], end = off[u + 1];
                for (; e < end; ++e) {
                    int v = at[e];
                    DistT nd = (DistT)(d + (DistT)aw[e]);
                    if (nd < dist[v]) {
                        dist[v] = nd;
                        int idx2 = idx + aw[e];
                        if (idx2 >= nb) idx2 -= nb;
                        dq.pushIdx(v, idx2);
                    }
                }
            }
            dq.bits[idx >> 6] &= ~((uint64_t)1 << (idx & 63));
        }

        out[(size_t)qi * 5 + 0] = s;
        out[(size_t)qi * 5 + 1] = reach;
        out[(size_t)qi * 5 + 2] = total;
        out[(size_t)qi * 5 + 3] = far;
        out[(size_t)qi * 5 + 4] = farNode;
    }
}

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    _setmode(_fileno(stdout), _O_BINARY);

    size_t len = 0;
    char* data = readAll(argv[1], len);
    Parser par{(const unsigned char*)data};

    int N = par.nextInt();
    int M = par.nextInt();
    int Q = par.nextInt();

    std::vector<int> eu((size_t)M), ev((size_t)M), ew((size_t)M);
    std::vector<int> deg((size_t)N, 0);
    int maxW = 0;

    for (int i = 0; i < M; ++i) {
        int u = par.nextInt();
        int v = par.nextInt();
        int w = par.nextInt();
        eu[i] = u; ev[i] = v; ew[i] = w;
        ++deg[u]; ++deg[v];
        if (w > maxW) maxW = w;
    }

    std::vector<int> off((size_t)N + 1);
    int acc = 0;
    for (int i = 0; i < N; ++i) {
        off[i] = acc;
        acc += deg[i];
    }
    off[N] = acc;

    std::vector<int> at((size_t)acc), aw((size_t)acc);
    std::vector<int> cur(off.begin(), off.end());
    for (int i = 0; i < M; ++i) {
        int u = eu[i], v = ev[i], w = ew[i];
        at[cur[u]] = v; aw[cur[u]] = w; ++cur[u];
        at[cur[v]] = u; aw[cur[v]] = w; ++cur[v];
    }

    std::vector<int> src((size_t)Q);
    for (int i = 0; i < Q; ++i) src[i] = par.nextInt();

    std::vector<int>().swap(eu);
    std::vector<int>().swap(ev);
    std::vector<int>().swap(ew);
    std::vector<int>().swap(deg);
    std::vector<int>().swap(cur);

    // Distances fit in 32 bits whenever N*maxW stays below INT32_MAX.
    std::vector<int64_t> out;
    bool small = (int64_t)N * (int64_t)maxW < (int64_t)INT32_MAX - 1;
    if (small) runAll<int32_t>(N, Q, src, off, at, aw, maxW, out);
    else       runAll<int64_t>(N, Q, src, off, at, aw, maxW, out);

    char buf[256];
    for (int qi = 0; qi < Q; ++qi) {
        int n = std::snprintf(buf, sizeof(buf), "%lld %lld %lld %lld %lld\n",
                              (long long)out[(size_t)qi * 5 + 0],
                              (long long)out[(size_t)qi * 5 + 1],
                              (long long)out[(size_t)qi * 5 + 2],
                              (long long)out[(size_t)qi * 5 + 3],
                              (long long)out[(size_t)qi * 5 + 4]);
        std::fwrite(buf, 1, (size_t)n, stdout);
    }
    std::fflush(stdout);
    std::free(data);
    return 0;
}
