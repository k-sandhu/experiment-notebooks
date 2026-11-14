import java.io.FileOutputStream;
import java.io.FileDescriptor;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

// Weighted edit distance for many pairs.
//
// With Q[j] = sum of column (insert) costs of C[1..j], the kernels store E[i][j] = D[i][j] - Q[j]:
//   E[i][j] = min(E[i-1][j] + rc, E[i-1][j-1] + adj[j], E[i][j-1]),  adj[j] = M[r][C_j] - cc[C_j]
// so the loop-carried dependency is a single min instead of add+min.
public class Main {
    private static byte[] data;
    private static int pos;

    private static long readInt() {
        byte[] d = data;
        int p = pos;
        while (p < d.length && (d[p] < '0' || d[p] > '9')) p++;
        long v = 0;
        while (p < d.length && d[p] >= '0' && d[p] <= '9') v = v * 10 + (d[p++] - '0');
        pos = p;
        return v;
    }

    private static int readWord(byte[] idx, byte[] w) {
        byte[] d = data;
        int p = pos;
        while (p < d.length && (d[p] < 'A' || d[p] > 'Z')) p++;
        int n = 0;
        while (p < d.length && d[p] >= 'A' && d[p] <= 'Z') w[n++] = idx[d[p++]];
        pos = p;
        return n;
    }

    // Rows are processed two per pass: two independent running-min chains and half the row
    // traffic. The passes are small methods so the JIT compiles them early as whole methods.
    private static int dp32(byte[] R, int n, int m, int[] rc, int[][] adjFor, int[] row) {
        final int len = m + 1;
        java.util.Arrays.fill(row, 0, len, 0);
        int i = 0;
        for (; i + 1 < n; i += 2) rows2(row, len, rc[R[i]], rc[R[i + 1]], adjFor[R[i]], adjFor[R[i + 1]]);
        if (i < n) row1(row, len, rc[R[i]], adjFor[R[i]]);
        return row[m];
    }

    private static void rows2(int[] row, int len, int d1, int d2, int[] adj1, int[] adj2) {
        int diag1 = row[0];
        int left1 = diag1 + d1;
        int left2 = left1 + d2;
        row[0] = left2;
        for (int j = 1; j < len; j++) {
            int up = row[j];
            int v1 = Math.min(Math.min(up + d1, diag1 + adj1[j]), left1);
            int v2 = Math.min(Math.min(v1 + d2, left1 + adj2[j]), left2);
            row[j] = v2;
            diag1 = up;
            left1 = v1;
            left2 = v2;
        }
    }

    private static void row1(int[] row, int len, int d, int[] adj) {
        int diag = row[0];
        int left = diag + d;
        row[0] = left;
        for (int j = 1; j < len; j++) {
            int up = row[j];
            int v = Math.min(Math.min(up + d, diag + adj[j]), left);
            row[j] = v;
            left = v;
            diag = up;
        }
    }

    // adj[j] = M[a][C_j] - cc[C_j] for j = 1..m (adj[0] unused).
    private static void buildAdj(int[] r, int[] Ma, int[] cc, byte[] C, int m) {
        r[0] = 0;
        for (int j = 0; j < m; j++) {
            int c = C[j];
            r[j + 1] = Ma[c] - cc[c];
        }
    }

    private static long sumCosts(int[] cc, byte[] C, int m) {
        long q = 0;
        for (int j = 0; j < m; j++) q += cc[C[j]];
        return q;
    }

    // int64 fallback for extremely long strings, where values could exceed int32.
    private static long dp64(byte[] R, int n, int m, int[] rc, int[][] adjFor) {
        long[] row = new long[m + 1];
        for (int i = 0; i < n; i++) {
            final long d = rc[R[i]];
            final int[] adj = adjFor[R[i]];
            long diag = row[0];
            long left = diag + d;
            row[0] = left;
            for (int j = 1; j <= m; j++) {
                long up = row[j];
                long v = Math.min(Math.min(up + d, diag + adj[j]), left);
                row[j] = v;
                left = v;
                diag = up;
            }
        }
        return row[m];
    }

    public static void main(String[] args) throws IOException {
        data = Files.readAllBytes(Path.of(args[0]));
        pos = 0;
        byte[] idx = new byte[128];
        int A = 0;
        while (pos < data.length && data[pos] >= 'A' && data[pos] <= 'Z') idx[data[pos++]] = (byte) A++;

        int[] insC = new int[26], delC = new int[26];
        int[][] subM = new int[26][26], subT = new int[26][26];
        for (int i = 0; i < A; i++) insC[i] = (int) readInt();
        for (int i = 0; i < A; i++) delC[i] = (int) readInt();
        for (int i = 0; i < A; i++)
            for (int j = 0; j < A; j++) {
                int v = (int) readInt();
                subM[i][j] = v;
                subT[j][i] = v;
            }
        int P = (int) readInt();

        byte[] sBuf = new byte[16], tBuf = new byte[16];
        int[] row = new int[16];
        int[][] adjFor = new int[26][];
        int[][] adjPool = new int[26][];
        StringBuilder out = new StringBuilder(P * 12 + 32);
        long total = 0;

        for (int k = 0; k < P; k++) {
            int need = remainingWordLen();
            if (sBuf.length < need) sBuf = new byte[need];
            int ns = readWord(idx, sBuf);
            need = remainingWordLen();
            if (tBuf.length < need) tBuf = new byte[need];
            int nt = readWord(idx, tBuf);

            // Put the longer string on the inner (column) axis: transposing swaps insert/delete
            // and transposes the substitution table, leaving D[n][m] unchanged.
            byte[] R, C;
            int n, m;
            int[] rc, cc;
            int[][] M;
            if (ns <= nt) {
                R = sBuf; n = ns; C = tBuf; m = nt; rc = delC; cc = insC; M = subM;
            } else {
                R = tBuf; n = nt; C = sBuf; m = ns; rc = insC; cc = delC; M = subT;
            }

            boolean[] used = new boolean[26];
            for (int i = 0; i < n; i++) used[R[i]] = true;
            long Q = sumCosts(cc, C, m);
            for (int a = 0; a < A; a++) {
                if (!used[a]) { adjFor[a] = null; continue; }
                int[] r = adjPool[a];
                if (r == null || r.length < m + 1) r = adjPool[a] = new int[Math.max(m + 1, 1024)];
                buildAdj(r, M[a], cc, C, m);
                adjFor[a] = r;
            }

            long cost;
            if ((long) (n + m + 4) * 1000 < (1L << 30)) {
                if (row.length < m + 1) row = new int[Math.max(m + 1, 1024)];
                cost = dp32(R, n, m, rc, adjFor, row) + Q;
            } else {
                cost = dp64(R, n, m, rc, adjFor) + Q;
            }
            total += cost;
            out.append(cost).append('\n');
        }
        out.append("total ").append(total).append('\n');
        FileOutputStream fos = new FileOutputStream(FileDescriptor.out);
        fos.write(out.toString().getBytes(StandardCharsets.US_ASCII));
        fos.flush();
    }

    // Length of the next word (skipping separators), without consuming it.
    private static int remainingWordLen() {
        byte[] d = data;
        int p = pos;
        while (p < d.length && (d[p] < 'A' || d[p] > 'Z')) p++;
        int q = p;
        while (q < d.length && d[q] >= 'A' && d[q] <= 'Z') q++;
        return q - p;
    }
}
