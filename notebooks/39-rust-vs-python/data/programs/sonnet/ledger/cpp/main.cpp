#include <cstdio>
#include <cstdint>
#include <cstring>
#include <string>
#include <vector>
#include <algorithm>
#include <io.h>
#include <fcntl.h>

typedef int64_t i64;
typedef unsigned char uchar;

struct Str {
    const uchar* p;
    int n;
};

static void appendUtf8(std::string& o, uint32_t cp) {
    if (cp < 0x80) {
        o.push_back((char)cp);
    } else if (cp < 0x800) {
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

static inline uint32_t hex4(const uchar* p) {
    uint32_t v = 0;
    for (int i = 0; i < 4; i++) {
        uchar c = p[i];
        v <<= 4;
        if (c >= '0' && c <= '9') v |= c - '0';
        else if (c >= 'a' && c <= 'f') v |= c - 'a' + 10;
        else v |= c - 'A' + 10;
    }
    return v;
}

// p at opening quote; leaves p after closing quote. Escapes are decoded into buf.
static inline Str parseStr(const uchar*& p, std::string& buf) {
    const uchar* s = ++p;
    for (;;) {
        uchar c = *p;
        if (c == '"') {
            Str r{s, (int)(p - s)};
            ++p;
            return r;
        }
        if (c == '\\') break;
        ++p;
    }
    buf.assign((const char*)s, p - s);
    for (;;) {
        uchar c = *p;
        if (c == '"') { ++p; break; }
        if (c == '\\') {
            uchar e = p[1];
            p += 2;
            switch (e) {
                case 'n': buf.push_back('\n'); break;
                case 't': buf.push_back('\t'); break;
                case 'r': buf.push_back('\r'); break;
                case 'b': buf.push_back('\b'); break;
                case 'f': buf.push_back('\f'); break;
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
                    appendUtf8(buf, cp);
                    break;
                }
                default: buf.push_back((char)e); break;
            }
        } else {
            buf.push_back((char)c);
            ++p;
        }
    }
    return Str{(const uchar*)buf.data(), (int)buf.size()};
}

static inline void skipWs(const uchar*& p) {
    while (*p == ' ' || *p == '\n' || *p == '\t' || *p == '\r') ++p;
}

static inline void skipString(const uchar*& p) {
    ++p;
    for (;;) {
        uchar c = *p;
        if (c == '"') break;
        if (c == '\\') ++p;
        ++p;
    }
    ++p;
}

static void skipValue(const uchar*& p) {
    uchar c = *p;
    if (c == '"') { skipString(p); return; }
    if (c == '{' || c == '[') {
        int depth = 0;
        for (;;) {
            c = *p;
            if (c == '"') { skipString(p); continue; }
            ++p;
            if (c == '{' || c == '[') ++depth;
            else if (c == '}' || c == ']') { if (--depth == 0) return; }
        }
    }
    while (c != ',' && c != '}' && c != ']' && c != ' ' && c != '\n' && c != '\r' && c != '\t') c = *++p;
}

struct Entry {
    uint32_t hash;
    std::string key;
    i64 sum;
    i64 count;
};

struct Table {
    std::vector<Entry> entries;
    std::vector<int32_t> index;
    uint32_t mask;
    Table() : index(1 << 12, -1), mask((1 << 12) - 1) {}
    void grow() {
        size_t cap = index.size() * 2;
        index.assign(cap, -1);
        mask = (uint32_t)cap - 1;
        for (size_t i = 0; i < entries.size(); i++) {
            uint32_t h = entries[i].hash & mask;
            while (index[h] >= 0) h = (h + 1) & mask;
            index[h] = (int32_t)i;
        }
    }
    inline void add(Str k, i64 v) {
        uint32_t hash = 2166136261u;
        for (int i = 0; i < k.n; i++) hash = (hash ^ k.p[i]) * 16777619u;
        hash ^= hash >> 15;
        uint32_t h = hash & mask;
        for (;;) {
            int32_t ix = index[h];
            if (ix < 0) break;
            Entry& e = entries[ix];
            if (e.hash == hash && (int)e.key.size() == k.n && memcmp(e.key.data(), k.p, k.n) == 0) {
                e.sum += v;
                e.count++;
                return;
            }
            h = (h + 1) & mask;
        }
        index[h] = (int32_t)entries.size();
        entries.push_back(Entry{hash, std::string((const char*)k.p, k.n), v, 1});
        if (entries.size() * 2 > index.size()) grow();
    }
};

struct Rate {
    std::string key;
    i64 rate;
};

static std::vector<Rate> rates;
static Table accounts, channels;
static i64 totalCount = 0, totalNet = 0;
static std::string sT, sA, sC;

static inline i64 parseInt(const uchar*& p) {
    i64 v = 0;
    while (*p >= '0' && *p <= '9') v = v * 10 + (*p++ - '0');
    return v;
}

static void parseRates(const uchar*& p) {
    ++p;
    for (;;) {
        skipWs(p);
        Str k = parseStr(p, sT);
        skipWs(p); ++p; skipWs(p);
        if (k.n == 5 && memcmp(k.p, "rates", 5) == 0) {
            ++p;
            for (;;) {
                skipWs(p);
                if (*p == '}') { ++p; break; }
                Str c = parseStr(p, sT);
                std::string name((const char*)c.p, c.n);
                skipWs(p); ++p; skipWs(p);
                i64 r = parseInt(p);
                rates.push_back(Rate{name, r});
                skipWs(p);
                if (*p == ',') ++p;
            }
        } else {
            skipValue(p);
        }
        skipWs(p);
        if (*p == ',') { ++p; continue; }
        ++p;
        break;
    }
}

enum { K_OTHER, K_ACC, K_TYPE, K_AMT, K_CUR, K_TAGS, K_META };

static inline int classify(Str k) {
    const char* s = (const char*)k.p;
    switch (k.n) {
        case 4:
            if (memcmp(s, "type", 4) == 0) return K_TYPE;
            if (memcmp(s, "tags", 4) == 0) return K_TAGS;
            if (memcmp(s, "meta", 4) == 0) return K_META;
            return K_OTHER;
        case 6: return memcmp(s, "amount", 6) == 0 ? K_AMT : K_OTHER;
        case 7: return memcmp(s, "account", 7) == 0 ? K_ACC : K_OTHER;
        case 8: return memcmp(s, "currency", 8) == 0 ? K_CUR : K_OTHER;
    }
    return K_OTHER;
}

static void parseTx(const uchar*& p) {
    ++p;
    Str acc{nullptr, 0}, chan{nullptr, 0};
    int type = 0;
    i64 hund = 0, rate = 0;
    bool test = false;
    for (;;) {
        skipWs(p);
        if (*p == '}') { ++p; break; }
        Str k = parseStr(p, sT);
        skipWs(p); ++p; skipWs(p);
        switch (classify(k)) {
            case K_ACC:
                acc = parseStr(p, sA);
                break;
            case K_TYPE: {
                Str t = parseStr(p, sT);
                type = t.n ? t.p[0] : 0;
                break;
            }
            case K_AMT: {
                Str a = parseStr(p, sT);
                const uchar* q = a.p;
                const uchar* e = q + a.n;
                i64 ip = 0;
                while (q < e && *q != '.') ip = ip * 10 + (*q++ - '0');
                i64 fr = 0;
                if (q < e) {
                    ++q;
                    if (q < e) { fr = (*q++ - '0') * 10; if (q < e) fr += *q - '0'; }
                }
                hund = ip * 100 + fr;
                break;
            }
            case K_CUR: {
                Str c = parseStr(p, sT);
                for (const Rate& r : rates) {
                    if ((int)r.key.size() == c.n && memcmp(r.key.data(), c.p, c.n) == 0) { rate = r.rate; break; }
                }
                break;
            }
            case K_TAGS: {
                ++p;
                skipWs(p);
                if (*p == ']') { ++p; break; }
                for (;;) {
                    skipWs(p);
                    Str s = parseStr(p, sT);
                    if (s.n == 4 && memcmp(s.p, "test", 4) == 0) test = true;
                    skipWs(p);
                    if (*p == ',') { ++p; continue; }
                    ++p;
                    break;
                }
                break;
            }
            case K_META: {
                ++p;
                for (;;) {
                    skipWs(p);
                    if (*p == '}') { ++p; break; }
                    Str mk = parseStr(p, sT);
                    skipWs(p); ++p; skipWs(p);
                    if (mk.n == 7 && memcmp(mk.p, "channel", 7) == 0 && *p == '"') chan = parseStr(p, sC);
                    else skipValue(p);
                    skipWs(p);
                    if (*p == ',') { ++p; continue; }
                    ++p;
                    break;
                }
                break;
            }
            default:
                skipValue(p);
        }
        skipWs(p);
        if (*p == ',') { ++p; continue; }
        ++p;
        break;
    }
    if (type == 'v' || test) return;
    i64 usd = hund * rate / 1000000;
    i64 v = type == 'd' ? -usd : usd;
    totalCount++;
    totalNet += v;
    accounts.add(acc, v);
    channels.add(chan, v);
}

static bool ratesDone = false;

static void processChunk(const uchar* p, const uchar* end) {
    for (;;) {
        skipWs(p);
        if (p >= end) break;
        if (!ratesDone) { parseRates(p); ratesDone = true; }
        else parseTx(p);
    }
}

int main(int argc, char** argv) {
    _setmode(_fileno(stdout), _O_BINARY);
    FILE* f = fopen(argv[1], "rb");
    if (!f) return 1;
    size_t cap = 1 << 22;
    std::vector<uchar> buf(cap + 16);
    size_t have = 0;
    bool eof = false;
    while (!eof) {
        size_t n = fread(buf.data() + have, 1, cap - have, f);
        if (n == 0) eof = true;
        have += n;
        size_t end;
        if (eof) {
            if (have > 0 && buf[have - 1] != '\n') buf[have++] = '\n';
            end = have;
            buf[end] = 0;
        } else {
            size_t i = have;
            while (i > 0 && buf[i - 1] != '\n') i--;
            if (i == 0) {
                cap *= 2;
                buf.resize(cap + 16);
                continue;
            }
            end = i;
        }
        processChunk(buf.data(), buf.data() + end);
        if (!eof) {
            memmove(buf.data(), buf.data() + end, have - end);
            have -= end;
        }
    }
    fclose(f);

    std::string out;
    char tmp[128];
    snprintf(tmp, sizeof tmp, "counted %lld\nnet %lld\n", (long long)totalCount, (long long)totalNet);
    out += tmp;
    std::vector<Entry*> ch;
    for (auto& e : channels.entries) ch.push_back(&e);
    std::sort(ch.begin(), ch.end(), [](Entry* a, Entry* b) { return a->key < b->key; });
    for (Entry* e : ch) {
        out += "channel " + e->key;
        snprintf(tmp, sizeof tmp, " %lld %lld\n", (long long)e->count, (long long)e->sum);
        out += tmp;
    }
    std::vector<Entry*> ac;
    for (auto& e : accounts.entries) ac.push_back(&e);
    auto cmp = [](Entry* a, Entry* b) { return a->sum != b->sum ? a->sum > b->sum : a->key < b->key; };
    size_t top = std::min<size_t>(10, ac.size());
    std::partial_sort(ac.begin(), ac.begin() + top, ac.end(), cmp);
    for (size_t i = 0; i < top; i++) {
        out += "account " + ac[i]->key;
        snprintf(tmp, sizeof tmp, " %lld\n", (long long)ac[i]->sum);
        out += tmp;
    }
    fwrite(out.data(), 1, out.size(), stdout);
    return 0;
}
