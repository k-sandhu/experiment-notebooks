#include <cstdio>
#include <cstdlib>
#include <io.h>
#include <fcntl.h>
#include <cstring>
#include <cstdint>
#include <string>
#include <string_view>
#include <vector>
#include <unordered_map>
#include <algorithm>
#include <deque>

typedef long long i64;

// ---------------------------------------------------------------- input/parser
static const char* P;
static const char* E;

// Result of the last scanString().
static const char* sBeg;
static size_t sLen;
static bool sEsc;
static std::string uScratch;   // decoded text, only built when escapes are present

static inline void skipWs() {
    while (P < E) {
        char c = *P;
        if (c == ' ' || c == '\t' || c == '\r' || c == '\n') ++P;
        else break;
    }
}

// P is at '"'.  Record the raw contents, skipping over escape sequences.
static inline void scanString() {
    ++P;
    sBeg = P;
    bool esc = false;
    while (*P != '"') {
        if (*P == '\\') {
            esc = true;
            ++P;
            if (*P == 'u') P += 5; else ++P;
        } else {
            ++P;
        }
    }
    sLen = (size_t)(P - sBeg);
    ++P;
    sEsc = esc;
}

static inline void skipString() {
    ++P;
    while (*P != '"') {
        if (*P == '\\') {
            ++P;
            if (*P == 'u') P += 5; else ++P;
        } else {
            ++P;
        }
    }
    ++P;
}

static inline unsigned hex4(const char* q) {
    unsigned v = 0;
    for (int i = 0; i < 4; ++i) {
        char c = q[i];
        unsigned d;
        if (c >= '0' && c <= '9') d = (unsigned)(c - '0');
        else if (c >= 'a' && c <= 'f') d = (unsigned)(c - 'a' + 10);
        else d = (unsigned)(c - 'A' + 10);
        v = (v << 4) | d;
    }
    return v;
}

static void unescape() {
    uScratch.clear();
    const char* q = sBeg;
    const char* end = sBeg + sLen;
    while (q < end) {
        char c = *q++;
        if (c != '\\') { uScratch.push_back(c); continue; }
        char e = *q++;
        switch (e) {
            case '"':  uScratch.push_back('"');  break;
            case '\\': uScratch.push_back('\\'); break;
            case '/':  uScratch.push_back('/');  break;
            case 'b':  uScratch.push_back('\b'); break;
            case 'f':  uScratch.push_back('\f'); break;
            case 'n':  uScratch.push_back('\n'); break;
            case 'r':  uScratch.push_back('\r'); break;
            case 't':  uScratch.push_back('\t'); break;
            case 'u': {
                unsigned cp = hex4(q); q += 4;
                if (cp >= 0xD800 && cp <= 0xDBFF && q + 6 <= end && q[0] == '\\' && q[1] == 'u') {
                    unsigned lo = hex4(q + 2);
                    if (lo >= 0xDC00 && lo <= 0xDFFF) {
                        cp = 0x10000u + ((cp - 0xD800u) << 10) + (lo - 0xDC00u);
                        q += 6;
                    }
                }
                if (cp < 0x80) {
                    uScratch.push_back((char)cp);
                } else if (cp < 0x800) {
                    uScratch.push_back((char)(0xC0 | (cp >> 6)));
                    uScratch.push_back((char)(0x80 | (cp & 0x3F)));
                } else if (cp < 0x10000) {
                    uScratch.push_back((char)(0xE0 | (cp >> 12)));
                    uScratch.push_back((char)(0x80 | ((cp >> 6) & 0x3F)));
                    uScratch.push_back((char)(0x80 | (cp & 0x3F)));
                } else {
                    uScratch.push_back((char)(0xF0 | (cp >> 18)));
                    uScratch.push_back((char)(0x80 | ((cp >> 12) & 0x3F)));
                    uScratch.push_back((char)(0x80 | ((cp >> 6) & 0x3F)));
                    uScratch.push_back((char)(0x80 | (cp & 0x3F)));
                }
                break;
            }
            default: uScratch.push_back(e); break;
        }
    }
}

static inline std::string_view sView() {
    if (!sEsc) return std::string_view(sBeg, sLen);
    unescape();
    return std::string_view(uScratch.data(), uScratch.size());
}

static inline bool sEquals(const char* lit, size_t n) {
    if (!sEsc) return sLen == n && std::memcmp(sBeg, lit, n) == 0;
    unescape();
    return uScratch.size() == n && std::memcmp(uScratch.data(), lit, n) == 0;
}

static inline bool keyIs(std::string_view k, const char* lit, size_t n) {
    return k.size() == n && std::memcmp(k.data(), lit, n) == 0;
}

// Skip one arbitrary JSON value (depth scan; input is valid JSON).
static void skipValue() {
    skipWs();
    char c = *P;
    if (c == '"') { skipString(); return; }
    if (c == '{' || c == '[') {
        int depth = 0;
        while (true) {
            char d = *P;
            if (d == '"') { skipString(); continue; }
            if (d == '{' || d == '[') { ++depth; ++P; }
            else if (d == '}' || d == ']') { ++P; if (--depth == 0) return; }
            else ++P;
        }
    }
    while (P < E) {
        char d = *P;
        if (d == ',' || d == '}' || d == ']' || d == ' ' || d == '\t' || d == '\r' || d == '\n') break;
        ++P;
    }
}

// ---------------------------------------------------------------- accounting
struct Rate { std::string name; i64 rate; };
static std::vector<Rate> rates;

struct Channel { std::string name; i64 cnt; i64 net; };
static std::vector<Channel> channels;

struct Account {
    std::string name;
    i64 sum;
    i64 cnt;
};
static std::vector<Account> accounts;
static std::unordered_map<std::string_view, int> accountIndex;
static std::deque<std::string> ownedAccountKeys;

static int internAccount() {
    std::string_view v;
    if (sEsc) {
        unescape();
        v = std::string_view(uScratch);
    } else {
        v = std::string_view(sBeg, sLen);
    }
    auto it = accountIndex.find(v);
    if (it != accountIndex.end()) return it->second;
    // Copy escaped keys to stable storage; raw keys point into the (never moved) input buffer.
    std::string_view storedKey;
    if (sEsc) {
        ownedAccountKeys.emplace_back(v);
        storedKey = std::string_view(ownedAccountKeys.back());
    } else {
        storedKey = v;
    }
    int idx = (int)accounts.size();
    accounts.push_back(Account{std::string(v), 0, 0});
    accountIndex.emplace(storedKey, idx);
    return idx;
}

static int internChannel() {
    std::string_view v = sView();
    for (size_t i = 0; i < channels.size(); ++i) {
        const std::string& n = channels[i].name;
        if (n.size() == v.size() && std::memcmp(n.data(), v.data(), v.size()) == 0) return (int)i;
    }
    channels.push_back(Channel{std::string(v), 0, 0});
    return (int)channels.size() - 1;
}

static i64 lookupRate(std::string_view v) {
    for (size_t i = 0; i < rates.size(); ++i) {
        const std::string& n = rates[i].name;
        if (n.size() == v.size() && std::memcmp(n.data(), v.data(), v.size()) == 0) return rates[i].rate;
    }
    return 0;
}

static i64 parseAmount(std::string_view v) {
    i64 whole = 0;
    size_t i = 0, n = v.size();
    while (i < n && v[i] >= '0' && v[i] <= '9') {
        whole = whole * 10 + (v[i] - '0');
        ++i;
    }
    int f1 = 0, f2 = 0;
    if (i < n && v[i] == '.') {
        ++i;
        if (i < n) { f1 = v[i] - '0'; ++i; }
        if (i < n) { f2 = v[i] - '0'; ++i; }
    }
    return whole * 100 + f1 * 10 + f2;
}

// ---------------------------------------------------------------- transaction
static i64 totalCount;
static i64 totalNet;

static void parseTagsAndTest(bool& hasTest) {
    // P at '['
    ++P; skipWs();
    if (*P == ']') { ++P; return; }
    while (true) {
        skipWs();
        if (*P == '"') {
            scanString();
            if (!hasTest && sEquals("test", 4)) hasTest = true;
        } else {
            skipValue();
        }
        skipWs();
        if (*P == ',') { ++P; continue; }
        ++P;  // ']'
        return;
    }
}

static void parseMeta(int& chIdx) {
    // P at '{'
    ++P; skipWs();
    if (*P == '}') { ++P; return; }
    while (true) {
        skipWs();
        scanString();
        std::string_view k = sView();
        skipWs();
        ++P;  // ':'
        skipWs();
        if (keyIs(k, "channel", 7)) {
            scanString();
            chIdx = internChannel();
        } else {
            skipValue();
        }
        skipWs();
        if (*P == ',') { ++P; continue; }
        ++P;  // '}'
        return;
    }
}

static void parseTransaction() {
    int acctIdx = -1;
    int chIdx = -1;
    int sign = 1;          // +1 credit/refund, -1 debit, 0 = void/skip
    bool hasTest = false;
    i64 hundredths = 0;
    i64 rate = 0;

    ++P;  // '{'
    skipWs();
    if (*P == '}') { ++P; return; }
    while (true) {
        skipWs();
        scanString();
        std::string_view k = sView();
        skipWs();
        ++P;  // ':'
        skipWs();

        switch (k.size() ? k[0] : 0) {
            case 'a':
                if (keyIs(k, "account", 7)) { scanString(); acctIdx = internAccount(); }
                else if (keyIs(k, "amount", 6)) { scanString(); hundredths = parseAmount(sView()); }
                else skipValue();
                break;
            case 't':
                if (keyIs(k, "type", 4)) {
                    scanString();
                    if (sEquals("void", 4)) sign = 0;
                    else if (sEquals("debit", 5)) sign = -1;
                    else sign = 1;
                } else if (keyIs(k, "tags", 4)) {
                    parseTagsAndTest(hasTest);
                } else {
                    skipValue();
                }
                break;
            case 'm':
                if (keyIs(k, "meta", 4)) parseMeta(chIdx);
                else skipValue();
                break;
            case 'c':
                if (keyIs(k, "currency", 8)) { scanString(); rate = lookupRate(sView()); }
                else skipValue();
                break;
            case 'i':
                skipValue();
                break;
            default:
                if (keyIs(k, "amount", 6)) { scanString(); hundredths = parseAmount(sView()); }
                else skipValue();
                break;
        }

        skipWs();
        if (*P == ',') { ++P; continue; }
        ++P;  // '}'
        break;
    }

    if (sign == 0 || hasTest) return;

    i64 usd = (hundredths * rate) / 1000000LL;
    i64 val = (sign > 0) ? usd : -usd;

    ++totalCount;
    totalNet += val;

    if (acctIdx >= 0) {
        accounts[acctIdx].sum += val;
        accounts[acctIdx].cnt += 1;
    }
    if (chIdx >= 0) {
        channels[chIdx].cnt += 1;
        channels[chIdx].net += val;
    }
}

// ---------------------------------------------------------------- output
struct ChCmp {
    bool operator()(const Channel& a, const Channel& b) const { return a.name < b.name; }
};

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    _setmode(_fileno(stdout), _O_BINARY);

    FILE* f = std::fopen(argv[1], "rb");
    if (!f) return 1;
    _fseeki64(f, 0, SEEK_END);
    i64 sz = _ftelli64(f);
    _fseeki64(f, 0, SEEK_SET);
    std::vector<char> data((size_t)sz + 1);
    size_t got = std::fread(data.data(), 1, (size_t)sz, f);
    std::fclose(f);
    data[got] = '\0';

    P = data.data();
    E = data.data() + got;

    accountIndex.reserve(1 << 16);

    // First line: {"rates": { "USD": 1000000, ... }}
    skipWs();
    ++P;  // outer '{'
    skipWs();
    if (*P != '}') {
        while (true) {
            skipWs();
            scanString();
            std::string_view k = sView();
            skipWs();
            ++P;  // ':'
            skipWs();
            if (keyIs(k, "rates", 5) && *P == '{') {
                ++P;  // inner '{'
                skipWs();
                if (*P != '}') {
                    while (true) {
                        skipWs();
                        scanString();
                        std::string_view cur = sView();
                        skipWs();
                        ++P;  // ':'
                        skipWs();
                        bool neg = false;
                        if (*P == '-') { neg = true; ++P; }
                        i64 v = 0;
                        while (*P >= '0' && *P <= '9') { v = v * 10 + (*P - '0'); ++P; }
                        if (neg) v = -v;
                        rates.push_back(Rate{std::string(cur), v});
                        skipWs();
                        if (*P == ',') { ++P; continue; }
                        ++P;  // inner '}'
                        break;
                    }
                } else {
                    ++P;
                }
            } else {
                skipValue();
            }
            skipWs();
            if (*P == ',') { ++P; continue; }
            ++P;  // outer '}'
            break;
        }
    } else {
        ++P;
    }

    // Remaining objects: transactions.
    while (true) {
        skipWs();
        if (P >= E) break;
        if (*P != '{') { ++P; continue; }
        parseTransaction();
    }

    std::sort(channels.begin(), channels.end(), ChCmp());

    // Best ten accounts by net desc, then id asc.
    int best[10];
    int bn = 0;
    for (int i = 0; i < (int)accounts.size(); ++i) {
        if (accounts[i].cnt == 0) continue;
        i64 s = accounts[i].sum;
        const std::string& nm = accounts[i].name;
        int pos = bn;
        while (pos > 0) {
            const Account& o = accounts[best[pos - 1]];
            bool better;
            if (s != o.sum) better = s > o.sum;
            else better = nm < o.name;
            if (!better) break;
            --pos;
        }
        if (pos >= 10) continue;
        if (bn < 10) ++bn;
        for (int j = bn - 1; j > pos; --j) best[j] = best[j - 1];
        best[pos] = i;
    }

    std::string out;
    out.reserve(4096);
    out += "counted ";
    out += std::to_string(totalCount);
    out += "\nnet ";
    out += std::to_string(totalNet);
    out += '\n';
    for (const Channel& c : channels) {
        if (c.cnt == 0) continue;
        out += "channel ";
        out += c.name;
        out += ' ';
        out += std::to_string(c.cnt);
        out += ' ';
        out += std::to_string(c.net);
        out += '\n';
    }
    for (int i = 0; i < bn; ++i) {
        const Account& a = accounts[best[i]];
        out += "account ";
        out += a.name;
        out += ' ';
        out += std::to_string(a.sum);
        out += '\n';
    }
    std::fwrite(out.data(), 1, out.size(), stdout);
    return 0;
}
