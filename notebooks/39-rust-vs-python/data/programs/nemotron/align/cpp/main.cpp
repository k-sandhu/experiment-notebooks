#include <cstdio>
#include <vector>
#include <cstdint>
#include <algorithm>

// Weighted edit distance for many string pairs.
// D[i][j] = min(D[i-1][j] + del[s_i], D[i][j-1] + ins[t_j],
//               D[i-1][j-1] + sub[s_i][t_j])
// Only two rows are needed. All costs are small (0..1000) and strings are at
// most 1000 letters, so every table cell fits in a 32-bit int; the total is a
// 64-bit integer.

static inline int readInt(const char*& p) {
    while (*p == ' ' || *p == '\n' || *p == '\r' || *p == '\t') ++p;
    int x = 0;
    while (*p >= '0' && *p <= '9') { x = x * 10 + (*p - '0'); ++p; }
    return x;
}

// Read one whitespace-separated token as letter indices into out (reused).
static void readToken(const char*& p, const int* idx, std::vector<int>& out) {
    while (*p == ' ' || *p == '\n' || *p == '\r' || *p == '\t') ++p;
    const char* start = p;
    while (*p > 32) ++p;
    out.clear();
    out.reserve(p - start);
    for (const char* q = start; q < p; ++q) out.push_back(idx[(unsigned char)*q]);
}

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    FILE* f = fopen(argv[1], "rb");
    if (!f) return 1;
    fseek(f, 0, SEEK_END);
    long len = ftell(f);
    fseek(f, 0, SEEK_SET);
    std::vector<char> buf(len + 1);
    size_t got = fread(buf.data(), 1, len, f);
    fclose(f);
    buf[got] = '\0';
    const char* p = buf.data();

    // Alphabet: A distinct upper-case letters.
    while (*p == ' ' || *p == '\n' || *p == '\r' || *p == '\t') ++p;
    const char* alphaStart = p;
    while (*p > 32) ++p;
    int A = (int)(p - alphaStart);
    int idx[256];
    for (int i = 0; i < 256; ++i) idx[i] = -1;
    for (int i = 0; i < A; ++i) idx[(unsigned char)alphaStart[i]] = i;

    std::vector<int> ins(A), del(A), sub(A * A);
    for (int i = 0; i < A; ++i) ins[i] = readInt(p);
    for (int i = 0; i < A; ++i) del[i] = readInt(p);
    for (int i = 0; i < A * A; ++i) sub[i] = readInt(p);

    int P = readInt(p);

    std::vector<int> s, t;
    std::vector<int> prevRow, curRow;

    long long total = 0;
    for (int pair = 0; pair < P; ++pair) {
        readToken(p, idx, s);
        readToken(p, idx, t);
        int n = (int)s.size();
        int m = (int)t.size();

        prevRow.resize(m + 1);
        curRow.resize(m + 1);

        int* pv = prevRow.data();
        int* cv = curRow.data();
        const int* sr = s.data();
        const int* tr = t.data();

        pv[0] = 0;
        for (int j = 1; j <= m; ++j) pv[j] = pv[j - 1] + ins[tr[j - 1]];

        for (int i = 0; i < n; ++i) {
            int d = del[sr[i]];
            const int* subrow = &sub[sr[i] * A];
            cv[0] = pv[0] + d;
            int diag = pv[0];
            for (int j = 1; j <= m; ++j) {
                int tj = tr[j - 1];
                int best = pv[j] + d;
                int v = cv[j - 1] + ins[tj];
                if (v < best) best = v;
                v = diag + subrow[tj];
                if (v < best) best = v;
                cv[j] = best;
                diag = pv[j];
            }
            int* tmp = pv; pv = cv; cv = tmp;
        }

        long long cost = pv[m];
        total += cost;
        std::printf("%lld\n", cost);
    }
    std::printf("total %lld\n", total);
    return 0;
}
