#include <cstdio>
#include <cstdint>
#include <vector>
#include <string>
#include <utility>
#include <io.h>
#include <fcntl.h>

using namespace std;

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    _setmode(_fileno(stdout), _O_BINARY);

    FILE* f = fopen(argv[1], "rb");
    if (!f) return 1;
    fseek(f, 0, SEEK_END);
    long size = ftell(f);
    fseek(f, 0, SEEK_SET);
    string data;
    data.resize(size + 1);
    fread(&data[0], 1, size, f);
    fclose(f);
    data[size] = '\0';
    const char* p = data.data();

    auto isSpace = [](char c) {
        return c == ' ' || c == '\n' || c == '\r' || c == '\t' || c == '\f' || c == '\v';
    };
    auto skip = [&]() { while (isSpace(*p)) ++p; };

    auto readInt = [&]() -> long long {
        skip();
        bool neg = false;
        if (*p == '-') { neg = true; ++p; }
        long long v = 0;
        while (*p >= '0' && *p <= '9') { v = v * 10 + (*p - '0'); ++p; }
        return neg ? -v : v;
    };

    auto readToken = [&]() -> string {
        skip();
        const char* start = p;
        while (*p && !isSpace(*p)) ++p;
        return string(start, (size_t)(p - start));
    };

    string alphabet = readToken();
    int A = (int)alphabet.size();

    int charIndex[26];
    for (int i = 0; i < 26; ++i) charIndex[i] = -1;
    for (int i = 0; i < A; ++i) charIndex[alphabet[i] - 'A'] = i;

    vector<long long> ins(A), del(A);
    for (int i = 0; i < A; ++i) ins[i] = readInt();
    for (int i = 0; i < A; ++i) del[i] = readInt();
    vector<vector<long long>> sub(A, vector<long long>(A));
    for (int i = 0; i < A; ++i)
        for (int j = 0; j < A; ++j)
            sub[i][j] = readInt();

    long long P = readInt();

    vector<long long> prev, cur;
    vector<int> sIdx, tIdx, insT;

    long long total = 0;
    for (long long pair = 0; pair < P; ++pair) {
        string s = readToken();
        string t = readToken();
        int n = (int)s.size(), m = (int)t.size();

        sIdx.resize(n);
        for (int i = 0; i < n; ++i) sIdx[i] = charIndex[s[i] - 'A'];
        tIdx.resize(m);
        insT.resize(m);
        for (int j = 0; j < m; ++j) { tIdx[j] = charIndex[t[j] - 'A']; insT[j] = ins[tIdx[j]]; }

        if ((int)prev.size() < m + 1) { prev.resize(m + 1); cur.resize(m + 1); }

        prev[0] = 0;
        for (int j = 1; j <= m; ++j) prev[j] = prev[j - 1] + insT[j - 1];

        for (int i = 1; i <= n; ++i) {
            int si = sIdx[i - 1];
            long long delSi = del[si];
            const long long* subRow = sub[si].data();
            long long* prevPtr = prev.data();
            long long* curPtr = cur.data();
            curPtr[0] = prevPtr[0] + delSi;
            for (int j = 1; j <= m; ++j) {
                int tj = tIdx[j - 1];
                long long up = prevPtr[j] + delSi;
                long long left = curPtr[j - 1] + insT[j - 1];
                long long diag = prevPtr[j - 1] + subRow[tj];
                long long best = up < left ? up : left;
                curPtr[j] = diag < best ? diag : best;
            }
            swap(prev, cur);
        }

        long long cost = prev[m];
        total += cost;
        printf("%lld\n", cost);
    }
    printf("total %lld\n", total);
    return 0;
}
