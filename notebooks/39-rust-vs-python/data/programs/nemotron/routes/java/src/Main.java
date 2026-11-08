import java.io.File;
import java.io.FileInputStream;
import java.util.Arrays;

public class Main {
    static byte[] data;
    static int pos;
    static int len;

    static int readInt() {
        while (pos < len && (data[pos] < '0' || data[pos] > '9')) pos++;
        int x = 0;
        while (pos < len && data[pos] >= '0' && data[pos] <= '9') {
            x = x * 10 + (data[pos] - '0');
            pos++;
        }
        return x;
    }

    // Min-heap of packed (distance << 32) | node entries.
    static final class Heap {
        long[] h;
        int n;

        Heap(int cap) {
            h = new long[cap];
        }

        void push(long x) {
            if (n == h.length) {
                long[] g = new long[n * 2 + 1];
                System.arraycopy(h, 0, g, 0, n);
                h = g;
            }
            int i = n++;
            while (i > 0) {
                int p = (i - 1) / 2;
                if (h[p] <= x) break;
                h[i] = h[p];
                i = p;
            }
            h[i] = x;
        }

        long pop() {
            long top = h[0];
            long x = h[--n];
            if (n > 0) {
                int i = 0;
                h[0] = x;
                for (;;) {
                    int c = 2 * i + 1;
                    if (c >= n) break;
                    if (c + 1 < n && h[c + 1] < h[c]) c++;
                    if (h[c] >= x) break;
                    h[i] = h[c];
                    i = c;
                }
                h[i] = x;
            }
            return top;
        }
    }

    public static void main(String[] args) throws Exception {
        File file = new File(args[0]);
        data = new byte[(int) file.length()];
        try (FileInputStream fis = new FileInputStream(file)) {
            int got = 0;
            while (got < data.length) {
                int r = fis.read(data, got, data.length - got);
                if (r < 0) break;
                got += r;
            }
        }
        len = data.length;

        int N = readInt();
        int M = readInt();
        int Q = readInt();

        int[] eu = new int[M];
        int[] ev = new int[M];
        int[] ew = new int[M];
        int[] deg = new int[N];
        for (int i = 0; i < M; i++) {
            int u = readInt();
            int v = readInt();
            int w = readInt();
            eu[i] = u;
            ev[i] = v;
            ew[i] = w;
            deg[u]++;
            deg[v]++;
        }

        int[] off = new int[N + 1];
        for (int i = 0; i < N; i++) off[i + 1] = off[i] + deg[i];
        int[] to = new int[2 * M];
        int[] wt = new int[2 * M];
        int[] cur = new int[N];
        System.arraycopy(off, 0, cur, 0, N);
        for (int i = 0; i < M; i++) {
            int u = eu[i];
            int v = ev[i];
            int w = ew[i];
            int p = cur[u]++;
            to[p] = v;
            wt[p] = w;
            int q = cur[v]++;
            to[q] = u;
            wt[q] = w;
        }

        int[] sources = new int[Q];
        for (int i = 0; i < Q; i++) sources[i] = readInt();

        int[] dist = new int[N];
        Heap heap = new Heap(Math.max(M + 1, 1));
        StringBuilder sb = new StringBuilder();

        for (int s : sources) {
            Arrays.fill(dist, Integer.MAX_VALUE);
            dist[s] = 0;
            heap.n = 0;
            heap.push(((long) 0 << 32) | s);

            while (heap.n > 0) {
                long packed = heap.pop();
                int d = (int) (packed >> 32);
                int v = (int) (packed & 0xFFFFFFFFL);
                if (d > dist[v]) continue; // stale entry
                int e0 = off[v];
                int e1 = off[v + 1];
                for (int e = e0; e < e1; e++) {
                    int t = to[e];
                    int nd = d + wt[e];
                    if (nd < dist[t]) {
                        dist[t] = nd;
                        heap.push(((long) nd << 32) | t);
                    }
                }
            }

            long reach = 0;
            long total = 0;
            long far = -1;
            int node = -1;
            for (int v = 0; v < N; v++) {
                int dv = dist[v];
                if (dv != Integer.MAX_VALUE) {
                    reach++;
                    total += dv;
                    if (dv > far) {
                        far = dv;
                        node = v;
                    }
                }
            }

            sb.append(s).append(' ').append(reach).append(' ').append(total).append(' ').append(far).append(' ').append(node).append('\n');
        }

        System.out.print(sb);
    }
}
