// Ledger: fast single-pass JSON Lines aggregator.
// Hand-rolled scanner over the whole input buffer (no DOM), custom open-addressing maps.
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fcntl.h>
#include <io.h>
#include <string>
#include <string_view>
#include <vector>

namespace {

constexpr uint64_t FNV_OFFSET = 1469598103934665603ULL;
constexpr uint64_t FNV_PRIME = 1099511628211ULL;

inline uint64_t hashBytes(const char* s, size_t len) {
    uint64_t h = FNV_OFFSET;
    for (size_t j = 0; j < len; ++j) {
        h ^= static_cast<unsigned char>(s[j]);
        h *= FNV_PRIME;
    }
    return h;
}

struct ChVal {
    int64_t net = 0;
    int64_t count = 0;
};

// Open-addressing map keyed by (ptr, len). Keys must outlive the map: either they
// point into the input buffer, or a copy is kept in `owned`.
template <class Val>
struct HashMap {
    struct Slot {
        const char* key;
        uint32_t keyLen;
        uint64_t hash;
        Val val;
    };
    std::vector<Slot> slots;
    size_t mask = 0;
    size_t count = 0;
    std::vector<std::string> owned;

    explicit HashMap(size_t logSlots = 4) : slots(size_t(1) << logSlots), mask((size_t(1) << logSlots) - 1) {}

    void grow() {
        std::vector<Slot> ns(slots.size() * 2);
        size_t nm = ns.size() - 1;
        for (const auto& s : slots) {
            if (!s.key) continue;
            size_t j = s.hash & nm;
            while (ns[j].key) j = (j + 1) & nm;
            ns[j] = s;
        }
        slots.swap(ns);
        mask = nm;
    }

    Val* find(const char* key, uint32_t len, uint64_t h) {
        size_t j = h & mask;
        while (slots[j].key) {
            if (slots[j].hash == h && slots[j].keyLen == len && memcmp(slots[j].key, key, len) == 0)
                return &slots[j].val;
            j = (j + 1) & mask;
        }
        return nullptr;
    }

    Val& at(const char* key, uint32_t len, uint64_t h) {
        if ((count + 1) * 2 > slots.size()) grow();
        size_t j = h & mask;
        while (slots[j].key) {
            if (slots[j].hash == h && slots[j].keyLen == len && memcmp(slots[j].key, key, len) == 0)
                return slots[j].val;
            j = (j + 1) & mask;
        }
        slots[j] = {key, len, h, Val()};
        ++count;
        return slots[j].val;
    }

    void keep(const char* key, uint32_t len) { owned.emplace_back(key, len); }
};

// ---- scanner state ----
const char* p;
size_t n;
size_t i;

inline void skipWs() {
    while (i < n) {
        char c = p[i];
        if (c == ' ' || c == '\t' || c == '\r' || c == '\n')
            ++i;
        else
            break;
    }
}

size_t sStart, sEnd;
bool sEsc;

void skipString() {  // i at opening quote; leaves i past closing quote
    ++i;
    while (true) {
        char c = p[i];
        if (c == '\\') {
            i += 2;  // the escape char and, for \u, the 4 hex digits contain no '"' or '\\'
            continue;
        }
        if (c == '"') {
            ++i;
            return;
        }
        ++i;
    }
}

void scanString() {  // i at opening quote; leaves i past closing quote
    ++i;
    sStart = i;
    sEsc = false;
    while (true) {
        char c = p[i];
        if (c == '\\') {
            sEsc = true;
            i += 2;
            continue;
        }
        if (c == '"') {
            sEnd = i;
            ++i;
            return;
        }
        ++i;
    }
}

void skipValue() {
    char c = p[i];
    if (c == '"') {
        skipString();
        return;
    }
    if (c == '{' || c == '[') {
        int depth = 0;
        while (i < n) {
            char d = p[i];
            if (d == '"') {
                skipString();
                continue;
            }
            if (d == '{' || d == '[')
                ++depth;
            else if (d == '}' || d == ']') {
                --depth;
                if (depth == 0) {
                    ++i;
                    return;
                }
            }
            ++i;
        }
        return;
    }
    while (i < n) {
        char d = p[i];
        if (d == ',' || d == '}' || d == ']' || d == ' ' || d == '\t' || d == '\r' || d == '\n') return;
        ++i;
    }
}

// ---- string decoding ----
std::vector<char> scratch;

unsigned hex4(const char* s, size_t at) {
    unsigned v = 0;
    for (int k = 0; k < 4; ++k) {
        char c = s[at + k];
        v <<= 4;
        if (c <= '9')
            v += static_cast<unsigned>(c - '0');
        else if (c <= 'F')
            v += static_cast<unsigned>(c - 'A' + 10);
        else
            v += static_cast<unsigned>(c - 'a' + 10);
    }
    return v;
}

size_t decode(char* dst, const char* s, size_t len) {
    size_t o = 0, j = 0;
    while (j < len) {
        char c = s[j];
        if (c != '\\') {
            dst[o++] = c;
            ++j;
            continue;
        }
        char e = s[j + 1];
        j += 2;
        switch (e) {
            case '"': dst[o++] = '"'; break;
            case '\\': dst[o++] = '\\'; break;
            case '/': dst[o++] = '/'; break;
            case 'b': dst[o++] = '\b'; break;
            case 'f': dst[o++] = '\f'; break;
            case 'n': dst[o++] = '\n'; break;
            case 'r': dst[o++] = '\r'; break;
            case 't': dst[o++] = '\t'; break;
            case 'u': {
                unsigned cp = hex4(s, j);
                j += 4;
                if (cp >= 0xD800 && cp <= 0xDBFF && j + 1 < len && s[j] == '\\' && s[j + 1] == 'u') {
                    unsigned lo = hex4(s, j + 2);
                    if (lo >= 0xDC00 && lo <= 0xDFFF) {
                        cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
                        j += 6;
                    }
                }
                if (cp < 0x80) {
                    dst[o++] = static_cast<char>(cp);
                } else if (cp < 0x800) {
                    dst[o++] = static_cast<char>(0xC0 | (cp >> 6));
                    dst[o++] = static_cast<char>(0x80 | (cp & 0x3F));
                } else if (cp < 0x10000) {
                    dst[o++] = static_cast<char>(0xE0 | (cp >> 12));
                    dst[o++] = static_cast<char>(0x80 | ((cp >> 6) & 0x3F));
                    dst[o++] = static_cast<char>(0x80 | (cp & 0x3F));
                } else {
                    dst[o++] = static_cast<char>(0xF0 | (cp >> 18));
                    dst[o++] = static_cast<char>(0x80 | ((cp >> 12) & 0x3F));
                    dst[o++] = static_cast<char>(0x80 | ((cp >> 6) & 0x3F));
                    dst[o++] = static_cast<char>(0x80 | (cp & 0x3F));
                }
                break;
            }
            default: dst[o++] = e; break;
        }
    }
    return o;
}

inline char* scratchBuf(size_t need) {
    if (scratch.size() < need) scratch.resize(need);
    return scratch.data();
}

bool strEq(const char* s, size_t len, bool esc, const char* lit, size_t litLen) {
    if (!esc) return len == litLen && memcmp(s, lit, len) == 0;
    if (litLen > len) return false;  // decoding never grows the string
    size_t dn = decode(scratchBuf(len), s, len);
    return dn == litLen && memcmp(scratch.data(), lit, dn) == 0;
}

// Key that must outlive this line: raw slices point into the buffer, escaped
// strings are decoded and copied into `owned`.
std::string_view keyValueInto(std::vector<std::string>& owned, const char* s, size_t len, bool esc) {
    if (!esc) return std::string_view(s, len);
    size_t dn = decode(scratchBuf(len), s, len);
    owned.emplace_back(scratch.data(), dn);
    return owned.back();
}

long long parseAmount(const char* s, size_t len) {
    long long ip = 0;
    size_t j = 0;
    while (j < len && s[j] >= '0' && s[j] <= '9') {
        ip = ip * 10 + (s[j] - '0');
        ++j;
    }
    long long frac = 0;
    int fd = 0;
    if (j < len && s[j] == '.') {
        ++j;
        while (j < len && fd < 2 && s[j] >= '0' && s[j] <= '9') {
            frac = frac * 10 + (s[j] - '0');
            ++fd;
            ++j;
        }
    }
    while (fd < 2) {
        frac *= 10;
        ++fd;
    }
    return ip * 100 + frac;
}

void appendInt(std::string& out, long long v) {
    char tmp[24];
    int k = 24;
    bool neg = v < 0;
    unsigned long long u = neg ? (0ULL - static_cast<unsigned long long>(v)) : static_cast<unsigned long long>(v);
    do {
        tmp[--k] = static_cast<char>('0' + (u % 10));
        u /= 10;
    } while (u);
    if (neg) tmp[--k] = '-';
    out.append(tmp + k, 24 - k);
}

void parseTags(bool& testTag) {
    ++i;  // '['
    while (true) {
        skipWs();
        if (p[i] == ']') {
            ++i;
            return;
        }
        if (p[i] == '"') {
            scanString();
            if (!testTag && strEq(p + sStart, sEnd - sStart, sEsc, "test", 4)) testTag = true;
        } else {
            skipValue();
        }
        skipWs();
        if (p[i] == ',') ++i;
    }
}

void parseMeta(const char*& chPtr, size_t& chLen, bool& chEsc) {
    ++i;  // '{'
    while (true) {
        skipWs();
        if (p[i] == '}') {
            ++i;
            return;
        }
        scanString();
        const char* ks = p + sStart;
        size_t klen = sEnd - sStart;
        bool kesc = sEsc;
        skipWs();
        ++i;  // ':'
        skipWs();
        if (!kesc && klen == 7 && memcmp(ks, "channel", 7) == 0) {
            scanString();
            chPtr = p + sStart;
            chLen = sEnd - sStart;
            chEsc = sEsc;
        } else if (kesc && strEq(ks, klen, kesc, "channel", 7)) {
            scanString();
            chPtr = p + sStart;
            chLen = sEnd - sStart;
            chEsc = sEsc;
        } else {
            skipValue();
        }
        skipWs();
        if (p[i] == ',') ++i;
    }
}

}  // namespace

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    _setmode(_fileno(stdout), _O_BINARY);

    FILE* f = fopen(argv[1], "rb");
    if (!f) return 1;
    fseek(f, 0, SEEK_END);
    long sz = ftell(f);
    fseek(f, 0, SEEK_SET);
    std::vector<char> buf(static_cast<size_t>(sz));
    if (sz > 0 && fread(buf.data(), 1, static_cast<size_t>(sz), f) != static_cast<size_t>(sz)) return 1;
    fclose(f);

    p = buf.data();
    n = static_cast<size_t>(sz);
    i = 0;

    HashMap<int64_t> rates;
    HashMap<ChVal> channels;
    HashMap<int64_t> accounts;
    std::vector<std::string> ownedKeys;

    // ---- first line: rates ----
    skipWs();
    ++i;  // '{'
    while (true) {
        skipWs();
        scanString();
        const char* ks = p + sStart;
        size_t klen = sEnd - sStart;
        bool kesc = sEsc;
        skipWs();
        ++i;  // ':'
        skipWs();
        if (!kesc && klen == 5 && memcmp(ks, "rates", 5) == 0) {
            ++i;  // '{'
            while (true) {
                skipWs();
                if (p[i] == '}') {
                    ++i;
                    break;
                }
                scanString();
                std::string_view cur = keyValueInto(ownedKeys, p + sStart, sEnd - sStart, sEsc);
                skipWs();
                ++i;  // ':'
                skipWs();
                int64_t r = 0;
                while (p[i] >= '0' && p[i] <= '9') {
                    r = r * 10 + (p[i] - '0');
                    ++i;
                }
                uint64_t h = hashBytes(cur.data(), cur.size());
                rates.at(cur.data(), static_cast<uint32_t>(cur.size()), h) = r;
                skipWs();
                if (p[i] == ',') ++i;
            }
        } else {
            skipValue();
        }
        skipWs();
        if (p[i] == ',') {
            ++i;
            continue;
        }
        ++i;
        break;
    }

    // ---- transactions ----
    int64_t totalCount = 0;
    int64_t totalNet = 0;

    while (true) {
        skipWs();
        if (i >= n) break;
        ++i;  // '{'

        const char* typePtr = nullptr;
        size_t typeLen = 0;
        bool typeEsc = false;
        const char* amtPtr = nullptr;
        size_t amtLen = 0;
        bool amtEsc = false;
        const char* curPtr = nullptr;
        size_t curLen = 0;
        bool curEsc = false;
        const char* accPtr = nullptr;
        size_t accLen = 0;
        bool accEsc = false;
        const char* chPtr = nullptr;
        size_t chLen = 0;
        bool chEsc = false;
        bool testTag = false;

        while (true) {
            skipWs();
            scanString();
            const char* ks = p + sStart;
            size_t klen = sEnd - sStart;
            bool kesc = sEsc;
            skipWs();
            ++i;  // ':'
            skipWs();
            if (!kesc) {
                char c0 = klen ? ks[0] : 0;
                if (klen == 4 && c0 == 't' && memcmp(ks, "type", 4) == 0) {
                    scanString();
                    typePtr = p + sStart;
                    typeLen = sEnd - sStart;
                    typeEsc = sEsc;
                } else if (klen == 6 && memcmp(ks, "amount", 6) == 0) {
                    scanString();
                    amtPtr = p + sStart;
                    amtLen = sEnd - sStart;
                    amtEsc = sEsc;
                } else if (klen == 8 && memcmp(ks, "currency", 8) == 0) {
                    scanString();
                    curPtr = p + sStart;
                    curLen = sEnd - sStart;
                    curEsc = sEsc;
                } else if (klen == 7 && memcmp(ks, "account", 7) == 0) {
                    scanString();
                    accPtr = p + sStart;
                    accLen = sEnd - sStart;
                    accEsc = sEsc;
                } else if (klen == 4 && c0 == 't' && memcmp(ks, "tags", 4) == 0) {
                    parseTags(testTag);
                } else if (klen == 4 && c0 == 'm' && memcmp(ks, "meta", 4) == 0) {
                    parseMeta(chPtr, chLen, chEsc);
                } else {
                    skipValue();
                }
            } else {
                size_t dn = decode(scratchBuf(klen), ks, klen);
                if (dn == 4 && memcmp(scratch.data(), "type", 4) == 0) {
                    scanString();
                    typePtr = p + sStart;
                    typeLen = sEnd - sStart;
                    typeEsc = sEsc;
                } else if (dn == 6 && memcmp(scratch.data(), "amount", 6) == 0) {
                    scanString();
                    amtPtr = p + sStart;
                    amtLen = sEnd - sStart;
                    amtEsc = sEsc;
                } else if (dn == 8 && memcmp(scratch.data(), "currency", 8) == 0) {
                    scanString();
                    curPtr = p + sStart;
                    curLen = sEnd - sStart;
                    curEsc = sEsc;
                } else if (dn == 7 && memcmp(scratch.data(), "account", 7) == 0) {
                    scanString();
                    accPtr = p + sStart;
                    accLen = sEnd - sStart;
                    accEsc = sEsc;
                } else if (dn == 4 && memcmp(scratch.data(), "tags", 4) == 0) {
                    parseTags(testTag);
                } else if (dn == 4 && memcmp(scratch.data(), "meta", 4) == 0) {
                    parseMeta(chPtr, chLen, chEsc);
                } else {
                    skipValue();
                }
            }
            skipWs();
            if (p[i] == ',') {
                ++i;
                continue;
            }
            ++i;  // '}'
            break;
        }

        if (strEq(typePtr, typeLen, typeEsc, "void", 4)) continue;
        if (testTag) continue;

        // currency -> rate
        std::string_view cur;
        if (!curEsc) {
            cur = std::string_view(curPtr, curLen);
        } else {
            size_t dn = decode(scratchBuf(curLen), curPtr, curLen);
            cur = std::string_view(scratch.data(), dn);
        }
        uint64_t curHash = hashBytes(cur.data(), cur.size());
        int64_t* rate = rates.find(cur.data(), static_cast<uint32_t>(cur.size()), curHash);
        if (!rate) continue;

        long long hund;
        if (!amtEsc) {
            hund = parseAmount(amtPtr, amtLen);
        } else {
            size_t dn = decode(scratchBuf(amtLen), amtPtr, amtLen);
            hund = parseAmount(scratch.data(), dn);
        }
        long long usd = (hund * (*rate)) / 1000000;
        long long v = strEq(typePtr, typeLen, typeEsc, "debit", 5) ? -usd : usd;

        totalCount += 1;
        totalNet += v;

        // channel
        std::string_view chKey;
        if (!chEsc) {
            chKey = std::string_view(chPtr, chLen);
        } else {
            size_t dn = decode(scratchBuf(chLen), chPtr, chLen);
            channels.keep(scratch.data(), static_cast<uint32_t>(dn));
            chKey = channels.owned.back();
        }
        uint64_t chHash = hashBytes(chKey.data(), chKey.size());
        ChVal& cv = channels.at(chKey.data(), static_cast<uint32_t>(chKey.size()), chHash);
        cv.net += v;
        cv.count += 1;

        // account
        std::string_view accKey;
        if (!accEsc) {
            accKey = std::string_view(accPtr, accLen);
        } else {
            size_t dn = decode(scratchBuf(accLen), accPtr, accLen);
            accounts.keep(scratch.data(), static_cast<uint32_t>(dn));
            accKey = accounts.owned.back();
        }
        uint64_t accHash = hashBytes(accKey.data(), accKey.size());
        accounts.at(accKey.data(), static_cast<uint32_t>(accKey.size()), accHash) += v;
    }

    // ---- output ----
    std::string out;
    out.reserve(1 << 20);
    out.append("counted ", 8);
    appendInt(out, totalCount);
    out.push_back('\n');
    out.append("net ", 4);
    appendInt(out, totalNet);
    out.push_back('\n');

    std::vector<const typename HashMap<ChVal>::Slot*> chRows;
    chRows.reserve(channels.count);
    for (const auto& s : channels.slots)
        if (s.key) chRows.push_back(&s);
    std::sort(chRows.begin(), chRows.end(), [](const HashMap<ChVal>::Slot* a, const HashMap<ChVal>::Slot* b) {
        std::string_view ka(a->key, a->keyLen), kb(b->key, b->keyLen);
        return ka < kb;
    });
    for (const auto* s : chRows) {
        out.append("channel ", 8);
        out.append(s->key, s->keyLen);
        out.push_back(' ');
        appendInt(out, s->val.count);
        out.push_back(' ');
        appendInt(out, s->val.net);
        out.push_back('\n');
    }

    std::vector<std::pair<int64_t, std::string_view>> accRows;
    accRows.reserve(accounts.count);
    for (const auto& s : accounts.slots)
        if (s.key) accRows.emplace_back(s.val, std::string_view(s.key, s.keyLen));
    std::sort(accRows.begin(), accRows.end(), [](const auto& a, const auto& b) {
        if (a.first != b.first) return a.first > b.first;
        return a.second < b.second;
    });
    size_t lim = accRows.size() < 10 ? accRows.size() : 10;
    for (size_t k = 0; k < lim; ++k) {
        out.append("account ", 8);
        out.append(accRows[k].second.data(), accRows[k].second.size());
        out.push_back(' ');
        appendInt(out, accRows[k].first);
        out.push_back('\n');
    }

    fwrite(out.data(), 1, out.size(), stdout);
    return 0;
}
