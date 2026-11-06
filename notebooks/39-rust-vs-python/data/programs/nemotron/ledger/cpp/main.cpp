#include <cstdio>
#include <cstdint>
#include <cstring>
#include <vector>
#include <string>
#include <string_view>
#include <unordered_map>
#include <algorithm>
#include <cstdlib>
#include <cinttypes>
#include <io.h>
#include <fcntl.h>

using i64 = int64_t;
using sv = std::string_view;

static std::string read_file(const char* path) {
    std::FILE* f = std::fopen(path, "rb");
    if (!f) { std::fprintf(stderr, "cannot open %s\n", path); std::exit(1); }
    std::fseek(f, 0, SEEK_END);
    long sz = std::ftell(f);
    std::fseek(f, 0, SEEK_SET);
    std::string buf;
    if (sz > 0) { buf.resize(sz); std::fread(buf.data(), 1, sz, f); }
    std::fclose(f);
    return buf;
}

// Scan a JSON string value starting at line[pos] (line[pos] == '"'). Unescapes into out.
// Sets pos to just after the closing quote. Returns false on malformed input.
static bool scan_string(sv line, size_t& pos, std::string& out) {
    out.clear();
    size_t i = pos + 1, n = line.size();
    while (i < n) {
        char c = line[i++];
        if (c == '"') { pos = i; return true; }
        if (c == '\\') {
            if (i >= n) return false;
            char e = line[i++];
            switch (e) {
                case '"': out.push_back('"'); break;
                case '\\': out.push_back('\\'); break;
                case '/': out.push_back('/'); break;
                case 'n': out.push_back('\n'); break;
                case 'r': out.push_back('\r'); break;
                case 't': out.push_back('\t'); break;
                case 'b': out.push_back('\b'); break;
                case 'f': out.push_back('\f'); break;
                case 'u': {
                    if (i + 3 >= n) return false;
                    unsigned cp = 0;
                    for (int k = 0; k < 4; ++k) {
                        char h = line[i++];
                        cp <<= 4;
                        if (h >= '0' && h <= '9') cp += h - '0';
                        else if (h >= 'a' && h <= 'f') cp += h - 'a' + 10;
                        else if (h >= 'A' && h <= 'F') cp += h - 'A' + 10;
                        else return false;
                    }
                    if (cp >= 0xD800 && cp <= 0xDBFF && i + 5 < n && line[i] == '\\' && line[i + 1] == 'u') {
                        i += 2; // skip \u
                        unsigned cp2 = 0;
                        for (int k = 0; k < 4; ++k) {
                            char h = line[i++];
                            cp2 <<= 4;
                            if (h >= '0' && h <= '9') cp2 += h - '0';
                            else if (h >= 'a' && h <= 'f') cp2 += h - 'a' + 10;
                            else if (h >= 'A' && h <= 'F') cp2 += h - 'A' + 10;
                            else return false;
                        }
                        cp = 0x10000u + ((cp - 0xD800u) << 10) + (cp2 - 0xDC00u);
                    }
                    if (cp < 0x80) out.push_back((char)cp);
                    else if (cp < 0x800) { out.push_back((char)(0xC0 | (cp >> 6))); out.push_back((char)(0x80 | (cp & 0x3F))); }
                    else if (cp < 0x10000) { out.push_back((char)(0xE0 | (cp >> 12))); out.push_back((char)(0x80 | ((cp >> 6) & 0x3F))); out.push_back((char)(0x80 | (cp & 0x3F))); }
                    else { out.push_back((char)(0xF0 | (cp >> 18))); out.push_back((char)(0x80 | ((cp >> 12) & 0x3F))); out.push_back((char)(0x80 | ((cp >> 6) & 0x3F))); out.push_back((char)(0x80 | (cp & 0x3F))); }
                    break;
                }
                default: return false;
            }
        } else {
            out.push_back(c);
        }
    }
    return false;
}

static void skip_ws(sv line, size_t& pos) {
    size_t n = line.size();
    while (pos < n && (line[pos] == ' ' || line[pos] == '\t' || line[pos] == '\r' || line[pos] == '\n')) ++pos;
}

// Skip a scalar non-string value (number / true / false / null) starting at line[pos].
static bool skip_scalar(sv line, size_t& pos);
// Parse a non-negative integer at line[pos], advancing pos past it.
static bool parse_int(sv line, size_t& pos, i64& out);

enum LineKind { RATES_LINE, TXN_COUNTED, TXN_SKIPPED, LINE_BAD };

// Parse a single line. For RATES_LINE fills rates. For TXN_* fills tx.
static LineKind parse_line(sv line, std::unordered_map<std::string, i64>& rates,
                           i64& usd, std::string& channel, std::string& account) {
    size_t i = 0, n = line.size();
    skip_ws(line, i);
    if (i >= n || line[i] != '{') return LINE_BAD;
    ++i; // skip outer {

    int depth = 1;
    std::string key;
    bool haveKey = false;
    int keyDepth = 0;

    bool inRates = false;
    int ratesDepth = 0;

    bool inMeta = false;
    int metaDepth = 0;

    bool inTags = false;
    int tagsDepth = 0;

    std::string acc, typ, amt, cur, chan;
    bool hasTest = false;
    bool isRates = false;

    while (i < n && depth > 0) {
        char c = line[i];
        if (c == '"') {
            std::string str;
            if (!scan_string(line, i, str)) return LINE_BAD;
            skip_ws(line, i);
            if (i < n && line[i] == ':') {
                // key
                key = str;
                keyDepth = depth;
                haveKey = true;
                ++i; // skip ':'
                skip_ws(line, i);
                if (i >= n) return LINE_BAD;
                char nxt = line[i];
                if (nxt == '"') {
                    // string value
                    if (!scan_string(line, i, str)) return LINE_BAD;
                    if (haveKey && keyDepth == 1) {
                        if (key == "account") acc = str;
                        else if (key == "type") typ = str;
                        else if (key == "currency") cur = str;
                        else if (key == "amount") amt = str;
                    } else if (haveKey && inMeta && depth == metaDepth && key == "channel") {
                        chan = str;
                    }
                    haveKey = false;
                } else if (nxt == '{') {
                    ++depth; ++i;
                    if (haveKey && keyDepth == 1 && key == "rates") { inRates = true; ratesDepth = depth; isRates = true; }
                    else if (haveKey && keyDepth == 1 && key == "meta") { metaDepth = depth; inMeta = true; }
                    haveKey = false;
                } else if (nxt == '[') {
                    ++depth; ++i;
                    if (haveKey && keyDepth == 1 && key == "tags") { inTags = true; tagsDepth = depth; }
                    haveKey = false;
                } else {
                    // scalar non-string value (number, true, false, null)
                    if (inRates && depth == ratesDepth && haveKey) {
                        i64 val = 0;
                        if (!parse_int(line, i, val)) return LINE_BAD;
                        rates[key] = val;
                    } else {
                        if (!skip_scalar(line, i)) return LINE_BAD;
                    }
                    haveKey = false;
                }
            } else {
                // string value without key -> array element
                if (inTags && depth == tagsDepth) {
                    if (str == "test") hasTest = true;
                }
                haveKey = false;
            }
        } else if (c == '{' || c == '[') {
            ++depth; ++i;
            haveKey = false;
        } else if (c == '}' || c == ']') {
            --depth; ++i;
            if (inMeta && depth == metaDepth - 1) inMeta = false;
            if (inTags && depth == tagsDepth - 1) inTags = false;
            haveKey = false;
        } else {
            ++i;
        }
    }

    if (isRates) return RATES_LINE;
    if (typ == "void") return TXN_SKIPPED;
    if (hasTest) return TXN_SKIPPED;

    // convert amount to integer hundredths: "12"->1200, "12.5"->1250, "12.05"->1205
    i64 hundredths = 0;
    {
        size_t j = 0;
        i64 dollars = 0;
        while (j < amt.size() && amt[j] >= '0' && amt[j] <= '9') { dollars = dollars * 10 + (amt[j] - '0'); ++j; }
        i64 cents = 0;
        if (j < amt.size() && amt[j] == '.') {
            ++j;
            int nd = 0;
            while (j < amt.size() && amt[j] >= '0' && amt[j] <= '9' && nd < 2) { cents = cents * 10 + (amt[j] - '0'); ++j; ++nd; }
            while (nd < 2) { cents *= 10; ++nd; }
        }
        hundredths = dollars * 100 + cents;
    }

    auto it = rates.find(cur);
    if (it == rates.end()) return LINE_BAD; // unknown currency
    i64 rate = it->second;
    usd = (hundredths * rate) / 1000000;
    if (typ == "debit") usd = -usd;
    channel = chan;
    account = acc;
    return TXN_COUNTED;
}

// Skip a scalar non-string value (number / true / false / null) starting at line[pos].
static bool skip_scalar(sv line, size_t& pos) {
    size_t i = pos, n = line.size();
    while (i < n) {
        char c = line[i];
        if (c == ',' || c == '}' || c == ']' || c == ' ' || c == '\t' || c == '\r' || c == '\n') { pos = i; return true; }
        ++i;
    }
    pos = n;
    return true;
}

// Parse a non-negative integer at line[pos], advancing pos past it.
static bool parse_int(sv line, size_t& pos, i64& out) {
    size_t i = pos, n = line.size();
    i64 v = 0;
    bool any = false;
    while (i < n && line[i] >= '0' && line[i] <= '9') { v = v * 10 + (line[i] - '0'); ++i; any = true; }
    if (!any) return false;
    pos = i;
    out = v;
    return true;
}

int main(int argc, char** argv) {
    if (argc < 2) { std::fprintf(stderr, "usage: solution INPUT_PATH\n"); return 1; }
    _setmode(_fileno(stdout), _O_BINARY);
    std::string buf = read_file(argv[1]);

    std::unordered_map<std::string, i64> rates;
    rates.reserve(64);

    // channel -> {count, net}
    struct Chan { i64 count = 0; i64 net = 0; };
    std::unordered_map<std::string, Chan> channels;
    channels.reserve(64);

    // account -> net
    std::unordered_map<std::string, i64> accounts;
    accounts.reserve(1024);

    i64 totalCount = 0;
    i64 totalNet = 0;

    size_t pos = 0, n = buf.size();
    while (pos < n) {
        size_t lineStart = pos;
        while (pos < n && buf[pos] != '\n') ++pos;
        sv line(buf.data() + lineStart, pos - lineStart);
        if (pos < n) ++pos; // skip newline

        if (line.size() == 0) continue;

        i64 usd = 0;
        std::string channel, account;
        LineKind kind = parse_line(line, rates, usd, channel, account);
        if (kind == RATES_LINE) { continue; }
        if (kind == LINE_BAD) continue;
        if (kind == TXN_SKIPPED) continue;

        totalCount++;
        totalNet += usd;

        Chan& c = channels[channel];
        c.count += 1;
        c.net += usd;

        accounts[account] += usd;
    }

    // Output
    std::string out;
    out.reserve(4096);
    out += "counted ";
    out += std::to_string(totalCount);
    out += '\n';
    out += "net ";
    out += std::to_string(totalNet);
    out += '\n';

    // channels sorted by name ascending
    std::vector<std::string> chNames;
    chNames.reserve(channels.size());
    for (auto& kv : channels) chNames.push_back(kv.first);
    std::sort(chNames.begin(), chNames.end());
    for (auto& name : chNames) {
        Chan& c = channels[name];
        out += "channel ";
        out += name;
        out += ' ';
        out += std::to_string(c.count);
        out += ' ';
        out += std::to_string(c.net);
        out += '\n';
    }

    // top 10 accounts by net desc, then id asc
    std::vector<std::pair<std::string, i64>> accts;
    accts.reserve(accounts.size());
    for (auto& kv : accounts) accts.push_back(kv);
    std::sort(accts.begin(), accts.end(), [](const auto& a, const auto& b) {
        if (a.second != b.second) return a.second > b.second;
        return a.first < b.first;
    });
    size_t limit = accts.size() < 10 ? accts.size() : 10;
    for (size_t k = 0; k < limit; ++k) {
        out += "account ";
        out += accts[k].first;
        out += ' ';
        out += std::to_string(accts[k].second);
        out += '\n';
    }

    std::fputs(out.c_str(), stdout);
    return 0;
}
