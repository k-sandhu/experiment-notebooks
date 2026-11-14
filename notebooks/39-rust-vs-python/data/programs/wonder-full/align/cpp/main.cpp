#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>

static unsigned char* g_data;
static size_t g_len;
static size_t g_pos;

static inline bool isWs(unsigned char c) { return c == ' ' || c == '\n' || c == '\r' || c == '\t'; }

static inline void skipWs() { while (g_pos < g_len && isWs(g_data[g_pos])) ++g_pos; }

// returns token [start, start+len)
static inline void nextToken(size_t& start, size_t& len) {
    skipWs();
    start = g_pos;
    while (g_pos < g_len && !isWs(g_data[g_pos])) ++g_pos;
    len = g_pos - start;
}

static inline int nextInt() {
    skipWs();
    int v = 0;
    while (g_pos < g_len && g_data[g_pos] >= '0' && g_data[g_pos] <= '9') {
        v = v * 10 + (g_data[g_pos++] - '0');
    }
    return v;
}

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    FILE* f = std::fopen(argv[1], "rb");
    if (!f) return 1;
    std::fseek(f, 0, SEEK_END);
    long fsize = std::ftell(f);
    std::fseek(f, 0, SEEK_SET);
    g_data = (unsigned char*)std::malloc(fsize > 0 ? fsize : 1);
    g_len = std::fread(g_data, 1, fsize, f);
    std::fclose(f);
    g_pos = 0;

    size_t aStart, aLen;
    nextToken(aStart, aLen);
    int A = (int)aLen;
    int idx[256];
    for (int i = 0; i < 256; ++i) idx[i] = 0;
    for (int i = 0; i < A; ++i) idx[g_data[aStart + i]] = i;

    std::vector<int> ins(A), del(A), sub((size_t)A * A);
    for (int i = 0; i < A; ++i) ins[i] = nextInt();
    for (int i = 0; i < A; ++i) del[i] = nextInt();
    for (int i = 0; i < A * A; ++i) sub[i] = nextInt();
    int P = nextInt();

    std::vector<int> sIdx, tIdx, prevRow, currRow, colIns, subCols;
    std::string out;
    out.reserve((size_t)P * 8 + 32);
    char numBuf[32];
    long long total = 0;

    for (int p = 0; p < P; ++p) {
        size_t sStart, sLen, tStart, tLen;
        nextToken(sStart, sLen);
        nextToken(tStart, tLen);
        long long ans;
        if (sLen == tLen && std::memcmp(g_data + sStart, g_data + tStart, sLen) == 0) {
            ans = 0;
        } else {
            sIdx.resize(sLen);
            tIdx.resize(tLen);
            for (size_t i = 0; i < sLen; ++i) sIdx[i] = idx[g_data[sStart + i]];
            for (size_t i = 0; i < tLen; ++i) tIdx[i] = idx[g_data[tStart + i]];

            // columns = shorter string (transpose swaps ins/del and sub indices)
            const int* rowStr; const int* colStr;
            int R, C;
            const int* rowCost; const int* colCost;
            bool transposed;
            if ((int)tLen <= (int)sLen) {
                rowStr = sIdx.data(); colStr = tIdx.data(); R = (int)sLen; C = (int)tLen;
                rowCost = del.data(); colCost = ins.data(); transposed = false;
            } else {
                rowStr = tIdx.data(); colStr = sIdx.data(); R = (int)tLen; C = (int)sLen;
                rowCost = ins.data(); colCost = del.data(); transposed = true;
            }

            colIns.assign(C + 1, 0);
            for (int j = 0; j < C; ++j) colIns[j + 1] = colCost[colStr[j]];

            subCols.assign((size_t)A * C, 0);
            if (!transposed) {
                for (int a = 0; a < A; ++a) {
                    int* dst = &subCols[(size_t)a * C];
                    const int* srow = &sub[(size_t)a * A];
                    for (int j = 0; j < C; ++j) dst[j] = srow[colStr[j]];
                }
            } else {
                for (int b = 0; b < A; ++b) {
                    int* dst = &subCols[(size_t)b * C];
                    for (int j = 0; j < C; ++j) dst[j] = sub[(size_t)colStr[j] * A + b];
                }
            }

            prevRow.assign(C + 1, 0);
            currRow.assign(C + 1, 0);
            int* __restrict prev = prevRow.data();
            int* __restrict curr = currRow.data();
            const int* __restrict cins = colIns.data();
            for (int j = 1; j <= C; ++j) prev[j] = prev[j - 1] + cins[j];

            for (int i = 0; i < R; ++i) {
                int rc = rowStr[i];
                int d = rowCost[rc];
                const int* __restrict sc = &subCols[(size_t)rc * C];
                int left = prev[0] + d;
                curr[0] = left;
                int diag = prev[0];
                for (int j = 1; j <= C; ++j) {
                    int up = prev[j];
                    int best = diag + sc[j - 1];
                    int cand = up + d;
                    if (cand < best) best = cand;
                    cand = left + cins[j];
                    if (cand < best) best = cand;
                    curr[j] = best;
                    diag = up;
                    left = best;
                }
                int* tmp = prev; prev = curr; curr = tmp;
            }
            ans = prev[C];
        }
        total += ans;
        int n = std::snprintf(numBuf, sizeof(numBuf), "%lld\n", ans);
        out.append(numBuf, n);
    }
    int n = std::snprintf(numBuf, sizeof(numBuf), "total %lld\n", total);
    out.append(numBuf, n);
    std::fwrite(out.data(), 1, out.size(), stdout);
    return 0;
}
