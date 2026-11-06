// Ledger: streaming JSON Lines scanner with exact integer currency conversion.
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fcntl.h>
#include <io.h>
#include <emmintrin.h>
#include <intrin.h>
#include <string>
#include <string_view>
#include <vector>

namespace {

inline uint32_t lowBit(uint32_t m) {
    unsigned long i;
    _BitScanForward(&i, m);
    return i;
}

inline bool isWs(unsigned char c) { return c == ' ' || c == '\n' || c == '\r' || c == '\t'; }

inline const char* skipWs(const char* p) {
    while (isWs((unsigned char)*p)) ++p;
    return p;
}

inline uint32_t hexVal(char c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    return c - 'A' + 10;
}

inline uint32_t hex4(const char* p) {
    return (hexVal(p[0]) << 12) | (hexVal(p[1]) << 8) | (hexVal(p[2]) << 4) | hexVal(p[3]);
}

void appendUtf8(std::string& out, uint32_t cp) {
    if (cp < 0x80) {
        out.push_back((char)cp);
    } else if (cp < 0x800) {
        out.push_back((char)(0xC0 | (cp >> 6)));
        out.push_back((char)(0x80 | (cp & 0x3F)));
    } else if (cp < 0x10000) {
        out.push_back((char)(0xE0 | (cp >> 12)));
        out.push_back((char)(0x80 | ((cp >> 6) & 0x3F)));
        out.push_back((char)(0x80 | (cp & 0x3F)));
    } else {
        out.push_back((char)(0xF0 | (cp >> 18)));
        out.push_back((char)(0x80 | ((cp >> 12) & 0x3F)));
        out.push_back((char)(0x80 | ((cp >> 6) & 0x3F)));
        out.push_back((char)(0x80 | (cp & 0x3F)));
    }
}

// Slow path: decode a string containing escapes. `b` is the start of the content,
// `p` the first backslash. Returns the pointer past the closing quote.
__declspec(noinline) const char* decodeStr(const char* b, const char* p, std::string_view& out,
                                           std::string& scratch) {
    scratch.assign(b, p);
    for (;;) {
        char c = *p;
        if (c == '"') break;
        if (c != '\\') {
            scratch.push_back(c);
            ++p;
            continue;
        }
        char e = p[1];
        p += 2;
        switch (e) {
            case 'n': scratch.push_back('\n'); break;
            case 't': scratch.push_back('\t'); break;
            case 'r': scratch.push_back('\r'); break;
            case 'b': scratch.push_back('\b'); break;
            case 'f': scratch.push_back('\f'); break;
            case 'u': {
                uint32_t cp = hex4(p);
                p += 4;
                if (cp >= 0xD800 && cp < 0xDC00 && p[0] == '\\' && p[1] == 'u') {
                    uint32_t lo = hex4(p + 2);
                    if (lo >= 0xDC00 && lo < 0xE000) {
                        cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
                        p += 6;
                    }
                }
                appendUtf8(scratch, cp);
                break;
            }
            default: scratch.push_back(e); break;  // \" \\ \/
        }
    }
    out = std::string_view(scratch);
    return p + 1;
}

// First quote or backslash at or after p (16-byte SSE2 blocks; the buffer has slack).
inline const char* findQuoteOrEscape(const char* p) {
    const __m128i vq = _mm_set1_epi8('"');
    const __m128i vb = _mm_set1_epi8('\\');
    for (;;) {
        __m128i x = _mm_loadu_si128((const __m128i*)p);
        uint32_t m = (uint32_t)_mm_movemask_epi8(_mm_or_si128(_mm_cmpeq_epi8(x, vq), _mm_cmpeq_epi8(x, vb)));
        if (m) return p + lowBit(m);
        p += 16;
    }
}

// p points at the opening quote. Result view points into the input when there are no escapes.
inline const char* parseStr(const char* p, std::string_view& out, std::string& scratch) {
    const char* b = ++p;
    p = findQuoteOrEscape(p);
    if (*p == '"') {
        out = std::string_view(b, p - b);
        return p + 1;
    }
    return decodeStr(b, p, out, scratch);
}

// p points just past the opening quote; returns the pointer past the closing quote.
inline const char* skipStrBody(const char* p) {
    for (;;) {
        p = findQuoteOrEscape(p);
        if (*p == '"') return p + 1;
        p += 2;
    }
}

// Skips a nested object or array starting at p ('{' or '[').
const char* skipContainer(const char* p) {
    const __m128i vq = _mm_set1_epi8('"');
    const __m128i vmask = _mm_set1_epi8((char)0xD9);  // {, }, [, ] all map to 0x59 (also Y, _, y, DEL)
    const __m128i vbr = _mm_set1_epi8(0x59);
    int depth = 1;
    ++p;
    for (;;) {
        uint32_t m;
        for (;;) {
            __m128i x = _mm_loadu_si128((const __m128i*)p);
            m = (uint32_t)_mm_movemask_epi8(
                _mm_or_si128(_mm_cmpeq_epi8(x, vq), _mm_cmpeq_epi8(_mm_and_si128(x, vmask), vbr)));
            if (m) break;
            p += 16;
        }
        p += lowBit(m);
        char c = *p++;
        if (c == '"') {
            p = skipStrBody(p);
        } else if (c == '{' || c == '[') {
            ++depth;
        } else if (c == '}' || c == ']') {
            if (--depth == 0) return p;
        }
    }
}

const char* skipVal(const char* p) {
    char c = *p;
    if (c == '"') return skipStrBody(p + 1);
    if (c == '{' || c == '[') return skipContainer(p);
    while (!(c == ',' || c == '}' || c == ']' || isWs((unsigned char)c))) c = *++p;
    return p;
}

inline bool eq(std::string_view s, const char* lit, size_t n) {
    return s.size() == n && std::memcmp(s.data(), lit, n) == 0;
}

inline uint64_t hashBytes(const char* s, size_t n) {
    uint64_t h = 0x9E3779B97F4A7C15ull ^ (n * 0xff51afd7ed558ccdull);
    while (n >= 8) {
        uint64_t w;
        std::memcpy(&w, s, 8);
        h = (h ^ w) * 0xbf58476d1ce4e5b9ull;
        h ^= h >> 31;
        s += 8;
        n -= 8;
    }
    uint64_t w = 0;
    for (size_t i = 0; i < n; ++i) w |= (uint64_t)(unsigned char)s[i] << (8 * i);
    h = (h ^ w) * 0x94d049bb133111ebull;
    h ^= h >> 29;
    return h;
}

// Open-addressing intern table mapping byte strings to dense indices.
struct Interner {
    struct Slot {
        uint32_t hash;
        uint32_t idx;  // index + 1, 0 = empty
    };
    std::vector<Slot> slots;
    std::vector<std::string> keys;
    uint32_t mask;

    Interner() : slots(1024), mask(1023) {}

    uint32_t find(std::string_view k) const {
        uint32_t h = (uint32_t)hashBytes(k.data(), k.size());
        for (uint32_t i = h & mask;; i = (i + 1) & mask) {
            const Slot& s = slots[i];
            if (s.idx == 0) return UINT32_MAX;
            if (s.hash == h && keys[s.idx - 1] == k) return s.idx - 1;
        }
    }

    uint32_t intern(std::string_view k) {
        uint32_t h = (uint32_t)hashBytes(k.data(), k.size());
        for (uint32_t i = h & mask;; i = (i + 1) & mask) {
            Slot& s = slots[i];
            if (s.idx == 0) {
                keys.emplace_back(k);
                s.hash = h;
                s.idx = (uint32_t)keys.size();
                if (keys.size() * 2 > slots.size()) grow();
                return (uint32_t)keys.size() - 1;
            }
            if (s.hash == h) {
                const std::string& e = keys[s.idx - 1];
                if (e.size() == k.size() && std::memcmp(e.data(), k.data(), k.size()) == 0) return s.idx - 1;
            }
        }
    }

    void grow() {
        std::vector<Slot> old(slots.size() * 2);
        old.swap(slots);
        mask = (uint32_t)slots.size() - 1;
        for (const Slot& s : old) {
            if (s.idx == 0) continue;
            uint32_t i = s.hash & mask;
            while (slots[i].idx != 0) i = (i + 1) & mask;
            slots[i] = s;
        }
    }
};

struct Ledger {
    Interner currencies;
    std::vector<int64_t> rates;
    Interner channels;
    std::vector<int64_t> chanCount, chanSum;
    Interner accounts;
    std::vector<int64_t> accSum;
    int64_t counted = 0, net = 0;

    std::string sKey, sAcc, sChan, sType, sAmt, sCur, sTag;

    const char* parseRates(const char* p) {
        p = skipWs(p) + 1;  // '{'
        p = skipWs(p);
        if (*p == '}') return p + 1;
        for (;;) {
            std::string_view key;
            p = parseStr(p, key, sKey);
            p = skipWs(p) + 1;  // ':'
            p = skipWs(p);
            if (eq(key, "rates", 5) && *p == '{') {
                p = skipWs(p + 1);
                if (*p != '}') {
                    for (;;) {
                        std::string_view cur;
                        p = parseStr(p, cur, sCur);
                        p = skipWs(p) + 1;
                        p = skipWs(p);
                        bool neg = false;
                        if (*p == '-') {
                            neg = true;
                            ++p;
                        }
                        int64_t v = 0;
                        while (*p >= '0' && *p <= '9') v = v * 10 + (*p++ - '0');
                        p = skipVal(p);  // any fraction/exponent (not expected)
                        uint32_t id = currencies.intern(cur);
                        if (id >= rates.size()) rates.resize(id + 1);
                        rates[id] = neg ? -v : v;
                        p = skipWs(p);
                        if (*p == ',') {
                            p = skipWs(p + 1);
                            continue;
                        }
                        break;
                    }
                }
                ++p;  // '}'
            } else {
                p = skipVal(p);
            }
            p = skipWs(p);
            if (*p == ',') {
                p = skipWs(p + 1);
                continue;
            }
            return p + 1;
        }
    }

    // Parses one transaction object starting at '{'.
    const char* parseTx(const char* p) {
        std::string_view acc, chan, cur, amt;
        int sign = 0;  // +1 credit/refund, -1 debit, 0 void/unknown
        bool test = false;

        p = skipWs(p + 1);
        if (*p == '}') return p + 1;
        for (;;) {
            std::string_view key;
            p = parseStr(p, key, sKey);
            p = skipWs(p) + 1;
            p = skipWs(p);
            bool handled = false;
            switch (key.size()) {
                case 4:
                    if (eq(key, "type", 4)) {
                        std::string_view t;
                        p = parseStr(p, t, sType);
                        if (eq(t, "credit", 6) || eq(t, "refund", 6))
                            sign = 1;
                        else if (eq(t, "debit", 5))
                            sign = -1;
                        else
                            sign = 0;
                        handled = true;
                    } else if (eq(key, "tags", 4)) {
                        p = skipWs(p + 1);
                        if (*p != ']') {
                            for (;;) {
                                if (*p == '"') {
                                    std::string_view tag;
                                    p = parseStr(p, tag, sTag);
                                    if (eq(tag, "test", 4)) test = true;
                                } else {
                                    p = skipVal(p);
                                }
                                p = skipWs(p);
                                if (*p == ',') {
                                    p = skipWs(p + 1);
                                    continue;
                                }
                                break;
                            }
                        }
                        ++p;
                        handled = true;
                    } else if (eq(key, "meta", 4)) {
                        p = skipWs(p + 1);
                        if (*p != '}') {
                            for (;;) {
                                std::string_view mk;
                                p = parseStr(p, mk, sKey);
                                p = skipWs(p) + 1;
                                p = skipWs(p);
                                if (eq(mk, "channel", 7) && *p == '"')
                                    p = parseStr(p, chan, sChan);
                                else
                                    p = skipVal(p);
                                p = skipWs(p);
                                if (*p == ',') {
                                    p = skipWs(p + 1);
                                    continue;
                                }
                                break;
                            }
                        }
                        ++p;
                        handled = true;
                    }
                    break;
                case 6:
                    if (eq(key, "amount", 6)) {
                        p = parseStr(p, amt, sAmt);
                        handled = true;
                    }
                    break;
                case 7:
                    if (eq(key, "account", 7)) {
                        p = parseStr(p, acc, sAcc);
                        handled = true;
                    }
                    break;
                case 8:
                    if (eq(key, "currency", 8)) {
                        p = parseStr(p, cur, sCur);
                        handled = true;
                    }
                    break;
            }
            if (!handled) p = skipVal(p);
            p = skipWs(p);
            if (*p == ',') {
                p = skipWs(p + 1);
                continue;
            }
            ++p;  // '}'
            break;
        }

        if (sign == 0 || test) return p;

        int64_t hund = 0;
        size_t i = 0, n = amt.size();
        const char* a = amt.data();
        while (i < n && a[i] != '.') hund = hund * 10 + (a[i++] - '0');
        hund *= 100;
        if (i < n) {
            ++i;
            if (i < n) hund += (a[i] - '0') * 10;
            if (i + 1 < n) hund += a[i + 1] - '0';
        }
        uint32_t cid = currencies.find(cur);
        int64_t rate = cid == UINT32_MAX ? 0 : rates[cid];
        int64_t usd = hund * rate / 1000000;
        int64_t v = sign > 0 ? usd : -usd;

        ++counted;
        net += v;
        uint32_t ch = channels.intern(chan);
        if (ch >= chanCount.size()) {
            chanCount.resize(ch + 1);
            chanSum.resize(ch + 1);
        }
        ++chanCount[ch];
        chanSum[ch] += v;
        uint32_t ac = accounts.intern(acc);
        if (ac >= accSum.size()) accSum.resize(ac + 1 + accSum.size());
        accSum[ac] += v;
        return p;
    }

    void process(const char* p, const char* end, bool& first) {
        for (;;) {
            p = skipWs(p);
            if (p >= end) return;
            if (first) {
                p = parseRates(p);
                first = false;
            } else {
                p = parseTx(p);
            }
        }
    }

    void print() {
        std::string out;
        char line[512];
        out += "counted " + std::to_string(counted) + "\nnet " + std::to_string(net) + "\n";
        std::vector<uint32_t> idx(channels.keys.size());
        for (uint32_t i = 0; i < idx.size(); ++i) idx[i] = i;
        std::sort(idx.begin(), idx.end(),
                  [&](uint32_t a, uint32_t b) { return channels.keys[a] < channels.keys[b]; });
        for (uint32_t i : idx) {
            out += "channel ";
            out += channels.keys[i];
            std::snprintf(line, sizeof line, " %lld %lld\n", (long long)chanCount[i], (long long)chanSum[i]);
            out += line;
        }
        std::vector<uint32_t> ac(accounts.keys.size());
        for (uint32_t i = 0; i < ac.size(); ++i) ac[i] = i;
        size_t k = std::min<size_t>(10, ac.size());
        std::partial_sort(ac.begin(), ac.begin() + k, ac.end(), [&](uint32_t a, uint32_t b) {
            if (accSum[a] != accSum[b]) return accSum[a] > accSum[b];
            return accounts.keys[a] < accounts.keys[b];
        });
        for (size_t i = 0; i < k; ++i) {
            out += "account ";
            out += accounts.keys[ac[i]];
            std::snprintf(line, sizeof line, " %lld\n", (long long)accSum[ac[i]]);
            out += line;
        }
        _setmode(_fileno(stdout), _O_BINARY);
        std::fwrite(out.data(), 1, out.size(), stdout);
    }
};

}  // namespace

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    FILE* f = std::fopen(argv[1], "rb");
    if (!f) return 1;
    std::setvbuf(f, nullptr, _IONBF, 0);

    Ledger* ledger = new Ledger();
    size_t cap = 8u << 20;
    char* buf = (char*)std::malloc(cap + 64);
    size_t len = 0;
    bool first = true;
    for (;;) {
        if (len == cap) {
            cap *= 2;
            buf = (char*)std::realloc(buf, cap + 64);
        }
        size_t got = std::fread(buf + len, 1, cap - len, f);
        bool eof = got == 0;
        len += got;
        size_t lim;
        if (eof) {
            if (len == 0) break;
            if (buf[len - 1] != '\n') buf[len++] = '\n';  // slack after cap leaves room for this, the sentinel and SIMD over-reads
            lim = len;
        } else {
            const char* nl = nullptr;
            for (size_t i = len; i > 0; --i) {
                if (buf[i - 1] == '\n') {
                    nl = buf + i;
                    break;
                }
            }
            if (!nl) continue;  // line longer than buffer: read more
            lim = nl - buf;
        }
        char saved = buf[lim];
        buf[lim] = 0;  // sentinel stops whitespace skipping
        ledger->process(buf, buf + lim, first);
        buf[lim] = saved;
        std::memmove(buf, buf + lim, len - lim);
        len -= lim;
        if (eof) break;
    }
    std::fclose(f);
    ledger->print();
    return 0;
}
