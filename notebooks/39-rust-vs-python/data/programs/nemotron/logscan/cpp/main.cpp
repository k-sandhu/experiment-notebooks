#include <cstdio>
#include <cstdint>
#include <cstring>
#include <fcntl.h>
#include <io.h>
#include <vector>
#include <string>
#include <string_view>
#include <unordered_map>
#include <algorithm>
#include <utility>

using namespace std;

struct Stats {
    int count = 0;
    vector<int> lat; // latency in tenths of a ms
};

struct SVHash {
    using is_transparent = void;
    size_t operator()(string_view s) const noexcept {
        size_t h = 1469598103934665603ULL;
        for (unsigned char c : s) {
            h ^= c;
            h *= 1099511628211ULL;
        }
        return h;
    }
    size_t operator()(const string& s) const noexcept { return (*this)(string_view(s)); }
};

struct SVEq {
    using is_transparent = void;
    bool operator()(string_view a, string_view b) const noexcept { return a == b; }
    bool operator()(const string& a, string_view b) const noexcept { return string_view(a) == b; }
    bool operator()(string_view a, const string& b) const noexcept { return a == string_view(b); }
    bool operator()(const string& a, const string& b) const noexcept { return a == b; }
};

static unordered_map<string, Stats, SVHash, SVEq> g_map;

static inline bool isDig(char c) { return c >= '0' && c <= '9'; }

struct Parsed {
    int cls;
    int lat; // tenths of a ms
    const char* pathStart;
    const char* pathEnd;
};

// Validates one line (without its newline) against the SPEC.md regex and
// extracts status class, latency (tenths of a ms) and the path span.
// Full manual validation: every part of the regex is checked.
static bool parseLine(const char* s, const char* e, Parsed& out) {
    size_t len = (size_t)(e - s);
    if (len < 49) return false; // shortest possible well-formed line

    // timestamp: \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z<sp>
    if (s[4] != '-' || s[7] != '-' || s[10] != 'T' || s[13] != ':' || s[16] != ':' ||
        s[19] != '.' || s[23] != 'Z' || s[24] != ' ')
        return false;
    if (!isDig(s[0]) || !isDig(s[1]) || !isDig(s[2]) || !isDig(s[3]) ||
        !isDig(s[5]) || !isDig(s[6]) || !isDig(s[8]) || !isDig(s[9]) ||
        !isDig(s[11]) || !isDig(s[12]) || !isDig(s[14]) || !isDig(s[15]) ||
        !isDig(s[17]) || !isDig(s[18]) || !isDig(s[20]) || !isDig(s[21]) || !isDig(s[22]))
        return false;

    // host: [a-z]+-\d+<sp>
    const char* h = s + 25;
    if (h >= e || *h < 'a' || *h > 'z') return false;
    while (h < e && *h >= 'a' && *h <= 'z') ++h;
    if (h >= e || *h != '-') return false;
    ++h;
    if (h >= e || !isDig(*h)) return false;
    while (h < e && isDig(*h)) ++h;
    if (h >= e || *h != ' ') return false;
    ++h; // method

    size_t mlen = 0;
    size_t rem = (size_t)(e - h);
    if (rem >= 3 && (memcmp(h, "GET", 3) == 0 || memcmp(h, "PUT", 3) == 0)) mlen = 3;
    else if (rem >= 4 && memcmp(h, "POST", 4) == 0) mlen = 4;
    else if (rem >= 6 && memcmp(h, "DELETE", 6) == 0) mlen = 6;
    else if (rem >= 5 && memcmp(h, "PATCH", 5) == 0) mlen = 5;
    if (mlen == 0) return false;
    h += mlen;
    if (h >= e || *h != ' ') return false;
    ++h;

    // path: /[A-Za-z0-9_/-]* then optional \?[^ ]* then <sp>
    if (h >= e || *h != '/') return false;
    const char* pathStart = h;
    ++h;
    while (h < e) {
        char c = *h;
        if (c == ' ' || c == '?') break;
        if (!((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') ||
              c == '_' || c == '/' || c == '-'))
            return false;
        ++h;
    }
    const char* pathEnd = h;
    if (h < e && *h == '?') {
        ++h;
        while (h < e && *h != ' ') ++h;
    }
    if (h >= e || *h != ' ') return false;
    ++h;

    // status: \d{3}<sp>
    if (e - h < 3 || !isDig(h[0]) || !isDig(h[1]) || !isDig(h[2])) return false;
    out.cls = h[0] - '0';
    h += 3;
    if (h >= e || *h != ' ') return false;
    ++h;

    // size: \d+B<sp>
    if (h >= e || !isDig(*h)) return false;
    while (h < e && isDig(*h)) ++h;
    if (h >= e || *h != 'B') return false;
    ++h;
    if (h >= e || *h != ' ') return false;
    ++h;

    // latency: \d+.\dms "<ua>"<end>
    long long lat = 0;
    if (h >= e || !isDig(*h)) return false;
    while (h < e && isDig(*h)) { lat = lat * 10 + (*h - '0'); ++h; }
    if (h >= e || *h != '.') return false;
    ++h;
    if (h >= e || !isDig(*h)) return false;
    lat = lat * 10 + (*h - '0');
    ++h;
    if (e - h < 4 || h[0] != 'm' || h[1] != 's' || h[2] != ' ' || h[3] != '"') return false;
    h += 4;
    while (h < e && *h != '"') ++h;
    if (h >= e || *h != '"') return false;
    ++h;
    if (h != e) return false;

    out.pathStart = pathStart;
    out.pathEnd = pathEnd;
    out.lat = (int)lat;
    return true;
}

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    _setmode(_fileno(stdout), _O_BINARY);
    FILE* f = fopen(argv[1], "rb");
    if (!f) return 1;
    fseek(f, 0, SEEK_END);
    long fsize = ftell(f);
    fseek(f, 0, SEEK_SET);
    string data;
    if (fsize > 0) {
        data.resize((size_t)fsize);
        if (fread(data.data(), 1, data.size(), f) != data.size()) {
            fclose(f);
            return 1;
        }
    }
    fclose(f);

    const char* p = data.data();
    const char* end = p + data.size();

    long long nLines = 0, nMalformed = 0;
    int statusCount[10] = {};

    g_map.reserve(1 << 14);
    string tmplBuf;
    tmplBuf.reserve(128);
    Parsed parsed;

    while (p < end) {
        ++nLines;
        const char* lineStart = p;
        const char* nl = (const char*)memchr(p, '\n', (size_t)(end - p));
        const char* lineEnd = nl ? nl : end;
        p = nl ? nl + 1 : end;

        if (!parseLine(lineStart, lineEnd, parsed)) {
            ++nMalformed;
            continue;
        }
        ++statusCount[parsed.cls];

        // path template: split on '/', replace all-digit non-empty segments with {id}
        tmplBuf.clear();
        tmplBuf.push_back('/');
        {
            const char* segStart = parsed.pathStart + 1;
            const char* i = segStart;
            for (;;) {
                if (i == parsed.pathEnd || *i == '/') {
                    size_t seglen = (size_t)(i - segStart);
                    if (seglen > 0) {
                        bool allDig = true;
                        for (const char* j = segStart; j < i; ++j) {
                            if (!isDig(*j)) { allDig = false; break; }
                        }
                        if (allDig) tmplBuf.append("{id}", 4);
                        else tmplBuf.append(segStart, seglen);
                    }
                    if (i < parsed.pathEnd) tmplBuf.push_back('/');
                    segStart = i + 1;
                }
                if (i == parsed.pathEnd) break;
                ++i;
            }
        }

        string_view key(tmplBuf.data(), tmplBuf.size()); // transparent lookup: no allocation on hit
        auto it = g_map.find(key);
        if (it == g_map.end()) {
            it = g_map.emplace(string(tmplBuf), Stats{}).first;
            it->second.lat.reserve(16);
        }
        Stats& st = it->second;
        ++st.count;
        st.lat.push_back(parsed.lat);
    }

    vector<pair<string, Stats>> items;
    items.reserve(g_map.size());
    for (auto& kv : g_map)
        items.emplace_back(kv.first, std::move(kv.second));

    sort(items.begin(), items.end(),
         [](const pair<string, Stats>& a, const pair<string, Stats>& b) {
             if (a.second.count != b.second.count) return a.second.count > b.second.count;
             return a.first.compare(b.first) < 0; // byte order
         });

    string out;
    out.reserve(8192);
    out += "lines ";
    out += to_string(nLines);
    out += '\n';
    out += "malformed ";
    out += to_string(nMalformed);
    out += '\n';
    for (int c = 0; c < 10; ++c) {
        if (statusCount[c] != 0) {
            out += "status ";
            out += char('0' + c);
            out += "xx ";
            out += to_string(statusCount[c]);
            out += '\n';
        }
    }
    size_t top = items.size() < 10 ? items.size() : 10;
    for (size_t i = 0; i < top; ++i) {
        vector<int>& lat = items[i].second.lat;
        sort(lat.begin(), lat.end());
        size_t n = lat.size();
        auto kth = [&](int pct) -> int {
            return lat[((size_t)pct * n + 99) / 100 - 1];
        };
        auto fmt = [&](int t) {
            out += to_string(t / 10);
            out += '.';
            out += to_string(t % 10);
        };
        out += "path ";
        out += items[i].first;
        out += ' ';
        out += to_string(items[i].second.count);
        out += ' ';
        fmt(kth(50));
        out += ' ';
        fmt(kth(95));
        out += ' ';
        fmt((int)lat.back());
        out += '\n';
    }

    fwrite(out.data(), 1, out.size(), stdout);
    return 0;
}
