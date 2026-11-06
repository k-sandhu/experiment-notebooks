import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.Arrays;

// Routes: shortest road distances from several sources.
// Multi-source Dijkstra (one run per source) over an undirected graph.
// Java SE only (Jackson libs are unused: input is plain integers).
//
// Graph is stored in CSR form: start[node..node+1) indexes into to/weight.
// Distances are int: any simple path has at most N-1 edges of weight <= 1000,
// so a distance never exceeds (N-1)*1000 < 2^31. Totals need long.

public class Main {
    private static byte[] buf;
    private static int pos;

    private static int N, M, Q;
    private static int[] start, to, weight;

    private static final int INF = Integer.MAX_VALUE;

    private static int nextInt() {
        while (pos < buf.length && buf[pos] <= 32) pos++;
        boolean neg = false;
        if (pos < buf.length && buf[pos] == '-') { neg = true; pos++; }
        int v = 0;
        while (pos < buf.length && buf[pos] >= '0' && buf[pos] <= '9') {
            v = v * 10 + (buf[pos] - '0');
            pos++;
        }
        return neg ? -v : v;
    }

    // Binary heap over (distance, node) pairs stored in two parallel arrays.
    private static final class Heap {
        private int[] d;
        private int[] n;
        private int size;

        Heap(int cap) {
            d = new int[cap];
            n = new int[cap];
            size = 0;
        }

        void clear() {
            size = 0;
        }

        void push(int dist, int node) {
            int i = size++;
            d[i] = dist;
            n[i] = node;
            while (i > 0) {
                int p = (i - 1) / 2;
                if (d[p] <= dist) break;
                d[i] = d[p];
                n[i] = n[p];
                i = p;
            }
            d[i] = dist;
            n[i] = node;
        }

        // Assumes non-empty. Leaves the min at index 0 until pop() is called.
        int peekDist() {
            return d[0];
        }

        int peekNode() {
            return n[0];
        }

        void pop() {
            --size;
            if (size == 0) return;
            int lastD = d[size];
            int lastN = n[size];
            int i = 0;
            for (;;) {
                int l = 2 * i + 1;
                int r = l + 1;
                if (l >= size) break;
                int child = l;
                if (r < size && d[r] < d[l]) child = r;
                if (d[child] >= lastD) break;
                d[i] = d[child];
                n[i] = n[child];
                i = child;
            }
            d[i] = lastD;
            n[i] = lastN;
        }

        boolean isEmpty() {
            return size == 0;
        }
    }

    public static void main(String[] args) throws Exception {
        buf = Files.readAllBytes(Paths.get(args[0]));
        pos = 0;

        N = nextInt();
        M = nextInt();
        Q = nextInt();

        int[] deg = new int[N + 1];
        int[] eu = new int[M];
        int[] ev = new int[M];
        int[] ew = new int[M];
        for (int i = 0; i < M; i++) {
            int u = nextInt();
            int v = nextInt();
            int w = nextInt();
            eu[i] = u;
            ev[i] = v;
            ew[i] = w;
            deg[u]++;
            deg[v]++;
        }

        start = new int[N + 1];
        for (int i = 0; i < N; i++) start[i + 1] = start[i] + deg[i];

        int totalEdges = 2 * M;
        to = new int[totalEdges];
        weight = new int[totalEdges];
        int[] cur = new int[N];
        System.arraycopy(start, 0, cur, 0, N);
        for (int i = 0; i < M; i++) {
            int u = eu[i];
            int v = ev[i];
            int w = ew[i];
            int p = cur[u]++;
            to[p] = v;
            weight[p] = w;
            p = cur[v]++;
            to[p] = u;
            weight[p] = w;
        }

        eu = null;
        ev = null;
        ew = null;
        deg = null;
        cur = null;

        int[] dist = new int[N];
        Heap heap = new Heap(Math.max(16, M));

        StringBuilder out = new StringBuilder();
        for (int q = 0; q < Q; q++) {
            int s = nextInt();
            Arrays.fill(dist, INF);
            dist[s] = 0;
            heap.clear();
            heap.push(0, s);
            while (!heap.isEmpty()) {
                int d = heap.peekDist();
                int u = heap.peekNode();
                heap.pop();
                if (d > dist[u]) continue;
                for (int e = start[u]; e < start[u + 1]; e++) {
                    int v = to[e];
                    int nd = d + weight[e];
                    if (nd < dist[v]) {
                        dist[v] = nd;
                        heap.push(nd, v);
                    }
                }
            }

            int R = 0;
            long total = 0;
            int far = -1;
            int node = -1;
            for (int i = 0; i < N; i++) {
                int d = dist[i];
                if (d != INF) {
                    R++;
                    total += d;
                    if (d > far) {
                        far = d;
                        node = i;
                    }
                }
            }
            out.append(s).append(' ').append(R).append(' ').append(total)
               .append(' ').append(far).append(' ').append(node).append('\n');
        }

        System.out.print(out);
    }
}
