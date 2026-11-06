// Log scan: status-class counts and latency percentiles of the busiest path templates (see SPEC.md).
//
// The file is streamed in 1 MiB chunks. Each line is checked by a hand-written matcher that accepts
// exactly the language of the SPEC regex. Path templates are interned in a hash map keyed by string_view,
// so a lookup never allocates. Only the ten busiest templates have their latencies sorted.

#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>
#include <string_view>
#include <unordered_map>
#include <utility>
#include <vector>

#include <fcntl.h>
#include <io.h>

namespace {

constexpr size_t kChunkSize = 1 << 20;
constexpr size_t kTopN = 10;

// Characters allowed in the path group: [A-Za-z0-9_/-].
constexpr std::array<bool, 256> make_path_table() {
    std::array<bool, 256> t{};
    for (int c = 0; c < 256; ++c) {
        t[c] = (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') || c == '_' ||
               c == '/' || c == '-';
    }
    return t;
}
constexpr std::array<bool, 256> kPathChar = make_path_table();

inline bool is_digit(char c) { return static_cast<unsigned char>(c - '0') < 10; }
inline bool is_lower(char c) { return static_cast<unsigned char>(c - 'a') < 26; }

// True if [p, e) starts with the literal lit (lit has no terminating NUL).
inline bool starts_with(const char* p, const char* e, std::string_view lit) {
    return static_cast<size_t>(e - p) >= lit.size() && std::memcmp(p, lit.data(), lit.size()) == 0;
}

struct Line {
    int status_class;     // first digit of the status code
    const char* path;     // path group, without any query string
    const char* path_end;
    int64_t tenths;       // latency in tenths of a millisecond
};

// Matches one line (without its '\n') against the SPEC regex. Returns false for a malformed line.
bool parse_line(const char* p, const char* e, Line& out) {
    // Timestamp: dddd-dd-ddTdd:dd:dd.dddZ followed by a space.
    if (e - p < 25) return false;
    static constexpr std::string_view kTs = "dddd-dd-ddTdd:dd:dd.dddZ";
    for (size_t i = 0; i < kTs.size(); ++i) {
        if (kTs[i] == 'd' ? !is_digit(p[i]) : p[i] != kTs[i]) return false;
    }
    if (p[24] != ' ') return false;
    p += 25;

    // Host: [a-z]+-\d+ followed by a space.
    const char* q = p;
    while (q < e && is_lower(*q)) ++q;
    if (q == p || q == e || *q != '-') return false;
    const char* digits = ++q;
    while (q < e && is_digit(*q)) ++q;
    if (q == digits || q == e || *q != ' ') return false;
    p = q + 1;

    // Method, then a space. The methods are checked in the order of the spec's alternation.
    if (starts_with(p, e, "GET ")) p += 4;
    else if (starts_with(p, e, "POST ")) p += 5;
    else if (starts_with(p, e, "PUT ")) p += 4;
    else if (starts_with(p, e, "DELETE ")) p += 7;
    else if (starts_with(p, e, "PATCH ")) p += 6;
    else return false;

    // Path: '/' followed by path characters, then an optional query that runs to the next space.
    if (p == e || *p != '/') return false;
    out.path = p;
    ++p;
    while (p < e && kPathChar[static_cast<unsigned char>(*p)]) ++p;
    out.path_end = p;
    if (p < e && *p == '?') {
        while (p < e && *p != ' ') ++p;
    }
    if (p == e || *p != ' ') return false;
    ++p;

    // Status: exactly three digits, then a space.
    if (e - p < 4 || !is_digit(p[0]) || !is_digit(p[1]) || !is_digit(p[2]) || p[3] != ' ') return false;
    out.status_class = p[0] - '0';
    p += 4;

    // Response size: \d+B followed by a space.
    q = p;
    while (q < e && is_digit(*q)) ++q;
    if (q == p || q == e || *q != 'B') return false;
    if (++q == e || *q != ' ') return false;
    p = q + 1;

    // Latency: \d+ '.' \d 'ms' followed by a space. Value is kept in tenths of a millisecond.
    q = p;
    int64_t whole = 0;
    while (q < e && is_digit(*q)) whole = whole * 10 + (*q++ - '0');
    if (q == p || q == e || *q != '.') return false;
    if (++q == e || !is_digit(*q)) return false;
    const int64_t frac = *q++ - '0';
    if (e - q < 3 || q[0] != 'm' || q[1] != 's' || q[2] != ' ') return false;
    out.tenths = whole * 10 + frac;
    p = q + 3;

    // User agent: "[^"]*" which must end the line.
    if (e - p < 2 || *p != '"' || e[-1] != '"') return false;
    for (const char* u = p + 1; u < e - 1; ++u) {
        if (*u == '"') return false;
    }
    return true;
}

struct Template {
    std::string name;
    uint64_t count = 0;
    std::vector<int64_t> latencies;  // tenths of a millisecond
};

struct StringViewHash {
    using is_transparent = void;
    size_t operator()(std::string_view s) const noexcept { return std::hash<std::string_view>{}(s); }
};

class Scanner {
public:
    void add(const char* p, const char* e) {
        ++total_;
        Line line;
        if (!parse_line(p, e, line)) {
            ++malformed_;
            return;
        }
        ++status_[line.status_class];
        build_template(line.path, line.path_end);

        auto it = index_.find(std::string_view(template_));
        size_t id;
        if (it == index_.end()) {
            id = templates_.size();
            templates_.push_back(Template{template_, 0, {}});
            index_.emplace(template_, id);
        } else {
            id = it->second;
        }
        Template& t = templates_[id];
        ++t.count;
        t.latencies.push_back(line.tenths);
    }

    void report(std::FILE* out) {
        std::string s = "lines " + std::to_string(total_) + "\nmalformed " + std::to_string(malformed_) + "\n";
        for (int c = 0; c < 10; ++c) {
            if (status_[c] != 0) {
                s += "status " + std::to_string(c) + "xx " + std::to_string(status_[c]) + "\n";
            }
        }

        // Keep the kTopN busiest templates, best first, by insertion into a small sorted array.
        auto better = [this](size_t a, size_t b) {
            if (templates_[a].count != templates_[b].count) return templates_[a].count > templates_[b].count;
            return templates_[a].name < templates_[b].name;
        };
        std::vector<size_t> top;
        top.reserve(kTopN + 1);
        for (size_t i = 0; i < templates_.size(); ++i) {
            if (top.size() == kTopN) {
                if (!better(i, top.back())) continue;
                top.back() = i;
            } else {
                top.push_back(i);
            }
            for (size_t k = top.size() - 1; k > 0 && better(top[k], top[k - 1]); --k) {
                std::swap(top[k], top[k - 1]);
            }
        }

        for (size_t id : top) {
            Template& t = templates_[id];
            std::vector<int64_t>& lat = t.latencies;
            std::sort(lat.begin(), lat.end());
            const uint64_t n = lat.size();
            const int64_t p50 = lat[(50 * n + 99) / 100 - 1];
            const int64_t p95 = lat[(95 * n + 99) / 100 - 1];
            s += "path " + t.name + " " + std::to_string(t.count) + " " + format_tenths(p50) + " " +
                 format_tenths(p95) + " " + format_tenths(lat.back()) + "\n";
        }
        std::fwrite(s.data(), 1, s.size(), out);
    }

private:
    static std::string format_tenths(int64_t t) {
        return std::to_string(t / 10) + "." + static_cast<char>('0' + t % 10);
    }

    // Path template: each non-empty all-digit segment becomes {id}. Writes into template_.
    void build_template(const char* p, const char* e) {
        template_.clear();
        const char* seg = p;
        for (;;) {
            const char* end = seg;
            bool all_digits = true;
            while (end < e && *end != '/') {
                all_digits = all_digits && is_digit(*end);
                ++end;
            }
            if (end > seg && all_digits) {
                template_ += "{id}";
            } else {
                template_.append(seg, end);
            }
            if (end == e) break;
            template_ += '/';
            seg = end + 1;
        }
    }

    uint64_t total_ = 0;
    uint64_t malformed_ = 0;
    std::array<uint64_t, 10> status_{};
    std::string template_;
    std::vector<Template> templates_;
    std::unordered_map<std::string, size_t, StringViewHash, std::equal_to<>> index_;
};

}  // namespace

int main(int argc, char** argv) {
    if (argc < 2) {
        std::fprintf(stderr, "usage: solution INPUT_PATH\n");
        return 2;
    }
    std::FILE* in = std::fopen(argv[1], "rb");
    if (!in) {
        std::fprintf(stderr, "cannot open %s\n", argv[1]);
        return 1;
    }

    Scanner scanner;
    std::vector<char> buf(kChunkSize);
    size_t start = 0;  // first byte of the unprocessed data
    size_t end = 0;    // one past the last byte read
    bool eof = false;
    for (;;) {
        const void* nl = std::memchr(buf.data() + start, '\n', end - start);
        if (nl) {
            const char* line_end = static_cast<const char*>(nl);
            scanner.add(buf.data() + start, line_end);
            start = static_cast<size_t>(line_end - buf.data()) + 1;
            continue;
        }
        if (eof) {
            if (start < end) scanner.add(buf.data() + start, buf.data() + end);  // last line without '\n'
            break;
        }
        // No complete line in the buffer: move the partial line to the front and read more.
        if (start > 0) {
            std::memmove(buf.data(), buf.data() + start, end - start);
            end -= start;
            start = 0;
        }
        if (end == buf.size()) buf.resize(buf.size() * 2);  // one line longer than the buffer
        const size_t n = std::fread(buf.data() + end, 1, buf.size() - end, in);
        end += n;
        if (n == 0) eof = true;
    }
    std::fclose(in);

    // Keep '\n' as is: the text-mode CRT would turn it into "\r\n".
    _setmode(_fileno(stdout), _O_BINARY);
    scanner.report(stdout);
    return 0;
}
