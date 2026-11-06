#include <cstdio>
#include <cstdint>
#include <io.h>
#include <fcntl.h>
#include <cstring>
#include <vector>
#include <string>

using namespace std;

static int mapc[256];
static int insC[32], delC[32];
static int subC[32 * 32];
static int A;

static inline int readInt(const char*& p) {
    while (*p && (unsigned char)*p <= ' ') ++p;
    int x = 0;
    while (*p >= '0' && *p <= '9') {
        x = x * 10 + (*p - '0');
        ++p;
    }
    return x;
}

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    _setmode(_fileno(stdout), _O_BINARY);
    FILE* f = fopen(argv[1], "rb");
    if (!f) return 1;
    fseek(f, 0, SEEK_END);
    long sz = ftell(f);
    fseek(f, 0, SEEK_SET);
    vector<char> data((size_t)sz + 1);
    size_t rd = fread(data.data(), 1, (size_t)sz, f);
    fclose(f);
    data[rd] = 0;

    const char* p = data.data();

    for (int i = 0; i < 256; ++i) mapc[i] = -1;
    while (*p && (unsigned char)*p <= ' ') ++p;
    const char* astart = p;
    while (*p > ' ') ++p;
    A = (int)(p - astart);
    for (int i = 0; i < A; ++i) mapc[(unsigned char)astart[i]] = i;

    for (int i = 0; i < A; ++i) insC[i] = readInt(p);
    for (int i = 0; i < A; ++i) delC[i] = readInt(p);
    for (int i = 0; i < A; ++i)
        for (int j = 0; j < A; ++j)
            subC[i * A + j] = readInt(p);

    int P = readInt(p);
    vector<uint8_t> si, ti;
    si.reserve(4096);
    ti.reserve(4096);
    vector<int> insT;
    vector<int> prev, cur;
    string out;
    out.reserve((size_t)P * 8 + 16);

    int64_t total = 0;

    for (int q = 0; q < P; ++q) {
        while (*p && (unsigned char)*p <= ' ') ++p;
        si.clear();
        while (*p > ' ') { si.push_back((uint8_t)mapc[(unsigned char)*p]); ++p; }
        while (*p && (unsigned char)*p <= ' ') ++p;
        ti.clear();
        while (*p > ' ') { ti.push_back((uint8_t)mapc[(unsigned char)*p]); ++p; }

        const int n = (int)si.size();
        const int m = (int)ti.size();

        insT.resize(m);
        for (int j = 0; j < m; ++j) insT[j] = insC[ti[j]];

        prev.resize(m + 1);
        cur.resize(m + 1);
        prev[0] = 0;
        for (int j = 1; j <= m; ++j) prev[j] = prev[j - 1] + insT[j - 1];

        for (int i = 1; i <= n; ++i) {
            const int c = si[i - 1];
            const int d = delC[c];
            const int* sr = subC + c * A;
            int v = prev[0] + d;
            cur[0] = v;
            for (int j = 1; j <= m; ++j) {
                const int best0 = prev[j] + d;
                int x = v + insT[j - 1];
                int best = x < best0 ? x : best0;
                x = prev[j - 1] + sr[ti[j - 1]];
                if (x < best) best = x;
                v = best;
                cur[j] = best;
            }
            prev.swap(cur);
        }

        int cost = prev[m];
        total += cost;
        out += to_string(cost);
        out += '\n';
    }

    out += "total ";
    out += to_string(total);
    out += '\n';
    fwrite(out.data(), 1, out.size(), stdout);
    return 0;
}
