#include <algorithm>
#include <array>
#include <bit>
#include <charconv>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>
#include <string_view>
#include <vector>

class LineReader {
    FILE* file_;
    std::vector<char> buffer_;
    std::size_t position_ = 0;
    std::size_t available_ = 0;
    std::string spanning_;

public:
    explicit LineReader(FILE* file)
        : file_(file), buffer_(4 * 1024 * 1024) {}

    bool next(std::string_view& line) {
        spanning_.clear();

        for (;;) {
            if (position_ == available_) {
                available_ = std::fread(
                    buffer_.data(), 1, buffer_.size(), file_);
                position_ = 0;
                if (available_ == 0) {
                    if (spanning_.empty()) return false;
                    line = spanning_;
                    return true;
                }
            }

            const char* start = buffer_.data() + position_;
            const std::size_t remaining = available_ - position_;
            const char* newline = static_cast<const char*>(
                std::memchr(start, '\n', remaining));

            if (newline != nullptr) {
                const std::size_t length =
                    static_cast<std::size_t>(newline - start);
                position_ += length + 1;

                if (spanning_.empty()) {
                    line = std::string_view(start, length);
                } else {
                    spanning_.append(start, length);
                    line = spanning_;
                }
                return true;
            }

            spanning_.append(start, remaining);
            position_ = available_;
        }
    }
};

class JsonCursor {
    static unsigned hexDigit(unsigned char c) {
        if (c <= '9') return c - '0';
        if (c <= 'F') return c - 'A' + 10;
        return c - 'a' + 10;
    }

    std::uint32_t readHex4() {
        std::uint32_t value = 0;
        for (int i = 0; i < 4; ++i) {
            value = (value << 4) |
                hexDigit(static_cast<unsigned char>(*p++));
        }
        return value;
    }

    static void appendUtf8(std::string& out, std::uint32_t cp) {
        if (cp < 0x80) {
            out.push_back(static_cast<char>(cp));
        } else if (cp < 0x800) {
            out.push_back(static_cast<char>(0xC0 | (cp >> 6)));
            out.push_back(static_cast<char>(0x80 | (cp & 0x3F)));
        } else if (cp < 0x10000) {
            out.push_back(static_cast<char>(0xE0 | (cp >> 12)));
            out.push_back(static_cast<char>(0x80 | ((cp >> 6) & 0x3F)));
            out.push_back(static_cast<char>(0x80 | (cp & 0x3F)));
        } else {
            out.push_back(static_cast<char>(0xF0 | (cp >> 18)));
            out.push_back(static_cast<char>(0x80 | ((cp >> 12) & 0x3F)));
            out.push_back(static_cast<char>(0x80 | ((cp >> 6) & 0x3F)));
            out.push_back(static_cast<char>(0x80 | (cp & 0x3F)));
        }
    }

    void skipStringBody() {
        for (;;) {
            const char c = *p++;
            if (c == '"') return;
            if (c == '\\') ++p;
        }
    }

public:
    const char* p;
    const char* end;

    explicit JsonCursor(std::string_view line)
        : p(line.data()), end(line.data() + line.size()) {}

    void whitespace() {
        while (p != end && static_cast<unsigned char>(*p) <= 32) ++p;
    }

    std::string_view string(std::string& scratch) {
        const char* start = ++p;
        while (*p != '"' && *p != '\\') ++p;

        if (*p == '"') {
            const std::string_view result(
                start, static_cast<std::size_t>(p - start));
            ++p;
            return result;
        }

        scratch.assign(start, static_cast<std::size_t>(p - start));

        for (;;) {
            const char c = *p++;
            if (c == '"') return scratch;

            if (c != '\\') {
                scratch.push_back(c);
                continue;
            }

            switch (*p++) {
            case '"':  scratch.push_back('"');  break;
            case '\\': scratch.push_back('\\'); break;
            case '/':  scratch.push_back('/');  break;
            case 'b':  scratch.push_back('\b'); break;
            case 'f':  scratch.push_back('\f'); break;
            case 'n':  scratch.push_back('\n'); break;
            case 'r':  scratch.push_back('\r'); break;
            case 't':  scratch.push_back('\t'); break;
            case 'u': {
                std::uint32_t cp = readHex4();
                if (cp >= 0xD800 && cp <= 0xDBFF &&
                    p[0] == '\\' && p[1] == 'u') {
                    const char* saved = p;
                    p += 2;
                    const std::uint32_t low = readHex4();
                    if (low >= 0xDC00 && low <= 0xDFFF) {
                        cp = 0x10000 +
                            ((cp - 0xD800) << 10) + (low - 0xDC00);
                    } else {
                        p = saved;
                    }
                }
                appendUtf8(scratch, cp);
                break;
            }
            }
        }
    }

    void skipValue() {
        if (*p == '"') {
            ++p;
            skipStringBody();
            return;
        }

        if (*p == '{' || *p == '[') {
            ++p;
            std::size_t depth = 1;
            while (depth != 0) {
                const char c = *p++;
                if (c == '"') {
                    skipStringBody();
                } else if (c == '{' || c == '[') {
                    ++depth;
                } else if (c == '}' || c == ']') {
                    --depth;
                }
            }
            return;
        }

        while (p != end) {
            const unsigned char c = static_cast<unsigned char>(*p);
            if (c <= 32 || c == ',' || c == '}' || c == ']') return;
            ++p;
        }
    }
};

class StringTable {
public:
    struct Entry {
        std::string name;
        std::uint64_t hash;
        std::int64_t value;
        std::uint64_t count;
    };

private:
    std::vector<Entry> entries_;
    std::vector<std::size_t> buckets_;

    static std::uint64_t hashString(std::string_view key) {
        constexpr std::uint64_t p1 = 11400714785074694791ULL;
        constexpr std::uint64_t p2 = 14029467366897019727ULL;
        constexpr std::uint64_t p3 = 1609587929392839161ULL;
        constexpr std::uint64_t p4 = 9650029242287828579ULL;
        constexpr std::uint64_t p5 = 2870177450012600261ULL;

        const char* p = key.data();
        std::size_t length = key.size();
        std::uint64_t h = p5 + static_cast<std::uint64_t>(length);

        while (length >= 8) {
            std::uint64_t word;
            std::memcpy(&word, p, sizeof(word));
            word *= p2;
            word = std::rotl(word, 31);
            word *= p1;
            h ^= word;
            h = std::rotl(h, 27) * p1 + p4;
            p += 8;
            length -= 8;
        }

        if (length >= 4) {
            std::uint32_t word;
            std::memcpy(&word, p, sizeof(word));
            h ^= static_cast<std::uint64_t>(word) * p1;
            h = std::rotl(h, 23) * p2 + p3;
            p += 4;
            length -= 4;
        }

        while (length != 0) {
            h ^= static_cast<std::uint64_t>(
                static_cast<unsigned char>(*p++)) * p5;
            h = std::rotl(h, 11) * p1;
            --length;
        }

        h ^= h >> 33;
        h *= p2;
        h ^= h >> 29;
        h *= p3;
        h ^= h >> 32;
        return h;
    }

    static bool matches(const Entry& entry, std::string_view key,
                        std::uint64_t hash) {
        return entry.hash == hash &&
            entry.name.size() == key.size() &&
            (key.empty() ||
             std::memcmp(entry.name.data(), key.data(), key.size()) == 0);
    }

    void rehash(std::size_t capacity) {
        std::vector<std::size_t> replacement(capacity, 0);
        const std::size_t mask = capacity - 1;

        for (std::size_t i = 0; i < entries_.size(); ++i) {
            std::size_t slot =
                static_cast<std::size_t>(entries_[i].hash) & mask;
            while (replacement[slot] != 0) {
                slot = (slot + 1) & mask;
            }
            replacement[slot] = i + 1;
        }

        buckets_.swap(replacement);
    }

public:
    explicit StringTable(std::size_t capacity = 16)
        : buckets_(capacity, 0) {
        entries_.reserve(capacity / 2);
    }

    Entry& touch(std::string_view key) {
        const std::uint64_t hash = hashString(key);
        std::size_t mask = buckets_.size() - 1;
        std::size_t slot = static_cast<std::size_t>(hash) & mask;

        while (buckets_[slot] != 0) {
            Entry& entry = entries_[buckets_[slot] - 1];
            if (matches(entry, key, hash)) return entry;
            slot = (slot + 1) & mask;
        }

        if ((entries_.size() + 1) * 10 >= buckets_.size() * 7) {
            rehash(buckets_.size() * 2);
            mask = buckets_.size() - 1;
            slot = static_cast<std::size_t>(hash) & mask;
            while (buckets_[slot] != 0) {
                slot = (slot + 1) & mask;
            }
        }

        entries_.push_back({std::string(key), hash, 0, 0});
        buckets_[slot] = entries_.size();
        return entries_.back();
    }

    const Entry* find(std::string_view key) const {
        const std::uint64_t hash = hashString(key);
        const std::size_t mask = buckets_.size() - 1;
        std::size_t slot = static_cast<std::size_t>(hash) & mask;

        while (buckets_[slot] != 0) {
            const Entry& entry = entries_[buckets_[slot] - 1];
            if (matches(entry, key, hash)) return &entry;
            slot = (slot + 1) & mask;
        }
        return nullptr;
    }

    const std::vector<Entry>& entries() const {
        return entries_;
    }
};

struct Scratch {
    std::string key;
    std::string account;
    std::string amount;
    std::string currency;
    std::string channel;
    std::string temporary;
};

struct Transaction {
    std::string_view account;
    std::string_view amount;
    std::string_view currency;
    std::string_view channel;
    bool debit = false;
    bool voided = false;
    bool test = false;
};

static bool readTags(JsonCursor& json, Scratch& scratch) {
    ++json.p;
    json.whitespace();

    bool test = false;
    if (*json.p == ']') {
        ++json.p;
        return false;
    }

    for (;;) {
        if (json.string(scratch.temporary) == "test") test = true;
        json.whitespace();
        if (*json.p == ']') {
            ++json.p;
            return test;
        }
        ++json.p;
        json.whitespace();
    }
}

static std::string_view readMeta(JsonCursor& json, Scratch& scratch) {
    ++json.p;
    json.whitespace();
    std::string_view channel;

    if (*json.p == '}') {
        ++json.p;
        return channel;
    }

    for (;;) {
        const std::string_view key = json.string(scratch.key);
        json.whitespace();
        ++json.p;
        json.whitespace();

        if (key == "channel") {
            channel = json.string(scratch.channel);
        } else {
            json.skipValue();
        }

        json.whitespace();
        if (*json.p == '}') {
            ++json.p;
            return channel;
        }
        ++json.p;
        json.whitespace();
    }
}

static Transaction readTransaction(std::string_view line, Scratch& scratch) {
    JsonCursor json(line);
    Transaction transaction;

    json.whitespace();
    ++json.p;
    json.whitespace();

    if (*json.p == '}') return transaction;

    for (;;) {
        const std::string_view key = json.string(scratch.key);
        json.whitespace();
        ++json.p;
        json.whitespace();

        switch (key.size()) {
        case 4:
            if (key == "type") {
                const std::string_view type = json.string(scratch.temporary);
                transaction.debit = type == "debit";
                transaction.voided = type == "void";
            } else if (key == "tags") {
                transaction.test = readTags(json, scratch);
            } else if (key == "meta") {
                transaction.channel = readMeta(json, scratch);
            } else {
                json.skipValue();
            }
            break;

        case 6:
            if (key == "amount") {
                transaction.amount = json.string(scratch.amount);
            } else {
                json.skipValue();
            }
            break;

        case 7:
            if (key == "account") {
                transaction.account = json.string(scratch.account);
            } else {
                json.skipValue();
            }
            break;

        case 8:
            if (key == "currency") {
                transaction.currency = json.string(scratch.currency);
            } else {
                json.skipValue();
            }
            break;

        default:
            json.skipValue();
            break;
        }

        json.whitespace();
        if (*json.p == '}') return transaction;
        ++json.p;
        json.whitespace();
    }
}

static void readRateObject(JsonCursor& json, Scratch& scratch,
                           StringTable& rates) {
    ++json.p;
    json.whitespace();

    if (*json.p == '}') {
        ++json.p;
        return;
    }

    for (;;) {
        const std::string_view currency = json.string(scratch.currency);
        json.whitespace();
        ++json.p;
        json.whitespace();

        std::int64_t rate = 0;
        const auto result = std::from_chars(json.p, json.end, rate);
        json.p = result.ptr;
        rates.touch(currency).value = rate;

        json.whitespace();
        if (*json.p == '}') {
            ++json.p;
            return;
        }
        ++json.p;
        json.whitespace();
    }
}

static void readRates(std::string_view line, Scratch& scratch,
                      StringTable& rates) {
    JsonCursor json(line);
    json.whitespace();
    ++json.p;
    json.whitespace();

    if (*json.p == '}') return;

    for (;;) {
        const std::string_view key = json.string(scratch.key);
        json.whitespace();
        ++json.p;
        json.whitespace();

        if (key == "rates") {
            readRateObject(json, scratch, rates);
        } else {
            json.skipValue();
        }

        json.whitespace();
        if (*json.p == '}') return;
        ++json.p;
        json.whitespace();
    }
}

static std::uint64_t hundredths(std::string_view amount) {
    std::uint64_t whole = 0;
    std::size_t i = 0;

    while (i < amount.size() && amount[i] != '.') {
        whole = whole * 10 +
            static_cast<unsigned>(amount[i] - '0');
        ++i;
    }

    std::uint64_t fraction = 0;
    if (i < amount.size()) {
        ++i;
        fraction = static_cast<unsigned>(amount[i++] - '0') * 10;
        if (i < amount.size()) {
            fraction += static_cast<unsigned>(amount[i] - '0');
        }
    }

    return whole * 100 + fraction;
}

static std::int64_t convert(std::string_view amount, std::int64_t rate) {
    if (rate == 0) return 0;

    const std::uint64_t cents = hundredths(amount);

    if (rate > 0) {
        const std::uint64_t product =
            cents * static_cast<std::uint64_t>(rate);
        return static_cast<std::int64_t>(product / 1000000);
    }

    const std::uint64_t magnitude =
        std::uint64_t(0) - static_cast<std::uint64_t>(rate);
    const std::uint64_t product = cents * magnitude;
    return -static_cast<std::int64_t>(
        product / 1000000 + (product % 1000000 != 0));
}

class Output {
    std::array<char, 65536> buffer_;
    std::size_t used_ = 0;

public:
    void flush() {
        if (used_ != 0) {
            std::fwrite(buffer_.data(), 1, used_, stdout);
            used_ = 0;
        }
    }

    void append(std::string_view text) {
        if (text.size() > buffer_.size() - used_) flush();

        if (text.size() > buffer_.size()) {
            std::fwrite(text.data(), 1, text.size(), stdout);
        } else if (!text.empty()) {
            std::memcpy(buffer_.data() + used_, text.data(), text.size());
            used_ += text.size();
        }
    }

    template<class Integer>
    void number(Integer value) {
        char digits[32];
        const auto result = std::to_chars(digits, digits + sizeof(digits), value);
        append(std::string_view(
            digits, static_cast<std::size_t>(result.ptr - digits)));
    }
};

int main(int argc, char* argv[]) {
    if (argc < 2) return 0;

    FILE* file = std::fopen(argv[1], "rb");
    if (file == nullptr) return 0;

    LineReader reader(file);
    StringTable rates;
    StringTable channels;
    StringTable accounts(8192);
    Scratch scratch;
    std::string_view line;

    if (!reader.next(line)) {
        std::fclose(file);
        return 0;
    }
    readRates(line, scratch, rates);

    std::uint64_t counted = 0;
    std::int64_t net = 0;

    while (reader.next(line)) {
        const Transaction transaction = readTransaction(line, scratch);
        if (transaction.voided || transaction.test) continue;

        const std::int64_t rate = rates.find(transaction.currency)->value;
        std::int64_t value = convert(transaction.amount, rate);
        if (transaction.debit) value = -value;

        ++counted;
        net += value;

        auto& account = accounts.touch(transaction.account);
        account.value += value;

        auto& channel = channels.touch(transaction.channel);
        ++channel.count;
        channel.value += value;
    }

    std::fclose(file);

    using Entry = StringTable::Entry;

    std::vector<const Entry*> sortedChannels;
    sortedChannels.reserve(channels.entries().size());
    for (const auto& entry : channels.entries()) {
        sortedChannels.push_back(&entry);
    }
    std::sort(sortedChannels.begin(), sortedChannels.end(),
        [](const Entry* a, const Entry* b) {
            return a->name < b->name;
        });

    const auto better = [](const Entry* a, const Entry* b) {
        if (a->value != b->value) return a->value > b->value;
        return a->name < b->name;
    };

    std::array<const Entry*, 10> top{};
    std::size_t topCount = 0;

    for (const auto& entry : accounts.entries()) {
        const Entry* candidate = &entry;
        if (topCount == top.size() && !better(candidate, top.back())) {
            continue;
        }

        std::size_t position;
        if (topCount < top.size()) {
            position = topCount++;
        } else {
            position = top.size() - 1;
        }

        while (position != 0 && better(candidate, top[position - 1])) {
            top[position] = top[position - 1];
            --position;
        }
        top[position] = candidate;
    }

    Output output;
    output.append("counted ");
    output.number(counted);
    output.append("\nnet ");
    output.number(net);
    output.append("\n");

    for (const Entry* channel : sortedChannels) {
        output.append("channel ");
        output.append(channel->name);
        output.append(" ");
        output.number(channel->count);
        output.append(" ");
        output.number(channel->value);
        output.append("\n");
    }

    for (std::size_t i = 0; i < topCount; ++i) {
        output.append("account ");
        output.append(top[i]->name);
        output.append(" ");
        output.number(top[i]->value);
        output.append("\n");
    }

    output.flush();
    return 0;
}
