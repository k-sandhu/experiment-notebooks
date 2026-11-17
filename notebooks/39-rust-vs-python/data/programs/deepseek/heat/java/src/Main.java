import java.nio.file.Files;
import java.nio.file.Path;

public class Main {
    public static void main(String[] args) throws Exception {
        byte[] buf = Files.readAllBytes(Path.of(args[0]));
        int pos = 0;
        int len = buf.length;

        // read H W S
        while (pos < len && buf[pos] <= ' ') pos++;
        int H = 0;
        while (pos < len && buf[pos] >= '0' && buf[pos] <= '9') H = H * 10 + (buf[pos++] - '0');
        while (pos < len && buf[pos] <= ' ') pos++;
        int W = 0;
        while (pos < len && buf[pos] >= '0' && buf[pos] <= '9') W = W * 10 + (buf[pos++] - '0');
        while (pos < len && buf[pos] <= ' ') pos++;
        int S = 0;
        while (pos < len && buf[pos] >= '0' && buf[pos] <= '9') S = S * 10 + (buf[pos++] - '0');
        while (pos < len && buf[pos] != '\n') pos++;
        if (pos < len) pos++;

        int W2 = W + 2;
        int N = (H + 2) * W2;
        int[] cur = new int[N];
        int[] nxt = new int[N];
        byte[] kind = new byte[N]; // 0 wall, 1 open, 2 source
        int[] open = new int[H * W];
        int nOpen = 0;

        for (int r = 0; r < H; r++) {
            int rowStart = pos;
            int base = (r + 1) * W2 + 1;
            for (int c = 0; c < W; c++) {
                byte ch = buf[rowStart + c];
                int idx = base + c;
                if (ch == '.') {
                    kind[idx] = 1;
                    open[nOpen++] = idx;
                } else if (ch >= '1' && ch <= '9') {
                    kind[idx] = 2;
                    int v = (ch - '0') * 1000;
                    cur[idx] = v;
                    nxt[idx] = v;
                }
            }
            pos += W;
            while (pos < len && buf[pos] != '\n') pos++;
            if (pos < len) pos++;
        }

        byte[] coef = new byte[nOpen];
        for (int j = 0; j < nOpen; j++) {
            int i = open[j];
            int a = kind[i - W2] != 0 ? 1 : 0;
            int b = kind[i + W2] != 0 ? 1 : 0;
            int l = kind[i - 1] != 0 ? 1 : 0;
            int rr = kind[i + 1] != 0 ? 1 : 0;
            coef[j] = (byte) (4 + (1 - a) + (1 - b) + (1 - l) + (1 - rr));
        }

        int[] c = cur, n = nxt;
        for (int s = 0; s < S; s++) {
            for (int j = 0; j < nOpen; j++) {
                int i = open[j];
                n[i] = (coef[j] * c[i]
                        + c[i - W2] + c[i + W2] + c[i - 1] + c[i + 1]) >> 3;
            }
            int[] tmp = c; c = n; n = tmp;
        }

        long sum = 0, chk = 0;
        int maxv = -1, bestR = 0, bestC = 0;
        for (int j = 0; j < nOpen; j++) {
            int i = open[j];
            int v = c[i];
            int r = i / W2 - 1;
            int col = i % W2 - 1;
            sum += v;
            chk += (long) v * ((long) r * W + col + 1);
            if (v > maxv) { maxv = v; bestR = r; bestC = col; }
        }

        StringBuilder sb = new StringBuilder(80);
        sb.append("sum ").append(sum).append('\n');
        sb.append("max ").append(maxv).append(' ').append(bestR).append(' ').append(bestC).append('\n');
        sb.append("checksum ").append(chk).append('\n');
        System.out.print(sb);
    }
}
