import java.io.FileOutputStream;
import java.nio.file.Files;
import java.nio.file.Paths;

public class Main {
    static byte[] d;
    static int pos, N;

    static void skipWs() {
        while (pos < N) {
            byte c = d[pos];
            if (c == ' ' || c == '\n' || c == '\r' || c == '\t') pos++;
            else break;
        }
    }

    static int parseInt() {
        skipWs();
        int v = 0;
        while (pos < N && d[pos] >= '0' && d[pos] <= '9') v = v * 10 + (d[pos++] - '0');
        return v;
    }

    public static void main(String[] args) throws Exception {
        d = Files.readAllBytes(Paths.get(args[0]));
        N = d.length;
        pos = 0;

        int[] charIdx = new int[256];
        java.util.Arrays.fill(charIdx, -1);
        int A = 0;
        while (pos < N && d[pos] != '\n') {
            int c = d[pos++] & 0xFF;
            if (c >= 'A' && c <= 'Z') charIdx[c] = A++;
        }
        if (pos < N) pos++;

        int[] ins = new int[A], del = new int[A], sub = new int[A * A];
        for (int i = 0; i < A; i++) ins[i] = parseInt();
        for (int i = 0; i < A; i++) del[i] = parseInt();
        for (int i = 0; i < A * A; i++) sub[i] = parseInt();
        int P = parseInt();

        byte[][] strs = new byte[2 * P][];
        int maxLen = 0;
        for (int k = 0; k < 2 * P; k++) {
            skipWs();
            int start = pos;
            while (pos < N) {
                byte c = d[pos];
                if (c == ' ' || c == '\n' || c == '\r' || c == '\t') break;
                pos++;
            }
            int len = pos - start;
            byte[] s = new byte[len];
            for (int i = 0; i < len; i++) s[i] = (byte) charIdx[d[start + i] & 0xFF];
            if (len > maxLen) maxLen = len;
            strs[k] = s;
        }

        int[] prev = new int[maxLen + 1], cur = new int[maxLen + 1], insT = new int[maxLen];
        StringBuilder out = new StringBuilder(P * 12);
        long total = 0;

        for (int p = 0; p < P; p++) {
            byte[] s = strs[2 * p], t = strs[2 * p + 1];
            int n = s.length, m = t.length;
            for (int j = 0; j < m; j++) insT[j] = ins[t[j]];
            prev[0] = 0;
            for (int j = 0; j < m; j++) prev[j + 1] = prev[j] + insT[j];
            for (int i = 0; i < n; i++) {
                int si = s[i];
                int dcost = del[si];
                int subBase = si * A;
                int diag = prev[0];
                int left = diag + dcost;
                cur[0] = left;
                for (int j = 0; j < m; j++) {
                    int up = prev[j + 1];
                    int a = up + dcost;
                    int b = left + insT[j];
                    int c = diag + sub[subBase + t[j]];
                    int v = a < b ? a : b;
                    if (c < v) v = c;
                    diag = up;
                    left = v;
                    cur[j + 1] = v;
                }
                int[] tmp = prev; prev = cur; cur = tmp;
            }
            int ans = prev[m];
            total += ans;
            out.append(ans).append('\n');
        }
        out.append("total ").append(total).append('\n');
        FileOutputStream fos = new FileOutputStream(java.io.FileDescriptor.out);
        fos.write(out.toString().getBytes());
        fos.flush();
    }
}
