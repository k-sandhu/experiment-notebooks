#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cstdint>
#include <string>
#include <vector>
#include <algorithm>

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    FILE* f = std::fopen(argv[1], "rb");
    if (!f) return 1;
    std::fseek(f, 0, SEEK_END);
    long fsize = std::ftell(f);
    std::fseek(f, 0, SEEK_SET);
    std::vector<uint8_t> buf((size_t)fsize + 1);
    size_t rd = fsize > 0 ? std::fread(buf.data(), 1, (size_t)fsize, f) : 0;
    std::fclose(f);
    buf.resize(rd);
    const uint8_t* d = buf.data();
    const size_t N = rd;
    size_t pos = 0;

    // Alphabet line: map letter -> index
    int charIdx[256];
    for (int i = 0; i < 256; i++) charIdx[i] = -1;
    int A = 0;
    while (pos < N && d[pos] != '\n') {
        uint8_t c = d[pos++];
        if (c >= 'A' && c <= 'Z') charIdx[c] = A++;
    }
    if (pos < N) pos++; // '\n'

    auto skipWs = [&]() {
        while (pos < N && (d[pos] == ' ' || d[pos] == '\n' || d[pos] == '\r' || d[pos] == '\t')) pos++;
    };
    auto parseInt = [&]() -> int {
        skipWs();
        int v = 0;
        while (pos < N && d[pos] >= '0' && d[pos] <= '9') v = v * 10 + (d[pos++] - '0');
        return v;
    };

    std::vector<int> ins(A), del(A), sub((size_t)A * A);
    for (int i = 0; i < A; i++) ins[i] = parseInt();
    for (int i = 0; i < A; i++) del[i] = parseInt();
    for (int i = 0; i < A * A; i++) sub[i] = parseInt();
    int P = parseInt();

    // Parse 2P string tokens into index bytes
    std::vector<std::vector<uint8_t>> strs;
    strs.reserve((size_t)2 * P);
    int maxLen = 0;
    for (int k = 0; k < 2 * P; k++) {
        skipWs();
        size_t start = pos;
        while (pos < N && d[pos] != ' ' && d[pos] != '\n' && d[pos] != '\r' && d[pos] != '\t') pos++;
        size_t len = pos - start;
        std::vector<uint8_t> s(len);
        for (size_t i = 0; i < len; i++) s[i] = (uint8_t)charIdx[d[start + i]];
        if ((int)len > maxLen) maxLen = (int)len;
        strs.push_back(std::move(s));
    }

    std::vector<int> prev((size_t)maxLen + 1), cur((size_t)maxLen + 1), insT(maxLen);
    int* prevP = prev.data();
    int* curP = cur.data();
    int* insTP = insT.data();
    const int* insP = ins.data();
    const int* delP = del.data();
    const int* subP = sub.data();

    std::string out;
    out.reserve((size_t)P * 12);
    long long total = 0;

    for (int p = 0; p < P; p++) {
        const std::vector<uint8_t>& sv = strs[2 * p];
        const std::vector<uint8_t>& tv = strs[2 * p + 1];
        const uint8_t* s = sv.data();
        const uint8_t* t = tv.data();
        int n = (int)sv.size();
        int m = (int)tv.size();

        for (int j = 0; j < m; j++) insTP[j] = insP[t[j]];

        prevP[0] = 0;
        for (int j = 0; j < m; j++) prevP[j + 1] = prevP[j] + insTP[j];

        for (int i = 0; i < n; i++) {
            int si = s[i];
            int dcost = delP[si];
            const int* subRow = subP + (size_t)si * A;
            int diag = prevP[0];
            int left = diag + dcost;
            curP[0] = left;
            for (int j = 0; j < m; j++) {
                int up = prevP[j + 1];
                int a = up + dcost;
                int b = left + insTP[j];
                int c = diag + subRow[t[j]];
                int v = a < b ? a : b;
                v = v < c ? v : c;
                diag = up;
                left = v;
                curP[j + 1] = v;
            }
            std::swap(prevP, curP);
        }
        int ans = prevP[m];
        total += ans;
        out.append(std::to_string(ans));
        out.push_back('\n');
    }
    out.append("total ");
    out.append(std::to_string(total));
    out.push_back('\n');
    std::fwrite(out.data(), 1, out.size(), stdout);
    return 0;
}
