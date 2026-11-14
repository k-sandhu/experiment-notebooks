import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.Arrays;

public class Main {
    static int pos;
    static int parseInt(byte[] b) {
        int n = b.length;
        while (pos < n && (b[pos] < '0' || b[pos] > '9')) pos++;
        int v = 0;
        while (pos < n && b[pos] >= '0' && b[pos] <= '9') { v = v * 10 + (b[pos] - '0'); pos++; }
        return v;
    }
    public static void main(String[] args) throws Exception {
        byte[] buf = Files.readAllBytes(Paths.get(args[0]));
        pos = 0;
        if (buf.length == 0) return;
        int N = parseInt(buf), M = parseInt(buf), Q = parseInt(buf);
        int[] eu = new int[M], ev = new int[M], ew = new int[M];
        int[] deg = new int[N];
        int ecnt = 0;
        for (int i = 0; i < M; i++) {
            int u = parseInt(buf), v = parseInt(buf), w = parseInt(buf);
            if (u == v) continue;
            eu[ecnt] = u; ev[ecnt] = v; ew[ecnt] = w; ecnt++;
            deg[u]++; deg[v]++;
        }
        int[] sources = new int[Q];
        for (int i = 0; i < Q; i++) sources[i] = parseInt(buf);
        buf = null;
        int[] off = new int[N + 1];
        for (int i = 0; i < N; i++) off[i + 1] = off[i] + deg[i];
        int[] adj = new int[off[N]];
        int[] cur = new int[N];
        System.arraycopy(off, 0, cur, 0, N);
        for (int i = 0; i < ecnt; i++) {
            int u = eu[i], v = ev[i], w = ew[i];
            adj[cur[u]++] = (v << 10) | w;
            adj[cur[v]++] = (u << 10) | w;
        }
        eu = null; ev = null; ew = null; deg = null; cur = null;

        final int INF = 0x3f3f3f3f;
        int[] dist = new int[N];
        int[] nxt = new int[N], prv = new int[N];
        byte[] done = new byte[N];
        int[] head = new int[1024];
        long[] words = new long[16];

        StringBuilder out = new StringBuilder(Q * 40);
        int[] cs = new int[64]; long[] cR = new long[64], cTot = new long[64], cFar = new long[64]; int[] cNode = new int[64]; int cacheN = 0;

        for (int qi = 0; qi < Q; qi++) {
            int s = sources[qi];
            long R, tot, far; int farNode;
            int ci = -1;
            for (int i = 0; i < cacheN; i++) if (cs[i] == s) { ci = i; break; }
            if (ci >= 0) { R = cR[ci]; tot = cTot[ci]; far = cFar[ci]; farNode = cNode[ci]; }
            else {
                Arrays.fill(dist, INF);
                Arrays.fill(done, (byte)0);
                Arrays.fill(head, -1);
                Arrays.fill(words, 0L);
                dist[s] = 0; head[0] = s; nxt[s] = -1; prv[s] = -1; words[0] = 1L;
                long inq = 1;
                int curDist = 0, curB = 0;
                R = 0; tot = 0; far = 0; farNode = s;
                while (inq > 0) {
                    int node = head[curB];
                    head[curB] = -1;
                    words[curB >> 6] &= ~(1L << (curB & 63));
                    while (node != -1) {
                        int nn = nxt[node];
                        done[node] = 1; inq--;
                        R++; tot += curDist;
                        if (curDist > far) { far = curDist; farNode = node; }
                        else if (curDist == far && node < farNode) farNode = node;
                        int a0 = off[node], a1 = off[node + 1];
                        for (int ai = a0; ai < a1; ai++) {
                            int pk = adj[ai];
                            int v = pk >> 10;
                            if (done[v] != 0) continue;
                            int nd = curDist + (pk & 1023);
                            if (nd < dist[v]) {
                                if (dist[v] != INF) {
                                    int ob = dist[v] & 1023;
                                    int pv = prv[v], nv = nxt[v];
                                    if (pv != -1) nxt[pv] = nv; else head[ob] = nv;
                                    if (nv != -1) prv[nv] = pv;
                                    if (head[ob] == -1) words[ob >> 6] &= ~(1L << (ob & 63));
                                } else inq++;
                                dist[v] = nd;
                                int nb = nd & 1023;
                                int oh = head[nb];
                                nxt[v] = oh; prv[v] = -1;
                                if (oh != -1) prv[oh] = v;
                                else words[nb >> 6] |= (1L << (nb & 63));
                                head[nb] = v;
                            }
                        }
                        node = nn;
                    }
                    if (inq == 0) break;
                    int wi = curB >> 6, bi = curB & 63;
                    int nb = -1;
                    long w0 = (bi == 63) ? 0L : (words[wi] & (~0L << (bi + 1)));
                    if (w0 != 0) nb = (wi << 6) + Long.numberOfTrailingZeros(w0);
                    else {
                        for (int k = 1; k < 16; k++) {
                            int idx = (wi + k) & 15;
                            long w = words[idx];
                            if (w != 0) { nb = (idx << 6) + Long.numberOfTrailingZeros(w); break; }
                        }
                        if (nb == -1) {
                            long low = (bi == 63) ? ~0L : ((1L << (bi + 1)) - 1L);
                            long w = words[wi] & low;
                            if (w != 0) nb = (wi << 6) + Long.numberOfTrailingZeros(w);
                        }
                    }
                    int offd = nb - curB; if (offd <= 0) offd += 1024;
                    curDist += offd; curB = nb;
                }
                if (cacheN < 64) { cs[cacheN] = s; cR[cacheN] = R; cTot[cacheN] = tot; cFar[cacheN] = far; cNode[cacheN] = farNode; cacheN++; }
            }
            out.append(s).append(' ').append(R).append(' ').append(tot).append(' ').append(far).append(' ').append(farNode).append('\n');
        }
        System.out.print(out.toString());
    }
}
