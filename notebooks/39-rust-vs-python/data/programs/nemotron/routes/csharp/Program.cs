using System;
using System.IO;
using System.Text;

class Program
{
    static byte[] data;
    static int pos;
    static int len;

    static int ReadInt()
    {
        while (pos < len && (data[pos] < '0' || data[pos] > '9')) pos++;
        int x = 0;
        while (pos < len && data[pos] >= '0' && data[pos] <= '9') {
            x = x * 10 + (data[pos] - '0');
            pos++;
        }
        return x;
    }

    static void HeapPush(long[] h, ref int n, long x)
    {
        if (n == h.Length) {
            long[] g = new long[n * 2 + 1];
            Array.Copy(h, 0, g, 0, n);
            h = g;
        }
        int i = n++;
        while (i > 0) {
            int p = (i - 1) / 2;
            if (h[p] <= x) break;
            h[i] = h[p];
            i = p;
        }
        h[i] = x;
    }

    static long HeapPop(long[] h, ref int n)
    {
        long top = h[0];
        long x = h[--n];
        if (n > 0) {
            int i = 0;
            h[0] = x;
            for (;;) {
                int c = 2 * i + 1;
                if (c >= n) break;
                if (c + 1 < n && h[c + 1] < h[c]) c++;
                if (h[c] >= x) break;
                h[i] = h[c];
                i = c;
            }
            h[i] = x;
        }
        return top;
    }

    static void Main(string[] args)
    {
        data = File.ReadAllBytes(args[0]);
        len = data.Length;

        int N = ReadInt();
        int M = ReadInt();
        int Q = ReadInt();

        int[] eu = new int[M];
        int[] ev = new int[M];
        int[] ew = new int[M];
        int[] deg = new int[N];
        for (int i = 0; i < M; i++) {
            int u = ReadInt();
            int v = ReadInt();
            int w = ReadInt();
            eu[i] = u;
            ev[i] = v;
            ew[i] = w;
            deg[u]++;
            deg[v]++;
        }

        int[] off = new int[N + 1];
        for (int i = 0; i < N; i++) off[i + 1] = off[i] + deg[i];
        int[] to = new int[2 * M];
        int[] wt = new int[2 * M];
        int[] cur = new int[N];
        Array.Copy(off, 0, cur, 0, N);
        for (int i = 0; i < M; i++) {
            int u = eu[i];
            int v = ev[i];
            int w = ew[i];
            int p = cur[u]++;
            to[p] = v;
            wt[p] = w;
            int q = cur[v]++;
            to[q] = u;
            wt[q] = w;
        }

        int[] sources = new int[Q];
        for (int i = 0; i < Q; i++) sources[i] = ReadInt();

        int[] dist = new int[N];
        long[] h = new long[Math.Max(M + 1, 1)];
        int hn = 0;
        var sb = new StringBuilder();

        for (int i = 0; i < Q; i++) {
            int s = sources[i];
            Array.Fill(dist, int.MaxValue);
            dist[s] = 0;
            hn = 0;
            HeapPush(h, ref hn, ((long)0 << 32) | (long)(uint)s);

            while (hn > 0) {
                long packed = HeapPop(h, ref hn);
                int d = (int)(packed >> 32);
                int v = (int)(packed & 0xFFFFFFFFL);
                if (d > dist[v]) continue; // stale entry
                int e0 = off[v];
                int e1 = off[v + 1];
                for (int e = e0; e < e1; e++) {
                    int t = to[e];
                    int nd = d + wt[e];
                    if (nd < dist[t]) {
                        dist[t] = nd;
                        HeapPush(h, ref hn, ((long)nd << 32) | (long)(uint)t);
                    }
                }
            }

            long reach = 0;
            long total = 0;
            long far = -1;
            int node = -1;
            for (int v = 0; v < N; v++) {
                int dv = dist[v];
                if (dv != int.MaxValue) {
                    reach++;
                    total += dv;
                    if (dv > far) {
                        far = dv;
                        node = v;
                    }
                }
            }

            sb.Append(s).Append(' ').Append(reach).Append(' ').Append(total).Append(' ').Append(far).Append(' ').Append(node).Append('\n');
        }

        // Write raw bytes so '\n' stays '\n' regardless of console code page.
        byte[] outBytes = Encoding.UTF8.GetBytes(sb.ToString());
        using var stdout = Console.OpenStandardOutput();
        stdout.Write(outBytes, 0, outBytes.Length);
    }
}
