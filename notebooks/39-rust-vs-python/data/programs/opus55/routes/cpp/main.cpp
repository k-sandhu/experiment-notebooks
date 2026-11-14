// Routes: multi-source (one at a time) Dijkstra with a monotone radix heap on a CSR graph.
#include <bit>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fcntl.h>
#include <io.h>
#include <string>
#include <vector>

namespace {

struct Edge {
    uint32_t to;
    uint32_t w;
};

struct Parser {
    const unsigned char* p;
    uint64_t next() {
        while (*p < '0' || *p > '9') ++p;
        uint64_t x = *p++ - '0';
        while (*p >= '0' && *p <= '9') x = x * 10 + (*p++ - '0');
        return x;
    }
};

// Monotone radix heap. Keys are packed (dist << shift) | node; buckets are chosen by dist only.
class RadixHeap {
public:
    explicit RadixHeap(int shift) : shift_(shift) {}

    void reset() {
        for (auto& b : buckets_) b.clear();
        size_ = 0;
        last_ = 0;
    }
    bool empty() const { return size_ == 0; }

    void push(uint64_t key) {
        uint64_t d = key >> shift_;
        buckets_[bucketOf(d)].push_back(key);
        ++size_;
    }

    uint64_t pop() {
        if (buckets_[0].empty()) {
            int i = 1;
            while (buckets_[i].empty()) ++i;
            auto& b = buckets_[i];
            uint64_t mn = UINT64_MAX;
            for (uint64_t k : b)
                if (k < mn) mn = k;
            last_ = mn >> shift_;
            for (uint64_t k : b) buckets_[bucketOf(k >> shift_)].push_back(k);
            b.clear();
        }
        --size_;
        uint64_t k = buckets_[0].back();
        buckets_[0].pop_back();
        return k;
    }

private:
    int bucketOf(uint64_t d) const { return d == last_ ? 0 : 64 - std::countl_zero(d ^ last_); }

    std::vector<uint64_t> buckets_[65];
    size_t size_ = 0;
    uint64_t last_ = 0;
    int shift_;
};

}  // namespace

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    FILE* f = std::fopen(argv[1], "rb");
    if (!f) return 1;
    std::fseek(f, 0, SEEK_END);
    long long len = _ftelli64(f);
    std::fseek(f, 0, SEEK_SET);
    std::vector<unsigned char> buf(static_cast<size_t>(len) + 16, 0);
    size_t got = std::fread(buf.data(), 1, static_cast<size_t>(len), f);
    std::fclose(f);
    buf[got] = 0;

    Parser ps{buf.data()};
    const uint32_t n = static_cast<uint32_t>(ps.next());
    const size_t m = static_cast<size_t>(ps.next());
    const size_t q = static_cast<size_t>(ps.next());

    std::vector<uint32_t> eu(m), ev(m), ew(m);
    std::vector<uint32_t> start(static_cast<size_t>(n) + 1, 0);
    for (size_t i = 0; i < m; ++i) {
        uint32_t u = static_cast<uint32_t>(ps.next());
        uint32_t v = static_cast<uint32_t>(ps.next());
        uint32_t w = static_cast<uint32_t>(ps.next());
        eu[i] = u;
        ev[i] = v;
        ew[i] = w;
        if (u != v) {  // self-loops never shorten a path
            ++start[u + 1];
            ++start[v + 1];
        }
    }
    for (uint32_t i = 0; i < n; ++i) start[i + 1] += start[i];
    std::vector<Edge> adj(start[n]);
    {
        std::vector<uint32_t> pos(start.begin(), start.end() - 1);
        for (size_t i = 0; i < m; ++i) {
            uint32_t u = eu[i], v = ev[i], w = ew[i];
            if (u == v) continue;
            adj[pos[u]++] = {v, w};
            adj[pos[v]++] = {u, w};
        }
    }
    std::vector<uint32_t>().swap(eu);
    std::vector<uint32_t>().swap(ev);
    std::vector<uint32_t>().swap(ew);

    // Pack (dist, node) into one 64-bit key: distances never exceed the total road length.
    const int shift = n > 1 ? 32 - std::countl_zero(n - 1) : 0;
    const uint64_t mask = (uint64_t(1) << shift) - 1;

    std::vector<uint64_t> dist(n);
    RadixHeap heap(shift);
    std::string out;
    char line[128];

    for (size_t qi = 0; qi < q; ++qi) {
        uint32_t s = static_cast<uint32_t>(ps.next());
        std::fill(dist.begin(), dist.end(), UINT64_MAX);
        heap.reset();
        dist[s] = 0;
        heap.push(s);
        uint64_t reach = 0, total = 0, far = 0;
        uint32_t farNode = s;
        while (!heap.empty()) {
            uint64_t key = heap.pop();
            uint64_t d = key >> shift;
            uint32_t u = static_cast<uint32_t>(key & mask);
            if (d != dist[u]) continue;
            ++reach;
            total += d;
            if (d > far) {
                far = d;
                farNode = u;
            } else if (d == far && u < farNode) {
                farNode = u;
            }
            const Edge* e = adj.data() + start[u];
            const Edge* end = adj.data() + start[u + 1];
            for (; e != end; ++e) {
                uint64_t nd = d + e->w;
                if (nd < dist[e->to]) {
                    dist[e->to] = nd;
                    heap.push((nd << shift) | e->to);
                }
            }
        }
        int k = std::snprintf(line, sizeof line, "%u %llu %llu %llu %u\n", s, (unsigned long long)reach,
                              (unsigned long long)total, (unsigned long long)far, farNode);
        out.append(line, k);
    }
    _setmode(_fileno(stdout), _O_BINARY);
    std::fwrite(out.data(), 1, out.size(), stdout);
    return 0;
}
