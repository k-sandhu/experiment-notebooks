#define _CRT_SECURE_NO_WARNINGS
#include <cstdio>
#include <cstdlib>
#include <cstdint>
#include <cstring>
#include <string>
#include <vector>
#include <new>
#include <bit>
#include <algorithm>

#if defined(_M_X64) || defined(_M_IX86) || defined(__SSE2__)
#include <emmintrin.h>
#define WP_SSE2 1
#endif
#if defined(_MSC_VER)
#include <intrin.h>
#define WP_NOINLINE __declspec(noinline)
#else
#define WP_NOINLINE __attribute__((noinline))
#endif

static inline unsigned ctz64(uint64_t x) {
#if defined(_MSC_VER) && defined(_M_X64)
    return (unsigned)_tzcnt_u64(x);
#else
    return (unsigned)std::countr_zero(x);
#endif
}

struct Entry {
    uint64_t lo, hi;
    uint32_t len, id;
    uint64_t pad;
};

static Entry* g_table = nullptr;
static uint64_t g_mask = 0;
static unsigned g_shift = 0;
static uint64_t g_cap = 0;
static uint32_t g_count = 0;
static std::vector<char> g_arena;
static std::vector<uint64_t> g_off;
static std::vector<uint32_t> g_len;

static inline uint64_t mixHash(uint64_t lo, uint64_t hi) {
    uint64_t h = (lo * 0x9E3779B97F4A7C15ull) ^ (hi * 0xC2B2AE3D27D4EB4Full);
    h ^= h >> 32;
    h *= 0xD6E8FEB86659FD93ull;
    return h;
}

static Entry* allocTable(uint64_t cap) {
    size_t bytes = (size_t)cap * sizeof(Entry);
    Entry* t = (Entry*)::operator new(bytes, std::align_val_t(64));
    memset(t, 0, bytes);
    return t;
}

static void growTable() {
    uint64_t ncap = g_cap * 2;
    unsigned nshift = g_shift - 1;
    uint64_t nmask = ncap - 1;
    Entry* nt = allocTable(ncap);
    for (uint64_t i = 0; i < g_cap; i++) {
        const Entry& e = g_table[i];
        if (e.len == 0) continue;
        uint64_t idx = mixHash(e.lo, e.hi) >> nshift;
        while (nt[idx].len != 0) idx = (idx + 1) & nmask;
        nt[idx] = e;
    }
    ::operator delete(g_table, std::align_val_t(64));
    g_table = nt;
    g_cap = ncap;
    g_mask = nmask;
    g_shift = nshift;
}

static WP_NOINLINE uint32_t insertWord(uint64_t lo, uint64_t hi, uint32_t len, uint64_t idx,
                                       const unsigned char* p) {
    uint32_t id = g_count++;
    g_off.push_back((uint64_t)g_arena.size());
    g_len.push_back(len);
    if (len <= 16) {
        char tmp[16];
        memcpy(tmp, &lo, 8);
        memcpy(tmp + 8, &hi, 8);
        g_arena.insert(g_arena.end(), tmp, tmp + len);
    } else {
        g_arena.insert(g_arena.end(), (const char*)p, (const char*)p + len);
    }
    Entry& e = g_table[idx];
    e.lo = lo;
    e.hi = hi;
    e.len = len;
    e.id = id;
    if ((uint64_t)g_count * 2 > g_cap) growTable();
    return id;
}

static inline uint64_t hashLong(const unsigned char* p, size_t len) {
    uint64_t h = 0x243F6A8885A308D3ull ^ (uint64_t)len;
    size_t i = 0;
    for (; i + 8 <= len; i += 8) {
        uint64_t w;
        memcpy(&w, p + i, 8);
        h = (h ^ w) * 0x9E3779B97F4A7C15ull;
        h ^= h >> 29;
    }
    if (i < len) {
        uint64_t w;
        memcpy(&w, p + i, 8);
        w &= (1ull << (8 * (len - i))) - 1;
        h = (h ^ w) * 0x9E3779B97F4A7C15ull;
        h ^= h >> 29;
    }
    return h;
}

static WP_NOINLINE uint32_t lookupLong(unsigned char* p, size_t len) {
    for (size_t i = 0; i < len; i++) p[i] |= 0x20;
    uint64_t lo;
    memcpy(&lo, p, 8);
    uint64_t hi = hashLong(p, len);
    uint32_t l32 = (uint32_t)len;
    uint64_t idx = mixHash(lo, hi) >> g_shift;
    for (;;) {
        const Entry& en = g_table[idx];
        if (en.len == 0) return insertWord(lo, hi, l32, idx, p);
        if (en.lo == lo && en.hi == hi && en.len == l32 &&
            memcmp(g_arena.data() + g_off[en.id], p, len) == 0)
            return en.id;
        idx = (idx + 1) & g_mask;
    }
}

static inline void blockMasks(const unsigned char* p, uint64_t& Lout, uint64_t& Tout) {
#ifdef WP_SSE2
    const __m128i c20 = _mm_set1_epi8(0x20);
    const __m128i lob = _mm_set1_epi8(0x60);
    const __m128i hib = _mm_set1_epi8(0x7B);
    const __m128i dot = _mm_set1_epi8('.');
    const __m128i exc = _mm_set1_epi8('!');
    const __m128i que = _mm_set1_epi8('?');
    uint64_t L = 0, T = 0;
    for (int k = 0; k < 4; k++) {
        __m128i v = _mm_loadu_si128((const __m128i*)(p + 16 * k));
        __m128i t = _mm_or_si128(v, c20);
        __m128i l = _mm_and_si128(_mm_cmpgt_epi8(t, lob), _mm_cmpgt_epi8(hib, t));
        __m128i e = _mm_or_si128(_mm_or_si128(_mm_cmpeq_epi8(v, dot), _mm_cmpeq_epi8(v, exc)),
                                 _mm_cmpeq_epi8(v, que));
        L |= (uint64_t)(uint32_t)_mm_movemask_epi8(l) << (16 * k);
        T |= (uint64_t)(uint32_t)_mm_movemask_epi8(e) << (16 * k);
    }
    Lout = L;
    Tout = T;
#else
    uint64_t L = 0, T = 0;
    for (int k = 0; k < 64; k++) {
        unsigned char c = p[k];
        unsigned char t = (unsigned char)(c | 0x20);
        if (t >= 'a' && t <= 'z') L |= 1ull << k;
        if (c == '.' || c == '!' || c == '?') T |= 1ull << k;
    }
    Lout = L;
    Tout = T;
#endif
}

struct Top {
    uint32_t c, f, s;
};

static inline int wordCmp(uint32_t a, uint32_t b) {
    uint32_t la = g_len[a], lb = g_len[b];
    int r = memcmp(g_arena.data() + g_off[a], g_arena.data() + g_off[b], la < lb ? la : lb);
    if (r != 0) return r;
    return la < lb ? -1 : (la > lb ? 1 : 0);
}

static inline bool pairBefore(const Top& x, const Top& y) {
    if (x.c != y.c) return x.c > y.c;
    if (x.f != y.f) return wordCmp(x.f, y.f) < 0;
    if (x.s != y.s) return wordCmp(x.s, y.s) < 0;
    return false;
}

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    FILE* f = fopen(argv[1], "rb");
    if (!f) return 1;
    setvbuf(f, nullptr, _IONBF, 0);
#if defined(_MSC_VER)
    _fseeki64(f, 0, SEEK_END);
    long long fsz = _ftelli64(f);
    _fseeki64(f, 0, SEEK_SET);
#else
    fseek(f, 0, SEEK_END);
    long long fsz = ftell(f);
    fseek(f, 0, SEEK_SET);
#endif
    if (fsz < 0) fsz = 0;
    size_t bufCap = ((size_t)fsz / 64 + 1) * 64 + 64;
    unsigned char* buf = (unsigned char*)malloc(bufCap);
    if (!buf) return 1;
    size_t n = 0;
    while (n < (size_t)fsz) {
        size_t r = fread(buf + n, 1, (size_t)fsz - n, f);
        if (r == 0) break;
        n += r;
    }
    fclose(f);
    memset(buf + n, ' ', bufCap - n);

    uint64_t ML[17], MH[17];
    for (int l = 0; l <= 16; l++) {
        ML[l] = l >= 8 ? ~0ull : ((1ull << (8 * l)) - 1);
        MH[l] = l <= 8 ? 0ull : (l >= 16 ? ~0ull : ((1ull << (8 * (l - 8))) - 1));
    }

    g_cap = 1ull << 16;
    g_shift = 48;
    g_mask = g_cap - 1;
    g_table = allocTable(g_cap);
    g_arena.reserve(1 << 20);
    g_off.reserve(1 << 16);
    g_len.reserve(1 << 16);

    uint32_t* tok = (uint32_t*)malloc((n / 2 + 2) * sizeof(uint32_t));
    if (!tok) return 1;
    size_t ntok = 0;

    {
        Entry* table = g_table;
        uint64_t mask = g_mask;
        unsigned shift = g_shift;
        const uint64_t LOWER = 0x2020202020202020ull;

        size_t nblocks = n / 64 + 1;
        uint64_t prevL = 0;
        bool inword = false;
        size_t cstart = 0;
        uint32_t cbrk = 0;
        uint32_t pending = 1;

        for (size_t b = 0; b < nblocks; b++) {
            size_t base = b * 64;
            uint64_t L, T;
            blockMasks(buf + base, L, T);
            uint64_t sh = (L << 1) | prevL;
            uint64_t S = L & ~sh;
            uint64_t E = ~L & sh;
            prevL = L >> 63;

            while (E) {
                unsigned e = ctz64(E);
                E &= E - 1;
                size_t start;
                uint32_t brk;
                if (inword) {
                    start = cstart;
                    brk = cbrk;
                    inword = false;
                } else {
                    unsigned s = ctz64(S);
                    S &= S - 1;
                    uint64_t below = T & ((1ull << s) - 1);
                    brk = pending | (uint32_t)(below != 0);
                    T ^= below;
                    pending = 0;
                    start = base + s;
                }
                size_t len = (base + e) - start;
                uint32_t id;
                if (len <= 16) {
                    const unsigned char* p = buf + start;
                    uint64_t lo, hi;
                    memcpy(&lo, p, 8);
                    memcpy(&hi, p + 8, 8);
                    lo = (lo | LOWER) & ML[len];
                    hi = (hi | LOWER) & MH[len];
                    uint32_t l32 = (uint32_t)len;
                    uint64_t idx = mixHash(lo, hi) >> shift;
                    for (;;) {
                        const Entry& en = table[idx];
                        if (((en.lo ^ lo) | (en.hi ^ hi) | (uint64_t)(en.len ^ l32)) == 0) {
                            id = en.id;
                            break;
                        }
                        if (en.len == 0) {
                            id = insertWord(lo, hi, l32, idx, nullptr);
                            table = g_table;
                            mask = g_mask;
                            shift = g_shift;
                            break;
                        }
                        idx = (idx + 1) & mask;
                    }
                } else {
                    id = lookupLong(buf + start, len);
                    table = g_table;
                    mask = g_mask;
                    shift = g_shift;
                }
                tok[ntok++] = id | (brk << 31);
            }
            if (S) {
                unsigned s = ctz64(S);
                uint64_t below = T & ((1ull << s) - 1);
                cbrk = pending | (uint32_t)(below != 0);
                T ^= below;
                pending = 0;
                cstart = base + s;
                inword = true;
            }
            pending |= (uint32_t)(T != 0);
        }
    }

    const size_t W = ntok;
    const uint32_t V = g_count;
    const uint32_t IDM = 0x7FFFFFFFu;

    uint64_t Tpairs = 0;
    uint64_t D = 0;
    Top top[20];
    int ntop = 0;

    if (W >= 2) {
        std::vector<size_t> pos(V, 0), beg(V, 0);
        {
            uint32_t prev = tok[0] & IDM;
            for (size_t i = 1; i < W; i++) {
                uint32_t t = tok[i];
                pos[prev] += 1 - (t >> 31);
                prev = t & IDM;
            }
        }
        size_t run = 0;
        for (uint32_t w = 0; w < V; w++) {
            size_t c = pos[w];
            beg[w] = run;
            pos[w] = run;
            run += c + 1;
            Tpairs += c;
        }
        uint32_t* second = (uint32_t*)malloc((run + 1) * sizeof(uint32_t));
        if (!second) return 1;
        {
            uint32_t prev = tok[0] & IDM;
            for (size_t i = 1; i < W; i++) {
                uint32_t t = tok[i];
                uint32_t id = t & IDM;
                size_t ps = pos[prev];
                second[ps] = id;
                pos[prev] = ps + (1 - (t >> 31));
                prev = id;
            }
        }

        std::vector<uint32_t> c2v(V, 0);
        uint32_t* c2 = c2v.data();
        uint32_t thr = 1;
        int worst = -1;

        auto findWorst = [&]() {
            int wi = 0;
            for (int i = 1; i < ntop; i++)
                if (pairBefore(top[wi], top[i])) wi = i;
            worst = wi;
            thr = top[wi].c;
        };
        auto consider = [&](uint32_t c, uint32_t fw, uint32_t sw) {
            Top t{c, fw, sw};
            if (ntop < 20) {
                top[ntop++] = t;
                if (ntop == 20) findWorst();
                return;
            }
            if (!pairBefore(t, top[worst])) return;
            top[worst] = t;
            findWorst();
        };

        for (uint32_t fw = 0; fw < V; fw++) {
            const uint32_t* a = second + beg[fw];
            const uint32_t* e = second + pos[fw];
            if (a == e) continue;
            for (const uint32_t* q = a; q < e; q++) c2[*q]++;
            for (const uint32_t* q = a; q < e; q++) {
                uint32_t s = *q;
                uint32_t c = c2[s];
                c2[s] = 0;
                D += (c != 0);
                if (c >= thr) consider(c, fw, s);
            }
        }
        free(second);
    }

    std::sort(top, top + ntop, [](const Top& x, const Top& y) { return pairBefore(x, y); });

    std::string out;
    out.reserve(4096);
    out += "words ";
    out += std::to_string((unsigned long long)W);
    out += "\npairs ";
    out += std::to_string((unsigned long long)Tpairs);
    out += "\ndistinct ";
    out += std::to_string((unsigned long long)D);
    out += "\n";
    for (int i = 0; i < ntop; i++) {
        out += std::to_string(top[i].c);
        out += ' ';
        out.append(g_arena.data() + g_off[top[i].f], g_len[top[i].f]);
        out += ' ';
        out.append(g_arena.data() + g_off[top[i].s], g_len[top[i].s]);
        out += '\n';
    }
    fwrite(out.data(), 1, out.size(), stdout);
    fflush(stdout);
    return 0;
}
