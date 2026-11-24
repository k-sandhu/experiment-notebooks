#include <algorithm>
#include <bit>
#include <cstdint>
#include <cstdio>
#include <iostream>
#include <string>
#include <string_view>
#include <unordered_map>
#include <utility>
#include <vector>

using namespace std;

struct StringHash {
    using is_transparent = void;

    size_t operator()(string_view s) const noexcept {
        return hash<string_view>{}(s);
    }
};

struct StringEqual {
    using is_transparent = void;

    bool operator()(string_view a, string_view b) const noexcept {
        return a == b;
    }
};

class Parser {
    const char* p;

    static unsigned hex(char c) {
        if (c >= '0' && c <= '9') return static_cast<unsigned>(c - '0');
        if (c >= 'a' && c <= 'f') return static_cast<unsigned>(c - 'a' + 10);
        return static_cast<unsigned>(c - 'A' + 10);
    }

    unsigned readHex4() {
        unsigned value = 0;
        for (int i = 0; i < 4; ++i) {
            value = (value << 4) | hex(*p++);
        }
        return value;
    }

    static void appendUtf8(string& out, unsigned cp) {
        if (cp <= 0x7f) {
            out.push_back(static_cast<char>(cp));
        } else if (cp <= 0x7ff) {
            out.push_back(static_cast<char>(0xc0 | (cp >> 6)));
            out.push_back(static_cast<char>(0x80 | (cp & 0x3f)));
        } else if (cp <= 0xffff) {
            out.push_back(static_cast<char>(0xe0 | (cp >> 12)));
            out.push_back(static_cast<char>(0x80 | ((cp >> 6) & 0x3f)));
            out.push_back(static_cast<char>(0x80 | (cp & 0x3f)));
        } else {
            out.push_back(static_cast<char>(0xf0 | (cp >> 18)));
            out.push_back(static_cast<char>(0x80 | ((cp >> 12) & 0x3f)));
            out.push_back(static_cast<char>(0x80 | ((cp >> 6) & 0x3f)));
            out.push_back(static_cast<char>(0x80 | (cp & 0x3f)));
        }
    }

    void skipString() {
        ++p;
        while (*p != '"') {
            if (*p == '\\') {
                p += 2;
            } else {
                ++p;
            }
        }
        ++p;
    }

public:
    explicit Parser(const char* input) : p(input) {}

    void whitespace() {
        while (*p == ' ' || *p == '\t' || *p == '\r' || *p == '\n') {
            ++p;
        }
    }

    char peek() {
        whitespace();
        return *p;
    }

    void consume(char) {
        whitespace();
        ++p;
    }

    string_view readString(string& scratch) {
        whitespace();
        ++p;
        const char* start = p;

        while (*p != '"' && *p != '\\') {
            ++p;
        }

        if (*p == '"') {
            string_view result(start, static_cast<size_t>(p - start));
            ++p;
            return result;
        }

        scratch.assign(start, static_cast<size_t>(p - start));
        for (;;) {
            if (*p == '"') {
                ++p;
                return scratch;
            }
            if (*p != '\\') {
                scratch.push_back(*p++);
                continue;
            }

            ++p;
            char escape = *p++;
            switch (escape) {
                case '"':  scratch.push_back('"'); break;
                case '\\': scratch.push_back('\\'); break;
                case '/':  scratch.push_back('/'); break;
                case 'b':  scratch.push_back('\b'); break;
                case 'f':  scratch.push_back('\f'); break;
                case 'n':  scratch.push_back('\n'); break;
                case 'r':  scratch.push_back('\r'); break;
                case 't':  scratch.push_back('\t'); break;
                case 'u': {
                    unsigned cp = readHex4();
                    if (cp >= 0xd800 && cp <= 0xdbff) {
                        p += 2; // Backslash and 'u' of the low surrogate.
                        unsigned low = readHex4();
                        cp = 0x10000 + ((cp - 0xd800) << 10)
                             + (low - 0xdc00);
                    }
                    appendUtf8(scratch, cp);
                    break;
                }
            }
        }
    }

    uint64_t readUnsigned() {
        whitespace();
        uint64_t value = 0;
        while (*p >= '0' && *p <= '9') {
            value = value * 10 + static_cast<unsigned>(*p++ - '0');
        }
        return value;
    }

    void skipValue() {
        whitespace();
        if (*p == '"') {
            skipString();
            return;
        }
        if (*p == '{' || *p == '[') {
            int depth = 0;
            do {
                char c = *p;
                if (c == '"') {
                    skipString();
                } else {
                    if (c == '{' || c == '[') ++depth;
                    else if (c == '}' || c == ']') --depth;
                    ++p;
                }
            } while (depth != 0);
            return;
        }
        while (*p && *p != ',' && *p != '}' && *p != ']' &&
               *p != ' ' && *p != '\t' && *p != '\r' && *p != '\n') {
            ++p;
        }
    }
};

using Rates = unordered_map<string, uint64_t, StringHash, StringEqual>;

static void readRates(const string& line, Rates& rates) {
    Parser parser(line.c_str());
    string keyBuffer;
    string currencyBuffer;

    parser.consume('{');
    while (parser.peek() != '}') {
        string_view key = parser.readString(keyBuffer);
        parser.consume(':');

        if (key == "rates") {
            parser.consume('{');
            while (parser.peek() != '}') {
                string_view currency = parser.readString(currencyBuffer);
                parser.consume(':');
                uint64_t rate = parser.readUnsigned();
                rates[string(currency)] = rate;
                if (parser.peek() == ',') parser.consume(',');
                else break;
            }
            parser.consume('}');
        } else {
            parser.skipValue();
        }

        if (parser.peek() == ',') parser.consume(',');
        else break;
    }
}

struct Transaction {
    string accountBuffer;
    string currencyBuffer;
    string amountBuffer;
    string typeBuffer;
    string channelBuffer;
    string keyBuffer;
    string tagBuffer;

    string_view account;
    string_view currency;
    string_view amount;
    string_view type;
    string_view channel;

    bool parse(const string& line) {
        Parser parser(line.c_str());
        parser.consume('{');

        while (parser.peek() != '}') {
            string_view key = parser.readString(keyBuffer);
            parser.consume(':');

            if (key == "account") {
                account = parser.readString(accountBuffer);
            } else if (key == "currency") {
                currency = parser.readString(currencyBuffer);
            } else if (key == "amount") {
                amount = parser.readString(amountBuffer);
            } else if (key == "type") {
                type = parser.readString(typeBuffer);
                if (type == "void") return false;
            } else if (key == "tags") {
                parser.consume('[');
                while (parser.peek() != ']') {
                    string_view tag = parser.readString(tagBuffer);
                    if (tag == "test") return false;
                    if (parser.peek() == ',') parser.consume(',');
                    else break;
                }
                parser.consume(']');
            } else if (key == "meta") {
                parser.consume('{');
                while (parser.peek() != '}') {
                    string_view metaKey = parser.readString(keyBuffer);
                    parser.consume(':');
                    if (metaKey == "channel") {
                        channel = parser.readString(channelBuffer);
                    } else {
                        parser.skipValue();
                    }
                    if (parser.peek() == ',') parser.consume(',');
                    else break;
                }
                parser.consume('}');
            } else {
                parser.skipValue();
            }

            if (parser.peek() == ',') parser.consume(',');
            else break;
        }
        return true;
    }
};

static uint64_t hundredths(string_view amount) {
    uint64_t whole = 0;
    size_t i = 0;
    while (i < amount.size() && amount[i] != '.') {
        whole = whole * 10 + static_cast<unsigned>(amount[i] - '0');
        ++i;
    }

    unsigned fraction = 0;
    if (i < amount.size()) {
        ++i;
        fraction = static_cast<unsigned>(amount[i++] - '0') * 10;
        if (i < amount.size()) {
            fraction += static_cast<unsigned>(amount[i] - '0');
        }
    }
    return whole * 100 + fraction;
}

struct ChannelTotal {
    uint64_t count = 0;
    uint64_t net = 0;
};

static int64_t signedTotal(uint64_t value) {
    return bit_cast<int64_t>(value);
}

int main(int argc, char** argv) {
    if (argc < 2) return 1;

    FILE* input = nullptr;
    if (fopen_s(&input, argv[1], "rb") != 0) return 1;

    constexpr size_t bufferSize = 1 << 20;
    vector<char> buffer(bufferSize);
    string line;
    line.reserve(1024);

    Rates rates;
    rates.reserve(32);

    unordered_map<string, uint64_t, StringHash, StringEqual> accounts;
    accounts.reserve(65536);

    unordered_map<string, ChannelTotal, StringHash, StringEqual> channels;
    channels.reserve(32);

    uint64_t totalCount = 0;
    uint64_t totalNet = 0;
    bool firstLine = true;
    Transaction transaction;

    auto processLine = [&]() {
        if (firstLine) {
            readRates(line, rates);
            firstLine = false;
            return;
        }

        if (!transaction.parse(line)) return;

        auto rateIt = rates.find(transaction.currency);
        uint64_t value = hundredths(transaction.amount) * rateIt->second / 1000000;
        if (transaction.type == "debit") value = uint64_t(0) - value;

        ++totalCount;
        totalNet += value;

        auto accountIt = accounts.find(transaction.account);
        if (accountIt == accounts.end()) {
            accounts.emplace(string(transaction.account), value);
        } else {
            accountIt->second += value;
        }

        auto channelIt = channels.find(transaction.channel);
        if (channelIt == channels.end()) {
            channels.emplace(string(transaction.channel), ChannelTotal{1, value});
        } else {
            ++channelIt->second.count;
            channelIt->second.net += value;
        }
    };

    size_t bytesRead;
    while ((bytesRead = fread(buffer.data(), 1, buffer.size(), input)) != 0) {
        size_t start = 0;
        for (size_t i = 0; i < bytesRead; ++i) {
            if (buffer[i] == '\n') {
                line.append(buffer.data() + start, i - start);
                processLine();
                line.clear();
                start = i + 1;
            }
        }
        line.append(buffer.data() + start, bytesRead - start);
    }
    if (!line.empty()) processLine();
    fclose(input);

    ios::sync_with_stdio(false);
    cout << "counted " << totalCount << '\n';
    cout << "net " << signedTotal(totalNet) << '\n';

    using ChannelEntry = decltype(channels)::value_type;
    vector<const ChannelEntry*> sortedChannels;
    sortedChannels.reserve(channels.size());
    for (const auto& entry : channels) sortedChannels.push_back(&entry);
    sort(sortedChannels.begin(), sortedChannels.end(),
         [](const ChannelEntry* a, const ChannelEntry* b) {
             return a->first < b->first;
         });

    for (const ChannelEntry* entry : sortedChannels) {
        cout << "channel " << entry->first << ' '
             << entry->second.count << ' '
             << signedTotal(entry->second.net) << '\n';
    }

    using AccountEntry = decltype(accounts)::value_type;
    vector<const AccountEntry*> topAccounts;
    topAccounts.reserve(accounts.size());
    for (const auto& entry : accounts) topAccounts.push_back(&entry);

    auto accountOrder = [](const AccountEntry* a, const AccountEntry* b) {
        int64_t aNet = signedTotal(a->second);
        int64_t bNet = signedTotal(b->second);
        if (aNet != bNet) return aNet > bNet;
        return a->first < b->first;
    };

    size_t topCount = min<size_t>(10, topAccounts.size());
    partial_sort(topAccounts.begin(), topAccounts.begin() + topCount,
                 topAccounts.end(), accountOrder);

    for (size_t i = 0; i < topCount; ++i) {
        cout << "account " << topAccounts[i]->first << ' '
             << signedTotal(topAccounts[i]->second) << '\n';
    }

    return 0;
}
