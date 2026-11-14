#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>
#include <string_view>
#include <unordered_map>
#include <vector>
#include <fcntl.h>
#include <io.h>

using i64 = int64_t;
using sv = std::string_view;

// Strings without escapes are views into the current input block.
struct Json {
    const char* p;
    explicit Json(sv s) : p(s.data()) {}
    void ws() { while (static_cast<unsigned char>(*p) <= 32) ++p; }
    void take() { ws(); ++p; }
    bool more(char end) { ws(); if (*p == ',') { ++p; ws(); } if (*p == end) { ++p; return false; } return true; }
    static unsigned hex(char c) { return c <= '9' ? c - '0' : (c | 32) - 'a' + 10; }
    unsigned hex4() { unsigned n = 0; for (int j = 0; j < 4; ++j) n = n * 16 + hex(*p++); return n; }
    static void utf8(std::string& s, unsigned c) {
        if (c < 0x80) s += char(c);
        else if (c < 0x800) { s += char(0xc0 | (c >> 6)); s += char(0x80 | (c & 63)); }
        else if (c < 0x10000) { s += char(0xe0 | (c >> 12)); s += char(0x80 | ((c >> 6) & 63)); s += char(0x80 | (c & 63)); }
        else { s += char(0xf0 | (c >> 18)); s += char(0x80 | ((c >> 12) & 63)); s += char(0x80 | ((c >> 6) & 63)); s += char(0x80 | (c & 63)); }
    }
    sv str(std::string& scratch) {
        ws(); const char* start = ++p;
        while (*p != '"' && *p != '\\') ++p;
        if (*p == '"') { sv s(start, p - start); ++p; return s; }
        scratch.assign(start, p - start);
        for (;;) {
            char c = *p++;
            if (c == '"') return scratch;
            if (c != '\\') { scratch += c; continue; }
            c = *p++;
            switch (c) {
                case 'b': scratch += '\b'; break;
                case 'f': scratch += '\f'; break;
                case 'n': scratch += '\n'; break;
                case 'r': scratch += '\r'; break;
                case 't': scratch += '\t'; break;
                case 'u': {
                    unsigned cp = hex4();
                    if (cp >= 0xd800 && cp <= 0xdbff && p[0] == '\\' && p[1] == 'u') {
                        const char* saved = p; p += 2; unsigned low = hex4();
                        if (low >= 0xdc00 && low <= 0xdfff) cp = 0x10000 + ((cp - 0xd800) << 10) + low - 0xdc00;
                        else p = saved;
                    }
                    utf8(scratch, cp); break;
                }
                default: scratch += c;
            }
        }
    }
    void skipString() { ++p; while (*p != '"') { if (*p == '\\') ++p; ++p; } ++p; }
    // No recursion or allocations for ignored objects and arrays.
    void skip() {
        ws();
        if (*p == '"') { skipString(); return; }
        if (*p == '{' || *p == '[') {
            size_t depth = 1; ++p;
            while (depth) {
                char c = *p;
                if (c == '"') { skipString(); continue; }
                ++p;
                if (c == '{' || c == '[') ++depth;
                else if (c == '}' || c == ']') --depth;
            }
        } else {
            while (*p != ',' && *p != '}' && *p != ']' && static_cast<unsigned char>(*p) > 32) ++p;
        }
    }
    i64 integer() {
        ws(); bool neg = *p == '-'; if (neg) ++p;
        const char* start = p;
        i64 digits = 0, fraction = 0; bool dot = false;
        while ((*p >= '0' && *p <= '9') || *p == '.') {
            if (*p == '.') dot = true;
            else { ++digits; if (dot) ++fraction; }
            ++p;
        }
        const char* end = p;
        i64 exponent = 0;
        if (*p == 'e' || *p == 'E') {
            ++p; bool eneg = *p == '-'; if (*p == '+' || *p == '-') ++p;
            constexpr i64 cap = i64(1) << 60;
            while (*p >= '0' && *p <= '9') {
                exponent = exponent > cap / 10 ? cap : std::min(cap, exponent * 10 + (*p - '0')); ++p;
            }
            if (eneg) exponent = -exponent;
        }
        i64 scale = exponent - fraction;
        i64 keep = digits + std::min<i64>(scale, 0);
        uint64_t n = 0;
        for (const char* q = start; q < end && keep > 0; ++q) if (*q != '.') {
            n = n * 10 + (*q - '0'); --keep;
        }
        if (scale >= 64) n = 0;
        else for (i64 i = 0; i < scale; ++i) n *= 10;
        return neg ? static_cast<i64>(0 - n) : static_cast<i64>(n);
    }
};

struct Hash {
    using is_transparent = void;
    size_t operator()(sv s) const noexcept { return std::hash<sv>{}(s); }
};
template<class V> using Map = std::unordered_map<std::string, V, Hash, std::equal_to<>>;
struct Total { i64 count = 0, net = 0; };
static i64 add(i64 a, i64 b) {
    return static_cast<i64>(static_cast<uint64_t>(a) + static_cast<uint64_t>(b));
}

struct Ledger {
    Map<i64> rates, accounts;
    Map<Total> channels;
    i64 count = 0, net = 0;
    std::string keyBuf, valueBuf, accountBuf, channelBuf, currencyBuf, amountBuf;

    void header(sv line) {
        Json j(line); j.take();
        while (j.more('}')) {
            sv key = j.str(keyBuf); j.take();
            if (key != "rates") { j.skip(); continue; }
            j.take();
            while (j.more('}')) {
                std::string name(j.str(valueBuf)); j.take();
                rates.emplace(std::move(name), j.integer());
            }
        }
    }
    static uint64_t hundredths(sv s) {
        uint64_t n = 0; size_t i = 0;
        while (i < s.size() && s[i] != '.') n = n * 10 + (s[i++] - '0');
        n *= 100;
        if (i < s.size()) { ++i; n += (s[i++] - '0') * 10; if (i < s.size()) n += s[i] - '0'; }
        return n;
    }
    void transaction(sv line) {
        Json j(line); j.take();
        sv account, channel, currency, amount;
        bool debit = false;
        while (j.more('}')) {
            sv key = j.str(keyBuf); j.take();
            if (key == "account") account = j.str(accountBuf);
            else if (key == "currency") currency = j.str(currencyBuf);
            else if (key == "amount") amount = j.str(amountBuf);
            else if (key == "type") {
                sv type = j.str(valueBuf);
                if (type == "void") return;
                debit = type == "debit";
            } else if (key == "tags") {
                j.take();
                while (j.more(']')) if (j.str(valueBuf) == "test") return;
            } else if (key == "meta") {
                j.take();
                while (j.more('}')) {
                    sv mk = j.str(keyBuf); j.take();
                    if (mk == "channel") channel = j.str(channelBuf);
                    else j.skip();
                }
            } else j.skip();
        }
        const i64 rate = rates.find(currency)->second;
        i64 product = static_cast<i64>(hundredths(amount) * static_cast<uint64_t>(rate));
        i64 value = product / 1000000;
        if (product < 0 && product % 1000000) --value;
        if (debit) value = -value;
        ++count; net = add(net, value);
        auto a = accounts.find(account);
        if (a == accounts.end()) accounts.emplace(std::string(account), value);
        else a->second = add(a->second, value);
        auto c = channels.find(channel);
        if (c == channels.end()) channels.emplace(std::string(channel), Total{1, value});
        else { ++c->second.count; c->second.net = add(c->second.net, value); }
    }
    void output() {
        std::string out = "counted " + std::to_string(count) + "\nnet " + std::to_string(net) + "\n";
        std::vector<const Map<Total>::value_type*> ordered;
        for (const auto& c : channels) ordered.push_back(&c);
        std::sort(ordered.begin(), ordered.end(), [](auto a, auto b) { return a->first < b->first; });
        for (auto c : ordered) out += "channel " + c->first + " " + std::to_string(c->second.count) + " " + std::to_string(c->second.net) + "\n";
        std::vector<const Map<i64>::value_type*> top;
        auto better = [](auto a, auto b) { return a->second != b->second ? a->second > b->second : a->first < b->first; };
        for (const auto& a : accounts) {
            auto pos = std::lower_bound(top.begin(), top.end(), &a, better);
            if (pos != top.end() || top.size() < 10) { top.insert(pos, &a); if (top.size() > 10) top.pop_back(); }
        }
        for (auto a : top) out += "account " + a->first + " " + std::to_string(a->second) + "\n";
        std::fwrite(out.data(), 1, out.size(), stdout);
    }
};

int wmain(int argc, wchar_t** argv) {
    if (argc < 2) return 1;
    _setmode(_fileno(stdout), _O_BINARY);
    FILE* f = nullptr;
    if (_wfopen_s(&f, argv[1], L"rb") || !f) return 1;
    Ledger ledger;
    std::vector<char> buffer(1 << 20);
    std::string pending;
    bool first = true;
    auto consume = [&](sv line) { if (first) { ledger.header(line); first = false; } else ledger.transaction(line); };
    size_t n;
    while ((n = std::fread(buffer.data(), 1, buffer.size(), f)) != 0) {
        const char* p = buffer.data(); const char* end = p + n;
        while (p < end) {
            const char* nl = static_cast<const char*>(std::memchr(p, '\n', end - p));
            if (!nl) { pending.append(p, end - p); break; }
            if (pending.empty()) consume(sv(p, nl - p));
            else { pending.append(p, nl - p); consume(pending); pending.clear(); }
            p = nl + 1;
        }
    }
    if (!pending.empty()) consume(pending);
    std::fclose(f); ledger.output();
}
