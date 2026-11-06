#include <cstdio>
#include <cstdint>
#include <cstring>
#include <cstdlib>
#include <vector>
#include <string>
#include <algorithm>
#include <io.h>
#include <fcntl.h>

// ---------- word table: open addressing, ids into a byte arena ----------
static std::vector<uint32_t> wSlot;   // id+1, 0 = empty
static std::vector<uint32_t> wHash;   // full hash per slot
static std::vector<uint32_t> wOff;    // per id: offset in arena
static std::vector<uint32_t> wLen;    // per id: length
static std::vector<char> wArena;      // lowercased word bytes
static uint32_t wMask = 0, wCount = 0;

static inline uint32_t hashBytes(const unsigned char* p, uint32_t n) {
    uint32_t h = 2166136261u;
    for (uint32_t i = 0; i < n; i++) {
        h ^= p[i];
        h *= 16777619u;
    }
    return h ? h : 1;
}

static void wGrow() {
    uint32_t cap = wMask + 1, cap2 = cap * 2;
    std::vector<uint32_t> s2(cap2, 0), h2(cap2);
    uint32_t m2 = cap2 - 1;
    for (uint32_t i = 0; i < cap; i++) {
        if (wSlot[i]) {
            uint32_t j = wHash[i] & m2;
            while (s2[j]) j = (j + 1) & m2;
            s2[j] = wSlot[i];
            h2[j] = wHash[i];
        }
    }
    wSlot.swap(s2);
    wHash.swap(h2);
    wMask = m2;
}

static uint32_t wordFindOrAdd(const char* w, uint32_t n, uint32_t h) {
    uint32_t i = h & wMask;
    while (wSlot[i]) {
        uint32_t id = wSlot[i] - 1;
        if (wHash[i] == h && wLen[id] == n &&
            memcmp(wArena.data() + wOff[id], w, n) == 0)
            return id;
        i = (i + 1) & wMask;
    }
    if ((uint64_t)(wCount + 1) * 3 > (uint64_t)(wMask + 1) * 2) {
        wGrow();
        i = h & wMask;
        while (wSlot[i]) i = (i + 1) & wMask;
    }
    uint32_t id = wCount++;
    uint32_t o = (uint32_t)wArena.size();
    wArena.insert(wArena.end(), w, w + n);
    wOff.push_back(o);
    wLen.push_back(n);
    wSlot[i] = id + 1;
    wHash[i] = h;
    return id;
}

static inline int cmpWords(uint32_t a, uint32_t b) {
    uint32_t la = wLen[a], lb = wLen[b];
    const unsigned char* pa = (const unsigned char*)wArena.data() + wOff[a];
    const unsigned char* pb = (const unsigned char*)wArena.data() + wOff[b];
    uint32_t m = la < lb ? la : lb;
    for (uint32_t i = 0; i < m; i++)
        if (pa[i] != pb[i]) return pa[i] < pb[i] ? -1 : 1;
    return la < lb ? -1 : la > lb ? 1 : 0;
}

// ---------- pair table: open addressing on packed (id1,id2) ----------
static const uint64_t PEMPTY = 0xFFFFFFFFFFFFFFFFull;
static std::vector<uint64_t> pKey;
static std::vector<int32_t> pCnt;
static uint64_t pMask = 0;
static uint64_t pCount = 0;

static inline uint64_t mixKey(uint64_t x) {
    x *= 0x9E3779B97F4A7C15ull;
    x ^= x >> 32;
    x *= 0xBF58476D1CE4E5B9ull;
    x ^= x >> 29;
    return x;
}

static void pGrow() {
    uint64_t cap = pMask + 1, cap2 = cap * 2, m2 = cap2 - 1;
    std::vector<uint64_t> k2(cap2, PEMPTY);
    std::vector<int32_t> c2(cap2, 0);
    for (uint64_t i = 0; i < cap; i++) {
        if (pKey[i] != PEMPTY) {
            uint64_t j = mixKey(pKey[i]) & m2;
            while (k2[j] != PEMPTY) j = (j + 1) & m2;
            k2[j] = pKey[i];
            c2[j] = pCnt[i];
        }
    }
    pKey.swap(k2);
    pCnt.swap(c2);
    pMask = m2;
}

static inline void pairAdd(uint64_t key) {
    uint64_t i = mixKey(key) & pMask;
    while (pKey[i] != PEMPTY) {
        if (pKey[i] == key) {
            pCnt[i]++;
            return;
        }
        i = (i + 1) & pMask;
    }
    if ((pCount + 1) * 3 > (pMask + 1) * 2) {
        pGrow();
        i = mixKey(key) & pMask;
        while (pKey[i] != PEMPTY) i = (i + 1) & pMask;
    }
    pKey[i] = key;
    pCnt[i] = 1;
    pCount++;
}

struct PairRec {
    uint32_t id1, id2;
    int64_t cnt;
};

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    _setmode(_fileno(stdout), _O_BINARY);
    FILE* f = fopen(argv[1], "rb");
    if (!f) return 1;
    fseek(f, 0, SEEK_END);
    long fsz = ftell(f);
    fseek(f, 0, SEEK_SET);
    std::vector<unsigned char> data((size_t)fsz);
    if (fsz > 0 && fread(data.data(), 1, (size_t)fsz, f) != (size_t)fsz) { fclose(f); return 1; }
    fclose(f);

    size_t n = data.size();
    wMask = (1u << 16) - 1;
    wSlot.assign(wMask + 1, 0);
    wHash.assign(wMask + 1, 0);
    wArena.reserve(1 << 16);

    pMask = (1u << 20) - 1;
    pKey.assign(pMask + 1, PEMPTY);
    pCnt.assign(pMask + 1, 0);

    std::vector<unsigned char> wbuf;
    wbuf.reserve(256);

    long long totalWords = 0, totalPairs = 0;
    long prev = -1;
    const unsigned char* d = data.data();

    for (size_t i = 0; i < n; i++) {
        unsigned int c = d[i];
        if ((unsigned int)((c | 0x20u) - 'a') < 26u) {
            if (wbuf.size() == wbuf.capacity()) wbuf.reserve(wbuf.capacity() * 2);
            wbuf.push_back((unsigned char)(c | 0x20u));
        } else {
            if (wbuf.size()) {
                totalWords++;
                uint32_t h = hashBytes(wbuf.data(), (uint32_t)wbuf.size());
                uint32_t id = wordFindOrAdd((const char*)wbuf.data(), (uint32_t)wbuf.size(), h);
                if (prev >= 0) {
                    totalPairs++;
                    pairAdd(((uint64_t)prev << 32) | (uint64_t)id);
                }
                prev = id;
                wbuf.clear();
            }
            if (c == '.' || c == '!' || c == '?') prev = -1;
        }
    }
    if (wbuf.size()) {
        totalWords++;
        uint32_t h = hashBytes(wbuf.data(), (uint32_t)wbuf.size());
        uint32_t id = wordFindOrAdd((const char*)wbuf.data(), (uint32_t)wbuf.size(), h);
        if (prev >= 0) {
            totalPairs++;
            pairAdd(((uint64_t)prev << 32) | (uint64_t)id);
        }
    }

    // top 20 via bounded min-heap (root = worst); avoids materializing all pairs
    uint32_t hId1[20], hId2[20];
    int64_t hCnt[20];
    size_t hc = 0;
    auto worse = [](uint32_t a1, uint32_t a2, int64_t ac, uint32_t b1, uint32_t b2, int64_t bc) -> int {
        if (ac != bc) return ac > bc ? -1 : 1;
        int c = cmpWords(a1, b1);
        if (c) return c;
        return cmpWords(a2, b2);
    };
    for (uint64_t i = 0; i <= pMask; i++) {
        if (pKey[i] == PEMPTY) continue;
        uint32_t id1 = (uint32_t)(pKey[i] >> 32), id2 = (uint32_t)pKey[i];
        int64_t c1 = pCnt[i];
        if (hc < 20) {
            size_t q = hc++;
            hId1[q] = id1; hId2[q] = id2; hCnt[q] = c1;
            while (q > 0) {
                size_t par = (q - 1) / 2;
                if (worse(hId1[q], hId2[q], hCnt[q], hId1[par], hId2[par], hCnt[par]) <= 0) break;
                std::swap(hId1[q], hId1[par]);
                std::swap(hId2[q], hId2[par]);
                std::swap(hCnt[q], hCnt[par]);
                q = par;
            }
        } else if (worse(id1, id2, c1, hId1[0], hId2[0], hCnt[0]) < 0) {
            hId1[0] = id1; hId2[0] = id2; hCnt[0] = c1;
            size_t p = 0;
            for (;;) {
                size_t l = 2 * p + 1, r = l + 1, s = p;
                if (l < hc && worse(hId1[l], hId2[l], hCnt[l], hId1[s], hId2[s], hCnt[s]) > 0) s = l;
                if (r < hc && worse(hId1[r], hId2[r], hCnt[r], hId1[s], hId2[s], hCnt[s]) > 0) s = r;
                if (s == p) break;
                std::swap(hId1[p], hId1[s]);
                std::swap(hId2[p], hId2[s]);
                std::swap(hCnt[p], hCnt[s]);
                p = s;
            }
        }
    }

    size_t k = hc;
    // pop heap worst-first into reversed slots, then sort best-first
    std::vector<PairRec> recs(k);
    while (hc > 0) {
        hc--;
        recs[hc] = {hId1[0], hId2[0], hCnt[0]};
        hId1[0] = hId1[hc]; hId2[0] = hId2[hc]; hCnt[0] = hCnt[hc];
        size_t p = 0;
        for (;;) {
            size_t l = 2 * p + 1, r = l + 1, s = p;
            if (l < hc && worse(hId1[l], hId2[l], hCnt[l], hId1[s], hId2[s], hCnt[s]) > 0) s = l;
            if (r < hc && worse(hId1[r], hId2[r], hCnt[r], hId1[s], hId2[s], hCnt[s]) > 0) s = r;
            if (s == p) break;
            std::swap(hId1[p], hId1[s]);
            std::swap(hId2[p], hId2[s]);
            std::swap(hCnt[p], hCnt[s]);
            p = s;
        }
    }
    std::sort(recs.begin(), recs.begin() + k, [](const PairRec& a, const PairRec& b) {
        if (a.cnt != b.cnt) return a.cnt > b.cnt;
        int c = cmpWords(a.id1, b.id1);
        if (c) return c < 0;
        return cmpWords(a.id2, b.id2) < 0;
    });

    // output
    std::string out;
    out.reserve(4096);
    char tmp[128];
    snprintf(tmp, sizeof tmp, "words %lld\npairs %lld\ndistinct %llu\n",
             totalWords, totalPairs, (unsigned long long)pCount);
    out += tmp;
    for (size_t r = 0; r < k; r++) {
        const PairRec& p = recs[r];
        int m = snprintf(tmp, sizeof tmp, "%lld ", p.cnt);
        out.append(tmp, m);
        out.append(wArena.data() + wOff[p.id1], wLen[p.id1]);
        out.push_back(' ');
        out.append(wArena.data() + wOff[p.id2], wLen[p.id2]);
        out.push_back('\n');
    }
    fwrite(out.data(), 1, out.size(), stdout);
    return 0;
}
