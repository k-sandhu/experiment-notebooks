import java.io.FileDescriptor;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;

public class Main {
    private static byte[] buf;
    private static int pos;
    private static int len;

    private static int nextInt() {
        final byte[] b = buf;
        int p = pos;
        final int n = len;
        while (p < n && b[p] <= ' ') p++;
        boolean neg = false;
        if (p < n && b[p] == '-') {
            neg = true;
            p++;
        } else if (p < n && b[p] == '+') {
            p++;
        }
        int v = 0;
        while (p < n && b[p] > ' ') {
            v = v * 10 + (b[p] - '0');
            p++;
        }
        pos = p;
        return neg ? -v : v;
    }

    // F[i][j] = min(F[i-1][j], F[i-1][j-1] + w[s_i][t_j], F[i][j-1]) with zero borders.
    private static void rows1(int[] F, int[] p1, int m) {
        int diag = 0, l1 = 0;
        for (int j = 0; j < m; j++) {
            int up = F[j];
            int v1 = Math.min(Math.min(up, diag + p1[j]), l1);
            F[j] = v1;
            diag = up;
            l1 = v1;
        }
    }

    private static void rows4(int[] F, int[] p1, int[] p2, int[] p3, int[] p4, int m) {
        int diag = 0, l1 = 0, l2 = 0, l3 = 0, l4 = 0;
        for (int j = 0; j < m; j++) {
            int up = F[j];
            int v1 = Math.min(Math.min(up, diag + p1[j]), l1);
            int v2 = Math.min(Math.min(v1, l1 + p2[j]), l2);
            int v3 = Math.min(Math.min(v2, l2 + p3[j]), l3);
            int v4 = Math.min(Math.min(v3, l3 + p4[j]), l4);
            F[j] = v4;
            diag = up;
            l1 = v1;
            l2 = v2;
            l3 = v3;
            l4 = v4;
        }
    }

    public static void main(String[] args) throws IOException {
        byte[] b = Files.readAllBytes(Paths.get(args[0]));
        buf = b;
        len = b.length;
        int n0 = len;
        int p = 0;
        while (p < n0 && b[p] <= ' ') p++;
        int[] map = new int[256];
        int A = 0;
        while (p < n0 && b[p] > ' ') {
            map[b[p] & 0xFF] = A++;
            p++;
        }
        pos = p;

        int[] ins = new int[A];
        int[] del = new int[A];
        for (int i = 0; i < A; i++) ins[i] = nextInt();
        for (int i = 0; i < A; i++) del[i] = nextInt();
        int[][] W = new int[A][A];
        for (int i = 0; i < A; i++) {
            int[] wi = W[i];
            int di = del[i];
            for (int j = 0; j < A; j++) {
                wi[j] = nextInt() - ins[j] - di;
            }
        }
        int P = nextInt();

        int cap = 1024;
        int[][] prof = new int[A][cap];
        int[] F = new int[cap];
        int[] tc = new int[cap];

        StringBuilder sb = new StringBuilder(P * 8 + 32);
        long total = 0;
        p = pos;
        for (int q = 0; q < P; q++) {
            while (p < n0 && b[p] <= ' ') p++;
            int sStart = p;
            while (p < n0 && b[p] > ' ') p++;
            int sEnd = p;
            while (p < n0 && b[p] <= ' ') p++;
            int tStart = p;
            while (p < n0 && b[p] > ' ') p++;
            int tEnd = p;
            int n = sEnd - sStart;
            int m = tEnd - tStart;

            if (m > cap) {
                cap = Math.max(m, cap * 2);
                prof = new int[A][cap];
                F = new int[cap];
                tc = new int[cap];
            }

            long I = 0;
            for (int j = 0; j < m; j++) {
                int x = map[b[tStart + j] & 0xFF];
                tc[j] = x;
                I += ins[x];
            }

            long S = 0;
            int mask = 0;
            for (int i = sStart; i < sEnd; i++) {
                int c = map[b[i] & 0xFF];
                S += del[c];
                mask |= 1 << c;
            }

            for (int c = 0; c < A; c++) {
                if ((mask & (1 << c)) == 0) continue;
                int[] wc = W[c];
                int[] pc = prof[c];
                for (int j = 0; j < m; j++) {
                    pc[j] = wc[tc[j]];
                }
            }

            for (int j = 0; j < m; j++) F[j] = 0;

            int i = sStart;
            int r = n & 3;
            for (int k = 0; k < r; k++) {
                int c = map[b[i++] & 0xFF];
                rows1(F, prof[c], m);
            }
            for (; i < sEnd; i += 4) {
                int c1 = map[b[i] & 0xFF];
                int c2 = map[b[i + 1] & 0xFF];
                int c3 = map[b[i + 2] & 0xFF];
                int c4 = map[b[i + 3] & 0xFF];
                rows4(F, prof[c1], prof[c2], prof[c3], prof[c4], m);
            }

            long cost = (m > 0 ? (long) F[m - 1] : 0L) + I + S;
            total += cost;
            sb.append(cost).append('\n');
        }
        sb.append("total ").append(total).append('\n');

        byte[] out = sb.toString().getBytes(StandardCharsets.ISO_8859_1);
        FileOutputStream fos = new FileOutputStream(FileDescriptor.out);
        fos.write(out, 0, out.length);
        fos.flush();
    }
}
