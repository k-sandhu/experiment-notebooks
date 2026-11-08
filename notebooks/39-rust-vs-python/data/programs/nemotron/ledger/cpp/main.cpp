#include <cstdio>
#include <cstdint>
#include <cstring>
#include <vector>
#include <string>
#include <unordered_map>
#include <algorithm>
#include <utility>
#include <fcntl.h>
#include <io.h>

using i64 = long long;

static void appendInt(std::string& s, i64 v) {
    char tmp[24];
    char* t = tmp + sizeof(tmp);
    bool neg = v < 0;
    unsigned long long u = neg ? (unsigned long long)(-(v + 1)) + 1ULL : (unsigned long long)v;
    do { *--t = static_cast<char>('0' + (u % 10)); u /= 10; } while (u);
    if (neg) *--t = '-';
    s.append(t, tmp + sizeof(tmp));
}

struct Rate {
    std::string name;
    i64 value;
};

// Fast single-pass JSON scanner for one transaction line.
struct Parser {
    const char* p;
    const char* end;
    std::string tmp; // scratch for unescaping

    // Output fields
    std::string account_;
    std::string type_;
    i64 hundredths_ = 0;
    std::string currency_;
    bool testTag_ = false;
    std::string channel_;

    Parser(const char* b, const char* e) : p(b), end(e) {}

    void skipWs() {
        for (;;) {
            if (p == end) return;
            char c = *p;
            if (c == ' ' || c == '\t' || c == '\r' || c == '\n') ++p;
            else return;
        }
    }

    char cur() const { return p < end ? *p : '\0'; }

    struct Scan {
        const char* start;
        size_t len;
        bool hadEscape;
    };

    // Current char must be '"'. Leaves p just after the closing quote.
    Scan scanString() {
        ++p; // opening quote
        const char* start = p;
        bool esc = false;
        while (p < end && *p != '"') {
            if (*p == '\\') { esc = true; ++p; if (p < end) ++p; }
            else ++p;
        }
        Scan s{start, (size_t)(p - start), esc};
        if (p < end) ++p; // closing quote
        return s;
    }

    static int hexVal(char c) {
        if (c >= '0' && c <= '9') return c - '0';
        if (c >= 'a' && c <= 'f') return c - 'a' + 10;
        return c - 'A' + 10;
    }

    void unescapeAppend(const char* start, size_t len) {
        tmp.clear();
        size_t i = 0;
        while (i < len) {
            char c = start[i];
            if (c != '\\') { tmp.push_back(c); ++i; continue; }
            char e = start[i + 1];
            i += 2;
            switch (e) {
                case '"': tmp.push_back('"'); break;
                case '\\': tmp.push_back('\\'); break;
                case '/': tmp.push_back('/'); break;
                case 'n': tmp.push_back('\n'); break;
                case 't': tmp.push_back('\t'); break;
                case 'r': tmp.push_back('\r'); break;
                case 'b': tmp.push_back('\b'); break;
                case 'f': tmp.push_back('\f'); break;
                case 'u': {
                    unsigned cp = 0;
                    for (int k = 0; k < 4; ++k) cp = (cp << 4) | (unsigned)hexVal(start[i + k]);
                    i += 4;
                    if (cp >= 0xD800 && cp <= 0xDBFF && i + 2 <= len && start[i] == '\\' && start[i + 1] == 'u') {
                        unsigned cp2 = 0;
                        for (int k = 0; k < 4; ++k) cp2 = (cp2 << 4) | (unsigned)hexVal(start[i + 2 + k]);
                        i += 6;
                        if (cp2 >= 0xDC00 && cp2 <= 0xDFFF) {
                            cp = 0x10000u + ((cp - 0xD800u) << 10) + (cp2 - 0xDC00u);
                        }
                    }
                    if (cp < 0x80) tmp.push_back((char)cp);
                    else if (cp < 0x800) { tmp.push_back((char)(0xC0 | (cp >> 6))); tmp.push_back((char)(0x80 | (cp & 0x3F))); }
                    else if (cp < 0x10000) { tmp.push_back((char)(0xE0 | (cp >> 12))); tmp.push_back((char)(0x80 | ((cp >> 6) & 0x3F))); tmp.push_back((char)(0x80 | (cp & 0x3F))); }
                    else { tmp.push_back((char)(0xF0 | (cp >> 18))); tmp.push_back((char)(0x80 | ((cp >> 12) & 0x3F))); tmp.push_back((char)(0x80 | ((cp >> 6) & 0x3F))); tmp.push_back((char)(0x80 | (cp & 0x3F))); }
                    break;
                }
            }
        }
    }

    bool matchLit(const Scan& s, const char* lit) {
        size_t n = std::strlen(lit);
        if (s.len != n) return false;
        if (!s.hadEscape) return std::memcmp(s.start, lit, n) == 0;
        unescapeAppend(s.start, s.len);
        return tmp.size() == n && std::memcmp(tmp.data(), lit, n) == 0;
    }

    void takeString(const Scan& s, std::string& out) {
        if (!s.hadEscape) { out.assign(s.start, s.len); return; }
        unescapeAppend(s.start, s.len);
        out = tmp;
    }

    static i64 parseAmountRaw(const char* s, size_t len) {
        i64 h = 0;
        bool dot = false;
        i64 fr = 0;
        int fd = 0;
        for (size_t i = 0; i < len; ++i) {
            char c = s[i];
            if (c >= '0' && c <= '9') {
                if (!dot) h = h * 10 + (c - '0');
                else { fr = fr * 10 + (c - '0'); ++fd; }
            } else if (c == '.' && !dot) {
                dot = true;
            }
        }
        if (!dot) return h * 100;
        return fd == 1 ? h * 100 + fr * 10 : h * 100 + fr;
    }

    i64 parseAmount(const Scan& s) {
        if (!s.hadEscape) return parseAmountRaw(s.start, s.len);
        unescapeAppend(s.start, s.len);
        return parseAmountRaw(tmp.data(), tmp.size());
    }

    void skipArray() {
        ++p; // '['
        for (;;) {
            skipWs();
            if (cur() == ']') { ++p; return; }
            skipValue();
            skipWs();
            if (cur() == ',') { ++p; continue; }
            if (cur() == ']') { ++p; return; }
        }
    }

    void skipObject() {
        ++p; // '{'
        for (;;) {
            skipWs();
            if (cur() == '}') { ++p; return; }
            scanString(); // key
            skipWs();
            if (cur() == ':') ++p;
            skipValue();
            skipWs();
            if (cur() == ',') { ++p; continue; }
            if (cur() == '}') { ++p; return; }
        }
    }

    void skipValue() {
        skipWs();
        char c = cur();
        if (c == '"') scanString();
        else if (c == '{') skipObject();
        else if (c == '[') skipArray();
        else if (c == 't') p += 4; // true
        else if (c == 'f') p += 5; // false
        else if (c == 'n') p += 4; // null
        else { // number
            while (p < end && *p >= '0' && *p <= '9') ++p;
            if (p < end && (*p == '-' || *p == '+' || *p == '.' || *p == 'e' || *p == 'E')) ++p;
        }
    }

    // Tags array: true if any element equals exactly "test".
    bool scanTags() {
        ++p; // '['
        bool found = false;
        for (;;) {
            skipWs();
            if (cur() == ']') { ++p; return found; }
            Scan s = scanString();
            if (!found && matchLit(s, "test")) found = true;
            skipWs();
            if (cur() == ',') { ++p; continue; }
            if (cur() == ']') { ++p; return found; }
        }
    }

    void parseTxObject() {
        ++p; // '{'
        for (;;) {
            skipWs();
            if (cur() == '}') { ++p; return; }
            Scan key = scanString();
            skipWs();
            if (cur() == ':') ++p;
            skipWs();
            if (matchLit(key, "account") && cur() == '"') {
                takeString(scanString(), account_);
            } else if (matchLit(key, "type") && cur() == '"') {
                takeString(scanString(), type_);
            } else if (matchLit(key, "amount") && cur() == '"') {
                hundredths_ = parseAmount(scanString());
            } else if (matchLit(key, "currency") && cur() == '"') {
                takeString(scanString(), currency_);
            } else if (matchLit(key, "tags")) {
                if (cur() == '[') testTag_ = scanTags();
                else skipArray();
            } else if (matchLit(key, "meta")) {
                if (cur() == '{') {
                    ++p; // '{'
                    for (;;) {
                        skipWs();
                        if (cur() == '}') { ++p; break; }
                        Scan key = scanString();
                        skipWs();
                        if (cur() == ':') ++p;
                        skipWs();
                        if (matchLit(key, "channel") && cur() == '"') {
                            takeString(scanString(), channel_);
                        } else {
                            skipValue();
                        }
                        skipWs();
                        if (cur() == ',') { ++p; continue; }
                        if (cur() == '}') { ++p; break; }
                    }
                } else {
                    skipObject();
                }
            } else {
                skipValue();
            }
            skipWs();
            if (cur() == ',') { ++p; continue; }
            if (cur() == '}') { ++p; return; }
        }
    }
};

static const char* parseRates(const char* b, const char* e, std::vector<Rate>& rates) {
    const char* p = b;
    const char* end = e;
    while (p < end && *p != '{') ++p;
    if (p == end) return p;
    ++p; // outer '{'
    for (;;) {
        while (p < end && (*p == ' ' || *p == '\t' || *p == '\r' || *p == '\n')) ++p;
        if (p == end || *p == '}') break;
        if (*p == '"') {
            ++p;
            const char* ks = p;
            while (p < end && *p != '"') {
                if (*p == '\\') { ++p; if (p < end) ++p; }
                else ++p;
            }
            size_t klen = (size_t)(p - ks);
            if (p < end) ++p;
            while (p < end && (*p == ' ' || *p == '\t' || *p == '\r')) ++p;
            if (p < end && *p == ':') ++p;
            while (p < end && (*p == ' ' || *p == '\t' || *p == '\r' || *p == '\n')) ++p;
            bool isRates = (klen == 5 && std::memcmp(ks, "rates", 5) == 0);
            if (isRates && p < end && *p == '{') {
                ++p; // rates object
                for (;;) {
                    while (p < end && (*p == ' ' || *p == '\t' || *p == '\r' || *p == '\n')) ++p;
                    if (p == end || *p == '}') break;
                    std::string name;
                    if (*p == '"') {
                        ++p;
                        const char* ks2 = p;
                        while (p < end && *p != '"') {
                            if (*p == '\\') { ++p; if (p < end) ++p; }
                            else ++p;
                        }
                        name.assign(ks2, (size_t)(p - ks2));
                        if (p < end) ++p;
                    }
                    while (p < end && (*p == ' ' || *p == '\t' || *p == '\r')) ++p;
                    if (p < end && *p == ':') ++p;
                    while (p < end && (*p == ' ' || *p == '\t' || *p == '\r' || *p == '\n')) ++p;
                    i64 v = 0;
                    bool neg = false;
                    if (p < end && *p == '-') { neg = true; ++p; }
                    while (p < end && *p >= '0' && *p <= '9') { v = v * 10 + (*p - '0'); ++p; }
                    if (neg) v = -v;
                    Rate r;
                    r.name = std::move(name);
                    r.value = v;
                    rates.push_back(std::move(r));
                    while (p < end && (*p == ' ' || *p == '\t' || *p == '\r' || *p == ',' || *p == '}')) {
                        if (*p == ',') { ++p; break; }
                        if (*p == '}') { if (p < end) ++p; break; }
                        ++p;
                    }
                }
                break;
            } else {
                // skip the value
                if (p < end) {
                    char c = *p;
                    if (c == '"') { ++p; while (p < end && *p != '"') { if (*p == '\\') { ++p; if (p < end) ++p; } else ++p; } if (p < end) ++p; }
                    else if (c == '{') { ++p; int depth=1; while(p<end&&depth){if(*p=='{')++depth; else if(*p=='}'){--depth; if(depth==0){++p;break;}} else if(*p=='"'){++p; while(p<end&&*p!='"'){if(*p=='\\'){++p; if(p<end)++p;} else ++p;} if(p<end)++p;} else ++p;} }
                    else if (c == '[') { ++p; int depth=1; while(p<end&&depth){if(*p=='[')++depth; else if(*p==']'){--depth; if(depth==0){++p;break;}} else if(*p=='"'){++p; while(p<end&&*p!='"'){if(*p=='\\'){++p; if(p<end)++p;} else ++p;} if(p<end)++p;} else ++p;} }
                    else { while (p < end && *p >= '0' && *p <= '9') ++p; if (p < end && (*p=='-'||*p=='+'||*p=='.'||*p=='e'||*p=='E')) ++p; }
                }
            }
        }
    }
    return p;
}

int main(int argc, char** argv) {
    _setmode(_fileno(stdout), O_BINARY);
    if (argc < 2) return 1;
    FILE* f = std::fopen(argv[1], "rb");
    if (!f) return 1;
    std::fseek(f, 0, SEEK_END);
    long sz = std::ftell(f);
    std::fseek(f, 0, SEEK_SET);
    std::vector<char> buf((size_t)sz + 1);
    size_t rd = std::fread(buf.data(), 1, (size_t)sz, f);
    std::fclose(f);
    if (rd != (size_t)sz) return 1;
    buf[sz] = '\0';
    const char* end = buf.data() + sz;

    const char* nl = (const char*)std::memchr(buf.data(), '\n', (size_t)sz);
    const char* line1end = nl ? nl : end;

    std::vector<Rate> rates;
    parseRates(buf.data(), line1end, rates);

    std::unordered_map<std::string, i64> accounts;
    accounts.reserve(1 << 16);
    struct Ch { i64 count = 0; i64 net = 0; };
    std::unordered_map<std::string, Ch> channels;
    channels.reserve(1 << 10);

    i64 counted = 0;
    i64 net = 0;

    const char* line = line1end < end ? line1end + 1 : end;
    while (line < end) {
        const char* n = (const char*)std::memchr(line, '\n', (size_t)(end - line));
        const char* lineEnd = n ? n : end;
        Parser p(line, lineEnd);
        if (p.cur() != '{') {
            line = lineEnd < end ? lineEnd + 1 : end;
            continue;
        }
        p.parseTxObject();

        if (!p.type_.empty() && p.type_ != "void" && !p.testTag_) {
            i64 rate = 0;
            for (auto& r : rates) {
                if (r.name == p.currency_) { rate = r.value; break; }
            }
            i64 usd = (p.hundredths_ * rate) / 1000000;
            i64 val = (p.type_ == "credit" || p.type_ == "refund") ? usd : -usd;
            ++counted;
            net += val;
            Ch& c = channels[p.channel_];
            c.count += 1;
            c.net += val;
            accounts[p.account_] += val;
        }

        line = lineEnd < end ? lineEnd + 1 : end;
    }

    std::string out;
    out += "counted ";
    appendInt(out, counted); out.push_back('\n');
    out += "net ";
    appendInt(out, net); out.push_back('\n');

    struct ChE { std::string name; i64 count; i64 net; };
    std::vector<ChE> chs;
    chs.reserve(channels.size());
    for (auto& kv : channels) chs.push_back({kv.first, kv.second.count, kv.second.net});
    std::sort(chs.begin(), chs.end(), [](const ChE& a, const ChE& b) { return a.name < b.name; });
    for (auto& c : chs) {
        out += "channel ";
        out += c.name;
        out.push_back(' ');
        appendInt(out, c.count);
        out.push_back(' ');
        appendInt(out, c.net);
        out.push_back('\n');
    }

    struct AcE { std::string id; i64 net; };
    std::vector<AcE> acs;
    acs.reserve(accounts.size());
    for (auto& kv : accounts) acs.push_back({kv.first, kv.second});
    std::sort(acs.begin(), acs.end(), [](const AcE& a, const AcE& b) {
        if (a.net != b.net) return a.net > b.net;
        return a.id < b.id;
    });
    size_t m = acs.size() < 10 ? acs.size() : 10;
    for (size_t i = 0; i < m; ++i) {
        out += "account ";
        out += acs[i].id;
        out.push_back(' ');
        appendInt(out, acs[i].net);
        out.push_back('\n');
    }

    std::fwrite(out.data(), 1, out.size(), stdout);
    return 0;
}
