import java.io.*;
import java.nio.file.*;
import java.util.Arrays;

public class Main {
    static byte[] data;
    static int pos;

    static int nextInt() {
        byte[] d = data;
        int p = pos;
        int n = d.length;
        while (p < n && d[p] <= ' ') p++;
        if (p >= n) { pos = p; return 0; }
        boolean neg = false;
        if (d[p] == '-') { neg = true; p++; }
        int v = 0;
        while (p < n && d[p] >= '0' && d[p] <= '9') {
            v = v * 10 + (d[p] - '0');
            p++;
        }
        pos = p;
        return neg ? -v : v;
    }

    public static void main(String[] args) throws Exception {
        if (args.length < 1) return;
        data = Files.readAllBytes(Path.of(args[0]));
        pos = 0;
        int N = nextInt();
        int M = nextInt();
        int Q = nextInt();
        if (N < 0) N = 0;
        if (M < 0) M = 0;
        if (Q < 0) Q = 0;

        int[] eu = new int[M];
        int[] ev = new int[M];
        int[] ew = new int[M];
        int[] deg = new int[N];
        int mStored = 0;
        int wmax = 0;
        for (int i = 0; i < M; i++) {
            int u = nextInt(), v = nextInt(), w = nextInt();
            if (u == v) continue;
            if (u < 0 || u >= N || v < 0 || v >= N) continue;
            eu[mStored] = u; ev[mStored] = v; ew[mStored] = w;
            mStored++;
            deg[u]++; deg[v]++;
            if (w > wmax) wmax = w;
        }
        int[] sources = new int[Q];
        for (int i = 0; i < Q; i++) sources[i] = nextInt();
        data = null;

        int[] off = new int[N + 1];
        for (int i = 0; i < N; i++) off[i + 1] = off[i] + deg[i];
        int E = off[N];
        int[] adjTo = new int[E];
        int[] adjW = new int[E];
        int[] cursor = Arrays.copyOf(off, N);
        for (int i = 0; i < mStored; i++) {
            int u = eu[i], v = ev[i], w = ew[i];
            int a = cursor[u]++; adjTo[a] = v; adjW[a] = w;
            int b = cursor[v]++; adjTo[b] = u; adjW[b] = w;
        }
        eu = null; ev = null; ew = null; deg = null; cursor = null;

        final int B = wmax > 0 ? wmax + 1 : 1;
        final int WORDS = (B + 63) >> 6;
        long[] dist = new long[N];
        int[] head = new int[B];
        long[] bits = new long[WORDS];
        int cap = Math.max(1024, N * 2);
        int[] eNode = new int[cap];
        int[] eNext = new int[cap];
        final long INF = (long) 4e18;

        StringBuilder out = new StringBuilder(Q * 48);
        int[] doneSrc = new int[Q];
        String[] doneLine = new String[Q];
        int doneCnt = 0;

        for (int qi = 0; qi < Q; qi++) {
            int s = sources[qi];
            boolean dup = false;
            for (int k = 0; k < doneCnt; k++) {
                if (doneSrc[k] == s) { out.append(doneLine[k]); dup = true; break; }
            }
            if (dup) continue;

            long R = 0, total = 0, far = 0;
            int farNode = s;

            if (s >= 0 && s < N) {
                Arrays.fill(dist, INF);
                Arrays.fill(head, -1);
                Arrays.fill(bits, 0L);
                int poolSize = 0;
                int nonEmpty = 0;
                dist[s] = 0;
                // push s, bucket 0
                {
                    if (poolSize == eNode.length) {
                        int nc = eNode.length * 2;
                        eNode = Arrays.copyOf(eNode, nc);
                        eNext = Arrays.copyOf(eNext, nc);
                    }
                    int idx = poolSize++;
                    eNode[idx] = s;
                    eNext[idx] = head[0];
                    if (head[0] == -1) { bits[0] |= 1L; nonEmpty++; }
                    head[0] = idx;
                }
                int curBucket = 0;
                long curDist = 0;
                while (true) {
                    if (head[curBucket] == -1) {
                        if (nonEmpty == 0) break;
                        int wi = curBucket >> 6;
                        int bi = curBucket & 63;
                        int posB = -1;
                        long w = 0;
                        if (bi < 63) w = bits[wi] & (~0L << (bi + 1));
                        if (w != 0) {
                            posB = (wi << 6) + Long.numberOfTrailingZeros(w);
                        } else {
                            for (int step = 1; step <= WORDS; step++) {
                                int idxw = wi + step;
                                if (idxw >= WORDS) idxw -= WORDS;
                                long ww = bits[idxw];
                                if (ww != 0) { posB = (idxw << 6) + Long.numberOfTrailingZeros(ww); break; }
                            }
                        }
                        if (posB < 0) break;
                        int delta = posB > curBucket ? (posB - curBucket) : (posB - curBucket + B);
                        curDist += delta;
                        curBucket = posB;
                    }
                    int eidx = head[curBucket];
                    int u = eNode[eidx];
                    int nxt = eNext[eidx];
                    head[curBucket] = nxt;
                    if (nxt == -1) {
                        bits[curBucket >> 6] &= ~(1L << (curBucket & 63));
                        nonEmpty--;
                    }
                    if (dist[u] != curDist) continue;
                    R++;
                    total += curDist;
                    if (curDist > far) { far = curDist; farNode = u; }
                    else if (curDist == far && u < farNode) farNode = u;

                    int begin = off[u];
                    int end = off[u + 1];
                    for (int ei = begin; ei < end; ei++) {
                        int to = adjTo[ei];
                        int wgt = adjW[ei];
                        long nd = curDist + wgt;
                        if (nd < dist[to]) {
                            dist[to] = nd;
                            int b = curBucket + wgt;
                            if (b >= B) b -= B;
                            if (poolSize == eNode.length) {
                                int nc = eNode.length * 2;
                                eNode = Arrays.copyOf(eNode, nc);
                                eNext = Arrays.copyOf(eNext, nc);
                            }
                            int idx = poolSize++;
                            eNode[idx] = to;
                            int h = head[b];
                            eNext[idx] = h;
                            if (h == -1) { bits[b >> 6] |= (1L << (b & 63)); nonEmpty++; }
                            head[b] = idx;
                        }
                    }
                }
            }
            String line = s + " " + R + " " + total + " " + far + " " + farNode + "\n";
            out.append(line);
            doneSrc[doneCnt] = s;
            doneLine[doneCnt] = line;
            doneCnt++;
        }
        BufferedOutputStream bos = new BufferedOutputStream(System.out);
        bos.write(out.toString().getBytes());
        bos.flush();
    }
}
