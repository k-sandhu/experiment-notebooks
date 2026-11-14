#include <algorithm>
#include <bit>
#include <charconv>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

using u64 = std::uint64_t;
using i64 = std::int64_t;
using sv = std::string_view;

class LineReader {
    std::FILE* file_;
    std::vector<char> buffer_;
    std::size_t position_ = 0;
    std::size_t used_ = 0;
    bool eof_ = false;

public:
    explicit LineReader(std::FILE* file)
        : file_(file), buffer_(1u << 20) {}

    bool next(sv& line) {
        for (;;) {
            if (position_ < used_) {
                const char* begin = buffer_.data() + position_;
                const void* found = std::memchr(begin, '\n', used_ - position_);
                if (found) {
                    const char* end = static_cast<const char*>(found);
                    line = sv(begin, static_cast<std::size_t>(end - begin));
                    position_ = static_cast<std::size_t>(end - buffer_.data()) + 1;
                    return true;
                }
            }

            if (eof_) {
                if (position_ == used_) return false;
                line = sv(buffer_.data() + position_, used_ - position_);
                position_ = used_;
                return true;
            }

            const std::size_t remaining = used_ - position_;
            if (remaining && position_)
                std::memmove(buffer_.data(), buffer_.data() + position_, remaining);

            position_ = 0;
            used_ = remaining;
            if (used_ == buffer_.size())
                buffer_.resize(buffer_.size() * 2);

            const std::size_t n = std::fread(
                buffer_.data() + used_, 1, buffer_.size() - used_, file_);
            used_ += n;
            if (!n) eof_ = true;
        }
    }
};

static u64 hashString(sv s) noexcept {
    constexpr u64 multiplier = 0x9E3779B185EBCA87ULL;
    u64 h = 0xA0761D6478BD642FULL ^ static_cast<u64>(s.size());
    const char* p = s.data();
    std::size_t n = s.size();

    while (n >= 8) {
        u64 word;
        std::memcpy(&word, p, 8);
        h ^= word;
        h *= multiplier;
        h ^= h >> 29;
        p += 8;
        n -= 8;
    }

    u64 tail = 0;
    if (n) std::memcpy(&tail, p, n);
    h ^= tail;
    h *= multiplier;
    h ^= h >> 32;
    h *= 0xD6E8FEB86659FD93ULL;
    return h ^ (h >> 32);
}

template<class V>
class StringTable {
    std::vector<std::size_t> buckets_;

    void grow() {
        buckets_.assign(buckets_.size() * 2, 0);
        const std::size_t mask = buckets_.size() - 1;
        for (std::size_t i = 0; i < items.size(); ++i) {
            std::size_t slot = static_cast<std::size_t>(items[i].hash) & mask;
            while (buckets_[slot]) slot = (slot + 1) & mask;
            buckets_[slot] = i + 1;
        }
    }

public:
    struct Entry {
        std::string key;
        u64 hash;
        V value;
    };

    std::vector<Entry> items;

    explicit StringTable(std::size_t initial = 16) {
        std::size_t capacity = 16;
        while (capacity < initial) capacity *= 2;
        buckets_.assign(capacity, 0);
        items.reserve(capacity / 2);
    }

    const V* find(sv key) const noexcept {
        const u64 h = hashString(key);
        const std::size_t mask = buckets_.size() - 1;
        std::size_t slot = static_cast<std::size_t>(h) & mask;

        while (const std::size_t index = buckets_[slot]) {
            const Entry& entry = items[index - 1];
            if (entry.hash == h && sv(entry.key) == key)
                return &entry.value;
            slot = (slot + 1) & mask;
        }
        return nullptr;
    }

    V& getOrInsert(sv key) {
        const u64 h = hashString(key);
        std::size_t mask = buckets_.size() - 1;
        std::size_t slot = static_cast<std::size_t>(h) & mask;

        while (const std::size_t index = buckets_[slot]) {
            Entry& entry = items[index - 1];
            if (entry.hash == h && sv(entry.key) == key)
                return entry.value;
            slot = (slot + 1) & mask;
        }

        if ((items.size() + 1) * 10 > buckets_.size() * 7) {
            grow();
            mask = buckets_.size() - 1;
            slot = static_cast<std::size_t>(h) & mask;
            while (buckets_[slot]) slot = (slot + 1) & mask;
        }

        items.push_back(Entry{std::string(key), h, V{}});
        buckets_[slot] = items.size();
        return items.back().value;
    }
};

struct Transaction {
    sv account;
    sv currency;
    sv channel;
    u64 hundredths = 0;
    bool debit = false;
};

class Parser {
    const char* p_ = nullptr;
    std::string keyScratch_;
    std::string valueScratch_;
    std::string accountScratch_;
    std::string currencyScratch_;
    std::string channelScratch_;

    void whitespace() noexcept {
        while (static_cast<unsigned char>(*p_) <= 0x20) ++p_;
    }

    static unsigned hexDigit(unsigned char c) noexcept {
        if (c <= '9') return c - '0';
        return (c | 32u) - 'a' + 10u;
    }

    unsigned hex4() noexcept {
        unsigned result = 0;
        for (unsigned i = 0; i < 4; ++i)
            result = (result << 4) | hexDigit(static_cast<unsigned char>(*p_++));
        return result;
    }

    static void appendUtf8(std::string& out, unsigned cp) {
        if (cp < 0x80) {
            out.push_back(static_cast<char>(cp));
        } else if (cp < 0x800) {
            out.push_back(static_cast<char>(0xC0 | (cp >> 6)));
            out.push_back(static_cast<char>(0x80 | (cp & 63)));
        } else if (cp < 0x10000) {
            out.push_back(static_cast<char>(0xE0 | (cp >> 12)));
            out.push_back(static_cast<char>(0x80 | ((cp >> 6) & 63)));
            out.push_back(static_cast<char>(0x80 | (cp & 63)));
        } else {
            out.push_back(static_cast<char>(0xF0 | (cp >> 18)));
            out.push_back(static_cast<char>(0x80 | ((cp >> 12) & 63)));
            out.push_back(static_cast<char>(0x80 | ((cp >> 6) & 63)));
            out.push_back(static_cast<char>(0x80 | (cp & 63)));
        }
    }

    sv string(std::string& scratch) {
        const char* start = ++p_;
        while (*p_ != '"' && *p_ != '\\') ++p_;

        if (*p_ == '"') {
            const sv result(start, static_cast<std::size_t>(p_ - start));
            ++p_;
            return result;
        }

        scratch.assign(start, static_cast<std::size_t>(p_ - start));
        for (;;) {
            ++p_;
            const char escape = *p_++;
            switch (escape) {
            case 'b': scratch.push_back('\b'); break;
            case 'f': scratch.push_back('\f'); break;
            case 'n': scratch.push_back('\n'); break;
            case 'r': scratch.push_back('\r'); break;
            case 't': scratch.push_back('\t'); break;
            case 'u': {
                unsigned cp = hex4();
                if (cp >= 0xD800 && cp <= 0xDBFF &&
                    p_[0] == '\\' && p_[1] == 'u') {
                    const char* saved = p_;
                    p_ += 2;
                    const unsigned low = hex4();
                    if (low >= 0xDC00 && low <= 0xDFFF)
                        cp = 0x10000 + ((cp - 0xD800) << 10) + (low - 0xDC00);
                    else
                        p_ = saved;
                }
                appendUtf8(scratch, cp);
                break;
            }
            default:
                scratch.push_back(escape);
                break;
            }

            start = p_;
            while (*p_ != '"' && *p_ != '\\') ++p_;
            scratch.append(start, static_cast<std::size_t>(p_ - start));
            if (*p_ == '"') {
                ++p_;
                return sv(scratch);
            }
        }
    }

    void skipString() noexcept {
        ++p_;
        for (;;) {
            const char c = *p_++;
            if (c == '"') return;
            if (c == '\\') ++p_;
        }
    }

    void skipValue() noexcept {
        if (*p_ == '"') {
            skipString();
            return;
        }

        if (*p_ == '{' || *p_ == '[') {
            std::size_t depth = 1;
            ++p_;
            while (depth) {
                if (*p_ == '"') {
                    skipString();
                } else {
                    const char c = *p_++;
                    if (c == '{' || c == '[') ++depth;
                    else if (c == '}' || c == ']') --depth;
                }
            }
            return;
        }

        while (static_cast<unsigned char>(*p_) > 0x20 &&
               *p_ != ',' && *p_ != '}' && *p_ != ']')
            ++p_;
    }

    u64 integer() noexcept {
        const bool negative = *p_ == '-';
        if (negative) ++p_;
        u64 result = 0;
        while (*p_ >= '0' && *p_ <= '9')
            result = result * 10 + static_cast<unsigned>(*p_++ - '0');
        return negative ? u64(0) - result : result;
    }

    static u64 amount(sv value) noexcept {
        u64 whole = 0;
        std::size_t i = 0;
        while (i < value.size() && value[i] != '.')
            whole = whole * 10 + static_cast<unsigned>(value[i++] - '0');

        u64 result = whole * 100;
        if (i < value.size()) {
            ++i;
            result += static_cast<unsigned>(value[i++] - '0') * 10;
            if (i < value.size())
                result += static_cast<unsigned>(value[i] - '0');
        }
        return result;
    }

    bool testTags() {
        ++p_;
        whitespace();
        if (*p_ == ']') {
            ++p_;
            return false;
        }

        for (;;) {
            if (string(valueScratch_) == "test") return true;
            whitespace();
            if (*p_ == ']') {
                ++p_;
                return false;
            }
            ++p_;
            whitespace();
        }
    }

    void meta(Transaction& transaction) {
        ++p_;
        for (;;) {
            whitespace();
            if (*p_ == '}') {
                ++p_;
                return;
            }

            const bool channel = string(keyScratch_) == "channel";
            whitespace();
            ++p_;
            whitespace();

            if (channel)
                transaction.channel = string(channelScratch_);
            else
                skipValue();

            whitespace();
            if (*p_ == '}') {
                ++p_;
                return;
            }
            ++p_;
        }
    }

    void rateObject(StringTable<u64>& rates) {
        ++p_;
        for (;;) {
            whitespace();
            if (*p_ == '}') {
                ++p_;
                return;
            }

            const sv key = string(keyScratch_);
            whitespace();
            ++p_;
            whitespace();
            const u64 rate = integer();
            rates.getOrInsert(key) = rate;

            whitespace();
            if (*p_ == '}') {
                ++p_;
                return;
            }
            ++p_;
        }
    }

public:
    void header(sv line, StringTable<u64>& rates) {
        p_ = line.data();
        whitespace();
        ++p_;

        for (;;) {
            whitespace();
            if (*p_ == '}') return;

            const bool isRates = string(keyScratch_) == "rates";
            whitespace();
            ++p_;
            whitespace();
            if (isRates)
                rateObject(rates);
            else
                skipValue();

            whitespace();
            if (*p_ == '}') return;
            ++p_;
        }
    }

    bool transaction(sv line, Transaction& result) {
        p_ = line.data();
        result = Transaction{};
        whitespace();
        ++p_;

        for (;;) {
            whitespace();
            if (*p_ == '}') return true;

            const sv key = string(keyScratch_);
            unsigned field = 0;
            switch (key.size()) {
            case 4:
                if (key == "type") field = 1;
                else if (key == "tags") field = 2;
                else if (key == "meta") field = 3;
                break;
            case 6:
                if (key == "amount") field = 4;
                break;
            case 7:
                if (key == "account") field = 5;
                break;
            case 8:
                if (key == "currency") field = 6;
                break;
            default:
                break;
            }

            whitespace();
            ++p_;
            whitespace();

            switch (field) {
            case 1: {
                const sv type = string(valueScratch_);
                if (type == "void") return false;
                result.debit = type == "debit";
                break;
            }
            case 2:
                if (testTags()) return false;
                break;
            case 3:
                meta(result);
                break;
            case 4:
                result.hundredths = amount(string(valueScratch_));
                break;
            case 5:
                result.account = string(accountScratch_);
                break;
            case 6:
                result.currency = string(currencyScratch_);
                break;
            default:
                skipValue();
                break;
            }

            whitespace();
            if (*p_ == '}') return true;
            ++p_;
        }
    }
};

class Writer {
    char buffer_[65536];
    std::size_t used_ = 0;

public:
    ~Writer() { flush(); }

    void flush() {
        if (used_) {
            std::fwrite(buffer_, 1, used_, stdout);
            used_ = 0;
        }
    }

    void text(sv value) {
        if (value.size() > sizeof(buffer_) - used_) flush();
        if (value.size() >= sizeof(buffer_)) {
            std::fwrite(value.data(), 1, value.size(), stdout);
        } else if (!value.empty()) {
            std::memcpy(buffer_ + used_, value.data(), value.size());
            used_ += value.size();
        }
    }

    void character(char c) {
        if (used_ == sizeof(buffer_)) flush();
        buffer_[used_++] = c;
    }

    template<class T>
    void number(T value) {
        char digits[32];
        const auto result = std::to_chars(digits, digits + sizeof(digits), value);
        text(sv(digits, static_cast<std::size_t>(result.ptr - digits)));
    }
};

struct ChannelTotals {
    u64 count = 0;
    u64 net = 0;
};

static i64 signedValue(u64 value) noexcept {
    return std::bit_cast<i64>(value);
}

int main(int argc, char** argv) {
    if (argc != 2) return 1;

    std::FILE* file = nullptr;
#ifdef _MSC_VER
    if (fopen_s(&file, argv[1], "rb") != 0) return 1;
#else
    file = std::fopen(argv[1], "rb");
    if (!file) return 1;
#endif

    LineReader reader(file);
    Parser parser;
    StringTable<u64> rates;
    StringTable<u64> accounts(1024);
    StringTable<ChannelTotals> channels;

    sv line;
    if (!reader.next(line)) {
        std::fclose(file);
        return 1;
    }
    parser.header(line, rates);

    u64 counted = 0;
    u64 total = 0;
    Transaction transaction;

    while (reader.next(line)) {
        if (!parser.transaction(line, transaction)) continue;

        const u64 rate = *rates.find(transaction.currency);
        const i64 product = signedValue(transaction.hundredths * rate);
        i64 usd = product / 1000000;
        if (product % 1000000 < 0) --usd;

        u64 value = static_cast<u64>(usd);
        if (transaction.debit) value = u64(0) - value;

        ++counted;
        total += value;
        accounts.getOrInsert(transaction.account) += value;

        ChannelTotals& channel = channels.getOrInsert(transaction.channel);
        ++channel.count;
        channel.net += value;
    }

    std::fclose(file);

    using ChannelEntry = StringTable<ChannelTotals>::Entry;
    std::vector<const ChannelEntry*> sortedChannels;
    sortedChannels.reserve(channels.items.size());
    for (const auto& entry : channels.items)
        sortedChannels.push_back(&entry);
    std::sort(sortedChannels.begin(), sortedChannels.end(),
        [](const ChannelEntry* a, const ChannelEntry* b) {
            return a->key < b->key;
        });

    using AccountEntry = StringTable<u64>::Entry;
    const auto better = [](const AccountEntry* a, const AccountEntry* b) {
        const i64 av = signedValue(a->value);
        const i64 bv = signedValue(b->value);
        return av != bv ? av > bv : a->key < b->key;
    };

    std::vector<const AccountEntry*> top;
    top.reserve(11);
    for (const auto& entry : accounts.items) {
        const AccountEntry* candidate = &entry;
        if (top.size() == 10 && !better(candidate, top.back())) continue;
        const auto position = std::lower_bound(
            top.begin(), top.end(), candidate, better);
        top.insert(position, candidate);
        if (top.size() > 10) top.pop_back();
    }

    Writer output;
    output.text("counted ");
    output.number(counted);
    output.text("\nnet ");
    output.number(signedValue(total));
    output.character('\n');

    for (const ChannelEntry* entry : sortedChannels) {
        output.text("channel ");
        output.text(entry->key);
        output.character(' ');
        output.number(entry->value.count);
        output.character(' ');
        output.number(signedValue(entry->value.net));
        output.character('\n');
    }

    for (const AccountEntry* entry : top) {
        output.text("account ");
        output.text(entry->key);
        output.character(' ');
        output.number(signedValue(entry->value));
        output.character('\n');
    }

    return 0;
}
