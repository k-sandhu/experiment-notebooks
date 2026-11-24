#include <cstdio>
#include <cstdlib>
#include <cstdint>
#include <vector>

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    FILE* f = nullptr;
    if (fopen_s(&f, argv[1], "rb") != 0 || !f) return 1;
    fseek(f, 0, SEEK_END);
    long fsize = ftell(f);
    fseek(f, 0, SEEK_SET);
    std::vector<unsigned char> buf((size_t)fsize + 1);
    if (fsize > 0) fread(buf.data(), 1, (size_t)fsize, f);
    fclose(f);
    size_t p = 0, n = (size_t)fsize;
    auto parseInt = [&]() -> int {
        while (p < n && (buf[p] < '0' || buf[p] > '9') && buf[p] != '-') p++;
        int v = 0;
        while (p < n && buf[p] >= '0' && buf[p] <= '9') { v = v * 10 + (buf[p] - '0'); p++; }
        return v;
    };
    int H = parseInt(), W = parseInt(), S = parseInt();
    // skip to end of first line
    while (p < n && buf[p] != '\n') p++;
    if (p < n) p++;
    int N = H * W;
    std::vector<int> cur((size_t)N, 0), nxt((size_t)N, 0);
    std::vector<unsigned char> kind((size_t)N, 0);
    for (int r = 0; r < H; r++) {
        // skip possible \r\n already handled; ensure at row start
        while (p < n && (buf[p] == '\r' || buf[p] == '\n')) p++;
        for (int c = 0; c < W; c++) {
            unsigned char ch = (p < n ? buf[p++] : (unsigned char)'.');
            int i = r * W + c;
            if (ch == '#') kind[i] = 0;
            else if (ch == '.') kind[i] = 1;
            else { kind[i] = 2; int v = 1000 * (ch - '0'); cur[i] = v; nxt[i] = v; }
        }
    }
    std::vector<int> openIdx; openIdx.reserve(N);
    std::vector<int> runStart; std::vector<int> runLen;
    std::vector<int> eIdx, eU, eD, eL, eR;
    for (int r = 0; r < H; r++) {
        int c = 0;
        while (c < W) {
            int i = r * W + c;
            if (kind[i] != 1) { c++; continue; }
            bool fast = r > 0 && r + 1 < H && c > 0 && c + 1 < W
                && kind[i - W] != 0 && kind[i + W] != 0 && kind[i - 1] != 0 && kind[i + 1] != 0;
            if (fast) {
                int start = i; int len = 0;
                while (c < W) {
                    int j = r * W + c;
                    if (kind[j] != 1) break;
                    if (!(r > 0 && r + 1 < H && c > 0 && c + 1 < W && kind[j - W] != 0 && kind[j + W] != 0 && kind[j - 1] != 0 && kind[j + 1] != 0)) break;
                    openIdx.push_back(j);
                    len++; c++;
                }
                runStart.push_back(start); runLen.push_back(len);
            } else {
                openIdx.push_back(i);
                int up = (r > 0 && kind[i - W] != 0) ? i - W : i;
                int dn = (r + 1 < H && kind[i + W] != 0) ? i + W : i;
                int lf = (c > 0 && kind[i - 1] != 0) ? i - 1 : i;
                int rt = (c + 1 < W && kind[i + 1] != 0) ? i + 1 : i;
                eIdx.push_back(i); eU.push_back(up); eD.push_back(dn); eL.push_back(lf); eR.push_back(rt);
                c++;
            }
        }
    }
    int* curP = cur.data(); int* nxtP = nxt.data();
    int* rs = runStart.data(); int* rl = runLen.data();
    int nRuns = (int)runStart.size();
    int* ei = eIdx.data(); int* eu = eU.data(); int* ed = eD.data(); int* el = eL.data(); int* er = eR.data();
    int nEdge = (int)eIdx.size();
    for (int step = 0; step < S; step++) {
        for (int ri = 0; ri < nRuns; ri++) {
            int start = rs[ri]; int len = rl[ri];
            // manual loop, compiler vectorizes sequential stencil
            for (int k = 0; k < len; k++) {
                int i = start + k;
                int old = curP[i];
                nxtP[i] = ((old << 2) + curP[i - W] + curP[i + W] + curP[i - 1] + curP[i + 1]) >> 3;
            }
        }
        for (int k = 0; k < nEdge; k++) {
            int i = ei[k];
            int old = curP[i];
            nxtP[i] = ((old << 2) + curP[eu[k]] + curP[ed[k]] + curP[el[k]] + curP[er[k]]) >> 3;
        }
        int* tmp = curP; curP = nxtP; nxtP = tmp;
    }
    long long sum = 0, checksum = 0;
    int best = -1, bestIdx = openIdx.empty() ? 0 : openIdx[0];
    for (size_t k = 0; k < openIdx.size(); k++) {
        int i = openIdx[k]; int v = curP[i];
        sum += v; checksum += (long long)v * (long long)(i + 1);
        if (v > best) { best = v; bestIdx = i; }
    }
    int br = W ? bestIdx / W : 0, bc = W ? bestIdx % W : 0;
    printf("sum %lld\nmax %d %d %d\nchecksum %lld\n", sum, best, br, bc, checksum);
    return 0;
}
