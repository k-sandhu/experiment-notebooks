#include <algorithm>
#include <charconv>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>
#include <string_view>
#include <vector>

using namespace std::string_view_literals;

// Open-addressing map from byte-string keys to {net, cnt}. Keys are copied
// once into an arena; lookups never allocate.
struct StrMap {
    struct Entry {
        uint64_t hash = 0;
        uint32_t off = 0;
        uint32_t len = 0;
        int64_t net = 0;
        int64_t cnt = 0;
        bool used = false;
    };
    std::vector<Entry> t;
    std::vector<char> arena;
    size_t mask = 0;
    size_t usedCnt = 0;

    StrMap() { init(64); }
    explicit StrMap(size_t cap) { init(cap); }

    void init(size_t cap) {
        size_t c = 16;
        while (c < cap) c <<= 1;
        t.assign(c, Entry{});
        mask = c - 1;
    }
    static uint64_t hashBytes(const char* p, size_t len) {
        uint64_t h = 1469598103934665603ULL;
        for (size_t i = 0; i < len; i++) {
            h ^= (uint64_t)(unsigned char)p[i];
            h *= 1099511628211ULL;
        }
        h ^= h >> 33; h *= 0xff51afd7ed558ccdULL; h ^= h >> 33;
        return h;
    }
    void grow() {
        std::vector<Entry> old = std::move(t);
        t.assign(old.size() * 2, Entry{});
        mask = t.size() - 1;
        for (auto& e : old) if (e.used) {
            size_t i = (size_t)e.hash & mask;
            while (t[i].used) i = (i + 1) & mask;
            t[i] = e;
        }
    }
    Entry* findOrInsert(std::string_view key) {
        if ((usedCnt + 1) * 10 > t.size() * 7) grow();
        uint64_t h = hashBytes(key.data(), key.size());
        size_t i = (size_t)h & mask;
        while (true) {
            Entry& e = t[i];
            if (!e.used) {
                e.used = true; e.hash = h;
                e.off = (uint32_t)arena.size(); e.len = (uint32_t)key.size();
                arena.insert(arena.end(), key.begin(), key.end());
                e.net = 0; e.cnt = 0; usedCnt++;
                return &e;
            }
            if (e.hash == h && e.len == key.size() &&
                (e.len == 0 || std::memcmp(arena.data() + e.off, key.data(), e.len) == 0))
                return &e;
            i = (i + 1) & mask;
        }
    }
    Entry* find(std::string_view key) {
        uint64_t h = hashBytes(key.data(), key.size());
        size_t i = (size_t)h & mask;
        while (true) {
            Entry& e = t[i];
            if (!e.used) return nullptr;
            if (e.hash == h && e.len == key.size() &&
                (e.len == 0 || std::memcmp(arena.data() + e.off, key.data(), e.len) == 0))
                return &e;
            i = (i + 1) & mask;
        }
    }
    std::string_view keyOf(const Entry& e) const {
        return {arena.data() + e.off, e.len};
    }
};

static int cmpBytes(std::string_view a, std::string_view b) {
    size_t m = a.size() < b.size() ? a.size() : b.size();
    int c = m ? std::memcmp(a.data(), b.data(), m) : 0;
    if (c) return c;
    return a.size() < b.size() ? -1 : (a.size() > b.size() ? 1 : 0);
}

struct Parser {
    const unsigned char* d;
    size_t n, pos = 0;
    std::string keyDec, acctDec, chanDec, miscDec;

    void skipWs() {
        while (pos < n) {
            unsigned char c = d[pos];
            if (c == ' ' || c == '\t' || c == '\n' || c == '\r') pos++; else break;
        }
    }
    void skipStringRaw() { // d[pos]=='"'
        pos++;
        while (pos < n) {
            unsigned char c = d[pos];
            if (c == '"') { pos++; return; }
            pos += (c == '\\') ? 2 : 1;
        }
    }
    static void appendUtf8(std::string& s, uint32_t cp) {
        if (cp < 0x80) s.push_back((char)cp);
        else if (cp < 0x800) {
            s.push_back((char)(0xC0 | (cp >> 6)));
            s.push_back((char)(0x80 | (cp & 0x3F)));
        } else if (cp < 0x10000) {
            s.push_back((char)(0xE0 | (cp >> 12)));
            s.push_back((char)(0x80 | ((cp >> 6) & 0x3F)));
            s.push_back((char)(0x80 | (cp & 0x3F)));
        } else {
            s.push_back((char)(0xF0 | (cp >> 18)));
            s.push_back((char)(0x80 | ((cp >> 12) & 0x3F)));
            s.push_back((char)(0x80 | ((cp >> 6) & 0x3F)));
            s.push_back((char)(0x80 | (cp & 0x3F)));
        }
    }
    uint32_t hex4(size_t& i, size_t end) {
        uint32_t v = 0;
        for (int k = 0; k < 4 && i < end; k++, i++) {
            unsigned char c = d[i];
            v <<= 4;
            if (c >= '0' && c <= '9') v |= c - '0';
            else if (c >= 'a' && c <= 'f') v |= c - 'a' + 10;
            else if (c >= 'A' && c <= 'F') v |= c - 'A' + 10;
        }
        return v;
    }
    // d[pos]=='"'. Returns view into data, or into dec when escapes present.
    std::string_view parseString(std::string& dec) {
        pos++;
        size_t start = pos;
        bool esc = false;
        while (pos < n) {
            unsigned char c = d[pos];
            if (c == '"') break;
            if (c == '\\') { esc = true; pos += 2; } else pos++;
        }
        size_t end = pos;
        if (pos < n) pos++;
        if (!esc) return {(const char*)d + start, end - start};
        dec.clear();
        size_t i = start;
        while (i < end) {
            unsigned char c = d[i];
            if (c != '\\') { dec.push_back((char)c); i++; continue; }
            i++;
            if (i >= end) break;
            unsigned char e = d[i++];
            switch (e) {
                case '"': dec.push_back('"'); break;
                case '\\': dec.push_back('\\'); break;
                case '/': dec.push_back('/'); break;
                case 'b': dec.push_back('\b'); break;
                case 'f': dec.push_back('\f'); break;
                case 'n': dec.push_back('\n'); break;
                case 'r': dec.push_back('\r'); break;
                case 't': dec.push_back('\t'); break;
                case 'u': {
                    uint32_t cp = hex4(i, end);
                    if (cp >= 0xD800 && cp <= 0xDBFF && i + 1 < end && d[i] == '\\' && d[i + 1] == 'u') {
                        size_t save = i; i += 2;
                        uint32_t lo = hex4(i, end);
                        if (lo >= 0xDC00 && lo <= 0xDFFF)
                            cp = 0x10000u + ((cp - 0xD800u) << 10) + (lo - 0xDC00u);
                        else { appendUtf8(dec, cp); cp = lo; (void)save; }
                    }
                    appendUtf8(dec, cp);
                    break;
                }
                default: dec.push_back((char)e); break;
            }
        }
        return {dec.data(), dec.size()};
    }
    void skipValue() {
        skipWs();
        if (pos >= n) return;
        unsigned char c = d[pos];
        if (c == '"') { skipStringRaw(); return; }
        if (c == '{' || c == '[') {
            int depth = 0;
            while (pos < n) {
                unsigned char ch = d[pos];
                if (ch == '"') { skipStringRaw(); continue; }
                if (ch == '{' || ch == '[') { depth++; pos++; }
                else if (ch == '}' || ch == ']') { depth--; pos++; if (depth == 0) return; }
                else pos++;
            }
            return;
        }
        while (pos < n) {
            unsigned char ch = d[pos];
            if (ch == ',' || ch == '}' || ch == ']' || ch == ' ' || ch == '\t' || ch == '\n' || ch == '\r') break;
            pos++;
        }
    }
    int64_t parseInt64() {
        skipWs();
        bool neg = false;
        if (pos < n && d[pos] == '-') { neg = true; pos++; }
        int64_t v = 0;
        while (pos < n && d[pos] >= '0' && d[pos] <= '9') v = v * 10 + (d[pos++] - '0');
        return neg ? -v : v;
    }
    static int64_t parseAmount(std::string_view v) {
        size_t i = 0, m = v.size();
        int64_t ip = 0;
        while (i < m && v[i] != '.') { ip = ip * 10 + (v[i] - '0'); i++; }
        int64_t h = ip * 100;
        if (i < m) { // '.'
            i++;
            if (i < m) { h += (v[i] - '0') * 10; i++; }
            if (i < m) { h += (v[i] - '0'); }
        }
        return h;
    }
};

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    FILE* f = std::fopen(argv[1], "rb");
    if (!f) return 1;
    std::fseek(f, 0, SEEK_END);
    long fsz = std::ftell(f);
    if (fsz < 0) fsz = 0;
    std::fseek(f, 0, SEEK_SET);
    std::vector<unsigned char> data((size_t)fsz);
    size_t got = fsz ? std::fread(data.data(), 1, (size_t)fsz, f) : 0;
    data.resize(got);
    std::fclose(f);

    Parser p;
    p.d = data.data();
    p.n = data.size();

    StrMap rates(64), channels(64), accounts(1 << 16);

    // First object: rates.
    p.skipWs();
    if (p.pos < p.n && p.d[p.pos] == '{') {
        p.pos++; p.skipWs();
        if (p.pos < p.n && p.d[p.pos] == '}') p.pos++;
        else while (true) {
            p.skipWs();
            auto key = p.parseString(p.keyDec);
            p.skipWs(); p.pos++; // ':'
            p.skipWs();
            if (key == "rates"sv) {
                p.pos++; p.skipWs(); // '{'
                if (p.pos < p.n && p.d[p.pos] == '}') p.pos++;
                else while (true) {
                    p.skipWs();
                    auto ck = p.parseString(p.miscDec);
                    p.skipWs(); p.pos++; // ':'
                    int64_t rv = p.parseInt64();
                    rates.findOrInsert(ck)->net = rv;
                    p.skipWs();
                    if (p.pos < p.n && p.d[p.pos] == ',') { p.pos++; continue; }
                    if (p.pos < p.n && p.d[p.pos] == '}') { p.pos++; break; }
                    break;
                }
            } else p.skipValue();
            p.skipWs();
            if (p.pos < p.n && p.d[p.pos] == ',') { p.pos++; continue; }
            if (p.pos < p.n && p.d[p.pos] == '}') { p.pos++; break; }
            break;
        }
    }

    int64_t counted = 0, net = 0;

    while (true) {
        p.skipWs();
        if (p.pos >= p.n) break;
        // One transaction object; d[pos]=='{'
        std::string_view acct{}, chan{};
        int sign = 1;
        bool isVoid = false, hasTest = false;
        int64_t hundredths = 0, rate = 0;
        p.pos++; p.skipWs();
        if (p.pos < p.n && p.d[p.pos] == '}') { p.pos++; }
        else while (true) {
            p.skipWs();
            auto key = p.parseString(p.keyDec);
            p.skipWs(); p.pos++; // ':'
            p.skipWs();
            if (key == "account"sv) {
                acct = p.parseString(p.acctDec);
            } else if (key == "type"sv) {
                auto v = p.parseString(p.miscDec);
                if (v == "void"sv) isVoid = true;
                else if (v == "debit"sv) sign = -1;
                else sign = 1;
            } else if (key == "amount"sv) {
                hundredths = Parser::parseAmount(p.parseString(p.miscDec));
            } else if (key == "currency"sv) {
                auto v = p.parseString(p.miscDec);
                auto* e = rates.find(v);
                rate = e ? e->net : 0;
            } else if (key == "tags"sv) {
                p.pos++; p.skipWs(); // '['
                if (p.pos < p.n && p.d[p.pos] == ']') p.pos++;
                else while (true) {
                    p.skipWs();
                    if (p.pos < p.n && p.d[p.pos] == '"') {
                        if (p.parseString(p.miscDec) == "test"sv) hasTest = true;
                    } else p.skipValue();
                    p.skipWs();
                    if (p.pos < p.n && p.d[p.pos] == ',') { p.pos++; continue; }
                    if (p.pos < p.n && p.d[p.pos] == ']') { p.pos++; break; }
                    break;
                }
            } else if (key == "meta"sv) {
                p.pos++; p.skipWs(); // '{'
                if (p.pos < p.n && p.d[p.pos] == '}') p.pos++;
                else while (true) {
                    p.skipWs();
                    auto k2 = p.parseString(p.keyDec);
                    p.skipWs(); p.pos++; // ':'
                    p.skipWs();
                    if (k2 == "channel"sv) chan = p.parseString(p.chanDec);
                    else p.skipValue();
                    p.skipWs();
                    if (p.pos < p.n && p.d[p.pos] == ',') { p.pos++; continue; }
                    if (p.pos < p.n && p.d[p.pos] == '}') { p.pos++; break; }
                    break;
                }
            } else {
                p.skipValue();
            }
            p.skipWs();
            if (p.pos < p.n && p.d[p.pos] == ',') { p.pos++; continue; }
            if (p.pos < p.n && p.d[p.pos] == '}') { p.pos++; break; }
            break;
        }

        if (isVoid || hasTest) continue;
        int64_t usd = (hundredths * rate) / 1000000;
        int64_t signedVal = sign < 0 ? -usd : usd;
        counted++;
        net += signedVal;
        accounts.findOrInsert(acct)->net += signedVal;
        auto* ce = channels.findOrInsert(chan);
        ce->net += signedVal;
        ce->cnt++;
    }

    std::vector<const StrMap::Entry*> chans, accts;
    for (auto& e : channels.t) if (e.used) chans.push_back(&e);
    for (auto& e : accounts.t) if (e.used) accts.push_back(&e);
    std::sort(chans.begin(), chans.end(), [&](const StrMap::Entry* a, const StrMap::Entry* b) {
        return cmpBytes(channels.keyOf(*a), channels.keyOf(*b)) < 0;
    });
    std::sort(accts.begin(), accts.end(), [&](const StrMap::Entry* a, const StrMap::Entry* b) {
        if (a->net != b->net) return a->net > b->net;
        return cmpBytes(accounts.keyOf(*a), accounts.keyOf(*b)) < 0;
    });

    std::string out;
    out.reserve(4096);
    char num[32];
    auto appInt = [&](int64_t v) {
        auto r = std::to_chars(num, num + sizeof(num), v);
        out.append(num, r.ptr);
    };
    out += "counted "; appInt(counted); out += '\n';
    out += "net "; appInt(net); out += '\n';
    for (auto* e : chans) {
        out += "channel ";
        auto k = channels.keyOf(*e);
        out.append(k.data(), k.size());
        out += ' '; appInt(e->cnt); out += ' '; appInt(e->net); out += '\n';
    }
    size_t top = accts.size() < 10 ? accts.size() : 10;
    for (size_t i = 0; i < top; i++) {
        out += "account ";
        auto k = accounts.keyOf(*accts[i]);
        out.append(k.data(), k.size());
        out += ' '; appInt(accts[i]->net); out += '\n';
    }
    std::fwrite(out.data(), 1, out.size(), stdout);
    return 0;
}
