#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cstdint>
#include <fcntl.h>
#include <io.h>
#include <string>
#include <vector>
#include <algorithm>

#ifndef NOMINMAX
#define NOMINMAX
#endif
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <windows.h>

static inline bool isDig(char c) { return (unsigned)(c - '0') < 10u; }
static inline bool isLow(char c) { return (unsigned)(c - 'a') < 26u; }
static inline bool isPathCh(char c) {
    unsigned char u = (unsigned char)c;
    return isDig(c) || (u >= 'A' && u <= 'Z') || (u >= 'a' && u <= 'z') ||
           u == '_' || u == '/' || u == '-';
}

struct Entry {
    std::string tmpl;
    std::vector<long long> lat;
    uint32_t count = 0;
};

static std::vector<Entry> entries;
static std::vector<int32_t> table;   // slot value = entry index + 1

static inline uint32_t hashBytes(const char* b, size_t len) {
    uint32_t h = 2166136261u;
    for (size_t i = 0; i < len; ++i) {
        h = (h ^ (uint32_t)(unsigned char)b[i]) * 16777619u;
    }
    h ^= h >> 16;
    return h;
}

static int findEntry(const char* b, size_t len) {
    uint32_t mask = (uint32_t)table.size() - 1;
    uint32_t idx = hashBytes(b, len) & mask;
    for (;;) {
        int32_t s = table[idx];
        if (s == 0) return -1;
        const Entry& e = entries[(size_t)(s - 1)];
        if (e.tmpl.size() == len && memcmp(e.tmpl.data(), b, len) == 0)
            return (int)(s - 1);
        idx = (idx + 1) & mask;
    }
}

static int addEntry(const char* b, size_t len) {
    int e = (int)entries.size();
    entries.emplace_back();
    Entry& ent = entries.back();
    ent.tmpl.assign(b, len);
    ent.lat.reserve(16);
    size_t n = entries.size();
    if (n * 2 >= table.size()) {
        std::vector<int32_t> t(table.size() * 2, 0);
        uint32_t mask = (uint32_t)t.size() - 1;
        for (size_t i = 0; i < n; ++i) {
            const std::string& s = entries[i].tmpl;
            uint32_t idx = hashBytes(s.data(), s.size()) & mask;
            while (t[idx] != 0) idx = (idx + 1) & mask;
            t[idx] = (int32_t)(i + 1);
        }
        table.swap(t);
    } else {
        uint32_t mask = (uint32_t)table.size() - 1;
        uint32_t idx = hashBytes(b, len) & mask;
        while (table[idx] != 0) idx = (idx + 1) & mask;
        table[idx] = e + 1;
    }
    return e;
}

// Parses one line [p, p+le). Template bytes are written to ob (capacity guaranteed
// by caller). On success returns true and sets tplOut/tplLen/status/latency.
static bool parseLine(const char* p, size_t le, char* ob,
                      const char*& tplOut, size_t& tplLen,
                      int& outStatus, long long& outLat) {
    if (le < 25) return false;
    if (!(isDig(p[0]) && isDig(p[1]) && isDig(p[2]) && isDig(p[3]) && p[4] == '-' &&
          isDig(p[5]) && isDig(p[6]) && p[7] == '-' && isDig(p[8]) && isDig(p[9]) &&
          p[10] == 'T' && isDig(p[11]) && isDig(p[12]) && p[13] == ':' &&
          isDig(p[14]) && isDig(p[15]) && p[16] == ':' && isDig(p[17]) && isDig(p[18]) &&
          p[19] == '.' && isDig(p[20]) && isDig(p[21]) && isDig(p[22]) &&
          p[23] == 'Z' && p[24] == ' '))
        return false;

    size_t i = 25;
    size_t j = i;
    while (j < le && isLow(p[j])) ++j;
    if (j == i || j >= le || p[j] != '-') return false;
    ++j;
    size_t ds = j;
    while (j < le && isDig(p[j])) ++j;
    if (j == ds || j >= le || p[j] != ' ') return false;
    ++j;

    if (j + 4 <= le && p[j] == 'G' && p[j + 1] == 'E' && p[j + 2] == 'T' && p[j + 3] == ' ') {
        j += 4;
    } else if (j + 5 <= le && p[j] == 'P' && p[j + 1] == 'O' && p[j + 2] == 'S' &&
               p[j + 3] == 'T' && p[j + 4] == ' ') {
        j += 5;
    } else if (j + 4 <= le && p[j] == 'P' && p[j + 1] == 'U' && p[j + 2] == 'T' && p[j + 3] == ' ') {
        j += 4;
    } else if (j + 7 <= le && memcmp(p + j, "DELETE ", 7) == 0) {
        j += 7;
    } else if (j + 6 <= le && memcmp(p + j, "PATCH ", 6) == 0) {
        j += 6;
    } else {
        return false;
    }

    if (j >= le || p[j] != '/') return false;

    // Scan and build template in one pass. q ends at the first non-path char.
    size_t q = j;
    size_t t = 0;
    size_t segStart = 0;
    bool allDig = true;
    for (;;) {
        if (q >= le) break;
        unsigned char c = (unsigned char)p[q];
        if (c == '/') {
            if (allDig && t > segStart) {
                t = segStart;
                ob[t++] = '{'; ob[t++] = 'i'; ob[t++] = 'd'; ob[t++] = '}';
            }
            ob[t++] = '/';
            ++q;
            segStart = t;
            allDig = true;
            continue;
        }
        if (!isPathCh((char)c)) break;
        ob[t++] = (char)c;
        if (!isDig((char)c)) allDig = false;
        ++q;
    }
    if (allDig && t > segStart) {
        t = segStart;
        ob[t++] = '{'; ob[t++] = 'i'; ob[t++] = 'd'; ob[t++] = '}';
    }

    size_t fieldEnd;
    if (q < le && p[q] == '?') {
        size_t r = q + 1;
        while (r < le && p[r] != ' ') ++r;
        if (r >= le) return false;
        fieldEnd = r;
    } else if (q < le && p[q] == ' ') {
        fieldEnd = q;
    } else {
        return false;
    }

    size_t k = fieldEnd;
    if (k + 4 >= le) return false;
    if (!isDig(p[k + 1]) || !isDig(p[k + 2]) || !isDig(p[k + 3]) || p[k + 4] != ' ')
        return false;
    outStatus = (int)(p[k + 1] - '0');
    k += 5;

    size_t e = k;
    while (e < le && isDig(p[e])) ++e;
    if (e == k || e >= le || p[e] != 'B') return false;
    ++e;
    if (e >= le || p[e] != ' ') return false;
    ++e;

    size_t ls = e;
    uint64_t v = 0;
    while (e < le && isDig(p[e])) {
        v = v * 10u + (uint64_t)(p[e] - '0');
        ++e;
    }
    if (e == ls || e >= le || p[e] != '.') return false;
    ++e;
    if (e >= le || !isDig(p[e])) return false;
    v = v * 10u + (uint64_t)(p[e] - '0');
    ++e;
    if (e + 3 >= le) return false;
    if (p[e] != 'm' || p[e + 1] != 's' || p[e + 2] != ' ') return false;
    e += 3;
    if (p[e] != '"') return false;
    ++e;
    size_t r = e;
    while (r < le && p[r] != '"') ++r;
    if (r != le - 1) return false;

    tplOut = ob;
    tplLen = t;
    outLat = (long long)v;
    return true;
}

static void appendTenths(std::string& out, long long v) {
    char tmp[32];
    int n = snprintf(tmp, sizeof(tmp), "%lld.%lld", v / 10, v % 10);
    out.append(tmp, (size_t)n);
}

int main(int argc, char** argv) {
    _setmode(_fileno(stdout), _O_BINARY);
    if (argc < 2) return 1;

    HANDLE hFile = CreateFileA(argv[1], GENERIC_READ, FILE_SHARE_READ, nullptr,
                               OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (hFile == INVALID_HANDLE_VALUE) return 1;
    LARGE_INTEGER li;
    if (!GetFileSizeEx(hFile, &li)) { CloseHandle(hFile); return 1; }
    const char* data = nullptr;
    HANDLE hMap = nullptr;
    size_t sz = (size_t)li.QuadPart;
    if (sz > 0) {
        hMap = CreateFileMappingA(hFile, nullptr, PAGE_READONLY, 0, 0, nullptr);
        if (!hMap) { CloseHandle(hFile); return 1; }
        data = (const char*)MapViewOfFile(hMap, FILE_MAP_READ, 0, 0, 0);
        if (!data) { CloseHandle(hMap); CloseHandle(hFile); return 1; }
    }

    uint64_t lines = 0, malformed = 0;
    uint64_t statusCount[10] = {0};

    entries.reserve(1024);
    table.assign(2048, 0);

    static thread_local char localBuf[16384];

    const char* p = data;
    const char* end = data ? data + sz : data;
    while (p < end) {
        const char* nl = (const char*)memchr(p, '\n', (size_t)(end - p));
        const char* le = nl ? nl : end;
        ++lines;
        size_t lineLen = (size_t)(le - p);
        char* ob = localBuf;
        std::string big;
        if (lineLen * 4 + 16 > sizeof(localBuf)) {
            big.resize(lineLen * 4 + 16);
            ob = big.data();
        }
        const char* tpl = nullptr;
        size_t tlen = 0;
        int status = 0;
        long long lat = 0;
        if (parseLine(p, lineLen, ob, tpl, tlen, status, lat)) {
            ++statusCount[status];
            int e = findEntry(tpl, tlen);
            if (e < 0) e = addEntry(tpl, tlen);
            Entry& ent = entries[(size_t)e];
            ++ent.count;
            ent.lat.push_back(lat);
        } else {
            ++malformed;
        }
        if (nl) p = nl + 1;
        else break;
    }

    std::vector<uint32_t> ids(entries.size());
    for (uint32_t i = 0; i < (uint32_t)ids.size(); ++i) ids[i] = i;
    auto cmp = [](uint32_t a, uint32_t b) {
        const Entry& ea = entries[a];
        const Entry& eb = entries[b];
        if (ea.count != eb.count) return ea.count > eb.count;
        return ea.tmpl < eb.tmpl;
    };
    size_t topN = std::min<size_t>(10, ids.size());
    std::partial_sort(ids.begin(), ids.begin() + topN, ids.end(), cmp);

    std::string out;
    out.reserve(4096);
    out += "lines ";
    out += std::to_string(lines);
    out += "\nmalformed ";
    out += std::to_string(malformed);
    out += '\n';
    for (int c = 0; c < 10; ++c) {
        if (statusCount[c]) {
            out += "status ";
            out += (char)('0' + c);
            out += "xx ";
            out += std::to_string(statusCount[c]);
            out += '\n';
        }
    }
    for (size_t t = 0; t < topN; ++t) {
        Entry& ent = entries[ids[t]];
        std::vector<long long>& v = ent.lat;
        std::sort(v.begin(), v.end());
        size_t n = v.size();
        size_t i50 = (50 * n + 99) / 100 - 1;
        size_t i95 = (95 * n + 99) / 100 - 1;
        out += "path ";
        out += ent.tmpl;
        out += ' ';
        out += std::to_string(ent.count);
        out += ' ';
        appendTenths(out, v[i50]);
        out += ' ';
        appendTenths(out, v[i95]);
        out += ' ';
        appendTenths(out, v[n - 1]);
        out += '\n';
    }
    fwrite(out.data(), 1, out.size(), stdout);

    if (data) UnmapViewOfFile(data);
    if (hMap) CloseHandle(hMap);
    CloseHandle(hFile);
    return 0;
}
