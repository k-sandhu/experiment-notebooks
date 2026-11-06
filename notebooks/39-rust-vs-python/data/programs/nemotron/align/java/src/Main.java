import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.nio.file.Files;
import java.nio.file.Path;

public class Main {
    static final class Tokens {
        private final String s;
        private int pos;
        private final int len;

        Tokens(String s) {
            this.s = s;
            this.len = s.length();
        }

        private static boolean isSpace(int c) {
            return c == ' ' || c == '\n' || c == '\r' || c == '\t' || c == '\f';
        }

        void skip() {
            while (pos < len && isSpace(s.charAt(pos))) pos++;
        }

        String next() {
            skip();
            int start = pos;
            while (pos < len && !isSpace(s.charAt(pos))) pos++;
            return s.substring(start, pos);
        }

        int nextInt() {
            skip();
            boolean neg = false;
            if (pos < len && s.charAt(pos) == '-') { neg = true; pos++; }
            int v = 0;
            while (pos < len && s.charAt(pos) >= '0' && s.charAt(pos) <= '9') {
                v = v * 10 + (s.charAt(pos) - '0');
                pos++;
            }
            return neg ? -v : v;
        }
    }

    public static void main(String[] args) throws Exception {
        String content = Files.readString(Path.of(args[0]));
        Tokens tok = new Tokens(content);

        String alphabet = tok.next();
        int A = alphabet.length();

        int[] charIndex = new int[26];
        for (int i = 0; i < 26; i++) charIndex[i] = -1;
        for (int i = 0; i < A; i++) charIndex[alphabet.charAt(i) - 'A'] = i;

        int[] ins = new int[A];
        int[] del = new int[A];
        for (int i = 0; i < A; i++) ins[i] = tok.nextInt();
        for (int i = 0; i < A; i++) del[i] = tok.nextInt();
        int[][] sub = new int[A][A];
        for (int i = 0; i < A; i++)
            for (int j = 0; j < A; j++)
                sub[i][j] = tok.nextInt();

        int P = tok.nextInt();

        int[] prev = new int[1];
        int[] cur = new int[1];
        int[] sIdx = new int[0];
        int[] tIdx = new int[0];
        int[] insT = new int[0];

        long total = 0;
        BufferedWriter out = new BufferedWriter(new OutputStreamWriter(System.out, "UTF-8"));

        for (int pair = 0; pair < P; pair++) {
            String s = tok.next();
            String t = tok.next();
            int n = s.length(), m = t.length();

            if (sIdx.length < n) sIdx = new int[n];
            for (int i = 0; i < n; i++) sIdx[i] = charIndex[s.charAt(i) - 'A'];
            if (tIdx.length < m) tIdx = new int[m];
            if (insT.length < m) insT = new int[m];
            for (int j = 0; j < m; j++) {
                tIdx[j] = charIndex[t.charAt(j) - 'A'];
                insT[j] = ins[tIdx[j]];
            }

            if (prev.length < m + 1) { prev = new int[m + 1]; cur = new int[m + 1]; }

            prev[0] = 0;
            for (int j = 1; j <= m; j++) prev[j] = prev[j - 1] + insT[j - 1];

            for (int i = 1; i <= n; i++) {
                int si = sIdx[i - 1];
                int delSi = del[si];
                int[] subRow = sub[si];
                cur[0] = prev[0] + delSi;
                for (int j = 1; j <= m; j++) {
                    int tj = tIdx[j - 1];
                    int up = prev[j] + delSi;
                    int left = cur[j - 1] + insT[j - 1];
                    int diag = prev[j - 1] + subRow[tj];
                    int best = up < left ? up : left;
                    cur[j] = diag < best ? diag : best;
                }
                int[] tmp = prev; prev = cur; cur = tmp;
            }

            int cost = prev[m];
            total += cost;
            out.write(Integer.toString(cost));
            out.write("\n");
        }
        out.write("total ");
        out.write(Long.toString(total));
        out.write("\n");
        out.flush();
    }
}
