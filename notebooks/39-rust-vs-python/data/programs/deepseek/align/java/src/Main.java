import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

public class Main {
    static byte[] buf;
    static int pos;
    static int len;

    static int readInt() {
        byte[] b = buf;
        int p = pos;
        int n = len;
        while (p < n && b[p] <= ' ') p++;
        int x = 0;
        while (p < n && b[p] >= '0' && b[p] <= '9') {
            x = x * 10 + (b[p] - '0');
            p++;
        }
        pos = p;
        return x;
    }

    public static void main(String[] args) throws IOException {
        buf = Files.readAllBytes(Path.of(args[0]));
        len = buf.length;
        pos = 0;

        int[] map = new int[256];
        for (int i = 0; i < 256; i++) map[i] = -1;

        int p = pos;
        while (p < len && buf[p] <= ' ') p++;
        int astart = p;
        while (p < len && buf[p] > ' ') p++;
        int A = p - astart;
        for (int i = 0; i < A; i++) map[buf[astart + i] & 0xff] = i;
        pos = p;

        int[] insC = new int[A];
        int[] delC = new int[A];
        int[] subC = new int[A * A];
        for (int i = 0; i < A; i++) insC[i] = readInt();
        for (int i = 0; i < A; i++) delC[i] = readInt();
        for (int i = 0; i < A * A; i++) subC[i] = readInt();

        int P = readInt();
        p = pos;

        int[] sIdx = new int[4096];
        int[] tIdx = new int[4096];
        int[] insT = new int[4096];
        int[] prev = new int[4097];
        int[] cur = new int[4097];

        StringBuilder sb = new StringBuilder(P * 8 + 16);
        long total = 0;

        for (int q = 0; q < P; q++) {
            while (p < len && buf[p] <= ' ') p++;
            int s0 = p;
            while (p < len && buf[p] > ' ') p++;
            int n = p - s0;
            if (n > sIdx.length) {
                sIdx = new int[n];
                tIdx = new int[n];
                insT = new int[n];
                prev = new int[n + 1];
                cur = new int[n + 1];
            }
            for (int i = 0; i < n; i++) sIdx[i] = map[buf[s0 + i] & 0xff];

            while (p < len && buf[p] <= ' ') p++;
            int t0 = p;
            while (p < len && buf[p] > ' ') p++;
            int m = p - t0;
            if (m > tIdx.length) {
                tIdx = new int[m];
                insT = new int[m];
                prev = new int[m + 1];
                cur = new int[m + 1];
            }
            for (int j = 0; j < m; j++) {
                int c = map[buf[t0 + j] & 0xff];
                tIdx[j] = c;
                insT[j] = insC[c];
            }

            prev[0] = 0;
            for (int j = 1; j <= m; j++) prev[j] = prev[j - 1] + insT[j - 1];

            int[] pr = prev;
            int[] cu = cur;

            for (int i = 1; i <= n; i++) {
                int c = sIdx[i - 1];
                int d = delC[c];
                int sr = c * A;
                int v = pr[0] + d;
                cu[0] = v;
                for (int j = 1; j <= m; j++) {
                    int best0 = pr[j] + d;
                    int x = v + insT[j - 1];
                    int best = x < best0 ? x : best0;
                    x = pr[j - 1] + subC[sr + tIdx[j - 1]];
                    if (x < best) best = x;
                    v = best;
                    cu[j] = best;
                }
                int[] tmp = pr;
                pr = cu;
                cu = tmp;
            }

            prev = pr;
            cur = cu;
            int cost = pr[m];
            total += cost;
            sb.append(cost).append('\n');
        }

        sb.append("total ").append(total).append('\n');
        System.out.print(sb);
    }
}
