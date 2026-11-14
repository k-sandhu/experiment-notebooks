// Weighted alignment cost (see SPEC.md).
//
// The whole input is read into memory once and parsed in place: tokens are
// views into that buffer, letters are mapped to small codes, and the per-letter
// costs are copied into flat arrays. The DP keeps one row of 64-bit costs and
// updates it in place, carrying the diagonal and left values in registers.

#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <string>
#include <string_view>
#include <vector>

#ifdef _WIN32
#include <fcntl.h>
#include <io.h>
#endif

namespace {

using i64 = std::int64_t;

std::string readFile(const char* path) {
    std::FILE* f = std::fopen(path, "rb");
    if (!f) {
        std::fprintf(stderr, "cannot open %s\n", path);
        std::exit(1);
    }
    std::string data;
    char buf[1 << 16];
    std::size_t got;
    while ((got = std::fread(buf, 1, sizeof buf, f)) > 0) data.append(buf, got);
    std::fclose(f);
    return data;
}

inline bool isSpace(char c) { return c == ' ' || c == '\n' || c == '\r' || c == '\t'; }

// Whitespace-separated tokens; every token in the input is a single word.
class Reader {
public:
    explicit Reader(std::string_view text) : p_(text.data()), end_(text.data() + text.size()) {}

    std::string_view token() {
        while (p_ < end_ && isSpace(*p_)) ++p_;
        const char* start = p_;
        while (p_ < end_ && !isSpace(*p_)) ++p_;
        return std::string_view(start, static_cast<std::size_t>(p_ - start));
    }

    i64 number() {
        std::string_view t = token();
        i64 v = 0;
        for (char c : t) v = v * 10 + (c - '0');
        return v;
    }

private:
    const char* p_;
    const char* end_;
};

struct Costs {
    int A = 0;
    std::vector<i64> ins, del, sub;  // sub is row-major: sub[i * A + j]
};

// Cost of the pair: s[0..n) are rows (deletions), t[0..m) are columns (insertions).
// Scratch: row must hold m + 1 values; tIns must hold m values.
i64 alignCost(const unsigned char* s, int n, const unsigned char* t, int m,
              const Costs& c, i64* row, const i64* tIns) {
    row[0] = 0;
    for (int j = 1; j <= m; ++j) row[j] = row[j - 1] + tIns[j - 1];

    for (int i = 0; i < n; ++i) {
        const unsigned char si = s[i];
        const i64 d = c.del[si];
        const i64* subRow = c.sub.data() + static_cast<std::size_t>(si) * c.A;

        i64 diag = row[0];  // D[i][j-1] before this row is overwritten
        i64 left = row[0] += d;
        for (int j = 1; j <= m; ++j) {
            const i64 up = row[j];  // D[i][j] from the previous row
            const i64 fromUp = up + d;
            const i64 fromLeft = left + tIns[j - 1];
            const i64 fromDiag = diag + subRow[t[j - 1]];
            // fromLeft is the only term that depends on the previous cell, so it goes last.
            const i64 v = std::min(std::min(fromUp, fromDiag), fromLeft);
            row[j] = v;
            left = v;
            diag = up;
        }
    }
    return row[m];
}

// Keeps '\n' as '\n' on Windows (text mode would write "\r\n").
void setBinaryStdout() {
#ifdef _WIN32
    _setmode(_fileno(stdout), _O_BINARY);
#endif
}

}  // namespace

int main(int argc, char** argv) {
    if (argc < 2) {
        std::fprintf(stderr, "usage: solution INPUT_PATH\n");
        return 1;
    }
    setBinaryStdout();
    const std::string data = readFile(argv[1]);
    Reader in(data);

    const std::string_view alphabet = in.token();
    Costs c;
    c.A = static_cast<int>(alphabet.size());
    unsigned char code[256] = {};
    for (int i = 0; i < c.A; ++i) code[static_cast<unsigned char>(alphabet[i])] = static_cast<unsigned char>(i);

    c.ins.resize(c.A);
    c.del.resize(c.A);
    c.sub.resize(static_cast<std::size_t>(c.A) * c.A);
    for (auto& x : c.ins) x = in.number();
    for (auto& x : c.del) x = in.number();
    for (auto& x : c.sub) x = in.number();

    const i64 pairs = in.number();

    std::vector<unsigned char> s, t;
    std::vector<i64> tIns, row;
    std::string out;
    i64 total = 0;

    for (i64 p = 0; p < pairs; ++p) {
        const std::string_view ss = in.token();
        const std::string_view ts = in.token();
        const int n = static_cast<int>(ss.size());
        const int m = static_cast<int>(ts.size());

        s.resize(n);
        t.resize(m);
        tIns.resize(m);
        row.resize(m + 1);
        for (int i = 0; i < n; ++i) s[i] = code[static_cast<unsigned char>(ss[i])];
        for (int j = 0; j < m; ++j) {
            t[j] = code[static_cast<unsigned char>(ts[j])];
            tIns[j] = c.ins[t[j]];
        }

        const i64 cost = alignCost(s.data(), n, t.data(), m, c, row.data(), tIns.data());
        total += cost;
        out += std::to_string(cost);
        out += '\n';
    }

    out += "total ";
    out += std::to_string(total);
    out += '\n';
    std::fwrite(out.data(), 1, out.size(), stdout);
    return 0;
}
