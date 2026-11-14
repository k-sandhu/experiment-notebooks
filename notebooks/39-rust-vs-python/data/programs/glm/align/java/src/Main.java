import java.io.FileOutputStream;
import java.io.FileDescriptor;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;

public class Main {

    private static byte[] d;
    private static int pos;
    private static int end;

    private static int tokStart;
    private static int tokLen;

    private static void skipWs() {
        while (pos < end) {
            byte c = d[pos];
            if (c == ' ' || c == '\n' || c == '\r' || c == '\t') pos++;
            else break;
        }
    }

    private static long nextInt() {
        skipWs();
        boolean neg = false;
        if (pos < end && (d[pos] == '-' || d[pos] == '+')) {
            neg = d[pos] == '-';
            pos++;
        }
        long v = 0;
        while (pos < end) {
            byte c = d[pos];
            if (c >= '0' && c <= '9') {
                v = v * 10 + (c - '0');
                pos++;
            } else break;
        }
        return neg ? -v : v;
    }

    private static void nextToken() {
        skipWs();
        tokStart = pos;
        while (pos < end) {
            byte c = d[pos];
            if (c == ' ' || c == '\n' || c == '\r' || c == '\t') break;
            pos++;
        }
        tokLen = pos - tokStart;
    }

    // Compute cost of turning s (d[sStart..sStart+sLen)) into t, using the
    // already-parsed cost tables; returns the cost via a rolling row DP.
    private static long solve(int sStart, int sLen, int tStart, int tLen,
                              int[] idx, int[] ins, int[] del, int[] sub) {
        final int n = sLen;
        final int m = tLen;
        int[] row = rowBuf;
        if (row.length < m + 1) {
            row = new int[Math.max(m + 1, row.length * 2)];
            rowBuf = row;
        }
        int[] tIdx = tIdxBuf;
        int[] insT = insTBuf;
        if (tIdx.length < m) {
            tIdx = new int[Math.max(m, tIdx.length * 2)];
            tIdxBuf = tIdx;
            insT = new int[Math.max(m, insT.length * 2)];
            insTBuf = insT;
        }
        for (int j = 0; j < m; j++) {
            int c = idx[d[tStart + j] & 0xFF];
            tIdx[j] = c;
            insT[j] = ins[c];
        }

        row[0] = 0;
        for (int j = 0; j < m; j++) row[j + 1] = row[j] + insT[j];

        for (int i = 0; i < n; i++) {
            int si = idx[d[sStart + i] & 0xFF];
            int dl = del[si];
            int soff = si << 5; // sub row offset, stride 32
            int diag = row[0];
            row[0] = diag + dl;
            for (int j = 0; j < m; j++) {
                int up = row[j + 1];
                int v = up + dl;
                int x = row[j] + insT[j];
                if (x < v) v = x;
                x = diag + sub[soff + tIdx[j]];
                if (x < v) v = x;
                row[j + 1] = v;
                diag = up;
            }
        }
        return row[m];
    }

    private static int[] rowBuf = new int[64];
    private static int[] tIdxBuf = new int[64];
    private static int[] insTBuf = new int[64];

    private static byte[] outBuf = new byte[1 << 16];
    private static int outLen;
    private static final byte[] scratch = new byte[20];

    private static void appendInt(long v) {
        if (outLen + 24 > outBuf.length) {
            byte[] nb = new byte[outBuf.length * 2];
            System.arraycopy(outBuf, 0, nb, 0, outLen);
            outBuf = nb;
        }
        if (v == 0) {
            outBuf[outLen++] = '0';
            return;
        }
        int k = 20;
        while (v > 0) {
            scratch[--k] = (byte) ('0' + v % 10);
            v /= 10;
        }
        int cnt = 20 - k;
        System.arraycopy(scratch, k, outBuf, outLen, cnt);
        outLen += cnt;
    }

    public static void main(String[] args) throws IOException {
        d = Files.readAllBytes(Paths.get(args[0]));
        end = d.length;
        pos = 0;

        nextToken();
        final int A = tokLen;
        int[] idx = new int[256];
        java.util.Arrays.fill(idx, -1);
        for (int i = 0; i < A; i++) idx[d[tokStart + i] & 0xFF] = i;

        int[] ins = new int[A];
        int[] del = new int[A];
        int[] sub = new int[A << 5]; // stride 32 rows for cheap row offset
        for (int i = 0; i < A; i++) ins[i] = (int) nextInt();
        for (int i = 0; i < A; i++) del[i] = (int) nextInt();
        for (int i = 0; i < A; i++)
            for (int j = 0; j < A; j++) sub[(i << 5) + j] = (int) nextInt();

        final int P = (int) nextInt();

        outLen = 0;
        long total = 0;
        for (int q = 0; q < P; q++) {
            nextToken();
            int sStart = tokStart, n = tokLen;
            nextToken();
            int tStart = tokStart, m = tokLen;
            long cost = solve(sStart, n, tStart, m, idx, ins, del, sub);
            total += cost;
            appendInt(cost);
            outBuf[outLen++] = '\n';
        }
        if (outLen + 32 > outBuf.length) {
            byte[] nb = new byte[outBuf.length * 2];
            System.arraycopy(outBuf, 0, nb, 0, outLen);
            outBuf = nb;
        }
        outBuf[outLen++] = 't';
        outBuf[outLen++] = 'o';
        outBuf[outLen++] = 't';
        outBuf[outLen++] = 'a';
        outBuf[outLen++] = 'l';
        outBuf[outLen++] = ' ';
        appendInt(total);
        outBuf[outLen++] = '\n';
        FileOutputStream fo = new FileOutputStream(FileDescriptor.out);
        fo.write(outBuf, 0, outLen);
        fo.flush();
    }
}
