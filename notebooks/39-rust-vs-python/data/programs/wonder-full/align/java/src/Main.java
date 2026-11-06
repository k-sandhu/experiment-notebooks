import java.nio.file.Files;
import java.nio.file.Path;

public class Main {
    static byte[] data;
    static int pos;

    static boolean isWs(byte c) { return c == ' ' || c == '\n' || c == '\r' || c == '\t'; }

    static void skipWs() { while (pos < data.length && isWs(data[pos])) pos++; }

    // returns (start << 32) | len packed in long via two arrays; use int[] tok holder
    static void nextToken(int[] tok) {
        skipWs();
        int start = pos;
        while (pos < data.length && !isWs(data[pos])) pos++;
        tok[0] = start;
        tok[1] = pos - start;
    }

    static int nextInt() {
        skipWs();
        int v = 0;
        while (pos < data.length && data[pos] >= '0' && data[pos] <= '9') {
            v = v * 10 + (data[pos++] - '0');
        }
        return v;
    }

    public static void main(String[] args) throws Exception {
        data = Files.readAllBytes(Path.of(args[0]));
        pos = 0;
        int[] tok = new int[2];
        nextToken(tok);
        int aStart = tok[0];
        int A = tok[1];
        int[] idx = new int[256];
        for (int i = 0; i < A; i++) idx[data[aStart + i] & 0xFF] = i;

        int[] ins = new int[A], del = new int[A], sub = new int[A * A];
        for (int i = 0; i < A; i++) ins[i] = nextInt();
        for (int i = 0; i < A; i++) del[i] = nextInt();
        for (int i = 0; i < A * A; i++) sub[i] = nextInt();
        int P = nextInt();

        StringBuilder out = new StringBuilder(P * 8 + 32);
        long total = 0;
        int[] sIdx = new int[0], tIdx = new int[0];
        int[] prev = new int[0], curr = new int[0], colIns = new int[0], subCols = new int[0];

        for (int p = 0; p < P; p++) {
            nextToken(tok); int sStart = tok[0], sLen = tok[1];
            nextToken(tok); int tStart = tok[0], tLen = tok[1];
            long ans;
            boolean equal = sLen == tLen;
            if (equal) {
                for (int i = 0; i < sLen; i++) if (data[sStart + i] != data[tStart + i]) { equal = false; break; }
            }
            if (equal) {
                ans = 0;
            } else {
                if (sIdx.length < sLen) sIdx = new int[sLen];
                if (tIdx.length < tLen) tIdx = new int[tLen];
                for (int i = 0; i < sLen; i++) sIdx[i] = idx[data[sStart + i] & 0xFF];
                for (int i = 0; i < tLen; i++) tIdx[i] = idx[data[tStart + i] & 0xFF];

                int[] rowStr, colStr, rowCost, colCost;
                int R, C;
                boolean transposed;
                if (tLen <= sLen) {
                    rowStr = sIdx; colStr = tIdx; R = sLen; C = tLen;
                    rowCost = del; colCost = ins; transposed = false;
                } else {
                    rowStr = tIdx; colStr = sIdx; R = tLen; C = sLen;
                    rowCost = ins; colCost = del; transposed = true;
                }

                if (colIns.length < C + 1) colIns = new int[C + 1];
                for (int j = 0; j < C; j++) colIns[j + 1] = colCost[colStr[j]];

                if (subCols.length < A * C) subCols = new int[A * C];
                if (!transposed) {
                    for (int a = 0; a < A; a++) {
                        int base = a * C, sbase = a * A;
                        for (int j = 0; j < C; j++) subCols[base + j] = sub[sbase + colStr[j]];
                    }
                } else {
                    for (int b = 0; b < A; b++) {
                        int base = b * C;
                        for (int j = 0; j < C; j++) subCols[base + j] = sub[colStr[j] * A + b];
                    }
                }

                if (prev.length < C + 1) { prev = new int[C + 1]; curr = new int[C + 1]; }
                prev[0] = 0;
                for (int j = 1; j <= C; j++) prev[j] = prev[j - 1] + colIns[j];

                for (int i = 0; i < R; i++) {
                    int rc = rowStr[i];
                    int d = rowCost[rc];
                    int scBase = rc * C;
                    int left = prev[0] + d;
                    curr[0] = left;
                    int diag = prev[0];
                    for (int j = 1; j <= C; j++) {
                        int up = prev[j];
                        int best = diag + subCols[scBase + j - 1];
                        int cand = up + d;
                        if (cand < best) best = cand;
                        cand = left + colIns[j];
                        if (cand < best) best = cand;
                        curr[j] = best;
                        diag = up;
                        left = best;
                    }
                    int[] tmp = prev; prev = curr; curr = tmp;
                }
                ans = prev[C];
            }
            total += ans;
            out.append(ans).append('\n');
        }
        out.append("total ").append(total).append('\n');
        System.out.print(out.toString());
    }
}
