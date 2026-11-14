// Ledger: streams a JSON Lines file, parses only the fields it needs, and sums
// converted amounts per channel and per account with exact integer arithmetic.

#include <algorithm>
#include <charconv>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fcntl.h>
#include <io.h>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace {

// A decoded JSON string: points into the input, or into a scratch buffer when it had escapes.
struct Str {
    const char* p = nullptr;
    size_t n = 0;
    std::string_view view() const { return {p, n}; }
};

template <size_t N>
bool eq(const Str& s, const char (&lit)[N]) {
    return s.n == N - 1 && std::memcmp(s.p, lit, N - 1) == 0;
}

inline void skipWs(const char*& p) {
    while (*p == ' ' || *p == '\t' || *p == '\r' || *p == '\n') ++p;
}

// p points at an opening quote; returns the position after the closing quote.
inline const char* skipString(const char* p) {
    ++p;
    while (*p != '"') p += (*p == '\\') ? 2 : 1;
    return p + 1;
}

// Skips any JSON value starting at p and returns the position just after it.
const char* skipValue(const char* p) {
    if (*p == '"') return skipString(p);
    if (*p == '{' || *p == '[') {
        int depth = 0;
        for (;;) {
            char c = *p;
            if (c == '"') {
                p = skipString(p);
                continue;
            }
            if (c == '{' || c == '[') {
                ++depth;
            } else if (c == '}' || c == ']') {
                if (--depth == 0) return p + 1;
            }
            ++p;
        }
    }
    while (*p != ',' && *p != '}' && *p != ']' && *p != ' ' && *p != '\t' && *p != '\r' && *p != '\n') ++p;
    return p;
}

uint32_t hex4(const char* p) {
    uint32_t v = 0;
    for (int i = 0; i < 4; ++i) {
        char c = p[i];
        v = v * 16 + (c <= '9' ? uint32_t(c - '0') : uint32_t((c | 0x20) - 'a' + 10));
    }
    return v;
}

void appendUtf8(std::string& out, uint32_t cp) {
    if (cp < 0x80) {
        out.push_back(char(cp));
    } else if (cp < 0x800) {
        out.push_back(char(0xC0 | (cp >> 6)));
        out.push_back(char(0x80 | (cp & 0x3F)));
    } else if (cp < 0x10000) {
        out.push_back(char(0xE0 | (cp >> 12)));
        out.push_back(char(0x80 | ((cp >> 6) & 0x3F)));
        out.push_back(char(0x80 | (cp & 0x3F)));
    } else {
        out.push_back(char(0xF0 | (cp >> 18)));
        out.push_back(char(0x80 | ((cp >> 12) & 0x3F)));
        out.push_back(char(0x80 | ((cp >> 6) & 0x3F)));
        out.push_back(char(0x80 | (cp & 0x3F)));
    }
}

// Decodes the JSON escapes in [p, e) into out.
void decode(const char* p, const char* e, std::string& out) {
    out.clear();
    while (p < e) {
        if (*p != '\\') {
            out.push_back(*p++);
            continue;
        }
        char c = p[1];
        p += 2;
        switch (c) {
            case 'b': out.push_back('\b'); break;
            case 'f': out.push_back('\f'); break;
            case 'n': out.push_back('\n'); break;
            case 'r': out.push_back('\r'); break;
            case 't': out.push_back('\t'); break;
            case 'u': {
                uint32_t cp = hex4(p);
                p += 4;
                if (cp >= 0xD800 && cp <= 0xDBFF && p[0] == '\\' && p[1] == 'u') {
                    uint32_t lo = hex4(p + 2);
                    if (lo >= 0xDC00 && lo <= 0xDFFF) {
                        cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
                        p += 6;
                    }
                }
                appendUtf8(out, cp);
                break;
            }
            default: out.push_back(c); break;  // \" \\ \/
        }
    }
}

// p points at an opening quote; returns the position after the closing quote.
// The value is a view into the input unless it has escapes, then it is decoded into scratch.
inline const char* readString(const char* p, Str& out, std::string& scratch) {
    const char* start = ++p;
    bool escaped = false;
    while (*p != '"') {
        if (*p == '\\') {
            escaped = true;
            ++p;
        }
        ++p;
    }
    if (escaped) {
        decode(start, p, scratch);
        out.p = scratch.data();
        out.n = scratch.size();
    } else {
        out.p = start;
        out.n = size_t(p - start);
    }
    return p + 1;
}

// Calls f(key, pos) for each member of the object at p; f returns the position after the value.
template <class F>
const char* forEachMember(const char* p, F&& f, std::string& keyScratch) {
    ++p;  // '{'
    skipWs(p);
    if (*p == '}') return p + 1;
    for (;;) {
        skipWs(p);
        Str key;
        p = readString(p, key, keyScratch);
        skipWs(p);
        ++p;  // ':'
        skipWs(p);
        p = f(key, p);
        skipWs(p);
        if (*p++ == '}') return p;  // otherwise it was ','
    }
}

// Calls f(pos) for each element of the array at p; f returns the position after the element.
template <class F>
const char* forEachElement(const char* p, F&& f) {
    ++p;  // '['
    skipWs(p);
    if (*p == ']') return p + 1;
    for (;;) {
        skipWs(p);
        p = f(p);
        skipWs(p);
        if (*p++ == ']') return p;  // otherwise it was ','
    }
}

// Parses an amount such as "12", "12.5" or "12.05" into hundredths.
int64_t toHundredths(Str a) {
    int64_t v = 0;
    size_t i = 0;
    for (; i < a.n && a.p[i] != '.'; ++i) v = v * 10 + (a.p[i] - '0');
    v *= 100;
    if (i < a.n) {
        ++i;
        int64_t frac = 0;
        int digits = 0;
        for (; digits < 2 && i < a.n; ++i, ++digits) frac = frac * 10 + (a.p[i] - '0');
        if (digits == 1) frac *= 10;
        v += frac;
    }
    return v;
}

// Maps byte-string keys to dense indexes, keeping a sum and a count per key.
class KeyIndex {
public:
    KeyIndex() : slots_(1024, 0), mask_(1023) {}

    size_t find(std::string_view k) {
        size_t h = hashOf(k) & mask_;
        for (;;) {
            uint32_t s = slots_[h];
            if (s == 0) break;
            if (keys_[s - 1] == k) return s - 1;
            h = (h + 1) & mask_;
        }
        keys_.emplace_back(k);
        sums_.push_back(0);
        counts_.push_back(0);
        slots_[h] = uint32_t(keys_.size());
        if (keys_.size() * 2 > slots_.size()) grow();
        return keys_.size() - 1;
    }

    size_t size() const { return keys_.size(); }
    const std::string& key(size_t i) const { return keys_[i]; }
    int64_t& sum(size_t i) { return sums_[i]; }
    int64_t sum(size_t i) const { return sums_[i]; }
    int64_t& count(size_t i) { return counts_[i]; }
    int64_t count(size_t i) const { return counts_[i]; }

private:
    static size_t hashOf(std::string_view k) {
        uint64_t h = 1469598103934665603ULL;  // FNV-1a
        for (char c : k) h = (h ^ uint8_t(c)) * 1099511628211ULL;
        return size_t(h ^ (h >> 29));
    }

    void grow() {
        slots_.assign(slots_.size() * 2, 0);
        mask_ = slots_.size() - 1;
        for (size_t i = 0; i < keys_.size(); ++i) {
            size_t h = hashOf(keys_[i]) & mask_;
            while (slots_[h] != 0) h = (h + 1) & mask_;
            slots_[h] = uint32_t(i + 1);
        }
    }

    std::vector<std::string> keys_;
    std::vector<int64_t> sums_;
    std::vector<int64_t> counts_;
    std::vector<uint32_t> slots_;
    size_t mask_;
};

class Ledger {
public:
    void run(std::FILE* f);
    void print();

private:
    void processLines(const char* p, size_t n);
    void parseRates(const char* p);
    void parseTxn(const char* p);

    struct Rate {
        std::string name;
        int64_t value;
    };

    std::vector<Rate> rates_;
    bool haveRates_ = false;
    int64_t counted_ = 0;
    int64_t net_ = 0;
    KeyIndex channels_;
    KeyIndex accounts_;

    // Scratch storage, reused for every line.
    std::string keyBuf_, typeBuf_, accBuf_, curBuf_, amtBuf_, chanBuf_, tagBuf_;
};

void Ledger::run(std::FILE* f) {
    size_t cap = size_t(1) << 22;
    std::vector<char> buf(cap + 1);
    size_t carry = 0;
    for (;;) {
        if (carry == cap) {
            cap *= 2;
            buf.resize(cap + 1);
        }
        size_t got = std::fread(buf.data() + carry, 1, cap - carry, f);
        size_t end = carry + got;
        size_t stop = 0;
        if (got == 0) {
            stop = end;  // end of file: the last line may lack a newline
        } else {
            for (size_t i = end; i > 0; --i) {
                if (buf[i - 1] == '\n') {
                    stop = i;
                    break;
                }
            }
        }
        processLines(buf.data(), stop);
        carry = end - stop;
        std::memmove(buf.data(), buf.data() + stop, carry);
        if (got == 0) break;
    }
}

void Ledger::processLines(const char* p, size_t n) {
    const char* end = p + n;
    while (p < end) {
        const char* nl = static_cast<const char*>(std::memchr(p, '\n', size_t(end - p)));
        const char* lineEnd = nl ? nl : end;
        const char* q = p;
        while (q < lineEnd && (*q == ' ' || *q == '\t' || *q == '\r')) ++q;
        if (q < lineEnd) {
            if (haveRates_) {
                parseTxn(q);
            } else {
                parseRates(q);
                haveRates_ = true;
            }
        }
        p = lineEnd + 1;
    }
}

void Ledger::parseRates(const char* p) {
    forEachMember(
        p,
        [&](Str key, const char* q) -> const char* {
            if (!eq(key, "rates")) return skipValue(q);
            return forEachMember(
                q,
                [&](Str cur, const char* r) -> const char* {
                    bool neg = *r == '-';
                    if (neg) ++r;
                    int64_t v = 0;
                    while (*r >= '0' && *r <= '9') v = v * 10 + (*r++ - '0');
                    rates_.push_back({std::string(cur.view()), neg ? -v : v});
                    return r;
                },
                keyBuf_);
        },
        keyBuf_);
}

void Ledger::parseTxn(const char* p) {
    Str account, channel, currency, amount, type;
    bool test = false;
    forEachMember(
        p,
        [&](Str key, const char* q) -> const char* {
            if (eq(key, "account")) return readString(q, account, accBuf_);
            if (eq(key, "type")) return readString(q, type, typeBuf_);
            if (eq(key, "currency")) return readString(q, currency, curBuf_);
            if (eq(key, "amount")) {
                if (*q == '"') return readString(q, amount, amtBuf_);
                const char* e = skipValue(q);
                amount.p = q;
                amount.n = size_t(e - q);
                return e;
            }
            if (eq(key, "tags")) {
                return forEachElement(q, [&](const char* r) -> const char* {
                    if (*r != '"') return skipValue(r);
                    Str tag;
                    r = readString(r, tag, tagBuf_);
                    if (eq(tag, "test")) test = true;
                    return r;
                });
            }
            if (eq(key, "meta")) {
                return forEachMember(
                    q,
                    [&](Str mkey, const char* r) -> const char* {
                        if (eq(mkey, "channel") && *r == '"') return readString(r, channel, chanBuf_);
                        return skipValue(r);
                    },
                    keyBuf_);
            }
            return skipValue(q);
        },
        keyBuf_);

    if (eq(type, "void") || test) return;
    int64_t rate = 0;
    bool found = false;
    for (const Rate& r : rates_) {
        if (r.name == currency.view()) {
            rate = r.value;
            found = true;
            break;
        }
    }
    if (!found) return;

    int64_t usd = toHundredths(amount) * rate / 1000000;
    int64_t value = eq(type, "debit") ? -usd : usd;

    ++counted_;
    net_ += value;
    size_t c = channels_.find(channel.view());
    channels_.count(c) += 1;
    channels_.sum(c) += value;
    size_t a = accounts_.find(account.view());
    accounts_.sum(a) += value;
}

void Ledger::print() {
    std::string out;
    char num[32];
    auto put = [&](int64_t v) {
        auto r = std::to_chars(num, num + sizeof num, v);
        out.append(num, r.ptr);
    };

    out += "counted ";
    put(counted_);
    out += "\nnet ";
    put(net_);
    out += '\n';

    std::vector<size_t> chanOrder(channels_.size());
    for (size_t i = 0; i < chanOrder.size(); ++i) chanOrder[i] = i;
    std::sort(chanOrder.begin(), chanOrder.end(),
              [&](size_t a, size_t b) { return channels_.key(a) < channels_.key(b); });
    for (size_t i : chanOrder) {
        out += "channel ";
        out += channels_.key(i);
        out += ' ';
        put(channels_.count(i));
        out += ' ';
        put(channels_.sum(i));
        out += '\n';
    }

    std::vector<size_t> accOrder(accounts_.size());
    for (size_t i = 0; i < accOrder.size(); ++i) accOrder[i] = i;
    size_t top = std::min<size_t>(10, accOrder.size());
    std::partial_sort(accOrder.begin(), accOrder.begin() + top, accOrder.end(), [&](size_t a, size_t b) {
        if (accounts_.sum(a) != accounts_.sum(b)) return accounts_.sum(a) > accounts_.sum(b);
        return accounts_.key(a) < accounts_.key(b);
    });
    for (size_t k = 0; k < top; ++k) {
        size_t i = accOrder[k];
        out += "account ";
        out += accounts_.key(i);
        out += ' ';
        put(accounts_.sum(i));
        out += '\n';
    }

    std::fwrite(out.data(), 1, out.size(), stdout);
}

}  // namespace

int main(int argc, char** argv) {
    if (argc < 2) {
        std::fputs("usage: solution INPUT_PATH\n", stderr);
        return 2;
    }
    std::FILE* f = std::fopen(argv[1], "rb");
    if (!f) {
        std::fprintf(stderr, "cannot open %s\n", argv[1]);
        return 1;
    }
    _setmode(_fileno(stdout), _O_BINARY);  // keep "\n" as LF
    Ledger ledger;
    ledger.run(f);
    std::fclose(f);
    ledger.print();
    return 0;
}
