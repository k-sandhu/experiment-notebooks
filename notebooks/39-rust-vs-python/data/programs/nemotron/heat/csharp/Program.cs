using System;
using System.IO;
using System.Text;

class Program {
    static void Main(string[] args) {
        byte[] data = File.ReadAllBytes(args[0]);
        int n = data.Length;
        int pos = 0;

        int ReadInt() {
            while (pos < n && data[pos] <= 32) {
                pos++;
            }
            int sign = 1;
            if (pos < n && data[pos] == 45) { // '-'
                sign = -1;
                pos++;
            }
            int v = 0;
            while (pos < n && data[pos] > 32) {
                v = v * 10 + (data[pos] - 48);
                pos++;
            }
            return sign * v;
        }

        int H = ReadInt();
        int W = ReadInt();
        int S = ReadInt();

        int N = H * W;
        byte[] grid = new byte[N];
        int gi = 0;
        while (gi < N) {
            byte b = data[pos++];
            if (b > 32) {
                grid[gi++] = b;
            }
        }

        int[] cur = new int[N];
        int[] nxt = new int[N];
        int[] self = new int[N];
        int[] up = new int[N];
        int[] down = new int[N];
        int[] left = new int[N];
        int[] right = new int[N];
        int count = 0;

        for (int r = 0; r < H; r++) {
            int baseIndex = r * W;
            for (int c = 0; c < W; c++) {
                int i = baseIndex + c;
                int b = grid[i];
                if (b == 46) { // '.'
                    self[count] = i;
                    up[count] = (r > 0 && grid[i - W] != 35) ? i - W : i;
                    down[count] = (r + 1 < H && grid[i + W] != 35) ? i + W : i;
                    left[count] = (c > 0 && grid[i - 1] != 35) ? i - 1 : i;
                    right[count] = (c + 1 < W && grid[i + 1] != 35) ? i + 1 : i;
                    count++;
                } else if (b >= 49 && b <= 57) { // '1'..'9'
                    int v = 1000 * (b - 48);
                    cur[i] = v;
                    nxt[i] = v;
                }
            }
        }

        for (int step = 0; step < S; step++) {
            for (int k = 0; k < count; k++) {
                int i = self[k];
                int v = cur[i];
                int s = 4 * v + cur[up[k]] + cur[down[k]] + cur[left[k]] + cur[right[k]];
                nxt[i] = s >> 3; // all values non-negative
            }
            int[] swp = cur;
            cur = nxt;
            nxt = swp;
        }

        long total = 0;
        long checksum = 0;
        int bestV = -1;
        int bestR = 0;
        int bestC = 0;
        for (int k = 0; k < count; k++) {
            int i = self[k];
            int v = cur[i];
            total += v;
            if (v > bestV) {
                bestV = v;
                bestR = i / W;
                bestC = i % W;
            }
            checksum += (long)v * (i + 1);
        }

        StringBuilder sb = new StringBuilder();
        sb.Append("sum ").Append(total).Append('\n');
        sb.Append("max ").Append(bestV).Append(' ').Append(bestR).Append(' ').Append(bestC).Append('\n');
        sb.Append("checksum ").Append(checksum).Append('\n');
        Console.Write(sb);
    }
}
