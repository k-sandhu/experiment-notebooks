#include <cstdint>
#include <fstream>
#include <iostream>
#include <string>
#include <utility>
#include <vector>

struct Run {
    std::size_t begin;
    std::size_t end;
    std::size_t logicalBegin;
};

static void advance(
    const std::uint32_t* __restrict current,
    std::uint32_t* __restrict next,
    const std::uint32_t* __restrict coefficient,
    std::size_t stride,
    const std::vector<Run>& runs)
{
    for (const Run& run : runs) {
        for (std::size_t i = run.begin; i < run.end; ++i) {
            next[i] = (
                coefficient[i] * current[i] +
                current[i - stride] +
                current[i + stride] +
                current[i - 1] +
                current[i + 1]
            ) >> 3;
        }
    }
}

int main(int argc, char* argv[])
{
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);

    if (argc != 2) {
        return 0;
    }

    std::ifstream input(argv[1], std::ios::binary);
    std::size_t height, width;
    std::uint64_t steps;

    if (!(input >> height >> width >> steps)) {
        return 0;
    }

    const std::size_t stride = width + 2;
    const std::size_t total = (height + 2) * stride;

    std::vector<char> grid(total, '#');
    std::vector<std::uint32_t> first(total, 0);
    std::vector<std::uint32_t> second(total, 0);
    std::vector<std::uint32_t> coefficient(total, 0);
    std::vector<Run> runs;

    bool hasSource = false;
    std::string row;

    for (std::size_t r = 0; r < height; ++r) {
        input >> row;
        const std::size_t base = (r + 1) * stride + 1;

        for (std::size_t c = 0; c < width; ++c) {
            const char ch = row[c];
            const std::size_t i = base + c;
            grid[i] = ch;

            if (ch >= '1' && ch <= '9') {
                const std::uint32_t value =
                    1000u * static_cast<std::uint32_t>(ch - '0');
                first[i] = value;
                second[i] = value;
                hasSource = true;
            }
        }

        std::size_t c = 0;
        while (c < width) {
            if (row[c] != '.') {
                ++c;
                continue;
            }

            const std::size_t start = c;
            do {
                ++c;
            } while (c < width && row[c] == '.');

            runs.push_back({base + start, base + c, r * width + start + 1});
        }
    }

    for (const Run& run : runs) {
        for (std::size_t i = run.begin; i < run.end; ++i) {
            coefficient[i] =
                4u +
                static_cast<unsigned>(grid[i - stride] == '#') +
                static_cast<unsigned>(grid[i + stride] == '#') +
                static_cast<unsigned>(grid[i - 1] == '#') +
                static_cast<unsigned>(grid[i + 1] == '#');
        }
    }

    std::uint32_t* current = first.data();
    std::uint32_t* next = second.data();

    if (hasSource) {
        for (std::uint64_t s = 0; s < steps; ++s) {
            advance(current, next, coefficient.data(), stride, runs);
            std::swap(current, next);
        }
    }

    std::int64_t sum = 0;
    std::int64_t checksum = 0;
    std::uint32_t maximum = 0;
    std::size_t best = runs.front().logicalBegin;

    for (const Run& run : runs) {
        std::size_t logical = run.logicalBegin;
        for (std::size_t i = run.begin; i < run.end; ++i, ++logical) {
            const std::uint32_t value = current[i];
            sum += value;
            checksum += static_cast<std::int64_t>(value) *
                        static_cast<std::int64_t>(logical);

            if (value > maximum) {
                maximum = value;
                best = logical;
            }
        }
    }

    const std::size_t bestRow = (best - 1) / width;
    const std::size_t bestColumn = (best - 1) % width;

    std::cout << "sum " << sum << '\n'
              << "max " << maximum << ' ' << bestRow << ' ' << bestColumn << '\n'
              << "checksum " << checksum << '\n';

    return 0;
}
