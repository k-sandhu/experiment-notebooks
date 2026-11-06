#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include <algorithm>

using std::vector;

static inline bool isWs(unsigned char c) {
    return c == ' ' || c == '\n' || c == '\r' || c == '\t' || c == '\v' || c == '\f';
}

// Returns pointer to next token, sets len. Advances p. Returns nullptr at EOF.
static inline char* nextTok(char*& p, char* end, int& len) {
    while (p < end && isWs((unsigned char)*p)) ++p;
    if (p >= end) return nullptr;
    char* start = p;
    while (p < end && !isWs((unsigned char)*p)) ++p;
    len = (int)(p - start);
    return start;
}

static inline long long toInt(const char* s, int len) {
    long long v = 0;
    for (int i = 0; i < len; ++i) v = v * 10 + (s[i] - '0');
    return v;
}

static char* outBuf;
static size_t outPos;

static inline void writeInt(long long v) {
    char tmp[20];
    int k = 0;
    if (v == 0) tmp[k++] = '0';
    while (v > 0) { tmp[k++] = char('0' + v % 10); v /= 10; }
    while (k > 0) outBuf[outPos++] = tmp[--k];
    outBuf[outPos++] = '\n';
}

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    FILE* f = fopen(argv[1], "rb");
    if (!f) return 1;
    fseek(f, 0, SEEK_END);
    long sz = ftell(f);
    fseek(f, 0, SEEK_SET);
    vector<char> data(sz + 1);
    size_t rd = fread(data.data(), 1, sz, f);
    fclose(f);
    char* end = data.data() + rd;

    char* p = data.data();
    int len;
    char* tok = nextTok(p, end, len);
    int A = len;
    int charId[128];
    for (int i = 0; i < 128; ++i) charId[i] = -1;
    for (int i = 0; i < A; ++i) charId[(unsigned char)tok[i]] = i;

    vector<int> ins(A), del(A), sub(A * A);
    for (int i = 0; i < A; ++i) { tok = nextTok(p, end, len); ins[i] = (int)toInt(tok, len); }
    for (int i = 0; i < A; ++i) { tok = nextTok(p, end, len); del[i] = (int)toInt(tok, len); }
    for (int i = 0; i < A * A; ++i) { tok = nextTok(p, end, len); sub[i] = (int)toInt(tok, len); }
    tok = nextTok(p, end, len);
    int P = (int)toInt(tok, len);

    // Output buffer: each line at most ~7 digits; pairs lines + total.
    outBuf = (char*)malloc((size_t)P * 8 + 32);
    outPos = 0;

    vector<int> sIds, tIds;
    sIds.reserve(1100);
    tIds.reserve(1100);
    vector<int> prevRow(1101), curRow(1101);
    int* prev = prevRow.data();
    int* cur = curRow.data();

    long long total = 0;
    const int* subp = sub.data();
    const int* insp = ins.data();
    const int* delp = del.data();

    for (int q = 0; q < P; ++q) {
        tok = nextTok(p, end, len);
        int n = len;
        sIds.clear();
        for (int i = 0; i < n; ++i) sIds.push_back(charId[(unsigned char)tok[i]]);
        tok = nextTok(p, end, len);
        int m = len;
        tIds.clear();
        for (int j = 0; j < m; ++j) tIds.push_back(charId[(unsigned char)tok[j]]);
        const int* t = tIds.data();
        const int* s = sIds.data();

        prev[0] = 0;
        for (int j = 1; j <= m; ++j) prev[j] = prev[j - 1] + insp[t[j - 1]];
        for (int i = 0; i < n; ++i) {
            const int si = s[i];
            const int dc = delp[si];
            const int* subRow = subp + (size_t)si * A;
            int left = prev[0] + dc;
            cur[0] = left;
            const int* upRow = prev;
            const int* pv = prev;
            int diag = prev[0];
            for (int j = 1; j <= m; ++j) {
                const int tj = t[j - 1];
                int best = pv[j] + dc;                 // deletion
                const int l = left + insp[tj];         // insertion
                const int d = diag + subRow[tj];       // substitution
                if (l < best) best = l;
                if (d < best) best = d;
                cur[j] = best;
                left = best;
                diag = pv[j];
            }
            int* tmp = prev; prev = cur; cur = tmp;
        }
        long long cost = prev[m];
        total += cost;
        writeInt(cost);
    }

    memcpy(outBuf + outPos, "total ", 6);
    outPos += 6;
    writeInt(total);
    fwrite(outBuf, 1, outPos, stdout);
    return 0;
}
