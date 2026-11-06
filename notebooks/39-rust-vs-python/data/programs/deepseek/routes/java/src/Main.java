import java.nio.file.Files;
import java.nio.file.Path;

public class Main {
    static byte[] data;
    static int pos;

    static int nextInt() {
        byte[] a = data;
        int n = a.length;
        int i = pos;
        while (i < n) {
            int c = a[i] - '0';
            if (c >= 0 && c <= 9) break;
            ++i;
        }
        int x = 0;
        while (i < n) {
            int c = a[i] - '0';
            if (c < 0 || c > 9) break;
            x = x * 10 + c;
            ++i;
        }
        pos = i;
        return x;
    }

    static long[] heap;
    static int heapSize;

    static void heapPush(long x) {
        long[] h = heap;
        int i = heapSize++;
        while (i > 0) {
            int p = (i - 1) >>> 1;
            if (h[p] <= x) break;
            h[i] = h[p];
            i = p;
        }
        h[i] = x;
    }

    static long heapPop() {
        long[] h = heap;
        long top = h[0];
        long x = h[--heapSize];
        int n = heapSize;
        if (n > 0) {
            int i = 0;
            for (;;) {
                int c = (i << 1) + 1;
                if (c >= n) break;
                if (c + 1 < n && h[c + 1] < h[c]) ++c;
                if (h[c] >= x) break;
                h[i] = h[c];
                i = c;
            }
            h[i] = x;
        }
        return top;
    }

    public static void main(String[] args) throws Exception {
        data = Files.readAllBytes(Path.of(args[0]));

        int N = nextInt();
        int M = nextInt();
        int Q = nextInt();

        int[] eu = new int[M];
        int[] ev = new int[M];
        int[] ew = new int[M];
        int[] deg = new int[N + 1];
        for (int i = 0; i < M; ++i) {
            int u = nextInt(), v = nextInt(), w = nextInt();
            eu[i] = u; ev[i] = v; ew[i] = w;
            ++deg[u]; ++deg[v];
        }
        int[] src = new int[Q];
        for (int i = 0; i < Q; ++i) src[i] = nextInt();

        int[] off = new int[N + 1];
        int acc = 0;
        for (int i = 0; i < N; ++i) { off[i] = acc; acc += deg[i]; }
        off[N] = acc;

        int[] fill = off.clone();
        int[] adj = new int[2 * M];
        for (int i = 0; i < M; ++i) {
            int u = eu[i], v = ev[i], w = ew[i];
            int p = fill[u]++; adj[p] = (v << 10) | w;
            p = fill[v]++; adj[p] = (u << 10) | w;
        }
        eu = null; ev = null; ew = null; deg = null; fill = null;

        final int INF = 0x3f3f3f3f;
        int[] dist = new int[N];

        int shift = 0;
        while ((1L << shift) < (long) N) ++shift;
        final long mask = (1L << shift) - 1L;

        heap = new long[2 * M + 16];

        StringBuilder out = new StringBuilder(256);

        for (int qi = 0; qi < Q; ++qi) {
            int s = src[qi];
            java.util.Arrays.fill(dist, INF);
            heapSize = 0;
            dist[s] = 0;
            heapPush(s);

            long total = 0;
            int reach = 0;
            int far = 0;
            int farNode = s;

            while (heapSize > 0) {
                long key = heapPop();
                int v = (int) (key & mask);
                int d = (int) (key >>> shift);
                if (d != dist[v]) continue;

                ++reach;
                total += d;
                if (d > far) { far = d; farNode = v; }

                int end = off[v + 1];
                for (int e = off[v]; e < end; ++e) {
                    int a = adj[e];
                    int u = a >>> 10;
                    int nd = d + (a & 1023);
                    if (nd < dist[u]) {
                        dist[u] = nd;
                        heapPush(((long) nd << shift) | (long) u);
                    }
                }
            }

            out.append(s).append(' ').append(reach).append(' ').append(total)
               .append(' ').append(far).append(' ').append(farNode).append('\n');
        }
        System.out.print(out);
    }
}
