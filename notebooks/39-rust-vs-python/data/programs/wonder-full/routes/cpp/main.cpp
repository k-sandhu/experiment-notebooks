#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>
#include <intrin.h>

static inline int ctz64(uint64_t x) { unsigned long i; _BitScanForward64(&i, x); return (int)i; }

struct Edge {
    int32_t to;
    int32_t w;
};

static const char* bufPtr;
static const char* bufEnd;

static inline bool nextInt(int& out) {
    const char* p = bufPtr;
    while (p < bufEnd && *p <= ' ') ++p;
    if (p >= bufEnd) { bufPtr = p; return false; }
    bool neg = false;
    if (*p == '-') { neg = true; ++p; }
    int v = 0;
    while (p < bufEnd && *p >= '0' && *p <= '9') {
        v = v * 10 + (*p - '0');
        ++p;
    }
    bufPtr = p;
    out = neg ? -v : v;
    return true;
}

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    FILE* f = std::fopen(argv[1], "rb");
    if (!f) return 1;
    std::fseek(f, 0, SEEK_END);
    long sz = std::ftell(f);
    std::fseek(f, 0, SEEK_SET);
    if (sz < 0) sz = 0;
    std::string data;
    data.resize((size_t)sz);
    if (sz > 0) {
        size_t rd = std::fread(data.data(), 1, (size_t)sz, f);
        data.resize(rd);
    }
    std::fclose(f);
    bufPtr = data.data();
    bufEnd = data.data() + data.size();

    int N = 0, M = 0, Q = 0;
    if (!nextInt(N)) return 0;
    nextInt(M);
    nextInt(Q);
    if (N < 0) N = 0;
    if (M < 0) M = 0;
    if (Q < 0) Q = 0;

    std::vector<int> eu;
    std::vector<int> ev;
    std::vector<int> ew;
    eu.reserve(M);
    ev.reserve(M);
    ew.reserve(M);
    std::vector<int> deg((size_t)N, 0);
    int wmax = 0;
    for (int i = 0; i < M; ++i) {
        int u, v, w;
        nextInt(u); nextInt(v); nextInt(w);
        if (u == v) continue;
        if (u < 0 || u >= N || v < 0 || v >= N) continue;
        eu.push_back(u); ev.push_back(v); ew.push_back(w);
        ++deg[(size_t)u];
        ++deg[(size_t)v];
        if (w > wmax) wmax = w;
    }
    std::vector<int> sources((size_t)Q, 0);
    for (int i = 0; i < Q; ++i) {
        int s = 0;
        nextInt(s);
        sources[(size_t)i] = s;
    }
    data.clear();
    data.shrink_to_fit();

    // CSR
    std::vector<int> off((size_t)N + 1, 0);
    for (int i = 0; i < N; ++i) off[(size_t)i + 1] = off[(size_t)i] + deg[(size_t)i];
    int E = off[(size_t)N];
    std::vector<Edge> adj((size_t)E);
    std::vector<int> cursor(off.begin(), off.begin() + N);
    int mStored = (int)eu.size();
    for (int i = 0; i < mStored; ++i) {
        int u = eu[(size_t)i], v = ev[(size_t)i], w = ew[(size_t)i];
        adj[(size_t)cursor[(size_t)u]++] = Edge{v, w};
        adj[(size_t)cursor[(size_t)v]++] = Edge{u, w};
    }
    eu.clear(); eu.shrink_to_fit();
    ev.clear(); ev.shrink_to_fit();
    ew.clear(); ew.shrink_to_fit();
    deg.clear(); deg.shrink_to_fit();
    cursor.clear(); cursor.shrink_to_fit();

    const int B = (wmax > 0 ? wmax + 1 : 1);
    const int WORDS = (B + 63) >> 6;
    std::vector<int64_t> dist((size_t)N);
    std::vector<int> head((size_t)B);
    std::vector<uint64_t> bits((size_t)WORDS);
    std::vector<int> eNode;
    std::vector<int> eNext;
    size_t initCap = (size_t)(N > 1024 ? (size_t)N * 2 : 1024);
    eNode.resize(initCap);
    eNext.resize(initCap);

    const int64_t INF = (int64_t)4e18;
    std::string out;
    out.reserve((size_t)Q * 48);
    char line[160];

    // memo for duplicate sources
    std::vector<int> doneSrc;
    std::vector<std::string> doneLine;

    const int* offP = off.data();
    const Edge* adjP = adj.data();

    for (int qi = 0; qi < Q; ++qi) {
        int s = sources[(size_t)qi];
        bool dup = false;
        for (size_t k = 0; k < doneSrc.size(); ++k) {
            if (doneSrc[k] == s) { out += doneLine[k]; dup = true; break; }
        }
        if (dup) continue;

        int64_t R = 0, total = 0, far = 0;
        int farNode = s;

        if (s >= 0 && s < N) {
            std::fill(dist.begin(), dist.end(), INF);
            std::fill(head.begin(), head.end(), -1);
            std::fill(bits.begin(), bits.end(), 0ULL);
            int poolSize = 0;
            int nonEmpty = 0;
            int64_t* distP = dist.data();
            int* headP = head.data();
            uint64_t* bitsP = bits.data();

            distP[s] = 0;
            // push s into bucket 0
            {
                if ((size_t)poolSize == eNode.size()) {
                    size_t nc = eNode.size() ? eNode.size() * 2 : 1024;
                    eNode.resize(nc); eNext.resize(nc);
                }
                int idx = poolSize++;
                eNode[(size_t)idx] = s;
                eNext[(size_t)idx] = headP[0];
                if (headP[0] == -1) { bitsP[0] |= 1ULL; ++nonEmpty; }
                headP[0] = idx;
            }

            int curBucket = 0;
            int64_t curDist = 0;

            while (true) {
                if (headP[curBucket] == -1) {
                    if (nonEmpty == 0) break;
                    // find next non-empty bucket
                    int wi = curBucket >> 6;
                    int bi = curBucket & 63;
                    int pos = -1;
                    uint64_t w = 0;
                    if (bi < 63) w = bitsP[wi] & (~0ULL << (bi + 1));
                    if (w) {
                        pos = (wi << 6) + ctz64(w);
                    } else {
                        for (int step = 1; step <= WORDS; ++step) {
                            int idxw = wi + step;
                            if (idxw >= WORDS) idxw -= WORDS;
                            uint64_t ww = bitsP[idxw];
                            if (ww) { pos = (idxw << 6) + ctz64(ww); break; }
                        }
                    }
                    if (pos < 0) break;
                    int delta = pos > curBucket ? (pos - curBucket) : (pos - curBucket + B);
                    curDist += delta;
                    curBucket = pos;
                }
                int eidx = headP[curBucket];
                int u = eNode[(size_t)eidx];
                int nxt = eNext[(size_t)eidx];
                headP[curBucket] = nxt;
                if (nxt == -1) {
                    bitsP[curBucket >> 6] &= ~(1ULL << (curBucket & 63));
                    --nonEmpty;
                }
                if (distP[u] != curDist) continue;
                ++R;
                total += curDist;
                if (curDist > far) { far = curDist; farNode = u; }
                else if (curDist == far && u < farNode) { farNode = u; }

                int begin = offP[u];
                int end = offP[u + 1];
                for (int ei = begin; ei < end; ++ei) {
                    Edge e = adjP[ei];
                    int64_t nd = curDist + e.w;
                    if (nd < distP[e.to]) {
                        distP[e.to] = nd;
                        int b = curBucket + e.w;
                        if (b >= B) b -= B;
                        if ((size_t)poolSize == eNode.size()) {
                            size_t nc = eNode.size() ? eNode.size() * 2 : 1024;
                            eNode.resize(nc); eNext.resize(nc);
                        }
                        int idx = poolSize++;
                        eNode[(size_t)idx] = e.to;
                        int h = headP[b];
                        eNext[(size_t)idx] = h;
                        if (h == -1) { bitsP[b >> 6] |= (1ULL << (b & 63)); ++nonEmpty; }
                        headP[b] = idx;
                    }
                }
            }
        }

        int len = std::snprintf(line, sizeof(line), "%d %lld %lld %lld %d\n",
                                s, (long long)R, (long long)total, (long long)far, farNode);
        std::string ls(line, (size_t)len);
        out += ls;
        doneSrc.push_back(s);
        doneLine.push_back(std::move(ls));
    }

    std::fwrite(out.data(), 1, out.size(), stdout);
    return 0;
}
