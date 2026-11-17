import java.io.IOException;
import java.io.PrintStream;
import java.io.FileOutputStream;
import java.io.FileDescriptor;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;

// Routes: Dijkstra from each source with a monotone radix heap on a CSR graph.
public class Main {
    private static byte[] buf;
    private static int pos;

    private static long next() {
        byte[] b = buf;
        int p = pos;
        while (b[p] < '0' || b[p] > '9') p++;
        long x = b[p++] - '0';
        while (p < b.length && b[p] >= '0' && b[p] <= '9') x = x * 10 + (b[p++] - '0');
        pos = p;
        return x;
    }

    // Graph in CSR form: neighbours of u are adj[2*k] (node) and adj[2*k+1] (length) for k in start[u]..start[u+1).
    private static int[] start;
    private static int[] adj;
    private static long[] dist;
    private static int shift;

    // Radix heap: keys are packed (dist << shift) | node, bucketed by the highest bit where dist differs from last.
    private static final long[][] buckets = new long[65][];
    private static final int[] sizes = new int[65];

    private static void push(long[][] bk, int[] sz, int b, long key) {
        long[] a = bk[b];
        int s = sz[b];
        if (s == a.length) bk[b] = a = Arrays.copyOf(a, s * 2);
        a[s] = key;
        sz[b] = s + 1;
    }

    private static String solve(int s) {
        long[] dist = Main.dist;
        int[] start = Main.start;
        int[] adj = Main.adj;
        long[][] bk = buckets;
        int[] sz = sizes;
        int sh = shift;
        long mask = (1L << sh) - 1;
        Arrays.fill(dist, Long.MAX_VALUE);
        Arrays.fill(sz, 0);
        long last = 0;
        int heapSize = 1;
        dist[s] = 0;
        push(bk, sz, 0, s);
        long reach = 0, total = 0, far = 0;
        int farNode = s;
        while (heapSize > 0) {
            if (sz[0] == 0) {
                int i = 1;
                while (sz[i] == 0) i++;
                long[] a = bk[i];
                int cnt = sz[i];
                long mn = Long.MAX_VALUE;
                for (int j = 0; j < cnt; j++) if (a[j] < mn) mn = a[j];
                last = mn >>> sh;
                sz[i] = 0;
                for (int j = 0; j < cnt; j++) {
                    long k = a[j];
                    long dk = k >>> sh;
                    push(bk, sz, dk == last ? 0 : 64 - Long.numberOfLeadingZeros(dk ^ last), k);
                }
            }
            heapSize--;
            long key = bk[0][--sz[0]];
            long d = key >>> sh;
            int u = (int) (key & mask);
            if (d != dist[u]) continue;
            reach++;
            total += d;
            if (d > far) {
                far = d;
                farNode = u;
            } else if (d == far && u < farNode) {
                farNode = u;
            }
            for (int k = start[u] << 1, end = start[u + 1] << 1; k < end; k += 2) {
                int v = adj[k];
                long nd = d + adj[k + 1];
                if (nd < dist[v]) {
                    dist[v] = nd;
                    push(bk, sz, nd == last ? 0 : 64 - Long.numberOfLeadingZeros(nd ^ last), (nd << sh) | v);
                    heapSize++;
                }
            }
        }
        return s + " " + reach + " " + total + " " + far + " " + farNode + "\n";
    }

    public static void main(String[] args) throws IOException {
        buf = Files.readAllBytes(Path.of(args[0]));
        pos = 0;
        int n = (int) next();
        int m = (int) next();
        int q = (int) next();

        int[] eu = new int[m], ev = new int[m], ew = new int[m];
        int[] st = new int[n + 1];
        for (int i = 0; i < m; i++) {
            int u = (int) next(), v = (int) next(), w = (int) next();
            eu[i] = u;
            ev[i] = v;
            ew[i] = w;
            if (u != v) { // self-loops never shorten a path
                st[u + 1]++;
                st[v + 1]++;
            }
        }
        for (int i = 0; i < n; i++) st[i + 1] += st[i];
        int[] a = new int[2 * st[n]];
        int[] fill = Arrays.copyOf(st, n);
        for (int i = 0; i < m; i++) {
            int u = eu[i], v = ev[i], w = ew[i];
            if (u == v) continue;
            int pu = fill[u]++ << 1;
            a[pu] = v;
            a[pu + 1] = w;
            int pv = fill[v]++ << 1;
            a[pv] = u;
            a[pv + 1] = w;
        }
        start = st;
        adj = a;
        dist = new long[n];
        shift = n > 1 ? 32 - Integer.numberOfLeadingZeros(n - 1) : 0;
        for (int i = 0; i < 65; i++) buckets[i] = new long[1024];

        StringBuilder out = new StringBuilder();
        for (int i = 0; i < q; i++) out.append(solve((int) next()));
        PrintStream ps = new PrintStream(new FileOutputStream(FileDescriptor.out), false, StandardCharsets.US_ASCII);
        ps.print(out);
        ps.flush();
    }
}
