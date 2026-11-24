#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <string>
#include <utility>
#include <vector>

struct Run {
    std::size_t begin;
    std::size_t end;
};

template<unsigned Weight>
static void update(
    const std::uint32_t* __restrict current,
    std::uint32_t* __restrict next,
    std::size_t pitch,
    const std::vector<Run>& runs)
{
    for (const Run& run : runs) {
        const std::size_t end = run.end;
        const std::uint32_t* above = current - pitch + run.begin;
        const std::uint32_t* below = current + pitch + run.begin;
        const std::uint32_t* center = current + run.begin;
        std::uint32_t* destination = next + run.begin;
        const std::size_t length = end - run.begin;

        #pragma loop(ivdep)
        for (std::size_t j = 0; j < length; ++j) {
            destination[j] =
                (Weight * center[j] +
                 above[j] + below[j] +
                 center[static_cast<std::ptrdiff_t>(j) - 1] +
                 center[j + 1]) >> 3;
        }
    }
}

int main(int argc, char** argv)
{
    if (argc != 2)
        return 1;

    std::ifstream input(argv[1], std::ios::binary);
    if (!input)
        return 1;

    std::size_t height, width;
    std::uint64_t steps;
    if (!(input >> height >> width >> steps))
        return 1;

    const std::size_t pitch = width + 2;
    const std::size_t storageSize = (height + 2) * pitch;

    std::vector<char> grid(storageSize, '#');
    std::size_t firstOpen = std::numeric_limits<std::size_t>::max();
    std::size_t sourceCount = 0;
    std::string row;

    for (std::size_t r = 0; r < height; ++r) {
        input >> row;
        const std::size_t base = (r + 1) * pitch + 1;

        for (std::size_t c = 0; c < width; ++c) {
            const char ch = row[c];
            grid[base + c] = ch;
            if (ch == '.') {
                if (firstOpen == std::numeric_limits<std::size_t>::max())
                    firstOpen = r * width + c;
            } else if (ch >= '1' && ch <= '9') {
                ++sourceCount;
            }
        }
    }

    if (steps == 0 || sourceCount == 0) {
        std::cout << "sum 0\nmax 0 "
                  << firstOpen / width << ' ' << firstOpen % width
                  << "\nchecksum 0\n";
        return 0;
    }

    std::vector<std::uint32_t> bufferA(storageSize, 0);
    std::vector<std::uint32_t> bufferB(storageSize, 0);
    std::array<std::vector<Run>, 4> runs;
    bool sourceTouchesOpen = false;

    for (std::size_t r = 1; r <= height; ++r) {
        const std::size_t base = r * pitch;

        for (std::size_t c = 1; c <= width; ++c) {
            const std::size_t p = base + c;
            const char ch = grid[p];

            if (ch >= '1' && ch <= '9') {
                const std::uint32_t value =
                    static_cast<std::uint32_t>(ch - '0') * 1000u;
                bufferA[p] = value;
                bufferB[p] = value;

                sourceTouchesOpen |=
                    grid[p - pitch] == '.' ||
                    grid[p + pitch] == '.' ||
                    grid[p - 1] == '.' ||
                    grid[p + 1] == '.';
            } else if (ch == '.') {
                const unsigned walls =
                    static_cast<unsigned>(grid[p - pitch] == '#') +
                    static_cast<unsigned>(grid[p + pitch] == '#') +
                    static_cast<unsigned>(grid[p - 1] == '#') +
                    static_cast<unsigned>(grid[p + 1] == '#');

                // A completely enclosed open cell stays zero.
                if (walls == 4)
                    continue;

                auto& bucket = runs[walls];
                if (!bucket.empty() && bucket.back().end == p)
                    ++bucket.back().end;
                else
                    bucket.push_back({p, p + 1});
            }
        }
    }

    if (!sourceTouchesOpen) {
        std::cout << "sum 0\nmax 0 "
                  << firstOpen / width << ' ' << firstOpen % width
                  << "\nchecksum 0\n";
        return 0;
    }

    std::uint32_t* current = bufferA.data();
    std::uint32_t* next = bufferB.data();

    for (std::uint64_t step = 0; step < steps; ++step) {
        update<4>(current, next, pitch, runs[0]);
        update<5>(current, next, pitch, runs[1]);
        update<6>(current, next, pitch, runs[2]);
        update<7>(current, next, pitch, runs[3]);
        std::swap(current, next);
    }

    std::uint64_t total = 0;
    std::uint64_t checksum = 0;
    std::uint32_t maximum = 0;
    std::size_t bestIndex = firstOpen;
    std::size_t logicalIndex = 0;

    for (std::size_t r = 1; r <= height; ++r) {
        const std::size_t base = r * pitch;

        for (std::size_t c = 1; c <= width; ++c, ++logicalIndex) {
            const std::size_t p = base + c;
            if (grid[p] != '.')
                continue;

            const std::uint32_t value = current[p];
            total += value;
            checksum += static_cast<std::uint64_t>(value) *
                        (static_cast<std::uint64_t>(logicalIndex) + 1);

            if (value > maximum) {
                maximum = value;
                bestIndex = logicalIndex;
            }
        }
    }

    std::cout << "sum " << total
              << "\nmax " << maximum << ' '
              << bestIndex / width << ' ' << bestIndex % width
              << "\nchecksum " << checksum << '\n';

    return 0;
}
