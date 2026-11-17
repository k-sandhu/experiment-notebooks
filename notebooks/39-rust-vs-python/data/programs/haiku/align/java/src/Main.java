import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

// Weighted alignment cost (see SPEC.md).
//
// The input file is read as one byte array and parsed in place; no per-token Strings are
// created. The DP keeps one row of longs, updated in place, with the diagonal and left values
// held in locals. The scratch arrays are reused across pairs and only grow.
public class Main {
    private final byte[] data;
    private int pos;
    private int tokenEnd;

    private Main(byte[] data) {
        this.data = data;
    }

    // Skips whitespace, returns the start of the next token and sets tokenEnd to its end.
    private int nextToken() {
        int p = pos;
        while (p < data.length && data[p] <= ' ') p++;
        int start = p;
        while (p < data.length && data[p] > ' ') p++;
        pos = p;
        tokenEnd = p;
        return start;
    }

    private long nextNumber() {
        int start = nextToken();
        long v = 0;
        for (int k = start; k < tokenEnd; k++) v = v * 10 + (data[k] - '0');
        return v;
    }

    // Cost of the pair: s[1..n] are rows (deletions), t[1..m] are columns (insertions).
    // tIns[j] = ins[t[j]]. row must hold m + 1 values.
    static long alignCost(int[] s, int n, int[] t, int m, long[] tIns,
                          long[] del, long[] sub, int a, long[] row) {
        row[0] = 0;
        for (int j = 1; j <= m; j++) row[j] = row[j - 1] + tIns[j];

        for (int i = 1; i <= n; i++) {
            int si = s[i];
            long d = del[si];
            int base = si * a;

            long diag = row[0];
            long left = row[0] += d;
            for (int j = 1; j <= m; j++) {
                long up = row[j];
                // left is the only term that depends on the previous cell, so it goes last.
                long v = Math.min(Math.min(up + d, diag + sub[base + t[j]]), left + tIns[j]);
                row[j] = v;
                left = v;
                diag = up;
            }
        }
        return row[m];
    }

    public static void main(String[] args) throws IOException {
        Main in = new Main(Files.readAllBytes(Path.of(args[0])));

        int aStart = in.nextToken();
        int a = in.tokenEnd - aStart;
        int[] code = new int[256];
        for (int i = 0; i < a; i++) code[in.data[aStart + i] & 0xFF] = i;

        long[] ins = new long[a];
        long[] del = new long[a];
        long[] sub = new long[a * a];
        for (int i = 0; i < a; i++) ins[i] = in.nextNumber();
        for (int i = 0; i < a; i++) del[i] = in.nextNumber();
        for (int i = 0; i < a * a; i++) sub[i] = in.nextNumber();

        int pairs = (int) in.nextNumber();

        int[] s = new int[1];
        int[] t = new int[1];
        long[] tIns = new long[1];
        long[] row = new long[1];
        StringBuilder out = new StringBuilder();
        long total = 0;

        for (int p = 0; p < pairs; p++) {
            int sStart = in.nextToken();
            int n = in.tokenEnd - sStart;
            int tStart = in.nextToken();
            int m = in.tokenEnd - tStart;

            if (s.length < n + 1) s = new int[n + 1];
            if (t.length < m + 1) {
                t = new int[m + 1];
                tIns = new long[m + 1];
                row = new long[m + 1];
            }
            for (int i = 1; i <= n; i++) s[i] = code[in.data[sStart + i - 1] & 0xFF];
            for (int j = 1; j <= m; j++) {
                t[j] = code[in.data[tStart + j - 1] & 0xFF];
                tIns[j] = ins[t[j]];
            }

            long cost = alignCost(s, n, t, m, tIns, del, sub, a, row);
            total += cost;
            out.append(cost).append('\n');
        }

        out.append("total ").append(total).append('\n');
        System.out.print(out);
        System.out.flush();
    }
}
