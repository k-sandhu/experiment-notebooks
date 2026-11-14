#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>
#include <unordered_map>
#include <vector>

using U64 = std::uint64_t;

static constexpr U64 BIG_FLAG = U64{1} << 63;

static const std::array<bool, 256> PATH_CHAR = [] {
    std::array<bool, 256> a{};
    for (unsigned c = 'a'; c <= 'z'; ++c) a[c] = true;
    for (unsigned c = 'A'; c <= 'Z'; ++c) a[c] = true;
    for (unsigned c = '0'; c <= '9'; ++c) a[c] = true;
    a['_'] = a['/'] = a['-'] = true;
    return a;
}();

static inline bool digit(char c) noexcept {
    return static_cast<unsigned char>(c) >= '0' &&
           static_cast<unsigned char>(c) <= '9';
}

struct Parsed {
    const char* pathBegin;
    const char* pathEnd;
    const char* integerBegin;
    const char* integerEnd;
    unsigned fraction;
    unsigned status;
};

static bool parseLine(const char* b, const char* e, Parsed& out) {
    if (e - b < 25) return false;

    if (b[4] != '-' || b[7] != '-' || b[10] != 'T' ||
        b[13] != ':' || b[16] != ':' || b[19] != '.' ||
        b[23] != 'Z' || b[24] != ' ') {
        return false;
    }

    static constexpr unsigned positions[] = {
        0, 1, 2, 3, 5, 6, 8, 9, 11, 12, 14, 15, 17, 18, 20, 21, 22
    };
    for (unsigned i : positions) {
        if (!digit(b[i])) return false;
    }

    const char* p = b + 25;
    const char* start = p;
    while (p < e && *p >= 'a' && *p <= 'z') ++p;
    if (p == start || p == e || *p != '-') return false;
    ++p;

    start = p;
    while (p < e && digit(*p)) ++p;
    if (p == start || p == e || *p != ' ') return false;
    ++p;

    const char* methodEnd = static_cast<const char*>(
        std::memchr(p, ' ', static_cast<std::size_t>(e - p)));
    if (!methodEnd) return false;

    const std::size_t methodLength =
        static_cast<std::size_t>(methodEnd - p);
    bool validMethod = false;
    switch (methodLength) {
        case 3:
            validMethod = std::memcmp(p, "GET", 3) == 0 ||
                          std::memcmp(p, "PUT", 3) == 0;
            break;
        case 4:
            validMethod = std::memcmp(p, "POST", 4) == 0;
            break;
        case 5:
            validMethod = std::memcmp(p, "PATCH", 5) == 0;
            break;
        case 6:
            validMethod = std::memcmp(p, "DELETE", 6) == 0;
            break;
        default:
            break;
    }
    if (!validMethod) return false;

    p = methodEnd + 1;
    if (p == e || *p != '/') return false;
    out.pathBegin = p;
    do {
        ++p;
    } while (p < e && PATH_CHAR[static_cast<unsigned char>(*p)]);
    out.pathEnd = p;

    if (p < e && *p == '?') {
        p = static_cast<const char*>(
            std::memchr(p + 1, ' ', static_cast<std::size_t>(e - p - 1)));
        if (!p) return false;
    }
    if (p == e || *p != ' ') return false;
    ++p;

    if (e - p < 4 || !digit(p[0]) || !digit(p[1]) ||
        !digit(p[2]) || p[3] != ' ') {
        return false;
    }
    out.status = static_cast<unsigned>(p[0] - '0');
    p += 4;

    start = p;
    while (p < e && digit(*p)) ++p;
    if (p == start || e - p < 2 || p[0] != 'B' || p[1] != ' ') {
        return false;
    }
    p += 2;

    out.integerBegin = p;
    while (p < e && digit(*p)) ++p;
    out.integerEnd = p;
    if (p == out.integerBegin || e - p < 7 ||
        p[0] != '.' || !digit(p[1]) ||
        p[2] != 'm' || p[3] != 's' ||
        p[4] != ' ' || p[5] != '"' || e[-1] != '"') {
        return false;
    }
    out.fraction = static_cast<unsigned>(p[1] - '0');
    p += 6;

    return std::memchr(p, '"', static_cast<std::size_t>((e - 1) - p))
           == nullptr;
}

struct LatencyLess {
    const std::vector<std::string>* large;

    bool operator()(U64 a, U64 b) const {
        if ((a & b & BIG_FLAG) == 0) return a < b;
        const std::string& x =
            (*large)[static_cast<std::size_t>(a & ~BIG_FLAG)];
        const std::string& y =
            (*large)[static_cast<std::size_t>(b & ~BIG_FLAG)];
        if (x.size() != y.size()) return x.size() < y.size();
        return x < y;
    }
};

class Scanner {
public:
    using Groups = std::unordered_map<std::string, std::vector<U64>>;
    using Entry = Groups::value_type;

    U64 lines = 0;
    U64 malformed = 0;
    std::array<U64, 10> statuses{};
    Groups groups;
    std::vector<std::string> largeLatencies;
    std::string path;

    Scanner() {
        groups.max_load_factor(0.8f);
        groups.reserve(4096);
        path.reserve(256);
    }

    void process(const char* b, const char* e) {
        ++lines;
        Parsed parsed{};
        if (!parseLine(b, e, parsed)) {
            ++malformed;
            return;
        }

        ++statuses[parsed.status];

        path.clear();
        const char* p = parsed.pathBegin;
        while (p < parsed.pathEnd) {
            if (*p == '/') {
                path.push_back('/');
                ++p;
                continue;
            }

            const char* segment = p;
            bool numeric = true;
            do {
                numeric = numeric && digit(*p);
                ++p;
            } while (p < parsed.pathEnd && *p != '/');

            if (numeric) {
                path.append("{id}", 4);
            } else {
                path.append(segment, static_cast<std::size_t>(p - segment));
            }
        }

        const char* significant = parsed.integerBegin;
        while (significant < parsed.integerEnd && *significant == '0') {
            ++significant;
        }

        U64 latency = 0;
        bool large = parsed.integerEnd - significant > 18;
        if (!large) {
            for (const char* q = significant; q < parsed.integerEnd; ++q) {
                latency = latency * 10 + static_cast<unsigned>(*q - '0');
            }
            latency = latency * 10 + parsed.fraction;
            large = latency >= BIG_FLAG;
        }

        if (large) {
            std::string value(
                significant,
                static_cast<std::size_t>(parsed.integerEnd - significant));
            value.push_back(static_cast<char>('0' + parsed.fraction));
            latency = BIG_FLAG | static_cast<U64>(largeLatencies.size());
            largeLatencies.push_back(std::move(value));
        }

        auto it = groups.find(path);
        if (it == groups.end()) {
            it = groups.try_emplace(path).first;
        }
        it->second.push_back(latency);
    }

    void appendLatency(std::string& output, U64 value) const {
        if ((value & BIG_FLAG) == 0) {
            output += std::to_string(value / 10);
            output.push_back('.');
            output.push_back(static_cast<char>('0' + value % 10));
        } else {
            const std::string& s =
                largeLatencies[static_cast<std::size_t>(value & ~BIG_FLAG)];
            output.append(s.data(), s.size() - 1);
            output.push_back('.');
            output.push_back(s.back());
        }
    }

    void print() {
        std::string output;
        output.reserve(4096);
        output += "lines ";
        output += std::to_string(lines);
        output += "\nmalformed ";
        output += std::to_string(malformed);
        output.push_back('\n');

        for (unsigned i = 0; i < 10; ++i) {
            if (statuses[i] == 0) continue;
            output += "status ";
            output.push_back(static_cast<char>('0' + i));
            output += "xx ";
            output += std::to_string(statuses[i]);
            output.push_back('\n');
        }

        const auto better = [](const Entry* a, const Entry* b) {
            if (a->second.size() != b->second.size()) {
                return a->second.size() > b->second.size();
            }
            return a->first < b->first;
        };

        std::array<Entry*, 10> top{};
        std::size_t used = 0;
        for (auto& entry : groups) {
            Entry* candidate = &entry;
            std::size_t position;
            if (used == top.size()) {
                if (!better(candidate, top.back())) continue;
                position = top.size() - 1;
            } else {
                position = used++;
            }
            while (position > 0 && better(candidate, top[position - 1])) {
                top[position] = top[position - 1];
                --position;
            }
            top[position] = candidate;
        }

        const LatencyLess less{&largeLatencies};
        for (std::size_t i = 0; i < used; ++i) {
            Entry& entry = *top[i];
            std::vector<U64>& values = entry.second;
            const std::size_t n = values.size();
            const std::size_t k50 = (n - 1) / 2;
            const std::size_t k95 = n - 1 - n / 20;

            auto at95 = values.begin() + k95;
            std::nth_element(values.begin(), at95, values.end(), less);
            const U64 p95 = *at95;
            const U64 maximum =
                *std::max_element(at95, values.end(), less);

            if (k50 < k95) {
                std::nth_element(
                    values.begin(), values.begin() + k50, at95, less);
            }
            const U64 p50 = values[k50];

            output += "path ";
            output += entry.first;
            output.push_back(' ');
            output += std::to_string(n);
            output.push_back(' ');
            appendLatency(output, p50);
            output.push_back(' ');
            appendLatency(output, p95);
            output.push_back(' ');
            appendLatency(output, maximum);
            output.push_back('\n');
        }

        std::fwrite(output.data(), 1, output.size(), stdout);
    }
};

int main(int argc, char* argv[]) {
    if (argc < 2) return 0;

    std::FILE* file = nullptr;
    if (fopen_s(&file, argv[1], "rb") != 0 || !file) return 0;

    Scanner scanner;
    std::vector<char> buffer(4 * 1024 * 1024);
    std::string pending;

    for (;;) {
        const std::size_t count =
            std::fread(buffer.data(), 1, buffer.size(), file);
        if (count == 0) break;

        const char* p = buffer.data();
        const char* end = p + count;

        if (!pending.empty()) {
            const char* newline = static_cast<const char*>(
                std::memchr(p, '\n', static_cast<std::size_t>(end - p)));
            if (!newline) {
                pending.append(p, static_cast<std::size_t>(end - p));
                continue;
            }
            pending.append(p, static_cast<std::size_t>(newline - p));
            scanner.process(pending.data(), pending.data() + pending.size());
            pending.clear();
            p = newline + 1;
        }

        while (p < end) {
            const char* newline = static_cast<const char*>(
                std::memchr(p, '\n', static_cast<std::size_t>(end - p)));
            if (!newline) {
                pending.assign(p, static_cast<std::size_t>(end - p));
                break;
            }
            scanner.process(p, newline);
            p = newline + 1;
        }
    }

    std::fclose(file);
    scanner.print();
    return 0;
}
