#include <cstdio>
#include <cstdint>
#include <cstring>
#include <cstdlib>
#include <vector>
#include <string>
#include <algorithm>
#include <fcntl.h>
#include <io.h>

using namespace std;

static inline bool isd(unsigned char c) { return (unsigned)(c - '0') < 10; }

struct Entry {
    string tmpl;
    uint32_t hash;
    uint64_t count = 0;
    vector<uint32_t> lat;
};

static vector<Entry> entries;
static vector<uint32_t> table; // entry index + 1, 0 = empty
static size_t tmask;
static size_t used;

static uint32_t hashBytes(const char* b, size_t n) {
    uint32_t h = 2166136261u;
    for (size_t i = 0; i < n; i++) { h ^= (unsigned char)b[i]; h *= 16777619u; }
    return h;
}

static void growTable() {
    size_t ncap = table.size() * 2;
    table.assign(ncap, 0);
    tmask = ncap - 1;
    for (size_t e = 0; e < entries.size(); e++) {
        uint32_t i = entries[e].hash & (uint32_t)tmask;
        while (table[i]) i = (i + 1) & (uint32_t)tmask;
        table[i] = (uint32_t)(e + 1);
    }
}

static size_t findOrInsert(const char* b, size_t n, uint32_t h) {
    uint32_t i = h & (uint32_t)tmask;
    while (table[i]) {
        Entry& e = entries[table[i] - 1];
        if (e.hash == h && e.tmpl.size() == n && memcmp(e.tmpl.data(), b, n) == 0)
            return table[i] - 1;
        i = (i + 1) & (uint32_t)tmask;
    }
    entries.emplace_back();
    Entry& e = entries.back();
    e.tmpl.assign(b, n);
    e.hash = h;
    table[i] = (uint32_t)entries.size();
    used++;
    if (used * 10 >= table.size() * 7) growTable();
    return entries.size() - 1;
}

static vector<char> tbuf;

static bool parse(const char* s, size_t n, size_t& ps, size_t& pe, uint32_t& tenths, int& cls) {
    if (n < 50) return false;
    static const char pat[] = "dddd-dd-ddTdd:dd:dd.dddZ";
    for (int j = 0; j < 24; j++) {
        char c = s[j], pc = pat[j];
        if (pc == 'd') { if (!isd((unsigned char)c)) return false; }
        else if (c != pc) return false;
    }
    size_t i = 24;
    if (s[i++] != ' ') return false;
    // host: [a-z]+-\d+
    size_t st = i;
    while (i < n && (unsigned)(s[i] - 'a') < 26) i++;
    if (i == st || i >= n || s[i] != '-') return false;
    i++;
    st = i;
    while (i < n && isd((unsigned char)s[i])) i++;
    if (i == st || i >= n || s[i] != ' ') return false;
    i++;
    // method
    if (n - i >= 4 && memcmp(s + i, "GET ", 4) == 0) i += 4;
    else if (n - i >= 4 && memcmp(s + i, "PUT ", 4) == 0) i += 4;
    else if (n - i >= 5 && memcmp(s + i, "POST ", 5) == 0) i += 5;
    else if (n - i >= 6 && memcmp(s + i, "PATCH ", 6) == 0) i += 6;
    else if (n - i >= 7 && memcmp(s + i, "DELETE ", 7) == 0) i += 7;
    else return false;
    if (n - i < 17) return false; // '/' + ' ' + minimal tail
    if (s[i] != '/') return false;
    ps = i;
    i++;
    while (i < n) {
        unsigned char c = (unsigned char)s[i];
        if ((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') || isd(c) ||
            c == '_' || c == '-' || c == '/') i++;
        else break;
    }
    pe = i;
    if (i < n && s[i] == '?') {
        i++;
        while (i < n && s[i] != ' ') i++;
    }
    if (i >= n || s[i] != ' ') return false;
    i++;
    if (n - i < 15) return false; // minimal tail: status .. closing quote
    if (!isd((unsigned char)s[i]) || !isd((unsigned char)s[i + 1]) || !isd((unsigned char)s[i + 2])) return false;
    cls = s[i] - '0';
    i += 3;
    if (s[i++] != ' ') return false;
    if (n - i < 11) return false; // minimal tail: size .. closing quote
    // size \d+B
    st = i;
    while (i < n && isd((unsigned char)s[i])) i++;
    if (i == st || s[i] != 'B') return false;
    i++;
    if (s[i++] != ' ') return false;
    // latency \d+\.\dms
    st = i;
    uint64_t v = 0;
    size_t nd = 0;
    while (i < n && isd((unsigned char)s[i])) {
        if (nd < 15) v = v * 10 + (uint64_t)(s[i] - '0');
        i++; nd++;
    }
    if (i == st || s[i] != '.') return false;
    i++;
    if (!isd((unsigned char)s[i])) return false;
    v = v * 10 + (uint64_t)(s[i] - '0');
    i++;
    if (s[i] != 'm' || s[i + 1] != 's' || s[i + 2] != ' ') return false;
    tenths = (uint32_t)min<uint64_t>(v, 0xFFFFFFFFull);
    i += 3;
    if (s[i] != '"') return false;
    i++;
    while (i < n && s[i] != '"') i++;
    if (i + 1 != n) return false;
    return true;
}

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    _setmode(_fileno(stdout), _O_BINARY);

    FILE* f = fopen(argv[1], "rb");
    if (!f) return 1;
    fseek(f, 0, SEEK_END);
    long long fsz = _ftelli64(f);
    fseek(f, 0, SEEK_SET);
    vector<char> data((size_t)fsz);
    if (fsz > 0 && fread(data.data(), 1, (size_t)fsz, f) != (size_t)fsz) { fclose(f); return 1; }
    fclose(f);

    const char* p = data.data();
    const char* end = p + fsz;

    table.assign(1024, 0);
    tmask = 1023;
    tbuf.reserve(512);

    uint64_t lines = 0, malformed = 0;
    uint64_t clsCount[10] = { 0 };

    while (p < end) {
        const char* nl = (const char*)memchr(p, '\n', (size_t)(end - p));
        const char* le = nl ? nl : end;
        size_t n = (size_t)(le - p);
        lines++;
        size_t ps, pe;
        uint32_t tenths;
        int cls;
        if (parse(p, n, ps, pe, tenths, cls)) {
            // build template
            size_t need = (size_t)(pe - ps) * 5 + 8;
            if (tbuf.size() < need) tbuf.resize(need * 2);
            size_t t = 0;
            size_t k = ps;
            while (k < pe) {
                tbuf[t++] = '/';
                k++;
                size_t s0 = k;
                while (k < pe && p[k] != '/') k++;
                size_t len = k - s0;
                bool dig = len > 0;
                for (size_t z = 0; dig && z < len; z++) if (!isd((unsigned char)p[s0 + z])) dig = false;
                if (dig) {
                    tbuf[t] = '{'; tbuf[t + 1] = 'i'; tbuf[t + 2] = 'd'; tbuf[t + 3] = '}';
                    t += 4;
                } else {
                    memcpy(tbuf.data() + t, p + s0, len);
                    t += len;
                }
            }
            uint32_t h = hashBytes(tbuf.data(), t);
            size_t e = findOrInsert(tbuf.data(), t, h);
            entries[e].count++;
            entries[e].lat.push_back(tenths);
            clsCount[cls]++;
        } else {
            malformed++;
        }
        if (!nl) break;
        p = nl + 1;
    }

    // order entries: count desc, template asc
    vector<uint32_t> ord(entries.size());
    for (size_t i = 0; i < ord.size(); i++) ord[i] = (uint32_t)i;
    sort(ord.begin(), ord.end(), [&](uint32_t a, uint32_t b) {
        if (entries[a].count != entries[b].count) return entries[a].count > entries[b].count;
        return entries[a].tmpl < entries[b].tmpl;
    });

    printf("lines %llu\n", (unsigned long long)lines);
    printf("malformed %llu\n", (unsigned long long)malformed);
    for (int d = 0; d < 10; d++)
        if (clsCount[d]) printf("status %dxx %llu\n", d, (unsigned long long)clsCount[d]);

    size_t top = min<size_t>(10, ord.size());
    for (size_t r = 0; r < top; r++) {
        Entry& e = entries[ord[r]];
        vector<uint32_t>& lat = e.lat;
        sort(lat.begin(), lat.end());
        size_t nn = lat.size();
        uint32_t p50 = lat[(50 * nn + 99) / 100 - 1];
        uint32_t p95 = lat[(95 * nn + 99) / 100 - 1];
        uint32_t mx = lat[nn - 1];
        printf("path %s %llu %u.%u %u.%u %u.%u\n", e.tmpl.c_str(),
               (unsigned long long)e.count,
               p50 / 10, p50 % 10, p95 / 10, p95 % 10, mx / 10, mx % 10);
    }
    return 0;
}
