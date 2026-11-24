import java.io.IOException;
import java.io.PrintStream;
import java.nio.file.Files;
import java.nio.file.Paths;

public class Main {

    private static void step(int[] a, int[] d, int[] p, int[] o, int P, int from, int to) {
        for (int i = from; i < to; i++) {
            int c = a[i];
            int s = ((a[i - P] - c) & p[i - P])
                  + ((a[i + P] - c) & p[i + P])
                  + ((a[i - 1] - c) & p[i - 1])
                  + ((a[i + 1] - c) & p[i + 1]);
            d[i] = c + ((s & o[i]) >> 3);
        }
    }

    public static void main(String[] args) throws IOException {
        byte[] in = Files.readAllBytes(Paths.get(args[0]));
        int n = in.length;
        int pos = 0;
        int[] hdr = new int[3];
        for (int k = 0; k < 3; k++) {
            while (pos < n && (in[pos] < '0' || in[pos] > '9')) pos++;
            int v = 0;
            while (pos < n && in[pos] >= '0' && in[pos] <= '9') {
                v = v * 10 + (in[pos] - '0');
                pos++;
            }
            hdr[k] = v;
        }
        int H = hdr[0], W = hdr[1], S = hdr[2];
        while (pos < n && in[pos] != '\n') pos++;
        if (pos < n) pos++;

        int P = W + 2;
        int total = (H + 2) * P;
        int[] a = new int[total];
        int[] b = new int[total];
        int[] p = new int[total]; // passable (open or source): -1, else 0
        int[] o = new int[total]; // open: -1, else 0

        for (int r = 0; r < H; r++) {
            while (pos < n && (in[pos] == '\n' || in[pos] == '\r')) pos++;
            int base = (r + 1) * P + 1;
            for (int c = 0; c < W; c++) {
                if (pos >= n) break;
                byte ch = in[pos];
                if (ch == '\n' || ch == '\r') break;
                pos++;
                int idx = base + c;
                if (ch == '.') {
                    p[idx] = -1;
                    o[idx] = -1;
                } else if (ch >= '1' && ch <= '9') {
                    p[idx] = -1;
                    a[idx] = 1000 * (ch - '0');
                }
            }
        }
        System.arraycopy(a, 0, b, 0, total);

        int from = P;
        int to = (H + 1) * P;
        for (int s = 0; s < S; s++) {
            step(a, b, p, o, P, from, to);
            int[] t = a;
            a = b;
            b = t;
        }

        long sum = 0;
        long checksum = 0;
        int max = -1, maxR = 0, maxC = 0;
        for (int r = 0; r < H; r++) {
            int base = (r + 1) * P + 1;
            long wbase = (long) r * W + 1;
            for (int c = 0; c < W; c++) {
                int idx = base + c;
                if (o[idx] != 0) {
                    int v = a[idx];
                    sum += v;
                    checksum += (long) v * (wbase + c);
                    if (v > max) {
                        max = v;
                        maxR = r;
                        maxC = c;
                    }
                }
            }
        }

        StringBuilder sb = new StringBuilder(96);
        sb.append("sum ").append(sum).append('\n');
        sb.append("max ").append(max).append(' ').append(maxR).append(' ').append(maxC).append('\n');
        sb.append("checksum ").append(checksum).append('\n');
        PrintStream out = System.out;
        out.print(sb);
        out.flush();
    }
}
