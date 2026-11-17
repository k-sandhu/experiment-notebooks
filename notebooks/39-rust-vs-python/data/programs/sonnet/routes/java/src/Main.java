import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;

public class Main {
    static byte[] buf;
    static int pos;

    static int readInt() {
        byte[] b = buf;
        int p = pos;
        while (b[p] < '0') p++;
        int x = 0;
        while (p < b.length && b[p] >= '0') { x = x * 10 + (b[p] - '0'); p++; }
        pos = p;
        return x;
    }

    public static void main(String[] args) throws IOException {
        buf = Files.readAllBytes(Paths.get(args[0]));
        int n = readInt(), m = readInt(), q = readInt();
        int[] eu = new int[m], ev = new int[m], ew = new int[m];
        int[] start = new int[n + 2];
        for (int i = 0; i < m; i++) {
            int u = readInt(), v = readInt(), w = readInt();
            eu[i] = u; ev[i] = v; ew[i] = w;
            if (u != v) { start[u + 2]++; start[v + 2]++; }
        }
        for (int i = 2; i <= n + 1; i++) start[i] += start[i - 1];
        int[] adj = new int[start[n + 1]];
        for (int i = 0; i < m; i++) {
            int u = eu[i], v = ev[i], w = ew[i];
            if (u == v) continue;
            adj[start[u + 1]++] = v * 1024 + w;
            adj[start[v + 1]++] = u * 1024 + w;
        }
        final long INF = Long.MAX_VALUE;
        long[] dist = new long[n];
        long[] h = new long[adj.length + 2];
        StringBuilder sb = new StringBuilder();
        for (int qi = 0; qi < q; qi++) {
            int s = readInt();
            java.util.Arrays.fill(dist, INF);
            int hs = 0;
            dist[s] = 0;
            h[hs++] = s;
            while (hs > 0) {
                long top = h[0];
                long last = h[--hs];
                if (hs > 0) {
                    int i = 0;
                    for (;;) {
                        int c = 2 * i + 1;
                        if (c >= hs) break;
                        if (c + 1 < hs && h[c + 1] < h[c]) c++;
                        if (h[c] >= last) break;
                        h[i] = h[c];
                        i = c;
                    }
                    h[i] = last;
                }
                int u = (int) (top & 0xffffffffL);
                long d = top >>> 32;
                if (d != dist[u]) continue;
                for (int e = start[u], ee = start[u + 1]; e < ee; e++) {
                    int x = adj[e];
                    int v = x >> 10;
                    long nd = d + (x & 1023);
                    if (nd < dist[v]) {
                        dist[v] = nd;
                        long key = (nd << 32) | v;
                        int i = hs++;
                        while (i > 0) {
                            int par = (i - 1) >> 1;
                            if (h[par] <= key) break;
                            h[i] = h[par];
                            i = par;
                        }
                        h[i] = key;
                    }
                }
            }
            long total = 0, far = 0, cnt = 0;
            for (int i = 0; i < n; i++) {
                long d = dist[i];
                if (d != INF) {
                    cnt++;
                    total += d;
                    if (d > far) far = d;
                }
            }
            int node = 0;
            for (int i = 0; i < n; i++) if (dist[i] == far) { node = i; break; }
            sb.append(s).append(' ').append(cnt).append(' ').append(total).append(' ')
              .append(far).append(' ').append(node).append('\n');
        }
        System.out.print(sb);
        System.out.flush();
    }
}
