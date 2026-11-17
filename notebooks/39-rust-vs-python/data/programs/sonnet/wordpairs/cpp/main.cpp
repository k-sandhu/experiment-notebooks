#include <cstdio>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <vector>
#include <algorithm>
#include <io.h>
#include <immintrin.h>
#include <fcntl.h>

namespace {

struct WordInfo { uint32_t start, len; uint64_t hash; };
struct WSlot { uint32_t id1; uint32_t h; };  // id1 = id+1, 0 = empty
struct PSlot { uint64_t key; uint32_t count; uint32_t pad; };

constexpr uint64_t EMPTY = ~0ULL;

std::vector<WordInfo> words;
std::vector<WSlot> wtab;
uint32_t wmask;
const unsigned char* buf;

void growWords() {
    size_t ncap = wtab.size() * 2;
    std::vector<WSlot> nt(ncap, WSlot{0, 0});
    uint32_t nmask = (uint32_t)ncap - 1;
    for (uint32_t id = 0; id < words.size(); id++) {
        uint32_t p = (uint32_t)(words[id].hash >> 20) & nmask;
        while (nt[p].id1) p = (p + 1) & nmask;
        nt[p] = WSlot{id + 1, (uint32_t)words[id].hash};
    }
    wtab.swap(nt);
    wmask = nmask;
}

inline uint32_t lookupWord(uint32_t start, uint32_t len, uint64_t h) {
    uint32_t p = (uint32_t)(h >> 20) & wmask;
    uint32_t h32 = (uint32_t)h;
    const unsigned char* s = buf + start;
    for (;;) {
        WSlot& sl = wtab[p];
        if (!sl.id1) break;
        if (sl.h == h32) {
            const WordInfo& w = words[sl.id1 - 1];
            if (w.len == len) {
                const unsigned char* t = buf + w.start;
                uint32_t k = 0;
                while (k < len && ((s[k] ^ t[k]) | 0x20) == 0x20) k++;  // equal ignoring case (letters only)
                if (k == len) return sl.id1 - 1;
            }
        }
        p = (p + 1) & wmask;
    }
    uint32_t id = (uint32_t)words.size();
    words.push_back(WordInfo{start, len, h});
    wtab[p] = WSlot{id + 1, h32};
    if (words.size() * 2 > wtab.size()) growWords();
    return id;
}


constexpr uint64_t PM = 0x9E3779B97F4A7C15ULL;
constexpr uint32_t NONE = 0xFFFFFFFFu;
PSlot* ptab;
size_t pcap, pmask;
int pshift;
size_t distinctCount = 0;
uint64_t Tcount = 0;

void growPairs() {
    size_t ncap = pcap * 2;
    int nshift = pshift - 1;
    PSlot* nt = (PSlot*)malloc(ncap * sizeof(PSlot));
    for (size_t q = 0; q < ncap; q++) nt[q].key = EMPTY, nt[q].count = 0;
    size_t nmask = ncap - 1;
    for (size_t q = 0; q < pcap; q++) {
        if (ptab[q].key == EMPTY) continue;
        size_t pp = (size_t)((ptab[q].key * PM) >> nshift);
        while (nt[pp].key != EMPTY) pp = (pp + 1) & nmask;
        nt[pp] = ptab[q];
    }
    free(ptab);
    ptab = nt; pcap = ncap; pshift = nshift; pmask = nmask;
}

// ids[0..cnt]: ids[0] is the previous word (or NONE); NONE marks a sentence end.
void flush(const uint32_t* ids, size_t cnt) {
    for (size_t k = 1; k <= cnt; k++) {
        uint64_t key = ((uint64_t)ids[k - 1] << 32) | ids[k];
        _mm_prefetch((const char*)&ptab[(size_t)((key * PM) >> pshift)], _MM_HINT_T0);
    }
    for (size_t k = 1; k <= cnt; k++) {
        if (ids[k - 1] == NONE || ids[k] == NONE) continue;
        Tcount++;
        uint64_t key = ((uint64_t)ids[k - 1] << 32) | ids[k];
        size_t p = (size_t)((key * PM) >> pshift);
        for (;;) {
            PSlot& s = ptab[p];
            if (s.key == key) { s.count++; break; }
            if (s.key == EMPTY) {
                s.key = key; s.count = 1; distinctCount++;
                if (distinctCount * 10 > pcap * 7) growPairs();
                break;
            }
            p = (p + 1) & pmask;
        }
    }
}

struct Top { uint32_t count, a, b; };

int cmpWords(uint32_t x, uint32_t y) {
    if (x == y) return 0;
    const WordInfo& wx = words[x];
    const WordInfo& wy = words[y];
    uint32_t n = wx.len < wy.len ? wx.len : wy.len;
    for (uint32_t i = 0; i < n; i++) {
        unsigned char cx = buf[wx.start + i] | 0x20, cy = buf[wy.start + i] | 0x20;
        if (cx != cy) return cx < cy ? -1 : 1;
    }
    return wx.len < wy.len ? -1 : (wx.len > wy.len ? 1 : 0);
}

bool better(const Top& x, const Top& y) {
    if (x.count != y.count) return x.count > y.count;
    int c = cmpWords(x.a, y.a);
    if (c) return c < 0;
    return cmpWords(x.b, y.b) < 0;
}

void printWord(uint32_t id) {
    const WordInfo& w = words[id];
    char tmp[256];
    uint32_t pos = 0;
    while (pos < w.len) {
        uint32_t n = std::min<uint32_t>(256, w.len - pos);
        for (uint32_t i = 0; i < n; i++) tmp[i] = (char)(buf[w.start + pos + i] | 0x20);
        fwrite(tmp, 1, n, stdout);
        pos += n;
    }
}

}  // namespace

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    _setmode(1, _O_BINARY);
    FILE* f = fopen(argv[1], "rb");
    if (!f) return 1;
    _fseeki64(f, 0, SEEK_END);
    size_t n = (size_t)_ftelli64(f);
    _fseeki64(f, 0, SEEK_SET);
    unsigned char* data = (unsigned char*)malloc(n + 1);
    size_t got = fread(data, 1, n, f);
    fclose(f);
    n = got;
    data[n] = '\n';
    buf = data;

    wtab.assign(1 << 16, WSlot{0, 0});
    wmask = (1 << 16) - 1;
    words.reserve(1 << 15);

    pcap = 1 << 16;
    while (pcap < n / 12 && pcap < ((size_t)1 << 28)) pcap <<= 1;
    pshift = 64;
    for (size_t t = pcap; t > 1; t >>= 1) pshift--;
    pmask = pcap - 1;
    ptab = (PSlot*)malloc(pcap * sizeof(PSlot));
    for (size_t i = 0; i < pcap; i++) ptab[i].key = EMPTY, ptab[i].count = 0;
    uint64_t W = 0;
    constexpr size_t B = 512;
    uint32_t ids[B + 1];
    ids[0] = NONE;
    size_t cnt = 0;

    size_t i = 0;
    while (i < n) {
        unsigned char c = data[i];
        if (((c | 0x20) - 'a') < 26u) {
            size_t st = i;
            uint64_t h = 0xcbf29ce484222325ULL;
            do {
                h = (h ^ (c | 0x20)) * 0x100000001b3ULL;
                c = data[++i];
            } while (((c | 0x20) - 'a') < 26u);
            h ^= h >> 29; h *= PM; h ^= h >> 32;
            ids[++cnt] = lookupWord((uint32_t)st, (uint32_t)(i - st), h);
            W++;
            if (cnt == B) { flush(ids, cnt); ids[0] = ids[B]; cnt = 0; }
        } else {
            if (c == '.' || c == '!' || c == '?') {
                if (cnt == B) { flush(ids, cnt); ids[0] = ids[B]; cnt = 0; }
                if (ids[cnt] != NONE) ids[++cnt] = NONE;
                if (cnt == B) { flush(ids, cnt); ids[0] = ids[B]; cnt = 0; }
            }
            i++;
        }
    }
    flush(ids, cnt);
    uint64_t T = Tcount;
    size_t distinct = distinctCount;

    Top top[21];
    int nt = 0;
    for (size_t q = 0; q < pcap; q++) {
        const PSlot& s = ptab[q];
        if (s.key == EMPTY) continue;
        if (nt == 20 && s.count < top[19].count) continue;
        Top t{s.count, (uint32_t)(s.key >> 32), (uint32_t)s.key};
        if (nt == 20 && !better(t, top[19])) continue;
        int j = nt < 20 ? nt++ : 19;
        while (j > 0 && better(t, top[j - 1])) { top[j] = top[j - 1]; j--; }
        top[j] = t;
    }

    printf("words %llu\npairs %llu\ndistinct %llu\n", (unsigned long long)W, (unsigned long long)T, (unsigned long long)distinct);
    for (int k = 0; k < nt; k++) {
        printf("%u ", top[k].count);
        printWord(top[k].a);
        putchar(' ');
        printWord(top[k].b);
        putchar('\n');
    }
    return 0;
}
