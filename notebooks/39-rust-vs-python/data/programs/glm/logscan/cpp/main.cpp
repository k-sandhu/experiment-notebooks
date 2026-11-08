#include <cstdio>
#include <cstdint>
#include <cstring>
#include <charconv>
#include <fcntl.h>
#include <io.h>
#include <string>
#include <string_view>
#include <unordered_map>
#include <vector>
#include <algorithm>

using namespace std;

struct SvHash {
    using is_transparent = void;
    size_t operator()(string_view s) const noexcept {
        return hash<string_view>{}(s);
    }
};

struct Agg {
    uint64_t count = 0;
    vector<int64_t> lats;
};

static inline bool isdig(char c) { return c >= '0' && c <= '9'; }
static inline bool issegc(char c) {  // path segment char (regex [A-Za-z0-9_-])
    return (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || c == '_' || c == '-';
}

struct Parser {
    uint64_t lines = 0, malformed = 0;
    uint64_t statusCnt[10] = {0, 0, 0, 0, 0, 0, 0, 0, 0, 0};
    unordered_map<string, Agg, SvHash, equal_to<>> aggs;
    vector<char> scratch;
    string out;

    bool parseLine(const char* p, const char* end) {
        if (end - p < 26) return false;
        // timestamp: dddd-dd-ddTdd:dd:dd.dddZ + space
        if (p[4] != '-' || p[7] != '-' || p[10] != 'T' || p[13] != ':' || p[16] != ':' ||
            p[19] != '.' || p[23] != 'Z' || p[24] != ' ')
            return false;
        for (int i : {0, 1, 2, 3, 5, 6, 8, 9, 11, 12, 14, 15, 17, 18, 20, 21, 22})
            if (!isdig(p[i])) return false;
        p += 25;
        // server: [a-z]+-\d+ + space
        const char* s0 = p;
        while (p < end && *p >= 'a' && *p <= 'z') ++p;
        if (p == s0 || p + 1 >= end || *p != '-') return false;
        ++p;
        const char* d0 = p;
        while (p < end && isdig(*p)) ++p;
        if (p == d0 || p + 1 >= end || *p != ' ') return false;
        ++p;
        // method
        if (end - p >= 4 && memcmp(p, "GET ", 4) == 0) p += 4;
        else if (end - p >= 6 && memcmp(p, "POST ", 5) == 0) p += 5;
        else if (end - p >= 4 && memcmp(p, "PUT ", 4) == 0) p += 4;
        else if (end - p >= 7 && memcmp(p, "DELETE ", 7) == 0) p += 7;
        else if (end - p >= 6 && memcmp(p, "PATCH ", 6) == 0) p += 6;
        else return false;
        // path: /[A-Za-z0-9_/-]* with digit segments -> {id}
        if (p >= end || *p != '/') return false;
        scratch.clear();
        while (true) {
            size_t segStart = scratch.size();
            while (p < end && issegc(*p)) { scratch.push_back(*p); ++p; }
            bool allDig = scratch.size() > segStart;
            for (size_t i = segStart; allDig && i < scratch.size(); ++i) allDig = isdig(scratch[i]);
            if (allDig) {
                scratch.resize(segStart);
                scratch.insert(scratch.end(), {'{', 'i', 'd', '}'});
            }
            if (p < end && *p == '/') { scratch.push_back('/'); ++p; continue; }
            break;
        }
        if (p < end && *p == '?') { ++p; while (p < end && *p != ' ') ++p; }
        if (p + 1 >= end || *p != ' ') return false;
        ++p;
        // status \d{3}
        if (end - p < 4 || !isdig(p[0]) || !isdig(p[1]) || !isdig(p[2])) return false;
        unsigned cls = p[0] - '0';
        p += 3;
        if (p + 1 >= end || *p != ' ') return false;
        ++p;
        // size \d+B
        const char* b0 = p;
        while (p < end && isdig(*p)) ++p;
        if (p == b0 || end - p < 2 || p[0] != 'B' || p[1] != ' ') return false;
        p += 2;
        // latency \d+.\dms
        const char* l0 = p;
        while (p < end && isdig(*p)) ++p;
        if (p == l0 || end - p < 5 || p[0] != '.' || !isdig(p[1]) || p[2] != 'm' || p[3] != 's' || p[4] != ' ')
            return false;
        uint64_t v = 0;
        if (p - l0 > 18) {
            v = 1000000000000000ULL;  // saturate absurdly large latencies
        } else {
            while (l0 < p) v = v * 10 + (uint64_t)(*l0++ - '0');
            v = v * 10 + (uint64_t)(p[1] - '0');
            if (v > 1000000000000000ULL) v = 1000000000000000ULL;
        }
        p += 5;
        // user agent "[^"]*"
        if (*p != '"') return false;
        ++p;
        while (p < end && *p != '"') ++p;
        if (p != end - 1) return false;
        // aggregate
        ++statusCnt[cls];
        string_view key(scratch.data(), scratch.size());
        auto it = aggs.find(key);
        if (it == aggs.end()) it = aggs.emplace(string(key), Agg{}).first;
        it->second.count++;
        it->second.lats.push_back((int64_t)v);
        return true;
    }

    static void appendNum(string& out, uint64_t v) {
        char tmp[20];
        auto r = to_chars(tmp, tmp + sizeof(tmp), v);
        out.append(tmp, r.ptr);
    }
    static void appendTenths(string& out, int64_t v) {
        appendNum(out, (uint64_t)v / 10);
        out.push_back('.');
        out.push_back((char)('0' + (v % 10)));
    }

    void run(const char* data, size_t sz) {
        scratch.reserve(512);
        const char* p = data;
        const char* end = data + sz;
        while (p < end) {
            const char* nl = (const char*)memchr(p, '\n', (size_t)(end - p));
            const char* le = nl ? nl : end;
            ++lines;
            if (!parseLine(p, le)) ++malformed;
            p = nl ? nl + 1 : end;
        }
        // rank templates
        vector<pair<const string, Agg>*> ranked;
        ranked.reserve(aggs.size());
        for (auto& kv : aggs) ranked.push_back(&kv);
        sort(ranked.begin(), ranked.end(), [](auto* a, auto* b) {
            if (a->second.count != b->second.count) return a->second.count > b->second.count;
            return a->first < b->first;
        });
        if (ranked.size() > 10) ranked.resize(10);
        out.reserve(4096);
        out += "lines ";
        appendNum(out, lines);
        out += "\nmalformed ";
        appendNum(out, malformed);
        out += '\n';
        char clsName[4] = {'0', 'x', 'x', 0};
        for (unsigned d = 0; d < 10; ++d) {
            if (!statusCnt[d]) continue;
            clsName[0] = (char)('0' + d);
            out += "status ";
            out += clsName;
            out += ' ';
            appendNum(out, statusCnt[d]);
            out += '\n';
        }
        for (auto* kv : ranked) {
            vector<int64_t>& lats = kv->second.lats;
            size_t n = lats.size();
            sort(lats.begin(), lats.end());
            size_t i50 = (50 * n + 99) / 100 - 1;
            size_t i95 = (95 * n + 99) / 100 - 1;
            out += "path ";
            out += kv->first;
            out += ' ';
            appendNum(out, kv->second.count);
            out += ' ';
            appendTenths(out, lats[i50]);
            out += ' ';
            appendTenths(out, lats[i95]);
            out += ' ';
            appendTenths(out, lats[n - 1]);
            out += '\n';
        }
        fwrite(out.data(), 1, out.size(), stdout);
    }
};

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    _setmode(_fileno(stdout), _O_BINARY);
    FILE* f = fopen(argv[1], "rb");
    if (!f) return 1;
    _fseeki64(f, 0, SEEK_END);
    long long sz = _ftelli64(f);
    _fseeki64(f, 0, SEEK_SET);
    vector<char> buf((size_t)sz);
    if (sz > 0 && fread(buf.data(), 1, (size_t)sz, f) != (size_t)sz) return 1;
    fclose(f);
    Parser ps;
    ps.run(buf.data(), (size_t)sz);
    return 0;
}
