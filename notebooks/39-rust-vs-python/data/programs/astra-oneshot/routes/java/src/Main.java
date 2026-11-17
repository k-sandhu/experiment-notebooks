import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.HashMap;

public class Main {
    private static final int BUCKET_COUNT = 1024;
    private static final int BUCKET_MASK = BUCKET_COUNT - 1;
    private static final long INF = Long.MAX_VALUE;

    private static final class FastInput {
        private final InputStream input;
        private final byte[] buffer = new byte[1 << 16];
        private int position;
        private int limit;

        FastInput(InputStream input) {
            this.input = input;
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
            } while (c <= 32 && c >= 0);

            int value = 0;
            while (c > 32) {
                value = value * 10 + c - '0';
                c = read();
            }
            return value;
        }
    }

    private static final class Graph {
        final int[] offsets;
        final int[] neighbors;
        final short[] weights;

        Graph(int[] offsets, int[] neighbors, short[] weights) {
            this.offsets = offsets;
            this.neighbors = neighbors;
            this.weights = weights;
        }
    }

    private static Graph readGraph(FastInput input, int n, int m)
            throws IOException {
        int[] from = new int[m];
        int[] to = new int[m];
        short[] weight = new short[m];
        int[] offsets = new int[n + 1];
        int edges = 0;

        for (int i = 0; i < m; i++) {
            int u = input.nextInt();
            int v = input.nextInt();
            int w = input.nextInt();

            // Positive-length self-loops cannot improve any shortest path.
            if (u != v) {
                from[edges] = u;
                to[edges] = v;
                weight[edges] = (short) w;
                offsets[u + 1]++;
                offsets[v + 1]++;
                edges++;
            }
        }

        for (int i = 1; i <= n; i++) {
            offsets[i] += offsets[i - 1];
        }

        int[] cursor = offsets.clone();
        int[] neighbors = new int[edges * 2];
        short[] weights = new short[edges * 2];

        for (int i = 0; i < edges; i++) {
            int u = from[i];
            int v = to[i];
            short w = weight[i];

            int p = cursor[u]++;
            neighbors[p] = v;
            weights[p] = w;

            p = cursor[v]++;
            neighbors[p] = u;
            weights[p] = w;
        }

        return new Graph(offsets, neighbors, weights);
    }

    private static final class Solver {
        private final Graph graph;
        private final long[] distance;
        private final int[] previous;
        private final int[] next;
        private final int[] heads = new int[BUCKET_COUNT];
        private final long[] occupied = new long[BUCKET_COUNT / 64];

        Solver(Graph graph, int n) {
            this.graph = graph;
            distance = new long[n];
            previous = new int[n];
            next = new int[n];
        }

        String solve(int source) {
            final long[] dist = distance;
            final int[] prev = previous;
            final int[] nextNode = next;
            final int[] head = heads;
            final long[] bits = occupied;
            final int[] offsets = graph.offsets;
            final int[] neighbors = graph.neighbors;
            final short[] weights = graph.weights;

            Arrays.fill(dist, INF);
            Arrays.fill(head, -1);
            Arrays.fill(bits, 0L);

            dist[source] = 0;
            prev[source] = -1;
            nextNode[source] = -1;
            head[0] = source;
            bits[0] = 1L;

            long summary = 1L;
            int bucket = 0;

            long reachable = 0;
            long total = 0;
            long farthest = 0;
            int farthestNode = source;

            // All queued distances lie in a window of width at most 1000.
            // Thus 1024 circular buckets preserve exact distance ordering.
            while (summary != 0) {
                if (head[bucket] == -1) {
                    int word = bucket >>> 6;
                    long candidates = bits[word] & (-1L << (bucket & 63));

                    if (candidates == 0) {
                        long laterWords = summary & (-1L << (word + 1));
                        word = Long.numberOfTrailingZeros(
                                laterWords != 0 ? laterWords : summary);
                        candidates = bits[word];
                    }

                    bucket = (word << 6)
                            + Long.numberOfTrailingZeros(candidates);
                }

                int u = head[bucket];
                int following = nextNode[u];
                head[bucket] = following;

                if (following != -1) {
                    prev[following] = -1;
                } else {
                    int word = bucket >>> 6;
                    bits[word] &= ~(1L << (bucket & 63));
                    if (bits[word] == 0) {
                        summary &= ~(1L << word);
                    }
                }

                long currentDistance = dist[u];
                reachable++;
                total += currentDistance;

                if (currentDistance > farthest) {
                    farthest = currentDistance;
                    farthestNode = u;
                } else if (currentDistance == farthest && u < farthestNode) {
                    farthestNode = u;
                }

                for (int e = offsets[u], end = offsets[u + 1]; e < end; e++) {
                    int v = neighbors[e];
                    long candidate = currentDistance + weights[e];
                    long oldDistance = dist[v];

                    if (candidate >= oldDistance) {
                        continue;
                    }

                    if (oldDistance != INF) {
                        // A strict improvement cannot target a settled node.
                        int oldBucket = (int) oldDistance & BUCKET_MASK;
                        int before = prev[v];
                        int after = nextNode[v];

                        if (before == -1) {
                            head[oldBucket] = after;
                        } else {
                            nextNode[before] = after;
                        }

                        if (after != -1) {
                            prev[after] = before;
                        }

                        if (head[oldBucket] == -1) {
                            int word = oldBucket >>> 6;
                            bits[word] &= ~(1L << (oldBucket & 63));
                            if (bits[word] == 0) {
                                summary &= ~(1L << word);
                            }
                        }
                    }

                    dist[v] = candidate;
                    int newBucket = (int) candidate & BUCKET_MASK;
                    int first = head[newBucket];

                    prev[v] = -1;
                    nextNode[v] = first;
                    head[newBucket] = v;

                    if (first != -1) {
                        prev[first] = v;
                    } else {
                        int word = newBucket >>> 6;
                        bits[word] |= 1L << (newBucket & 63);
                        summary |= 1L << word;
                    }
                }
            }

            return source + " " + reachable + " " + total + " "
                    + farthest + " " + farthestNode;
        }
    }

    public static void main(String[] args) throws IOException {
        try (InputStream file = new FileInputStream(args[0]);
             BufferedWriter output = new BufferedWriter(
                     new OutputStreamWriter(System.out, StandardCharsets.US_ASCII),
                     1 << 16)) {
            FastInput input = new FastInput(file);
            int n = input.nextInt();
            int m = input.nextInt();
            int q = input.nextInt();

            Graph graph = readGraph(input, n, m);
            Solver solver = new Solver(graph, n);
            HashMap<Integer, String> answers = new HashMap<>();

            for (int i = 0; i < q; i++) {
                int source = input.nextInt();
                String answer = answers.get(source);
                if (answer == null) {
                    answer = solver.solve(source);
                    answers.put(source, answer);
                }
                output.write(answer);
                output.write('\n');
            }
        }
    }
}
