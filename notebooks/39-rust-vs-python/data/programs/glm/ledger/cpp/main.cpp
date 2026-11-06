// Ledger: sum JSON-lines transactions with exact integer currency conversion.
// Single pass over the raw bytes; we only extract the fields we need.
#include <cstdio>
#include <cstdint>
#include <fcntl.h>
#include <io.h>
#include <cstring>
#include <cstdlib>
#include <charconv>
#include <string>
#include <string_view>
#include <unordered_map>
#include <vector>
#include <algorithm>

using namespace std;

namespace {

constexpr uint64_t kMicro = 1000000;

// Aggregates for a channel: number of counted transactions and their net sum.
struct ChannelAgg {
    int64_t count = 0;
    int64_t net = 0;
};

// Keys must stay alive for the whole run: string_views point into the file
// buffer (unescaped keys are copied into a persistent arena when needed).
unordered_map<string_view, ChannelAgg> g_channels;
unordered_map<string_view, int64_t> g_accounts;
unordered_map<string_view, int64_t> g_rates;
constexpr size_t kChunk = 4096;
string g_arena;    // backing store for decoded (escaped) keys
size_t g_arenaOff = 0;

const int64_t* findRate(string_view cur) {
    auto it = g_rates.find(cur);
    return it == g_rates.end() ? nullptr : &it->second;
}

ChannelAgg* findChannel(string_view name) {
    auto it = g_channels.find(name);
    return it == g_channels.end() ? nullptr : &it->second;
}

int64_t* findAccount(string_view id) {
    auto it = g_accounts.find(id);
    return it == g_accounts.end() ? nullptr : &it->second;
}

// Copy a decoded key into persistent storage and return a view of it.
// Uses fixed blocks so nothing ever moves (map keys hold views into this).
string_view intern(string_view key) {
    if (g_arena.empty() || g_arena.size() - g_arenaOff < key.size()) {
        g_arena.resize(g_arena.size() + (key.size() > kChunk ? key.size() : kChunk));
    }
    char* dst = g_arena.data() + g_arenaOff;
    memcpy(dst, key.data(), key.size());
    g_arenaOff += key.size();
    return string_view(dst, key.size());
}

vector<char> g_scratch; // reused scratch for decoded strings

string_view decodeString(const char* s, size_t len) {
    g_scratch.clear();
    g_scratch.reserve(len);
    for (size_t i = 0; i < len; ++i) {
        char c = s[i];
        if (c != '\\') { g_scratch.push_back(c); continue; }
        char e = s[++i];
        switch (e) {
            case '"': g_scratch.push_back('"'); break;
            case '\\': g_scratch.push_back('\\'); break;
            case '/': g_scratch.push_back('/'); break;
            case 'b': g_scratch.push_back('\b'); break;
            case 'f': g_scratch.push_back('\f'); break;
            case 'n': g_scratch.push_back('\n'); break;
            case 'r': g_scratch.push_back('\r'); break;
            case 't': g_scratch.push_back('\t'); break;
            case 'u': {
                uint32_t cp = 0;
                for (int k = 1; k <= 4; ++k) {
                    char h = s[i + k];
                    cp <<= 4;
                    if (h >= '0' && h <= '9') cp |= h - '0';
                    else if (h >= 'a' && h <= 'f') cp |= h - 'a' + 10;
                    else if (h >= 'A' && h <= 'F') cp |= h - 'A' + 10;
                }
                i += 4;
                if (cp >= 0xD800 && cp <= 0xDBFF && i + 7 <= len &&
                    s[i + 1] == '\\' && s[i + 2] == 'u') {
                    uint32_t lo = 0;
                    for (int k = 3; k <= 6; ++k) {
                        char h = s[i + k];
                        lo <<= 4;
                        if (h >= '0' && h <= '9') lo |= h - '0';
                        else if (h >= 'a' && h <= 'f') lo |= h - 'a' + 10;
                        else if (h >= 'A' && h <= 'F') lo |= h - 'A' + 10;
                    }
                    if (lo >= 0xDC00 && lo <= 0xDFFF) {
                        cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
                        i += 6;
                    }
                }
                // UTF-8 encode
                if (cp < 0x80) g_scratch.push_back(char(cp));
                else if (cp < 0x800) {
                    g_scratch.push_back(char(0xC0 | (cp >> 6)));
                    g_scratch.push_back(char(0x80 | (cp & 0x3F)));
                } else if (cp < 0x10000) {
                    g_scratch.push_back(char(0xE0 | (cp >> 12)));
                    g_scratch.push_back(char(0x80 | ((cp >> 6) & 0x3F)));
                    g_scratch.push_back(char(0x80 | (cp & 0x3F)));
                } else {
                    g_scratch.push_back(char(0xF0 | (cp >> 18)));
                    g_scratch.push_back(char(0x80 | ((cp >> 12) & 0x3F)));
                    g_scratch.push_back(char(0x80 | ((cp >> 6) & 0x3F)));
                    g_scratch.push_back(char(0x80 | (cp & 0x3F)));
                }
                break;
            }
            default: g_scratch.push_back(e); break;
        }
    }
    return string_view(g_scratch.data(), g_scratch.size());
}

struct StrVal {
    const char* p;
    uint32_t len;
    bool escaped;
};

inline bool isWs(char c) {
    return c == ' ' || c == '\t' || c == '\r' || c == '\n';
}

// Parses a JSON string starting at '"'; returns raw slice + escape flag.
StrVal parseString(const char* p) {
    const char* start = ++p; // skip opening quote
    bool esc = false;
    for (;;) {
        char c = *p;
        if (c == '"') return {start, uint32_t(p - start), esc};
        if (c == '\\') {
            esc = true;
            ++p;
            if (*p == 'u') p += 4;
        }
        ++p;
    }
}

// Skips any JSON value (number, string, true/false/null, object, array).
const char* skipValue(const char* p) {
    if (*p == '"') return parseString(p).p + parseString(p).len + 1;
    if (*p == '{' || *p == '[') {
        int depth = 0;
        for (;;) {
            char c = *p;
            if (c == '"') {
                p = parseString(p).p + parseString(p).len + 1;
                continue;
            }
            if (c == '{' || c == '[') ++depth;
            else if (c == '}' || c == ']') {
                if (--depth == 0) return p + 1;
            }
            ++p;
        }
    }
    while (*p != ',' && *p != '}' && *p != ']') ++p;
    return p;
}

// Compares a (possibly escaped) string value against a plain ASCII literal.
bool strEquals(const StrVal& sv, string_view lit) {
    if (!sv.escaped) return sv.len == lit.size() && memcmp(sv.p, lit.data(), lit.size()) == 0;
    return decodeString(sv.p, sv.len) == lit;
}

inline const char* skipWs(const char* p) {
    while (isWs(*p)) ++p;
    return p;
}

// Reads one "key": value pair key name as a raw slice starting at '"'.
StrVal parseKey(const char* p) { return parseString(p); }

int64_t parseUnsignedAmount(const StrVal& sv) {
    // digits, optionally '.' plus one or two digits -> integer hundredths
    const char* p = sv.p;
    const char* end = sv.p + sv.len;
    uint64_t whole = 0;
    while (p < end && *p >= '0' && *p <= '9') whole = whole * 10 + (*p++ - '0');
    uint32_t frac = 0;
    if (p < end && *p == '.') {
        ++p;
        int d = *p++ - '0';
        frac = uint32_t(d) * 10;
        if (p < end) frac += uint32_t(*p - '0');
    }
    return int64_t(whole * 100 + frac);
}

void appendInt(string& out, int64_t v) {
    char buf[24];
    auto res = to_chars(buf, buf + sizeof(buf), v);
    out.append(buf, res.ptr);
}

void loadRates(const char* p, const char* lineEnd) {
    (void)lineEnd;
    p = skipWs(p);
    if (*p != '{') return;
    ++p;
    for (;;) {
        p = skipWs(p);
        if (*p == '}') break;
        StrVal key = parseKey(p);
        p = skipWs(key.p + key.len + 1);
        ++p; // ':'
        p = skipWs(p);
        if (strEquals(key, "rates")) {
            p = skipWs(p);
            ++p; // '{'
            for (;;) {
                p = skipWs(p);
                if (*p == '}') break;
                StrVal cur = parseKey(p);
                p = skipWs(cur.p + cur.len + 1);
                ++p; // ':'
                p = skipWs(p);
                bool neg = (*p == '-');
                if (neg) ++p;
                int64_t rate = 0;
                while (*p >= '0' && *p <= '9') rate = rate * 10 + (*p++ - '0');
                if (neg) rate = -rate;
                string_view name(cur.p, cur.len);
                if (cur.escaped) name = intern(decodeString(cur.p, cur.len));
                g_rates.emplace(name, rate);
                p = skipWs(p);
                if (*p == ',') ++p;
            }
            ++p;
        } else {
            p = skipValue(p);
        }
        p = skipWs(p);
        if (*p == ',') ++p;
    }
}

} // namespace

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    _setmode(_fileno(stdout), _O_BINARY);
    FILE* f = fopen(argv[1], "rb");
    if (!f) return 1;
    fseek(f, 0, SEEK_END);
    long size = ftell(f);
    fseek(f, 0, SEEK_SET);
    string data(size, '\0');
    size_t got = fread(data.data(), 1, size_t(size), f);
    fclose(f);
    if (got != size_t(size)) return 1;

    const char* p = data.data();
    const char* end = p + size;

    // First line: rates.
    const char* eol = (const char*)memchr(p, '\n', size_t(end - p));
    if (!eol) eol = end;
    loadRates(p, eol);
    p = eol + 1;

    int64_t totalNet = 0;
    int64_t totalCount = 0;
    int32_t sign = 0;
    const int64_t* rate = nullptr;
    int64_t amount = 0;
    const char* accP = nullptr;
    uint32_t accLen = 0;
    bool accEsc = false;
    StrVal chan{nullptr, 0, false};
    bool isTest = false;

    while (p < end) {
        eol = (const char*)memchr(p, '\n', size_t(end - p));
        if (!eol) eol = end;
        const char* q = skipWs(p);
        if (q < eol && *q == '{') {
            ++q;
            sign = 0;
            rate = nullptr;
            amount = 0;
            accP = nullptr;
            accLen = 0;
            accEsc = false;
            chan = {nullptr, 0, false};
            isTest = false;
            for (;;) {
                q = skipWs(q);
                if (*q == '}') { ++q; break; }
                if (*q == ',') { ++q; continue; }
                StrVal key = parseKey(q);
                q = skipWs(key.p + key.len + 1);
                ++q; // ':'
                q = skipWs(q);
                if (!key.escaped) {
                    uint32_t kl = key.len;
                    char k0 = kl ? key.p[0] : '\0';
                    if (k0 == 't' && kl == 4 && memcmp(key.p, "type", 4) == 0) {
                        StrVal v = parseString(q);
                        q = v.p + v.len + 1;
                        if (!v.escaped) {
                            if (v.len == 6 && memcmp(v.p, "credit", 6) == 0) sign = 1;
                            else if (v.len == 5 && memcmp(v.p, "debit", 5) == 0) sign = -1;
                            else if (v.len == 6 && memcmp(v.p, "refund", 6) == 0) sign = 1;
                        } else {
                            if (strEquals(v, "credit") || strEquals(v, "refund")) sign = 1;
                            else if (strEquals(v, "debit")) sign = -1;
                        }
                        continue;
                    } else if (k0 == 'a' && kl == 6 && memcmp(key.p, "amount", 6) == 0) {
                        StrVal v = parseString(q);
                        q = v.p + v.len + 1;
                        amount = parseUnsignedAmount(v);
                        continue;
                    } else if (k0 == 'c' && kl == 8 && memcmp(key.p, "currency", 8) == 0) {
                        StrVal v = parseString(q);
                        q = v.p + v.len + 1;
                        rate = findRate(string_view(v.p, v.len));
                        continue;
                    } else if (k0 == 'a' && kl == 7 && memcmp(key.p, "account", 7) == 0) {
                        StrVal v = parseString(q);
                        q = v.p + v.len + 1;
                        accP = v.p;
                        accLen = v.len;
                        accEsc = v.escaped;
                        continue;
                    } else if (k0 == 't' && kl == 4 && memcmp(key.p, "tags", 4) == 0) {
                        // array of strings; look for "test"
                        ++q; // '['
                        for (;;) {
                            q = skipWs(q);
                            if (*q == ']') { ++q; break; }
                            if (*q == '"') {
                                StrVal v = parseString(q);
                                q = v.p + v.len + 1;
                                if (!isTest && strEquals(v, "test")) isTest = true;
                            } else {
                                q = skipValue(q);
                            }
                            q = skipWs(q);
                            if (*q == ',') ++q;
                        }
                        continue;
                    } else if (k0 == 'm' && kl == 4 && memcmp(key.p, "meta", 4) == 0) {
                        // object; we only need meta.channel
                        ++q; // '{'
                        for (;;) {
                            q = skipWs(q);
                            if (*q == '}') { ++q; break; }
                            StrVal mk = parseKey(q);
                            q = skipWs(mk.p + mk.len + 1);
                            ++q; // ':'
                            q = skipWs(q);
                            if (strEquals(mk, "channel")) {
                                chan = parseString(q);
                                q = chan.p + chan.len + 1;
                            } else {
                                q = skipValue(q);
                            }
                            q = skipWs(q);
                            if (*q == ',') ++q;
                        }
                        continue;
                    }
                }
                q = skipValue(q);
            }
            if (sign != 0 && !isTest && rate != nullptr && accP != nullptr &&
                chan.p != nullptr) {
                int64_t usd = (amount * *rate) / int64_t(kMicro);
                int64_t val = sign * usd;
                ++totalCount;
                totalNet += val;
                string_view cname(chan.p, chan.len);
                if (chan.escaped) cname = intern(decodeString(chan.p, chan.len));
                if (ChannelAgg* ca = findChannel(cname)) {
                    ca->count += 1;
                    ca->net += val;
                } else {
                    string_view key = chan.escaped ? intern(decodeString(chan.p, chan.len)) : cname;
                    g_channels.emplace(key, ChannelAgg{1, val});
                }
                string_view aname(accP, accLen);
                if (accEsc) aname = decodeString(accP, accLen);
                if (int64_t* an = findAccount(aname)) {
                    *an += val;
                } else {
                    string_view key = accEsc ? intern(aname) : aname;
                    g_accounts.emplace(key, val);
                }
            }
        }
        p = eol < end ? eol + 1 : end;
    }

    string out;
    out.reserve(1 << 16);
    out += "counted ";
    appendInt(out, totalCount);
    out += "\nnet ";
    appendInt(out, totalNet);
    out += '\n';

    // Channel lines sorted by name ascending (byte order).
    vector<const pair<const string_view, ChannelAgg>*> chans;
    chans.reserve(g_channels.size());
    for (const auto& kv : g_channels) chans.push_back(&kv);
    sort(chans.begin(), chans.end(),
         [](auto* a, auto* b) { return a->first < b->first; });
    for (auto* kv : chans) {
        out += "channel ";
        out.append(kv->first.data(), kv->first.size());
        out += ' ';
        appendInt(out, kv->second.count);
        out += ' ';
        appendInt(out, kv->second.net);
        out += '\n';
    }

    // Top 10 accounts by net desc, then id asc.
    vector<pair<int64_t, string_view>> accts;
    accts.reserve(g_accounts.size());
    for (const auto& kv : g_accounts) accts.emplace_back(kv.second, kv.first);
    size_t take = min<size_t>(10, accts.size());
    nth_element(accts.begin(), accts.begin() + take, accts.end(),
                [](const auto& a, const auto& b) {
                    if (a.first != b.first) return a.first > b.first;
                    return a.second < b.second;
                });
    sort(accts.begin(), accts.begin() + take,
         [](const auto& a, const auto& b) {
             if (a.first != b.first) return a.first > b.first;
             return a.second < b.second;
         });
    for (size_t i = 0; i < take; ++i) {
        out += "account ";
        out.append(accts[i].second.data(), accts[i].second.size());
        out += ' ';
        appendInt(out, accts[i].first);
        out += '\n';
    }

    fwrite(out.data(), 1, out.size(), stdout);
    return 0;
}
