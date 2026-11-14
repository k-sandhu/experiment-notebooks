import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;

public class Main {
    private static byte[] input;
    private static int pos;

    private static long number() {
        while (input[pos] <= 32) ++pos;
        long value = 0;
        while (pos < input.length && input[pos] >= '0' && input[pos] <= '9') {
            int digit = input[pos++] - '0';
            value = value > (Long.MAX_VALUE - digit) / 10
                  ? Long.MAX_VALUE : value * 10 + digit;
        }
        return value;
    }

    public static void main(String[] args) throws Exception {
        input = Files.readAllBytes(Path.of(args[0]));
        int h = (int) number(), w = (int) number();
        long steps = number();
        int stride = w + 2, size = (h + 2) * stride;
        int begin = stride, end = (h + 1) * stride;
        byte[] grid = new byte[size];
        Arrays.fill(grid, (byte) '#');
        int[] a = new int[size], b = new int[size], weight = new int[size];
        int openCount = 0;
        boolean hasSource = false;
        for (int r = 1; r <= h; ++r) {
            while (pos < input.length && input[pos] <= 32) ++pos;
            for (int c = 1; c <= w; ++c) {
                int i = r * stride + c;
                byte ch = input[pos++];
                grid[i] = ch;
                if (ch == '.') ++openCount;
                if (ch >= '1' && ch <= '9') {
                    a[i] = b[i] = (ch - '0') * 1000;
                    hasSource = true;
                }
            }
        }
        boolean sparse = openCount < (end - begin) / 4;
        int[] indices = new int[sparse ? openCount : end - begin - openCount];
        int count = 0;
        for (int i = begin; i < end; ++i) {
            if (grid[i] == '.') {
                weight[i] = 4 + (grid[i - stride] == '#' ? 1 : 0)
                              + (grid[i + stride] == '#' ? 1 : 0)
                              + (grid[i - 1] == '#' ? 1 : 0)
                              + (grid[i + 1] == '#' ? 1 : 0);
                if (sparse) indices[count++] = i;
            } else if (!sparse) indices[count++] = i;
        }
        input = null;
        if (hasSource) a = simulate(a, b, weight, indices, sparse, stride, begin, end, steps);
        long total = 0, checksum = 0;
        int best = -1, bestR = 0, bestC = 0;
        for (int r = 0; r < h; ++r) {
            for (int c = 0; c < w; ++c) {
                int i = (r + 1) * stride + c + 1;
                if (grid[i] != '.') continue;
                int value = a[i];
                total += value;
                checksum += (long) value * ((long) r * w + c + 1);
                if (value > best) { best = value; bestR = r; bestC = c; }
            }
        }
        System.out.print("sum " + total + "\nmax " + best + " " + bestR + " " + bestC
                         + "\nchecksum " + checksum + "\n");
    }

    private static int[] simulate(int[] a, int[] b, int[] weight, int[] indices,
                                   boolean sparse, int stride, int begin, int end, long steps) {
        for (long step = 0; step < steps; ++step) {
            if (sparse) {
                for (int i : indices)
                    b[i] = (weight[i] * a[i] + a[i - stride] + a[i + stride]
                            + a[i - 1] + a[i + 1]) >>> 3;
            } else {
                for (int i = begin; i < end; ++i)
                    b[i] = (weight[i] * a[i] + a[i - stride] + a[i + stride]
                            + a[i - 1] + a[i + 1]) >>> 3;
                for (int i : indices) b[i] = a[i];
            }
            boolean stable = (step & 63) == 63 && Arrays.equals(a, b);
            int[] temp = a; a = b; b = temp;
            if (stable) break;
        }
        return a;
    }
}
