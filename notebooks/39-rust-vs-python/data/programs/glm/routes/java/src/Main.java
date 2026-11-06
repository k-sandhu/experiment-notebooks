import java.io.FileDescriptor;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;

public class Main {

    public static void main(String[] args) throws IOException {
        byte[] data;
        try (FileInputStream in = new FileInputStream(args[0])) {
            data = in.readAllBytes();
        }

        Parse p = new Parse(data);
        final int n = (int) p.next();
        final int m = (int) p.next();
        final int q = (int) p.next();

        int[] eu = new int[m], ev = new int[m], ew = new int[m];
        for (int i = 0; i < m; i++) {
            eu[i] = (int) p.next();
            ev[i] = (int) p.next();
            ew[i] = (int) p.next();
        }
        int[] src = new int[q];
        for (int i = 0; i < q; i++) src[i] = (int) p.next();

        // CSR adjacency (skip self-loops)
        int[] off = new int[n + 1];
        for (int i = 0; i < m; i++) {
            if (eu[i] != ev[i]) { off[eu[i]]++; off[ev[i]]++; }
        }
        int run = 0;
        for (int v = 0; v < n; v++) { int d = off[v]; off[v] = run; run += d; }
        off[n] = run;
        int[] adj = new int[run], wt = new int[run];
        int[] pos = new int[n];
        System.arraycopy(off, 0, pos, 0, n);
        for (int i = 0; i < m; i++) {
            int u = eu[i], v = ev[i], w = ew[i];
            if (u == v) continue;
            adj[pos[u]] = v; wt[pos[u]] = w; pos[u]++;
            adj[pos[v]] = u; wt[pos[v]] = w; pos[v]++;
        }

        final long INF = Long.MAX_VALUE / 4;
        long[] dist = new long[n];
        long[] hd = new long[2 * m + 16];
        int[] hn = new int[2 * m + 16];

        FileOutputStream out = new FileOutputStream(FileDescriptor.out);
        byte[] obuf = new byte[1 << 20];
        int opos = 0;

        for (int qi = 0; qi < q; qi++) {
            int s = src[qi];
            for (int v = 0; v < n; v++) dist[v] = INF;
            int hsize = 0;
            dist[s] = 0;
            hd[hsize] = 0; hn[hsize] = s; hsize++;
            long total = 0, far = -1;
            long cnt = 0;
            int farNode = s;

            while (hsize > 0) {
                long d = hd[0];
                int v = hn[0];
                hsize--;
                hd[0] = hd[hsize]; hn[0] = hn[hsize];
                // sift down (hole method, 4-ary); reinsert moved last element
                long d0 = hd[hsize]; int v0 = hn[hsize];
                int i = 0;
                while (hsize > 0) {
                    int c = 4 * i + 1;
                    int mm = i;
                    long mv = d0;
                    int e = c + 4;
                    if (e > hsize) e = hsize;
                    for (int j = c; j < e; j++) {
                        if (hd[j] < mv) { mv = hd[j]; mm = j; }
                    }
                    if (mm == i) break;
                    hd[i] = mv; hn[i] = hn[mm];
                    i = mm;
                }
                if (hsize > 0) { hd[i] = d0; hn[i] = v0; }
                if (d != dist[v]) continue;
                cnt++;
                total += d;
                if (d > far || (d == far && v < farNode)) { far = d; farNode = v; }
                int e0 = off[v], e1 = off[v + 1];
                for (int e = e0; e < e1; e++) {
                    int to = adj[e];
                    long nd = d + wt[e];
                    if (nd < dist[to]) {
                        dist[to] = nd;
                        // push
                        int j = hsize;
                        hd[j] = nd; hn[j] = to; hsize++;
                        while (j > 0) {
                            int par = (j - 1) >> 2;
                            if (hd[par] <= nd) break;
                            hd[j] = hd[par]; hn[j] = hn[par];
                            j = par;
                        }
                        hd[j] = nd; hn[j] = to;
                    }
                }
            }

            opos = writeU64(obuf, opos, s, (byte) ' ');
            opos = writeU64(obuf, opos, cnt, (byte) ' ');
            opos = writeU64(obuf, opos, total, (byte) ' ');
            opos = writeU64(obuf, opos, far, (byte) ' ');
            opos = writeU64(obuf, opos, farNode, (byte) '\n');
            if (opos > (1 << 20) - 64) {
                out.write(obuf, 0, opos);
                opos = 0;
            }
        }
        if (opos > 0) out.write(obuf, 0, opos);
        out.flush();
    }

    static int writeU64(byte[] b, int o, long val, byte sep) {
        if (val == 0) { b[o++] = '0'; }
        else {
            int n = 0;
            char[] tmp = new char[20];
            long v = val;
            while (v != 0) { tmp[n++] = (char) ('0' + v % 10); v /= 10; }
            while (n > 0) b[o++] = (byte) tmp[--n];
        }
        b[o++] = sep;
        return o;
    }

    static final class Parse {
        final byte[] d;
        int p = 0;

        Parse(byte[] d) { this.d = d; }

        long next() {
            byte[] d = this.d;
            int i = p, n = d.length;
            while (i < n && (d[i] < '0' || d[i] > '9')) i++;
            long v = 0;
            while (i < n && d[i] >= '0' && d[i] <= '9') {
                v = v * 10 + (d[i] - '0');
                i++;
            }
            p = i;
            return v;
        }
    }
}
