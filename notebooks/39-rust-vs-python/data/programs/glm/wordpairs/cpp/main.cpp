// Word pairs: count adjacent word pairs within sentences, report totals and top 20.
#include <cstdio>
#include <cstdint>
#include <cstring>
#include <vector>
#include <string>
#include <algorithm>
#include <fcntl.h>
#include <io.h>

using u8 = uint8_t;
using u32 = uint32_t;
using u64 = uint64_t;

static inline bool isLetter(unsigned c) { return (c | 32u) - 'a' <= 25u; }

static inline u64 mix64(u64 x) {
    x += 0x9E3779B97F4A7C15ull;
    x = (x ^ (x >> 30)) * 0xBF58476D1CE4E5B9ull;
    x = (x ^ (x >> 27)) * 0x94D049BB133111EBull;
    return x ^ (x >> 31);
}

static std::vector<u8> readAll(const char* path) {
    FILE* f = nullptr;
    if (fopen_s(&f, path, "rb") != 0 || !f) {
        fprintf(stderr, "cannot open %s\n", path);
        exit(1);
    }
    fseek(f, 0, SEEK_END);
    long long sz = _ftelli64(f);
    fseek(f, 0, SEEK_SET);
    std::vector<u8> buf((size_t)sz);
    if (sz > 0 && fread(buf.data(), 1, (size_t)sz, f) != (size_t)sz) {
        fprintf(stderr, "read error\n");
        exit(1);
    }
    fclose(f);
    return buf;
}

// Open-addressing map: u64 key -> u32 count. cnt == 0 marks an empty slot.
struct PairMap {
    std::vector<u64> keys;
    std::vector<u32> cnt;
    u64 mask = 0;
    u64 filled = 0;

    PairMap() { init(1 << 20); }
    void init(size_t cap) {
        size_t s = 16;
        while (s < cap) s <<= 1;
        keys.assign(s, 0);
        cnt.assign(s, 0);
        mask = s - 1;
        filled = 0;
    }
    void add(u64 key) {
        if ((filled + 1) * 4 > (mask + 1) * 3) grow();
        u64 i = mix64(key) & mask;
        for (;;) {
            if (cnt[i] == 0) {
                keys[i] = key;
                cnt[i] = 1;
                ++filled;
                return;
            }
            if (keys[i] == key) {
                ++cnt[i];
                return;
            }
            i = (i + 1) & mask;
        }
    }
    void grow() {
        std::vector<u64> ok(std::move(keys));
        std::vector<u32> oc(std::move(cnt));
        size_t ns = ok.size() * 2;
        keys.assign(ns, 0);
        cnt.assign(ns, 0);
        mask = ns - 1;
        filled = 0;
        for (size_t j = 0; j < ok.size(); ++j) {
            if (oc[j]) {
                u64 key = ok[j];
                u64 i = mix64(key) & mask;
                while (cnt[i] != 0) i = (i + 1) & mask;
                keys[i] = key;
                cnt[i] = oc[j];
                ++filled;
            }
        }
    }
};

// Interns lowercased words stored inside the shared buffer.
struct WordMap {
    const u8* buf = nullptr;
    std::vector<u32> tab; // slot -> id + 1
    std::vector<u32> off, len, hsh;
    u64 mask = 0;

    void init(const u8* b) {
        buf = b;
        size_t s = 1 << 16;
        tab.assign(s, 0);
        mask = s - 1;
        off.reserve(1 << 16);
        len.reserve(1 << 16);
        hsh.reserve(1 << 16);
    }
    u32 intern(u32 o, u32 l, u64 h) {
        u64 i = h & mask;
        for (;;) {
            u32 slot = tab[i];
            if (slot == 0) {
                u32 id = (u32)off.size();
                off.push_back(o);
                len.push_back(l);
                hsh.push_back((u32)h);
                tab[i] = id + 1;
                if ((off.size() + 1) * 2 > mask + 1) grow();
                return id;
            }
            u32 id = slot - 1;
            if (hsh[id] == (u32)h && len[id] == l &&
                memcmp(buf + off[id], buf + o, l) == 0)
                return id;
            i = (i + 1) & mask;
        }
    }
    void grow() {
        std::vector<u32> ot(std::move(tab));
        size_t ns = ot.size() * 2;
        tab.assign(ns, 0);
        mask = ns - 1;
        for (size_t j = 0; j < ot.size(); ++j) {
            if (ot[j]) {
                u32 id = ot[j] - 1;
                u64 h = hsh[id];
                u64 i = h & mask;
                while (tab[i] != 0) i = (i + 1) & mask;
                tab[i] = id + 1;
            }
        }
    }
};

struct TopEntry {
    u32 c1, c2; // word ids
    u32 cnt;
};

static const u8* g_buf;
static const std::vector<u32>* g_off;
static const std::vector<u32>* g_len;

static int cmpWords(u32 a1, u32 a2, u32 b1, u32 b2) {
    auto wa = [&](u32 id) { return g_buf + (*g_off)[id]; };
    auto la = [&](u32 id) { return (*g_len)[id]; };
    int c = memcmp(wa(a1), wa(b1), std::min(la(a1), la(b1)));
    if (c != 0) return c;
    if (la(a1) != la(b1)) return la(a1) < la(b1) ? -1 : 1;
    c = memcmp(wa(a2), wa(b2), std::min(la(a2), la(b2)));
    if (c != 0) return c;
    if (la(a2) != la(b2)) return la(a2) < la(b2) ? -1 : 1;
    return 0;
}

// "worse" = lower count, or equal count and lexicographically greater pair.
static bool worse(const TopEntry& a, const TopEntry& b) {
    if (a.cnt != b.cnt) return a.cnt < b.cnt;
    return cmpWords(a.c1, a.c2, b.c1, b.c2) > 0;
}

int main(int argc, char** argv) {
    if (argc < 2) {
        fprintf(stderr, "usage: solution INPUT_PATH\n");
        return 1;
    }
    _setmode(_fileno(stdout), _O_BINARY); // no CRLF translation
    std::vector<u8> buf = readAll(argv[1]);
    size_t n = buf.size();
    // Lowercase in place so words can be compared/printed straight from the buffer.
    for (size_t i = 0; i < n; ++i) {
        u8 c = buf[i];
        if (c >= 'A' && c <= 'Z') buf[i] = c + 32;
    }

    WordMap wm;
    wm.init(buf.data());
    PairMap pm;
    {
        size_t want = n / 8; // distinct pairs scale with input size; avoid rehashing
        size_t s = 1 << 20;
        while (s < want) s <<= 1;
        pm.init(s);
    }

    u64 words = 0, pairs = 0;
    u32 prev = 0xFFFFFFFFu; // no previous word in current sentence
    size_t i = 0;
    while (i < n) {
        u8 c = buf[i];
        if (isLetter(c)) {
            size_t start = i;
            u64 h = 0xCBF29CE484222325ull;
            do {
                h = (h ^ buf[i]) * 0x100000001B3ull;
                ++i;
            } while (i < n && isLetter(buf[i]));
            u32 id = wm.intern((u32)start, (u32)(i - start), h);
            ++words;
            if (prev != 0xFFFFFFFFu) {
                pm.add(((u64)prev << 32) | id);
                ++pairs;
            }
            prev = id;
        } else {
            if (c == '.' || c == '!' || c == '?') prev = 0xFFFFFFFFu;
            ++i;
        }
    }

    // Keep the 20 best pairs in a min-heap while scanning the pair table.
    g_buf = buf.data();
    g_off = &wm.off;
    g_len = &wm.len;

    TopEntry heap[20];
    int hn = 0;
    for (u64 j = 0; j <= pm.mask; ++j) {
        if (!pm.cnt[j]) continue;
        TopEntry e{ (u32)(pm.keys[j] >> 32), (u32)pm.keys[j], pm.cnt[j] };
        if (hn < 20) {
            int k = hn++;
            heap[k] = e;
            while (k > 0) {
                int p = (k - 1) / 2;
                if (worse(heap[k], heap[p])) { std::swap(heap[p], heap[k]); k = p; }
                else break;
            }
        } else if (worse(heap[0], e)) {
            heap[0] = e;
            int k = 0;
            for (;;) {
                int l = 2 * k + 1, r = l + 1, m = k;
                if (l < hn && worse(heap[l], heap[m])) m = l;
                if (r < hn && worse(heap[r], heap[m])) m = r;
                if (m == k) break;
                std::swap(heap[m], heap[k]);
                k = m;
            }
        }
    }
    std::sort(heap, heap + hn, [](const TopEntry& a, const TopEntry& b) {
        if (a.cnt != b.cnt) return a.cnt > b.cnt;
        return cmpWords(a.c1, a.c2, b.c1, b.c2) < 0;
    });

    std::string out;
    out.reserve(4096 + 32 * hn);
    auto num = [&](u64 v) {
        char tmp[24];
        int k = 0;
        do { tmp[k++] = char('0' + v % 10); v /= 10; } while (v);
        while (k) out += tmp[--k];
    };
    auto word = [&](u32 id) { out.append((const char*)g_buf + wm.off[id], wm.len[id]); };

    out += "words "; num(words); out += '\n';
    out += "pairs "; num(pairs); out += '\n';
    out += "distinct "; num(pm.filled); out += '\n';
    for (int k = 0; k < hn; ++k) {
        num(heap[k].cnt); out += ' ';
        word(heap[k].c1); out += ' ';
        word(heap[k].c2); out += '\n';
    }
    fwrite(out.data(), 1, out.size(), stdout);
    return 0;
}
