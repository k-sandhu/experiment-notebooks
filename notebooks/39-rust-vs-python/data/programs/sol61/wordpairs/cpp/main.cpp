#include <algorithm>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <numeric>
#include <string_view>
#include <vector>

// Most inputs need only 16 bits per word ID. Promote without truncating IDs if
// the vocabulary is larger. Sorting streams contiguous arrays instead of making
// a random hash-table access for every pair.
struct PairList {
    std::vector<uint32_t> narrow;
    std::vector<uint64_t> wide;
    bool isWide = false;
    explicit PairList(size_t estimate) { narrow.reserve(estimate); }
    void add(uint32_t a, uint32_t b) {
        if (!isWide && (a > 65535 || b > 65535)) {
            wide.reserve(std::max(narrow.capacity(), narrow.size() + 1));
            for (uint32_t key : narrow) wide.push_back((uint64_t(key >> 16) << 32) | (key & 65535));
            std::vector<uint32_t>().swap(narrow); isWide = true;
        }
        if (isWide) wide.push_back((uint64_t(a) << 32) | b);
        else narrow.push_back((a << 16) | b);
    }
};

template<class T> void radixSort(std::vector<T>& keys) {
    if (keys.size() < 2048) { std::sort(keys.begin(), keys.end()); return; }
    T combined = 0;
    const T first = keys.front();
    for (T key : keys) combined |= key ^ first;
    if (!combined) return;
    std::vector<T> scratch(keys.size());
    for (unsigned shift = 0; shift < sizeof(T) * 8 && (combined >> shift); shift += 11) {
        if (((combined >> shift) & 2047) == 0) continue;
        size_t offsets[2048] = {};
        for (T key : keys) ++offsets[(key >> shift) & 2047];
        size_t total = 0;
        for (auto& offset : offsets) { size_t count = offset; offset = total; total += count; }
        for (T key : keys) scratch[offsets[(key >> shift) & 2047]++] = key;
        keys.swap(scratch);
    }
}

struct Word { size_t start, length; uint32_t hash; };
struct Vocabulary {
    const std::vector<char>& data;
    std::vector<Word> words{{0, 0, 0}};
    std::vector<uint32_t> slots = std::vector<uint32_t>(1024);
    explicit Vocabulary(const std::vector<char>& input) : data(input) {}
    std::string_view word(uint32_t id) const {
        const auto& w = words[id]; return {data.data() + w.start, w.length};
    }
    uint32_t intern(size_t start, size_t length, uint32_t hash) {
        size_t mask = slots.size() - 1, p = hash & mask;
        while (uint32_t id = slots[p]) {
            const auto& w = words[id];
            if (w.hash == hash && w.length == length &&
                std::memcmp(data.data() + start, data.data() + w.start, length) == 0) return id;
            p = (p + 1) & mask;
        }
        if (words.size() >= slots.size() * 3 / 4) {
            slots.assign(slots.size() * 2, 0); mask = slots.size() - 1;
            for (uint32_t id = 1; id < words.size(); ++id) {
                size_t q = words[id].hash & mask;
                while (slots[q]) q = (q + 1) & mask;
                slots[q] = id;
            }
            p = hash & mask; while (slots[p]) p = (p + 1) & mask;
        }
        uint32_t id = static_cast<uint32_t>(words.size());
        words.push_back({start, length, hash}); slots[p] = id; return id;
    }
};

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    std::ifstream file(argv[1], std::ios::binary | std::ios::ate);
    if (!file) return 1;
    const auto length = file.tellg();
    if (length < 0) return 1;
    std::vector<char> data(static_cast<size_t>(length));
    file.seekg(0);
    if (!data.empty() && !file.read(data.data(), static_cast<std::streamsize>(data.size()))) return 1;
    Vocabulary vocabulary(data);
    PairList pairs(data.size() / 6);
    uint64_t wordCount = 0, pairCount = 0;
    uint32_t previous = 0;
    size_t i = 0;
    while (i < data.size()) {
        unsigned c = static_cast<unsigned char>(data[i]) | 32u;
        if (c >= 'a' && c <= 'z') {
            size_t start = i;
            uint32_t h = 2166136261u;
            do {
                data[i++] = static_cast<char>(c); h = (h ^ c) * 16777619u;
                if (i == data.size()) break;
                c = static_cast<unsigned char>(data[i]) | 32u;
            } while (c >= 'a' && c <= 'z');
            uint32_t id = vocabulary.intern(start, i - start, h);
            ++wordCount;
            if (previous) { pairs.add(previous, id); ++pairCount; }
            previous = id;
        } else {
            const char raw = data[i++];
            if (raw == '.' || raw == '!' || raw == '?') previous = 0;
        }
    }
    std::vector<uint32_t> order(vocabulary.words.size() - 1), rank(vocabulary.words.size());
    std::iota(order.begin(), order.end(), 1u);
    std::sort(order.begin(), order.end(), [&](uint32_t a, uint32_t b) { return vocabulary.word(a) < vocabulary.word(b); });
    for (size_t j = 0; j < order.size(); ++j) rank[order[j]] = static_cast<uint32_t>(j);
    struct Entry { uint64_t key, count; };
    auto better = [&](const Entry& a, const Entry& b) {
        if (a.count != b.count) return a.count > b.count;
        uint32_t af = rank[uint32_t(a.key >> 32)], bf = rank[uint32_t(b.key >> 32)];
        if (af != bf) return af < bf;
        return rank[uint32_t(a.key)] < rank[uint32_t(b.key)];
    };
    std::vector<Entry> top; top.reserve(21);
    uint64_t distinct = 0;
    auto scan = [&](auto& keys, unsigned bits, uint64_t mask) {
        radixSort(keys);
        for (size_t j = 0; j < keys.size();) {
            size_t start = j;
            const auto key = keys[j++];
            while (j < keys.size() && keys[j] == key) ++j;
            ++distinct;
            Entry e{(uint64_t(key >> bits) << 32) | (key & mask), uint64_t(j - start)};
            if (top.size() == 20 && !better(e, top.back())) continue;
            auto p = std::lower_bound(top.begin(), top.end(), e, better);
            top.insert(p, e); if (top.size() > 20) top.pop_back();
        }
    };
    if (pairs.isWide) scan(pairs.wide, 32, 0xffffffffULL);
    else scan(pairs.narrow, 16, 65535);
    std::cout << "words " << wordCount << "\npairs " << pairCount << "\ndistinct " << distinct << '\n';
    for (auto e : top) std::cout << e.count << ' ' << vocabulary.word(uint32_t(e.key >> 32))
                               << ' ' << vocabulary.word(uint32_t(e.key)) << '\n';
}
