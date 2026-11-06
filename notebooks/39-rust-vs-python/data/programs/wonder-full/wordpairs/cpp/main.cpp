#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>
#include <algorithm>
#include <filesystem>
#include <io.h>
#include <fcntl.h>

static inline uint64_t mix64(uint64_t x) {
    x += 0x9e3779b97f4a7c15ULL;
    x = (x ^ (x >> 30)) * 0xbf58476d1ce4e5b9ULL;
    x = (x ^ (x >> 27)) * 0x94d049bb133111ebULL;
    return x ^ (x >> 31);
}

struct Entry { int count; int a; int b; };

int main(int argc, char** argv) {
    _setmode(_fileno(stdout), _O_BINARY);
    if (argc < 2) return 1;
    std::error_code ec;
    auto fsz = std::filesystem::file_size(argv[1], ec);
    if (ec) return 1;
    FILE* f = fopen(argv[1], "rb");
    if (!f) return 1;
    std::vector<unsigned char> data((size_t)fsz);
    if (fsz && fread(data.data(), 1, (size_t)fsz, f) != (size_t)fsz) return 1;
    fclose(f);
    const unsigned char* d = data.data();
    const size_t n = data.size();

    // word table
    size_t wcap = 1024;
    while (wcap < (size_t(1) << 17) && wcap * 64 < n) wcap <<= 1;
    std::vector<int> wtab(wcap, -1);
    size_t wmask = wcap - 1;
    std::vector<unsigned char> arena;
    arena.reserve(1 << 20);
    std::vector<int> woff; woff.reserve(65536);
    std::vector<int> wlen; wlen.reserve(65536);
    std::vector<uint64_t> whash; whash.reserve(65536);
    int V = 0;

    std::vector<uint64_t> pairs;
    {
        size_t est = n / 6 + 1024;
        if (est > (size_t(1) << 24)) est = size_t(1) << 24;
        pairs.reserve(est);
    }

    long long W = 0, T = 0;
    int prev = -1;
    size_t i = 0;
    while (i < n) {
        unsigned b = d[i];
        unsigned lo = b | 32u;
        if (lo - 97u < 26u) {
            size_t start = i;
            uint64_t h = 14695981039346656037ULL;
            do {
                h ^= (uint64_t)lo;
                h *= 1099511628211ULL;
                ++i;
                if (i >= n) break;
                b = d[i]; lo = b | 32u;
            } while (lo - 97u < 26u);
            int len = (int)(i - start);
            uint64_t mh = mix64(h);
            size_t idx = (size_t)mh & wmask;
            int id;
            for (;;) {
                id = wtab[idx];
                if (id < 0) {
                    id = V++;
                    wtab[idx] = id;
                    whash.push_back(mh);
                    woff.push_back((int)arena.size());
                    wlen.push_back(len);
                    for (int k = 0; k < len; ++k) arena.push_back((unsigned char)(d[start + k] | 32u));
                    if ((size_t)V * 4 > wcap * 3) {
                        size_t ncap = wcap << 1;
                        std::vector<int> nt(ncap, -1);
                        size_t nmask = ncap - 1;
                        for (int wi = 0; wi < V; ++wi) {
                            size_t j = (size_t)whash[wi] & nmask;
                            while (nt[j] >= 0) j = (j + 1) & nmask;
                            nt[j] = wi;
                        }
                        wtab.swap(nt); wcap = ncap; wmask = nmask;
                    }
                    break;
                }
                if (whash[id] == mh && wlen[id] == len) {
                    const unsigned char* ap = arena.data() + woff[id];
                    bool eq = true;
                    for (int k = 0; k < len; ++k) if (ap[k] != (unsigned char)(d[start + k] | 32u)) { eq = false; break; }
                    if (eq) break;
                }
                idx = (idx + 1) & wmask;
            }
            ++W;
            if (prev >= 0) {
                ++T;
                pairs.push_back(((uint64_t)(uint32_t)prev << 32) | (uint32_t)id);
            }
            prev = id;
        } else {
            if (b == '.' || b == '!' || b == '?') prev = -1;
            ++i;
        }
    }
    // free input
    std::vector<unsigned char>().swap(data);
    d = nullptr;

    // rank words lexicographically
    std::vector<int> ids(V);
    for (int k = 0; k < V; ++k) ids[k] = k;
    const unsigned char* ar = arena.data();
    std::sort(ids.begin(), ids.end(), [&](int a, int b) {
        int la = wlen[a], lb = wlen[b];
        int m = la < lb ? la : lb;
        int c = m ? std::memcmp(ar + woff[a], ar + woff[b], (size_t)m) : 0;
        if (c) return c < 0;
        return la < lb;
    });
    std::vector<int> rankv(V);
    for (int k = 0; k < V; ++k) rankv[ids[k]] = k;
    const int* rk = rankv.data();

    auto better = [&](const Entry& x, const Entry& y) -> bool {
        if (x.count != y.count) return x.count > y.count;
        if (rk[x.a] != rk[y.a]) return rk[x.a] < rk[y.a];
        return rk[x.b] < rk[y.b];
    };

    long long D = 0;
    Entry top[20];
    int topN = 0, worst = 0;
    const long long tcount = (long long)pairs.size();
    if (tcount > 0) {
        std::vector<int> cnt(65536);
        const size_t tc = (size_t)tcount;
        auto radixScan = [&](auto* src, auto* dst, int bits, auto getA, auto getB) {
            for (int shift = 0; shift < bits; shift += 16) {
                std::fill(cnt.begin(), cnt.end(), 0);
                for (size_t k = 0; k < tc; ++k) cnt[(src[k] >> shift) & 0xFFFF]++;
                int sum = 0;
                for (int k = 0; k < 65536; ++k) { int t = cnt[k]; cnt[k] = sum; sum += t; }
                for (size_t k = 0; k < tc; ++k) { auto v = src[k]; dst[cnt[(v >> shift) & 0xFFFF]++] = v; }
                auto* tmp = src; src = dst; dst = tmp;
            }
            size_t k = 0;
            while (k < tc) {
                size_t j = k + 1;
                auto v = src[k];
                while (j < tc && src[j] == v) ++j;
                ++D;
                Entry e{(int)(j - k), getA(v), getB(v)};
                if (topN < 20) {
                    top[topN++] = e;
                    if (topN == 20) { worst = 0; for (int q = 1; q < 20; ++q) if (better(top[worst], top[q])) worst = q; }
                } else if (better(e, top[worst])) {
                    top[worst] = e;
                    worst = 0; for (int q = 1; q < 20; ++q) if (better(top[worst], top[q])) worst = q;
                }
                k = j;
            }
        };
        if (V <= 65536) {
            std::vector<uint32_t> keys(tc);
            for (size_t k = 0; k < tc; ++k) { uint64_t v = pairs[k]; keys[k] = (uint32_t)((v >> 16) & 0xFFFF0000u) | (uint32_t)(v & 0xFFFFu); }
            // note: v = (prev<<32)|cur, prev<65536 so (v>>16)&0xFFFF0000 = prev<<16, cur = v&0xFFFF
            std::vector<uint64_t>().swap(pairs);
            std::vector<uint32_t> aux(tc);
            radixScan(keys.data(), aux.data(), 32,
                [](uint32_t v) { return (int)(v >> 16); },
                [](uint32_t v) { return (int)(v & 0xFFFFu); });
        } else {
            std::vector<uint64_t> aux(tc);
            radixScan(pairs.data(), aux.data(), 64,
                [](uint64_t v) { return (int)(v >> 32); },
                [](uint64_t v) { return (int)(v & 0xFFFFFFFFu); });
        }
    }
    std::sort(top, top + topN, [&](const Entry& x, const Entry& y) { return better(x, y); });

    std::string out;
    out.reserve(1024);
    out += "words "; out += std::to_string(W); out += '\n';
    out += "pairs "; out += std::to_string(T); out += '\n';
    out += "distinct "; out += std::to_string(D); out += '\n';
    for (int k = 0; k < topN; ++k) {
        out += std::to_string(top[k].count); out += ' ';
        out.append((const char*)ar + woff[top[k].a], (size_t)wlen[top[k].a]); out += ' ';
        out.append((const char*)ar + woff[top[k].b], (size_t)wlen[top[k].b]); out += '\n';
    }
    fwrite(out.data(), 1, out.size(), stdout);
    return 0;
}
