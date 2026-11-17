#define _CRT_SECURE_NO_WARNINGS
#include <cstdio>
#include <cstdint>
#include <cstring>
#include <cstdlib>
#include <cmath>
#include <string>
#include <string_view>
#include <vector>
#include <algorithm>
#include <emmintrin.h>
#ifdef _MSC_VER
#include <intrin.h>
#include <io.h>
#include <fcntl.h>
#endif

namespace {

constexpr size_t PAD = 64;
constexpr uint32_t EMPTY = 0xFFFFFFFFu;

constexpr uint64_t pack(const char* s, size_t n) {
    uint64_t k = 0;
    for (size_t i = 0; i < n; ++i) k |= (uint64_t)(unsigned char)s[i] << (8 * i);
    return k;
}

constexpr uint64_t M4 = 0xFFFFFFFFull;
constexpr uint64_t M5 = 0xFFFFFFFFFFull;
constexpr uint64_t M6 = 0xFFFFFFFFFFFFull;
constexpr uint64_t M7 = 0xFFFFFFFFFFFFFFull;

constexpr uint64_t K_TYPE = pack("type", 4);
constexpr uint64_t K_TAGS = pack("tags", 4);
constexpr uint64_t K_META = pack("meta", 4);
constexpr uint64_t K_TEST = pack("test", 4);
constexpr uint64_t K_RATES = pack("rates", 5);
constexpr uint64_t K_DEBIT = pack("debit", 5);
constexpr uint64_t K_AMOUNT = pack("amount", 6);
constexpr uint64_t K_CREDIT = pack("credit", 6);
constexpr uint64_t K_REFUND = pack("refund", 6);
constexpr uint64_t K_ACCOUNT = pack("account", 7);
constexpr uint64_t K_CHANNEL = pack("channel", 7);
constexpr uint64_t K_CURRENCY = pack("currency", 8);

const char EMPTYBUF[16] = {0};

inline unsigned ctz32(unsigned m) {
#ifdef _MSC_VER
    unsigned long i;
    _BitScanForward(&i, (unsigned long)m);
    return (unsigned)i;
#else
    return (unsigned)__builtin_ctz(m);
#endif
}

inline uint64_t load8(const char* s) {
    uint64_t k;
    std::memcpy(&k, s, 8);
    return k;
}

inline uint64_t hashStr(const char* s, size_t n) {
    uint64_t h = 0x9E3779B97F4A7C15ull ^ ((uint64_t)n * 0xD6E8FEB86659FD93ull);
    while (n > 8) {
        uint64_t k = load8(s);
        h = (h ^ k) * 0x9FB21C651E98DF25ull;
        h ^= h >> 29;
        s += 8;
        n -= 8;
    }
    uint64_t k = load8(s);
    if (n < 8) k &= (1ull << (n * 8)) - 1;
    h = (h ^ k) * 0x9FB21C651E98DF25ull;
    h ^= h >> 32;
    return h;
}

struct Table {
    struct Entry {
        uint64_t hash;
        uint32_t off;
        uint32_t len;
        int64_t sum;
        int64_t count;
    };
    std::vector<Entry> e;
    std::vector<char> arena;
    size_t mask;
    size_t size = 0;

    explicit Table(size_t cap) : e(cap, Entry{0, EMPTY, 0, 0, 0}), mask(cap - 1) {}

    void grow() {
        std::vector<Entry> old;
        old.swap(e);
        e.assign(old.size() * 2, Entry{0, EMPTY, 0, 0, 0});
        mask = e.size() - 1;
        for (const Entry& x : old) {
            if (x.off != EMPTY) {
                size_t i = (size_t)x.hash & mask;
                while (e[i].off != EMPTY) i = (i + 1) & mask;
                e[i] = x;
            }
        }
    }

    inline Entry* lookup(const char* s, size_t n) {
        const uint64_t h = hashStr(s, n);
        size_t i = (size_t)h & mask;
        for (;;) {
            Entry& x = e[i];
            if (x.off == EMPTY) return nullptr;
            if (x.hash == h && x.len == n && std::memcmp(arena.data() + x.off, s, n) == 0) return &x;
            i = (i + 1) & mask;
        }
    }

    inline Entry* find(const char* s, size_t n) {
        const uint64_t h = hashStr(s, n);
        size_t i = (size_t)h & mask;
        for (;;) {
            Entry& x = e[i];
            if (x.off == EMPTY) break;
            if (x.hash == h && x.len == n && std::memcmp(arena.data() + x.off, s, n) == 0) return &x;
            i = (i + 1) & mask;
        }
        if ((size + 1) * 2 > e.size()) {
            grow();
            i = (size_t)h & mask;
            while (e[i].off != EMPTY) i = (i + 1) & mask;
        }
        Entry& x = e[i];
        x.hash = h;
        x.off = (uint32_t)arena.size();
        x.len = (uint32_t)n;
        x.sum = 0;
        x.count = 0;
        arena.insert(arena.end(), s, s + n);
        ++size;
        return &x;
    }
};

Table g_rates(64);
Table g_channels(64);
Table g_accounts(1 << 12);
int64_t g_counted = 0;
int64_t g_net = 0;

inline char* skipWs(char* p) {
    while ((unsigned char)*p <= 0x20) ++p;
    return p;
}

inline unsigned hexv(char c) {
    if (c >= '0' && c <= '9') return (unsigned)(c - '0');
    c = (char)(c | 0x20);
    if (c >= 'a' && c <= 'f') return (unsigned)(c - 'a' + 10);
    return 0;
}

inline unsigned hex4(const char* p) {
    return (hexv(p[0]) << 12) | (hexv(p[1]) << 8) | (hexv(p[2]) << 4) | hexv(p[3]);
}

// p points at the first backslash inside the string; decodes in place.
char* parseStringSlow(char* start, char* p, const char*& s, size_t& n) {
    char* out = p;
    for (;;) {
        char c = *p;
        if (c == '"') {
            ++p;
            break;
        }
        if (c == '\\') {
            char e = p[1];
            p += 2;
            switch (e) {
                case 'n': *out++ = '\n'; break;
                case 't': *out++ = '\t'; break;
                case 'r': *out++ = '\r'; break;
                case 'b': *out++ = '\b'; break;
                case 'f': *out++ = '\f'; break;
                case 'u': {
                    unsigned cp = hex4(p);
                    p += 4;
                    if (cp >= 0xD800 && cp < 0xDC00 && p[0] == '\\' && p[1] == 'u') {
                        unsigned lo = hex4(p + 2);
                        if (lo >= 0xDC00 && lo < 0xE000) {
                            cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
                            p += 6;
                        }
                    }
                    if (cp < 0x80) {
                        *out++ = (char)cp;
                    } else if (cp < 0x800) {
                        *out++ = (char)(0xC0 | (cp >> 6));
                        *out++ = (char)(0x80 | (cp & 0x3F));
                    } else if (cp < 0x10000) {
                        *out++ = (char)(0xE0 | (cp >> 12));
                        *out++ = (char)(0x80 | ((cp >> 6) & 0x3F));
                        *out++ = (char)(0x80 | (cp & 0x3F));
                    } else {
                        *out++ = (char)(0xF0 | (cp >> 18));
                        *out++ = (char)(0x80 | ((cp >> 12) & 0x3F));
                        *out++ = (char)(0x80 | ((cp >> 6) & 0x3F));
                        *out++ = (char)(0x80 | (cp & 0x3F));
                    }
                    break;
                }
                default: *out++ = e; break;
            }
        } else {
            *out++ = c;
            ++p;
        }
    }
    s = start;
    n = (size_t)(out - start);
    return p;
}

// p points just after the opening quote. Returns pointer just after the closing quote.
inline char* parseString(char* p, const char*& s, size_t& n) {
    char* start = p;
    const __m128i Q = _mm_set1_epi8('"');
    const __m128i B = _mm_set1_epi8('\\');
    for (;;) {
        __m128i v = _mm_loadu_si128((const __m128i*)p);
        int m = _mm_movemask_epi8(_mm_or_si128(_mm_cmpeq_epi8(v, Q), _mm_cmpeq_epi8(v, B)));
        if (m) {
            p += ctz32((unsigned)m);
            break;
        }
        p += 16;
    }
    if (*p == '"') {
        s = start;
        n = (size_t)(p - start);
        return p + 1;
    }
    return parseStringSlow(start, p, s, n);
}

// p points just after the opening quote.
inline char* skipString(char* p) {
    const __m128i Q = _mm_set1_epi8('"');
    const __m128i B = _mm_set1_epi8('\\');
    for (;;) {
        __m128i v = _mm_loadu_si128((const __m128i*)p);
        int m = _mm_movemask_epi8(_mm_or_si128(_mm_cmpeq_epi8(v, Q), _mm_cmpeq_epi8(v, B)));
        if (m) {
            p += ctz32((unsigned)m);
            if (*p == '"') return p + 1;
            p += 2;
        } else {
            p += 16;
        }
    }
}

// p points just after the opening '{' or '['.
inline char* skipContainer(char* p) {
    int depth = 1;
    const __m128i Q = _mm_set1_epi8('"');
    const __m128i L = _mm_set1_epi8(0x20);
    const __m128i O = _mm_set1_epi8(0x7B);
    const __m128i C = _mm_set1_epi8(0x7D);
    for (;;) {
        __m128i v = _mm_loadu_si128((const __m128i*)p);
        __m128i lv = _mm_or_si128(v, L);
        int mq = _mm_movemask_epi8(_mm_cmpeq_epi8(v, Q));
        int mo = _mm_movemask_epi8(_mm_cmpeq_epi8(lv, O));
        int mc = _mm_movemask_epi8(_mm_cmpeq_epi8(lv, C));
        int m = mq | mo | mc;
        for (;;) {
            if (!m) {
                p += 16;
                break;
            }
            unsigned i = ctz32((unsigned)m);
            int bit = 1 << i;
            if (mq & bit) {
                p = skipString(p + i + 1);
                break;
            }
            if (mo & bit) {
                ++depth;
            } else if (--depth == 0) {
                return p + i + 1;
            }
            m &= m - 1;
        }
    }
}

inline char* skipValue(char* p) {
    char c = *p;
    if (c == '"') return skipString(p + 1);
    if (c == '{' || c == '[') return skipContainer(p + 1);
    for (;;) {
        c = *p;
        if (c == ',' || c == '}' || c == ']' || (unsigned char)c <= 0x20) return p;
        ++p;
    }
}

// p points just after '['.
inline char* parseTags(char* p, bool& test) {
    test = false;
    p = skipWs(p);
    if (*p == ']') return p + 1;
    for (;;) {
        if (*p == '"') {
            const char* s;
            size_t n;
            p = parseString(p + 1, s, n);
            if (n == 4 && (load8(s) & M4) == K_TEST) test = true;
        } else {
            p = skipValue(p);
        }
        p = skipWs(p);
        if (*p == ',') {
            p = skipWs(p + 1);
            continue;
        }
        if (*p == ']') ++p;
        break;
    }
    return p;
}

// p points just after '{'.
inline char* parseMeta(char* p, const char*& chS, size_t& chN) {
    p = skipWs(p);
    if (*p == '}') return p + 1;
    for (;;) {
        if (*p != '"') break;
        const char* ks;
        size_t kn;
        p = parseString(p + 1, ks, kn);
        p = skipWs(p);
        if (*p == ':') ++p;
        p = skipWs(p);
        if (kn == 7 && *p == '"' && (load8(ks) & M7) == K_CHANNEL) {
            p = parseString(p + 1, chS, chN);
        } else {
            p = skipValue(p);
        }
        p = skipWs(p);
        if (*p == ',') {
            p = skipWs(p + 1);
            continue;
        }
        if (*p == '}') ++p;
        break;
    }
    return p;
}

int64_t parseIntTok(const char* q, const char* e) {
    if (q < e && *q == '"') {
        ++q;
        if (e > q) --e;
    }
    const char* a = q;
    bool neg = false;
    if (a < e && *a == '-') {
        neg = true;
        ++a;
    }
    int64_t v = 0;
    const char* d0 = a;
    while (a < e && (unsigned)(*a - '0') < 10u) {
        v = v * 10 + (*a - '0');
        ++a;
    }
    if (a == e && a != d0) return neg ? -v : v;
    double d = std::strtod(q, nullptr);
    return (int64_t)std::llround(d);
}

// p points at '{'.
char* parseRates(char* p) {
    ++p;
    p = skipWs(p);
    if (*p == '}') return p + 1;
    for (;;) {
        if (*p != '"') break;
        const char* ks;
        size_t kn;
        p = parseString(p + 1, ks, kn);
        p = skipWs(p);
        if (*p == ':') ++p;
        p = skipWs(p);
        if (kn == 5 && *p == '{' && (load8(ks) & M5) == K_RATES) {
            ++p;
            p = skipWs(p);
            if (*p == '}') {
                ++p;
            } else {
                for (;;) {
                    if (*p != '"') break;
                    const char* cs;
                    size_t cn;
                    p = parseString(p + 1, cs, cn);
                    p = skipWs(p);
                    if (*p == ':') ++p;
                    p = skipWs(p);
                    char* q = p;
                    p = skipValue(p);
                    int64_t r = parseIntTok(q, p);
                    g_rates.find(cs, cn)->sum = r;
                    p = skipWs(p);
                    if (*p == ',') {
                        p = skipWs(p + 1);
                        continue;
                    }
                    if (*p == '}') ++p;
                    break;
                }
            }
        } else {
            p = skipValue(p);
        }
        p = skipWs(p);
        if (*p == ',') {
            p = skipWs(p + 1);
            continue;
        }
        if (*p == '}') ++p;
        break;
    }
    return p;
}

// p points at '{'.
inline char* parseTxn(char* p) {
    ++p;
    const char* typeS = EMPTYBUF;
    const char* amtS = EMPTYBUF;
    const char* curS = EMPTYBUF;
    const char* accS = EMPTYBUF;
    const char* chS = EMPTYBUF;
    size_t typeN = 0, amtN = 0, curN = 0, accN = 0, chN = 0;
    bool test = false;

    p = skipWs(p);
    if (*p == '}') {
        ++p;
    } else {
        for (;;) {
            if (*p != '"') break;
            const char* ks;
            size_t kn;
            p = parseString(p + 1, ks, kn);
            p = skipWs(p);
            if (*p == ':') ++p;
            p = skipWs(p);
            const char c = *p;
            const uint64_t k = load8(ks);
            switch (kn) {
                case 4: {
                    const uint64_t k4 = k & M4;
                    if (c == '"' && k4 == K_TYPE) {
                        p = parseString(p + 1, typeS, typeN);
                    } else if (c == '[' && k4 == K_TAGS) {
                        p = parseTags(p + 1, test);
                    } else if (c == '{' && k4 == K_META) {
                        p = parseMeta(p + 1, chS, chN);
                    } else {
                        p = skipValue(p);
                    }
                    break;
                }
                case 6:
                    if (c == '"' && (k & M6) == K_AMOUNT) {
                        p = parseString(p + 1, amtS, amtN);
                    } else {
                        p = skipValue(p);
                    }
                    break;
                case 7:
                    if (c == '"' && (k & M7) == K_ACCOUNT) {
                        p = parseString(p + 1, accS, accN);
                    } else {
                        p = skipValue(p);
                    }
                    break;
                case 8:
                    if (c == '"' && k == K_CURRENCY) {
                        p = parseString(p + 1, curS, curN);
                    } else {
                        p = skipValue(p);
                    }
                    break;
                default:
                    p = skipValue(p);
                    break;
            }
            p = skipWs(p);
            if (*p == ',') {
                p = skipWs(p + 1);
                continue;
            }
            if (*p == '}') ++p;
            break;
        }
    }

    bool credit;
    if (typeN == 6) {
        const uint64_t t = load8(typeS) & M6;
        if (t == K_CREDIT || t == K_REFUND) credit = true;
        else return p;
    } else if (typeN == 5 && (load8(typeS) & M5) == K_DEBIT) {
        credit = false;
    } else {
        return p;
    }
    if (test) return p;

    uint64_t h = 0;
    const char* a = amtS;
    const char* ae = a + amtN;
    while (a < ae && (unsigned)(*a - '0') < 10u) {
        h = h * 10 + (uint64_t)(*a - '0');
        ++a;
    }
    h *= 100;
    if (a < ae && *a == '.') {
        ++a;
        if (a < ae && (unsigned)(*a - '0') < 10u) {
            h += (uint64_t)(*a - '0') * 10;
            ++a;
            if (a < ae && (unsigned)(*a - '0') < 10u) {
                h += (uint64_t)(*a - '0');
            }
        }
    }

    const Table::Entry* r = g_rates.lookup(curS, curN);
    const int64_t rate = r ? r->sum : 0;
    const int64_t prod = (int64_t)h * rate;
    int64_t usd = prod / 1000000;
    if (prod % 1000000 < 0) --usd;
    const int64_t v = credit ? usd : -usd;

    ++g_counted;
    g_net += v;
    Table::Entry* ch = g_channels.find(chS, chN);
    ch->count += 1;
    ch->sum += v;
    Table::Entry* ac = g_accounts.find(accS, accN);
    ac->sum += v;
    return p;
}

bool g_first = true;

void processChunk(char* p, char* e) {
    for (;;) {
        while (p < e && (unsigned char)*p <= 0x20) ++p;
        if (p >= e) break;
        if (*p != '{') {
            char* nl = (char*)std::memchr(p, '\n', (size_t)(e - p));
            if (!nl) break;
            p = nl + 1;
            continue;
        }
        if (g_first) {
            g_first = false;
            p = parseRates(p);
        } else {
            p = parseTxn(p);
        }
    }
}

} // namespace

int main(int argc, char** argv) {
    if (argc < 2) return 1;

#ifdef _MSC_VER
    int fd = _open(argv[1], _O_RDONLY | _O_BINARY | _O_SEQUENTIAL);
    if (fd < 0) return 1;
    auto readSome = [&](char* dst, size_t n) -> size_t {
        if (n > ((size_t)1 << 30)) n = (size_t)1 << 30;
        int r = _read(fd, dst, (unsigned)n);
        return r > 0 ? (size_t)r : 0;
    };
#else
    FILE* f = std::fopen(argv[1], "rb");
    if (!f) return 1;
    auto readSome = [&](char* dst, size_t n) -> size_t { return std::fread(dst, 1, n, f); };
#endif

    size_t cap = (size_t)1 << 20;
    std::vector<char> buf(cap + PAD);
    size_t have = 0;

    for (;;) {
        if (have == cap) {
            cap *= 2;
            buf.resize(cap + PAD);
        }
        size_t got = readSome(buf.data() + have, cap - have);
        const bool eof = (got == 0);
        if (eof) {
            if (have == 0) break;
            buf[have++] = '\n';
        } else {
            have += got;
        }
        char* base = buf.data();
        size_t end = have;
        while (end > 0 && base[end - 1] != '\n') --end;
        if (end > 0) {
            processChunk(base, base + end);
            size_t rem = have - end;
            if (rem) std::memmove(base, base + end, rem);
            have = rem;
        }
        if (eof) break;
    }

#ifdef _MSC_VER
    _close(fd);
#else
    std::fclose(f);
#endif

    std::string out;
    out.reserve(4096);
    out += "counted ";
    out += std::to_string((long long)g_counted);
    out += '\n';
    out += "net ";
    out += std::to_string((long long)g_net);
    out += '\n';

    struct Item {
        std::string_view name;
        int64_t count;
        int64_t sum;
    };

    {
        std::vector<Item> ch;
        ch.reserve(g_channels.size);
        for (const Table::Entry& x : g_channels.e) {
            if (x.off != EMPTY) {
                ch.push_back(Item{std::string_view(g_channels.arena.data() + x.off, x.len), x.count, x.sum});
            }
        }
        std::sort(ch.begin(), ch.end(), [](const Item& a, const Item& b) { return a.name < b.name; });
        for (const Item& c : ch) {
            out += "channel ";
            out.append(c.name.data(), c.name.size());
            out += ' ';
            out += std::to_string((long long)c.count);
            out += ' ';
            out += std::to_string((long long)c.sum);
            out += '\n';
        }
    }

    {
        std::vector<Item> ac;
        ac.reserve(g_accounts.size);
        for (const Table::Entry& x : g_accounts.e) {
            if (x.off != EMPTY) {
                ac.push_back(Item{std::string_view(g_accounts.arena.data() + x.off, x.len), x.count, x.sum});
            }
        }
        size_t k = ac.size() < 10 ? ac.size() : 10;
        auto cmp = [](const Item& a, const Item& b) {
            if (a.sum != b.sum) return a.sum > b.sum;
            return a.name < b.name;
        };
        std::partial_sort(ac.begin(), ac.begin() + k, ac.end(), cmp);
        for (size_t i = 0; i < k; ++i) {
            out += "account ";
            out.append(ac[i].name.data(), ac[i].name.size());
            out += ' ';
            out += std::to_string((long long)ac[i].sum);
            out += '\n';
        }
    }

    std::fwrite(out.data(), 1, out.size(), stdout);
    std::fflush(stdout);
    return 0;
}
