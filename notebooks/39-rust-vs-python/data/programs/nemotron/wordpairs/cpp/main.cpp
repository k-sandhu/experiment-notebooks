// Word pairs benchmark - C++20, MSVC.
// Single pass over the text: lowercase words in place, intern them to ids,
// emit (prevId, curId) pairs within sentences, sort packed pairs, count runs,
// keep the top 20 by (count desc, word1 asc, word2 asc).
#include <cstdio>
#include <cstdint>
#include <cstring>
#include <vector>
#include <algorithm>
#include <io.h>
#include <fcntl.h>

using u32 = uint32_t;
using u64 = uint64_t;

static inline bool is_letter(unsigned char c) {
    c = (unsigned char)(c | 0x20); // fold to lower case
    return c >= 'a' && c <= 'z';
}

static inline unsigned char to_lower(unsigned char c) {
    if (c >= 'A' && c <= 'Z') return (unsigned char)(c + 0x20);
    return c;
}

// Open-addressing hash map from lowercase word (view into the input buffer)
// to a dense word id. The buffer owns the strings, so no copies are made.
struct InternMap {
    struct Slot {
        u32 hashPlusOne; // 0 means empty slot
        u32 id;
    };

    std::vector<Slot> slots;
    std::vector<char> pool;   // null-terminated words, indexed by id
    std::vector<u32> offs;    // offset of each word inside pool
    std::vector<u32> lens;    // length of each word
    u64 mask;
    u32 occupied;

    InternMap() : mask(0), occupied(0) { reset(1 << 14); }

    void reset(size_t cap) {
        slots.assign(cap, Slot{0, 0});
        mask = (u64)cap - 1;
    }

    void rehash(const std::vector<Slot>& old) {
        for (const Slot& s : old) {
            if (s.hashPlusOne != 0) {
                u32 h = s.hashPlusOne - 1;
                size_t pos = (u64)h & mask;
                while (slots[pos].hashPlusOne != 0) pos = (pos + 1) & mask;
                slots[pos] = s;
            }
        }
    }

    u32 intern(const char* data, u32 start, u32 len, u32 hash) {
        if (((u64)occupied + 1) * 4 >= (u64)slots.size() * 3) {
            size_t newCap = slots.size() * 2;
            std::vector<Slot> old = std::move(slots);
            slots.assign(newCap, Slot{0, 0});
            mask = (u64)newCap - 1;
            rehash(old);
        }
        u32 hp = hash + 1;
        size_t pos = (u64)hash & mask;
        while (true) {
            Slot& s = slots[pos];
            if (s.hashPlusOne == 0) {
                s.hashPlusOne = hp;
                s.id = occupied;
                offs.push_back((u32)pool.size());
                lens.push_back(len);
                pool.insert(pool.end(), data + start, data + start + len);
                pool.push_back('\0');
                ++occupied;
                return s.id;
            }
            if (s.hashPlusOne == hp) {
                u32 id = s.id;
                if (lens[id] == len && std::memcmp(pool.data() + offs[id], data + start, len) == 0)
                    return id;
            }
            pos = (pos + 1) & mask;
        }
    }
};

int main(int argc, char** argv) {
    if (argc < 2) return 1;

    // write LF-only output no matter how stdout is captured
    _setmode(_fileno(stdout), _O_BINARY);

    FILE* f = fopen(argv[1], "rb");
    if (!f) return 1;
    fseek(f, 0, SEEK_END);
    long fileLen = ftell(f);
    fseek(f, 0, SEEK_SET);
    std::vector<char> buf;
    if (fileLen > 0) {
        buf.resize((size_t)fileLen);
        if (fread(buf.data(), 1, buf.size(), f) != (size_t)fileLen) {
            fclose(f);
            return 1;
        }
    }
    fclose(f);

    char* data = buf.data();
    size_t n = buf.size();

    InternMap intern;
    std::vector<u64> pairs;
    pairs.reserve(1 << 20);

    u32 prevId = 0;
    bool havePrev = false;
    u64 wordTotal = 0, pairTotal = 0;

    // compare two word ids by their lower-cased spelling (byte order)
    auto wordLess = [&](u32 a, u32 b) -> bool {
        const char* sa = intern.pool.data() + intern.offs[a];
        const char* sb = intern.pool.data() + intern.offs[b];
        u32 la = intern.lens[a], lb = intern.lens[b];
        u32 m = la < lb ? la : lb;
        int c = std::memcmp(sa, sb, m);
        if (c != 0) return c < 0;
        return la < lb;
    };

    auto better = [&](u64 c1, u32 a1, u32 b1, u64 c2, u32 a2, u32 b2) -> bool {
        // is (c1,a1,b1) better than (c2,a2,b2)? count desc, then words asc
        if (c1 != c2) return c1 > c2;
        if (wordLess(a1, a2)) return true;
        if (wordLess(a2, a1)) return false;
        return wordLess(b1, b2);
    };

    struct Entry { u64 count; u32 w1; u32 w2; };
    Entry best[20];
    int bestn = 0;

    auto consider = [&](u64 count, u32 w1, u32 w2) {
        if (bestn < 20) {
            int pos = bestn;
            while (pos > 0 && better(count, w1, w2, best[pos - 1].count, best[pos - 1].w1, best[pos - 1].w2)) {
                best[pos] = best[pos - 1];
                --pos;
            }
            best[pos].count = count;
            best[pos].w1 = w1;
            best[pos].w2 = w2;
            ++bestn;
        } else if (better(count, w1, w2, best[19].count, best[19].w1, best[19].w2)) {
            Entry e{count, w1, w2};
            int pos = 19;
            while (pos > 0 && better(count, w1, w2, best[pos - 1].count, best[pos - 1].w1, best[pos - 1].w2)) {
                best[pos] = best[pos - 1];
                --pos;
            }
            best[pos] = e;
        }
    };

    size_t i = 0;
    while (i < n) {
        // skip to the next word; sentence enders reset the previous word
        while (i < n) {
            unsigned char c = (unsigned char)data[i];
            if (is_letter(c)) break;
            if (c == '.' || c == '!' || c == '?') havePrev = false;
            ++i;
        }
        if (i >= n) break;

        // scan the word, lowercasing in place
        u32 start = (u32)i;
        u32 hash = 2166136261u;
        while (i < n) {
            unsigned char c = (unsigned char)data[i];
            if (!is_letter(c)) break;
            c = to_lower(c);
            data[i] = (char)c;
            hash ^= c;
            hash *= 16777619u;
            ++i;
        }
        u32 len = (u32)(i - start);

        u32 id = intern.intern(data, start, len, hash);
        ++wordTotal;
        if (havePrev) {
            pairs.push_back(((u64)prevId << 32) | (u64)id);
            ++pairTotal;
        }
        prevId = id;
        havePrev = true;
    }

    std::sort(pairs.begin(), pairs.end());

    size_t k = 0;
    u64 distinct = 0;
    while (k < pairs.size()) {
        size_t j = k + 1;
        while (j < pairs.size() && pairs[j] == pairs[k]) ++j;
        consider((u64)(j - k), (u32)(pairs[k] >> 32), (u32)pairs[k]);
        ++distinct;
        k = j;
    }

    printf("words %llu\npairs %llu\ndistinct %llu\n",
           (unsigned long long)wordTotal, (unsigned long long)pairTotal, (unsigned long long)distinct);
    for (int t = 0; t < bestn; ++t) {
        const char* w1 = intern.pool.data() + intern.offs[best[t].w1];
        const char* w2 = intern.pool.data() + intern.offs[best[t].w2];
        printf("%llu %s %s\n", (unsigned long long)best[t].count, w1, w2);
    }
    return 0;
}
