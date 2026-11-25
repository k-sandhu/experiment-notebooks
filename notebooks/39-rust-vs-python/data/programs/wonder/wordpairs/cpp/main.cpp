#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cstdint>
#include <vector>
#include <algorithm>
#include <string>
#include <io.h>
#include <fcntl.h>

static inline bool isLetter(unsigned char c) {
    return (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z');
}
static inline unsigned char toLow(unsigned char c) {
    return (c >= 'A' && c <= 'Z') ? (unsigned char)(c + 32) : c;
}
static inline uint64_t mix64(uint64_t x) {
    x ^= x >> 32;
    x *= 0xd6e8feb86659fd93ULL;
    x ^= x >> 32;
    return x;
}

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    FILE* f = nullptr;
    fopen_s(&f, argv[1], "rb");
    if (!f) return 1;
    fseek(f, 0, SEEK_END);
    long long fsize = _ftelli64(f);
    fseek(f, 0, SEEK_SET);
    size_t n = (size_t)fsize;
    std::vector<unsigned char> data(n + 1);
    if (n) {
        size_t rd = fread(data.data(), 1, n, f);
        n = rd;
    }
    fclose(f);
    const unsigned char* buf = data.data();

    // Word interning table (open addressing)
    size_t wcap = 1 << 17; // 131072
    size_t wmask = wcap - 1;
    std::vector<int32_t> wtab(wcap, -1);
    std::vector<uint32_t> whash(wcap, 0);
    // word storage
    std::vector<char> arena;
    arena.reserve(1 << 19);
    std::vector<uint32_t> woff;
    std::vector<uint32_t> wlen;
    woff.reserve(45000);
    wlen.reserve(45000);
    int32_t vocab = 0;

    // Pair table
    size_t pcap = 1 << 21;
    size_t pmask = pcap - 1;
    std::vector<uint64_t> pkeys(pcap, UINT64_MAX);
    std::vector<uint32_t> pcounts(pcap, 0);
    size_t psize = 0;

    auto pairGrow = [&]() {
        size_t ncap = pcap * 2;
        size_t nmask = ncap - 1;
        std::vector<uint64_t> nk(ncap, UINT64_MAX);
        std::vector<uint32_t> nc(ncap, 0);
        for (size_t i = 0; i < pcap; i++) {
            uint64_t k = pkeys[i];
            if (k == UINT64_MAX) continue;
            size_t idx = (size_t)mix64(k) & nmask;
            while (nk[idx] != UINT64_MAX) idx = (idx + 1) & nmask;
            nk[idx] = k; nc[idx] = pcounts[i];
        }
        pkeys.swap(nk); pcounts.swap(nc); pcap = ncap; pmask = nmask;
    };
    auto wordGrow = [&]() {
        size_t ncap = wcap * 2;
        size_t nmask = ncap - 1;
        std::vector<int32_t> nt(ncap, -1);
        std::vector<uint32_t> nh(ncap, 0);
        for (size_t i = 0; i < wcap; i++) {
            int32_t id = wtab[i];
            if (id < 0) continue;
            size_t idx = whash[i] & nmask;
            while (nt[idx] != -1) idx = (idx + 1) & nmask;
            nt[idx] = id; nh[idx] = whash[i];
        }
        wtab.swap(nt); whash.swap(nh); wcap = ncap; wmask = nmask;
    };

    long long W = 0, T = 0;
    int32_t prev = -1;
    size_t i = 0;
    while (i < n) {
        unsigned char c = buf[i];
        if (isLetter(c)) {
            size_t start = i;
            uint32_t h = 2166136261u;
            while (i < n && isLetter(buf[i])) {
                h ^= toLow(buf[i]);
                h *= 16777619u;
                i++;
            }
            size_t len = i - start;
            // intern
            int32_t id;
            size_t idx = h & wmask;
            while (true) {
                int32_t cur = wtab[idx];
                if (cur < 0) {
                    id = vocab++;
                    uint32_t off = (uint32_t)arena.size();
                    for (size_t j = start; j < i; j++) arena.push_back((char)toLow(buf[j]));
                    woff.push_back(off);
                    wlen.push_back((uint32_t)len);
                    wtab[idx] = id; whash[idx] = h;
                    if ((size_t)vocab * 2 > wcap) wordGrow();
                    break;
                }
                if (whash[idx] == h && wlen[cur] == len) {
                    uint32_t off = woff[cur];
                    bool eq = true;
                    for (size_t j = 0; j < len; j++) {
                        if ((unsigned char)arena[off + j] != toLow(buf[start + j])) { eq = false; break; }
                    }
                    if (eq) { id = cur; break; }
                }
                idx = (idx + 1) & wmask;
            }
            W++;
            if (prev >= 0) {
                T++;
                uint64_t key = ((uint64_t)(uint32_t)prev << 32) | (uint32_t)id;
                size_t pi = (size_t)mix64(key) & pmask;
                while (true) {
                    uint64_t k = pkeys[pi];
                    if (k == UINT64_MAX) {
                        pkeys[pi] = key; pcounts[pi] = 1; psize++;
                        if (psize * 10 > pcap * 7) pairGrow();
                        break;
                    }
                    if (k == key) { pcounts[pi]++; break; }
                    pi = (pi + 1) & pmask;
                }
            }
            prev = id;
            // note: terminator check happens in else branch for the delimiter byte; do not consume it here
        } else {
            if (c == '.' || c == '!' || c == '?') prev = -1;
            i++;
        }
    }

    long long D = (long long)psize;

    // Top 20: insertion into sorted array best..worst
    struct Cand { uint32_t count; int32_t a; int32_t b; };
    auto wordCmp = [&](int32_t a, int32_t b) -> int {
        if (a == b) return 0;
        uint32_t oa = woff[a], ob = woff[b];
        uint32_t la = wlen[a], lb = wlen[b];
        uint32_t m = la < lb ? la : lb;
        int cmp = m ? memcmp(arena.data() + oa, arena.data() + ob, m) : 0;
        if (cmp != 0) return cmp;
        if (la < lb) return -1;
        if (la > lb) return 1;
        return 0;
    };
    // returns true if x is strictly better than y
    auto better = [&](const Cand& x, const Cand& y) -> bool {
        if (x.count != y.count) return x.count > y.count;
        int c = wordCmp(x.a, y.a);
        if (c != 0) return c < 0;
        return wordCmp(x.b, y.b) < 0;
    };
    Cand top[20];
    int tsz = 0;
    for (size_t k = 0; k < pcap; k++) {
        if (pkeys[k] == UINT64_MAX) continue;
        Cand cand{ pcounts[k], (int32_t)(pkeys[k] >> 32), (int32_t)(pkeys[k] & 0xffffffffULL) };
        if (tsz < 20) {
            int pos = tsz++;
            while (pos > 0 && better(cand, top[pos - 1])) { top[pos] = top[pos - 1]; pos--; }
            top[pos] = cand;
        } else {
            if (!better(cand, top[19])) continue;
            int pos = 19;
            while (pos > 0 && better(cand, top[pos - 1])) { top[pos] = top[pos - 1]; pos--; }
            top[pos] = cand;
        }
    }

    std::string out;
    out.reserve(1024);
    out += "words "; out += std::to_string(W); out += '\n';
    out += "pairs "; out += std::to_string(T); out += '\n';
    out += "distinct "; out += std::to_string(D); out += '\n';
    for (int k = 0; k < tsz; k++) {
        out += std::to_string(top[k].count); out += ' ';
        out.append(arena.data() + woff[top[k].a], wlen[top[k].a]);
        out += ' ';
        out.append(arena.data() + woff[top[k].b], wlen[top[k].b]);
        out += '\n';
    }
    _setmode(_fileno(stdout), _O_BINARY);
    fwrite(out.data(), 1, out.size(), stdout);
    return 0;
}
