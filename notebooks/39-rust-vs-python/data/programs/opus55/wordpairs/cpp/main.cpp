// Word pairs: count adjacent word pairs within sentences, report the top 20.
//
// 1. Scan the input once. Words are found 8 bytes at a time (SWAR),
//    and interned to dense ids by an open-addressing table whose slots
//    hold the first 8 bytes of the word. The scan records the id sequence, with
//    a flag on each word that starts a sentence, and counts pairs per first word.
// 2. Counting-sort the pairs by first word (second words only).
// 3. For each first word, count its second words in a dense counter array that
//    stays in cache, and keep the 20 best pairs. Ties are broken by each word's
//    lexicographic rank, so the selection compares integers only.
#include <fcntl.h>
#include <io.h>

#include <algorithm>
#include <bit>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <memory>
#include <string>
#include <vector>

namespace {

constexpr uint64_t kOnes = 0x0101010101010101ULL;
constexpr uint64_t kHigh = 0x8080808080808080ULL;
constexpr uint64_t kCase = 0x2020202020202020ULL;
constexpr uint32_t kStart = 0x80000000u;  // flag: word starts a sentence

inline uint64_t load64(const uint8_t* p) {
    uint64_t v;
    std::memcpy(&v, p, 8);
    return v;
}

// High bit set in each byte of v (bytes < 0x80) that is an ASCII letter.
inline uint64_t letterMask(uint64_t v) {
    uint64_t x = v | kCase;  // fold case; bytes stay below 0x80
    uint64_t ge_a = x + 0x1F * kOnes;  // >= 0x80 iff x >= 'a'
    uint64_t gt_z = x + 0x05 * kOnes;  // >= 0x80 iff x >  'z'
    return ge_a & ~gt_z & kHigh;
}

// Mask covering the low n bytes (n >= 0).
inline uint64_t lowBytes(unsigned n) { return n >= 8 ? ~0ULL : (1ULL << (8 * n)) - 1; }

struct CharClass {
    uint8_t t[256];
    constexpr CharClass() : t{} {
        for (int c = 'a'; c <= 'z'; ++c) t[c] = 1;
        for (int c = 'A'; c <= 'Z'; ++c) t[c] = 1;
        t[(int)'.'] = 2;
        t[(int)'!'] = 2;
        t[(int)'?'] = 2;
    }
};
constexpr CharClass kClass;

struct Slot {
    uint64_t prefix;  // first 8 lower-case bytes, zero padded
    uint32_t hash;
    uint32_t id;  // 0 = empty
};

struct WordTable {
    std::vector<Slot> slots;
    int shift;
    uint64_t mask;
    std::vector<uint32_t> off{0}, len{0};  // per id, index 0 unused

    WordTable() { resize(16); }

    void resize(int bits) {
        std::vector<Slot> old;
        old.swap(slots);
        slots.assign(size_t(1) << bits, Slot{0, 0, 0});
        shift = 64 - bits;
        mask = (uint64_t(1) << bits) - 1;
        for (const Slot& s : old) {
            if (!s.id) continue;
            uint64_t i = uint64_t(s.hash) >> (32 - bits);
            while (slots[i].id) i = (i + 1) & mask;
            slots[i] = s;
        }
    }

    uint32_t count() const { return uint32_t(off.size() - 1); }

    // Bytes 8..n of a (lower case) and b (any case) are equal, ignoring case.
    static inline bool tailEq(const uint8_t* a, const uint8_t* b, uint32_t n) {
        for (uint32_t j = 8; j < n; j += 8) {
            uint64_t m = lowBytes(n - j);
            if (((load64(a + j) ^ (load64(b + j) | kCase)) & m) != 0) return false;
        }
        return true;
    }

    // h: 32-bit hash; its top bits pick the slot.
    inline uint32_t intern(uint8_t* buf, uint32_t start, uint32_t n, uint64_t prefix, uint32_t h) {
        uint64_t i = uint64_t(h) >> (shift - 32);
        for (;;) {
            const Slot& s = slots[i];
            if (s.id == 0) break;
            if (s.hash == h && s.prefix == prefix && (n < 8 || (len[s.id] == n && tailEq(buf + off[s.id], buf + start, n))))
                return s.id;
            i = (i + 1) & mask;
        }
        uint32_t id = uint32_t(off.size());
        for (uint32_t j = 0; j < n; ++j) buf[start + j] |= 0x20;  // lower-case the stored copy
        off.push_back(start);
        len.push_back(n);
        slots[i] = Slot{prefix, h, id};
        if (uint64_t(id) * 2 > slots.size()) resize(64 - shift + 1);
        return id;
    }
};

struct Top {
    uint32_t cnt, r1, r2, a, b;
};

// True if x ranks before y in the output order.
inline bool better(const Top& x, const Top& y) {
    if (x.cnt != y.cnt) return x.cnt > y.cnt;
    if (x.r1 != y.r1) return x.r1 < y.r1;
    return x.r2 < y.r2;
}

}  // namespace

int main(int argc, char** argv) {
    if (argc < 2) {
        std::fputs("usage: solution INPUT\n", stderr);
        return 1;
    }
    FILE* f = std::fopen(argv[1], "rb");
    if (!f) {
        std::fputs("cannot open input\n", stderr);
        return 1;
    }
    std::fseek(f, 0, SEEK_END);
    long long fsize = _ftelli64(f);
    std::fseek(f, 0, SEEK_SET);
    size_t n = size_t(fsize < 0 ? 0 : fsize);
    std::unique_ptr<uint8_t[]> bufHolder(new uint8_t[n + 16]);
    uint8_t* buf = bufHolder.get();
    n = n ? std::fread(buf, 1, n, f) : 0;
    std::fclose(f);
    std::memset(buf + n, 0, 16);  // zero padding: non-letters, safe 8-byte loads

    WordTable words;
    // Word id sequence; at most one word per two bytes, plus one.
    std::unique_ptr<uint32_t[]> seq(new uint32_t[n / 2 + 2]);
    size_t nseq = 0;
    std::vector<uint32_t> deg{0};  // pairs per first word
    uint64_t totalPairs = 0;
    uint32_t prev = 0;  // previous word id in the current sentence, 0 = none

    const uint8_t* cls = kClass.t;
    size_t i = 0;
    while (i < n) {
        uint8_t c = buf[i];
        if (cls[c] != 1) {
            if (cls[c] == 2) prev = 0;
            ++i;
            continue;
        }
        // Word starting at i: fold case and hash it 8 bytes at a time.
        size_t start = i;
        uint64_t v = load64(buf + i);
        uint64_t nl = ~letterMask(v) & kHigh;
        uint64_t prefix;
        uint64_t h;
        if (nl) {
            unsigned k = unsigned(std::countr_zero(nl)) >> 3;
            uint64_t m = lowBytes(k);
            prefix = (v | kCase) & m;
            h = prefix * 0x9E3779B97F4A7C15ULL;
            i += k;
        } else {
            prefix = v | kCase;
            h = prefix * 0x9E3779B97F4A7C15ULL;
            i += 8;
            for (;;) {
                v = load64(buf + i);
                nl = ~letterMask(v) & kHigh;
                if (nl) {
                    unsigned k = unsigned(std::countr_zero(nl)) >> 3;
                    if (k) {
                        uint64_t m = lowBytes(k);
                        h = (h ^ ((v | kCase) & m)) * 0xC2B2AE3D27D4EB4FULL;
                        i += k;
                    }
                    break;
                }
                h = (h ^ (v | kCase)) * 0xC2B2AE3D27D4EB4FULL;
                i += 8;
            }
        }
        uint32_t len = uint32_t(i - start);
        h ^= h >> 31;
        h += len;
        h *= 0xBF58476D1CE4E5B9ULL;
        uint32_t id = words.intern(buf, uint32_t(start), len, prefix, uint32_t(h >> 32));
        if (id == deg.size()) deg.push_back(0);
        if (prev) {
            ++deg[prev];
            ++totalPairs;
            seq[nseq++] = id;
        } else {
            seq[nseq++] = id | kStart;
        }
        prev = id;
    }
    uint64_t totalWords = nseq;
    uint32_t nw = words.count();

    // Bucket the second word of every pair by its first word.
    std::vector<uint64_t> pos(nw + 2);
    for (uint32_t id = 1; id <= nw; ++id) pos[id + 1] = pos[id] + deg[id];
    std::vector<uint64_t> fill(pos.begin(), pos.end());
    std::unique_ptr<uint32_t[]> second(new uint32_t[totalPairs + 1]);
    for (size_t j = 1; j < nseq; ++j) {
        uint32_t x = seq[j];
        if (!(x & kStart)) second[fill[seq[j - 1] & ~kStart]++] = x;
    }
    seq.reset();

    // Lexicographic rank of each word id.
    std::vector<uint32_t> order(nw);
    for (uint32_t id = 1; id <= nw; ++id) order[id - 1] = id;
    std::sort(order.begin(), order.end(), [&](uint32_t a, uint32_t b) {
        uint32_t la = words.len[a], lb = words.len[b];
        int r = std::memcmp(buf + words.off[a], buf + words.off[b], la < lb ? la : lb);
        return r != 0 ? r < 0 : la < lb;
    });
    std::vector<uint32_t> rank(nw + 1);
    for (uint32_t r = 0; r < nw; ++r) rank[order[r]] = r;

    // Count second words per first word; keep the 20 best pairs.
    constexpr int K = 20;
    Top top[K];
    int nt = 0;
    uint64_t distinct = 0;
    std::vector<uint32_t> cnt(nw + 1, 0);
    for (uint32_t a = 1; a <= nw; ++a) {
        uint64_t lo = pos[a], hi = pos[a + 1];
        if (lo == hi) continue;
        for (uint64_t j = lo; j < hi; ++j) ++cnt[second[j]];
        for (uint64_t j = lo; j < hi; ++j) {
            uint32_t b = second[j];
            uint32_t c = cnt[b];
            if (!c) continue;
            cnt[b] = 0;
            ++distinct;
            if (nt == K && c < top[K - 1].cnt) continue;
            Top t{c, rank[a], rank[b], a, b};
            if (nt == K && !better(t, top[K - 1])) continue;
            int p = nt < K ? nt++ : K - 1;
            while (p > 0 && better(t, top[p - 1])) {
                top[p] = top[p - 1];
                --p;
            }
            top[p] = t;
        }
    }

    std::string out;
    out.reserve(4096);
    out += "words " + std::to_string(totalWords) + "\n";
    out += "pairs " + std::to_string(totalPairs) + "\n";
    out += "distinct " + std::to_string(distinct) + "\n";
    for (int t = 0; t < nt; ++t) {
        out += std::to_string(top[t].cnt);
        out += ' ';
        out.append(reinterpret_cast<const char*>(buf + words.off[top[t].a]), words.len[top[t].a]);
        out += ' ';
        out.append(reinterpret_cast<const char*>(buf + words.off[top[t].b]), words.len[top[t].b]);
        out += '\n';
    }
    _setmode(_fileno(stdout), _O_BINARY);
    std::fwrite(out.data(), 1, out.size(), stdout);
    return 0;
}
