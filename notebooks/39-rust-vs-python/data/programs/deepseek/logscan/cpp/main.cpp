#include <cstdio>
#include <cstdlib>
#include <cstdint>
#include <cstring>
#include <vector>
#include <string>
#include <algorithm>
#include <unordered_map>
#include <io.h>
#include <fcntl.h>

static inline bool isDig(unsigned char c) { return (unsigned)(c - '0') <= 9u; }
static inline bool isPathCh(unsigned char c) {
    return (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') ||
           (c >= '0' && c <= '9') || c == '_' || c == '-' || c == '/';
}

static inline bool tsOk(const unsigned char* p) {
    return isDig(p[0]) && isDig(p[1]) && isDig(p[2]) && isDig(p[3]) && p[4] == '-' &&
           isDig(p[5]) && isDig(p[6]) && p[7] == '-' &&
           isDig(p[8]) && isDig(p[9]) && p[10] == 'T' &&
           isDig(p[11]) && isDig(p[12]) && p[13] == ':' &&
           isDig(p[14]) && isDig(p[15]) && p[16] == ':' &&
           isDig(p[17]) && isDig(p[18]) && p[19] == '.' &&
           isDig(p[20]) && isDig(p[21]) && isDig(p[22]) && p[23] == 'Z';
}

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    _setmode(_fileno(stdout), _O_BINARY);

    FILE* f = nullptr;
    if (fopen_s(&f, argv[1], "rb") != 0 || !f) return 1;

    std::unordered_map<std::string, uint32_t> map;
    map.reserve(1024);
    std::vector<std::string> names;
    std::vector<std::vector<uint64_t>> lats;
    std::vector<uint64_t> maxLat;
    std::string scratch;
    scratch.reserve(256);

    uint64_t lines = 0, malformed = 0;
    uint64_t statusCount[10] = {0, 0, 0, 0, 0, 0, 0, 0, 0, 0};

    auto process = [&](const unsigned char* p, const unsigned char* end) {
        lines++;
        bool ok = true;
        int statusClass = 0;
        uint64_t lat = 0;
        const unsigned char* pathStart = nullptr;
        const unsigned char* pathEnd = nullptr;

        do {
            if (end - p < 25 || !tsOk(p)) { ok = false; break; }
            p += 24;
            if (*p != ' ') { ok = false; break; }
            ++p;
            if (p >= end || *p < 'a' || *p > 'z') { ok = false; break; }
            ++p;
            while (p < end && *p >= 'a' && *p <= 'z') ++p;
            if (p >= end || *p != '-') { ok = false; break; }
            ++p;
            if (p >= end || !isDig(*p)) { ok = false; break; }
            while (p < end && isDig(*p)) ++p;
            if (p >= end || *p != ' ') { ok = false; break; }
            ++p;
            ptrdiff_t rem = end - p;
            if (rem >= 4 && p[0] == 'G' && p[1] == 'E' && p[2] == 'T' && p[3] == ' ') {
                p += 4;
            } else if (rem >= 5 && p[0] == 'P' && p[1] == 'O' && p[2] == 'S' && p[3] == 'T' && p[4] == ' ') {
                p += 5;
            } else if (rem >= 4 && p[0] == 'P' && p[1] == 'U' && p[2] == 'T' && p[3] == ' ') {
                p += 4;
            } else if (rem >= 7 && p[0] == 'D' && p[1] == 'E' && p[2] == 'L' && p[3] == 'E' && p[4] == 'T' && p[5] == 'E' && p[6] == ' ') {
                p += 7;
            } else if (rem >= 6 && p[0] == 'P' && p[1] == 'A' && p[2] == 'T' && p[3] == 'C' && p[4] == 'H' && p[5] == ' ') {
                p += 6;
            } else { ok = false; break; }

            if (p >= end || *p != '/') { ok = false; break; }
            pathStart = p;
            while (p < end && isPathCh(*p)) ++p;
            pathEnd = p;
            if (p < end && *p == '?') {
                ++p;
                while (p < end && *p != ' ') ++p;
            }
            if (p >= end || *p != ' ') { ok = false; break; }
            ++p;
            if (end - p < 4 || !isDig(p[0]) || !isDig(p[1]) || !isDig(p[2]) || p[3] != ' ') { ok = false; break; }
            statusClass = p[0] - '0';
            p += 4;
            if (p >= end || !isDig(*p)) { ok = false; break; }
            while (p < end && isDig(*p)) ++p;
            if (p >= end || *p != 'B') { ok = false; break; }
            ++p;
            if (p >= end || *p != ' ') { ok = false; break; }
            ++p;
            if (p >= end || !isDig(*p)) { ok = false; break; }
            uint64_t v = 0;
            while (p < end && isDig(*p)) { v = v * 10u + (uint64_t)(*p - '0'); ++p; }
            if (p >= end || *p != '.') { ok = false; break; }
            ++p;
            if (p >= end || !isDig(*p)) { ok = false; break; }
            v = v * 10u + (uint64_t)(*p - '0');
            ++p;
            if (end - p < 3 || p[0] != 'm' || p[1] != 's' || p[2] != ' ') { ok = false; break; }
            p += 3;
            if (p >= end || *p != '"') { ok = false; break; }
            ++p;
            while (p < end && *p != '"') ++p;
            if (p >= end) { ok = false; break; }
            ++p;
            if (p != end) { ok = false; break; }
            lat = v;
        } while (false);

        if (!ok) {
            malformed++;
        } else {
            statusCount[statusClass]++;
            scratch.clear();
            const unsigned char* q = pathStart;
            while (q < pathEnd) {
                scratch.push_back('/');
                ++q;
                const unsigned char* s = q;
                bool digits = true, nonempty = false;
                while (q < pathEnd && *q != '/') {
                    if (!isDig(*q)) digits = false;
                    nonempty = true;
                    ++q;
                }
                if (nonempty && digits) {
                    scratch += "{id}";
                } else {
                    scratch.append((const char*)s, (size_t)(q - s));
                }
            }
            auto it = map.find(scratch);
            uint32_t idx;
            if (it == map.end()) {
                idx = (uint32_t)names.size();
                map.emplace(scratch, idx);
                names.push_back(scratch);
                lats.emplace_back();
                maxLat.push_back(0);
            } else {
                idx = it->second;
            }
            lats[idx].push_back(lat);
            if (lat > maxLat[idx]) maxLat[idx] = lat;
        }
    };

    const size_t INIT_CAP = 4u << 20;
    size_t cap = INIT_CAP, len = 0;
    unsigned char* buf = (unsigned char*)malloc(cap);
    if (!buf) { fclose(f); return 1; }
    bool eof = false;
    while (!eof) {
        if (len == cap) {
            cap <<= 1;
            unsigned char* nb = (unsigned char*)realloc(buf, cap);
            if (!nb) { free(buf); fclose(f); return 1; }
            buf = nb;
        }
        size_t r = fread(buf + len, 1, cap - len, f);
        if (r == 0) {
            eof = true;
        } else {
            len += r;
        }
        size_t start = 0;
        while (start < len) {
            unsigned char* nl = (unsigned char*)memchr(buf + start, '\n', len - start);
            if (!nl) break;
            size_t e = (size_t)(nl - buf);
            process(buf + start, buf + e);
            start = e + 1;
        }
        if (start > 0) {
            memmove(buf, buf + start, len - start);
            len -= start;
        }
    }
    if (len > 0) process(buf, buf + len);
    fclose(f);
    free(buf);

    printf("lines %llu\n", (unsigned long long)lines);
    printf("malformed %llu\n", (unsigned long long)malformed);
    for (int d = 0; d < 10; ++d) {
        if (statusCount[d]) {
            printf("status %dxx %llu\n", d, (unsigned long long)statusCount[d]);
        }
    }

    std::vector<uint32_t> order(names.size());
    for (uint32_t i = 0; i < (uint32_t)order.size(); ++i) order[i] = i;
    std::sort(order.begin(), order.end(), [&](uint32_t a, uint32_t b) {
        size_t ca = lats[a].size(), cb = lats[b].size();
        if (ca != cb) return ca > cb;
        return names[a] < names[b];
    });

    size_t top = order.size() < 10 ? order.size() : 10;
    for (size_t k = 0; k < top; ++k) {
        uint32_t idx = order[k];
        std::vector<uint64_t>& v = lats[idx];
        std::sort(v.begin(), v.end());
        uint64_t cnt = (uint64_t)v.size();
        size_t i50 = (size_t)(((uint64_t)50 * cnt + 99) / 100) - 1;
        size_t i95 = (size_t)(((uint64_t)95 * cnt + 99) / 100) - 1;
        uint64_t p50 = v[i50], p95 = v[i95], mx = v.back();
        printf("path %s %llu %llu.%llu %llu.%llu %llu.%llu\n",
               names[idx].c_str(),
               (unsigned long long)cnt,
               (unsigned long long)(p50 / 10), (unsigned long long)(p50 % 10),
               (unsigned long long)(p95 / 10), (unsigned long long)(p95 % 10),
               (unsigned long long)(mx / 10), (unsigned long long)(mx % 10));
    }
    return 0;
}
