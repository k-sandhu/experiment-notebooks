import java.io.*;
import java.util.*;

public class Main {
    public static void main(String[] args) throws IOException {
        BufferedReader br = new BufferedReader(new FileReader(args[0]));
        StringTokenizer st = new StringTokenizer(br.readLine());
        int H = Integer.parseInt(st.nextToken());
        int W = Integer.parseInt(st.nextToken());
        int S = Integer.parseInt(st.nextToken());
        char[][] g = new char[H][];
        for (int r = 0; r < H; r++) {
            String line = br.readLine();
            g[r] = line.toCharArray();
        }
        br.close();
        int N = H * W;
        int[] a = new int[N];
        int[] b = new int[N];
        int cnt = 0;
        for (int r = 0; r < H; r++) {
            for (int c = 0; c < W; c++) {
                char ch = g[r][c];
                if (ch == '.') cnt++;
                else if (ch != '#') {
                    int v = 1000 * (ch - '0');
                    a[r * W + c] = v;
                    b[r * W + c] = v;
                }
            }
        }
        int[] cells = new int[cnt];
        int[] nbr = new int[cnt * 4];
        int k = 0;
        for (int r = 0; r < H; r++) {
            for (int c = 0; c < W; c++) {
                if (g[r][c] != '.') continue;
                int i = r * W + c;
                cells[k] = i;
                nbr[4 * k] = (r > 0 && g[r - 1][c] != '#') ? i - W : i;
                nbr[4 * k + 1] = (r < H - 1 && g[r + 1][c] != '#') ? i + W : i;
                nbr[4 * k + 2] = (c > 0 && g[r][c - 1] != '#') ? i - 1 : i;
                nbr[4 * k + 3] = (c < W - 1 && g[r][c + 1] != '#') ? i + 1 : i;
                k++;
            }
        }
        int[] cur = a, nxt = b;
        for (int s = 0; s < S; s++) {
            final int[] o = cur;
            final int[] n = nxt;
            for (int j = 0, p = 0; j < cnt; j++, p += 4) {
                int i = cells[j];
                n[i] = ((o[i] << 2) + o[nbr[p]] + o[nbr[p + 1]] + o[nbr[p + 2]] + o[nbr[p + 3]]) >> 3;
            }
            int[] t = cur;
            cur = nxt;
            nxt = t;
        }
        long sum = 0, chk = 0;
        int maxV = -1, maxR = 0, maxC = 0;
        for (int r = 0; r < H; r++) {
            for (int c = 0; c < W; c++) {
                if (g[r][c] != '.') continue;
                int v = cur[r * W + c];
                sum += v;
                chk += (long) v * (r * (long) W + c + 1);
                if (v > maxV) {
                    maxV = v;
                    maxR = r;
                    maxC = c;
                }
            }
        }
        System.out.println("sum " + sum);
        System.out.println("max " + maxV + " " + maxR + " " + maxC);
        System.out.println("checksum " + chk);
    }
}
