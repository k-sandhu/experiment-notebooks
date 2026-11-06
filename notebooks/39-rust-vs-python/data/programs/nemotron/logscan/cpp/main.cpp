// logscan: summarise an access log by status class and path-template latency percentiles.
// C++20, MSVC, standard library only.

#include <cstdio>
#include <cstdint>
#include <cstring>
#include <vector>
#include <string>
#include <string_view>
#include <algorithm>
#include <utility>
#include <io.h>
#include <fcntl.h>

using namespace std;

static inline bool isDigit(char c) { return c >= '0' && c <= '9'; }
static inline bool isUpper(char c) { return c >= 'A' && c <= 'Z'; }
static inline bool isLower(char c) { return c >= 'a' && c <= 'z'; }

struct Stats {
    int count = 0;
    int maxT = 0;          // max latency in tenths of a ms
    vector<int> lats;      // all latencies of this template, in tenths of a ms
};

static inline uint64_t fnv(string_view sv) {
    uint64_t h = 1469598103934665603ULL;
    for (unsigned char c : sv) {
        h ^= c;
        h *= 1099511628211ULL;
    }
    return h;
}

// Open-addressing map from path template (string_view) to stats.
// Keys are interned once on first sight; lookups never allocate.
class Map {
public:
    struct Entry {
        uint64_t hash = 0;
        string key;
        Stats stats;
        bool occupied = false;
    };

    Map() : buckets_(1 << 10), count_(0) {}

    Stats* findOrCreate(string_view sv) {
        uint64_t h = fnv(sv);
        size_t mask = buckets_.size() - 1;
        size_t i = (size_t)h & mask;
        while (buckets_[i].occupied) {
            if (buckets_[i].hash == h && buckets_[i].key == sv) return &buckets_[i].stats;
            i = (i + 1) & mask;
        }
        buckets_[i].occupied = true;
        buckets_[i].hash = h;
        buckets_[i].key.assign(sv.data(), sv.size());
        if (++count_ > (buckets_.size() * 7) / 10) grow();
        return &buckets_[i].stats;
    }

    vector<Entry>& buckets() { return buckets_; }

    void grow() {
        vector<Entry> nb(buckets_.size() * 2);
        size_t mask = nb.size() - 1;
        for (Entry& e : buckets_) {
            if (!e.occupied) continue;
            size_t i = (size_t)e.hash & mask;
            while (nb[i].occupied) i = (i + 1) & mask;
            nb[i] = move(e);
        }
        buckets_ = move(nb);
    }

private:
    vector<Entry> buckets_;
    size_t count_;
};

// Strictly validates one line of the access log and, if well-formed, extracts
// the status class (first digit of the status), the latency in tenths of a ms,
// and the path template.
static bool parseLine(const char* p, const char* e,
                      int& statusClass, int& latencyT, string& tbuf) {
    // 1. timestamp: \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z<space>
    if (e - p < 25) return false;
    if (!isDigit(p[0]) || !isDigit(p[1]) || !isDigit(p[2]) || !isDigit(p[3])) return false;
    if (p[4] != '-') return false;
    if (!isDigit(p[5]) || !isDigit(p[6])) return false;
    if (p[7] != '-') return false;
    if (!isDigit(p[8]) || !isDigit(p[9])) return false;
    if (p[10] != 'T') return false;
    if (!isDigit(p[11]) || !isDigit(p[12])) return false;
    if (p[13] != ':') return false;
    if (!isDigit(p[14]) || !isDigit(p[15])) return false;
    if (p[16] != ':') return false;
    if (!isDigit(p[17]) || !isDigit(p[18])) return false;
    if (p[19] != '.') return false;
    if (!isDigit(p[20]) || !isDigit(p[21]) || !isDigit(p[22])) return false;
    if (p[23] != 'Z' || p[24] != ' ') return false;
    p += 25;

    // 2. host: [a-z]+-\d+<space>
    if (p >= e || !isLower(*p)) return false;
    do { ++p; } while (p < e && isLower(*p));
    if (p >= e || *p != '-') return false;
    ++p;
    if (p >= e || !isDigit(*p)) return false;
    do { ++p; } while (p < e && isDigit(*p));
    if (p >= e || *p != ' ') return false;
    ++p;

    // 3. method: one of GET/POST/PUT/DELETE/PATCH followed by <space>
    static const struct { const char* s; int n; } methods[5] = {
        {"GET", 3}, {"POST", 4}, {"PUT", 3}, {"DELETE", 6}, {"PATCH", 5}
    };
    bool ok = false;
    for (int m = 0; m < 5 && !ok; ++m) {
        if (e - p > methods[m].n && memcmp(p, methods[m].s, methods[m].n) == 0 &&
            p[methods[m].n] == ' ') {
            p += methods[m].n + 1;
            ok = true;
        }
    }
    if (!ok) return false;

    // 4. path: '/' [A-Za-z0-9_/-]* [ '?' [^ ]* ] <space> ; build template on the fly
    tbuf.clear();
    if (p >= e || *p != '/') return false;
    size_t segStart = 0;
    bool segDigits = true;
    size_t segLen = 0;
    bool done = false;
    for (;;) {
        if (p >= e) return false; // path must terminate with space
        char c = *p;
        if (c == '/') {
            if (segLen > 0 && segDigits) {
                tbuf.resize(segStart);
                tbuf.append("{id}");
            }
            tbuf.push_back('/');
            ++p;
            segStart = tbuf.size();
            segDigits = true;
            segLen = 0;
        } else if (c == ' ') {
            if (segLen > 0 && segDigits) {
                tbuf.resize(segStart);
                tbuf.append("{id}");
            }
            ++p;
            done = true;
            break;
        } else if (c == '?') {
            if (segLen > 0 && segDigits) {
                tbuf.resize(segStart);
                tbuf.append("{id}");
            }
            ++p;
            while (p < e && *p != ' ') ++p; // query string: any non-space chars
            if (p >= e) return false;
            ++p;
            done = true;
            break;
        } else {
            if (!(isDigit(c) || isUpper(c) || isLower(c) || c == '_' || c == '-')) return false;
            if (segLen == 0) segDigits = isDigit(c);
            else if (segDigits && !isDigit(c)) segDigits = false;
            ++segLen;
            tbuf.push_back(c);
            ++p;
        }
    }
    if (!done) return false;

    // 5. status: \d{3}<space> ; class is the first digit
    if (e - p < 4) return false;
    if (!isDigit(p[0]) || !isDigit(p[1]) || !isDigit(p[2])) return false;
    if (p[3] != ' ') return false;
    statusClass = p[0] - '0';
    p += 4;

    // 6. size: \d+B<space>
    if (p >= e || !isDigit(*p)) return false;
    do { ++p; } while (p < e && isDigit(*p));
    if (p >= e || *p != 'B') return false;
    ++p;
    if (p >= e || *p != ' ') return false;
    ++p;

    // 7. latency: \d+.\d ms<space>
    const char* ls = p;
    while (p < e && isDigit(*p)) ++p;
    if (p == ls || p >= e || *p != '.') return false;
    const char* dot = p++;
    if (p >= e || !isDigit(*p)) return false;
    int frac = *p++ - '0';
    if (e - p < 3 || memcmp(p, "ms ", 3) != 0) return false;
    p += 3;
    long long ip = 0;
    for (const char* q = ls; q < dot; ++q) ip = ip * 10 + (*q - '0');
    latencyT = (int)(ip * 10 + frac);

    // 8. "..." then end of line
    if (p >= e || *p != '"') return false;
    ++p;
    while (p < e && *p != '"') ++p;
    if (p >= e) return false;
    ++p;
    return p == e;
}

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    _setmode(_fileno(stdout), _O_BINARY); // LF output, no CRLF translation
    FILE* f = fopen(argv[1], "rb");
    if (!f) return 1;
    if (fseek(f, 0, SEEK_END) != 0) { fclose(f); return 1; }
    long sz = ftell(f);
    if (sz < 0) { fclose(f); return 1; }
    if (fseek(f, 0, SEEK_SET) != 0) { fclose(f); return 1; }
    string buf;
    buf.resize((size_t)sz);
    if (sz > 0 && fread(buf.data(), 1, (size_t)sz, f) != (size_t)sz) { fclose(f); return 1; }
    fclose(f);

    const char* p = buf.data();
    const char* end = p + sz;

    long long lines = 0, malformed = 0;
    long long statusCount[10] = {};
    Map map;
    string tbuf;

    while (p < end) {
        const char* nl = (const char*)memchr(p, '\n', end - p);
        const char* lineEnd = nl ? nl : end;
        ++lines;
        int statusClass = 0, latencyT = 0;
        if (parseLine(p, lineEnd, statusClass, latencyT, tbuf)) {
            statusCount[statusClass]++;
            Stats* s = map.findOrCreate(string_view(tbuf.data(), tbuf.size()));
            s->count++;
            if (latencyT > s->maxT) s->maxT = latencyT;
            s->lats.push_back(latencyT);
        } else {
            ++malformed;
        }
        p = lineEnd + 1;
    }

    string out;
    out.reserve(1 << 12);
    out.append("lines ");
    out.append(to_string(lines));
    out.push_back('\n');
    out.append("malformed ");
    out.append(to_string(malformed));
    out.push_back('\n');
    for (int d = 0; d < 10; ++d) {
        if (statusCount[d] != 0) {
            out.append("status ");
            out.push_back(char('0' + d));
            out.append("xx ");
            out.append(to_string(statusCount[d]));
            out.push_back('\n');
        }
    }

    struct PathEntry {
        string key;
        Stats stats;
    };
    vector<PathEntry> paths;
    for (Map::Entry& e : map.buckets()) {
        if (e.occupied) paths.push_back({std::move(e.key), std::move(e.stats)});
    }
    sort(paths.begin(), paths.end(), [](const PathEntry& a, const PathEntry& b) {
        if (a.stats.count != b.stats.count) return a.stats.count > b.stats.count;
        return a.key < b.key; // byte order
    });

    auto fmtLat = [&](string& o, int t) {
        o.append(to_string(t / 10));
        o.push_back('.');
        o.push_back(char('0' + t % 10));
    };
    auto nearestRank = [](int pct, size_t n) -> size_t {
        return ((size_t)(((long long)pct * (long long)n + 99) / 100)) - 1;
    };

    size_t limit = min(paths.size(), (size_t)10);
    for (size_t i = 0; i < limit; ++i) {
        PathEntry& pe = paths[i];
        vector<int>& lats = pe.stats.lats;
        sort(lats.begin(), lats.end());
        size_t n = lats.size();
        out.append("path ");
        out.append(pe.key);
        out.push_back(' ');
        out.append(to_string(pe.stats.count));
        out.push_back(' ');
        fmtLat(out, lats[nearestRank(50, n)]);
        out.push_back(' ');
        fmtLat(out, lats[nearestRank(95, n)]);
        out.push_back(' ');
        fmtLat(out, pe.stats.maxT);
        out.push_back('\n');
    }

    fputs(out.c_str(), stdout);
    return 0;
}
