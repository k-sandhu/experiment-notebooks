#include <algorithm>
#include <array>
#include <bit>
#include <cstdint>
#include <cstdio>
#include <fstream>
#include <limits>
#include <vector>

struct Scanner {
    std::vector<unsigned char> data;
    size_t pos = 0;
    explicit Scanner(const char* path) {
        std::ifstream f(path, std::ios::binary | std::ios::ate);
        const size_t size = static_cast<size_t>(f.tellg());
        data.resize(size + 1);
        f.seekg(0);
        f.read(reinterpret_cast<char*>(data.data()), size);
        data[size] = 0;
    }
    int read() {
        while (data[pos] <= ' ') ++pos;
        int x = 0;
        do { x = x * 10 + data[pos++] - '0'; }
        while (data[pos] >= '0' && data[pos] <= '9');
        return x;
    }
};

// Queued distances span at most 1,000, so each circular bucket has one key.
struct Queue {
    std::array<int, 1024> head;
    std::array<uint32_t, 32> bits{};
    uint32_t summary = 0;
    int current = 0;
    std::vector<int> next, prev;
    explicit Queue(int n) : next(n), prev(n) { head.fill(-1); }
    void reset() { head.fill(-1); bits.fill(0); summary = 0; current = 0; }
    void insert(int v, int b) {
        int h = head[b]; next[v] = h; prev[v] = -1;
        if (h >= 0) prev[h] = v;
        else { bits[b >> 5] |= uint32_t(1) << (b & 31); summary |= uint32_t(1) << (b >> 5); }
        head[b] = v;
    }
    void remove(int v, int b) {
        int p = prev[v], n = next[v];
        if (p >= 0) next[p] = n; else head[b] = n;
        if (n >= 0) prev[n] = p;
        if (head[b] < 0) {
            auto& word = bits[b >> 5];
            word &= ~(uint32_t(1) << (b & 31));
            if (!word) summary &= ~(uint32_t(1) << (b >> 5));
        }
    }
    int pop() {
        int b = current;
        if (head[b] < 0) {
            int g = b >> 5;
            uint32_t word = bits[g] & (UINT32_MAX << (b & 31));
            if (!word) {
                uint32_t groups = summary & (uint32_t(0xfffffffe) << g);
                if (!groups) groups = summary;
                g = std::countr_zero(groups); word = bits[g];
            }
            current = b = (g << 5) + std::countr_zero(word);
        }
        int v = head[b]; remove(v, b); return v;
    }
};

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    Scanner in(argv[1]);
    const int n = in.read(), m = in.read(), q = in.read();
    const size_t edgeStart = in.pos;
    std::vector<int> offset(n + 1, 0);
    for (int i = 0; i < m; ++i) {
        int u = in.read(), v = in.read(); in.read();
        if (u != v) { ++offset[u + 1]; ++offset[v + 1]; }
    }
    for (int i = 1; i <= n; ++i) offset[i] += offset[i - 1];
    std::vector<int> to(offset[n]);
    std::vector<uint16_t> weight(offset[n]);
    Queue queue(n);
    std::copy_n(offset.begin(), n, queue.next.begin());
    in.pos = edgeStart;
    for (int i = 0; i < m; ++i) {
        int u = in.read(), v = in.read(), w = in.read();
        if (u == v) continue;
        int a = queue.next[u]++, b = queue.next[v]++;
        to[a] = v; weight[a] = static_cast<uint16_t>(w);
        to[b] = u; weight[b] = static_cast<uint16_t>(w);
    }
    std::vector<int> sources(q);
    for (auto& s : sources) s = in.read();
    std::vector<unsigned char>().swap(in.data);
    constexpr int64_t INF = std::numeric_limits<int64_t>::max();
    std::vector<int64_t> dist(n);
    for (int s : sources) {
        std::fill(dist.begin(), dist.end(), INF);
        queue.reset(); dist[s] = 0; queue.insert(s, 0);
        int64_t reached = 0, total = 0, far = 0;
        int farNode = s;
        while (queue.summary) {
            int u = queue.pop();
            int64_t d = dist[u]; ++reached; total += d;
            if (d > far) { far = d; farNode = u; }
            else if (d == far && u < farNode) farNode = u;
            for (int e = offset[u]; e < offset[u + 1]; ++e) {
                int v = to[e];
                int64_t nd = d + weight[e], old = dist[v];
                if (nd >= old) continue;
                if (old != INF) queue.remove(v, static_cast<int>(old & 1023));
                dist[v] = nd; queue.insert(v, static_cast<int>(nd & 1023));
            }
        }
        std::printf("%d %lld %lld %lld %d\n", s, static_cast<long long>(reached),
                    static_cast<long long>(total), static_cast<long long>(far), farNode);
    }
}
