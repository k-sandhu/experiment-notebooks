#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cstdint>
#include <string>
#include <string_view>
#include <vector>
#include <deque>
#include <algorithm>
#include <unordered_map>
#include <filesystem>
#include <io.h>
#include <fcntl.h>

static const char* g_p;
static const char* g_end;
static std::deque<std::string> g_pool; // stable storage for decoded strings

struct SVHash {
    size_t operator()(std::string_view s) const noexcept {
        // FNV-1a
        size_t h = 1469598103934665603ULL;
        for (unsigned char c : s) { h ^= c; h *= 1099511628211ULL; }
        h ^= h >> 33; h *= 0xff51afd7ed558ccdULL; h ^= h >> 33;
        return h;
    }
};

static inline void skipWs() {
    while (g_p < g_end) {
        char c = *g_p;
        if (c==' '||c=='\t'||c=='\r'||c=='\n') ++g_p; else break;
    }
}

// Decode a JSON string body [s,e) (contents, escapes present) into pool, return view.
static std::string_view decodeSpan(const char* s, const char* e) {
    std::string out;
    out.reserve((size_t)(e-s));
    const char* p = s;
    auto hex4 = [&](const char* q)->uint32_t{
        uint32_t v=0;
        for(int i=0;i<4 && q+i<e;i++){ char c=q[i]; v<<=4; if(c>='0'&&c<='9')v|=c-'0'; else if(c>='a'&&c<='f')v|=c-'a'+10; else if(c>='A'&&c<='F')v|=c-'A'+10; }
        return v;
    };
    auto emitUtf8 = [&](uint32_t cp){
        if (cp < 0x80) out.push_back((char)cp);
        else if (cp < 0x800) { out.push_back((char)(0xC0|(cp>>6))); out.push_back((char)(0x80|(cp&63))); }
        else if (cp < 0x10000) { out.push_back((char)(0xE0|(cp>>12))); out.push_back((char)(0x80|((cp>>6)&63))); out.push_back((char)(0x80|(cp&63))); }
        else { out.push_back((char)(0xF0|(cp>>18))); out.push_back((char)(0x80|((cp>>12)&63))); out.push_back((char)(0x80|((cp>>6)&63))); out.push_back((char)(0x80|(cp&63))); }
    };
    while (p < e) {
        char c = *p;
        if (c != '\\') { out.push_back(c); ++p; continue; }
        ++p; if (p>=e) break;
        char esc = *p++;
        switch (esc) {
            case '"': out.push_back('"'); break;
            case '\\': out.push_back('\\'); break;
            case '/': out.push_back('/'); break;
            case 'b': out.push_back('\b'); break;
            case 'f': out.push_back('\f'); break;
            case 'n': out.push_back('\n'); break;
            case 'r': out.push_back('\r'); break;
            case 't': out.push_back('\t'); break;
            case 'u': {
                uint32_t cp = hex4(p); p += 4;
                if (cp >= 0xD800 && cp <= 0xDBFF && p+1 < e && p[0]=='\\' && p[1]=='u') {
                    uint32_t lo = hex4(p+2);
                    if (lo >= 0xDC00 && lo <= 0xDFFF) { p += 6; cp = 0x10000 + ((cp-0xD800)<<10) + (lo-0xDC00); }
                }
                emitUtf8(cp);
                break;
            }
            default: out.push_back(esc); break;
        }
    }
    g_pool.push_back(std::move(out));
    const std::string& stored = g_pool.back();
    return std::string_view(stored.data(), stored.size());
}

// Parse string at g_p (at '"'), return view, advance past closing quote.
static std::string_view parseString() {
    ++g_p; // opening quote
    const char* start = g_p;
    const char* p = g_p;
    bool esc = false;
    while (p < g_end) {
        char c = *p;
        if (c == '"') break;
        if (c == '\\') { esc = true; p += 2; continue; }
        ++p;
    }
    const char* send = p;
    g_p = (p < g_end) ? p + 1 : p;
    if (!esc) return std::string_view(start, (size_t)(send-start));
    return decodeSpan(start, send);
}

static void skipString() {
    ++g_p;
    while (g_p < g_end) {
        char c = *g_p;
        if (c == '"') { ++g_p; return; }
        if (c == '\\') { g_p += 2; continue; }
        ++g_p;
    }
}

static void skipValue() {
    skipWs();
    if (g_p >= g_end) return;
    char c = *g_p;
    if (c == '"') { skipString(); return; }
    if (c == '{' || c == '[') {
        int depth = 0;
        while (g_p < g_end) {
            char ch = *g_p;
            if (ch == '"') { skipString(); continue; }
            if (ch == '{' || ch == '[') { ++depth; ++g_p; continue; }
            if (ch == '}' || ch == ']') { ++g_p; if (--depth == 0) return; continue; }
            ++g_p;
        }
        return;
    }
    // number / literal
    while (g_p < g_end) {
        char ch = *g_p;
        if (ch==','||ch=='}'||ch==']'||ch==' '||ch=='\t'||ch=='\r'||ch=='\n') break;
        ++g_p;
    }
}

static bool eqLit(std::string_view s, const char* lit, size_t n) {
    return s.size()==n && std::memcmp(s.data(), lit, n)==0;
}

struct Rate { std::string_view code; int64_t rate; };
struct Chan { std::string_view name; int64_t count; int64_t net; };
static std::vector<Rate> g_rates;
static std::vector<Chan> g_chans;
static std::unordered_map<std::string_view, int64_t, SVHash> g_accounts;

static inline int64_t lookupRate(std::string_view code) {
    for (auto &r : g_rates) if (r.code == code) return r.rate;
    return 0;
}
static inline Chan* findChan(std::string_view name) {
    for (auto &c : g_chans) if (c.name == name) return &c;
    g_chans.push_back({name, 0, 0});
    return &g_chans.back();
}

static int64_t parseIntValue() {
    skipWs();
    bool neg = false;
    if (g_p < g_end && *g_p=='-') { neg=true; ++g_p; }
    int64_t v = 0;
    while (g_p < g_end && *g_p>='0' && *g_p<='9') { v = v*10 + (*g_p-'0'); ++g_p; }
    // ignore fraction/exponent (not expected for rates)
    while (g_p < g_end) { char c=*g_p; if ((c>='0'&&c<='9')||c=='.'||c=='e'||c=='E'||c=='+'||c=='-') ++g_p; else break; }
    return neg ? -v : v;
}

static int64_t parseAmountHundredths(std::string_view s) {
    int64_t v = 0;
    size_t i = 0, n = s.size();
    while (i < n && s[i]>='0' && s[i]<='9') { v = v*10 + (s[i]-'0'); ++i; }
    v *= 100;
    if (i < n && s[i]=='.') {
        ++i;
        int frac = 0, digits = 0;
        while (i < n && s[i]>='0' && s[i]<='9' && digits<2) { frac = frac*10 + (s[i]-'0'); ++i; ++digits; }
        if (digits==1) frac *= 10;
        v += frac;
    }
    return v;
}

int main(int argc, char** argv) {
    _setmode(_fileno(stdout), _O_BINARY);
    if (argc < 2) return 1;
    std::error_code ec;
    auto fsize = std::filesystem::file_size(argv[1], ec);
    if (ec) return 1;
    std::vector<char> buf((size_t)fsize);
    FILE* f = std::fopen(argv[1], "rb");
    if (!f) return 1;
    size_t got = buf.empty()?0:std::fread(buf.data(), 1, buf.size(), f);
    std::fclose(f);
    buf.resize(got);
    if (buf.empty()) { std::printf("counted 0\nnet 0\n"); return 0; }
    g_p = buf.data(); g_end = buf.data() + buf.size();
    g_accounts.reserve(1<<20);
    g_accounts.max_load_factor(0.7f);

    // ---- first line: rates ----
    skipWs();
    if (g_p < g_end && *g_p=='{') {
        ++g_p;
        while (g_p < g_end) {
            skipWs();
            if (g_p>=g_end) break;
            if (*g_p=='}') { ++g_p; break; }
            if (*g_p==',') { ++g_p; continue; }
            auto key = parseString();
            skipWs(); if (g_p<g_end && *g_p==':') ++g_p;
            if (eqLit(key,"rates",5)) {
                skipWs();
                if (g_p<g_end && *g_p=='{') {
                    ++g_p;
                    while (g_p < g_end) {
                        skipWs();
                        if (g_p>=g_end) break;
                        if (*g_p=='}') { ++g_p; break; }
                        if (*g_p==',') { ++g_p; continue; }
                        auto code = parseString();
                        skipWs(); if (g_p<g_end && *g_p==':') ++g_p;
                        int64_t rate = parseIntValue();
                        g_rates.push_back({code, rate});
                    }
                } else skipValue();
            } else skipValue();
        }
    }

    int64_t counted = 0, totalNet = 0;

    // ---- transactions ----
    while (true) {
        // advance to next '{' at line start (skip newlines/ws)
        while (g_p < g_end && (*g_p=='\n'||*g_p=='\r'||*g_p==' '||*g_p=='\t')) ++g_p;
        if (g_p >= g_end) break;
        if (*g_p != '{') { // skip line defensively
            while (g_p < g_end && *g_p!='\n') ++g_p;
            continue;
        }
        ++g_p; // '{'
        std::string_view account{}, channel{};
        bool hasAccount=false, hasChannel=false;
        int64_t hundredths = 0, rate = 1000000;
        int sign = 1;
        bool isVoid = false, skipTxn = false;

        while (g_p < g_end) {
            skipWs();
            if (g_p>=g_end) break;
            char c = *g_p;
            if (c=='}') { ++g_p; break; }
            if (c==',') { ++g_p; continue; }
            if (c=='\n') { ++g_p; break; } // shouldn't happen
            auto key = parseString();
            skipWs(); if (g_p<g_end && *g_p==':') ++g_p; skipWs();
            if (key.size()==7 && eqLit(key,"account",7)) {
                if (g_p<g_end && *g_p=='"') { account = parseString(); hasAccount=true; } else skipValue();
            } else if (key.size()==4 && eqLit(key,"type",4)) {
                if (g_p<g_end && *g_p=='"') {
                    auto v = parseString();
                    if (eqLit(v,"void",4)) { isVoid=true; skipTxn=true; }
                    else if (eqLit(v,"debit",5)) sign = -1;
                    else sign = 1; // credit, refund
                } else skipValue();
            } else if (key.size()==6 && eqLit(key,"amount",6)) {
                if (g_p<g_end && *g_p=='"') { auto v = parseString(); hundredths = parseAmountHundredths(v); } else skipValue();
            } else if (key.size()==8 && eqLit(key,"currency",8)) {
                if (g_p<g_end && *g_p=='"') { auto v = parseString(); rate = lookupRate(v); } else skipValue();
            } else if (key.size()==4 && eqLit(key,"tags",4)) {
                // parse array
                skipWs();
                if (g_p<g_end && *g_p=='[') {
                    ++g_p;
                    while (g_p < g_end) {
                        skipWs();
                        if (g_p>=g_end) break;
                        if (*g_p==']') { ++g_p; break; }
                        if (*g_p==',') { ++g_p; continue; }
                        if (*g_p=='"') { auto v = parseString(); if (eqLit(v,"test",4)) skipTxn=true; }
                        else skipValue();
                        if (skipTxn) break;
                    }
                } else skipValue();
            } else if (key.size()==4 && eqLit(key,"meta",4)) {
                skipWs();
                if (g_p<g_end && *g_p=='{') {
                    ++g_p;
                    while (g_p < g_end) {
                        skipWs();
                        if (g_p>=g_end) break;
                        if (*g_p=='}') { ++g_p; break; }
                        if (*g_p==',') { ++g_p; continue; }
                        auto mk = parseString();
                        skipWs(); if (g_p<g_end && *g_p==':') ++g_p; skipWs();
                        if (eqLit(mk,"channel",7)) {
                            if (g_p<g_end && *g_p=='"') { channel = parseString(); hasChannel=true; } else skipValue();
                        } else skipValue();
                    }
                } else skipValue();
            } else {
                skipValue();
            }
            if (skipTxn) {
                // skip to end of line
                const char* nl = (const char*)std::memchr(g_p, '\n', (size_t)(g_end-g_p));
                g_p = nl ? nl+1 : g_end;
                break;
            }
        }
        if (skipTxn || isVoid) continue;
        int64_t usd = (hundredths * rate) / 1000000;
        int64_t signedVal = sign * usd;
        ++counted; totalNet += signedVal;
        if (hasChannel) { Chan* ch = findChan(channel); ch->count++; ch->net += signedVal; }
        if (hasAccount) {
            auto it = g_accounts.find(account);
            if (it == g_accounts.end()) g_accounts.emplace(account, signedVal);
            else it->second += signedVal;
        }
    }

    std::sort(g_chans.begin(), g_chans.end(), [](const Chan& a, const Chan& b){ return a.name < b.name; });
    std::vector<std::pair<std::string_view,int64_t>> acc(g_accounts.begin(), g_accounts.end());
    // Actually unordered_map iteration gives pair<const string_view, int64>
    // Rebuild correctly:
    // (acc already constructed from iterators of pair<const...> converts fine)
    std::sort(acc.begin(), acc.end(), [](auto& a, auto& b){
        if (a.second != b.second) return a.second > b.second;
        return a.first < b.first;
    });
    size_t nTop = acc.size() < 10 ? acc.size() : 10;

    std::string out;
    out.reserve(4096 + g_chans.size()*64 + nTop*64);
    char tmp[128];
    int len = std::snprintf(tmp, sizeof tmp, "counted %lld\nnet %lld\n", (long long)counted, (long long)totalNet);
    out.append(tmp, len);
    for (auto &c : g_chans) {
        len = std::snprintf(tmp, sizeof tmp, "channel ");
        out.append(tmp, len);
        out.append(c.name.data(), c.name.size());
        len = std::snprintf(tmp, sizeof tmp, " %lld %lld\n", (long long)c.count, (long long)c.net);
        out.append(tmp, len);
    }
    for (size_t i=0;i<nTop;i++) {
        out.append("account ");
        out.append(acc[i].first.data(), acc[i].first.size());
        len = std::snprintf(tmp, sizeof tmp, " %lld\n", (long long)acc[i].second);
        out.append(tmp, len);
    }
    std::fwrite(out.data(), 1, out.size(), stdout);
    return 0;
}
