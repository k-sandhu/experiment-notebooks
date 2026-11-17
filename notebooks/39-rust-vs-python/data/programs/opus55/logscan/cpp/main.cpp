// Log scan: single pass over the file in large chunks, hand-written matcher for the
// line grammar, custom open-addressing hash table for path templates.
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fcntl.h>
#include <io.h>
#include <memory>
#include <string>
#include <vector>

namespace {

enum : uint8_t { C_DIGIT = 1, C_LOWER = 2, C_PATH = 4 };

struct CharTable {
    uint8_t t[256]{};
    constexpr CharTable() {
        for (int c = '0'; c <= '9'; ++c) t[c] |= C_DIGIT | C_PATH;
        for (int c = 'a'; c <= 'z'; ++c) t[c] |= C_LOWER | C_PATH;
        for (int c = 'A'; c <= 'Z'; ++c) t[c] |= C_PATH;
        t['_'] |= C_PATH;
        t['-'] |= C_PATH;
        t['/'] |= C_PATH;
    }
};
constexpr CharTable kCT;

inline bool isDigit(uint8_t c) { return (unsigned)(c - '0') < 10; }

struct Slot {
    uint64_t hash;
    uint32_t off;
    uint32_t len;
    int32_t id;  // -1 = empty
};

class TemplateTable {
public:
    std::string arena;
    std::vector<uint32_t> offs, lens, counts;

    TemplateTable() : slots_(1024), mask_(1023) {
        for (auto& s : slots_) s.id = -1;
    }

    int32_t intern(const uint8_t* key, uint32_t len, uint64_t h) {
        size_t i = h & mask_;
        for (;;) {
            Slot& s = slots_[i];
            if (s.id < 0) break;
            if (s.hash == h && s.len == len && std::memcmp(arena.data() + s.off, key, len) == 0) {
                ++counts[s.id];
                return s.id;
            }
            i = (i + 1) & mask_;
        }
        int32_t id = (int32_t)offs.size();
        uint32_t off = (uint32_t)arena.size();
        arena.append((const char*)key, len);
        offs.push_back(off);
        lens.push_back(len);
        counts.push_back(1);
        slots_[i] = Slot{h, off, len, id};
        if (offs.size() * 2 > slots_.size()) grow();
        return id;
    }

    std::string_view key(int32_t id) const { return std::string_view(arena.data() + offs[id], lens[id]); }

private:
    std::vector<Slot> slots_;
    size_t mask_;

    void grow() {
        std::vector<Slot> old(slots_.size() * 2);
        old.swap(slots_);
        mask_ = slots_.size() - 1;
        for (auto& s : slots_) s.id = -1;
        for (const Slot& s : old) {
            if (s.id < 0) continue;
            size_t i = s.hash & mask_;
            while (slots_[i].id >= 0) i = (i + 1) & mask_;
            slots_[i] = s;
        }
    }
};

struct State {
    uint64_t lines = 0, malformed = 0;
    uint64_t status[10]{};
    TemplateTable table;
    std::vector<int32_t> ids;
    std::vector<int64_t> lats;
};

// Parses one line starting at p; nl points at its terminating '\n'.
// Returns true if well-formed and records it.
inline bool parseLine(const uint8_t* p, const uint8_t* nl, State& st, uint8_t* tbuf) {
    // Timestamp: dddd-dd-ddTdd:dd:dd.dddZ<space>
    if (!(isDigit(p[0]) && isDigit(p[1]) && isDigit(p[2]) && isDigit(p[3]) && p[4] == '-' && isDigit(p[5]) &&
          isDigit(p[6]) && p[7] == '-' && isDigit(p[8]) && isDigit(p[9]) && p[10] == 'T' && isDigit(p[11]) &&
          isDigit(p[12]) && p[13] == ':' && isDigit(p[14]) && isDigit(p[15]) && p[16] == ':' && isDigit(p[17]) &&
          isDigit(p[18]) && p[19] == '.' && isDigit(p[20]) && isDigit(p[21]) && isDigit(p[22]) && p[23] == 'Z' &&
          p[24] == ' '))
        return false;
    p += 25;
    // Host: [a-z]+-\d+<space>
    if (!(kCT.t[*p] & C_LOWER)) return false;
    do ++p; while (kCT.t[*p] & C_LOWER);
    if (*p != '-') return false;
    ++p;
    if (!isDigit(*p)) return false;
    do ++p; while (isDigit(*p));
    if (*p != ' ') return false;
    ++p;
    // Method
    switch (*p) {
        case 'G':
            if (p[1] != 'E' || p[2] != 'T') return false;
            p += 3;
            break;
        case 'P':
            if (p[1] == 'U' && p[2] == 'T') p += 3;
            else if (p[1] == 'O' && p[2] == 'S' && p[3] == 'T') p += 4;
            else if (p[1] == 'A' && p[2] == 'T' && p[3] == 'C' && p[4] == 'H') p += 5;
            else return false;
            break;
        case 'D':
            if (std::memcmp(p + 1, "ELETE", 5) != 0) return false;
            p += 6;
            break;
        default:
            return false;
    }
    if (*p != ' ') return false;
    ++p;
    // Path: /[A-Za-z0-9_/-]* ; build template while scanning.
    if (*p != '/') return false;
    ++p;
    uint8_t* out = tbuf;
    *out++ = '/';
    for (;;) {
        const uint8_t* seg = p;
        bool allDigit = true;
        uint8_t c;
        while (((c = *p), (kCT.t[c] & C_PATH)) && c != '/') {
            allDigit &= isDigit(c);
            ++p;
        }
        size_t n = (size_t)(p - seg);
        if (n != 0 && allDigit) {
            std::memcpy(out, "{id}", 4);
            out += 4;
        } else {
            std::memcpy(out, seg, n);
            out += n;
        }
        if (c != '/') break;
        *out++ = '/';
        ++p;
    }
    // Optional query: \?[^ ]*
    if (*p == '?') {
        p = (const uint8_t*)std::memchr(p, ' ', (size_t)(nl - p));
        if (!p) return false;
    }
    if (*p != ' ') return false;
    ++p;
    // Status: \d{3}<space>
    if (!(isDigit(p[0]) && isDigit(p[1]) && isDigit(p[2]) && p[3] == ' ')) return false;
    int cls = p[0] - '0';
    p += 4;
    // Size: \d+B<space>
    if (!isDigit(*p)) return false;
    do ++p; while (isDigit(*p));
    if (p[0] != 'B' || p[1] != ' ') return false;
    p += 2;
    // Latency: (\d+)\.(\d)ms<space>"
    if (!isDigit(*p)) return false;
    int64_t lat = 0;
    do lat = lat * 10 + (*p++ - '0');
    while (isDigit(*p));
    if (p[0] != '.' || !isDigit(p[1]) || p[2] != 'm' || p[3] != 's' || p[4] != ' ' || p[5] != '"') return false;
    lat = lat * 10 + (p[1] - '0');
    p += 6;
    // User agent: [^"]*"$
    if (nl[-1] != '"' || nl - 1 < p || std::memchr(p, '"', (size_t)(nl - 1 - p)) != nullptr) return false;

    uint32_t len = (uint32_t)(out - tbuf);
    // FNV-1a-ish 64-bit hash over the template, 8 bytes at a time.
    uint64_t h = 0x9E3779B97F4A7C15ull ^ len;
    size_t i = 0;
    for (; i + 8 <= len; i += 8) {
        uint64_t w;
        std::memcpy(&w, tbuf + i, 8);
        h = (h ^ w) * 0xFF51AFD7ED558CCDull;
        h ^= h >> 29;
    }
    if (i < len) {
        uint64_t w = 0;
        std::memcpy(&w, tbuf + i, len - i);
        h = (h ^ w) * 0xFF51AFD7ED558CCDull;
        h ^= h >> 29;
    }
    h *= 0xC4CEB9FE1A85EC53ull;
    h ^= h >> 32;

    int32_t id = st.table.intern(tbuf, len, h);
    st.status[cls]++;
    st.ids.push_back(id);
    st.lats.push_back(lat);
    return true;
}

void fmtLat(std::string& o, int64_t v) {
    o += std::to_string(v / 10);
    o += '.';
    o += (char)('0' + v % 10);
}

}  // namespace

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    FILE* f = std::fopen(argv[1], "rb");
    if (!f) return 1;

    State st;
    st.ids.reserve(1 << 21);
    st.lats.reserve(1 << 21);

    size_t cap = 1 << 22;
    std::vector<uint8_t> buf(cap + 8);
    // A template is at most 2.5x the path length, which is bounded by the buffer size.
    size_t tcap = cap * 3 + 16;
    std::unique_ptr<uint8_t[]> tbuf(new uint8_t[tcap]);
    size_t have = 0;
    for (;;) {
        size_t n = std::fread(buf.data() + have, 1, cap - have, f);
        have += n;
        if (have == 0) break;
        // Process all complete lines.
        uint8_t* base = buf.data();
        uint8_t* end = base + have;
        uint8_t* lastNl = nullptr;
        for (uint8_t* q = end; q > base;) {
            --q;
            if (*q == '\n') {
                lastNl = q;
                break;
            }
        }
        if (!lastNl) {
            if (n == 0) {
                // Trailing data without newline (not expected by spec): treat as a line.
                base[have] = '\n';
                lastNl = base + have;
                end = lastNl + 1;
                have++;
            } else {
                cap *= 2;
                buf.resize(cap + 8);
                tcap = cap * 3 + 16;
                tbuf.reset(new uint8_t[tcap]);
                continue;
            }
        }
        uint8_t* p = base;
        while (p <= lastNl) {
            st.lines++;
            uint8_t* nl = (uint8_t*)std::memchr(p, '\n', (size_t)(lastNl - p) + 1);
            if (!parseLine(p, nl, st, tbuf.get())) st.malformed++;
            p = nl + 1;
        }
        size_t rest = (size_t)(end - p);
        std::memmove(base, p, rest);
        have = rest;
        if (n == 0 && have == 0) break;
    }
    std::fclose(f);

    // Top 10 templates by count desc, then template asc.
    const auto& tbl = st.table;
    size_t nt = tbl.counts.size();
    std::vector<int32_t> top;
    auto better = [&](int32_t a, int32_t b) {
        if (tbl.counts[a] != tbl.counts[b]) return tbl.counts[a] > tbl.counts[b];
        return tbl.key(a) < tbl.key(b);
    };
    for (int32_t id = 0; id < (int32_t)nt; ++id) {
        if (top.size() == 10 && !better(id, top.back())) continue;
        auto it = std::upper_bound(top.begin(), top.end(), id, better);
        top.insert(it, id);
        if (top.size() > 10) top.pop_back();
    }

    std::vector<int> rank(nt, -1);
    std::vector<std::vector<int64_t>> buckets(top.size());
    for (size_t r = 0; r < top.size(); ++r) {
        rank[top[r]] = (int)r;
        buckets[r].reserve(tbl.counts[top[r]]);
    }
    for (size_t i = 0, n = st.ids.size(); i < n; ++i) {
        int r = rank[st.ids[i]];
        if (r >= 0) buckets[r].push_back(st.lats[i]);
    }

    std::string o;
    o += "lines " + std::to_string(st.lines) + "\n";
    o += "malformed " + std::to_string(st.malformed) + "\n";
    for (int c = 0; c < 10; ++c)
        if (st.status[c]) o += "status " + std::to_string(c) + "xx " + std::to_string(st.status[c]) + "\n";
    for (size_t r = 0; r < top.size(); ++r) {
        auto& v = buckets[r];
        size_t n = v.size();
        size_t k50 = (50 * n + 99) / 100 - 1, k95 = (95 * n + 99) / 100 - 1;
        std::nth_element(v.begin(), v.begin() + k50, v.end());
        int64_t p50 = v[k50];
        std::nth_element(v.begin() + k50, v.begin() + k95, v.end());
        int64_t p95 = v[k95];
        int64_t mx = *std::max_element(v.begin() + k95, v.end());
        o += "path ";
        o += tbl.key(top[r]);
        o += ' ';
        o += std::to_string(n);
        o += ' ';
        fmtLat(o, p50);
        o += ' ';
        fmtLat(o, p95);
        o += ' ';
        fmtLat(o, mx);
        o += '\n';
    }
    _setmode(_fileno(stdout), _O_BINARY);
    std::fwrite(o.data(), 1, o.size(), stdout);
    return 0;
}
