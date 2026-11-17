import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;

public class Main {
    public static void main(String[] args) throws IOException {
        byte[] buf = Files.readAllBytes(Paths.get(args[0]));
        int rd = buf.length;
        int p = 0;

        int H = nextInt(buf, rd, p);
        p = skipInt(buf, rd, p);
        int W = nextInt(buf, rd, p);
        p = skipInt(buf, rd, p);
        int S = nextInt(buf, rd, p);
        p = skipInt(buf, rd, p);

        final int n = H * W;
        int[] cur = new int[n];
        int[] nxt = new int[n];
        boolean[] wall = new boolean[n];
        int[] openList = new int[n];
        int m = 0;

        while (p < rd && buf[p] != '\n') p++;
        if (p < rd) p++;

        for (int r = 0; r < H; r++) {
            for (int c = 0; c < W; c++) {
                char ch = (char) (buf[p++] & 0xFF);
                int i = r * W + c;
                if (ch == '#') {
                    wall[i] = true;
                } else if (ch >= '1' && ch <= '9') {
                    cur[i] = 1000 * (ch - '0');
                } else {
                    openList[m++] = i;
                }
            }
            while (p < rd && buf[p] != '\n') p++;
            if (p < rd) p++;
        }

        int[] iup = new int[n];
        int[] idown = new int[n];
        int[] ileft = new int[n];
        int[] iright = new int[n];
        System.arraycopy(cur, 0, nxt, 0, n);  // sources keep their fixed value in the swap buffer

        for (int k = 0; k < m; k++) {
            int i = openList[k];
            int r = i / W, c = i % W;
            iup[i]    = (r > 0      && !wall[i - W]) ? i - W : i;
            idown[i]  = (r + 1 < H  && !wall[i + W]) ? i + W : i;
            ileft[i]  = (c > 0      && !wall[i - 1]) ? i - 1 : i;
            iright[i] = (c + 1 < W  && !wall[i + 1]) ? i + 1 : i;
        }

        for (int s = 0; s < S; s++) {
            for (int k = 0; k < m; k++) {
                int i = openList[k];
                int v = cur[i];
                nxt[i] = (4 * v + cur[iup[i]] + cur[idown[i]] + cur[ileft[i]] + cur[iright[i]]) >> 3;
            }
            int[] t = cur; cur = nxt; nxt = t;
        }

        long sum = 0, chk = 0;
        int mx = -1, mi = 0;
        for (int k = 0; k < m; k++) {
            int i = openList[k];
            int v = cur[i];
            sum += v;
            chk += (long) v * (i + 1);
            if (v > mx) { mx = v; mi = i; }
        }

        StringBuilder sb = new StringBuilder(64);
        sb.append("sum ").append(sum).append('\n')
          .append("max ").append(mx).append(' ').append(mi / W).append(' ').append(mi % W).append('\n')
          .append("checksum ").append(chk).append('\n');
        System.out.print(sb);
    }

    static int nextInt(byte[] b, int rd, int p) {
        while (p < rd && (b[p] < '0' || b[p] > '9') && b[p] != '-') p++;
        boolean neg = false;
        if (p < rd && b[p] == '-') { neg = true; p++; }
        int v = 0;
        while (p < rd && b[p] >= '0' && b[p] <= '9') { v = v * 10 + (b[p] - '0'); p++; }
        return neg ? -v : v;
    }

    static int skipInt(byte[] b, int rd, int p) {
        while (p < rd && (b[p] < '0' || b[p] > '9') && b[p] != '-') p++;
        if (p < rd && b[p] == '-') p++;
        while (p < rd && b[p] >= '0' && b[p] <= '9') p++;
        return p;
    }
}
