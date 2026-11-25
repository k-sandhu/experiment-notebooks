// Shortest paths from each source with Dial's bucket queue. Edge weights are 1..1000, so a ring of
// 1024 buckets replaces a heap: the bucket of distance d is d & 1023 and nothing else is needed.
#include <fcntl.h>
#include <io.h>

#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>

namespace {

constexpr uint32_t kBuckets = 1024;  // greater than the largest weight (1000)
constexpr uint32_t kNil = 0xFFFFFFFFu;
constexpr int64_t kInf = INT64_MAX;

struct Arc {
    uint32_t to;
    uint32_t w;
};

struct Graph {
    std::vector<uint32_t> start;  // arcs of node v are arcs[start[v] .. start[v + 1])
    std::vector<Arc> arcs;
};

struct Answer {
    int64_t reached;
    int64_t total;
    int64_t far;
    uint32_t node;
};

class Scanner {
public:
    Scanner(const char* begin, const char* end) : p_(begin), end_(end) {}

    uint32_t next() {
        while (p_ < end_ && static_cast<unsigned>(*p_ - '0') > 9) ++p_;
        uint32_t x = 0;
        while (p_ < end_ && static_cast<unsigned>(*p_ - '0') <= 9) x = x * 10 + static_cast<uint32_t>(*p_++ - '0');
        return x;
    }

private:
    const char* p_;
    const char* end_;
};

std::vector<char> readFile(const char* path) {
    std::FILE* f = std::fopen(path, "rb");
    if (!f) {
        std::fprintf(stderr, "cannot open %s\n", path);
        std::exit(1);
    }
    std::fseek(f, 0, SEEK_END);
    const long size = std::ftell(f);
    std::rewind(f);
    std::vector<char> data(static_cast<size_t>(size));
    const size_t got = std::fread(data.data(), 1, data.size(), f);
    std::fclose(f);
    data.resize(got);
    return data;
}

// dist and buckets are scratch space reused for every source. A node can be queued several times;
// a queued copy is stale unless its node's final distance still equals the bucket's distance.
Answer solve(const Graph& g, uint32_t src, std::vector<int64_t>& dist, std::vector<uint32_t> (&buckets)[kBuckets]) {
    std::fill(dist.begin(), dist.end(), kInf);
    for (auto& cell : buckets) cell.clear();

    uint64_t pending = 0;
    dist[src] = 0;
    buckets[0].push_back(src);
    ++pending;

    Answer a{0, 0, 0, src};
    for (int64_t cur = 0; pending > 0; ++cur) {
        // Arcs have weight 1..1000, so nothing is pushed into the bucket being scanned.
        std::vector<uint32_t>& cell = buckets[static_cast<uint32_t>(cur) & (kBuckets - 1)];
        for (size_t i = 0; i < cell.size(); ++i) {
            const uint32_t v = cell[i];
            if (dist[v] != cur) continue;

            ++a.reached;
            a.total += cur;
            if (cur > a.far || (cur == a.far && v < a.node)) {
                a.far = cur;
                a.node = v;
            }
            const uint32_t end = g.start[v + 1];
            for (uint32_t k = g.start[v]; k < end; ++k) {
                const Arc arc = g.arcs[k];
                const int64_t nd = cur + arc.w;
                if (nd < dist[arc.to]) {
                    dist[arc.to] = nd;
                    buckets[static_cast<uint32_t>(nd) & (kBuckets - 1)].push_back(arc.to);
                    ++pending;
                }
            }
        }
        pending -= cell.size();
        cell.clear();
    }
    return a;
}

}  // namespace

int main(int argc, char** argv) {
    if (argc < 2) {
        std::fprintf(stderr, "usage: solution INPUT_PATH\n");
        return 1;
    }
    const std::vector<char> data = readFile(argv[1]);
    Scanner in(data.data(), data.data() + data.size());
    const uint32_t n = in.next();
    const uint32_t m = in.next();
    const uint32_t q = in.next();

    // Two passes over the edge lines: the first counts degrees, the second fills the adjacency arrays.
    // Parsing is cheaper than keeping three edge arrays alive.
    const Scanner edgesAt = in;
    Graph g;
    g.start.assign(static_cast<size_t>(n) + 1, 0);
    for (uint32_t i = 0; i < m; ++i) {
        ++g.start[in.next() + 1];
        ++g.start[in.next() + 1];
        in.next();
    }
    for (uint32_t v = 0; v < n; ++v) g.start[v + 1] += g.start[v];

    g.arcs.resize(2 * static_cast<size_t>(m));
    std::vector<uint32_t> fill(g.start.begin(), g.start.end() - 1);
    in = edgesAt;
    for (uint32_t i = 0; i < m; ++i) {
        const uint32_t u = in.next();
        const uint32_t v = in.next();
        const uint32_t w = in.next();
        g.arcs[fill[u]++] = Arc{v, w};
        g.arcs[fill[v]++] = Arc{u, w};
    }
    std::vector<uint32_t>().swap(fill);

    std::vector<int64_t> dist(n);
    std::vector<uint32_t> buckets[kBuckets];

    std::string out;
    char line[128];
    for (uint32_t k = 0; k < q; ++k) {
        const uint32_t s = in.next();
        const Answer a = solve(g, s, dist, buckets);
        const int len = std::snprintf(line, sizeof line, "%u %lld %lld %lld %u\n", s, static_cast<long long>(a.reached),
                                      static_cast<long long>(a.total), static_cast<long long>(a.far), a.node);
        out.append(line, static_cast<size_t>(len));
    }
    // Text mode would turn each LF into CR LF; the expected output uses plain LF.
    _setmode(_fileno(stdout), _O_BINARY);
    std::fwrite(out.data(), 1, out.size(), stdout);
    return 0;
}
