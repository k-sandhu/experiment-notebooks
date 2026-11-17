#include <cstdio>
#include <cstdint>
#include <cstring>
#include <cstdlib>
#include <vector>
#include <algorithm>
#include <io.h>
#include <fcntl.h>

static uint8_t LOWER[256];
static uint32_t RADIX[256];

// ---------------------------------------------------------------------------
// Word interner.
//
// Every distinct word is represented by (prefix0, prefix1, len), where the
// prefixes are the first 16 lowercased letters packed little-endian and
// zero-padded.  Because letters are never 0x00 this identifies any word of at
// most 16 letters exactly; longer words are verified against their bytes in
// the input buffer.  A hash of the prefixes picks the slot, so the table can
// be rebuilt without touching the input text.
//
// Entry layout is kept compact so a probe touches a single cache line.
// ---------------------------------------------------------------------------
struct WEntry {
    uint64_t p0, p1;
    uint32_t len;
    int32_t id;
};

static std::vector<WEntry> tab;
static uint32_t mask;
static std::vector<int32_t> wOff;
static std::vector<int32_t> wLen;
static const uint8_t* GBUF = nullptr;

static inline uint64_t mixKey(uint64_t p0, uint64_t p1, uint32_t len) {
    uint64_t h = p0 * 0x9E3779B97F4A7C15ULL;
    h ^= (p1 + (uint64_t)len) * 0xC2B2AE3D27D4EB4FULL;
    h ^= h >> 29;
    h *= 0xBF58476D1CE4E5B9ULL;
    h ^= h >> 32;
    return h;
}

static void rehash(uint32_t cap) {
    std::vector<WEntry> t(cap);
    for (uint32_t q = 0; q < cap; ++q) { t[q].id = -1; t[q].len = 0; t[q].p0 = 0; t[q].p1 = 0; }
    uint32_t m = cap - 1;
    for (size_t q = 0; q < tab.size(); ++q) {
        const WEntry& e = tab[q];
        if (e.id < 0) continue;
        uint32_t idx = (uint32_t)mixKey(e.p0, e.p1, e.len) & m;
        while (t[idx].id >= 0) idx = (idx + 1) & m;
        t[idx] = e;
    }
    tab.swap(t);
    mask = m;
}

static inline uint64_t load64(const uint8_t* p) {
    uint64_t v;
    std::memcpy(&v, p, 8);
    return v;
}

static inline int32_t internWord(uint64_t p0, uint64_t p1, uint32_t len, const uint8_t* wstart, uint32_t off) {
    uint32_t idx = (uint32_t)mixKey(p0, p1, len) & mask;
    for (;;) {
        WEntry& e = tab[idx];
        if (e.id < 0) break;
        if (e.len == len && e.p0 == p0 && e.p1 == p1) {
            if (len <= 16 ||
                std::memcmp(GBUF + (uint32_t)wOff[e.id] + 16, wstart + 16, len - 16) == 0)
                return e.id;
        }
        idx = (idx + 1) & mask;
    }
    int32_t id = (int32_t)wOff.size();
    wOff.push_back((int32_t)off);
    wLen.push_back((int32_t)len);
    tab[idx].p0 = p0;
    tab[idx].p1 = p1;
    tab[idx].len = len;
    tab[idx].id = id;
    if (wOff.size() * 10 > tab.size() * 7) {
        uint32_t cap = (uint32_t)tab.size() << 1;
        rehash(cap);
    }
    return id;
}

struct Item { uint32_t cnt; int32_t a, b; };

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    _setmode(_fileno(stdout), _O_BINARY);

    for (int c = 'a'; c <= 'z'; ++c) LOWER[c] = (uint8_t)c;
    for (int c = 'A'; c <= 'Z'; ++c) LOWER[c] = (uint8_t)(c + 32);

    // ---- read the whole input -------------------------------------------
    FILE* f = fopen(argv[1], "rb");
    if (!f) return 1;
    _fseeki64(f, 0, SEEK_END);
    long long fsz = _ftelli64(f);
    _fseeki64(f, 0, SEEK_SET);
    std::vector<uint8_t> data((size_t)fsz + 32);
    size_t got = fread(data.data(), 1, (size_t)fsz, f);
    fclose(f);
    for (int q = 0; q < 32; ++q) data[got + q] = 0;
    uint8_t* buf = data.data();
    size_t n = got;
    GBUF = buf;

    tab.resize(4096);
    for (uint32_t q = 0; q < 4096; ++q) { tab[q].id = -1; tab[q].len = 0; tab[q].p0 = 0; tab[q].p1 = 0; }
    mask = 4095;
    wOff.reserve(1 << 16);
    wLen.reserve(1 << 16);

    std::vector<uint64_t> pairs;
    pairs.reserve(n / 6 + 1024);

    int32_t prev = -1;
    int64_t W = 0, T = 0;
    size_t i = 0;

    // ---- scan words ------------------------------------------------------
    while (i < n) {
        uint32_t lc = LOWER[buf[i]];
        if (lc) {
            uint32_t start = (uint32_t)i;
            do {
                buf[i] = (uint8_t)lc;
                ++i;
                lc = (i < n) ? LOWER[buf[i]] : 0;
            } while (lc);
            uint32_t len = (uint32_t)i - start;

            uint64_t r0 = load64(buf + start);
            uint64_t p0 = (len >= 8) ? r0 : (r0 & ((1ULL << (8 * len)) - 1));
            uint64_t p1 = 0;
            if (len > 8) {
                uint64_t r1 = load64(buf + start + 8);
                uint32_t rem = len - 8;
                p1 = (rem >= 8) ? r1 : (r1 & ((1ULL << (8 * rem)) - 1));
            }

            int32_t id = internWord(p0, p1, len, buf + start, start);
            ++W;
            if (prev >= 0) {
                pairs.push_back(((uint64_t)(uint32_t)prev << 32) | (uint32_t)id);
                ++T;
            }
            prev = id;
        } else {
            uint8_t c = buf[i];
            if (c == '.' || c == '!' || c == '?') prev = -1;
            ++i;
        }
    }

    // ---- sort pair keys (LSD radix, 8-bit digits, cache friendly) --------
    size_t m = pairs.size();
    uint64_t* keys = pairs.data();
    std::vector<uint64_t> tmp;
    if (m > 1) {
        uint64_t orAll = 0;
        for (size_t k = 0; k < m; ++k) orAll |= keys[k];
        tmp.resize(m);
        uint64_t* src = keys;
        uint64_t* dst = tmp.data();
        for (int pass = 0; pass < 8; ++pass) {
            int shift = 8 * pass;
            if (((orAll >> shift) & 0xFFULL) == 0) continue;
            std::memset(RADIX, 0, sizeof(RADIX));
            for (size_t k = 0; k < m; ++k)
                ++RADIX[(src[k] >> shift) & 0xFF];
            uint32_t sum = 0;
            for (int d = 0; d < 256; ++d) {
                uint32_t c = RADIX[d];
                RADIX[d] = sum;
                sum += c;
            }
            for (size_t k = 0; k < m; ++k) {
                uint64_t key = src[k];
                dst[RADIX[(key >> shift) & 0xFF]++] = key;
            }
            uint64_t* t = src; src = dst; dst = t;
        }
        keys = src;
    }

    // ---- count runs, keep the best 20 ------------------------------------
    const int32_t* woff = wOff.data();
    const int32_t* wlen = wLen.data();

    auto cmpWord = [&](int32_t x, int32_t y) -> int {
        int lx = wlen[x], ly = wlen[y];
        int l = lx < ly ? lx : ly;
        int c = std::memcmp(buf + woff[x], buf + woff[y], (size_t)l);
        if (c) return c;
        return lx - ly;
    };
    auto better = [&](const Item& x, const Item& y) -> bool {
        if (x.cnt != y.cnt) return x.cnt > y.cnt;
        int c = cmpWord(x.a, y.a);
        if (c) return c < 0;
        return cmpWord(x.b, y.b) < 0;
    };
    auto worse = [&](const Item& x, const Item& y) -> bool { return better(y, x); };

    Item best[20];
    int bn = 0;
    uint64_t distinct = 0;

    auto pushItem = [&](const Item& it) {
        best[bn] = it;
        int idx = bn++;
        while (idx > 0) {
            int p = (idx - 1) >> 1;
            if (worse(best[idx], best[p])) {
                Item t = best[idx]; best[idx] = best[p]; best[p] = t;
                idx = p;
            } else break;
        }
    };
    auto replaceRoot = [&](const Item& it) {
        best[0] = it;
        int idx = 0;
        for (;;) {
            int l = 2 * idx + 1, r = l + 1, w = idx;
            if (l < bn && worse(best[l], best[w])) w = l;
            if (r < bn && worse(best[r], best[w])) w = r;
            if (w == idx) break;
            Item t = best[idx]; best[idx] = best[w]; best[w] = t;
            idx = w;
        }
    };

    size_t k = 0;
    while (k < m) {
        size_t j = k + 1;
        uint64_t key = keys[k];
        while (j < m && keys[j] == key) ++j;
        Item it;
        it.cnt = (uint32_t)(j - k);
        it.a = (int32_t)(key >> 32);
        it.b = (int32_t)(key & 0xFFFFFFFFu);
        if (bn < 20) pushItem(it);
        else if (better(it, best[0])) replaceRoot(it);
        ++distinct;
        k = j;
    }
    std::sort(best, best + bn, better);

    // ---- output ----------------------------------------------------------
    printf("words %lld\npairs %lld\ndistinct %llu\n",
           (long long)W, (long long)T, (unsigned long long)distinct);
    for (int q = 0; q < bn; ++q) {
        const Item& it = best[q];
        printf("%u %.*s %.*s\n", it.cnt,
               (int)wlen[it.a], (const char*)(buf + woff[it.a]),
               (int)wlen[it.b], (const char*)(buf + woff[it.b]));
    }
    return 0;
}
