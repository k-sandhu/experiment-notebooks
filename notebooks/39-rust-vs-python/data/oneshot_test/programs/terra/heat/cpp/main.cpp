#include <fstream>
#include <iostream>
#include <string>
#include <vector>
#include <cstdint>
#include <utility>

struct Cell {
    int index;
    int up;
    int down;
    int left;
    int right;
};

int main(int argc, char* argv[]) {
    if (argc < 2) return 1;

    std::ifstream input(argv[1]);
    if (!input) return 1;

    int h, w;
    long long steps;
    input >> h >> w >> steps;

    const int stride = w + 2;
    const int size = (h + 2) * stride;

    std::vector<char> grid(size, '#');
    std::vector<int> current(size, 0);
    std::vector<int> next(size, 0);

    std::string row;
    for (int r = 0; r < h; ++r) {
        input >> row;
        for (int c = 0; c < w; ++c) {
            const int i = (r + 1) * stride + c + 1;
            const char ch = row[c];
            grid[i] = ch;
            if (ch >= '1' && ch <= '9') {
                current[i] = next[i] = (ch - '0') * 1000;
            }
        }
    }

    std::vector<Cell> cells;
    cells.reserve(static_cast<std::size_t>(h) * w);

    for (int r = 0; r < h; ++r) {
        for (int c = 0; c < w; ++c) {
            const int i = (r + 1) * stride + c + 1;
            if (grid[i] != '.') continue;

            cells.push_back({
                i,
                grid[i - stride] == '#' ? i : i - stride,
                grid[i + stride] == '#' ? i : i + stride,
                grid[i - 1] == '#' ? i : i - 1,
                grid[i + 1] == '#' ? i : i + 1
            });
        }
    }

    for (long long step = 0; step < steps; ++step) {
        bool changed = false;
        const int* src = current.data();
        int* dst = next.data();

        for (const Cell& cell : cells) {
            const int old = src[cell.index];
            const int value = (4 * old + src[cell.up] + src[cell.down]
                             + src[cell.left] + src[cell.right]) / 8;
            dst[cell.index] = value;
            changed |= value != old;
        }

        current.swap(next);
        if (!changed) break;
    }

    std::int64_t sum = 0;
    std::int64_t checksum = 0;
    int maximum = -1;
    int maxRow = 0;
    int maxCol = 0;

    for (const Cell& cell : cells) {
        const int value = current[cell.index];
        const int r = cell.index / stride - 1;
        const int c = cell.index % stride - 1;

        sum += value;
        checksum += static_cast<std::int64_t>(value)
                  * (static_cast<std::int64_t>(r) * w + c + 1);

        if (value > maximum) {
            maximum = value;
            maxRow = r;
            maxCol = c;
        }
    }

    std::cout << "sum " << sum << '\n'
              << "max " << maximum << ' ' << maxRow << ' ' << maxCol << '\n'
              << "checksum " << checksum << '\n';

    return 0;
}
