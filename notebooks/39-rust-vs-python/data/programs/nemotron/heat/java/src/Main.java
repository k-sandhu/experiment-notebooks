import java.nio.file.Files;
import java.nio.file.Path;

public class Main {
    private static byte[] data;
    private static int n;
    private static int pos;

    private static int readInt() {
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

    public static void main(String[] args) throws Exception {
        data = Files.readAllBytes(Path.of(args[0]));
        n = data.length;
        pos = 0;

        int H = readInt();
        int W = readInt();
        int S = readInt();

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
            int base = r * W;
            for (int c = 0; c < W; c++) {
                int i = base + c;
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
            int[] tmp = cur;
            cur = nxt;
            nxt = tmp;
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
            checksum += (long) v * (i + 1);
        }

        StringBuilder out = new StringBuilder();
        out.append("sum ").append(total).append('\n');
        out.append("max ").append(bestV).append(' ').append(bestR).append(' ').append(bestC).append('\n');
        out.append("checksum ").append(checksum).append('\n');
        System.out.print(out);
    }
}
