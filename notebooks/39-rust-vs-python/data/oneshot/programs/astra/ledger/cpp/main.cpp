#define _CRT_SECURE_NO_WARNINGS

#include <algorithm>
#include <bit>
#include <charconv>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <functional>
#include <string>
#include <string_view>
#include <unordered_map>
#include <utility>
#include <vector>

using U64 = std::uint64_t;
using I64 = std::int64_t;

struct StringHash {
    using is_transparent = void;

    std::size_t operator()(std::string_view s) const noexcept {
        return std::hash<std::string_view>{}(s);
    }
};

struct StringEqual {
    using is_transparent = void;

    bool operator()(std::string_view a, std::string_view b) const noexcept {
        return a == b;
    }
};

template<class T>
using StringMap = std::unordered_map<std::string, T, StringHash, StringEqual>;

class LineReader {
    std::FILE* file_;
    std::vector<char> buffer_;
    std::size_t position_ = 0;
    std::size_t available_ = 0;
    std::string spanning_;

public:
    explicit LineReader(std::FILE* file)
        : file_(file), buffer_(1u << 20) {}

    bool next(std::string_view& line) {
        spanning_.clear();

        for (;;) {
            if (position_ == available_) {
                available_ = std::fread(
                    buffer_.data(), 1, buffer_.size(), file_);
                position_ = 0;

                if (available_ == 0) {
                    if (spanning_.empty())
                        return false;
                    line = spanning_;
                    return true;
                }
            }

            const char* begin = buffer_.data() + position_;
            const std::size_t remaining = available_ - position_;
            const char* newline = static_cast<const char*>(
                std::memchr(begin, '\n', remaining));

            if (newline != nullptr) {
                const std::size_t length =
                    static_cast<std::size_t>(newline - begin);
                position_ += length + 1;

                if (spanning_.empty()) {
                    line = std::string_view(begin, length);
                } else {
                    spanning_.append(begin, length);
                    line = spanning_;
                }
                return true;
            }

            spanning_.append(begin, remaining);
            position_ = available_;
        }
    }
};

struct Rate {
    U64 magnitude = 0;
    bool negative = false;
};

class JsonCursor {
    const char* p_;
    const char* end_;

    std::uint32_t hex4() noexcept {
        std::uint32_t value = 0;
        for (int i = 0; i < 4; ++i) {
            const unsigned char c = static_cast<unsigned char>(*p_++);
            const unsigned digit =
                c <= '9' ? c - '0' :
                c <= 'F' ? c - 'A' + 10 :
                           c - 'a' + 10;
            value = (value << 4) | digit;
        }
        return value;
    }

    static void append_utf8(std::string& out, std::uint32_t cp) {
        if (cp <= 0x7F) {
            out.push_back(static_cast<char>(cp));
        } else if (cp <= 0x7FF) {
            out.push_back(static_cast<char>(0xC0 | (cp >> 6)));
            out.push_back(static_cast<char>(0x80 | (cp & 0x3F)));
        } else if (cp <= 0xFFFF) {
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

    void skip_string() noexcept {
        ++p_;
        for (;;) {
            const char* quote = static_cast<const char*>(
                std::memchr(p_, '"', static_cast<std::size_t>(end_ - p_)));
            const char* back = quote;
            while (back > p_ && back[-1] == '\\')
                --back;

            const bool escaped =
                (static_cast<std::size_t>(quote - back) & 1u) != 0;
            p_ = quote + 1;
            if (!escaped)
                return;
        }
    }

public:
    explicit JsonCursor(std::string_view line)
        : p_(line.data()), end_(line.data() + line.size()) {}

    void whitespace() noexcept {
        while (p_ != end_ && static_cast<unsigned char>(*p_) <= 0x20)
            ++p_;
    }

    char take() noexcept {
        whitespace();
        return *p_++;
    }

    bool consume(char c) noexcept {
        whitespace();
        if (p_ != end_ && *p_ == c) {
            ++p_;
            return true;
        }
        return false;
    }

    std::string_view string(std::string& decoded) {
        whitespace();
        const char* start = ++p_;
        const char* quote = static_cast<const char*>(
            std::memchr(start, '"', static_cast<std::size_t>(end_ - start)));
        const char* slash = static_cast<const char*>(
            std::memchr(start, '\\', static_cast<std::size_t>(quote - start)));

        if (slash == nullptr) {
            p_ = quote + 1;
            return std::string_view(
                start, static_cast<std::size_t>(quote - start));
        }

        decoded.assign(start, static_cast<std::size_t>(slash - start));
        p_ = slash;

        for (;;) {
            char c = *p_++;
            if (c == '"')
                return std::string_view(decoded);

            if (c != '\\') {
                decoded.push_back(c);
                continue;
            }

            c = *p_++;
            switch (c) {
            case '"':
            case '\\':
            case '/':
                decoded.push_back(c);
                break;
            case 'b':
                decoded.push_back('\b');
                break;
            case 'f':
                decoded.push_back('\f');
                break;
            case 'n':
                decoded.push_back('\n');
                break;
            case 'r':
                decoded.push_back('\r');
                break;
            case 't':
                decoded.push_back('\t');
                break;
            case 'u': {
                std::uint32_t cp = hex4();
                if (cp >= 0xD800 && cp <= 0xDBFF) {
                    p_ += 2;
                    const std::uint32_t low = hex4();
                    cp = 0x10000 + ((cp - 0xD800) << 10)
                         + (low - 0xDC00);
                }
                append_utf8(decoded, cp);
                break;
            }
            }
        }
    }

    Rate integer() noexcept {
        whitespace();
        Rate result;
        if (*p_ == '-') {
            result.negative = true;
            ++p_;
        }

        while (p_ != end_) {
            const unsigned digit =
                static_cast<unsigned char>(*p_) - static_cast<unsigned>('0');
            if (digit > 9)
                break;
            result.magnitude = result.magnitude * 10 + digit;
            ++p_;
        }
        return result;
    }

    void skip_value() noexcept {
        whitespace();

        if (*p_ == '"') {
            skip_string();
            return;
        }

        if (*p_ == '{' || *p_ == '[') {
            std::size_t depth = 1;
            ++p_;

            while (depth != 0) {
                const char c = *p_;
                if (c == '"') {
                    skip_string();
                } else {
                    ++p_;
                    if (c == '{' || c == '[')
                        ++depth;
                    else if (c == '}' || c == ']')
                        --depth;
                }
            }
            return;
        }

        while (p_ != end_) {
            const unsigned char c = static_cast<unsigned char>(*p_);
            if (c <= 0x20 || c == ',' || c == '}' || c == ']')
                break;
            ++p_;
        }
    }
};

static void read_rates(std::string_view line, StringMap<Rate>& rates) {
    JsonCursor json(line);
    std::string key_storage;
    std::string currency_storage;

    json.take();
    if (json.consume('}'))
        return;

    do {
        const auto key = json.string(key_storage);
        json.take();

        if (key == "rates") {
            rates.clear();
            json.take();
            if (!json.consume('}')) {
                do {
                    const auto currency = json.string(currency_storage);
                    json.take();
                    const Rate rate = json.integer();
                    rates.insert_or_assign(std::string(currency), rate);
                } while (json.take() == ',');
            }
        } else {
            json.skip_value();
        }
    } while (json.take() == ',');
}

struct Transaction {
    std::string_view account;
    std::string_view amount;
    std::string_view currency;
    std::string_view channel;
    bool debit = false;
};

class TransactionParser {
    std::string key_storage_;
    std::string temporary_storage_;
    std::string account_storage_;
    std::string amount_storage_;
    std::string currency_storage_;
    std::string channel_storage_;

    bool read_tags(JsonCursor& json) {
        bool test = false;
        json.take();

        if (!json.consume(']')) {
            do {
                if (json.string(temporary_storage_) == "test")
                    test = true;
            } while (json.take() == ',');
        }
        return test;
    }

    void read_meta(JsonCursor& json, Transaction& transaction) {
        json.take();
        if (json.consume('}'))
            return;

        do {
            const auto key = json.string(key_storage_);
            json.take();

            if (key == "channel")
                transaction.channel = json.string(channel_storage_);
            else
                json.skip_value();
        } while (json.take() == ',');
    }

public:
    bool parse(std::string_view line, Transaction& transaction) {
        transaction = Transaction{};
        bool is_void = false;
        bool has_test = false;
        JsonCursor json(line);

        json.take();
        if (json.consume('}'))
            return false;

        do {
            const auto key = json.string(key_storage_);
            json.take();

            if (key == "account") {
                transaction.account = json.string(account_storage_);
            } else if (key == "type") {
                const auto type = json.string(temporary_storage_);
                transaction.debit = type == "debit";
                is_void = type == "void";
            } else if (key == "amount") {
                transaction.amount = json.string(amount_storage_);
            } else if (key == "currency") {
                transaction.currency = json.string(currency_storage_);
            } else if (key == "tags") {
                has_test = read_tags(json);
            } else if (key == "meta") {
                transaction.channel = {};
                read_meta(json, transaction);
            } else {
                json.skip_value();
            }
        } while (json.take() == ',');

        return !is_void && !has_test;
    }
};

static U64 hundredths(std::string_view amount) noexcept {
    U64 whole = 0;
    std::size_t i = 0;

    while (i < amount.size() && amount[i] != '.') {
        whole = whole * 10 + static_cast<unsigned>(amount[i] - '0');
        ++i;
    }

    U64 result = whole * 100;
    if (i < amount.size()) {
        ++i;
        result += static_cast<unsigned>(amount[i++] - '0') * 10u;
        if (i < amount.size())
            result += static_cast<unsigned>(amount[i] - '0');
    }
    return result;
}

struct ChannelStats {
    U64 count = 0;
    U64 net = 0;
};

class Output {
    std::string buffer_;

public:
    Output() {
        buffer_.reserve(1u << 16);
    }

    void append(std::string_view text) {
        buffer_.append(text.data(), text.size());
    }

    void number(U64 value) {
        char digits[32];
        const auto result = std::to_chars(digits, digits + sizeof(digits), value);
        buffer_.append(digits, static_cast<std::size_t>(result.ptr - digits));
    }

    void number(I64 value) {
        char digits[32];
        const auto result = std::to_chars(digits, digits + sizeof(digits), value);
        buffer_.append(digits, static_cast<std::size_t>(result.ptr - digits));
    }

    void newline() {
        buffer_.push_back('\n');
        if (buffer_.size() >= (1u << 16))
            flush();
    }

    void flush() {
        if (!buffer_.empty()) {
            std::fwrite(buffer_.data(), 1, buffer_.size(), stdout);
            buffer_.clear();
        }
    }
};

int main(int argc, char* argv[]) {
    if (argc < 2)
        return 0;

    std::FILE* input = std::fopen(argv[1], "rb");
    if (input == nullptr)
        return 0;

    LineReader reader(input);
    std::string_view line;

    if (!reader.next(line)) {
        std::fclose(input);
        return 0;
    }

    StringMap<Rate> rates;
    rates.reserve(16);
    read_rates(line, rates);

    using AccountMap = StringMap<U64>;
    using ChannelMap = StringMap<ChannelStats>;

    AccountMap accounts;
    ChannelMap channels;
    accounts.reserve(65536);
    channels.reserve(32);

    TransactionParser parser;
    Transaction transaction;
    U64 counted = 0;
    U64 net = 0;

    while (reader.next(line)) {
        if (!parser.parse(line, transaction))
            continue;

        const Rate& rate = rates.find(transaction.currency)->second;
        const U64 product = hundredths(transaction.amount) * rate.magnitude;
        U64 value = product / 1000000;

        if (rate.negative) {
            value += (product % 1000000 != 0);
            value = U64{0} - value;
        }
        if (transaction.debit)
            value = U64{0} - value;

        // Unsigned accumulation also avoids intermediate signed overflow.
        ++counted;
        net += value;

        auto account = accounts.find(transaction.account);
        if (account == accounts.end())
            accounts.emplace(std::string(transaction.account), value);
        else
            account->second += value;

        auto channel = channels.find(transaction.channel);
        if (channel == channels.end()) {
            channels.emplace(
                std::string(transaction.channel), ChannelStats{1, value});
        } else {
            ++channel->second.count;
            channel->second.net += value;
        }
    }

    std::fclose(input);

    using ChannelEntry = ChannelMap::value_type;
    std::vector<const ChannelEntry*> ordered_channels;
    ordered_channels.reserve(channels.size());

    for (const auto& entry : channels)
        ordered_channels.push_back(&entry);

    std::sort(
        ordered_channels.begin(), ordered_channels.end(),
        [](const ChannelEntry* a, const ChannelEntry* b) {
            return a->first < b->first;
        });

    using AccountEntry = AccountMap::value_type;
    const auto better = [](const AccountEntry* a, const AccountEntry* b) {
        const I64 a_net = std::bit_cast<I64>(a->second);
        const I64 b_net = std::bit_cast<I64>(b->second);
        if (a_net != b_net)
            return a_net > b_net;
        return a->first < b->first;
    };

    std::vector<const AccountEntry*> top;
    top.reserve(10);

    for (const auto& entry : accounts) {
        if (top.size() < 10) {
            top.push_back(&entry);
            std::push_heap(top.begin(), top.end(), better);
        } else if (better(&entry, top.front())) {
            std::pop_heap(top.begin(), top.end(), better);
            top.back() = &entry;
            std::push_heap(top.begin(), top.end(), better);
        }
    }

    std::sort(top.begin(), top.end(), better);

    Output output;
    output.append("counted ");
    output.number(counted);
    output.newline();

    output.append("net ");
    output.number(std::bit_cast<I64>(net));
    output.newline();

    for (const ChannelEntry* entry : ordered_channels) {
        output.append("channel ");
        output.append(entry->first);
        output.append(" ");
        output.number(entry->second.count);
        output.append(" ");
        output.number(std::bit_cast<I64>(entry->second.net));
        output.newline();
    }

    for (const AccountEntry* entry : top) {
        output.append("account ");
        output.append(entry->first);
        output.append(" ");
        output.number(std::bit_cast<I64>(entry->second));
        output.newline();
    }

    output.flush();
    return 0;
}
