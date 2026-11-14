import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

/**
 * Weighted edit distance for many string pairs (exact DP recurrence from SPEC.md).
 * Two rolling rows; all table cells fit in 32 bits, the grand total in 64 bits.
 * Jackson libraries are unused: the input is plain whitespace-separated text.
 */
public class Main {

    static byte[] b;
    static int pos;
    static int len;

    static void skipWs() {
        while (pos < len && b[pos] <= 32) pos++;
    }

    static int nextInt() {
        skipWs();
        int x = 0;
        while (pos < len && b[pos] > 32) {
            x = x * 10 + (b[pos] - '0');
            pos++;
        }
        return x;
    }

    // Read one whitespace-separated token as letter indices.
    static int[] readTokenIdx(int[] idx) {
        skipWs();
        int start = pos;
        while (pos < len && b[pos] > 32) pos++;
        int n = pos - start;
        int[] a = new int[n];
        for (int i = 0; i < n; i++) a[i] = idx[b[start + i]];
        return a;
    }

    public static void main(String[] args) throws IOException {
        b = Files.readAllBytes(Path.of(args[0]));
        len = b.length;

        skipWs();
        int alphaStart = pos;
        while (pos < len && b[pos] > 32) pos++;
        int A = pos - alphaStart;

        int[] idx = new int[256];
        for (int i = 0; i < 256; i++) idx[i] = -1;
        for (int i = 0; i < A; i++) idx[b[alphaStart + i]] = i;

        int[] ins = new int[A];
        int[] del = new int[A];
        int[] sub = new int[A * A];
        for (int i = 0; i < A; i++) ins[i] = nextInt();
        for (int i = 0; i < A; i++) del[i] = nextInt();
        for (int i = 0; i < A * A; i++) sub[i] = nextInt();

        int P = nextInt();

        int[] prev = null;
        int[] cur = null;
        int[] insT = null;

        StringBuilder out = new StringBuilder();
        long total = 0;

        for (int pair = 0; pair < P; pair++) {
            int[] s = readTokenIdx(idx);
            int[] t = readTokenIdx(idx);
            int n = s.length;
            int m = t.length;

            if (prev == null || prev.length < m + 1) {
                prev = new int[m + 1];
                cur = new int[m + 1];
            }
            if (insT == null || insT.length < m) insT = new int[m];

            for (int j = 0; j < m; j++) insT[j] = ins[t[j]];

            prev[0] = 0;
            for (int j = 1; j <= m; j++) prev[j] = prev[j - 1] + insT[j - 1];

            for (int i = 0; i < n; i++) {
                int si = s[i];
                int d = del[si];
                int base = si * A;
                cur[0] = prev[0] + d;
                int diag = prev[0];
                for (int j = 1; j <= m; j++) {
                    int tj = t[j - 1];
                    int best = prev[j] + d;
                    int v = cur[j - 1] + insT[j - 1];
                    if (v < best) best = v;
                    v = diag + sub[base + tj];
                    if (v < best) best = v;
                    cur[j] = best;
                    diag = prev[j];
                }
                int[] tmp = prev;
                prev = cur;
                cur = tmp;
            }

            total += prev[m];
            out.append(prev[m]);
            out.append('\n');
        }

        out.append("total ");
        out.append(total);
        out.append('\n');
        System.out.print(out);
    }
}
