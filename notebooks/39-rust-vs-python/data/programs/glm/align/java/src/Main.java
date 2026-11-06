import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;

public class Main {

    public static void main(String[] args) throws IOException {
        byte[] buf = Files.readAllBytes(Path.of(args[0]));
        Parser ps = new Parser(buf);

        // Alphabet token
        String alpha = ps.token();
        int a = alpha.length();
        int[] charId = new int[128];
        Arrays.fill(charId, -1);
        for (int i = 0; i < a; i++) charId[alpha.charAt(i)] = i;

        int[] ins = new int[a];
        int[] del = new int[a];
        int[] sub = new int[a * a];
        ps.readInts(ins, a);
        ps.readInts(del, a);
        ps.readInts(sub, a * a);
        int p = ps.nextInt();

        StringBuilder out = new StringBuilder(Math.max(16, p * 9 + 16));
        long total = 0;

        int[] sIds = new int[1100];
        int[] tIds = new int[1100];
        int[] rowA = new int[1101];
        int[] rowB = new int[1101];

        for (int q = 0; q < p; q++) {
            byte[] b = ps.buf;
            // read s
            int start = ps.tokenStart();
            int n = ps.tokenEnd() - start;
            for (int i = 0; i < n; i++) sIds[i] = charId[b[start + i]];
            // read t
            start = ps.tokenStart();
            int m = ps.tokenEnd() - start;
            for (int j = 0; j < m; j++) tIds[j] = charId[b[start + j]];

            int[] prev = rowA;
            int[] cur = rowB;
            prev[0] = 0;
            for (int j = 1; j <= m; j++) prev[j] = prev[j - 1] + ins[tIds[j - 1]];
            for (int i = 0; i < n; i++) {
                final int si = sIds[i];
                final int dc = del[si];
                final int subBase = si * a;
                int left = prev[0] + dc;
                cur[0] = left;
                int diag = prev[0];
                for (int j = 1; j <= m; j++) {
                    final int tj = tIds[j - 1];
                    int best = prev[j] + dc;
                    final int l = left + ins[tj];
                    final int d = diag + sub[subBase + tj];
                    if (l < best) best = l;
                    if (d < best) best = d;
                    cur[j] = best;
                    left = best;
                    diag = prev[j];
                }
                int[] tmp = prev; prev = cur; cur = tmp;
            }
            long cost = prev[m];
            total += cost;
            out.append(cost).append('\n');
        }
        out.append("total ").append(total).append('\n');
        System.out.print(out);
    }

    private static final class Parser {
        final byte[] buf;
        final int len;
        int pos;
        int tokStart, tokEnd;

        Parser(byte[] buf) {
            this.buf = buf;
            this.len = buf.length;
        }

        private boolean isWs(byte b) {
            return b == ' ' || b == '\n' || b == '\r' || b == '\t' || b == '\f' || b == 11;
        }

        String token() {
            while (pos < len && isWs(buf[pos])) pos++;
            tokStart = pos;
            while (pos < len && !isWs(buf[pos])) pos++;
            tokEnd = pos;
            return new String(buf, tokStart, tokEnd - tokStart,
                    java.nio.charset.StandardCharsets.ISO_8859_1);
        }

        int tokenStart() {
            while (pos < len && isWs(buf[pos])) pos++;
            tokStart = pos;
            while (pos < len && !isWs(buf[pos])) pos++;
            tokEnd = pos;
            return tokStart;
        }

        int tokenEnd() {
            return tokEnd;
        }

        int nextInt() {
            while (pos < len && isWs(buf[pos])) pos++;
            int v = 0;
            while (pos < len && !isWs(buf[pos])) {
                v = v * 10 + (buf[pos] - '0');
                pos++;
            }
            return v;
        }

        void readInts(int[] dst, int count) {
            for (int i = 0; i < count; i++) dst[i] = nextInt();
        }
    }
}
