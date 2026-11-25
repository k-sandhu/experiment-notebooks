#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <unordered_map>
#include <vector>
#ifdef _WIN32
#include <fcntl.h>
#include <io.h>
#endif

using Number = std::uint64_t;
struct Group {
    std::vector<Number> values;
    // Values with more than 15 significant digits, without leading zeros.
    std::vector<std::string> large;
    std::size_t count() const { return values.size() + large.size(); }
};

static bool digit(unsigned char c) { return c >= '0' && c <= '9'; }
static const auto path_chars = [] {
    std::array<bool, 256> a{};
    for (int c = 0; c < 256; ++c)
        a[c] = digit(static_cast<unsigned char>(c)) || (c >= 'A' && c <= 'Z') ||
            (c >= 'a' && c <= 'z') || c == '_' || c == '/' || c == '-';
    return a;
}();

class Scanner {
    std::unordered_map<std::string, Group> groups;
    std::string key;
    Number lines = 0, malformed = 0;
    std::array<Number, 10> statuses{};

    bool parse(std::string_view s) {
        const std::size_t n = s.size();
        if (n < 50) return false;
        constexpr std::string_view stamp = "0000-00-00T00:00:00.000Z ";
        for (std::size_t j = 0; j < stamp.size(); ++j)
            if (stamp[j] == '0' ? !digit(s[j]) : s[j] != stamp[j]) return false;
        std::size_t i = 25, start = i;
        while (i < n && s[i] >= 'a' && s[i] <= 'z') ++i;
        if (i == start || i == n || s[i++] != '-') return false;
        start = i;
        while (i < n && digit(s[i])) ++i;
        if (i == start || i == n || s[i++] != ' ') return false;
        start = i;
        while (i < n && s[i] != ' ') ++i;
        const auto method = s.substr(start, i - start);
        if (i == n || (method != "GET" && method != "POST" && method != "PUT" &&
                        method != "DELETE" && method != "PATCH")) return false;
        ++i;
        if (i == n || s[i] != '/') return false;
        const std::size_t path_start = i;
        while (i < n && path_chars[static_cast<unsigned char>(s[i])]) ++i;
        const std::size_t path_end = i;
        if (i < n && s[i] == '?') while (i < n && s[i] != ' ') ++i;
        if (i == n || s[i++] != ' ') return false;
        if (n - i < 4 || !digit(s[i]) || !digit(s[i+1]) || !digit(s[i+2]) || s[i+3] != ' ')
            return false;
        const unsigned status = s[i] - '0';
        i += 4;
        start = i;
        while (i < n && digit(s[i])) ++i;
        if (i == start || n - i < 2 || s[i] != 'B' || s[i+1] != ' ') return false;
        i += 2;
        start = i;
        while (i < n && s[i] == '0') ++i;
        const std::size_t significant = i;
        while (i < n && digit(s[i])) ++i;
        const std::size_t decimal = i;
        if (i == start || n - i < 7 || s[i] != '.' || !digit(s[i+1]) ||
            s[i+2] != 'm' || s[i+3] != 's' || s[i+4] != ' ' || s[i+5] != '"' ||
            s[n-1] != '"' || s.find('"', i+6) != n-1) return false;

        key.clear();
        std::size_t p = path_start;
        while (p < path_end) {
            key.push_back('/');
            start = ++p;
            bool numeric = true;
            while (p < path_end && s[p] != '/') { numeric &= digit(s[p]); ++p; }
            if (p != start && numeric) key += "{id}";
            else key.append(s.data() + start, p - start);
        }
        auto& group = groups.try_emplace(key).first->second;
        if (decimal - significant <= 14) {
            Number value = 0;
            for (std::size_t j = significant; j < decimal; ++j) value = value * 10 + (s[j] - '0');
            group.values.push_back(value * 10 + (s[decimal+1] - '0'));
        } else {
            std::string value(s.substr(significant, decimal - significant));
            value.push_back(s[decimal+1]);
            group.large.push_back(std::move(value));
        }
        ++statuses[status];
        return true;
    }

    static std::string format(Number value) {
        return std::to_string(value / 10) + '.' + char('0' + value % 10);
    }
    static bool large_less(const std::string& a, const std::string& b) {
        return a.size() != b.size() ? a.size() < b.size() : a < b;
    }
public:
    void read(const char* path) {
        FILE* f = std::fopen(path, "rb");
        if (!f) throw std::runtime_error("Cannot open input");
        std::vector<char> buffer(1 << 20);
        std::size_t used = 0;
        for (;;) {
            const std::size_t got = std::fread(buffer.data() + used, 1, buffer.size() - used, f);
            if (!got) break;
            const std::size_t end = used + got;
            std::size_t begin = 0;
            while (begin < end) {
                const char* newline = static_cast<const char*>(std::memchr(buffer.data() + begin, '\n', end - begin));
                if (!newline) break;
                const std::size_t next = newline - buffer.data();
                ++lines;
                if (!parse(std::string_view(buffer.data() + begin, next - begin))) ++malformed;
                begin = next + 1;
            }
            used = end - begin;
            if (used) std::memmove(buffer.data(), buffer.data() + begin, used);
            if (used == buffer.size()) buffer.resize(buffer.size() * 2);
        }
        const bool failed = std::ferror(f) != 0;
        std::fclose(f);
        if (failed) throw std::runtime_error("Cannot read input");
    }
    void output() {
        std::cout << "lines " << lines << "\nmalformed " << malformed << '\n';
        for (unsigned c = 0; c < 10; ++c)
            if (statuses[c]) std::cout << "status " << c << "xx " << statuses[c] << '\n';
        using Entry = std::pair<const std::string, Group>;
        std::vector<Entry*> top;
        auto better = [](const Entry* a, const Entry* b) {
            return a->second.count() != b->second.count() ? a->second.count() > b->second.count() : a->first < b->first;
        };
        for (auto& entry : groups) {
            auto pos = std::lower_bound(top.begin(), top.end(), &entry, better);
            if (top.size() < 10 || pos != top.end()) {
                top.insert(pos, &entry);
                if (top.size() > 10) top.pop_back();
            }
        }
        for (auto* entry : top) {
            auto& g = entry->second;
            const std::size_t count = g.count();
            std::sort(g.large.begin(), g.large.end(), large_less);
            std::array<std::size_t, 3> ranks{(count - 1) / 2, count - 1 - count / 20, count - 1};
            std::array<std::string, 3> result;
            std::size_t lower = 0;
            for (unsigned r = 0; r < 3; ++r) {
                const auto rank = ranks[r];
                if (rank < g.values.size()) {
                    if (rank >= lower) {
                        std::nth_element(g.values.begin() + lower, g.values.begin() + rank, g.values.end());
                        lower = rank + 1;
                    }
                    result[r] = format(g.values[rank]);
                } else {
                    const auto& v = g.large[rank - g.values.size()];
                    result[r] = v.substr(0, v.size()-1) + '.' + v.back();
                }
            }
            std::cout << "path " << entry->first << ' ' << count << ' ' << result[0] << ' ' << result[1] << ' ' << result[2] << '\n';
        }
    }
};

int main(int argc, char** argv) {
    if (argc < 2) return 1;
#ifdef _WIN32
    // Preserve the specified LF bytes when stdout is redirected on Windows.
    _setmode(_fileno(stdout), _O_BINARY);
#endif
    std::ios::sync_with_stdio(false);
    try { Scanner scanner; scanner.read(argv[1]); scanner.output(); }
    catch (const std::exception& e) { std::cerr << e.what() << '\n'; return 1; }
}
