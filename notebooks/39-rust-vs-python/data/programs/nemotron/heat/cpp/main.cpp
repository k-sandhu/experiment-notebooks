#include <cstdio>
#include <cstdlib>
#include <io.h>
#include <fcntl.h>
#include <vector>

namespace {
char* g_buf = nullptr;
size_t g_pos = 0;
size_t g_size = 0;

int read_int() {
    while (g_pos < g_size && g_buf[g_pos] <= 32) ++g_pos;
    int sign = 1;
    if (g_pos < g_size && g_buf[g_pos] == 45) { // '-'
        sign = -1;
        ++g_pos;
    }
    int v = 0;
    while (g_pos < g_size && g_buf[g_pos] > 32) {
        v = v * 10 + (g_buf[g_pos] - 48);
        ++g_pos;
    }
    return sign * v;
}
} // namespace

struct Cell {
    int self;
    int up;
    int down;
    int left;
    int right;
};

int main(int argc, char** argv) {
    if (argc < 2) {
        return 1;
    }
    FILE* f = std::fopen(argv[1], "rb");
    if (!f) {
        return 1;
    }
    std::fseek(f, 0, SEEK_END);
    long size = std::ftell(f);
    std::fseek(f, 0, SEEK_SET);
    std::vector<char> buf((size_t)size);
    if (std::fread(buf.data(), 1, (size_t)size, f) != (size_t)size) {
        std::fclose(f);
        return 1;
    }
    std::fclose(f);
    g_buf = buf.data();
    g_size = (size_t)size;

    int H = read_int();
    int W = read_int();
    int S = read_int();

    int N = H * W;
    std::vector<unsigned char> grid(N);
    int gi = 0;
    while (gi < N) {
        char b = g_buf[g_pos++];
        if (b > 32) {
            grid[gi++] = (unsigned char)b;
        }
    }

    std::vector<int> cur(N, 0);
    std::vector<int> nxt(N, 0);
    std::vector<Cell> cells;
    for (int r = 0; r < H; ++r) {
        int base = r * W;
        for (int c = 0; c < W; ++c) {
            int i = base + c;
            unsigned char b = grid[i];
            if (b == '.') {
                Cell cell;
                cell.self = i;
                cell.up = (r > 0 && grid[i - W] != '#') ? i - W : i;
                cell.down = (r + 1 < H && grid[i + W] != '#') ? i + W : i;
                cell.left = (c > 0 && grid[i - 1] != '#') ? i - 1 : i;
                cell.right = (c + 1 < W && grid[i + 1] != '#') ? i + 1 : i;
                cells.push_back(cell);
            } else if (b >= '1' && b <= '9') {
                int v = 1000 * (b - '0');
                cur[i] = v;
                nxt[i] = v;
            }
        }
    }

    size_t count = cells.size();
    for (int step = 0; step < S; ++step) {
        for (size_t k = 0; k < count; ++k) {
            const Cell& cell = cells[k];
            int v = cur[cell.self];
            int s = 4 * v + cur[cell.up] + cur[cell.down] +
                    cur[cell.left] + cur[cell.right];
            nxt[cell.self] = s >> 3; // all values non-negative, so >>3 == floor division by 8
        }
        cur.swap(nxt);
    }

    // Keep stdout as pure bytes so '\n' stays '\n' on Windows.
    _setmode(_fileno(stdout), _O_BINARY);

    long long total = 0;
    long long checksum = 0;
    int best_v = -1;
    int best_r = 0;
    int best_c = 0;
    for (size_t k = 0; k < count; ++k) {
        int i = cells[k].self;
        int v = cur[i];
        total += v;
        if (v > best_v) {
            best_v = v;
            best_r = i / W;
            best_c = i % W;
        }
        checksum += (long long)v * (long long)(i + 1);
    }

    std::printf("sum %lld\nmax %d %d %d\nchecksum %lld\n",
                total, best_v, best_r, best_c, checksum);
    return 0;
}
