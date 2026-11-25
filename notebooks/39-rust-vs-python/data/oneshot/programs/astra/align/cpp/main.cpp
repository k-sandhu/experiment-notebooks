#include <cstdio>
#include <cstdint>
#include <limits>
#include <string>
#include <utility>
#include <vector>

class Input {
    FILE* file_;
    char buffer_[65536];
    std::size_t position_ = 0;
    std::size_t available_ = 0;

    int get() {
        if (position_ == available_) {
            available_ = std::fread(buffer_, 1, sizeof(buffer_), file_);
            position_ = 0;
            if (available_ == 0) return EOF;
        }
        return static_cast<unsigned char>(buffer_[position_++]);
    }

public:
    explicit Input(FILE* file) : file_(file) {}

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

    int integer() {
        int c;
        do {
            c = get();
        } while (c != EOF && c <= ' ');

        int value = 0;
        while (c >= '0' && c <= '9') {
            value = value * 10 + c - '0';
            c = get();
        }
        return value;
    }
};

struct Costs {
    int insertion[26]{};
    int deletion[26]{};
    int substitution[26][26]{};
};

template<class Value>
std::int64_t alignment(const std::string& source,
                       const std::string& target,
                       const Costs& costs) {
    const std::size_t m = target.size();
    std::vector<Value> dp(m + 1);
    std::vector<int> insertion(m);

    for (std::size_t j = 0; j < m; ++j) {
        insertion[j] =
            costs.insertion[static_cast<unsigned char>(target[j])];
        dp[j + 1] = dp[j] + insertion[j];
    }

    for (unsigned char letter : source) {
        const int deletion = costs.deletion[letter];
        const int* substitutions = costs.substitution[letter];

        Value diagonal = dp[0];
        Value left = diagonal + deletion;
        dp[0] = left;

        for (std::size_t j = 0; j < m; ++j) {
            const Value above = dp[j + 1];
            Value best = diagonal +
                substitutions[static_cast<unsigned char>(target[j])];

            const Value deleteCost = above + deletion;
            if (deleteCost < best) best = deleteCost;

            const Value insertCost = left + insertion[j];
            if (insertCost < best) best = insertCost;

            dp[j + 1] = best;
            diagonal = above;
            left = best;
        }
    }

    return static_cast<std::int64_t>(dp[m]);
}

int main(int argc, char* argv[]) {
    if (argc < 2) return 0;

    FILE* file = nullptr;
    if (fopen_s(&file, argv[1], "rb") != 0 || file == nullptr) return 0;

    Input input(file);
    std::string alphabet;
    input.word(alphabet);

    const int alphabetSize = static_cast<int>(alphabet.size());
    unsigned char index[256]{};
    for (int i = 0; i < alphabetSize; ++i) {
        index[static_cast<unsigned char>(alphabet[i])] =
            static_cast<unsigned char>(i);
    }

    Costs forward, reverse;
    for (int i = 0; i < alphabetSize; ++i) {
        forward.insertion[i] = input.integer();
        reverse.deletion[i] = forward.insertion[i];
    }
    for (int i = 0; i < alphabetSize; ++i) {
        forward.deletion[i] = input.integer();
        reverse.insertion[i] = forward.deletion[i];
    }
    for (int i = 0; i < alphabetSize; ++i) {
        for (int j = 0; j < alphabetSize; ++j) {
            const int cost = input.integer();
            forward.substitution[i][j] = cost;
            reverse.substitution[j][i] = cost;
        }
    }

    const int pairs = input.integer();
    std::int64_t total = 0;
    std::string output;
    std::string source, target;

    constexpr std::size_t intLengthLimit =
        static_cast<std::size_t>(
            (std::numeric_limits<int>::max() - 1000) / 1000);

    for (int pair = 0; pair < pairs; ++pair) {
        input.word(source);
        input.word(target);

        std::int64_t answer = 0;
        if (source != target) {
            for (char& c : source) {
                c = static_cast<char>(index[static_cast<unsigned char>(c)]);
            }
            for (char& c : target) {
                c = static_cast<char>(index[static_cast<unsigned char>(c)]);
            }

            const Costs* costs = &forward;
            if (target.size() > source.size()) {
                source.swap(target);
                costs = &reverse;
            }

            if (source.size() <= intLengthLimit &&
                target.size() <= intLengthLimit - source.size()) {
                answer = alignment<int>(source, target, *costs);
            } else {
                answer = alignment<std::int64_t>(source, target, *costs);
            }
        }

        total += answer;
        output += std::to_string(answer);
        output.push_back('\n');
    }

    std::fclose(file);

    output += "total ";
    output += std::to_string(total);
    output.push_back('\n');
    std::fwrite(output.data(), 1, output.size(), stdout);
    return 0;
}
