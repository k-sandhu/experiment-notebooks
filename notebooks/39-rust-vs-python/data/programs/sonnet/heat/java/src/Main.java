import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.Arrays;

public class Main {
    public static void main(String[] args) throws Exception {
        byte[] buf = Files.readAllBytes(Paths.get(args[0]));
        int[] pos = {0};
        int H = readInt(buf, pos), W = readInt(buf, pos), S = readInt(buf, pos);
        int w2 = W + 2, h2 = H + 2, n = w2 * h2;
        int[] a = new int[n], b = new int[n], c = new int[n], m = new int[n];
        boolean[] open = new boolean[n];
        Arrays.fill(c, 8);
        int[] wall = new int[n];
        Arrays.fill(wall, 1);
        int p = pos[0];
        for (int r = 0; r < H; r++) {
            while (p < buf.length && buf[p] != '.' && buf[p] != '#' && (buf[p] < '1' || buf[p] > '9')) p++;
            for (int col = 0; col < W; col++) {
                byte ch = buf[p++];
                int idx = (r + 1) * w2 + col + 1;
                if (ch == '.') { open[idx] = true; wall[idx] = 0; m[idx] = -1; }
                else if (ch != '#') { a[idx] = 1000 * (ch - '0'); wall[idx] = 0; }
            }
        }
        for (int r = 1; r <= H; r++)
            for (int col = 1; col <= W; col++) {
                int idx = r * w2 + col;
                if (!open[idx]) continue;
                c[idx] = 4 + wall[idx - 1] + wall[idx + 1] + wall[idx - w2] + wall[idx + w2];
            }
        System.arraycopy(a, 0, b, 0, n);
        int lo = w2 + 1, hi = (H + 1) * w2 - 1;
        for (int s = 0; s < S; s++) {
            step(a, b, c, m, lo, hi, w2);
            int[] t = a; a = b; b = t;
        }
        long sum = 0, best = -1, br = 0, bc = 0, chk = 0;
        for (int r = 0; r < H; r++)
            for (int col = 0; col < W; col++) {
                int idx = (r + 1) * w2 + col + 1;
                if (!open[idx]) continue;
                long v = a[idx];
                sum += v;
                if (v > best) { best = v; br = r; bc = col; }
                chk += v * ((long) r * W + col + 1);
            }
        System.out.print("sum " + sum + "\nmax " + best + " " + br + " " + bc + "\nchecksum " + chk + "\n");
        System.out.flush();
    }

    static void step(int[] a, int[] b, int[] c, int[] m, int lo, int hi, int w2) {
        for (int i = lo; i < hi; i++) {
            b[i] = (c[i] * a[i] + ((a[i - 1] + a[i + 1] + a[i - w2] + a[i + w2]) & m[i])) >> 3;
        }
    }

    static int readInt(byte[] buf, int[] pos) {
        int p = pos[0];
        while (p < buf.length && (buf[p] < '0' || buf[p] > '9')) p++;
        int v = 0;
        while (p < buf.length && buf[p] >= '0' && buf[p] <= '9') v = v * 10 + (buf[p++] - '0');
        pos[0] = p;
        return v;
    }
}
