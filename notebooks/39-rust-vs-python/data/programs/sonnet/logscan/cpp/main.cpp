#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>
#include <io.h>
#include <fcntl.h>

namespace {

struct Entry {
    uint32_t off, len, count;
    uint64_t hash;
};

std::vector<char> arena;
std::vector<Entry> entries;
std::vector<int32_t> table;  // -1 empty
uint64_t tableMask = 0;
std::vector<int32_t> recTid;
std::vector<int64_t> recLat;
std::vector<char> tmpl;

uint64_t lines = 0, malformed = 0;
uint64_t statusCount[10];

inline bool isDigit(char c) { return (unsigned)(c - '0') < 10u; }

void growTable() {
    size_t cap = table.empty() ? 1024 : table.size() * 2;
    table.assign(cap, -1);
    tableMask = cap - 1;
    for (size_t i = 0; i < entries.size(); i++) {
        uint64_t h = entries[i].hash & tableMask;
        while (table[h] >= 0) h = (h + 1) & tableMask;
        table[h] = (int32_t)i;
    }
}

int32_t lookup(const char* t, size_t len) {
    uint64_t h = 1469598103934665603ULL;
    for (size_t i = 0; i < len; i++) h = (h ^ (unsigned char)t[i]) * 1099511628211ULL;
    h ^= h >> 29;
    uint64_t slot = h & tableMask;
    while (true) {
        int32_t id = table[slot];
        if (id < 0) break;
        const Entry& e = entries[id];
        if (e.hash == h && e.len == len && memcmp(&arena[e.off], t, len) == 0) return id;
        slot = (slot + 1) & tableMask;
    }
    Entry e;
    e.off = (uint32_t)arena.size();
    e.len = (uint32_t)len;
    e.count = 0;
    e.hash = h;
    arena.insert(arena.end(), t, t + len);
    entries.push_back(e);
    int32_t id = (int32_t)entries.size() - 1;
    if (entries.size() * 2 > table.size()) {
        growTable();
    } else {
        table[slot] = id;
    }
    return id;
}

inline bool isPathChar(unsigned char c) {
    return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') || c == '_' || c == '/' || c == '-';
}

void processLine(const char* s, const char* e) {
    lines++;
    const char* p = s;
    size_t n = (size_t)(e - s);
    if (n < 40) { malformed++; return; }
    // timestamp
    if (!(isDigit(p[0]) && isDigit(p[1]) && isDigit(p[2]) && isDigit(p[3]) && p[4] == '-' && isDigit(p[5]) &&
          isDigit(p[6]) && p[7] == '-' && isDigit(p[8]) && isDigit(p[9]) && p[10] == 'T' && isDigit(p[11]) &&
          isDigit(p[12]) && p[13] == ':' && isDigit(p[14]) && isDigit(p[15]) && p[16] == ':' && isDigit(p[17]) &&
          isDigit(p[18]) && p[19] == '.' && isDigit(p[20]) && isDigit(p[21]) && isDigit(p[22]) && p[23] == 'Z' &&
          p[24] == ' ')) { malformed++; return; }
    p += 25;
    // host
    const char* q = p;
    while (q < e && *q >= 'a' && *q <= 'z') q++;
    if (q == p || q >= e || *q != '-') { malformed++; return; }
    q++;
    p = q;
    while (q < e && isDigit(*q)) q++;
    if (q == p || q >= e || *q != ' ') { malformed++; return; }
    p = q + 1;
    // method
    size_t rem = (size_t)(e - p);
    if (rem < 8) { malformed++; return; }
    if (memcmp(p, "GET ", 4) == 0) p += 4;
    else if (memcmp(p, "PUT ", 4) == 0) p += 4;
    else if (memcmp(p, "POST ", 5) == 0) p += 5;
    else if (memcmp(p, "PATCH ", 6) == 0) p += 6;
    else if (memcmp(p, "DELETE ", 7) == 0) p += 7;
    else { malformed++; return; }
    // path
    if (p >= e || *p != '/') { malformed++; return; }
    const char* pathStart = p;
    p++;
    while (p < e && isPathChar((unsigned char)*p)) p++;
    const char* pathEnd = p;
    if (p >= e) { malformed++; return; }
    if (*p == '?') {
        p++;
        while (p < e && *p != ' ') p++;
        if (p >= e) { malformed++; return; }
    }
    if (*p != ' ') { malformed++; return; }
    p++;
    // status
    if (e - p < 5 || !(isDigit(p[0]) && isDigit(p[1]) && isDigit(p[2]) && p[3] == ' ')) { malformed++; return; }
    int cls = p[0] - '0';
    p += 4;
    // size
    q = p;
    while (q < e && isDigit(*q)) q++;
    if (q == p || e - q < 2 || q[0] != 'B' || q[1] != ' ') { malformed++; return; }
    p = q + 2;
    // latency
    int64_t lat = 0;
    q = p;
    while (q < e && isDigit(*q)) { lat = lat * 10 + (*q - '0'); q++; }
    if (q == p || e - q < 6 || q[0] != '.' || !isDigit(q[1]) || q[2] != 'm' || q[3] != 's' || q[4] != ' ' || q[5] != '"') {
        malformed++;
        return;
    }
    lat = lat * 10 + (q[1] - '0');
    p = q + 6;
    // user agent: closing quote must be the last char
    const char* last = e - 1;
    if (p > last || *last != '"' || memchr(p, '"', (size_t)(last - p)) != nullptr) { malformed++; return; }

    statusCount[cls]++;
    // template
    size_t plen = (size_t)(pathEnd - pathStart);
    if (tmpl.size() < plen * 4 + 8) tmpl.resize(plen * 4 + 8);
    char* out = tmpl.data();
    *out++ = '/';
    char* segStart = out;
    bool allDigits = true;
    for (const char* c = pathStart + 1;; c++) {
        if (c == pathEnd || *c == '/') {
            if (allDigits && out > segStart) {
                out = segStart;
                memcpy(out, "{id}", 4);
                out += 4;
            }
            if (c == pathEnd) break;
            *out++ = '/';
            segStart = out;
            allDigits = true;
        } else {
            *out++ = *c;
            allDigits &= isDigit(*c);
        }
    }
    size_t tlen = (size_t)(out - tmpl.data());
    int32_t id = lookup(tmpl.data(), tlen);
    entries[id].count++;
    recTid.push_back(id);
    recLat.push_back(lat);
}

void fmtLat(std::string& o, int64_t v) {
    o += std::to_string(v / 10);
    o += '.';
    o += (char)('0' + v % 10);
}

}  // namespace

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    _setmode(_fileno(stdout), _O_BINARY);
    FILE* f = fopen(argv[1], "rb");
    if (!f) return 1;
    growTable();
    recTid.reserve(1 << 16);
    recLat.reserve(1 << 16);
    size_t cap = 1 << 22, have = 0;
    std::vector<char> buf(cap);
    while (true) {
        size_t n = fread(buf.data() + have, 1, cap - have, f);
        bool eof = n == 0;
        have += n;
        const char* base = buf.data();
        const char* cur = base;
        const char* end = base + have;
        while (cur < end) {
            const char* nl = (const char*)memchr(cur, '\n', (size_t)(end - cur));
            if (!nl) break;
            processLine(cur, nl);
            cur = nl + 1;
        }
        size_t rest = (size_t)(end - cur);
        if (eof) {
            if (rest > 0) processLine(cur, end);
            break;
        }
        if (cur != base) memmove(buf.data(), cur, rest);
        have = rest;
        if (have == cap) {
            cap *= 2;
            buf.resize(cap);
        }
    }
    fclose(f);

    std::string o;
    o += "lines " + std::to_string(lines) + "\n";
    o += "malformed " + std::to_string(malformed) + "\n";
    for (int c = 0; c < 10; c++) {
        if (statusCount[c]) {
            o += "status ";
            o += (char)('0' + c);
            o += "xx " + std::to_string(statusCount[c]) + "\n";
        }
    }
    std::vector<int32_t> order(entries.size());
    for (size_t i = 0; i < order.size(); i++) order[i] = (int32_t)i;
    auto cmp = [&](int32_t a, int32_t b) {
        if (entries[a].count != entries[b].count) return entries[a].count > entries[b].count;
        const Entry& x = entries[a];
        const Entry& y = entries[b];
        int r = memcmp(&arena[x.off], &arena[y.off], std::min(x.len, y.len));
        if (r != 0) return r < 0;
        return x.len < y.len;
    };
    size_t top = std::min<size_t>(10, order.size());
    std::partial_sort(order.begin(), order.begin() + top, order.end(), cmp);
    size_t total = recTid.size();
    std::vector<int64_t> v;
    std::vector<uint32_t> hist;
    for (size_t k = 0; k < top; k++) {
        int32_t id = order[k];
        const Entry& e = entries[id];
        v.clear();
        v.reserve(e.count);
        int64_t mx = 0;
        for (size_t i = 0; i < total; i++) {
            if (recTid[i] == id) {
                v.push_back(recLat[i]);
                if (recLat[i] > mx) mx = recLat[i];
            }
        }
        size_t cnt = v.size();
        size_t r50 = (50 * cnt + 99) / 100, r95 = (95 * cnt + 99) / 100;
        int64_t p50, p95;
        if (mx < (1 << 22)) {
            hist.assign((size_t)mx + 1, 0);
            for (int64_t x : v) hist[(size_t)x]++;
            size_t acc = 0;
            p50 = p95 = -1;
            for (size_t b = 0; b <= (size_t)mx; b++) {
                acc += hist[b];
                if (p50 < 0 && acc >= r50) p50 = (int64_t)b;
                if (acc >= r95) { p95 = (int64_t)b; break; }
            }
        } else {
            std::sort(v.begin(), v.end());
            p50 = v[r50 - 1];
            p95 = v[r95 - 1];
        }
        o += "path ";
        o.append(&arena[e.off], e.len);
        o += ' ' + std::to_string(cnt) + ' ';
        fmtLat(o, p50);
        o += ' ';
        fmtLat(o, p95);
        o += ' ';
        fmtLat(o, mx);
        o += '\n';
    }
    fwrite(o.data(), 1, o.size(), stdout);
    return 0;
}
