import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.Arrays;

// Shortest paths from each source with Dial's bucket queue. Edge weights are 1..1000, so a ring of
// 1024 buckets replaces a heap: the bucket of distance d is d & 1023.
public final class Main {
    private static final int BUCKETS = 1024; // greater than the largest weight (1000)
    private static final int NIL = -1;

    private static byte[] buf;
    private static int pos;

    private static int nextInt() {
        final byte[] b = buf;
        int p = pos;
        final int len = b.length;
        while (p < len && (b[p] < '0' || b[p] > '9')) p++;
        int x = 0;
        while (p < len && b[p] >= '0' && b[p] <= '9') x = x * 10 + (b[p++] - '0');
        pos = p;
        return x;
    }

    public static void main(String[] args) throws IOException {
        buf = Files.readAllBytes(Paths.get(args[0]));
        final int n = nextInt();
        final int m = nextInt();
        final int q = nextInt();

        // Two passes over the edge lines: the first counts degrees, the second fills the adjacency arrays.
        final int edgesAt = pos;
        final int[] start = new int[n + 1];
        for (int i = 0; i < m; i++) {
            start[nextInt() + 1]++;
            start[nextInt() + 1]++;
            nextInt();
        }
        for (int v = 0; v < n; v++) start[v + 1] += start[v];

        final int[] arcTo = new int[2 * m];
        final int[] arcW = new int[2 * m];
        final int[] fill = Arrays.copyOf(start, n);
        pos = edgesAt;
        for (int i = 0; i < m; i++) {
            final int u = nextInt();
            final int v = nextInt();
            final int w = nextInt();
            int a = fill[u]++;
            arcTo[a] = v;
            arcW[a] = w;
            a = fill[v]++;
            arcTo[a] = u;
            arcW[a] = w;
        }

        final long[] dist = new long[n];
        final int[] head = new int[BUCKETS];
        final int[] entNode = new int[2 * m + 1];
        final int[] entNext = new int[2 * m + 1];
        final StringBuilder out = new StringBuilder();
        for (int k = 0; k < q; k++) {
            final int s = nextInt();
            Arrays.fill(dist, Long.MAX_VALUE);
            Arrays.fill(head, NIL);

            int used = 0;
            int pending = 0;
            dist[s] = 0;
            entNode[used] = s;
            entNext[used] = NIL;
            head[0] = used++;
            pending++;

            long reached = 0;
            long total = 0;
            long far = 0;
            int node = s;
            for (long cur = 0; pending > 0; cur++) {
                final int b = (int) (cur & (BUCKETS - 1));
                int e = head[b];
                head[b] = NIL;
                while (e != NIL) {
                    final int v = entNode[e];
                    e = entNext[e];
                    pending--;
                    if (dist[v] != cur) continue;

                    reached++;
                    total += cur;
                    if (cur > far || (cur == far && v < node)) {
                        far = cur;
                        node = v;
                    }
                    final int end = start[v + 1];
                    for (int i = start[v]; i < end; i++) {
                        final int to = arcTo[i];
                        final long nd = cur + arcW[i];
                        if (nd < dist[to]) {
                            dist[to] = nd;
                            final int nb = (int) (nd & (BUCKETS - 1));
                            entNode[used] = to;
                            entNext[used] = head[nb];
                            head[nb] = used++;
                            pending++;
                        }
                    }
                }
            }
            out.append(s).append(' ').append(reached).append(' ').append(total).append(' ')
                    .append(far).append(' ').append(node).append('\n');
        }
        System.out.print(out);
        System.out.flush();
    }
}
