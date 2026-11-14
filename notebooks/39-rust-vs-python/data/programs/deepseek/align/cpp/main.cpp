#include <cstdio>
#include <cstdint>
#include <cstring>
#include <vector>
#include <string>
#include <charconv>
#include <io.h>
#include <fcntl.h>

namespace {

struct Parser {
    const unsigned char* p;
    const unsigned char* end;

    void skipWs() {
        while (p < end && *p <= ' ') ++p;
    }

    // Parse a non-negative integer.
    int nextInt() {
        skipWs();
        int v = 0;
        while (p < end && *p >= '0' && *p <= '9') {
            v = v * 10 + (*p - '0');
            ++p;
        }
        return v;
    }
};

inline void appendInt(std::string& out, long long v) {
    char buf[24];
    char* e = buf + sizeof(buf);
    char* b = e;
    if (v == 0) {
        out.push_back('0');
        return;
    }
    bool neg = v < 0;
    unsigned long long u = neg ? (unsigned long long)(-(v + 1)) + 1ULL : (unsigned long long)v;
    while (u) {
        *--b = char('0' + (u % 10));
        u /= 10;
    }
    if (neg) *--b = '-';
    out.append(b, e);
}

} // namespace

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    _setmode(_fileno(stdout), _O_BINARY);

    FILE* f = std::fopen(argv[1], "rb");
    if (!f) return 1;
    std::fseek(f, 0, SEEK_END);
    long sz = std::ftell(f);
    std::fseek(f, 0, SEEK_SET);
    std::vector<unsigned char> data((size_t)(sz > 0 ? sz : 0) + 1);
    size_t got = std::fread(data.data(), 1, (size_t)(sz > 0 ? sz : 0), f);
    std::fclose(f);
    data[got] = 0;

    Parser ps{data.data(), data.data() + got};

    // Alphabet line: letters in alphabet order.
    ps.skipWs();
    const unsigned char* ab = ps.p;
    while (ps.p < ps.end && *ps.p > ' ') ++ps.p;
    int A = (int)(ps.p - ab);
    int mp[256];
    for (int i = 0; i < 256; ++i) mp[i] = 0;
    for (int i = 0; i < A; ++i) mp[ab[i]] = i;

    std::vector<int> ins(A), delc(A), sub((size_t)A * A);
    for (int i = 0; i < A; ++i) ins[i] = ps.nextInt();
    for (int i = 0; i < A; ++i) delc[i] = ps.nextInt();
    for (int i = 0; i < A * A; ++i) sub[i] = ps.nextInt();

    int P = ps.nextInt();

    std::vector<unsigned char> s, t;
    std::vector<int> tins;
    std::vector<int> row;
    std::string out;
    out.reserve(8192);
    long long total = 0;

    for (int q = 0; q < P; ++q) {
        ps.skipWs();
        s.clear();
        while (ps.p < ps.end && *ps.p > ' ') {
            s.push_back((unsigned char)mp[*ps.p]);
            ++ps.p;
        }
        ps.skipWs();
        t.clear();
        while (ps.p < ps.end && *ps.p > ' ') {
            t.push_back((unsigned char)mp[*ps.p]);
            ++ps.p;
        }

        const int n = (int)s.size();
        const int m = (int)t.size();

        if (n == m && (n == 0 || std::memcmp(s.data(), t.data(), (size_t)n) == 0)) {
            out.push_back('0');
            out.push_back('\n');
            continue;
        }

        tins.resize(m);
        for (int j = 0; j < m; ++j) tins[j] = ins[t[j]];

        row.resize((size_t)m + 1);
        row[0] = 0;
        for (int j = 1; j <= m; ++j) row[j] = row[j - 1] + tins[j - 1];

        const unsigned char* sp = s.data();
        const unsigned char* tp = t.data();
        const int* tinsP = tins.data();
        int* r = row.data();

        for (int i = 0; i < n; ++i) {
            const int si = sp[i];
            const int dc = delc[si];
            const int* srow = sub.data() + (size_t)si * A;

            int diag = r[0];
            int left = diag + dc;
            r[0] = left;

            for (int j = 1; j <= m; ++j) {
                const int up = r[j];
                const int a = up + dc;
                const int b = diag + srow[tp[j - 1]];
                const int mn = a < b ? a : b;
                const int x = left + tinsP[j - 1];
                left = x < mn ? x : mn;
                diag = up;
                r[j] = left;
            }
        }

        const long long cost = r[m];
        total += cost;
        appendInt(out, cost);
        out.push_back('\n');
    }

    out.append("total ");
    appendInt(out, total);
    out.push_back('\n');

    std::fwrite(out.data(), 1, out.size(), stdout);
    return 0;
}
