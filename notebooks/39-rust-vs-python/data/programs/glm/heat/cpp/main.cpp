#include <cstdio>
#include <cstdint>
#include <cstdlib>
#include <vector>
#include <io.h>
#include <fcntl.h>

using namespace std;

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    FILE* f = nullptr;
    if (fopen_s(&f, argv[1], "rb") != 0 || !f) return 1;
    fseek(f, 0, SEEK_END);
    long sz = ftell(f);
    fseek(f, 0, SEEK_SET);
    vector<char> buf((size_t)sz + 1);
    size_t rd = fread(buf.data(), 1, (size_t)sz, f);
    fclose(f);
    size_t p = 0;

    auto nextInt = [&]() -> long {
        while (p < rd && (buf[p] < '0' || buf[p] > '9') && buf[p] != '-') p++;
        bool neg = false;
        if (p < rd && buf[p] == '-') { neg = true; p++; }
        long v = 0;
        while (p < rd && buf[p] >= '0' && buf[p] <= '9') { v = v * 10 + (buf[p] - '0'); p++; }
        return neg ? -v : v;
    };

    const long H = nextInt();
    const long W = nextInt();
    const long S = nextInt();
    const size_t n = (size_t)H * (size_t)W;

    vector<int32_t> cur(n), nxt(n);
    vector<int32_t> iup(n), idown(n), ileft(n), iright(n);
    vector<char> wall(n);
    vector<uint32_t> openList;
    openList.reserve(n);

    // skip end of header line
    while (p < rd && buf[p] != '\n') p++;
    if (p < rd) p++;

    for (long r = 0; r < H; r++) {
        for (long c = 0; c < W; c++) {
            char ch = buf[p++];
            size_t i = (size_t)r * (size_t)W + (size_t)c;
            cur[i] = 0;
            if (ch == '#') {
                wall[i] = 1;
            } else if (ch >= '1' && ch <= '9') {
                cur[i] = 1000 * (ch - '0');
                wall[i] = 0;
            } else {
                wall[i] = 0;
                openList.push_back((uint32_t)i);
            }
        }
        while (p < rd && buf[p] != '\n') p++;
        if (p < rd) p++;
    }

    nxt = cur;  // sources keep their fixed value in the swap buffer

    // Precompute neighbor indices; wall / outside neighbour -> own index.
    for (uint32_t i : openList) {
        size_t r = i / (size_t)W, c = i % (size_t)W;
        iup[i]    = (r > 0     && !wall[i - (size_t)W]) ? (int32_t)(i - (size_t)W) : (int32_t)i;
        idown[i]  = (r + 1 < H && !wall[i + (size_t)W]) ? (int32_t)(i + (size_t)W) : (int32_t)i;
        ileft[i]  = (c > 0     && !wall[i - 1])         ? (int32_t)(i - 1)         : (int32_t)i;
        iright[i] = (c + 1 < W && !wall[i + 1])         ? (int32_t)(i + 1)         : (int32_t)i;
    }

    const int32_t* up = iup.data();
    const int32_t* dn = idown.data();
    const int32_t* lf = ileft.data();
    const int32_t* rt = iright.data();
    const uint32_t* cells = openList.data();
    const size_t m = openList.size();

    for (long s = 0; s < S; s++) {
        int32_t* __restrict cv = cur.data();
        int32_t* __restrict nv = nxt.data();
        for (size_t k = 0; k < m; k++) {
            const size_t i = cells[k];
            const int32_t v = cv[i];
            nv[i] = (4 * v + cv[up[i]] + cv[dn[i]] + cv[lf[i]] + cv[rt[i]]) >> 3;
        }
        cur.swap(nxt);
    }

    long long sum = 0, chk = 0;
    int32_t mx = -1;
    size_t mi = 0;
    for (size_t k = 0; k < m; k++) {
        const size_t i = cells[k];
        const int32_t v = cur[i];
        sum += v;
        chk += (long long)v * (long long)(i + 1);
        if (v > mx) { mx = v; mi = i; }
    }

    _setmode(_fileno(stdout), _O_BINARY);
    char out[128];
    int len = snprintf(out, sizeof out, "sum %lld\nmax %d %zu %zu\nchecksum %lld\n",
                       sum, (int)mx, mi / (size_t)W, mi % (size_t)W, chk);
    fwrite(out, 1, (size_t)len, stdout);
    return 0;
}
