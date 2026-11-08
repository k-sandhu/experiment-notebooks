import java.io.FileInputStream;
import java.nio.file.Path;
import java.util.Arrays;

public class Main {
    static byte[] data;
    static int pos;

    static int nextInt() {
        while (data[pos] <= ' ') pos++;
        int x = 0;
        while (data[pos] > ' ') {
            x = x * 10 + (data[pos] - '0');
            pos++;
        }
        return x;
    }

    // Smallest set bit index >= p (wrapping around), or -1.
    static int nextSetBit(long[] bits, int words, int p) {
        int wi = p >> 6;
        long w = bits[wi] & (~0L << (p & 63));
        if (w != 0L) return (wi << 6) + Long.numberOfTrailingZeros(w);
        for (int i = wi + 1; i < words; i++) {
            if (bits[i] != 0L) return (i << 6) + Long.numberOfTrailingZeros(bits[i]);
        }
        for (int i = 0; i < wi; i++) {
            if (bits[i] != 0L) return (i << 6) + Long.numberOfTrailingZeros(bits[i]);
        }
        long low = bits[wi] & ((1L << (p & 63)) - 1);
        if (low != 0L) return (wi << 6) + Long.numberOfTrailingZeros(low);
        return -1;
    }

    static void runInt(int N, int Q, int[] src, int[] off, int[] at, int[] aw,
                       int maxW, long[] out) {
        final int INF = Integer.MAX_VALUE;
        int[] dist = new int[N];

        int nb = maxW + 1;
        if (nb < 2) nb = 2;
        int words = (nb + 63) >> 6;
        long[] bits = new long[words];
        int[][] buckets = new int[nb][];
        int[] bsize = new int[nb];
        for (int i = 0; i < nb; i++) buckets[i] = new int[64];

        for (int qi = 0; qi < Q; qi++) {
            int s = src[qi];
            Arrays.fill(dist, INF);
            for (int i = 0; i < nb; i++) bsize[i] = 0;
            Arrays.fill(bits, 0L);
            long cur = 0;
            dist[s] = 0;
            buckets[0][0] = s;
            bsize[0] = 1;
            bits[0] |= 1L;

            long reach = 0, total = 0, far = -1;
            int farNode = -1;

            for (;;) {
                int p = (int) (cur % nb);
                int idx = nextSetBit(bits, words, p);
                if (idx < 0) break;
                int offset = idx - p;
                if (offset < 0) offset += nb;
                cur += offset;
                int d = (int) cur;

                int n = bsize[idx];
                int[] bk = buckets[idx];
                for (int c = n - 1; c >= 0; c--) {
                    int u = bk[c];
                    if (dist[u] != d) continue;

                    reach++;
                    total += d;
                    if (d > far) {
                        far = d;
                        farNode = u;
                    } else if (d == far && u < farNode) {
                        farNode = u;
                    }

                    for (int e = off[u], end = off[u + 1]; e < end; e++) {
                        int v = at[e];
                        int w = aw[e];
                        int nd = d + w;
                        if (nd < dist[v]) {
                            dist[v] = nd;
                            int idx2 = idx + w;
                            if (idx2 >= nb) idx2 -= nb;
                            int[] b2 = buckets[idx2];
                            int c2 = bsize[idx2];
                            if (c2 == b2.length) {
                                b2 = Arrays.copyOf(b2, c2 << 1);
                                buckets[idx2] = b2;
                            }
                            b2[c2] = v;
                            bsize[idx2] = c2 + 1;
                            bits[idx2 >> 6] |= 1L << (idx2 & 63);
                        }
                    }
                }
                bsize[idx] = 0;
                bits[idx >> 6] &= ~(1L << (idx & 63));
            }

            out[qi * 5 + 0] = s;
            out[qi * 5 + 1] = reach;
            out[qi * 5 + 2] = total;
            out[qi * 5 + 3] = far;
            out[qi * 5 + 4] = farNode;
        }
    }

    static void runLong(int N, int Q, int[] src, int[] off, int[] at, int[] aw,
                        int maxW, long[] out) {
        final long INF = Long.MAX_VALUE;
        long[] dist = new long[N];

        int nb = maxW + 1;
        if (nb < 2) nb = 2;
        int words = (nb + 63) >> 6;
        long[] bits = new long[words];
        int[][] buckets = new int[nb][];
        int[] bsize = new int[nb];
        for (int i = 0; i < nb; i++) buckets[i] = new int[64];

        for (int qi = 0; qi < Q; qi++) {
            int s = src[qi];
            Arrays.fill(dist, INF);
            for (int i = 0; i < nb; i++) bsize[i] = 0;
            Arrays.fill(bits, 0L);
            long cur = 0;
            dist[s] = 0;
            buckets[0][0] = s;
            bsize[0] = 1;
            bits[0] |= 1L;

            long reach = 0, total = 0, far = -1;
            int farNode = -1;

            for (;;) {
                int p = (int) (cur % nb);
                int idx = nextSetBit(bits, words, p);
                if (idx < 0) break;
                int offset = idx - p;
                if (offset < 0) offset += nb;
                cur += offset;
                long d = cur;

                int n = bsize[idx];
                int[] bk = buckets[idx];
                for (int c = n - 1; c >= 0; c--) {
                    int u = bk[c];
                    if (dist[u] != d) continue;

                    reach++;
                    total += d;
                    if (d > far) {
                        far = d;
                        farNode = u;
                    } else if (d == far && u < farNode) {
                        farNode = u;
                    }

                    for (int e = off[u], end = off[u + 1]; e < end; e++) {
                        int v = at[e];
                        int w = aw[e];
                        long nd = d + w;
                        if (nd < dist[v]) {
                            dist[v] = nd;
                            int idx2 = idx + w;
                            if (idx2 >= nb) idx2 -= nb;
                            int[] b2 = buckets[idx2];
                            int c2 = bsize[idx2];
                            if (c2 == b2.length) {
                                b2 = Arrays.copyOf(b2, c2 << 1);
                                buckets[idx2] = b2;
                            }
                            b2[c2] = v;
                            bsize[idx2] = c2 + 1;
                            bits[idx2 >> 6] |= 1L << (idx2 & 63);
                        }
                    }
                }
                bsize[idx] = 0;
                bits[idx >> 6] &= ~(1L << (idx & 63));
            }

            out[qi * 5 + 0] = s;
            out[qi * 5 + 1] = reach;
            out[qi * 5 + 2] = total;
            out[qi * 5 + 3] = far;
            out[qi * 5 + 4] = farNode;
        }
    }

    public static void main(String[] args) throws Exception {
        try (FileInputStream in = new FileInputStream(Path.of(args[0]).toFile())) {
            int len = (int) in.getChannel().size();
            data = new byte[len + 1];
            int got = 0;
            while (got < len) {
                int r = in.read(data, got, len - got);
                if (r < 0) break;
                got += r;
            }
            data[got] = 0;
        }
        pos = 0;

        int N = nextInt();
        int M = nextInt();
        int Q = nextInt();

        int[] eu = new int[M];
        int[] ev = new int[M];
        int[] ew = new int[M];
        int[] deg = new int[N];
        int maxW = 0;

        for (int i = 0; i < M; i++) {
            int u = nextInt();
            int v = nextInt();
            int w = nextInt();
            eu[i] = u;
            ev[i] = v;
            ew[i] = w;
            deg[u]++;
            deg[v]++;
            if (w > maxW) maxW = w;
        }

        int[] off = new int[N + 1];
        int acc = 0;
        for (int i = 0; i < N; i++) {
            off[i] = acc;
            acc += deg[i];
        }
        off[N] = acc;

        int[] at = new int[acc];
        int[] aw = new int[acc];
        int[] cur = Arrays.copyOf(off, N + 1);
        for (int i = 0; i < M; i++) {
            int u = eu[i], v = ev[i], w = ew[i];
            at[cur[u]] = v;
            aw[cur[u]] = w;
            cur[u]++;
            at[cur[v]] = u;
            aw[cur[v]] = w;
            cur[v]++;
        }

        int[] src = new int[Q];
        for (int i = 0; i < Q; i++) src[i] = nextInt();

        eu = null; ev = null; ew = null; deg = null; cur = null;
        data = null;

        long[] out = new long[Q * 5];
        if ((long) N * maxW < Integer.MAX_VALUE - 1L) {
            runInt(N, Q, src, off, at, aw, maxW, out);
        } else {
            runLong(N, Q, src, off, at, aw, maxW, out);
        }

        StringBuilder sb = new StringBuilder(256);
        for (int qi = 0; qi < Q; qi++) {
            sb.append(out[qi * 5]).append(' ')
              .append(out[qi * 5 + 1]).append(' ')
              .append(out[qi * 5 + 2]).append(' ')
              .append(out[qi * 5 + 3]).append(' ')
              .append(out[qi * 5 + 4]).append('\n');
        }
        System.out.print(sb);
    }
}
