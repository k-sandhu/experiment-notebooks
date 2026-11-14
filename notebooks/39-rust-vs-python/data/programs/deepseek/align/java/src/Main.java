import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;

public class Main {
    private byte[] data;
    private int pos;
    private int len;

    private void skipWs() {
        byte[] d = data;
        int p = pos, n = len;
        while (p < n && d[p] <= ' ') ++p;
        pos = p;
    }

    private int nextInt() {
        byte[] d = data;
        int p = pos, n = len;
        while (p < n && d[p] <= ' ') ++p;
        int v = 0;
        while (p < n) {
            int c = d[p];
            if (c < '0' || c > '9') break;
            v = v * 10 + (c - '0');
            ++p;
        }
        pos = p;
        return v;
    }

    public static void main(String[] args) throws Exception {
        Main m = new Main();
        m.run(args[0]);
    }

    private void run(String path) throws Exception {
        data = Files.readAllBytes(Path.of(path));
        len = data.length;
        pos = 0;

        skipWs();
        int abStart = pos;
        while (pos < len && data[pos] > ' ') ++pos;
        int A = pos - abStart;
        int[] mp = new int[256];
        for (int i = 0; i < A; ++i) mp[data[abStart + i] & 0xFF] = i;

        int[] ins = new int[A];
        int[] delc = new int[A];
        int[] sub = new int[A * A];
        for (int i = 0; i < A; ++i) ins[i] = nextInt();
        for (int i = 0; i < A; ++i) delc[i] = nextInt();
        for (int i = 0; i < A * A; ++i) sub[i] = nextInt();

        int P = nextInt();

        int[] s = new int[1024];
        int[] t = new int[1024];
        int[] tins = new int[1024];
        int[] row = new int[1024];

        StringBuilder out = new StringBuilder(P * 8 + 16);
        long total = 0;

        for (int q = 0; q < P; ++q) {
            skipWs();
            int sl = 0;
            while (pos < len && data[pos] > ' ') {
                if (sl == s.length) s = Arrays.copyOf(s, s.length * 2);
                s[sl++] = mp[data[pos] & 0xFF];
                ++pos;
            }
            skipWs();
            int tl = 0;
            while (pos < len && data[pos] > ' ') {
                if (tl == t.length) t = Arrays.copyOf(t, t.length * 2);
                t[tl++] = mp[data[pos] & 0xFF];
                ++pos;
            }

            final int n = sl;
            final int M = tl;

            boolean same = n == M;
            if (same) {
                for (int i = 0; i < n; ++i) {
                    if (s[i] != t[i]) { same = false; break; }
                }
            }
            if (same) {
                out.append('0').append('\n');
                continue;
            }

            if (tins.length < M) tins = new int[Math.max(M, tins.length * 2)];
            for (int j = 0; j < M; ++j) tins[j] = ins[t[j]];
            if (row.length < M + 1) row = new int[Math.max(M + 1, row.length * 2)];

            final int[] r = row;
            r[0] = 0;
            for (int j = 1; j <= M; ++j) r[j] = r[j - 1] + tins[j - 1];

            for (int i = 0; i < n; ++i) {
                final int si = s[i];
                final int dc = delc[si];
                final int sbase = si * A;

                int diag = r[0];
                int left = diag + dc;
                r[0] = left;

                for (int j = 1; j <= M; ++j) {
                    final int up = r[j];
                    final int a = up + dc;
                    final int b = diag + sub[sbase + t[j - 1]];
                    final int mn = a < b ? a : b;
                    final int x = left + tins[j - 1];
                    left = x < mn ? x : mn;
                    diag = up;
                    r[j] = left;
                }
            }

            final int cost = r[M];
            total += cost;
            out.append(cost).append('\n');
        }

        out.append("total ").append(total).append('\n');
        System.out.write(out.toString().getBytes());
        System.out.flush();
    }
}
