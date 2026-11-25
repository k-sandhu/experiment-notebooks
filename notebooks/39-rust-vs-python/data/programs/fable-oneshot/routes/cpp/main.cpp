#include <cstdio>
#include <cstdint>
#include <cstdlib>
#include <vector>
#include <string>
#include <bit>
#include <memory>
#include <algorithm>
#include <limits>

struct Edge {
    uint32_t to;
    uint32_t w;
};

struct Raw {
    uint32_t u, v, w;
};

static inline uint64_t readU(const char*& p, const char* end) {
    while (p < end && (unsigned char)(*p - '0') > 9) ++p;
    uint64_t x = 0;
    // buffer has a '\0' sentinel at end, so no bounds check needed here
    while ((unsigned char)(*p - '0') <= 9) {
        x = x * 10 + (uint64_t)(*p - '0');
        ++p;
    }
    return x;
}

template <class D>
static void solve(uint32_t N, const uint32_t* off, const Edge* adj,
                  const std::vector<uint64_t>& sources, std::string& out) {
    const D INF = std::numeric_limits<D>::max();
    std::vector<D> distv(N);
    D* dist = distv.data();
    std::vector<std::vector<uint32_t>> buckets(1024);
    for (auto& b : buckets) b.reserve(64);
    uint64_t bm[16];

    for (uint64_t s64 : sources) {
        if (s64 >= N) {
            out += std::to_string(s64);
            out += " 1 0 0 ";
            out += std::to_string(s64);
            out += '\n';
            continue;
        }
        uint32_t s = (uint32_t)s64;
        std::fill(distv.begin(), distv.end(), INF);
        for (int i = 0; i < 16; ++i) bm[i] = 0;

        dist[s] = 0;
        buckets[0].push_back(s);
        bm[0] |= 1ull;

        uint64_t cur = 0;
        uint64_t R = 0, total = 0, far = 0;
        uint32_t node = s;

        for (;;) {
            uint32_t pos = (uint32_t)(cur & 1023);
            uint32_t wd = pos >> 6;
            uint64_t m = bm[wd] >> (pos & 63);
            uint32_t idx;
            if (m) {
                idx = pos + (uint32_t)std::countr_zero(m);
            } else {
                bool found = false;
                idx = 0;
                for (uint32_t k = 1; k <= 16; ++k) {
                    uint32_t w2 = (wd + k) & 15;
                    if (bm[w2]) {
                        idx = w2 * 64 + (uint32_t)std::countr_zero(bm[w2]);
                        found = true;
                        break;
                    }
                }
                if (!found) break;
            }
            cur += (uint64_t)((idx - pos) & 1023);

            std::vector<uint32_t>& b = buckets[idx];
            const uint32_t* bp = b.data();
            const size_t bn = b.size();
            const D dc = (D)cur;

            for (size_t i = 0; i < bn; ++i) {
                uint32_t u = bp[i];
                if (dist[u] != dc) continue;
                ++R;
                total += cur;
                if (cur > far) {
                    far = cur;
                    node = u;
                } else if (u < node) {
                    node = u;
                }
                const Edge* e = adj + off[u];
                const Edge* ee = adj + off[u + 1];
                for (; e != ee; ++e) {
                    uint32_t v = e->to;
                    D nd = (D)(dc + (D)e->w);
                    if (nd < dist[v]) {
                        dist[v] = nd;
                        uint32_t nb = (uint32_t)(nd & 1023);
                        buckets[nb].push_back(v);
                        bm[nb >> 6] |= 1ull << (nb & 63);
                    }
                }
            }
            b.clear();
            bm[idx >> 6] &= ~(1ull << (idx & 63));
        }

        out += std::to_string(s);
        out += ' ';
        out += std::to_string(R);
        out += ' ';
        out += std::to_string(total);
        out += ' ';
        out += std::to_string(far);
        out += ' ';
        out += std::to_string(node);
        out += '\n';
    }
}

int main(int argc, char** argv) {
    if (argc < 2) return 0;
    FILE* f = std::fopen(argv[1], "rb");
    if (!f) return 0;
    _fseeki64(f, 0, SEEK_END);
    long long fsz = _ftelli64(f);
    _fseeki64(f, 0, SEEK_SET);
    if (fsz < 0) fsz = 0;
    std::unique_ptr<char[]> buf(new char[(size_t)fsz + 1]);
    size_t got = 0;
    while (got < (size_t)fsz) {
        size_t r = std::fread(buf.get() + got, 1, (size_t)fsz - got, f);
        if (r == 0) break;
        got += r;
    }
    std::fclose(f);
    buf[got] = '\0';

    const char* p = buf.get();
    const char* end = buf.get() + got;

    uint64_t N64 = readU(p, end);
    uint64_t M64 = readU(p, end);
    uint64_t Q64 = readU(p, end);
    uint32_t N = (uint32_t)N64;
    size_t M = (size_t)M64;

    std::unique_ptr<Raw[]> raw(new Raw[M ? M : 1]);
    std::vector<uint32_t> offv((size_t)N + 2, 0);
    uint32_t* off = offv.data();

    size_t cnt = 0;
    for (size_t i = 0; i < M; ++i) {
        uint64_t u = readU(p, end);
        uint64_t v = readU(p, end);
        uint64_t w = readU(p, end);
        if (u == v || u >= N || v >= N) continue; // self-loops never matter
        raw[cnt].u = (uint32_t)u;
        raw[cnt].v = (uint32_t)v;
        raw[cnt].w = (uint32_t)w;
        ++cnt;
        ++off[u + 1];
        ++off[v + 1];
    }

    std::vector<uint64_t> sources;
    sources.reserve((size_t)Q64);
    for (uint64_t i = 0; i < Q64; ++i) {
        sources.push_back(readU(p, end));
    }
    buf.reset();

    for (uint32_t i = 0; i < N; ++i) off[i + 1] += off[i];

    std::unique_ptr<Edge[]> adj(new Edge[cnt * 2 + 1]);
    {
        std::vector<uint32_t> posv(offv.begin(), offv.begin() + N + 1);
        uint32_t* pos = posv.data();
        for (size_t i = 0; i < cnt; ++i) {
            uint32_t u = raw[i].u, v = raw[i].v, w = raw[i].w;
            Edge& a = adj[pos[u]++];
            a.to = v;
            a.w = w;
            Edge& c = adj[pos[v]++];
            c.to = u;
            c.w = w;
        }
    }
    raw.reset();

    std::string out;
    out.reserve(64 * (sources.size() + 1));

    if ((uint64_t)N * 1000ull < 4000000000ull) {
        solve<uint32_t>(N, off, adj.get(), sources, out);
    } else {
        solve<uint64_t>(N, off, adj.get(), sources, out);
    }

    std::fwrite(out.data(), 1, out.size(), stdout);
    std::fflush(stdout);
    return 0;
}
