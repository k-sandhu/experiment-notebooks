import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;

public final class Main {
    private static final class Scanner {
        byte[] data;
        int pos;
        Scanner(String path) throws Exception { data = Files.readAllBytes(Path.of(path)); }
        int read() {
            while (data[pos] <= 32) ++pos;
            int x = 0;
            do { x = x * 10 + data[pos++] - 48; }
            while (pos < data.length && data[pos] >= 48 && data[pos] <= 57);
            return x;
        }
    }

    // Intrusive decrease-key queue with a two-level bitmap over circular buckets.
    private static final class BucketQueue {
        final int[] head = new int[1024], bits = new int[32];
        final int[] next, prev;
        int summary, current;
        BucketQueue(int n) { next = new int[n]; prev = new int[n]; }
        void reset() { Arrays.fill(head, -1); Arrays.fill(bits, 0); summary = current = 0; }
        void insert(int v, int b) {
            int h = head[b]; next[v] = h; prev[v] = -1;
            if (h >= 0) prev[h] = v;
            else { bits[b >>> 5] |= 1 << (b & 31); summary |= 1 << (b >>> 5); }
            head[b] = v;
        }
        void remove(int v, int b) {
            int p = prev[v], n = next[v];
            if (p >= 0) next[p] = n; else head[b] = n;
            if (n >= 0) prev[n] = p;
            if (head[b] < 0) {
                int g = b >>> 5;
                bits[g] &= ~(1 << (b & 31));
                if (bits[g] == 0) summary &= ~(1 << g);
            }
        }
        int pop() {
            int b = current;
            if (head[b] < 0) {
                int g = b >>> 5, word = bits[g] & (-1 << (b & 31));
                if (word == 0) {
                    int groups = summary & (-2 << g);
                    if (groups == 0) groups = summary;
                    g = Integer.numberOfTrailingZeros(groups); word = bits[g];
                }
                current = b = (g << 5) + Integer.numberOfTrailingZeros(word);
            }
            int v = head[b]; remove(v, b); return v;
        }
    }

    public static void main(String[] args) throws Exception {
        Scanner in = new Scanner(args[0]);
        int n = in.read(), m = in.read(), q = in.read(), edgeStart = in.pos;
        int[] offset = new int[n + 1];
        for (int i = 0; i < m; ++i) {
            int u = in.read(), v = in.read(); in.read();
            if (u != v) { ++offset[u + 1]; ++offset[v + 1]; }
        }
        for (int i = 1; i <= n; ++i) offset[i] += offset[i - 1];
        int[] to = new int[offset[n]];
        short[] weight = new short[offset[n]];
        BucketQueue queue = new BucketQueue(n);
        System.arraycopy(offset, 0, queue.next, 0, n);
        in.pos = edgeStart;
        for (int i = 0; i < m; ++i) {
            int u = in.read(), v = in.read(), w = in.read();
            if (u == v) continue;
            int a = queue.next[u]++, b = queue.next[v]++;
            to[a] = v; weight[a] = (short) w;
            to[b] = u; weight[b] = (short) w;
        }
        int[] sources = new int[q];
        for (int i = 0; i < q; ++i) sources[i] = in.read();
        in.data = null;
        long[] dist = new long[n];
        StringBuilder out = new StringBuilder();
        for (int s : sources) {
            Arrays.fill(dist, Long.MAX_VALUE);
            queue.reset(); dist[s] = 0; queue.insert(s, 0);
            long reached = 0, total = 0, far = 0;
            int farNode = s;
            while (queue.summary != 0) {
                int u = queue.pop();
                long d = dist[u]; ++reached; total += d;
                if (d > far) { far = d; farNode = u; }
                else if (d == far && u < farNode) farNode = u;
                for (int e = offset[u], end = offset[u + 1]; e < end; ++e) {
                    int v = to[e];
                    long nd = d + weight[e], old = dist[v];
                    if (nd >= old) continue;
                    if (old != Long.MAX_VALUE) queue.remove(v, (int) old & 1023);
                    dist[v] = nd; queue.insert(v, (int) nd & 1023);
                }
            }
            out.append(s).append(' ').append(reached).append(' ').append(total).append(' ')
               .append(far).append(' ').append(farNode).append('\n');
        }
        System.out.print(out);
    }
}
