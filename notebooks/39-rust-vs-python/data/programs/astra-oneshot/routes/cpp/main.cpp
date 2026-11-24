#include <algorithm>
#include <array>
#include <bit>
#include <cinttypes>
#include <cstdint>
#include <cstdio>
#include <limits>
#include <vector>

class FastInput {
    static constexpr std::size_t BufferSize = 1 << 16;
    FILE* file_;
    unsigned char buffer_[BufferSize];
    std::size_t position_ = 0;
    std::size_t length_ = 0;

    int get() {
        if (position_ == length_) {
            length_ = std::fread(buffer_, 1, BufferSize, file_);
            position_ = 0;
            if (length_ == 0) return EOF;
        }
        return buffer_[position_++];
    }

public:
    explicit FastInput(FILE* file) : file_(file) {}

    std::uint64_t number() {
        int c;
        do {
            c = get();
        } while (c != EOF && c <= ' ');

        std::uint64_t value = 0;
        while (c >= '0' && c <= '9') {
            value = value * 10 + static_cast<unsigned>(c - '0');
            c = get();
        }
        return value;
    }
};

struct InputEdge {
    std::uint32_t u, v, weight;
};

struct Edge {
    std::uint32_t to, weight;
};

class BucketQueue {
    static constexpr std::uint32_t None =
        std::numeric_limits<std::uint32_t>::max();

    std::array<std::uint32_t, 1024> heads_;
    std::array<std::uint64_t, 16> occupied_;
    std::uint32_t occupiedWords_ = 0;
    std::uint32_t current_ = 0;
    std::vector<std::uint32_t> next_;
    std::vector<std::uint32_t> previous_;

public:
    explicit BucketQueue(std::size_t n) : next_(n), previous_(n) {}

    void reset() {
        heads_.fill(None);
        occupied_.fill(0);
        occupiedWords_ = 0;
        current_ = 0;
    }

    bool empty() const {
        return occupiedWords_ == 0;
    }

    void erase(std::uint32_t node, std::uint32_t bucket) {
        const std::uint32_t before = previous_[node];
        const std::uint32_t after = next_[node];

        if (before == None) {
            heads_[bucket] = after;
        } else {
            next_[before] = after;
        }

        if (after != None) {
            previous_[after] = before;
        }

        if (heads_[bucket] == None) {
            const std::uint32_t word = bucket >> 6;
            occupied_[word] &= ~(std::uint64_t{1} << (bucket & 63));
            if (occupied_[word] == 0) {
                occupiedWords_ &= ~(std::uint32_t{1} << word);
            }
        }
    }

    void insert(std::uint32_t node, std::uint32_t bucket) {
        const std::uint32_t oldHead = heads_[bucket];
        previous_[node] = None;
        next_[node] = oldHead;

        if (oldHead != None) {
            previous_[oldHead] = node;
        } else {
            const std::uint32_t word = bucket >> 6;
            occupied_[word] |= std::uint64_t{1} << (bucket & 63);
            occupiedWords_ |= std::uint32_t{1} << word;
        }

        heads_[bucket] = node;
    }

    std::uint32_t pop() {
        std::uint32_t word = current_ >> 6;
        std::uint64_t candidates =
            occupied_[word] &
            (std::numeric_limits<std::uint64_t>::max() << (current_ & 63));

        if (candidates == 0) {
            const std::uint32_t laterWords =
                occupiedWords_ &
                (std::numeric_limits<std::uint32_t>::max() << (word + 1));

            word = static_cast<std::uint32_t>(
                std::countr_zero(laterWords != 0 ? laterWords : occupiedWords_));
            candidates = occupied_[word];
        }

        current_ = word * 64 +
            static_cast<std::uint32_t>(std::countr_zero(candidates));

        const std::uint32_t node = heads_[current_];
        erase(node, current_);
        return node;
    }
};

template<class Distance>
void solve(
    std::uint32_t n,
    const std::vector<std::size_t>& offsets,
    const std::vector<Edge>& edges,
    const std::vector<std::uint32_t>& sources
) {
    constexpr Distance Infinity = std::numeric_limits<Distance>::max();
    std::vector<Distance> distance(n);
    BucketQueue queue(n);

    for (const std::uint32_t source : sources) {
        std::fill(distance.begin(), distance.end(), Infinity);
        queue.reset();

        distance[source] = 0;
        queue.insert(source, 0);

        std::uint64_t reachable = 0;
        std::uint64_t total = 0;
        std::uint64_t farthest = 0;
        std::uint32_t farthestNode = source;

        while (!queue.empty()) {
            const std::uint32_t u = queue.pop();
            const Distance du = distance[u];

            ++reachable;
            total += static_cast<std::uint64_t>(du);

            if (du > farthest) {
                farthest = du;
                farthestNode = u;
            } else if (du == farthest && u < farthestNode) {
                farthestNode = u;
            }

            const std::size_t end = offsets[static_cast<std::size_t>(u) + 1];
            for (std::size_t i = offsets[u]; i < end; ++i) {
                const Edge edge = edges[i];
                const Distance candidate =
                    du + static_cast<Distance>(edge.weight);
                const Distance oldDistance = distance[edge.to];

                if (candidate < oldDistance) {
                    if (oldDistance != Infinity) {
                        queue.erase(
                            edge.to,
                            static_cast<std::uint32_t>(oldDistance & 1023));
                    }

                    distance[edge.to] = candidate;
                    queue.insert(
                        edge.to,
                        static_cast<std::uint32_t>(candidate & 1023));
                }
            }
        }

        std::printf(
            "%" PRIu32 " %" PRIu64 " %" PRIu64 " %" PRIu64 " %" PRIu32 "\n",
            source, reachable, total, farthest, farthestNode);
    }
}

int main(int argc, char** argv) {
    if (argc < 2) return 0;

    FILE* file = nullptr;
    if (fopen_s(&file, argv[1], "rb") != 0 || file == nullptr) return 0;

    FastInput input(file);
    const std::uint32_t n = static_cast<std::uint32_t>(input.number());
    const std::size_t m = static_cast<std::size_t>(input.number());
    const std::size_t q = static_cast<std::size_t>(input.number());

    std::vector<std::size_t> offsets(static_cast<std::size_t>(n) + 1, 0);
    std::vector<Edge> edges;

    {
        std::vector<InputEdge> inputEdges;
        inputEdges.reserve(m);

        for (std::size_t i = 0; i < m; ++i) {
            const std::uint32_t u = static_cast<std::uint32_t>(input.number());
            const std::uint32_t v = static_cast<std::uint32_t>(input.number());
            const std::uint32_t w = static_cast<std::uint32_t>(input.number());

            if (u != v) {
                inputEdges.push_back({u, v, w});
                ++offsets[static_cast<std::size_t>(u) + 1];
                ++offsets[static_cast<std::size_t>(v) + 1];
            }
        }

        for (std::size_t i = 1; i < offsets.size(); ++i) {
            offsets[i] += offsets[i - 1];
        }

        edges.resize(offsets.back());
        std::vector<std::size_t> cursor(offsets.begin(), offsets.end() - 1);

        for (const InputEdge& edge : inputEdges) {
            edges[cursor[edge.u]++] = {edge.v, edge.weight};
            edges[cursor[edge.v]++] = {edge.u, edge.weight};
        }
    }

    std::vector<std::uint32_t> sources(q);
    for (std::uint32_t& source : sources) {
        source = static_cast<std::uint32_t>(input.number());
    }

    std::fclose(file);

    if (n <= std::numeric_limits<std::uint32_t>::max() / 1000) {
        solve<std::uint32_t>(n, offsets, edges, sources);
    } else {
        solve<std::uint64_t>(n, offsets, edges, sources);
    }

    return 0;
}
