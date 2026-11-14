#include <cstdint>
#include <fstream>
#include <iostream>
#include <string>
#include <utility>
#include <vector>

struct Span {
    std::size_t begin;
    std::size_t end;
};

static void advance(
    const std::uint32_t* __restrict current,
    std::uint32_t* __restrict next,
    const std::uint32_t* __restrict weight,
    std::size_t stride,
    const std::vector<Span>& spans,
    const std::vector<std::size_t>& scattered)
{
    for (const Span& span : spans) {
        for (std::size_t i = span.begin; i < span.end; ++i) {
            next[i] = (
                weight[i] * current[i] +
                current[i - stride] +
                current[i + stride] +
                current[i - 1] +
                current[i + 1]
            ) >> 3;
        }
    }

    for (std::size_t i : scattered) {
        next[i] = (
            weight[i] * current[i] +
            current[i - stride] +
            current[i + stride] +
            current[i - 1] +
            current[i + 1]
        ) >> 3;
    }
}

int main(int argc, char* argv[])
{
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
    const std::size_t count = (height + 2) * stride;

    std::vector<char> grid(count, '#');
    std::vector<std::uint32_t> first(count, 0);
    std::vector<std::uint32_t> second(count, 0);
    std::vector<std::uint32_t> weight(count, 0);

    bool hasSource = false;
    std::string row;

    for (std::size_t r = 0; r < height; ++r) {
        input >> row;
        const std::size_t base = (r + 1) * stride + 1;

        for (std::size_t c = 0; c < width; ++c) {
            const std::size_t i = base + c;
            const char ch = row[c];
            grid[i] = ch;

            if (ch >= '1' && ch <= '9') {
                const std::uint32_t value =
                    static_cast<std::uint32_t>(ch - '0') * 1000;
                first[i] = value;
                second[i] = value;
                hasSource = true;
            }
        }
    }

    std::vector<Span> spans;
    std::vector<std::size_t> scattered;

    if (hasSource && steps != 0) {
        for (std::size_t r = 0; r < height; ++r) {
            const std::size_t base = (r + 1) * stride + 1;
            std::size_t c = 0;

            while (c < width) {
                if (grid[base + c] != '.') {
                    ++c;
                    continue;
                }

                const std::size_t begin = base + c;

                do {
                    const std::size_t i = base + c;
                    weight[i] = 4u
                        + static_cast<unsigned>(grid[i - stride] == '#')
                        + static_cast<unsigned>(grid[i + stride] == '#')
                        + static_cast<unsigned>(grid[i - 1] == '#')
                        + static_cast<unsigned>(grid[i + 1] == '#');
                    ++c;
                } while (c < width && grid[base + c] == '.');

                const std::size_t end = base + c;
                if (end - begin >= 16) {
                    spans.push_back({begin, end});
                } else {
                    for (std::size_t i = begin; i < end; ++i) {
                        scattered.push_back(i);
                    }
                }
            }
        }
    }

    std::uint32_t* current = first.data();
    std::uint32_t* next = second.data();

    if (hasSource) {
        for (std::uint64_t step = 0; step < steps; ++step) {
            advance(current, next, weight.data(), stride, spans, scattered);
            std::swap(current, next);
        }
    }

    std::int64_t total = 0;
    std::int64_t checksum = 0;
    std::int32_t maximum = -1;
    std::size_t bestRow = 0;
    std::size_t bestColumn = 0;

    for (std::size_t r = 0; r < height; ++r) {
        const std::size_t base = (r + 1) * stride + 1;

        for (std::size_t c = 0; c < width; ++c) {
            const std::size_t i = base + c;
            if (grid[i] != '.') {
                continue;
            }

            const std::int32_t value =
                static_cast<std::int32_t>(current[i]);

            total += value;
            checksum += static_cast<std::int64_t>(value)
                * static_cast<std::int64_t>(r * width + c + 1);

            if (value > maximum) {
                maximum = value;
                bestRow = r;
                bestColumn = c;
            }
        }
    }

    std::cout << "sum " << total << '\n'
              << "max " << maximum << ' ' << bestRow << ' '
              << bestColumn << '\n'
              << "checksum " << checksum << '\n';

    return 0;
}
