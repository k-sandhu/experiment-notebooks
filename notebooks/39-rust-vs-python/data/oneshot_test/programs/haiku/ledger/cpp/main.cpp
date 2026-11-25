#define _CRT_SECURE_NO_WARNINGS
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <deque>
#include <string>
#include <string_view>
#include <unordered_map>
#include <vector>

namespace {

using i64 = std::int64_t;
using u32 = std::uint32_t;
using sv = std::string_view;

struct Group {
    std::string name;
    i64 count = 0;
    i64 net = 0;
};

std::string keyS, rateKeyS, mKeyS, typS, curS, acctS, amtS, chanS, tagS;
std::deque<std::string> rateNames;
std::unordered_map<sv, i64> rates;
std::deque<Group> chanStore, acctStore;
std::unordered_map<sv, Group*> chanMap, acctMap;
i64 counted = 0;
i64 netTotal = 0;

inline bool isWs(char c) { return c == ' ' || c == '\t' || c == '\r' || c == '\n'; }
inline bool isDigit(char c) { return c >= '0' && c <= '9'; }

inline void skipWs(const char*& p, const char* e) {
    while (p < e && isWs(*p)) ++p;
}

void skipString(const char*& p, const char* e) {
    // p points at the opening quote
    ++p;
    while (p < e) {
        char c = *p;
        if (c == '\\') {
            p = (e - p >= 2) ? p + 2 : e;
            continue;
        }
        ++p;
        if (c == '"') return;
    }
}

void skipValue(const char*& p, const char* e) {
    skipWs(p, e);
    if (p >= e) return;
    char c = *p;
    if (c == '"') {
        skipString(p, e);
        return;
    }
    if (c == '{' || c == '[') {
        int depth = 0;
        while (p < e) {
            char d = *p;
            if (d == '"') {
                skipString(p, e);
                continue;
            }
            ++p;
            if (d == '{' || d == '[') {
                ++depth;
            } else if (d == '}' || d == ']') {
                if (--depth == 0) return;
            }
        }
        return;
    }
    while (p < e) {
        char d = *p;
        if (d == ',' || d == '}' || d == ']' || isWs(d)) break;
        ++p;
    }
}

u32 hex4(const char*& p, const char* e) {
    u32 v = 0;
    for (int i = 0; i < 4; ++i) {
        if (p >= e) break;
        char c = *p;
        u32 d;
        if (c >= '0' && c <= '9') d = static_cast<u32>(c - '0');
        else if (c >= 'a' && c <= 'f') d = static_cast<u32>(c - 'a' + 10);
        else if (c >= 'A' && c <= 'F') d = static_cast<u32>(c - 'A' + 10);
        else break;
        v = v * 16 + d;
        ++p;
    }
    return v;
}

void appendUtf8(std::string& s, u32 cp) {
    if (cp < 0x80) {
        s += static_cast<char>(cp);
    } else if (cp < 0x800) {
        s += static_cast<char>(0xC0 | (cp >> 6));
        s += static_cast<char>(0x80 | (cp & 0x3F));
    } else if (cp < 0x10000) {
        s += static_cast<char>(0xE0 | (cp >> 12));
        s += static_cast<char>(0x80 | ((cp >> 6) & 0x3F));
        s += static_cast<char>(0x80 | (cp & 0x3F));
    } else {
        s += static_cast<char>(0xF0 | (cp >> 18));
        s += static_cast<char>(0x80 | ((cp >> 12) & 0x3F));
        s += static_cast<char>(0x80 | ((cp >> 6) & 0x3F));
        s += static_cast<char>(0x80 | (cp & 0x3F));
    }
}

// p points at the opening quote. Returns the decoded content. If there are no
// escapes, the view points into the input; otherwise it points into scratch.
sv parseString(const char*& p, const char* e, std::string& scratch) {
    ++p;
    const char* s = p;
    while (p < e && *p != '"' && *p != '\\') ++p;
    if (p >= e) {
        return sv(s, static_cast<size_t>(p - s));
    }
    if (*p == '"') {
        sv v(s, static_cast<size_t>(p - s));
        ++p;
        return v;
    }
    scratch.assign(s, static_cast<size_t>(p - s));
    while (p < e && *p != '"') {
        if (*p == '\\') {
            ++p;
            if (p >= e) break;
            char c = *p++;
            switch (c) {
                case 'b': scratch += '\b'; break;
                case 'f': scratch += '\f'; break;
                case 'n': scratch += '\n'; break;
                case 'r': scratch += '\r'; break;
                case 't': scratch += '\t'; break;
                case 'u': {
                    u32 cp = hex4(p, e);
                    if (cp >= 0xD800 && cp <= 0xDBFF) {
                        bool paired = false;
                        if (e - p >= 6 && p[0] == '\\' && p[1] == 'u') {
                            const char* save = p;
                            p += 2;
                            u32 lo = hex4(p, e);
                            if (lo >= 0xDC00 && lo <= 0xDFFF) {
                                cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
                                paired = true;
                            } else {
                                p = save;
                            }
                        }
                        if (!paired) cp = 0xFFFD;
                    } else if (cp >= 0xDC00 && cp <= 0xDFFF) {
                        cp = 0xFFFD;
                    }
                    appendUtf8(scratch, cp);
                    break;
                }
                default:
                    // covers '"', '\\', '/'
                    scratch += c;
                    break;
            }
        } else {
            const char* q = p;
            while (q < e && *q != '"' && *q != '\\') ++q;
            scratch.append(p, static_cast<size_t>(q - p));
            p = q;
        }
    }
    if (p < e) ++p;
    return sv(scratch);
}

void readStr(const char*& p, const char* e, std::string& scratch, sv& out) {
    skipWs(p, e);
    if (p < e && *p == '"') {
        out = parseString(p, e, scratch);
    } else {
        out = sv();
        skipValue(p, e);
    }
}

i64 parseInt(const char*& p, const char* e) {
    bool neg = false;
    if (p < e && *p == '-') {
        neg = true;
        ++p;
    }
    i64 v = 0;
    while (p < e && isDigit(*p)) {
        v = v * 10 + (*p - '0');
        ++p;
    }
    return neg ? -v : v;
}

i64 parseHundredths(sv s) {
    size_t i = 0, n = s.size();
    i64 h = 0;
    while (i < n && isDigit(s[i])) {
        h = h * 10 + (s[i] - '0');
        ++i;
    }
    h *= 100;
    if (i < n && s[i] == '.') {
        ++i;
        i64 d1 = 0, d2 = 0;
        if (i < n && isDigit(s[i])) {
            d1 = s[i] - '0';
            ++i;
        }
        if (i < n && isDigit(s[i])) {
            d2 = s[i] - '0';
            ++i;
        }
        h += d1 * 10 + d2;
    }
    return h;
}

void parseRates(const char*& p, const char* e) {
    skipWs(p, e);
    if (p >= e || *p != '{') {
        skipValue(p, e);
        return;
    }
    ++p;
    for (;;) {
        skipWs(p, e);
        if (p >= e) return;
        char c = *p;
        if (c == '}') {
            ++p;
            return;
        }
        if (c == ',') {
            ++p;
            continue;
        }
        if (c != '"') {
            ++p;
            continue;
        }
        sv key = parseString(p, e, rateKeyS);
        skipWs(p, e);
        if (p < e && *p == ':') ++p;
        skipWs(p, e);
        if (p < e && (*p == '-' || isDigit(*p))) {
            i64 v = parseInt(p, e);
            rateNames.emplace_back(key);
            rates[sv(rateNames.back())] = v;
        } else {
            skipValue(p, e);
        }
    }
}

void parseTags(const char*& p, const char* e, bool& hasTest) {
    skipWs(p, e);
    if (p >= e || *p != '[') {
        skipValue(p, e);
        return;
    }
    ++p;
    for (;;) {
        skipWs(p, e);
        if (p >= e) return;
        char c = *p;
        if (c == ']') {
            ++p;
            return;
        }
        if (c == ',') {
            ++p;
            continue;
        }
        if (c == '"') {
            sv t = parseString(p, e, tagS);
            if (t == "test") hasTest = true;
        } else {
            const char* before = p;
            skipValue(p, e);
            if (p == before) ++p;
        }
    }
}

void parseMeta(const char*& p, const char* e, std::string& scratch, sv& chan) {
    skipWs(p, e);
    if (p >= e || *p != '{') {
        skipValue(p, e);
        return;
    }
    ++p;
    for (;;) {
        skipWs(p, e);
        if (p >= e) return;
        char c = *p;
        if (c == '}') {
            ++p;
            return;
        }
        if (c == ',') {
            ++p;
            continue;
        }
        if (c != '"') {
            ++p;
            continue;
        }
        sv key = parseString(p, e, mKeyS);
        skipWs(p, e);
        if (p < e && *p == ':') ++p;
        skipWs(p, e);
        if (key == "channel") {
            readStr(p, e, scratch, chan);
        } else {
            skipValue(p, e);
        }
    }
}

Group& getGroup(std::unordered_map<sv, Group*>& m, std::deque<Group>& store, sv k) {
    auto it = m.find(k);
    if (it != m.end()) return *it->second;
    store.emplace_back();
    Group& g = store.back();
    if (!k.empty()) g.name.assign(k.data(), k.size());
    m.emplace(sv(g.name), &g);
    return g;
}

void processLine(const char* p, const char* e) {
    skipWs(p, e);
    if (p >= e || *p != '{') return;
    ++p;

    sv typ, cur, acct, amt, chan;
    bool hasTest = false;

    for (;;) {
        skipWs(p, e);
        if (p >= e) break;
        char c = *p;
        if (c == '}') break;
        if (c == ',') {
            ++p;
            continue;
        }
        if (c != '"') break;

        sv key = parseString(p, e, keyS);
        skipWs(p, e);
        if (p < e && *p == ':') ++p;
        skipWs(p, e);

        if (key == "type") {
            readStr(p, e, typS, typ);
        } else if (key == "amount") {
            readStr(p, e, amtS, amt);
        } else if (key == "currency") {
            readStr(p, e, curS, cur);
        } else if (key == "account") {
            readStr(p, e, acctS, acct);
        } else if (key == "tags") {
            parseTags(p, e, hasTest);
        } else if (key == "meta") {
            parseMeta(p, e, chanS, chan);
        } else if (key == "rates") {
            parseRates(p, e);
        } else {
            skipValue(p, e);
        }
    }

    if (hasTest || typ == "void") return;

    auto rit = rates.find(cur);
    if (rit == rates.end()) return;

    i64 usd = parseHundredths(amt) * rit->second / 1000000;
    i64 v = (typ == "debit") ? -usd : usd;

    ++counted;
    netTotal += v;

    Group& cg = getGroup(chanMap, chanStore, chan);
    cg.count += 1;
    cg.net += v;

    Group& ag = getGroup(acctMap, acctStore, acct);
    ag.count += 1;
    ag.net += v;
}

}  // namespace

int main(int argc, char** argv) {
    if (argc < 2) {
        std::fprintf(stderr, "usage: solution INPUT_PATH\n");
        return 1;
    }
    std::FILE* f = std::fopen(argv[1], "rb");
    if (!f) {
        std::fprintf(stderr, "cannot open input\n");
        return 1;
    }

    std::vector<char> buf(static_cast<size_t>(1) << 22);
    size_t have = 0;
    for (;;) {
        if (have == buf.size()) buf.resize(buf.size() * 2);
        size_t got = std::fread(buf.data() + have, 1, buf.size() - have, f);
        bool eof = (got == 0);
        have += got;

        size_t cut = 0;
        if (eof) {
            cut = have;
        } else {
            for (size_t i = have; i > 0; --i) {
                if (buf[i - 1] == '\n') {
                    cut = i;
                    break;
                }
            }
        }

        const char* base = buf.data();
        const char* q = base;
        const char* lim = base + cut;
        while (q < lim) {
            const char* nl = static_cast<const char*>(std::memchr(q, '\n', static_cast<size_t>(lim - q)));
            const char* le = nl ? nl : lim;
            processLine(q, le);
            q = nl ? nl + 1 : lim;
        }

        size_t rem = have - cut;
        if (rem > 0 && cut > 0) std::memmove(buf.data(), buf.data() + cut, rem);
        have = rem;

        if (eof) break;
    }
    std::fclose(f);

    std::printf("counted %lld\n", static_cast<long long>(counted));
    std::printf("net %lld\n", static_cast<long long>(netTotal));

    std::vector<const Group*> chans;
    chans.reserve(chanStore.size());
    for (const Group& g : chanStore) chans.push_back(&g);
    std::sort(chans.begin(), chans.end(), [](const Group* a, const Group* b) {
        return a->name < b->name;
    });
    for (const Group* g : chans) {
        std::printf("channel %.*s %lld %lld\n",
                    static_cast<int>(g->name.size()), g->name.data(),
                    static_cast<long long>(g->count), static_cast<long long>(g->net));
    }

    std::vector<const Group*> accts;
    accts.reserve(acctStore.size());
    for (const Group& g : acctStore) accts.push_back(&g);
    size_t k = std::min<size_t>(10, accts.size());
    std::partial_sort(accts.begin(), accts.begin() + static_cast<std::ptrdiff_t>(k), accts.end(),
                      [](const Group* a, const Group* b) {
                          if (a->net != b->net) return a->net > b->net;
                          return a->name < b->name;
                      });
    for (size_t i = 0; i < k; ++i) {
        const Group* g = accts[i];
        std::printf("account %.*s %lld\n",
                    static_cast<int>(g->name.size()), g->name.data(),
                    static_cast<long long>(g->net));
    }

    return 0;
}
