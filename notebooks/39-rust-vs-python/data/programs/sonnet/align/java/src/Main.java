import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;

public class Main {
    static byte[] b;
    static int p;

    static void skipWs() {
        while (p < b.length && b[p] <= ' ') p++;
    }

    static int nextInt() {
        skipWs();
        int v = 0;
        while (p < b.length && b[p] >= '0' && b[p] <= '9') v = v * 10 + (b[p++] - '0');
        return v;
    }

    public static void main(String[] args) throws IOException {
        b = Files.readAllBytes(Paths.get(args[0]));
        skipWs();
        int[] code = new int[256];
        int A = 0;
        while (p < b.length && b[p] > ' ') code[b[p++] & 255] = A++;
        int[] ins = new int[A], del = new int[A];
        int[] sub = new int[A * A];
        for (int i = 0; i < A; i++) ins[i] = nextInt();
        for (int i = 0; i < A; i++) del[i] = nextInt();
        for (int i = 0; i < A * A; i++) sub[i] = nextInt();
        int P = nextInt();

        int[] prev = new int[16], cur = new int[16], tc = new int[16], insT = new int[16];
        StringBuilder out = new StringBuilder();
        long total = 0;
        for (int q = 0; q < P; q++) {
            skipWs();
            int s = p;
            while (p < b.length && b[p] > ' ') p++;
            int n = p - s;
            skipWs();
            int t = p;
            while (p < b.length && b[p] > ' ') p++;
            int m = p - t;
            if (tc.length < m + 1) {
                prev = new int[m + 1];
                cur = new int[m + 1];
                tc = new int[m + 1];
                insT = new int[m + 1];
            }
            for (int j = 1; j <= m; j++) {
                int c = code[b[t + j - 1] & 255];
                tc[j] = c;
                insT[j] = ins[c];
            }
            int[] pv = prev, cu = cur;
            pv[0] = 0;
            for (int j = 1; j <= m; j++) pv[j] = pv[j - 1] + insT[j];
            for (int i = 1; i <= n; i++) {
                int a = code[b[s + i - 1] & 255];
                int d = del[a];
                int base = a * A;
                int left = pv[0] + d;
                cu[0] = left;
                for (int j = 1; j <= m; j++) {
                    int v = Math.min(pv[j] + d, pv[j - 1] + sub[base + tc[j]]);
                    left = Math.min(v, left + insT[j]);
                    cu[j] = left;
                }
                int[] tmp = pv; pv = cu; cu = tmp;
            }
            long r = pv[m];
            total += r;
            out.append(r).append('\n');
        }
        out.append("total ").append(total).append('\n');
        System.out.print(out);
        System.out.flush();
    }
}
