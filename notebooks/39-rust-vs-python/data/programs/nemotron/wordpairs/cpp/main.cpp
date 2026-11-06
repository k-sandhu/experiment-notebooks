#include <cstdio>
#include <cstdint>
#include <cstring>
#include <vector>
#include <string>
#include <string_view>
#include <algorithm>
#include <io.h>
#include <fcntl.h>

static inline bool isLetter(unsigned char c) {
    return (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z');
}

static inline unsigned char toLower(unsigned char c) { return c | 0x20u; }

// Open-addressing map from lowercased word (string_view) to id.
// Views point into owned std::string objects in `words`, which never move
// their character data, so views stay valid across rehashes.
struct WordMap {
    std::vector<std::string> words; // id -> lowercase word
    std::vector<uint32_t> slots;    // id + 1, 0 means empty
    size_t mask;
    size_t count;

    WordMap() : mask(4095), count(0) { slots.assign(4096, 0); }

    static size_t hashView(std::string_view s) noexcept {
        size_t h = 14695981039346656037ull;
        for (unsigned char c : s) {
            h ^= c;
            h *= 1099511628211ull;
        }
        return h;
    }

    void grow() {
        std::vector<uint32_t> old;
        old.swap(slots);
        mask = mask * 2 + 1;
        slots.assign(mask + 1, 0);
        count = 0;
        for (uint32_t v : old) {
            if (v == 0) continue;
            size_t i = hashView(std::string_view(words[v - 1])) & mask;
            while (slots[i] != 0) i = (i + 1) & mask;
            slots[i] = v;
            ++count;
        }
    }

    std::pair<uint32_t, bool> intern(std::string_view s) {
        if (count * 4 >= slots.size() * 3) grow();
        size_t i = hashView(s) & mask;
        while (true) {
            uint32_t v = slots[i];
            if (v == 0) {
                words.emplace_back(s.data(), s.size());
                uint32_t id = uint32_t(words.size() - 1);
                slots[i] = id + 1;
                ++count;
                return { id, true };
            }
            const std::string& w = words[v - 1];
            if (w.size() == s.size() && std::memcmp(w.data(), s.data(), s.size()) == 0)
                return { v - 1, false };
            i = (i + 1) & mask;
        }
    }
};

// Open-addressing map from packed (id1, id2) pair key to count.
struct PairMap {
    std::vector<uint64_t> keys;   // UINT64_MAX means empty
    std::vector<uint32_t> counts;
    size_t mask;
    size_t count;

    PairMap() : mask((uint32_t(1) << 16) - 1), count(0) {
        keys.assign(mask + 1, UINT64_MAX);
        counts.assign(mask + 1, 0);
    }

    void grow() {
        std::vector<uint64_t> oldK;
        oldK.swap(keys);
        std::vector<uint32_t> oldC;
        oldC.swap(counts);
        mask = mask * 2 + 1;
        keys.assign(mask + 1, UINT64_MAX);
        counts.assign(mask + 1, 0);
        count = 0;
        for (size_t i = 0; i < oldK.size(); ++i) {
            uint64_t k = oldK[i];
            if (k == UINT64_MAX) continue;
            size_t j = slot(k, mask);
            while (keys[j] != UINT64_MAX) j = (j + 1) & mask;
            keys[j] = k;
            counts[j] = oldC[i];
            ++count;
        }
    }

    static size_t slot(uint64_t k, size_t m) noexcept {
        return size_t(k * 0x9E3779B97F4A7C15ull) & m;
    }

    uint32_t* findOrInsert(uint64_t key) {
        if ((count + 1) * 4 >= keys.size() * 3) grow();
        size_t i = slot(key, mask);
        while (keys[i] != UINT64_MAX) {
            if (keys[i] == key) return &counts[i];
            i = (i + 1) & mask;
        }
        keys[i] = key;
        counts[i] = 0;
        ++count;
        return &counts[i];
    }
};

struct Entry {
    uint32_t count;
    uint32_t id1;
    uint32_t id2;
};

int main(int argc, char** argv) {
    if (argc < 2) return 1;

    _setmode(_fileno(stdout), _O_BINARY);

    FILE* f = std::fopen(argv[1], "rb");
    if (!f) return 1;
    if (std::fseek(f, 0, SEEK_END) != 0) { std::fclose(f); return 1; }
    long len = std::ftell(f);
    if (len < 0) { std::fclose(f); return 1; }
    if (std::fseek(f, 0, SEEK_SET) != 0) { std::fclose(f); return 1; }
    std::string data;
    data.resize(size_t(len) + 1);
    if (len > 0) {
        std::fread(data.data(), 1, size_t(len), f);
    }
    std::fclose(f);

    const unsigned char* s = reinterpret_cast<const unsigned char*>(data.data());
    const unsigned char* end = s + size_t(len);

    WordMap wmap;
    PairMap pmap;
    std::string buf;
    buf.reserve(64);

    uint64_t wordsCount = 0;
    uint64_t pairsCount = 0;
    uint32_t prevId = UINT32_MAX;

    auto noteWord = [&](uint32_t id) {
        ++wordsCount;
        if (prevId != UINT32_MAX) {
            ++pairsCount;
            uint64_t key = (uint64_t(prevId) << 32) | uint64_t(id);
            *pmap.findOrInsert(key) += 1;
        }
        prevId = id;
    };

    while (s < end) {
        unsigned char c = *s++;
        if (isLetter(c)) {
            buf.push_back(char(toLower(c)));
        } else {
            if (!buf.empty()) {
                noteWord(wmap.intern(std::string_view(buf.data(), buf.size())).first);
                buf.clear();
            }
            if (c == '.' || c == '!' || c == '?') prevId = UINT32_MAX;
        }
    }
    if (!buf.empty()) {
        noteWord(wmap.intern(std::string_view(buf.data(), buf.size())).first);
    }

    uint64_t distinct = pmap.count;
    std::vector<Entry> entries;
    entries.reserve(pmap.count);
    for (size_t i = 0; i < pmap.keys.size(); ++i) {
        if (pmap.keys[i] != UINT64_MAX) {
            entries.push_back(Entry{
                pmap.counts[i],
                uint32_t(pmap.keys[i] >> 32),
                uint32_t(pmap.keys[i])
            });
        }
    }

    std::sort(entries.begin(), entries.end(), [&](const Entry& a, const Entry& b) {
        if (a.count != b.count) return a.count > b.count;
        const std::string& w1a = wmap.words[a.id1];
        const std::string& w1b = wmap.words[b.id1];
        int c = w1a.compare(w1b);
        if (c != 0) return c < 0;
        const std::string& w2a = wmap.words[a.id2];
        const std::string& w2b = wmap.words[b.id2];
        return w2a.compare(w2b) < 0;
    });

    std::printf("words %llu\npairs %llu\ndistinct %llu\n",
        (unsigned long long)wordsCount, (unsigned long long)pairsCount, (unsigned long long)distinct);
    size_t limit = entries.size() < 20 ? entries.size() : 20;
    for (size_t i = 0; i < limit; ++i) {
        std::printf("%u %s %s\n", entries[i].count,
            wmap.words[entries[i].id1].c_str(),
            wmap.words[entries[i].id2].c_str());
    }
    return 0;
}
