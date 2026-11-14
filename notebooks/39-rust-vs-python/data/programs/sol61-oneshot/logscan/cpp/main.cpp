#include <algorithm>
#include <array>
#include <charconv>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <memory>
#include <string>
#include <system_error>
#include <unordered_map>
#include <vector>

using U64 = std::uint64_t;

constexpr U64 BIG_FLAG = U64(1) << 63;

static inline bool isDigit(char c) {
    return static_cast<unsigned char>(c - '0') <= 9;
}

static inline bool isLower(char c) {
    return static_cast<unsigned char>(c - 'a') <= 25;
}

static constexpr std::array<unsigned char, 256> makePathTable() {
    std::array<unsigned char, 256> table{};
    for (unsigned c = 'a'; c <= 'z'; ++c) table[c] = 1;
    for (unsigned c = 'A'; c <= 'Z'; ++c) table[c] = 1;
    for (unsigned c = '0'; c <= '9'; ++c) table[c] = 1;
    table['_'] = table['/'] = table['-'] = 1;
    return table;
}

static constexpr auto PATH_TABLE = makePathTable();

struct Parsed {
    const char* pathBegin;
    const char* pathEnd;
    const char* latencyBegin;
    const char* latencyEnd;
    unsigned fraction;
    unsigned statusClass;
};

static bool parseLine(const char* begin, const char* end, Parsed& result) {
    if (end - begin < 50) return false;

    if (begin[4] != '-' || begin[7] != '-' ||
        begin[10] != 'T' || begin[13] != ':' ||
        begin[16] != ':' || begin[19] != '.' ||
        begin[23] != 'Z' || begin[24] != ' ') {
        return false;
    }

    constexpr unsigned digitPositions[] = {
        0, 1, 2, 3, 5, 6, 8, 9, 11, 12, 14, 15, 17, 18, 20, 21, 22
    };
    for (unsigned position : digitPositions) {
        if (!isDigit(begin[position])) return false;
    }

    const char* p = begin + 25;
    const char* start = p;
    while (p < end && isLower(*p)) ++p;
    if (p == start || p == end || *p != '-') return false;
    ++p;

    start = p;
    while (p < end && isDigit(*p)) ++p;
    if (p == start || p == end || *p != ' ') return false;
    ++p;

    if (end - p < 4) return false;
    switch (*p) {
    case 'G':
        if (std::memcmp(p, "GET ", 4) != 0) return false;
        p += 4;
        break;
    case 'D':
        if (end - p < 7 || std::memcmp(p, "DELETE ", 7) != 0)
            return false;
        p += 7;
        break;
    case 'P':
        if (std::memcmp(p, "PUT ", 4) == 0) {
            p += 4;
        } else if (end - p >= 5 && std::memcmp(p, "POST ", 5) == 0) {
            p += 5;
        } else if (end - p >= 6 && std::memcmp(p, "PATCH ", 6) == 0) {
            p += 6;
        } else {
            return false;
        }
        break;
    default:
        return false;
    }

    if (p == end || *p != '/') return false;
    result.pathBegin = p;
    while (p < end && PATH_TABLE[static_cast<unsigned char>(*p)]) ++p;
    result.pathEnd = p;

    if (p < end && *p == '?') {
        ++p;
        while (p < end && *p != ' ') ++p;
    }
    if (p == end || *p != ' ') return false;
    ++p;

    if (end - p < 4 ||
        !isDigit(p[0]) || !isDigit(p[1]) || !isDigit(p[2]) ||
        p[3] != ' ') {
        return false;
    }
    result.statusClass = static_cast<unsigned>(p[0] - '0');
    p += 4;

    start = p;
    while (p < end && isDigit(*p)) ++p;
    if (p == start || end - p < 2 || p[0] != 'B' || p[1] != ' ')
        return false;
    p += 2;

    result.latencyBegin = p;
    while (p < end && isDigit(*p)) ++p;
    result.latencyEnd = p;
    if (p == result.latencyBegin || end - p < 7) return false;

    if (p[0] != '.' || !isDigit(p[1]) ||
        p[2] != 'm' || p[3] != 's' || p[4] != ' ' ||
        p[5] != '"' || end[-1] != '"') {
        return false;
    }

    if (std::memchr(p + 6, '"', static_cast<std::size_t>(end - p - 7)))
        return false;

    result.fraction = static_cast<unsigned>(p[1] - '0');
    return true;
}

static void makeTemplate(const Parsed& parsed, std::string& key) {
    key.clear();
    key.push_back('/');
    const char* p = parsed.pathBegin + 1;

    for (;;) {
        const char* segment = p;
        bool numeric = true;
        while (p < parsed.pathEnd && *p != '/') {
            numeric = numeric && isDigit(*p);
            ++p;
        }

        if (p != segment && numeric)
            key.append("{id}", 4);
        else
            key.append(segment, static_cast<std::size_t>(p - segment));

        if (p == parsed.pathEnd) break;
        key.push_back('/');
        ++p;
    }
}

static U64 makeLatency(const Parsed& parsed, std::vector<std::string>& big) {
    U64 whole = 0;
    auto conversion = std::from_chars(
        parsed.latencyBegin, parsed.latencyEnd, whole);

    if (conversion.ec == std::errc{} &&
        whole <= (BIG_FLAG - 1 - parsed.fraction) / 10) {
        return whole * 10 + parsed.fraction;
    }

    const char* first = parsed.latencyBegin;
    while (first < parsed.latencyEnd && *first == '0') ++first;

    const U64 index = static_cast<U64>(big.size());
    big.emplace_back(first, static_cast<std::size_t>(parsed.latencyEnd - first));
    big.back().push_back(static_cast<char>('0' + parsed.fraction));
    return BIG_FLAG | index;
}

struct LatencyLess {
    const std::vector<std::string>* big;

    bool operator()(U64 a, U64 b) const {
        if (((a | b) & BIG_FLAG) == 0) return a < b;
        if ((a & BIG_FLAG) == 0) return true;
        if ((b & BIG_FLAG) == 0) return false;

        const auto& x = (*big)[static_cast<std::size_t>(a ^ BIG_FLAG)];
        const auto& y = (*big)[static_cast<std::size_t>(b ^ BIG_FLAG)];
        if (x.size() != y.size()) return x.size() < y.size();
        return x < y;
    }
};

template<class Less>
static std::array<U64, 3> statistics(std::vector<U64>& values, Less less) {
    const std::size_t n = values.size();
    const std::size_t i50 = (n - 1) / 2;
    const std::size_t i95 = n - 1 - n / 20;

    auto begin = values.begin();
    auto percentile95 = begin + i95;
    std::nth_element(begin, percentile95, values.end(), less);

    const U64 p95 = *percentile95;
    const U64 maximum = *std::max_element(percentile95, values.end(), less);

    if (i50 < i95)
        std::nth_element(begin, begin + i50, percentile95, less);

    return {values[i50], p95, maximum};
}

static void appendInteger(std::string& output, U64 value) {
    char buffer[32];
    auto result = std::to_chars(buffer, buffer + sizeof(buffer), value);
    output.append(buffer, static_cast<std::size_t>(result.ptr - buffer));
}

static void appendLatency(
    std::string& output, U64 value, const std::vector<std::string>& big) {
    if ((value & BIG_FLAG) == 0) {
        appendInteger(output, value / 10);
        output.push_back('.');
        output.push_back(static_cast<char>('0' + value % 10));
    } else {
        const auto& digits = big[static_cast<std::size_t>(value ^ BIG_FLAG)];
        output.append(digits.data(), digits.size() - 1);
        output.push_back('.');
        output.push_back(digits.back());
    }
}

int main(int argc, char** argv) {
    if (argc < 2) return 0;
    std::FILE* input = std::fopen(argv[1], "rb");
    if (!input) return 0;

    using Groups = std::unordered_map<std::string, std::vector<U64>>;
    Groups groups;
    groups.max_load_factor(0.8f);
    groups.reserve(4096);

    std::vector<std::string> big;
    std::array<U64, 10> statuses{};
    U64 lines = 0;
    U64 malformed = 0;
    std::string key;
    key.reserve(256);

    auto processLine = [&](const char* begin, const char* end) {
        ++lines;
        Parsed parsed;
        if (!parseLine(begin, end, parsed)) {
            ++malformed;
            return;
        }

        ++statuses[parsed.statusClass];
        makeTemplate(parsed, key);
        const U64 latency = makeLatency(parsed, big);

        auto found = groups.find(key);
        if (found == groups.end())
            found = groups.try_emplace(key).first;
        found->second.push_back(latency);
    };

    constexpr std::size_t BUFFER_SIZE = 4 * 1024 * 1024;
    auto buffer = std::make_unique<char[]>(BUFFER_SIZE);
    std::string partial;

    for (;;) {
        const std::size_t bytes =
            std::fread(buffer.get(), 1, BUFFER_SIZE, input);
        if (bytes == 0) break;

        const char* p = buffer.get();
        const char* end = p + bytes;
        while (p < end) {
            const char* newline = static_cast<const char*>(
                std::memchr(p, '\n', static_cast<std::size_t>(end - p)));
            if (!newline) {
                partial.append(p, static_cast<std::size_t>(end - p));
                break;
            }

            if (partial.empty()) {
                processLine(p, newline);
            } else {
                partial.append(p, static_cast<std::size_t>(newline - p));
                processLine(partial.data(), partial.data() + partial.size());
                partial.clear();
            }
            p = newline + 1;
        }
    }
    std::fclose(input);

    using Entry = Groups::value_type;
    std::array<Entry*, 10> top{};
    std::size_t topCount = 0;

    auto better = [](const Entry& a, const Entry& b) {
        if (a.second.size() != b.second.size())
            return a.second.size() > b.second.size();
        return a.first < b.first;
    };

    for (auto& entry : groups) {
        std::size_t position = 0;
        while (position < topCount && better(*top[position], entry))
            ++position;

        if (position >= 10) continue;
        if (topCount < 10) ++topCount;
        for (std::size_t i = topCount - 1; i > position; --i)
            top[i] = top[i - 1];
        top[position] = &entry;
    }

    std::string output;
    output.reserve(4096);
    output.append("lines ");
    appendInteger(output, lines);
    output.append("\nmalformed ");
    appendInteger(output, malformed);
    output.push_back('\n');

    for (unsigned i = 0; i < 10; ++i) {
        if (statuses[i] == 0) continue;
        output.append("status ");
        output.push_back(static_cast<char>('0' + i));
        output.append("xx ");
        appendInteger(output, statuses[i]);
        output.push_back('\n');
    }

    for (std::size_t i = 0; i < topCount; ++i) {
        Entry& entry = *top[i];
        std::array<U64, 3> stats;
        if (big.empty()) {
            stats = statistics(entry.second,
                [](U64 a, U64 b) { return a < b; });
        } else {
            stats = statistics(entry.second, LatencyLess{&big});
        }

        output.append("path ");
        output.append(entry.first);
        output.push_back(' ');
        appendInteger(output, static_cast<U64>(entry.second.size()));
        for (U64 value : stats) {
            output.push_back(' ');
            appendLatency(output, value, big);
        }
        output.push_back('\n');
    }

    std::fwrite(output.data(), 1, output.size(), stdout);
    return 0;
}
