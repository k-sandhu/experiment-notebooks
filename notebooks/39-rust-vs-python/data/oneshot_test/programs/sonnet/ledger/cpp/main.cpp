#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cstdint>
#include <string>
#include <string_view>
#include <vector>
#include <map>
#include <algorithm>

using i64 = long long;

static inline void skipWs(const char*& p) {
    while (*p == ' ' || *p == '\n' || *p == '\t' || *p == '\r') ++p;
}

static void appendUtf8(std::string& o, uint32_t cp) {
    if (cp < 0x80) o.push_back((char)cp);
    else if (cp < 0x800) {
        o.push_back((char)(0xC0 | (cp >> 6)));
        o.push_back((char)(0x80 | (cp & 0x3F)));
    } else if (cp < 0x10000) {
        o.push_back((char)(0xE0 | (cp >> 12)));
        o.push_back((char)(0x80 | ((cp >> 6) & 0x3F)));
        o.push_back((char)(0x80 | (cp & 0x3F)));
    } else {
        o.push_back((char)(0xF0 | (cp >> 18)));
        o.push_back((char)(0x80 | ((cp >> 12) & 0x3F)));
        o.push_back((char)(0x80 | ((cp >> 6) & 0x3F)));
        o.push_back((char)(0x80 | (cp & 0x3F)));
    }
}

static inline int hexv(char c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return 0;
}

static uint32_t hex4(const char* s) {
    return (hexv(s[0]) << 12) | (hexv(s[1]) << 8) | (hexv(s[2]) << 4) | hexv(s[3]);
}

static void decode(const char* s, const char* e, std::string& out) {
    out.clear();
    while (s < e) {
        char c = *s;
        if (c != '\\') { out.push_back(c); ++s; continue; }
        ++s;
        char d = *s++;
        switch (d) {
            case 'n': out.push_back('\n'); break;
            case 't': out.push_back('\t'); break;
            case 'r': out.push_back('\r'); break;
            case 'b': out.push_back('\b'); break;
            case 'f': out.push_back('\f'); break;
            case 'u': {
                uint32_t cp = hex4(s);
                s += 4;
                if (cp >= 0xD800 && cp < 0xDC00 && s + 6 <= e && s[0] == '\\' && s[1] == 'u') {
                    uint32_t lo = hex4(s + 2);
                    if (lo >= 0xDC00 && lo < 0xE000) {
                        cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
                        s += 6;
                    }
                }
                appendUtf8(out, cp);
                break;
            }
            default: out.push_back(d); break; // " \ /
        }
    }
}

// p at opening quote
static inline void parseString(const char*& p, std::string_view& sv, std::string& scratch) {
    ++p;
    const char* start = p;
    bool esc = false;
    while (*p != '"') {
        if (*p == '\\') { esc = true; ++p; }
        ++p;
    }
    const char* e = p;
    ++p;
    if (esc) {
        decode(start, e, scratch);
        sv = std::string_view(scratch);
    } else {
        sv = std::string_view(start, (size_t)(e - start));
    }
}

static inline void skipString(const char*& p) {
    ++p;
    while (*p != '"') {
        if (*p == '\\') ++p;
        ++p;
    }
    ++p;
}

static void skipValue(const char*& p) {
    char c = *p;
    if (c == '"') { skipString(p); return; }
    if (c == '{' || c == '[') {
        int depth = 0;
        do {
            char d = *p;
            if (d == '"') { skipString(p); continue; }
            if (d == '{' || d == '[') ++depth;
            else if (d == '}' || d == ']') --depth;
            ++p;
        } while (depth > 0);
        return;
    }
    while (true) {
        char d = *p;
        if (d == ',' || d == '}' || d == ']' || d == ' ' || d == '\t' || d == '\r' || d == '\n') break;
        ++p;
    }
}

struct Rate { std::string cur; i64 rate; };
static std::vector<Rate> rates;

struct Entry { std::string key; i64 sum; uint64_t h; };
static std::vector<Entry> entries;
static std::vector<uint32_t> table;
static size_t tmask = 0;

static inline uint64_t hashSv(std::string_view s) {
    uint64_t h = 1469598103934665603ULL;
    for (unsigned char c : s) { h ^= c; h *= 1099511628211ULL; }
    h ^= h >> 29;
    return h;
}

static void rehash() {
    size_t ns = table.empty() ? 1024 : table.size() * 2;
    table.assign(ns, 0);
    tmask = ns - 1;
    for (size_t i = 0; i < entries.size(); ++i) {
        size_t pos = entries[i].h & tmask;
        while (table[pos]) pos = (pos + 1) & tmask;
        table[pos] = (uint32_t)(i + 1);
    }
}

static void addAccount(std::string_view k, i64 v) {
    if (table.empty() || (entries.size() + 1) * 2 > table.size()) rehash();
    uint64_t h = hashSv(k);
    size_t pos = h & tmask;
    while (table[pos]) {
        Entry& e = entries[table[pos] - 1];
        if (e.h == h && std::string_view(e.key) == k) { e.sum += v; return; }
        pos = (pos + 1) & tmask;
    }
    entries.push_back(Entry{std::string(k), v, h});
    table[pos] = (uint32_t)entries.size();
}

struct Chan { i64 count = 0; i64 net = 0; };
static std::map<std::string, Chan, std::less<>> channels;

static i64 totalCount = 0, totalNet = 0;

static std::string kScratch, aScratch, tScratch, amScratch, cScratch, chScratch, tagScratch;

static void parseRates(const char*& p) {
    // p at '{'
    ++p;
    std::string_view key;
    while (true) {
        skipWs(p);
        if (*p == '}') { ++p; break; }
        parseString(p, key, kScratch);
        skipWs(p);
        ++p; // ':'
        skipWs(p);
        if (key == "rates" && *p == '{') {
            ++p;
            while (true) {
                skipWs(p);
                if (*p == '}') { ++p; break; }
                std::string_view cur;
                parseString(p, cur, aScratch);
                skipWs(p);
                ++p;
                skipWs(p);
                i64 v = 0;
                if (*p == '"') ++p;
                while (*p >= '0' && *p <= '9') { v = v * 10 + (*p - '0'); ++p; }
                if (*p == '"') ++p;
                rates.push_back(Rate{std::string(cur), v});
                skipWs(p);
                if (*p == ',') ++p;
            }
        } else {
            skipValue(p);
        }
        skipWs(p);
        if (*p == ',') ++p;
    }
}

static void parseTxn(const char*& p) {
    std::string_view account, type, amount, currency, channel;
    bool haveAccount = false, haveChannel = false;
    bool test = false;
    std::string_view key;
    ++p; // '{'
    while (true) {
        skipWs(p);
        if (*p == '}') { ++p; break; }
        parseString(p, key, kScratch);
        skipWs(p);
        ++p; // ':'
        skipWs(p);
        size_t kl = key.size();
        const char* kd = key.data();
        int which = 0;
        switch (kl) {
            case 4: if (!memcmp(kd, "type", 4)) which = 2; else if (!memcmp(kd, "tags", 4)) which = 5; else if (!memcmp(kd, "meta", 4)) which = 6; break;
            case 6: if (!memcmp(kd, "amount", 6)) which = 3; break;
            case 7: if (!memcmp(kd, "account", 7)) which = 1; break;
            case 8: if (!memcmp(kd, "currency", 8)) which = 4; break;
            default: break;
        }
        if (which >= 1 && which <= 4) {
            if (*p == '"') {
                switch (which) {
                    case 1: parseString(p, account, aScratch); haveAccount = true; break;
                    case 2: parseString(p, type, tScratch); break;
                    case 3: parseString(p, amount, amScratch); break;
                    case 4: parseString(p, currency, cScratch); break;
                }
            } else skipValue(p);
        } else if (which == 5) {
            if (*p == '[') {
                ++p;
                while (true) {
                    skipWs(p);
                    if (*p == ']') { ++p; break; }
                    if (*p == '"') {
                        std::string_view t;
                        parseString(p, t, tagScratch);
                        if (t == "test") test = true;
                    } else skipValue(p);
                    skipWs(p);
                    if (*p == ',') ++p;
                }
            } else skipValue(p);
        } else if (which == 6) {
            if (*p == '{') {
                ++p;
                std::string_view k2;
                while (true) {
                    skipWs(p);
                    if (*p == '}') { ++p; break; }
                    parseString(p, k2, kScratch);
                    skipWs(p);
                    ++p;
                    skipWs(p);
                    if (k2 == "channel" && *p == '"') {
                        parseString(p, channel, chScratch);
                        haveChannel = true;
                    } else skipValue(p);
                    skipWs(p);
                    if (*p == ',') ++p;
                }
            } else skipValue(p);
        } else {
            skipValue(p);
        }
        skipWs(p);
        if (*p == ',') ++p;
    }

    if (test) return;
    int sign;
    if (type == "credit" || type == "refund") sign = 1;
    else if (type == "debit") sign = -1;
    else return; // void or unknown

    // amount
    i64 whole = 0;
    const char* a = amount.data();
    const char* ae = a + amount.size();
    while (a < ae && *a >= '0' && *a <= '9') { whole = whole * 10 + (*a - '0'); ++a; }
    i64 frac = 0;
    if (a < ae && *a == '.') {
        ++a;
        int nd = 0;
        while (a < ae && *a >= '0' && *a <= '9' && nd < 2) { frac = frac * 10 + (*a - '0'); ++a; ++nd; }
        if (nd == 1) frac *= 10;
    }
    i64 hundredths = whole * 100 + frac;
    i64 rate = 0;
    for (const Rate& r : rates) {
        if (std::string_view(r.cur) == currency) { rate = r.rate; break; }
    }
    i64 usd = (hundredths * rate) / 1000000;
    i64 val = sign > 0 ? usd : -usd;

    ++totalCount;
    totalNet += val;
    if (haveChannel) {
        auto it = channels.find(channel);
        if (it == channels.end()) it = channels.emplace(std::string(channel), Chan{}).first;
        it->second.count++;
        it->second.net += val;
    }
    if (haveAccount) addAccount(account, val);
}

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    FILE* f = fopen(argv[1], "rb");
    if (!f) return 1;
    size_t cap = 8u << 20;
    std::vector<char> buf(cap + 2);
    size_t have = 0;
    bool ratesDone = false;
    for (;;) {
        size_t want = cap - have;
        size_t n = fread(buf.data() + have, 1, want, f);
        have += n;
        bool eof = n < want;
        size_t end;
        if (eof) {
            if (have > 0 && buf[have - 1] != '\n') buf[have++] = '\n';
            end = have;
        } else {
            size_t i = have;
            while (i > 0 && buf[i - 1] != '\n') --i;
            if (i == 0) {
                cap *= 2;
                buf.resize(cap + 2);
                continue;
            }
            end = i;
        }
        const char* p = buf.data();
        const char* e = buf.data() + end;
        // make sure the byte at e is a harmless sentinel
        while (true) {
            while (p < e && (*p == ' ' || *p == '\n' || *p == '\t' || *p == '\r')) ++p;
            if (p >= e) break;
            if (!ratesDone) { parseRates(p); ratesDone = true; }
            else parseTxn(p);
        }
        if (end < have) memmove(buf.data(), buf.data() + end, have - end);
        have -= end;
        if (eof) break;
    }
    fclose(f);

    printf("counted %lld\n", totalCount);
    printf("net %lld\n", totalNet);
    for (auto& kv : channels)
        printf("channel %s %lld %lld\n", kv.first.c_str(), kv.second.count, kv.second.net);

    std::vector<uint32_t> idx(entries.size());
    for (size_t i = 0; i < idx.size(); ++i) idx[i] = (uint32_t)i;
    auto cmp = [&](uint32_t a, uint32_t b) {
        const Entry& x = entries[a];
        const Entry& y = entries[b];
        if (x.sum != y.sum) return x.sum > y.sum;
        return x.key < y.key;
    };
    size_t top = std::min<size_t>(10, idx.size());
    std::partial_sort(idx.begin(), idx.begin() + top, idx.end(), cmp);
    for (size_t i = 0; i < top; ++i)
        printf("account %s %lld\n", entries[idx[i]].key.c_str(), entries[idx[i]].sum);
    return 0;
}
