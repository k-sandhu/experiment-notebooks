// Counts adjacent word pairs within sentences and prints the 20 most frequent ones (see SPEC.md).
//
// One pass over the whole input: letters form words, which are looked up in an open-addressing
// vocabulary table; each pair of neighbouring words is counted in an open-addressing table of
// 12-byte slots. Final ranking uses integer ranks so no strings are compared while selecting.
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <fcntl.h>
#include <io.h>
#include <numeric>
#include <string>
#include <vector>

namespace {

// Byte classes.
constexpr unsigned char kSeparator = 0;
constexpr unsigned char kLetter = 1;
constexpr unsigned char kSentenceEnd = 2;

struct ByteClasses {
    unsigned char v[256] = {};
    constexpr ByteClasses() {
        for (int c = 'A'; c <= 'Z'; ++c) v[c] = kLetter;
        for (int c = 'a'; c <= 'z'; ++c) v[c] = kLetter;
        v['.'] = kSentenceEnd;
        v['!'] = kSentenceEnd;
        v['?'] = kSentenceEnd;
    }
};
constexpr ByteClasses kClass{};

constexpr uint32_t kFnvOffset = 0x811C9DC5u;
constexpr uint32_t kFnvPrime = 0x01000193u;
constexpr uint32_t kNoWord = 0xFFFFFFFFu;
constexpr size_t kTop = 20;

inline uint32_t mixPair(uint32_t a, uint32_t b) {
    uint32_t h = (a * 0x9E3779B1u) ^ b;
    h ^= h >> 16;
    h *= 0x85EBCA6Bu;
    h ^= h >> 13;
    return h;
}

// Maps lower-cased words to dense ids in first-seen order.
class Vocab {
public:
    Vocab() : table_(kInitialSlots, 0), mask_(kInitialSlots - 1) {}

    // p[0..len) holds letters in either case; h is the FNV-1a hash of their lower-case form.
    uint32_t find(const unsigned char* p, size_t len, uint32_t h) {
        size_t idx = h & mask_;
        for (uint32_t v; (v = table_[idx]) != 0; idx = (idx + 1) & mask_) {
            uint32_t id = v - 1;
            if (hashes_[id] == h && equalsFolded(words_[id], p, len)) return id;
        }
        uint32_t id = static_cast<uint32_t>(words_.size());
        std::string w(len, '\0');
        for (size_t j = 0; j < len; ++j) w[j] = static_cast<char>(p[j] | 0x20);
        words_.push_back(std::move(w));
        hashes_.push_back(h);
        table_[idx] = id + 1;
        if (words_.size() * 2 > table_.size()) grow();
        return id;
    }

    const std::vector<std::string>& words() const { return words_; }

private:
    static constexpr size_t kInitialSlots = size_t{1} << 16;

    static bool equalsFolded(const std::string& w, const unsigned char* p, size_t len) {
        if (w.size() != len) return false;
        for (size_t j = 0; j < len; ++j) {
            if (static_cast<unsigned char>(w[j]) != (p[j] | 0x20)) return false;
        }
        return true;
    }

    void grow() {
        std::vector<uint32_t> bigger(table_.size() * 2, 0);
        size_t m = bigger.size() - 1;
        for (uint32_t id = 0; id < words_.size(); ++id) {
            size_t idx = hashes_[id] & m;
            while (bigger[idx] != 0) idx = (idx + 1) & m;
            bigger[idx] = id + 1;
        }
        table_.swap(bigger);
        mask_ = m;
    }

    std::vector<uint32_t> table_;  // id + 1, 0 = empty
    size_t mask_;
    std::vector<uint32_t> hashes_;
    std::vector<std::string> words_;
};

// One slot of the pair table; c == 0 marks an empty slot.
struct Slot {
    uint32_t a;
    uint32_t b;
    uint32_t c;
};

// Counts ordered pairs of word ids.
class PairCounter {
public:
    PairCounter() : slots_(kInitialSlots, Slot{0, 0, 0}), mask_(kInitialSlots - 1) {}

    void add(uint32_t a, uint32_t b) {
        size_t idx = mixPair(a, b) & mask_;
        for (;;) {
            Slot& s = slots_[idx];
            if (s.c == 0) {
                s = Slot{a, b, 1};
                if (++distinct_ * 4 > slots_.size() * 3) grow();
                return;
            }
            if (s.a == a && s.b == b) {
                ++s.c;
                return;
            }
            idx = (idx + 1) & mask_;
        }
    }

    size_t distinct() const { return distinct_; }
    const std::vector<Slot>& slots() const { return slots_; }

private:
    static constexpr size_t kInitialSlots = size_t{1} << 20;

    void grow() {
        std::vector<Slot> bigger(slots_.size() * 2, Slot{0, 0, 0});
        size_t m = bigger.size() - 1;
        for (const Slot& s : slots_) {
            if (s.c == 0) continue;
            size_t idx = mixPair(s.a, s.b) & m;
            while (bigger[idx].c != 0) idx = (idx + 1) & m;
            bigger[idx] = s;
        }
        slots_.swap(bigger);
        mask_ = m;
    }

    std::vector<Slot> slots_;
    size_t mask_;
    size_t distinct_ = 0;
};

// A ranked result: count, first word id, second word id.
struct Entry {
    uint32_t c;
    uint32_t a;
    uint32_t b;
};

}  // namespace

int main(int argc, char** argv) {
    if (argc < 2) {
        std::fprintf(stderr, "usage: solution INPUT_PATH\n");
        return 2;
    }
    FILE* f = std::fopen(argv[1], "rb");
    if (!f) {
        std::fprintf(stderr, "cannot open %s\n", argv[1]);
        return 1;
    }
    _fseeki64(f, 0, SEEK_END);
    size_t n = static_cast<size_t>(_ftelli64(f));
    _fseeki64(f, 0, SEEK_SET);
    std::vector<unsigned char> buf(n);
    size_t got = std::fread(buf.data(), 1, n, f);
    std::fclose(f);
    if (got != n) {
        std::fprintf(stderr, "cannot read %s\n", argv[1]);
        return 1;
    }

    Vocab vocab;
    PairCounter pairs;
    uint64_t words = 0;
    uint64_t total = 0;
    uint32_t prev = kNoWord;
    const unsigned char* p = buf.data();
    size_t i = 0;
    while (i < n) {
        unsigned char cls = kClass.v[p[i]];
        if (cls == kLetter) {
            size_t start = i;
            uint32_t h = kFnvOffset;
            do {
                h = (h ^ static_cast<uint32_t>(p[i] | 0x20)) * kFnvPrime;
                ++i;
            } while (i < n && kClass.v[p[i]] == kLetter);
            uint32_t id = vocab.find(p + start, i - start, h);
            ++words;
            if (prev != kNoWord) {
                pairs.add(prev, id);
                ++total;
            }
            prev = id;
        } else {
            if (cls == kSentenceEnd) prev = kNoWord;
            ++i;
        }
    }

    // Rank words by byte order so ties can be broken with integer comparisons.
    const std::vector<std::string>& names = vocab.words();
    std::vector<uint32_t> order(names.size());
    std::iota(order.begin(), order.end(), 0u);
    std::sort(order.begin(), order.end(), [&](uint32_t x, uint32_t y) { return names[x] < names[y]; });
    std::vector<uint32_t> rank(names.size());
    for (uint32_t r = 0; r < order.size(); ++r) rank[order[r]] = r;

    auto better = [&](const Entry& x, const Entry& y) {
        if (x.c != y.c) return x.c > y.c;
        if (rank[x.a] != rank[y.a]) return rank[x.a] < rank[y.a];
        return rank[x.b] < rank[y.b];
    };

    std::vector<Entry> top;
    top.reserve(kTop + 1);
    for (const Slot& s : pairs.slots()) {
        if (s.c == 0) continue;
        Entry e{s.c, s.a, s.b};
        if (top.size() == kTop && !better(e, top.back())) continue;
        top.push_back(e);
        for (size_t k = top.size() - 1; k > 0 && better(top[k], top[k - 1]); --k) {
            std::swap(top[k], top[k - 1]);
        }
        if (top.size() > kTop) top.pop_back();
    }

    std::string out;
    out += "words " + std::to_string(words) + "\n";
    out += "pairs " + std::to_string(total) + "\n";
    out += "distinct " + std::to_string(pairs.distinct()) + "\n";
    for (const Entry& e : top) {
        out += std::to_string(e.c) + " " + names[e.a] + " " + names[e.b] + "\n";
    }
    _setmode(_fileno(stdout), _O_BINARY);
    std::fwrite(out.data(), 1, out.size(), stdout);
    return 0;
}
