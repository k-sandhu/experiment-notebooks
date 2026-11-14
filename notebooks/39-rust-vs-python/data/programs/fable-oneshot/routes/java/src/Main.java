import java.io.IOException;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.Arrays;

public class Main {

    private static int findNext(long[] bm, int pos) {
        int w = pos >>> 6;
        long x = bm[w] & (-1L << (pos & 63));
        if (x != 0) return (w << 6) + Long.numberOfTrailingZeros(x);
        for (int i = 1; i <= 16; i++) {
            int ww = (w + i) & 15;
            x = bm[ww];
            if (x != 0) return (ww << 6) + Long.numberOfTrailingZeros(x);
        }
        return -1;
    }

    private static void runInt(int s, int[] off, int[] adj, int[] dist, int[] next, int[] prev,
                               int[] head, long[] bm, StringBuilder sb) {
        final int INF = Integer.MAX_VALUE;
        Arrays.fill(dist, INF);
        dist[s] = 0;
        head[0] = s;
        next[s] = -1;
        prev[s] = -1;
        bm[0] |= 1L;
        int pos = 0;
        long total = 0;
        int cnt = 0;
        int far = 0;
        int node = s;
        while (true) {
            int b = findNext(bm, pos);
            if (b < 0) break;
            int u = head[b];
            head[b] = -1;
            bm[b >>> 6] &= ~(1L << b);
            final int d = dist[u];
            int minNode = Integer.MAX_VALUE;
            int c = 0;
            while (u != -1) {
                int nu = next[u];
                c++;
                if (u < minNode) minNode = u;
                for (int e = off[u], end = off[u + 1]; e < end; e += 2) {
                    int v = adj[e];
                    int nd = d + adj[e + 1];
                    int dv = dist[v];
                    if (nd < dv) {
                        if (dv != INF) {
                            int pp = prev[v], nn = next[v];
                            if (pp == -1) {
                                int ob = dv & 1023;
                                head[ob] = nn;
                                if (nn == -1) bm[ob >>> 6] &= ~(1L << ob);
                            } else {
                                next[pp] = nn;
                            }
                            if (nn != -1) prev[nn] = pp;
                        }
                        dist[v] = nd;
                        int nb = nd & 1023;
                        int h = head[nb];
                        next[v] = h;
                        prev[v] = -1;
                        if (h != -1) prev[h] = v;
                        else bm[nb >>> 6] |= 1L << nb;
                        head[nb] = v;
                    }
                }
                u = nu;
            }
            cnt += c;
            total += (long) d * c;
            far = d;
            node = minNode;
            pos = (b + 1) & 1023;
        }
        sb.append(s).append(' ').append(cnt).append(' ').append(total).append(' ')
          .append(far).append(' ').append(node).append('\n');
    }

    private static void runLong(int s, int[] off, int[] adj, long[] dist, int[] next, int[] prev,
                                int[] head, long[] bm, StringBuilder sb) {
        final long INF = Long.MAX_VALUE;
        Arrays.fill(dist, INF);
        dist[s] = 0;
        head[0] = s;
        next[s] = -1;
        prev[s] = -1;
        bm[0] |= 1L;
        int pos = 0;
        long total = 0;
        int cnt = 0;
        long far = 0;
        int node = s;
        while (true) {
            int b = findNext(bm, pos);
            if (b < 0) break;
            int u = head[b];
            head[b] = -1;
            bm[b >>> 6] &= ~(1L << b);
            final long d = dist[u];
            int minNode = Integer.MAX_VALUE;
            int c = 0;
            while (u != -1) {
                int nu = next[u];
                c++;
                if (u < minNode) minNode = u;
                for (int e = off[u], end = off[u + 1]; e < end; e += 2) {
                    int v = adj[e];
                    long nd = d + adj[e + 1];
                    long dv = dist[v];
                    if (nd < dv) {
                        if (dv != INF) {
                            int pp = prev[v], nn = next[v];
                            if (pp == -1) {
                                int ob = (int) (dv & 1023);
                                head[ob] = nn;
                                if (nn == -1) bm[ob >>> 6] &= ~(1L << ob);
                            } else {
                                next[pp] = nn;
                            }
                            if (nn != -1) prev[nn] = pp;
                        }
                        dist[v] = nd;
                        int nb = (int) (nd & 1023);
                        int h = head[nb];
                        next[v] = h;
                        prev[v] = -1;
                        if (h != -1) prev[h] = v;
                        else bm[nb >>> 6] |= 1L << nb;
                        head[nb] = v;
                    }
                }
                u = nu;
            }
            cnt += c;
            total += d * c;
            far = d;
            node = minNode;
            pos = (b + 1) & 1023;
        }
        sb.append(s).append(' ').append(cnt).append(' ').append(total).append(' ')
          .append(far).append(' ').append(node).append('\n');
    }

    public static void main(String[] args) throws IOException {
        final byte[] buf = Files.readAllBytes(Paths.get(args[0]));
        final int len = buf.length;
        int p = 0;

        int[] hdr = new int[3];
        for (int i = 0; i < 3; i++) {
            while (p < len && buf[p] < '0') p++;
            int x = 0;
            while (p < len && buf[p] >= '0') {
                x = x * 10 + (buf[p] - '0');
                p++;
            }
            hdr[i] = x;
        }
        final int n = hdr[0];
        final int mTotal = hdr[1];
        final int q = hdr[2];

        int[] eu = new int[mTotal];
        int[] ev = new int[mTotal];
        int[] ew = new int[mTotal];
        int[] off = new int[n + 1];
        int m = 0;
        for (int i = 0; i < mTotal; i++) {
            while (p < len && buf[p] < '0') p++;
            int u = 0;
            while (p < len && buf[p] >= '0') {
                u = u * 10 + (buf[p] - '0');
                p++;
            }
            while (p < len && buf[p] < '0') p++;
            int v = 0;
            while (p < len && buf[p] >= '0') {
                v = v * 10 + (buf[p] - '0');
                p++;
            }
            while (p < len && buf[p] < '0') p++;
            int w = 0;
            while (p < len && buf[p] >= '0') {
                w = w * 10 + (buf[p] - '0');
                p++;
            }
            if (u != v) {
                eu[m] = u;
                ev[m] = v;
                ew[m] = w;
                m++;
                off[u + 1] += 2;
                off[v + 1] += 2;
            }
        }

        for (int i = 0; i < n; i++) off[i + 1] += off[i];
        int[] fill = Arrays.copyOf(off, n);
        int[] adj = new int[off[n]];
        for (int i = 0; i < m; i++) {
            int u = eu[i], v = ev[i], w = ew[i];
            int a = fill[u];
            fill[u] = a + 2;
            adj[a] = v;
            adj[a + 1] = w;
            int b = fill[v];
            fill[v] = b + 2;
            adj[b] = u;
            adj[b + 1] = w;
        }
        eu = null;
        ev = null;
        ew = null;
        fill = null;

        int[] src = new int[q];
        int qc = 0;
        for (int i = 0; i < q; i++) {
            while (p < len && buf[p] < '0') p++;
            if (p >= len) break;
            int x = 0;
            while (p < len && buf[p] >= '0') {
                x = x * 10 + (buf[p] - '0');
                p++;
            }
            src[qc++] = x;
        }

        int[] next = new int[n];
        int[] prev = new int[n];
        int[] head = new int[1024];
        Arrays.fill(head, -1);
        long[] bm = new long[16];
        StringBuilder sb = new StringBuilder(64 * (qc + 1));

        if (n <= 2000000) {
            int[] dist = new int[n];
            for (int i = 0; i < qc; i++) {
                runInt(src[i], off, adj, dist, next, prev, head, bm, sb);
            }
        } else {
            long[] dist = new long[n];
            for (int i = 0; i < qc; i++) {
                runLong(src[i], off, adj, dist, next, prev, head, bm, sb);
            }
        }

        byte[] out = sb.toString().getBytes(StandardCharsets.US_ASCII);
        PrintStream ps = System.out;
        ps.write(out, 0, out.length);
        ps.flush();
    }
}
