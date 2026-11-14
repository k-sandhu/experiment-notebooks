#include <array>
#include <bit>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <limits>
#include <memory>
#include <vector>

class FastInput {
    static constexpr std::size_t BUFFER_SIZE = 1 << 16;
    FILE* file_;
    char buffer_[BUFFER_SIZE];
    std::size_t position_ = 0;
    std::size_t length_ = 0;

    unsigned get() {
        if (position_ == length_) {
            length_ = std::fread(buffer_, 1, BUFFER_SIZE, file_);
            position_ = 0;
            if (length_ == 0) return 0;
        }
        return static_cast<unsigned char>(buffer_[position_++]);
    }

public:
    explicit FastInput(FILE* file) : file_(file) {}

    std::uint64_t nextUnsigned() {
        unsigned c;
        do {
            c = get();
        } while (c <= 32);

        std::uint64_t value = 0;
        do {
            value = value * 10 + (c - '0');
            c = get();
        } while (c >= '0' && c <= '9');

        return value;
    }
};

using Node = std::uint32_t;
static constexpr Node NONE = std::numeric_limits<Node>::max();
static constexpr std::uint64_t INF =
    std::numeric_limits<std::uint64_t>::max();

struct Road {
    Node u;
    Node v;
    std::uint32_t weight;
};

struct Edge {
    Node to;
    std::uint32_t weight;
};

struct State {
    std::uint64_t distance;
    Node next;
    Node previous;
};

// All pending distances lie within a range of width at most 1000.
// Thus 1024 circular buckets, indexed by distance modulo 1024,
// uniquely represent the pending distance levels.
class BucketQueue {
    State* states_;
    std::array<Node, 1024> heads_;
    std::array<std::uint64_t, 16> occupied_;
    std::uint64_t summary_ = 0;
    unsigned current_ = 0;

    void clearBucket(unsigned bucket) {
        const unsigned word = bucket >> 6;
        occupied_[word] &= ~(std::uint64_t{1} << (bucket & 63));
        if (occupied_[word] == 0) {
            summary_ &= ~(std::uint64_t{1} << word);
        }
    }

public:
    explicit BucketQueue(State* states) : states_(states) {
        reset();
    }

    void reset() {
        heads_.fill(NONE);
        occupied_.fill(0);
        summary_ = 0;
        current_ = 0;
    }

    bool empty() const {
        return summary_ == 0;
    }

    void insert(Node node, unsigned bucket) {
        State& state = states_[node];
        const Node oldHead = heads_[bucket];

        state.previous = NONE;
        state.next = oldHead;

        if (oldHead != NONE) {
            states_[oldHead].previous = node;
        } else {
            const unsigned word = bucket >> 6;
            occupied_[word] |= std::uint64_t{1} << (bucket & 63);
            summary_ |= std::uint64_t{1} << word;
        }

        heads_[bucket] = node;
    }

    void erase(Node node, unsigned bucket) {
        const Node previous = states_[node].previous;
        const Node next = states_[node].next;

        if (previous == NONE) {
            heads_[bucket] = next;
        } else {
            states_[previous].next = next;
        }

        if (next != NONE) {
            states_[next].previous = previous;
        }

        if (heads_[bucket] == NONE) {
            clearBucket(bucket);
        }
    }

    Node pop() {
        unsigned word = current_ >> 6;
        std::uint64_t bits =
            occupied_[word] &
            (~std::uint64_t{0} << (current_ & 63));

        if (bits == 0) {
            std::uint64_t words =
                summary_ & (~std::uint64_t{0} << (word + 1));
            if (words == 0) words = summary_;

            word = static_cast<unsigned>(std::countr_zero(words));
            bits = occupied_[word];
        }

        const unsigned bucket =
            (word << 6) + static_cast<unsigned>(std::countr_zero(bits));
        current_ = bucket;

        const Node node = heads_[bucket];
        const Node next = states_[node].next;
        heads_[bucket] = next;

        if (next != NONE) {
            states_[next].previous = NONE;
        } else {
            clearBucket(bucket);
        }

        return node;
    }
};

int main(int argc, char** argv) {
    if (argc < 2) return 0;

    FILE* file = std::fopen(argv[1], "rb");
    if (file == nullptr) return 0;

    FastInput input(file);

    const Node n = static_cast<Node>(input.nextUnsigned());
    const std::size_t m =
        static_cast<std::size_t>(input.nextUnsigned());
    const std::uint64_t q = input.nextUnsigned();

    std::vector<std::size_t> offsets(
        static_cast<std::size_t>(n) + 1, 0);
    std::unique_ptr<Road[]> roads(new Road[m]);
    std::size_t roadCount = 0;

    for (std::size_t i = 0; i < m; ++i) {
        const Node u = static_cast<Node>(input.nextUnsigned());
        const Node v = static_cast<Node>(input.nextUnsigned());
        const auto weight =
            static_cast<std::uint32_t>(input.nextUnsigned());

        // Positive self-loops cannot improve a shortest path.
        if (u == v) continue;

        roads[roadCount++] = Road{u, v, weight};
        ++offsets[static_cast<std::size_t>(u) + 1];
        ++offsets[static_cast<std::size_t>(v) + 1];
    }

    for (std::size_t i = 1; i <= n; ++i) {
        offsets[i] += offsets[i - 1];
    }

    std::unique_ptr<Edge[]> edges(new Edge[offsets[n]]);
    {
        std::vector<std::size_t> cursor(offsets);
        for (std::size_t i = 0; i < roadCount; ++i) {
            const Road& road = roads[i];
            edges[cursor[road.u]++] = Edge{road.v, road.weight};
            edges[cursor[road.v]++] = Edge{road.u, road.weight};
        }
    }
    roads.reset();

    std::unique_ptr<State[]> states(new State[n]);
    BucketQueue queue(states.get());

    for (std::uint64_t query = 0; query < q; ++query) {
        const Node source = static_cast<Node>(input.nextUnsigned());

        for (std::size_t i = 0; i < n; ++i) {
            states[i].distance = INF;
        }
        queue.reset();

        states[source].distance = 0;
        queue.insert(source, 0);

        std::uint64_t reachable = 0;
        std::uint64_t total = 0;
        std::uint64_t farthest = 0;
        Node farthestNode = source;

        while (!queue.empty()) {
            const Node u = queue.pop();
            const std::uint64_t distance = states[u].distance;

            ++reachable;
            total += distance;

            if (distance > farthest) {
                farthest = distance;
                farthestNode = u;
            } else if (distance == farthest && u < farthestNode) {
                farthestNode = u;
            }

            const std::size_t end =
                offsets[static_cast<std::size_t>(u) + 1];

            for (std::size_t i = offsets[u]; i < end; ++i) {
                const Edge& edge = edges[i];
                State& target = states[edge.to];
                const std::uint64_t candidate =
                    distance + edge.weight;

                if (candidate < target.distance) {
                    if (target.distance != INF) {
                        queue.erase(
                            edge.to,
                            static_cast<unsigned>(target.distance & 1023));
                    }

                    target.distance = candidate;
                    queue.insert(
                        edge.to,
                        static_cast<unsigned>(candidate & 1023));
                }
            }
        }

        std::printf(
            "%u %llu %llu %llu %u\n",
            static_cast<unsigned>(source),
            static_cast<unsigned long long>(reachable),
            static_cast<unsigned long long>(total),
            static_cast<unsigned long long>(farthest),
            static_cast<unsigned>(farthestNode));
    }

    std::fclose(file);
    return 0;
}
