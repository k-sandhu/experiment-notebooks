// Weighted edit distance for many pairs.
//
// Transformation used by the DP kernels: with Q[j] = sum of column (insert) costs of C[1..j],
// store E[i][j] = D[i][j] - Q[j]. Then
//   E[i][j] = min(E[i-1][j] + rc, E[i-1][j-1] + adj[j], E[i][j-1])
// where adj[j] = M[r][C_j] - cc[C_j]. The horizontal term becomes a plain running minimum,
// so the loop-carried dependency is a single min instead of add+min, and the vertical part
// vectorizes (SSE4.1 path: vertical step in SIMD + in-register prefix minimum).
#include <cstdio>
#include <cstdint>
#include <cstring>
#include <vector>
#include <string>
#include <algorithm>
#include <intrin.h>
#include <immintrin.h>
#include <io.h>
#include <fcntl.h>

using i64 = long long;

static int A;
static int insC[26], delC[26];
static int subM[26][26];   // sub[s][t]
static int subT[26][26];   // transposed

static bool hasSse41() {
    int r[4];
    __cpuid(r, 1);
    return (r[2] & (1 << 19)) != 0;
}
static const bool kSse41 = hasSse41();

// Scalar int32 kernel. row has m+1 entries; returns E[n][m].
static int dpScalar32(const uint8_t* R, int n, int m, const int* rc, const int* const* adjFor, int* row) {
    for (int j = 0; j <= m; ++j) row[j] = 0;
    for (int i = 0; i < n; ++i) {
        const int a = R[i];
        const int d = rc[a];
        const int* adj = adjFor[a];
        int diag = row[0];
        int left = diag + d;
        row[0] = left;
        for (int j = 1; j <= m; ++j) {
            int up = row[j];
            int v = std::min(up + d, diag + adj[j]);
            v = std::min(v, left);
            row[j] = v;
            left = v;
            diag = up;
        }
    }
    return row[m];
}

// SSE4.1 int32 kernel using two row buffers (prev, cur) of size m+1 padded to a multiple of 4 (+4).
static int dpSse32(const uint8_t* R, int n, int m, const int* rc, const int* const* adjFor, int* prev, int* cur) {
    // Layout: buf[0] = column 0, buf[1..m] = columns. Vector blocks cover j = 1..m in steps of 4,
    // reading prev[j-1..j+2] (unaligned) and prev[j..j+3].
    const int mv = (m + 3) & ~3;
    for (int j = 0; j <= mv; ++j) prev[j] = 0;
    const __m128i INF = _mm_set1_epi32(0x3fffffff);
    for (int i = 0; i < n; ++i) {
        const int a = R[i];
        const int d = rc[a];
        const int* adj = adjFor[a];
        const __m128i dv = _mm_set1_epi32(d);
        int c0 = prev[0] + d;
        cur[0] = c0;
        __m128i carry = _mm_set1_epi32(c0);
        for (int j = 1; j <= mv; j += 4) {
            __m128i up = _mm_loadu_si128((const __m128i*)(prev + j));
            __m128i dg = _mm_loadu_si128((const __m128i*)(prev + j - 1));
            __m128i ad = _mm_loadu_si128((const __m128i*)(adj + j));
            __m128i x = _mm_min_epi32(_mm_add_epi32(up, dv), _mm_add_epi32(dg, ad));
            // in-register prefix min, shifting in +INF
            x = _mm_min_epi32(x, _mm_alignr_epi8(x, INF, 12));
            x = _mm_min_epi32(x, _mm_alignr_epi8(x, INF, 8));
            x = _mm_min_epi32(x, carry);
            _mm_storeu_si128((__m128i*)(cur + j), x);
            carry = _mm_shuffle_epi32(x, 0xFF);
        }
        std::swap(prev, cur);
    }
    return prev[m];
}

// Scalar int64 fallback for extremely long strings (values could exceed int32).
static i64 dpScalar64(const uint8_t* R, int n, int m, const int* rc, const int* const* adjFor) {
    std::vector<i64> row(m + 1, 0);
    for (int i = 0; i < n; ++i) {
        const int a = R[i];
        const i64 d = rc[a];
        const int* adj = adjFor[a];
        i64 diag = row[0];
        i64 left = diag + d;
        row[0] = left;
        for (int j = 1; j <= m; ++j) {
            i64 up = row[j];
            i64 v = std::min(up + d, diag + adj[j]);
            v = std::min(v, left);
            row[j] = v;
            left = v;
            diag = up;
        }
    }
    return row[m];
}

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    FILE* f = std::fopen(argv[1], "rb");
    if (!f) return 1;
    std::fseek(f, 0, SEEK_END);
    long sz = std::ftell(f);
    std::fseek(f, 0, SEEK_SET);
    std::vector<char> buf((size_t)sz + 1);
    size_t got = std::fread(buf.data(), 1, (size_t)sz, f);
    std::fclose(f);
    buf[got] = 0;
    const char* p = buf.data();
    const char* end = p + got;

    int8_t idx[256];
    std::memset(idx, -1, sizeof idx);
    A = 0;
    while (p < end && *p >= 'A' && *p <= 'Z') idx[(uint8_t)*p++] = (int8_t)A++;

    auto readInt = [&]() -> i64 {
        while (p < end && (*p < '0' || *p > '9') && *p != '-') ++p;
        bool neg = false;
        if (*p == '-') { neg = true; ++p; }
        i64 v = 0;
        while (p < end && *p >= '0' && *p <= '9') v = v * 10 + (*p++ - '0');
        return neg ? -v : v;
    };
    for (int i = 0; i < A; ++i) insC[i] = (int)readInt();
    for (int i = 0; i < A; ++i) delC[i] = (int)readInt();
    for (int i = 0; i < A; ++i)
        for (int j = 0; j < A; ++j) { subM[i][j] = (int)readInt(); subT[j][i] = subM[i][j]; }
    i64 P = readInt();

    std::vector<uint8_t> sBuf, tBuf;
    std::vector<int> adjStore, rowA, rowB;
    std::string out;
    out.reserve((size_t)P * 12 + 32);
    i64 total = 0;
    char num[32];

    auto readWord = [&](std::vector<uint8_t>& w) {
        while (p < end && (*p < 'A' || *p > 'Z')) ++p;
        const char* q = p;
        while (p < end && *p >= 'A' && *p <= 'Z') ++p;
        w.resize(p - q);
        for (size_t k = 0; k < w.size(); ++k) w[k] = (uint8_t)idx[(uint8_t)q[k]];
    };

    for (i64 k = 0; k < P; ++k) {
        readWord(sBuf);
        readWord(tBuf);
        const uint8_t* R; const uint8_t* C;
        int n, m;
        const int* rc; const int* cc;
        int (*M)[26];
        // Put the longer string on the inner (column) axis. Transposing the problem swaps the
        // roles of insert/delete and transposes the substitution table; D[n][m] is unchanged.
        if (sBuf.size() <= tBuf.size()) {
            R = sBuf.data(); n = (int)sBuf.size(); C = tBuf.data(); m = (int)tBuf.size();
            rc = delC; cc = insC; M = subM;
        } else {
            R = tBuf.data(); n = (int)tBuf.size(); C = sBuf.data(); m = (int)sBuf.size();
            rc = insC; cc = delC; M = subT;
        }

        const int stride = ((m + 1) + 8) & ~3;
        bool used[26] = {};
        int nUsed = 0;
        for (int i = 0; i < n; ++i) if (!used[R[i]]) { used[R[i]] = true; ++nUsed; }
        adjStore.resize((size_t)stride * nUsed);
        const int* adjFor[26] = {};
        i64 Q = 0;
        for (int j = 0; j < m; ++j) Q += cc[C[j]];
        {
            int slot = 0;
            for (int a = 0; a < A; ++a) {
                if (!used[a]) continue;
                int* row = adjStore.data() + (size_t)stride * slot++;
                const int* Ma = M[a];
                row[0] = 0;
                for (int j = 0; j < m; ++j) row[j + 1] = Ma[C[j]] - cc[C[j]];
                for (int j = m + 1; j < stride; ++j) row[j] = 0;
                adjFor[a] = row;
            }
        }

        i64 cost;
        if ((i64)(n + m + 4) * 1000 < (1LL << 30)) {
            if ((size_t)rowA.size() < (size_t)stride) { rowA.resize(stride); rowB.resize(stride); }
            int e = kSse41 ? dpSse32(R, n, m, rc, adjFor, rowA.data(), rowB.data())
                           : dpScalar32(R, n, m, rc, adjFor, rowA.data());
            cost = (i64)e + Q;
        } else {
            cost = dpScalar64(R, n, m, rc, adjFor) + Q;
        }
        total += cost;
        int len = std::snprintf(num, sizeof num, "%lld\n", cost);
        out.append(num, len);
    }
    out += "total ";
    out += std::to_string(total);
    out += '\n';
    _setmode(_fileno(stdout), _O_BINARY);
    std::fwrite(out.data(), 1, out.size(), stdout);
    return 0;
}
