#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <fstream>
#include <limits>
#include <string>
#include <vector>

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    std::ifstream file(argv[1], std::ios::binary | std::ios::ate);
    if (!file) return 1;
    std::string input(static_cast<std::size_t>(file.tellg()), '\0');
    file.seekg(0);
    file.read(input.data(), static_cast<std::streamsize>(input.size()));
    std::size_t pos = 0;
    auto number = [&]() {
        while (input[pos] <= ' ') ++pos;
        std::uint64_t n = 0;
        while (pos < input.size() && input[pos] >= '0' && input[pos] <= '9') {
            const auto digit = static_cast<unsigned>(input[pos++] - '0');
            constexpr auto limit = std::numeric_limits<std::uint64_t>::max();
            n = n > (limit - digit) / 10 ? limit : n * 10 + digit;
        }
        return n;
    };
    const int h = static_cast<int>(number());
    const int w = static_cast<int>(number());
    const std::uint64_t steps = number();
    const int stride = w + 2;
    const int size = (h + 2) * stride;
    const int begin = stride, end = (h + 1) * stride;
    std::vector<char> grid(size, '#');
    std::vector<int> a(size), b(size), weight(size), indices;
    int open_count = 0;
    bool has_source = false;
    for (int r = 1; r <= h; ++r) {
        while (pos < input.size() && input[pos] <= ' ') ++pos;
        for (int c = 1; c <= w; ++c) {
            const int i = r * stride + c;
            const char ch = input[pos++];
            grid[i] = ch;
            if (ch == '.') ++open_count;
            if (ch >= '1' && ch <= '9') {
                a[i] = b[i] = (ch - '0') * 1000;
                has_source = true;
            }
        }
    }
    const bool sparse = open_count < (end - begin) / 4;
    indices.reserve(sparse ? open_count : end - begin - open_count);
    for (int i = begin; i < end; ++i) {
        if (grid[i] == '.') {
            // A blocked neighbour contributes the cell's own previous value.
            weight[i] = 4 + (grid[i - stride] == '#') + (grid[i + stride] == '#')
                          + (grid[i - 1] == '#') + (grid[i + 1] == '#');
            if (sparse) indices.push_back(i);
        } else if (!sparse) {
            indices.push_back(i);
        }
    }
    if (has_source) {
        for (std::uint64_t step = 0; step < steps; ++step) {
            const int* old = a.data();
            int* next = b.data();
            const int* weights = weight.data();
            if (sparse) {
                for (int i : indices)
                    next[i] = (weights[i] * old[i] + old[i - stride] + old[i + stride]
                               + old[i - 1] + old[i + 1]) >> 3;
            } else {
                // The buffers do not overlap, so all iterations are independent.
                #pragma loop(ivdep)
                for (int i = begin; i < end; ++i) {
                    next[i] = (weights[i] * old[i] + old[i - stride] + old[i + stride]
                               + old[i - 1] + old[i + 1]) >> 3;
                }
                for (int i : indices) next[i] = old[i];
            }
            const bool stable = (step & 63) == 63 &&
                std::equal(a.begin() + begin, a.begin() + end, b.begin() + begin);
            a.swap(b);
            if (stable) break;
        }
    }
    std::int64_t total = 0, checksum = 0;
    int best = -1, best_r = 0, best_c = 0;
    for (int r = 0; r < h; ++r) {
        for (int c = 0; c < w; ++c) {
            const int i = (r + 1) * stride + c + 1;
            if (grid[i] != '.') continue;
            const int value = a[i];
            total += value;
            checksum += static_cast<std::int64_t>(value) *
                        (static_cast<std::int64_t>(r) * w + c + 1);
            if (value > best) { best = value; best_r = r; best_c = c; }
        }
    }
    std::printf("sum %lld\nmax %d %d %d\nchecksum %lld\n",
        static_cast<long long>(total), best, best_r, best_c, static_cast<long long>(checksum));
}
