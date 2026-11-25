#include <cstdio>
#include <cstdint>
#include <cstring>
#include <cstdlib>
#include <vector>
#include <algorithm>
#include <string>
#include <io.h>
#include <fcntl.h>

static uint8_t* B;
static size_t LEN, P;

// ---------------------------------------------------------------------------
// Open addressing hash map whose keys are spans of the input buffer.
// Keys are decoded in place before insertion, so the bytes never move.
// ---------------------------------------------------------------------------
struct SpanMap {
    std::vector<int64_t> off;
    std::vector<int32_t> klen;
    std::vector<int64_t> v1, v2;
    size_t cap = 0, cnt = 0;

    void init(size_t c) {
        cap = c; cnt = 0;
        off.assign(cap, 0);
        klen.assign(cap, -1);
        v1.assign(cap, 0);
        v2.assign(cap, 0);
    }

    static inline uint64_t hashBytes(const uint8_t* p, size_t n) {
        uint64_t h = 1469598103934665603ULL;
        for (size_t i = 0; i < n; ++i) {
            h ^= (uint64_t)p[i];
            h *= 1099511628211ULL;
        }
        return h;
    }

    void grow() {
        size_t nc = cap ? cap * 2 : 1024;
        std::vector<int64_t> no(nc, 0);
        std::vector<int32_t> nl(nc, -1);
        std::vector<int64_t> n1(nc, 0), n2(nc, 0);
        for (size_t j = 0; j < cap; ++j) {
            if (klen[j] < 0) continue;
            const uint8_t* p = B + off[j];
            size_t n = (size_t)klen[j];
            size_t i = hashBytes(p, n) & (nc - 1);
            while (nl[i] >= 0) i = (i + 1) & (nc - 1);
            no[i] = off[j];
            nl[i] = klen[j];
            n1[i] = v1[j];
            n2[i] = v2[j];
        }
        off.swap(no); klen.swap(nl); v1.swap(n1); v2.swap(n2);
        cap = nc;
    }

    size_t find(const uint8_t* p, size_t n) const {
        size_t mask = cap - 1;
        size_t i = hashBytes(p, n) & mask;
        while (klen[i] >= 0) {
            if ((size_t)klen[i] == n && std::memcmp(B + off[i], p, n) == 0) return i;
            i = (i + 1) & mask;
        }
        return (size_t)-1;
    }

    size_t getOrInsert(const uint8_t* p, size_t n) {
        if ((cnt + 1) * 10 > cap * 7) grow();
        size_t mask = cap - 1;
        size_t i = hashBytes(p, n) & mask;
        while (klen[i] >= 0) {
            if ((size_t)klen[i] == n && std::memcmp(B + off[i], p, n) == 0) return i;
            i = (i + 1) & mask;
        }
        off[i] = (int64_t)(p - B);
        klen[i] = (int32_t)n;
        v1[i] = 0;
        v2[i] = 0;
        ++cnt;
        return i;
    }
};

static SpanMap rates, channels, accounts;

// ---------------------------------------------------------------------------
// Byte level JSON scanning
// ---------------------------------------------------------------------------
static inline void skipWs() {
    while (P < LEN) {
        uint8_t c = B[P];
        if (c == ' ' || c == '\t' || c == '\n' || c == '\r') ++P;
        else break;
    }
}

// Caller guarantees B[P] == '"'. pos is left just past the closing quote.
static inline void parseString(size_t& s, size_t& e, bool& esc) {
    ++P;
    s = P;
    esc = false;
    for (;;) {
        uint8_t c = B[P];
        if (c == '"') { e = P; ++P; return; }
        if (c == '\\') { esc = true; P += 2; }
        else ++P;
    }
}

static inline unsigned hex4(const uint8_t* p) {
    unsigned v = 0;
    for (int i = 0; i < 4; ++i) {
        unsigned c = p[i];
        unsigned d;
        if (c >= '0' && c <= '9') d = c - '0';
        else if (c >= 'a' && c <= 'f') d = c - 'a' + 10;
        else d = c - 'A' + 10;
        v = (v << 4) | d;
    }
    return v;
}

// Decode JSON escapes in place within [s,e). Returns the new end.
static size_t decode(size_t s, size_t e) {
    size_t w = s, r = s;
    while (r < e) {
        uint8_t c = B[r++];
        if (c != '\\') { B[w++] = c; continue; }
        uint8_t x = B[r++];
        switch (x) {
        case '"':  B[w++] = '"';  break;
        case '\\': B[w++] = '\\'; break;
        case '/':  B[w++] = '/';  break;
        case 'b':  B[w++] = 8;    break;
        case 'f':  B[w++] = 12;   break;
        case 'n':  B[w++] = '\n'; break;
        case 'r':  B[w++] = '\r'; break;
        case 't':  B[w++] = '\t'; break;
        case 'u': {
            unsigned cp = hex4(B + r);
            r += 4;
            if (cp >= 0xD800 && cp <= 0xDBFF && r + 6 <= e &&
                B[r] == '\\' && B[r + 1] == 'u') {
                unsigned lo = hex4(B + r + 2);
                if (lo >= 0xDC00 && lo <= 0xDFFF) {
                    cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
                    r += 6;
                }
            }
            if (cp < 0x80) {
                B[w++] = (uint8_t)cp;
            } else if (cp < 0x800) {
                B[w++] = (uint8_t)(0xC0 | (cp >> 6));
                B[w++] = (uint8_t)(0x80 | (cp & 0x3F));
            } else if (cp < 0x10000) {
                B[w++] = (uint8_t)(0xE0 | (cp >> 12));
                B[w++] = (uint8_t)(0x80 | ((cp >> 6) & 0x3F));
                B[w++] = (uint8_t)(0x80 | (cp & 0x3F));
            } else {
                B[w++] = (uint8_t)(0xF0 | (cp >> 18));
                B[w++] = (uint8_t)(0x80 | ((cp >> 12) & 0x3F));
                B[w++] = (uint8_t)(0x80 | ((cp >> 6) & 0x3F));
                B[w++] = (uint8_t)(0x80 | (cp & 0x3F));
            }
            break;
        }
        default:
            B[w++] = x;
            break;
        }
    }
    return w;
}

static inline void parseStringValue(size_t& s, size_t& e) {
    bool esc;
    parseString(s, e, esc);
    if (esc) e = decode(s, e);
}

static inline bool spanEq(size_t s, size_t e, const char* lit, size_t n) {
    return (e - s) == n && std::memcmp(B + s, lit, n) == 0;
}

// Skip an arbitrary JSON value (strings, nested objects/arrays, literals).
static void skipValue() {
    skipWs();
    uint8_t c = B[P];
    if (c == '"') {
        size_t s, e; bool esc;
        parseString(s, e, esc);
        return;
    }
    if (c == '{' || c == '[') {
        int depth = 0;
        for (;;) {
            c = B[P];
            if (c == '"') {
                size_t s, e; bool esc;
                parseString(s, e, esc);
            } else {
                ++P;
                if (c == '{' || c == '[') ++depth;
                else if (c == '}' || c == ']') {
                    if (--depth == 0) return;
                }
            }
        }
    }
    // number / true / false / null
    while (P < LEN) {
        c = B[P];
        if (c == ',' || c == '}' || c == ']' || c == ' ' || c == '\t' ||
            c == '\n' || c == '\r') return;
        ++P;
    }
}

static inline long long parseAmount(size_t s, size_t e) {
    long long ip = 0;
    size_t i = s;
    while (i < e && B[i] != '.') {
        ip = ip * 10 + (B[i] - '0');
        ++i;
    }
    long long frac = 0;
    if (i < e) {
        ++i; // '.'
        int digits = 0;
        while (i < e) {
            frac = frac * 10 + (B[i] - '0');
            ++i;
            ++digits;
        }
        if (digits == 1) frac *= 10;
    }
    return ip * 100 + frac;
}

// 0 = credit (+), 1 = debit (-), 2 = refund (+), 3 = void, -1 = unknown
static inline int typeKind(size_t s, size_t e) {
    size_t n = e - s;
    if (n == 6) {
        if (std::memcmp(B + s, "credit", 6) == 0) return 0;
        if (std::memcmp(B + s, "refund", 6) == 0) return 2;
    } else if (n == 5) {
        if (std::memcmp(B + s, "debit", 5) == 0) return 1;
    } else if (n == 4) {
        if (std::memcmp(B + s, "void", 4) == 0) return 3;
    }
    return -1;
}

static bool parseTags() {
    // Caller guarantees B[P] == '['
    ++P;
    bool hasTest = false;
    for (;;) {
        skipWs();
        if (B[P] == ']') { ++P; return hasTest; }
        size_t s, e;
        parseStringValue(s, e);
        if (e - s == 4 && std::memcmp(B + s, "test", 4) == 0) hasTest = true;
        skipWs();
        if (B[P] == ',') { ++P; continue; }
        if (B[P] == ']') { ++P; return hasTest; }
    }
}

static void parseMeta(size_t& chS, size_t& chE, bool& chSet) {
    // Caller guarantees B[P] == '{'
    ++P;
    for (;;) {
        skipWs();
        if (B[P] == '}') { ++P; return; }
        size_t ks, ke; bool esc;
        parseString(ks, ke, esc);
        if (esc) ke = decode(ks, ke);
        skipWs();
        ++P; // ':'
        skipWs();
        if (spanEq(ks, ke, "channel", 7)) {
            parseStringValue(chS, chE);
            chSet = true;
        } else {
            skipValue();
        }
        skipWs();
        if (B[P] == ',') { ++P; continue; }
        if (B[P] == '}') { ++P; return; }
    }
}

static void parseRatesObject() {
    // Caller guarantees B[P] == '{'
    ++P;
    for (;;) {
        skipWs();
        if (B[P] == '}') { ++P; return; }
        size_t ks, ke; bool esc;
        parseString(ks, ke, esc);
        if (esc) ke = decode(ks, ke);
        skipWs();
        ++P; // ':'
        skipWs();
        long long v = 0;
        bool neg = false;
        if (B[P] == '-') { neg = true; ++P; }
        while (P < LEN) {
            uint8_t c = B[P];
            if (c < '0' || c > '9') break;
            v = v * 10 + (c - '0');
            ++P;
        }
        if (neg) v = -v;
        size_t idx = rates.getOrInsert(B + ks, ke - ks);
        rates.v1[idx] = v;
        skipWs();
        if (B[P] == ',') { ++P; continue; }
        if (B[P] == '}') { ++P; return; }
    }
}

static long long totalNet = 0;
static long long totalCount = 0;

static void parseTransaction() {
    // Caller guarantees B[P] == '{'
    ++P;

    size_t accS = 0, accE = 0;
    size_t chS = 0, chE = 0;
    bool chSet = false;
    long long hundredths = 0;
    long long rate = 0;
    int type = -1;
    bool hasTest = false;

    for (;;) {
        skipWs();
        if (B[P] == '}') { ++P; break; }
        size_t ks, ke; bool esc;
        parseString(ks, ke, esc);
        if (esc) ke = decode(ks, ke);
        skipWs();
        ++P; // ':'
        skipWs();

        if (spanEq(ks, ke, "account", 7)) {
            parseStringValue(accS, accE);
        } else if (spanEq(ks, ke, "type", 4)) {
            size_t s, e;
            parseStringValue(s, e);
            type = typeKind(s, e);
        } else if (spanEq(ks, ke, "amount", 6)) {
            size_t s, e;
            parseStringValue(s, e);
            hundredths = parseAmount(s, e);
        } else if (spanEq(ks, ke, "currency", 8)) {
            size_t s, e;
            parseStringValue(s, e);
            size_t ri = rates.find(B + s, e - s);
            rate = (ri == (size_t)-1) ? 0 : rates.v1[ri];
        } else if (spanEq(ks, ke, "tags", 4)) {
            hasTest = parseTags();
        } else if (spanEq(ks, ke, "meta", 4)) {
            parseMeta(chS, chE, chSet);
        } else {
            skipValue();
        }

        skipWs();
        if (B[P] == ',') { ++P; continue; }
        if (B[P] == '}') { ++P; break; }
    }

    // Rules 1-4
    if (type == 3 || type == -1 || hasTest) return;

    long long usd = (hundredths * rate) / 1000000LL;
    long long signedVal = (type == 1) ? -usd : usd;
    totalNet += signedVal;
    ++totalCount;

    size_t ci = channels.getOrInsert(B + chS, chE - chS);
    channels.v1[ci] += 1;
    channels.v2[ci] += signedVal;

    size_t ai = accounts.getOrInsert(B + accS, accE - accS);
    accounts.v1[ai] += signedVal;
}

static inline bool spanLess(int64_t o1, int32_t l1, int64_t o2, int32_t l2) {
    int n = l1 < l2 ? l1 : l2;
    int c = std::memcmp(B + o1, B + o2, (size_t)n);
    if (c != 0) return c < 0;
    return l1 < l2;
}

int main(int argc, char** argv) {
    if (argc < 2) return 1;

    _setmode(_fileno(stdout), _O_BINARY);

    FILE* f = std::fopen(argv[1], "rb");
    if (!f) return 1;
    std::fseek(f, 0, SEEK_END);
    long sz = std::ftell(f);
    std::fseek(f, 0, SEEK_SET);
    B = (uint8_t*)std::malloc((size_t)sz + 1);
    if (!B) return 1;
    LEN = std::fread(B, 1, (size_t)sz, f);
    std::fclose(f);

    rates.init(64);
    channels.init(64);
    accounts.init(1 << 14);

    P = 0;

    // First top level object: { "rates": {...}, ... }
    skipWs();
    ++P; // '{'
    for (;;) {
        skipWs();
        if (B[P] == '}') { ++P; break; }
        size_t ks, ke; bool esc;
        parseString(ks, ke, esc);
        if (esc) ke = decode(ks, ke);
        skipWs();
        ++P; // ':'
        skipWs();
        if (spanEq(ks, ke, "rates", 5)) parseRatesObject();
        else skipValue();
        skipWs();
        if (B[P] == ',') { ++P; continue; }
        if (B[P] == '}') { ++P; break; }
    }

    for (;;) {
        skipWs();
        if (P >= LEN) break;
        parseTransaction();
    }

    // Channels, sorted by name (byte order)
    std::vector<size_t> chIdx;
    chIdx.reserve(channels.cnt);
    for (size_t i = 0; i < channels.cap; ++i)
        if (channels.klen[i] >= 0) chIdx.push_back(i);
    std::sort(chIdx.begin(), chIdx.end(), [](size_t a, size_t b) {
        return spanLess(channels.off[a], channels.klen[a],
                        channels.off[b], channels.klen[b]);
    });

    // Accounts: top 10 by net desc, then id asc
    std::vector<size_t> accIdx;
    accIdx.reserve(accounts.cnt);
    for (size_t i = 0; i < accounts.cap; ++i)
        if (accounts.klen[i] >= 0) accIdx.push_back(i);
    size_t k = accIdx.size() < 10 ? accIdx.size() : 10;
    if (k) {
        std::partial_sort(accIdx.begin(), accIdx.begin() + k, accIdx.end(),
            [](size_t a, size_t b) {
                if (accounts.v1[a] != accounts.v1[b])
                    return accounts.v1[a] > accounts.v1[b];
                return spanLess(accounts.off[a], accounts.klen[a],
                                accounts.off[b], accounts.klen[b]);
            });
    }

    std::string out;
    out.reserve(8192);
    char tmp[32];
    auto appendInt = [&](long long v) {
        int n = std::snprintf(tmp, sizeof(tmp), "%lld", v);
        out.append(tmp, (size_t)n);
    };

    out += "counted ";
    appendInt(totalCount);
    out += "\nnet ";
    appendInt(totalNet);
    out += '\n';

    for (size_t idx : chIdx) {
        out += "channel ";
        out.append((const char*)(B + channels.off[idx]), (size_t)channels.klen[idx]);
        out += ' ';
        appendInt(channels.v1[idx]);
        out += ' ';
        appendInt(channels.v2[idx]);
        out += '\n';
    }

    for (size_t j = 0; j < k; ++j) {
        size_t idx = accIdx[j];
        out += "account ";
        out.append((const char*)(B + accounts.off[idx]), (size_t)accounts.klen[idx]);
        out += ' ';
        appendInt(accounts.v1[idx]);
        out += '\n';
    }

    std::fwrite(out.data(), 1, out.size(), stdout);
    std::free(B);
    return 0;
}
