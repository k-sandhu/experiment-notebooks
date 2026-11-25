import java.io.*;
import java.util.Arrays;

public class Main {
    private static final int BUCKET_COUNT = 1024;
    private static final int BUCKET_MASK = BUCKET_COUNT - 1;

    public static void main(String[] args) throws Exception {
        FastInput input = new FastInput(args[0]);
        int n = input.nextInt();
        int m = input.nextInt();
        int q = input.nextInt();

        Graph graph = readGraph(input, n, m);
        int[] sources = new int[q];
        for (int i = 0; i < q; i++) {
            sources[i] = input.nextInt();
        }
        input.close();

        Solver solver = new Solver(graph);
        StringBuilder output = new StringBuilder();
        for (int source : sources) {
            solver.solve(source, output);
        }
        System.out.print(output);
    }

    private static Graph readGraph(FastInput input, int n, int m) throws IOException {
        int[] from = new int[m];
        int[] to = new int[m];
        short[] lengths = new short[m];
        int[] offsets = new int[n + 1];
        int edgeCount = 0;

        for (int i = 0; i < m; i++) {
            int u = input.nextInt();
            int v = input.nextInt();
            int w = input.nextInt();
            if (u != v) {
                from[edgeCount] = u;
                to[edgeCount] = v;
                lengths[edgeCount] = (short) w;
                edgeCount++;
                offsets[u + 1]++;
                offsets[v + 1]++;
            }
        }

        for (int i = 1; i <= n; i++) {
            offsets[i] += offsets[i - 1];
        }

        int[] targets = new int[offsets[n]];
        short[] weights = new short[offsets[n]];
        int[] positions = Arrays.copyOf(offsets, n);

        for (int i = 0; i < edgeCount; i++) {
            int u = from[i];
            int v = to[i];
            short w = lengths[i];

            int p = positions[u]++;
            targets[p] = v;
            weights[p] = w;

            p = positions[v]++;
            targets[p] = u;
            weights[p] = w;
        }

        return new Graph(offsets, targets, weights);
    }

    private static final class Graph {
        final int[] offsets;
        final int[] targets;
        final short[] weights;

        Graph(int[] offsets, int[] targets, short[] weights) {
            this.offsets = offsets;
            this.targets = targets;
            this.weights = weights;
        }
    }

    private static final class Solver {
        final Graph graph;
        final long[] distance;
        final int[] next;
        final int[] previous;
        final int[] heads = new int[BUCKET_COUNT];
        final long[] occupied = new long[BUCKET_COUNT / 64];

        Solver(Graph graph) {
            this.graph = graph;
            int n = graph.offsets.length - 1;
            distance = new long[n];
            next = new int[n];
            previous = new int[n];
        }

        void solve(int source, StringBuilder output) {
            final long[] dist = distance;
            final int[] nextNode = next;
            final int[] prevNode = previous;
            final int[] head = heads;
            final long[] bits = occupied;
            final int[] offsets = graph.offsets;
            final int[] targets = graph.targets;
            final short[] weights = graph.weights;

            Arrays.fill(dist, Long.MAX_VALUE);
            Arrays.fill(head, -1);
            Arrays.fill(bits, 0L);

            dist[source] = 0;
            nextNode[source] = -1;
            prevNode[source] = -1;
            head[0] = source;
            bits[0] = 1L;

            int nonemptyWords = 1;
            int currentBucket = 0;
            int reachable = 0;
            long total = 0;
            long farthest = 0;
            int farthestNode = source;

            while (nonemptyWords != 0) {
                if (head[currentBucket] == -1) {
                    int word = currentBucket >>> 6;
                    long candidates = bits[word] & (-1L << (currentBucket & 63));

                    if (candidates == 0) {
                        int higherWords = nonemptyWords & (-1 << (word + 1));
                        word = Integer.numberOfTrailingZeros(
                                higherWords != 0 ? higherWords : nonemptyWords);
                        candidates = bits[word];
                    }

                    currentBucket = (word << 6)
                            + Long.numberOfTrailingZeros(candidates);
                }

                int u = head[currentBucket];
                int following = nextNode[u];
                head[currentBucket] = following;

                if (following == -1) {
                    int word = currentBucket >>> 6;
                    bits[word] &= ~(1L << (currentBucket & 63));
                    if (bits[word] == 0) {
                        nonemptyWords &= ~(1 << word);
                    }
                } else {
                    prevNode[following] = -1;
                }

                long du = dist[u];
                reachable++;
                total += du;

                if (du > farthest) {
                    farthest = du;
                    farthestNode = u;
                } else if (du == farthest && u < farthestNode) {
                    farthestNode = u;
                }

                for (int e = offsets[u], end = offsets[u + 1]; e < end; e++) {
                    int v = targets[e];
                    long candidate = du + weights[e];
                    long oldDistance = dist[v];

                    if (candidate >= oldDistance) {
                        continue;
                    }

                    if (oldDistance != Long.MAX_VALUE) {
                        int oldBucket = (int) oldDistance & BUCKET_MASK;
                        int before = prevNode[v];
                        int after = nextNode[v];

                        if (before == -1) {
                            head[oldBucket] = after;
                        } else {
                            nextNode[before] = after;
                        }
                        if (after != -1) {
                            prevNode[after] = before;
                        }

                        if (head[oldBucket] == -1) {
                            int word = oldBucket >>> 6;
                            bits[word] &= ~(1L << (oldBucket & 63));
                            if (bits[word] == 0) {
                                nonemptyWords &= ~(1 << word);
                            }
                        }
                    }

                    dist[v] = candidate;
                    int bucket = (int) candidate & BUCKET_MASK;
                    int first = head[bucket];

                    prevNode[v] = -1;
                    nextNode[v] = first;
                    if (first != -1) {
                        prevNode[first] = v;
                    } else {
                        int word = bucket >>> 6;
                        bits[word] |= 1L << (bucket & 63);
                        nonemptyWords |= 1 << word;
                    }
                    head[bucket] = v;
                }
            }

            output.append(source).append(' ')
                    .append(reachable).append(' ')
                    .append(total).append(' ')
                    .append(farthest).append(' ')
                    .append(farthestNode).append('\n');
        }
    }

    private static final class FastInput implements Closeable {
        private final InputStream input;
        private final byte[] buffer = new byte[1 << 16];
        private int position;
        private int limit;

        FastInput(String path) throws IOException {
            input = new FileInputStream(path);
        }

        private int read() throws IOException {
            if (position >= limit) {
                limit = input.read(buffer);
                position = 0;
                if (limit < 0) {
                    return -1;
                }
            }
            return buffer[position++] & 255;
        }

        int nextInt() throws IOException {
            int c;
            do {
                c = read();
            } while (c <= 32 && c != -1);

            int value = 0;
            while (c >= '0' && c <= '9') {
                value = value * 10 + c - '0';
                c = read();
            }
            return value;
        }

        public void close() throws IOException {
            input.close();
        }
    }
}
