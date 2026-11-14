import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;

public class Main {
    static byte[] buf;
    static int pos;

    static int readInt() {
        while (pos < buf.length && (buf[pos] < '0' || buf[pos] > '9')) pos++;
        int r = 0;
        while (pos < buf.length && buf[pos] >= '0' && buf[pos] <= '9') {
            r = r * 10 + (buf[pos] - '0');
            pos++;
        }
        return r;
    }

    public static void main(String[] args) throws IOException {
        buf = Files.readAllBytes(Paths.get(args[0]));
        pos = 0;
        final int H = readInt();
        final int W = readInt();
        final int S = readInt();
        final int W2 = W + 2;
        final int size = (H + 2) * W2;

        // type: 0 = wall/outside, 1 = open free cell, 2 = source
        byte[] type = new byte[size];
        int[] cur = new int[size];
        int[] nxt = new int[size];

        for (int r = 0; r < H; r++) {
            while (pos < buf.length && buf[pos] <= ' ') pos++;
            int rowBase = (r + 1) * W2 + 1;
            for (int c = 0; c < W; c++) {
                byte ch = buf[pos++];
                int idx = rowBase + c;
                if (ch == '.') {
                    type[idx] = 1;
                } else if (ch >= '1' && ch <= '9') {
                    type[idx] = 2;
                    int v = 1000 * (ch - '0');
                    cur[idx] = v;
                    nxt[idx] = v;
                } else {
                    type[idx] = 0;
                }
            }
        }

        // Collect free open cells and their coefficient (4 + number of wall/outside neighbours)
        int freeCount = 0;
        for (int i = 0; i < size; i++) if (type[i] == 1) freeCount++;
        int[] idxArr = new int[freeCount];
        int[] cf = new int[freeCount];
        int k = 0;
        for (int i = 0; i < size; i++) {
            if (type[i] == 1) {
                int walls = 0;
                if (type[i - W2] == 0) walls++;
                if (type[i + W2] == 0) walls++;
                if (type[i - 1] == 0) walls++;
                if (type[i + 1] == 0) walls++;
                idxArr[k] = i;
                cf[k] = 4 + walls;
                k++;
            }
        }

        final int n = freeCount;
        final int up = -W2, down = W2, left = -1, right = 1;
        for (int s = 0; s < S; s++) {
            final int[] c = cur;
            final int[] x = nxt;
            for (int q = 0; q < n; q++) {
                int i = idxArr[q];
                int old = c[i];
                int sum = c[i + up] + c[i + down] + c[i + left] + c[i + right];
                x[i] = (cf[q] * old + sum) >> 3;
            }
            int[] t = cur;
            cur = nxt;
            nxt = t;
        }

        long total = 0;
        long checksum = 0;
        int maxV = -1, maxR = 0, maxC = 0;
        for (int r = 0; r < H; r++) {
            int rowBase = (r + 1) * W2 + 1;
            for (int c = 0; c < W; c++) {
                int i = rowBase + c;
                if (type[i] == 0) continue;
                int v = cur[i];
                total += v;
                if (v > maxV) {
                    maxV = v;
                    maxR = r;
                    maxC = c;
                }
                checksum += (long) v * ((long) r * W + c + 1);
            }
        }

        StringBuilder sb = new StringBuilder();
        sb.append("sum ").append(total).append('\n');
        sb.append("max ").append(maxV).append(' ').append(maxR).append(' ').append(maxC).append('\n');
        sb.append("checksum ").append(checksum).append('\n');
        System.out.print(sb);
    }
}
