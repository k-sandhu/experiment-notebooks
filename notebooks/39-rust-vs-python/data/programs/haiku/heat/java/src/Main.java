import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

// Heat on a grid (see SPEC.md).
//
// The grid is stored padded with a one-cell border of zeros, row stride W + 2, so every
// neighbour lookup is a plain offset. Walls and border cells always hold 0, so a wall
// neighbour contributes 0 and the "use own old value" rule becomes (8 - valid) * old.
// A flat, branch-free loop over all rows then updates the grid; C2 vectorises it.
public class Main {

    // One simulation step over the flat index range [begin, end).
    // mask is -1 for open cells and 0 otherwise; fixed holds the constant value of sources.
    static void step(int[] cur, int[] nxt, int[] mult, int[] mask, int[] fixed, int begin, int end,
                     int stride) {
        for (int i = begin; i < end; i++) {
            int sum = mult[i] * cur[i] + cur[i - 1] + cur[i + 1] + cur[i - stride] + cur[i + stride];
            nxt[i] = ((sum >> 3) & mask[i]) | fixed[i];
        }
    }

    static boolean isCell(byte ch) {
        return ch == '.' || ch == '#' || (ch >= '1' && ch <= '9');
    }

    public static void main(String[] args) throws IOException {
        byte[] buf = Files.readAllBytes(Path.of(args[0]));
        int p = 0;

        long[] header = new long[3];
        for (int k = 0; k < 3; k++) {
            while (buf[p] < '0' || buf[p] > '9') p++;
            long v = 0;
            while (p < buf.length && buf[p] >= '0' && buf[p] <= '9') v = v * 10 + (buf[p++] - '0');
            header[k] = v;
        }
        final int H = (int) header[0];
        final int W = (int) header[1];
        final long S = header[2];

        final int P = W + 2;
        final int N = (H + 2) * P;
        byte[] kind = new byte[N];  // 0 = wall or border, 1 = open, 2 = source
        int[] mult = new int[N];
        int[] mask = new int[N];
        int[] fixed = new int[N];

        for (int r = 1; r <= H; r++) {
            for (int c = 1; c <= W; c++) {
                while (p < buf.length && !isCell(buf[p])) p++;
                if (p >= buf.length) break;
                byte ch = buf[p++];
                int i = r * P + c;
                if (ch == '.') {
                    kind[i] = 1;
                } else if (ch != '#') {
                    kind[i] = 2;
                    fixed[i] = 1000 * (ch - '0');
                }
            }
        }

        for (int r = 1; r <= H; r++) {
            for (int c = 1; c <= W; c++) {
                int i = r * P + c;
                if (kind[i] == 1) {
                    int valid = (kind[i - 1] != 0 ? 1 : 0) + (kind[i + 1] != 0 ? 1 : 0)
                            + (kind[i - P] != 0 ? 1 : 0) + (kind[i + P] != 0 ? 1 : 0);
                    mult[i] = 8 - valid;
                    mask[i] = -1;
                }
            }
        }

        int[] cur = fixed.clone();  // sources start at their fixed value
        int[] nxt = fixed.clone();
        final int rowsBegin = P;
        final int rowsEnd = (H + 1) * P;
        for (long s = 0; s < S; s++) {
            step(cur, nxt, mult, mask, fixed, rowsBegin, rowsEnd, P);
            int[] t = cur;
            cur = nxt;
            nxt = t;
        }

        long total = 0, checksum = 0;
        long bestV = -1;
        int bestR = -1, bestC = -1;
        for (int r = 0; r < H; r++) {
            for (int c = 0; c < W; c++) {
                int i = (r + 1) * P + c + 1;
                if (kind[i] != 1) continue;
                long v = cur[i];
                total += v;
                if (v > bestV) {
                    bestV = v;
                    bestR = r;
                    bestC = c;
                }
                checksum += v * ((long) r * W + c + 1);
            }
        }

        System.out.print("sum " + total + "\nmax " + bestV + " " + bestR + " " + bestC
                + "\nchecksum " + checksum + "\n");
        System.out.flush();
    }
}
