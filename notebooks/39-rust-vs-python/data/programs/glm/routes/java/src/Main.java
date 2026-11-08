import java.io.*;
import java.nio.file.*;

public class Main {
    private static byte[] buf;
    private static int pos;

    private static int readInt() {
        while (buf[pos] < '0' || buf[pos] > '9') pos++;
        int x = 0;
        while (buf[pos] >= '0' && buf[pos] <= '9') x = x * 10 + (buf[pos++] - '0');
        return x;
    }

    public static void main(String[] args) throws IOException {
        buf = Files.readAllBytes(Paths.get(args[0]));
        int n = readInt(), m = readInt(), q = readInt();

        int[] eu = new int[m], ev = new int[m], ew = new int[m];
        int[] start = new int[n + 1];
        for (int i = 0; i < m; i++) {
            int u = readInt(), v = readInt(), w = readInt();
            eu[i] = u; ev[i] = v; ew[i] = w;
            start[u + 1]++; start[v + 1]++;
        }
        for (int i = 0; i < n; i++) start[i + 1] += start[i];
        int e2 = start[n];
        int[] adjV = new int[e2], adjW = new int[e2];
        int[] posArr = new int[n];
        System.arraycopy(start, 0, posArr, 0, n);
        for (int i = 0; i < m; i++) {
            adjV[posArr[eu[i]]] = ev[i]; adjW[posArr[eu[i]]] = ew[i]; posArr[eu[i]]++;
            adjV[posArr[ev[i]]] = eu[i]; adjW[posArr[ev[i]]] = ew[i]; posArr[ev[i]]++;
        }

        // Dial's bucket queue: weights are 1..1000, so a circular array of 1001
        // buckets (singly linked lists through the arena array) holds all
        // pending distances. Stale entries are skipped via the dist check.
        final int nb = 1001;
        int[] arena = new int[2 * m + 2];
        int[] nextIn = new int[2 * m + 2];
        int[] head = new int[nb];

        int[] dist = new int[n];
        byte[] settled = new byte[n];
        byte[] out = new byte[q * 80 + 16];
        int op = 0;

        for (int qi = 0; qi < q; qi++) {
            int s = readInt();
            java.util.Arrays.fill(dist, -1);
            java.util.Arrays.fill(settled, (byte) 0);
            java.util.Arrays.fill(head, -1);
            int cnt = 0;
            dist[s] = 0;
            arena[cnt] = s; nextIn[cnt] = -1; head[0] = cnt; cnt++;
            int remaining = 1;
            int idx = 0;
            int d = 0;
            while (remaining > 0) {
                int e = head[idx];
                if (e < 0) { idx = idx + 1 == nb ? 0 : idx + 1; d++; continue; }
                head[idx] = nextIn[e];
                remaining--;
                int v = arena[e];
                if (settled[v] != 0 || dist[v] != d) continue;
                settled[v] = 1;
                int end = start[v + 1];
                for (int i = start[v]; i < end; i++) {
                    int u = adjV[i];
                    if (settled[u] != 0) continue;
                    int nd = d + adjW[i];
                    int du = dist[u];
                    if (du < 0 || nd < du) {
                        dist[u] = nd;
                        int b = nd % nb;
                        arena[cnt] = u; nextIn[cnt] = head[b]; head[b] = cnt; cnt++;
                        remaining++;
                    }
                }
            }
            long total = 0;
            int far = 0;
            int farNode = s;
            int r = 0;
            for (int v = 0; v < n; v++) {
                int dd = dist[v];
                if (dd >= 0) {
                    r++;
                    total += dd;
                    if (dd > far || (dd == far && v < farNode)) { far = dd; farNode = v; }
                }
            }
            op = putLong(out, op, s); out[op++] = ' ';
            op = putLong(out, op, r); out[op++] = ' ';
            op = putLong(out, op, total); out[op++] = ' ';
            op = putLong(out, op, far); out[op++] = ' ';
            op = putLong(out, op, farNode); out[op++] = '\n';
        }
        System.out.write(out, 0, op);
        System.out.flush();
    }

    private static int putLong(byte[] out, int op, long x) {
        if (x == 0) { out[op++] = '0'; return op; }
        int t = op;
        while (x > 0) { out[op++] = (byte) ('0' + (int) (x % 10)); x /= 10; }
        for (int a = t, b = op - 1; a < b; a++, b--) {
            byte tmp = out[a]; out[a] = out[b]; out[b] = tmp;
        }
        return op;
    }
}
