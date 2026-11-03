#include <cstdio>
#include <cstdlib>
#include <cstdint>
#include <vector>
#include <string>
#include <algorithm>
#include <io.h>
#include <fcntl.h>

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    FILE* f = std::fopen(argv[1], "rb");
    if (!f) return 1;
    std::fseek(f, 0, SEEK_END);
    long sz = std::ftell(f);
    std::fseek(f, 0, SEEK_SET);
    std::vector<char> buf(sz + 1);
    sz = (long)std::fread(buf.data(), 1, sz, f);
    std::fclose(f);
    buf[sz] = 0;
    const char* p = buf.data();
    const char* end = p + sz;

    auto skipWs = [&]() { while (p < end && (unsigned char)*p <= ' ') ++p; };
    auto nextInt = [&]() -> int {
        skipWs();
        int v = 0;
        while (p < end && *p >= '0' && *p <= '9') v = v * 10 + (*p++ - '0');
        return v;
    };

    skipWs();
    int code[256];
    for (int& c : code) c = 0;
    int A = 0;
    while (p < end && *p > ' ') code[(unsigned char)*p++] = A++;
    std::vector<int> ins(A), del(A), sub(A * A + 1, 0);
    for (int i = 0; i < A; i++) ins[i] = nextInt();
    for (int i = 0; i < A; i++) del[i] = nextInt();
    for (int i = 0; i < A; i++)
        for (int j = 0; j < A; j++) sub[i * A + j] = nextInt();
    int P = nextInt();

    std::vector<int> prev, cur, tc, insT;
    std::string out;
    long long total = 0;
    for (int q = 0; q < P; q++) {
        skipWs();
        const char* s = p;
        while (p < end && *p > ' ') ++p;
        int n = (int)(p - s);
        skipWs();
        const char* t = p;
        while (p < end && *p > ' ') ++p;
        int m = (int)(p - t);

        tc.resize(m + 1);
        insT.resize(m + 1);
        prev.resize(m + 1);
        cur.resize(m + 1);
        for (int j = 1; j <= m; j++) {
            int c = code[(unsigned char)t[j - 1]];
            tc[j] = c;
            insT[j] = ins[c];
        }
        prev[0] = 0;
        for (int j = 1; j <= m; j++) prev[j] = prev[j - 1] + insT[j];
        int* pv = prev.data();
        int* cu = cur.data();
        const int* ti = tc.data();
        const int* it = insT.data();
        for (int i = 1; i <= n; i++) {
            int a = code[(unsigned char)s[i - 1]];
            int d = del[a];
            const int* sr = &sub[a * A];
            int left = pv[0] + d;
            cu[0] = left;
            for (int j = 1; j <= m; j++) {
                int v = std::min(pv[j] + d, pv[j - 1] + sr[ti[j]]);
                left = std::min(v, left + it[j]);
                cu[j] = left;
            }
            std::swap(pv, cu);
        }
        long long r = pv[m];
        total += r;
        out += std::to_string(r);
        out += '\n';
    }
    out += "total " + std::to_string(total) + "\n";
    _setmode(_fileno(stdout), _O_BINARY);
    std::fwrite(out.data(), 1, out.size(), stdout);
    return 0;
}
