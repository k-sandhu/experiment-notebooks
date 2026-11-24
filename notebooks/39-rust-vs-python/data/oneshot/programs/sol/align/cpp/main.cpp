#include <algorithm>
#include <charconv>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <limits>
#include <string>
#include <utility>
#include <vector>

class FastReader {
    static constexpr std::size_t BufferSize = 1 << 16;
    FILE* file_;
    char buffer_[BufferSize];
    std::size_t pos_ = 0;
    std::size_t size_ = 0;

    int get() {
        if (pos_ == size_) {
            size_ = std::fread(buffer_, 1, BufferSize, file_);
            pos_ = 0;
            if (size_ == 0) return EOF;
        }
        return static_cast<unsigned char>(buffer_[pos_++]);
    }

public:
    explicit FastReader(FILE* file) : file_(file) {}

    void word(std::string& result) {
        result.clear();
        int c;
        do {
            c = get();
        } while (c != EOF && c <= ' ');

        while (c != EOF && c > ' ') {
            result.push_back(static_cast<char>(c));
            c = get();
        }
    }

    std::size_t number() {
        int c;
        do {
            c = get();
        } while (c != EOF && c <= ' ');

        std::size_t value = 0;
        while (c >= '0' && c <= '9') {
            value = value * 10 + static_cast<unsigned>(c - '0');
            c = get();
        }
        return value;
    }
};

template<class Cost>
static std::uint64_t alignment(
    const std::string& source,
    const std::uint16_t* deletion,
    const std::vector<std::uint16_t>& insertion,
    const std::vector<std::uint16_t>& substitution)
{
    const std::size_t m = insertion.size();
    std::vector<Cost> row(m + 1);
    Cost* const dp = row.data();
    const std::uint16_t* const ins = insertion.data();

    for (std::size_t j = 0; j < m; ++j) {
        dp[j + 1] = dp[j] + ins[j];
    }

    for (unsigned char letter : source) {
        const Cost del = deletion[letter];
        const std::uint16_t* const sub =
            substitution.data() + static_cast<std::size_t>(letter) * m;

        Cost diagonal = dp[0];
        Cost left = diagonal + del;
        dp[0] = left;

        for (std::size_t j = 0; j < m; ++j) {
            const Cost above = dp[j + 1];
            const Cost remove = above + del;
            const Cost replace = diagonal + sub[j];
            const Cost insert = left + ins[j];

            const Cost best = remove < replace ? remove : replace;
            left = best < insert ? best : insert;
            dp[j + 1] = left;
            diagonal = above;
        }
    }

    return static_cast<std::uint64_t>(dp[m]);
}

static void appendNumber(std::string& output, std::uint64_t value) {
    char buffer[32];
    const auto result = std::to_chars(buffer, buffer + sizeof(buffer), value);
    output.append(buffer, static_cast<std::size_t>(result.ptr - buffer));
    output.push_back('\n');
}

int main(int argc, char** argv) {
    if (argc < 2) return 0;

    FILE* file = nullptr;
    if (fopen_s(&file, argv[1], "rb") != 0 || file == nullptr) return 0;

    FastReader reader(file);
    std::string alphabet;
    reader.word(alphabet);
    const std::size_t a = alphabet.size();

    unsigned char index[256] = {};
    for (std::size_t i = 0; i < a; ++i) {
        index[static_cast<unsigned char>(alphabet[i])] =
            static_cast<unsigned char>(i);
    }

    std::uint16_t insertionCosts[26] = {};
    std::uint16_t deletionCosts[26] = {};
    std::uint16_t substitutionCosts[26][26] = {};

    for (std::size_t i = 0; i < a; ++i) {
        insertionCosts[i] = static_cast<std::uint16_t>(reader.number());
    }
    for (std::size_t i = 0; i < a; ++i) {
        deletionCosts[i] = static_cast<std::uint16_t>(reader.number());
    }
    for (std::size_t i = 0; i < a; ++i) {
        for (std::size_t j = 0; j < a; ++j) {
            substitutionCosts[i][j] =
                static_cast<std::uint16_t>(reader.number());
        }
    }

    const std::size_t pairs = reader.number();
    std::string source, target;
    std::string output;
    output.reserve(8192);

    std::vector<std::uint16_t> insertion;
    std::vector<std::uint16_t> substitution;
    std::uint64_t total = 0;

    for (std::size_t p = 0; p < pairs; ++p) {
        reader.word(source);
        reader.word(target);

        if (source == target) {
            appendNumber(output, 0);
            continue;
        }

        const bool transposed = source.size() < target.size();
        if (transposed) std::swap(source, target);

        const std::uint16_t* const insCosts =
            transposed ? deletionCosts : insertionCosts;
        const std::uint16_t* const delCosts =
            transposed ? insertionCosts : deletionCosts;

        std::uint64_t upperBound = 0;

        for (char& c : source) {
            const unsigned char code = index[static_cast<unsigned char>(c)];
            c = static_cast<char>(code);
            upperBound += delCosts[code];
        }

        const std::size_t m = target.size();
        insertion.resize(m);
        for (std::size_t j = 0; j < m; ++j) {
            const unsigned char code =
                index[static_cast<unsigned char>(target[j])];
            target[j] = static_cast<char>(code);
            insertion[j] = insCosts[code];
            upperBound += insertion[j];
        }

        if (upperBound == 0) {
            appendNumber(output, 0);
            continue;
        }

        substitution.resize(a * m);
        for (std::size_t i = 0; i < a; ++i) {
            std::uint16_t* const row = substitution.data() + i * m;
            for (std::size_t j = 0; j < m; ++j) {
                const unsigned char code =
                    static_cast<unsigned char>(target[j]);
                row[j] = transposed
                    ? substitutionCosts[code][i]
                    : substitutionCosts[i][code];
            }
        }

        std::uint64_t cost;
        if (upperBound <=
            static_cast<std::uint64_t>(
                (std::numeric_limits<std::uint32_t>::max)()) - 1000) {
            cost = alignment<std::uint32_t>(
                source, delCosts, insertion, substitution);
        } else {
            cost = alignment<std::uint64_t>(
                source, delCosts, insertion, substitution);
        }

        total += cost;
        appendNumber(output, cost);
    }

    std::fclose(file);

    output += "total ";
    appendNumber(output, total);
    std::fwrite(output.data(), 1, output.size(), stdout);
    return 0;
}
