#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdio>
#include <fstream>
#include <string>
#include <string_view>
#include <vector>

struct Input {
    std::vector<char> data;
    size_t pos = 0;
    explicit Input(const char* path) {
        std::ifstream file(path, std::ios::binary | std::ios::ate);
        data.resize(static_cast<size_t>(file.tellg()));
        file.seekg(0);
        file.read(data.data(), static_cast<std::streamsize>(data.size()));
    }
    std::string_view token() {
        while (pos < data.size() && data[pos] <= ' ') ++pos;
        const size_t start = pos;
        while (pos < data.size() && data[pos] > ' ') ++pos;
        return {data.data() + start, pos - start};
    }
    int number() {
        const auto value = token();
        int result = 0;
        for (char c : value) result = result * 10 + c - '0';
        return result;
    }
};

struct Alignment {
    int ins[2][26]{}, del[2][26]{}, sub[2][26][26]{};
    std::vector<int> insertion, row32;
    std::vector<int64_t> row64;
    std::array<std::vector<int>, 26> profile;

    template<class T>
    T evaluate(std::string_view source, size_t width, const int* deletion,
               std::vector<T>& storage) {
        storage.resize(width);
        T* row = storage.data();
        const int* insert = insertion.data();
        T prefix = 0;
        for (size_t j = 0; j < width; ++j) row[j] = prefix += insert[j];
        T boundary = 0;
        for (char c : source) {
            const int letter = c - 'A';
            const int d = deletion[letter];
            const int* costs = profile[letter].data();
            T diagonal = boundary;
            T left = boundary += d;
            for (size_t j = 0; j < width; ++j) {
                const T above = row[j];
                left = std::min(std::min(above + d, left + insert[j]),
                                diagonal + costs[j]);
                row[j] = left;
                diagonal = above;
            }
        }
        return row[width - 1];
    }

    int64_t cost(std::string_view s, std::string_view t) {
        if (s == t) return 0;
        const int direction = s.size() < t.size();
        if (direction) std::swap(s, t);
        const size_t width = t.size();
        insertion.resize(width);
        int64_t bound = 0;
        uint32_t used = 0;
        for (char c : s) {
            const int letter = c - 'A';
            bound += del[direction][letter];
            used |= uint32_t{1} << letter;
        }
        for (size_t j = 0; j < width; ++j) {
            insertion[j] = ins[direction][t[j] - 'A'];
            bound += insertion[j];
        }
        if (bound == 0) return 0;
        for (int c = 0; c < 26; ++c) {
            if (!(used & (uint32_t{1} << c))) continue;
            auto& costs = profile[c];
            costs.resize(width);
            for (size_t j = 0; j < width; ++j)
                costs[j] = sub[direction][c][t[j] - 'A'];
        }
        // Each entry is bounded by deleting and inserting all letters.
        // Reserve 1000 for the addition before taking the minimum.
        if (bound <= INT32_MAX - 1000)
            return evaluate(s, width, del[direction], row32);
        return evaluate(s, width, del[direction], row64);
    }
};

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    Input input(argv[1]);
    const auto alphabet = input.token();
    Alignment solver;
    for (char c : alphabet) solver.ins[0][c - 'A'] = input.number();
    for (char c : alphabet) solver.del[0][c - 'A'] = input.number();
    for (char a : alphabet)
        for (char b : alphabet)
            solver.sub[0][a - 'A'][b - 'A'] = input.number();
    for (int a = 0; a < 26; ++a) {
        solver.ins[1][a] = solver.del[0][a];
        solver.del[1][a] = solver.ins[0][a];
        for (int b = 0; b < 26; ++b)
            solver.sub[1][a][b] = solver.sub[0][b][a];
    }
    const int pairs = input.number();
    int64_t total = 0;
    std::string output;
    for (int p = 0; p < pairs; ++p) {
        const auto s = input.token();
        const auto t = input.token();
        const auto result = solver.cost(s, t);
        total += result;
        output += std::to_string(result);
        output += '\n';
    }
    output += "total " + std::to_string(total) + "\n";
    std::fwrite(output.data(), 1, output.size(), stdout);
}
