#include <cstdio>
#include <cstdint>
#include <cstring>
#include <vector>
#include <io.h>
#include <fcntl.h>

using std::vector;

static vector<char> readAll(const char* path) {
    FILE* f = nullptr;
    if (fopen_s(&f, path, "rb") != 0 || !f) {
        std::fprintf(stderr, "cannot open input\n");
        std::exit(1);
    }
    std::fseek(f, 0, SEEK_END);
    long sz = std::ftell(f);
    std::fseek(f, 0, SEEK_SET);
    vector<char> buf((size_t)sz);
    if (sz > 0 && std::fread(buf.data(), 1, (size_t)sz, f) != (size_t)sz) {
        std::fclose(f);
        std::fprintf(stderr, "read error\n");
        std::exit(1);
    }
    std::fclose(f);
    return buf;
}

static inline bool isWs(unsigned char c) {
    return c == ' ' || c == '\n' || c == '\r' || c == '\t';
}

struct Scanner {
    const char* p;
    const char* e;
    const char* tok;
    int tokLen;

    void skip() {
        while (p < e && isWs((unsigned char)*p)) ++p;
    }
    int64_t nextInt() {
        skip();
        bool neg = false;
        if (p < e && (*p == '-' || *p == '+')) {
            neg = (*p == '-');
            ++p;
        }
        int64_t v = 0;
        while (p < e && *p >= '0' && *p <= '9') {
            v = v * 10 + (*p - '0');
            ++p;
        }
        return neg ? -v : v;
    }
    void nextToken() {
        skip();
        tok = p;
        while (p < e && !isWs((unsigned char)*p)) ++p;
        tokLen = (int)(p - tok);
    }
};

int main(int argc, char** argv) {
    if (argc < 2) {
        std::fprintf(stderr, "usage: solution INPUT_PATH\n");
        return 1;
    }
    vector<char> buf = readAll(argv[1]);
    Scanner sc{buf.data(), buf.data() + buf.size(), nullptr, 0};

    sc.nextToken();
    const int A = sc.tokLen;
    int idx[256];
    for (int i = 0; i < 256; ++i) idx[i] = -1;
    for (int i = 0; i < A; ++i) idx[(unsigned char)sc.tok[i]] = i;

    int ins[26], del[26], sub[26][26];
    for (int i = 0; i < A; ++i) ins[i] = (int)sc.nextInt();
    for (int i = 0; i < A; ++i) del[i] = (int)sc.nextInt();
    for (int i = 0; i < A; ++i)
        for (int j = 0; j < A; ++j) sub[i][j] = (int)sc.nextInt();

    const int64_t P = sc.nextInt();
    _setmode(_fileno(stdout), _O_BINARY);

    vector<int32_t> tIdx, insT;
    vector<int32_t> row(1, 0);
    vector<char> out;
    out.reserve((size_t)P * 16 + 32);
    int64_t total = 0;

    char tmp[24];
    auto appendInt = [&](int64_t v) {
        int k = 0;
        if (v < 0) {
            out.push_back('-');
            v = -v;
        }
        if (v == 0) tmp[k++] = '0';
        while (v > 0) {
            tmp[k++] = char('0' + v % 10);
            v /= 10;
        }
        while (k > 0) out.push_back(tmp[--k]);
    };

    for (int64_t q = 0; q < P; ++q) {
        sc.nextToken();
        const char* s = sc.tok;
        const int n = sc.tokLen;
        sc.nextToken();
        const char* t = sc.tok;
        const int m = sc.tokLen;

        if ((int)row.size() < m + 1) row.resize(m + 1);
        tIdx.resize(m);
        insT.resize(m);
        for (int j = 0; j < m; ++j) {
            int c = idx[(unsigned char)t[j]];
            tIdx[j] = (int32_t)c;
            insT[j] = (int32_t)ins[c];
        }

        int32_t* r = row.data();
        r[0] = 0;
        for (int j = 0; j < m; ++j) r[j + 1] = r[j] + insT[j];

        for (int i = 0; i < n; ++i) {
            const int si = idx[(unsigned char)s[i]];
            const int32_t dl = del[si];
            const int32_t* subr = sub[si];
            int32_t diag = r[0];
            r[0] = diag + dl;
            for (int j = 0; j < m; ++j) {
                const int32_t up = r[j + 1];
                int32_t v = up + dl;
                int32_t x = r[j] + insT[j];
                if (x < v) v = x;
                x = diag + subr[tIdx[j]];
                if (x < v) v = x;
                r[j + 1] = v;
                diag = up;
            }
        }

        const int64_t cost = row[m];
        total += cost;
        appendInt(cost);
        out.push_back('\n');
    }
    out.push_back('t');
    out.push_back('o');
    out.push_back('t');
    out.push_back('a');
    out.push_back('l');
    out.push_back(' ');
    appendInt(total);
    out.push_back('\n');
    std::fwrite(out.data(), 1, out.size(), stdout);
    return 0;
}
