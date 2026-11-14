#define _CRT_SECURE_NO_WARNINGS
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cstdint>
#include <string>
#include <string_view>
#include <vector>
#include <algorithm>
#include <bit>
#include <emmintrin.h>

namespace {

constexpr uint64_t sepMaskOf(const char* s) {
    uint64_t v = 0;
    for (int i = 0; i < 8; i++) if (s[i] != 'd') v |= 0xFFULL << (8 * i);
    return v;
}
constexpr uint64_t sepValOf(const char* s) {
    uint64_t v = 0;
    for (int i = 0; i < 8; i++) if (s[i] != 'd') v |= uint64_t((unsigned char)s[i]) << (8 * i);
    return v;
}
constexpr uint64_t fixOf(const char* s) {
    uint64_t v = 0;
    for (int i = 0; i < 8; i++) if (s[i] != 'd') v |= uint64_t((unsigned char)(s[i] ^ 0x30)) << (8 * i);
    return v;
}
constexpr uint32_t pack4(const char* s) {
    uint32_t v = 0;
    for (int i = 0; i < 4; i++) v |= uint32_t((unsigned char)s[i]) << (8 * i);
    return v;
}

constexpr uint64_t M0 = sepMaskOf("dddd-dd-"), V0 = sepValOf("dddd-dd-"), F0 = fixOf("dddd-dd-");
constexpr uint64_t M1 = sepMaskOf("ddTdd:dd"), V1 = sepValOf("ddTdd:dd"), F1 = fixOf("ddTdd:dd");
constexpr uint64_t M2 = sepMaskOf(":dd.dddZ"), V2 = sepValOf(":dd.dddZ"), F2 = fixOf(":dd.dddZ");

constexpr uint32_t W_GET = pack4("GET "), W_PUT = pack4("PUT "), W_POST = pack4("POST"),
                   W_PATC = pack4("PATC"), W_DELE = pack4("DELE");

inline bool okWord(uint64_t x, uint64_t sepMask, uint64_t sepVal, uint64_t fix) {
    if ((x & sepMask) != sepVal) return false;
    uint64_t y = x ^ fix;
    return ((y & 0xF0F0F0F0F0F0F0F0ULL) |
            (((y + 0x0606060606060606ULL) & 0xF0F0F0F0F0F0F0F0ULL) >> 4)) == 0x3333333333333333ULL;
}

struct Cls {
    unsigned char t[256];
    constexpr Cls() : t{} {
        for (int i = '0'; i <= '9'; i++) t[i] = 1;
        for (int i = 'a'; i <= 'z'; i++) t[i] = 2;
        for (int i = 'A'; i <= 'Z'; i++) t[i] = 2;
        t[(unsigned char)'_'] = 2;
        t[(unsigned char)'-'] = 2;
    }
};
constexpr Cls CLS;

inline bool isdig(char ch) { return (unsigned)((unsigned char)ch - '0') < 10u; }

struct Entry {
    uint32_t* data = nullptr;
    size_t size = 0, cap = 0;
    char* key = nullptr;
    size_t keyLen = 0;
    uint64_t hash = 0;
    std::vector<uint64_t> big;
};

struct Slot { uint32_t tag; uint32_t idx; };

std::vector<Slot> g_slots;
size_t g_mask = 0;
std::vector<Entry> g_entries;
uint64_t g_status[10] = {0};
uint64_t g_lines = 0, g_malformed = 0;
char* g_tb = nullptr;
size_t g_tcap = 0;

__declspec(noinline) void growT(size_t need) {
    size_t nc = g_tcap ? g_tcap : 4096;
    while (nc < need) nc *= 2;
    g_tb = (char*)realloc(g_tb, nc);
    g_tcap = nc;
}

__declspec(noinline) void growData(Entry& e) {
    size_t nc = e.cap ? e.cap * 2 : 16;
    e.data = (uint32_t*)realloc(e.data, nc * sizeof(uint32_t));
    e.cap = nc;
}

void rehash() {
    size_t ns = g_slots.size() * 2;
    std::vector<Slot> nsl(ns, Slot{0, 0});
    size_t mask = ns - 1;
    for (size_t i = 0; i < g_entries.size(); i++) {
        uint64_t h = g_entries[i].hash;
        size_t j = (size_t)h & mask;
        while (nsl[j].idx) j = (j + 1) & mask;
        nsl[j] = Slot{(uint32_t)(h >> 32), (uint32_t)(i + 1)};
    }
    g_slots.swap(nsl);
    g_mask = mask;
}

__declspec(noinline) Entry& insertNew(const char* t, size_t len, uint64_t h, size_t slot) {
    Entry e;
    e.key = (char*)malloc(len + 8);
    memcpy(e.key, t, len + 8); // includes 8 zero pad bytes
    e.keyLen = len;
    e.hash = h;
    g_entries.push_back(std::move(e));
    g_slots[slot] = Slot{(uint32_t)(h >> 32), (uint32_t)g_entries.size()};
    if (g_entries.size() * 2 > g_slots.size()) rehash();
    return g_entries.back();
}

inline bool eqPadded(const char* a, const char* b, size_t len) {
    for (size_t k = 0; k < len; k += 8) {
        uint64_t x, y;
        memcpy(&x, a + k, 8);
        memcpy(&y, b + k, 8);
        if (x != y) return false;
    }
    return true;
}

inline Entry& lookup(const char* t, size_t len, uint64_t h) {
    uint32_t tag = (uint32_t)(h >> 32);
    size_t mask = g_mask;
    size_t i = (size_t)h & mask;
    const Slot* slots = g_slots.data();
    Entry* ents = g_entries.data();
    for (;;) {
        Slot s = slots[i];
        if (s.idx == 0) break;
        if (s.tag == tag) {
            Entry& e = ents[s.idx - 1];
            if (e.keyLen == len && eqPadded(e.key, t, len)) return e;
        }
        i = (i + 1) & mask;
    }
    return insertNew(t, len, h, i);
}

// p .. end: end is one past the last '\n' of the region; region consists of complete lines
void process(const char* p, const char* end) {
    uint64_t lines = 0, malformed = 0;
    char* tb = g_tb;
    size_t tcap = g_tcap;
    const __m128i qv = _mm_set1_epi8('"');
    const __m128i nv = _mm_set1_epi8('\n');

    while (p < end) {
        ++lines;
        const char* c = p;
        {
            uint64_t w0, w1, w2;
            memcpy(&w0, p, 8);
            memcpy(&w1, p + 8, 8);
            memcpy(&w2, p + 16, 8);
            if (!okWord(w0, M0, V0, F0) || !okWord(w1, M1, V1, F1) || !okWord(w2, M2, V2, F2) ||
                p[24] != ' ')
                goto bad;
            c = p + 25;

            // host: [a-z]+-\d+
            {
                const char* s = c;
                while ((unsigned)((unsigned char)*c - 'a') < 26u) ++c;
                if (c == s || *c != '-') goto bad;
                ++c;
                s = c;
                while (isdig(*c)) ++c;
                if (c == s || *c != ' ') goto bad;
                ++c;
            }

            // method
            {
                uint32_t m;
                memcpy(&m, c, 4);
                if (m == W_GET || m == W_PUT) c += 4;
                else if (m == W_POST && c[4] == ' ') c += 5;
                else if (m == W_PATC && c[4] == 'H' && c[5] == ' ') c += 6;
                else if (m == W_DELE && c[4] == 'T' && c[5] == 'E' && c[6] == ' ') c += 7;
                else goto bad;
            }

            // path -> template
            if (*c != '/') goto bad;
            size_t o = 0;
            do {
                const char* s = c + 1;
                const char* q = s;
                while (CLS.t[(unsigned char)*q] == 1) ++q;
                bool id = (q != s) && CLS.t[(unsigned char)*q] == 0;
                if (!id) {
                    while (CLS.t[(unsigned char)*q]) ++q;
                }
                size_t seglen = (size_t)(q - s);
                if (o + seglen + 32 > tcap) {
                    growT(o + seglen + 32);
                    tb = g_tb;
                    tcap = g_tcap;
                }
                tb[o++] = '/';
                if (id) {
                    memcpy(tb + o, "{id}", 4);
                    o += 4;
                } else {
                    for (size_t k = 0; k < seglen; k += 8) {
                        uint64_t w;
                        memcpy(&w, s + k, 8);
                        memcpy(tb + o + k, &w, 8);
                    }
                    o += seglen;
                }
                c = q;
            } while (*c == '/');

            // query
            if (*c == '?') {
                ++c;
                while (*c != ' ' && *c != '\n') ++c;
            }
            if (*c != ' ') goto bad;
            ++c;

            // status
            if (!(isdig(c[0]) && isdig(c[1]) && isdig(c[2]) && c[3] == ' ')) goto bad;
            unsigned sc = (unsigned)(c[0] - '0');
            c += 4;

            // size
            if (!isdig(*c)) goto bad;
            do { ++c; } while (isdig(*c));
            if (c[0] != 'B' || c[1] != ' ') goto bad;
            c += 2;

            // latency
            if (!isdig(*c)) goto bad;
            uint64_t v = 0;
            do {
                v = v * 10 + (uint64_t)(*c - '0');
                ++c;
            } while (isdig(*c));
            if (c[0] != '.' || !isdig(c[1]) || c[2] != 'm' || c[3] != 's' || c[4] != ' ' ||
                c[5] != '"')
                goto bad;
            v = v * 10 + (uint64_t)(c[1] - '0');
            c += 6;

            // user agent: find first '"' or '\n'
            for (;;) {
                __m128i x = _mm_loadu_si128((const __m128i*)c);
                unsigned mask = (unsigned)_mm_movemask_epi8(
                    _mm_or_si128(_mm_cmpeq_epi8(x, qv), _mm_cmpeq_epi8(x, nv)));
                if (mask) {
                    c += std::countr_zero(mask);
                    break;
                }
                c += 16;
            }
            if (c[0] != '"' || c[1] != '\n') goto bad;

            // commit
            ++g_status[sc];
            {
                uint64_t z = 0;
                memcpy(tb + o, &z, 8);
                uint64_t h = (uint64_t)o * 0x9E3779B97F4A7C15ULL;
                for (size_t k = 0; k < o; k += 8) {
                    uint64_t w;
                    memcpy(&w, tb + k, 8);
                    h = (h ^ w) * 0xD6E8FEB86659FD93ULL;
                    h ^= h >> 32;
                }
                Entry& e = lookup(tb, o, h);
                if (v <= 0xFFFFFFFFULL) {
                    if (e.size == e.cap) growData(e);
                    e.data[e.size++] = (uint32_t)v;
                } else {
                    e.big.push_back(v);
                }
            }
            p = c + 2;
            continue;
        }
    bad:
        ++malformed;
        p = (const char*)memchr(c, '\n', (size_t)(end - c)) + 1;
    }
    g_lines += lines;
    g_malformed += malformed;
}

void appendTenths(std::string& s, uint64_t v) {
    s += std::to_string(v / 10);
    s += '.';
    s += (char)('0' + (int)(v % 10));
}

} // namespace

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    FILE* f = fopen(argv[1], "rb");
    if (!f) return 1;

    g_slots.assign(1024, Slot{0, 0});
    g_mask = 1023;
    g_entries.reserve(256);
    growT(4096);

    const size_t CAP = (size_t)1 << 20;
    const size_t PAD = 64;
    size_t slack = (size_t)1 << 16;
    char* base = (char*)malloc(slack + CAP + PAD);
    if (!base) return 1;
    size_t have = 0;

    for (;;) {
        char* rd = base + slack;
        size_t n = fread(rd, 1, CAP, f);
        if (n == 0) break;
        char* dataEnd = rd + n;
        memset(dataEnd, 0, PAD);
        char* last = dataEnd;
        while (last > rd && last[-1] != '\n') --last;
        char* start = rd - have;
        char* lp;
        if (last == rd) {
            have += n;
            lp = start;
        } else {
            process(start, last);
            have = (size_t)(dataEnd - last);
            lp = last;
        }
        if (n < CAP) break;
        if (have > slack) {
            size_t newSlack = std::max(have * 2, slack * 2);
            char* nb = (char*)malloc(newSlack + CAP + PAD);
            if (!nb) return 1;
            memcpy(nb + newSlack - have, lp, have);
            free(base);
            base = nb;
            slack = newSlack;
        } else if (have) {
            memmove(base + slack - have, lp, have);
        }
    }
    fclose(f);

    std::string out;
    out.reserve(4096);
    out += "lines ";
    out += std::to_string(g_lines);
    out += "\nmalformed ";
    out += std::to_string(g_malformed);
    out += '\n';
    for (int i = 0; i < 10; i++) {
        if (g_status[i]) {
            out += "status ";
            out += (char)('0' + i);
            out += "xx ";
            out += std::to_string(g_status[i]);
            out += '\n';
        }
    }

    size_t nE = g_entries.size();
    std::vector<uint32_t> idx(nE);
    for (size_t i = 0; i < nE; i++) idx[i] = (uint32_t)i;
    auto cmp = [](uint32_t a, uint32_t b) {
        const Entry& x = g_entries[a];
        const Entry& y = g_entries[b];
        size_t cx = x.size + x.big.size(), cy = y.size + y.big.size();
        if (cx != cy) return cx > cy;
        return std::string_view(x.key, x.keyLen) < std::string_view(y.key, y.keyLen);
    };
    size_t top = std::min<size_t>(10, nE);
    std::partial_sort(idx.begin(), idx.begin() + top, idx.end(), cmp);

    std::vector<uint32_t> hist;
    for (size_t t = 0; t < top; t++) {
        Entry& e = g_entries[idx[t]];
        uint32_t* d = e.data;
        size_t ns = e.size, nb = e.big.size(), n = ns + nb;
        size_t k50 = (size_t)(((uint64_t)n * 50 + 99) / 100);
        size_t k95 = (size_t)(((uint64_t)n * 95 + 99) / 100);
        uint64_t mx = 0, p50 = 0, p95 = 0;
        if (nb) mx = *std::max_element(e.big.begin(), e.big.end());
        else mx = *std::max_element(d, d + ns);

        if (nb == 0 && mx < (1u << 22) && mx <= (uint64_t)ns * 4) {
            hist.assign((size_t)mx + 1, 0);
            uint32_t* hp = hist.data();
            for (size_t i = 0; i < ns; i++) hp[d[i]]++;
            uint64_t cum = 0;
            size_t v = 0;
            for (;; v++) {
                cum += hp[v];
                if (cum >= k50) break;
            }
            p50 = v;
            while (cum < k95) {
                v++;
                cum += hp[v];
            }
            p95 = v;
        } else {
            size_t hiSmall = ns;
            if (k95 <= ns) {
                std::nth_element(d, d + (k95 - 1), d + ns);
                p95 = d[k95 - 1];
                hiSmall = k95 - 1;
            } else {
                std::nth_element(e.big.begin(), e.big.begin() + (k95 - ns - 1), e.big.end());
                p95 = e.big[k95 - ns - 1];
            }
            if (k50 == k95) {
                p50 = p95;
            } else if (k50 <= ns) {
                std::nth_element(d, d + (k50 - 1), d + hiSmall);
                p50 = d[k50 - 1];
            } else {
                std::nth_element(e.big.begin(), e.big.begin() + (k50 - ns - 1),
                                 e.big.begin() + (k95 - ns - 1));
                p50 = e.big[k50 - ns - 1];
            }
        }

        out += "path ";
        out.append(e.key, e.keyLen);
        out += ' ';
        out += std::to_string(n);
        out += ' ';
        appendTenths(out, p50);
        out += ' ';
        appendTenths(out, p95);
        out += ' ';
        appendTenths(out, mx);
        out += '\n';
    }

    fwrite(out.data(), 1, out.size(), stdout);
    fflush(stdout);
    return 0;
}
