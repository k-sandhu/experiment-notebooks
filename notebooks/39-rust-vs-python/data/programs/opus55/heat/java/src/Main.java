// Heat on a grid: exact integer diffusion with walls and fixed sources.
//
// Values never exceed 9000 (each new value is a floor-average of values <= the largest source). With
// S = sum of the four neighbour terms (wall or outside neighbours replaced by the cell's own value),
// floor((4*o + S) / 8) == (o + (S >> 2)) >> 1 and S <= 36000, so every intermediate fits in 16 bits and
// one long holds four cells (SWAR). Walls hold 0, so S = up+down+left+right + w*o with w the number of
// wall/outside neighbours; w*o is built from three masked shifts of o using the bits of w.
//
// Layout: each row is cpr words of four 16-bit lanes plus a zero word on each side; rows are padded
// above and below. Left/right neighbours come from shifting the word and its neighbour words.
//
// The iteration is monotone non-decreasing, so a row whose neighbourhood of rows did not change in the
// previous step cannot change; such rows are skipped, and a step with no change ends the run.

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

public class Main {
    private static final long LOW14 = 0x3FFF3FFF3FFF3FFFL;
    private static final int OPEN = 0, SOURCE = 1, WALL = 2;

    public static void main(String[] args) throws IOException {
        byte[] data = Files.readAllBytes(Path.of(args[0]));
        int[] pos = {0};
        int h = (int) readInt(data, pos);
        int w = (int) readInt(data, pos);
        long steps = readInt(data, pos);

        // Cell grid with a one-cell wall border, used only for setup.
        int cs = w + 2;
        byte[] type = new byte[(h + 2) * cs];
        int[] fixed = new int[(h + 2) * cs];
        java.util.Arrays.fill(type, (byte) WALL);
        int p = pos[0];
        for (int r = 0; r < h; r++) {
            while (data[p] == '\r' || data[p] == '\n' || data[p] == ' ' || data[p] == '\t') p++;
            int base = (r + 1) * cs + 1;
            for (int c = 0; c < w; c++) {
                byte ch = data[p + c];
                if (ch == '#') continue;
                if (ch >= '1' && ch <= '9') {
                    type[base + c] = SOURCE;
                    fixed[base + c] = 1000 * (ch - '0');
                } else {
                    type[base + c] = OPEN;
                }
            }
            p += w;
        }

        int cpr = (w + 3) / 4;   // words per row
        int rs = cpr + 2;        // word stride per row (one zero word each side)
        long[] a = new long[(h + 2) * rs];
        long[] meta = new long[(h + 2) * cpr * 5]; // per word: b0, b1, b2, open, fix
        for (int r = 0; r < h; r++) {
            for (int c = 0; c < w; c++) {
                int ci = (r + 1) * cs + c + 1;
                int word = (r + 1) * rs + 1 + (c >> 2);
                int m = ((r + 1) * cpr + (c >> 2)) * 5;
                int shift = (c & 3) * 16;
                if (type[ci] == SOURCE) {
                    a[word] |= (long) fixed[ci] << shift;
                    meta[m + 4] |= (long) fixed[ci] << shift;
                } else if (type[ci] == OPEN) {
                    int walls = (type[ci - 1] == WALL ? 1 : 0) + (type[ci + 1] == WALL ? 1 : 0)
                            + (type[ci - cs] == WALL ? 1 : 0) + (type[ci + cs] == WALL ? 1 : 0);
                    for (int bit = 0; bit < 3; bit++) {
                        if ((walls >> bit & 1) != 0) meta[m + bit] |= 0xFFFFL << shift;
                    }
                    meta[m + 3] |= 0x7FFFL << shift;
                }
            }
        }
        long[] b = a.clone();

        long[] cur = simulate(a, b, meta, h, cpr, rs, steps);

        long sum = 0, checksum = 0;
        int best = -1, bestR = 0, bestC = 0;
        for (int r = 0; r < h; r++) {
            long idx0 = (long) r * w + 1;
            for (int c = 0; c < w; c++) {
                if (type[(r + 1) * cs + c + 1] != OPEN) continue;
                int v = (int) (cur[(r + 1) * rs + 1 + (c >> 2)] >>> ((c & 3) * 16)) & 0xFFFF;
                sum += v;
                checksum += v * (idx0 + c);
                if (v > best) { best = v; bestR = r; bestC = c; }
            }
        }
        System.out.print("sum " + sum + "\nmax " + best + " " + bestR + " " + bestC + "\nchecksum " + checksum + "\n");
        System.out.flush();
    }

    private static long[] simulate(long[] a, long[] b, long[] meta, int h, int cpr, int rs, long steps) {
        boolean[] changed = new boolean[h + 2];
        boolean[] nextChanged = new boolean[h + 2];
        for (int r = 1; r <= h; r++) changed[r] = true;
        long[] cur = a, nxt = b;
        for (long step = 0; step < steps; step++) {
            boolean any = false;
            for (int r = 1; r <= h; r++) {
                if (!(changed[r - 1] | changed[r] | changed[r + 1])) {
                    nextChanged[r] = false;
                    continue;
                }
                boolean ch = row(cur, nxt, meta, r * rs + 1, r * cpr * 5, cpr, rs);
                nextChanged[r] = ch;
                any |= ch;
            }
            // Skipped rows hold equal values in both buffers, so swapping is safe.
            long[] t = cur; cur = nxt; nxt = t;
            boolean[] tc = changed; changed = nextChanged; nextChanged = tc;
            if (!any) break;
        }
        return cur;
    }

    // Computes one row of cpr words starting at word index base; returns true if any value changed.
    private static boolean row(long[] src, long[] dst, long[] meta, int base, int mbase, int cpr, int rs) {
        long diff = 0;
        long prev = src[base - 1];
        long o = src[base];
        for (int j = 0, m = mbase; j < cpr; j++, m += 5) {
            int i = base + j;
            long next = src[i + 1];
            long left = (o << 16) | (prev >>> 48);
            long right = (o >>> 16) | (next << 48);
            long s = src[i - rs] + src[i + rs] + left + right
                    + (o & meta[m]) + ((o << 1) & meta[m + 1]) + ((o << 2) & meta[m + 2]);
            long v = (((o + ((s >>> 2) & LOW14)) >>> 1) & meta[m + 3]) | meta[m + 4];
            dst[i] = v;
            diff |= v ^ o;
            prev = o;
            o = next;
        }
        return diff != 0;
    }

    private static long readInt(byte[] data, int[] pos) {
        int p = pos[0];
        while (p < data.length && (data[p] < '0' || data[p] > '9')) p++;
        long v = 0;
        while (p < data.length && data[p] >= '0' && data[p] <= '9') v = v * 10 + (data[p++] - '0');
        pos[0] = p;
        return v;
    }
}
