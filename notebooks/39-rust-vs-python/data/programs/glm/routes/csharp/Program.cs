using System;
using System.IO;
using System.Runtime.CompilerServices;

class Program
{
    static byte[] data;
    static int ppos = 0;

    static void Main(string[] args)
    {
        data = File.ReadAllBytes(args[0]);

        long nL = Next(), mL = Next(), qL = Next();
        int n = (int)nL, m = (int)mL, q = (int)qL;

        int[] eu = new int[m], ev = new int[m], ew = new int[m];
        for (int i = 0; i < m; i++)
        {
            eu[i] = (int)Next(); ev[i] = (int)Next(); ew[i] = (int)Next();
        }
        int[] src = new int[q];
        for (int i = 0; i < q; i++) src[i] = (int)Next();

        // CSR adjacency (skip self-loops)
        int[] off = new int[n + 1];
        for (int i = 0; i < m; i++)
        {
            if (eu[i] != ev[i]) { off[eu[i]]++; off[ev[i]]++; }
        }
        int run = 0;
        for (int v = 0; v < n; v++) { int d = off[v]; off[v] = run; run += d; }
        off[n] = run;
        int[] adj = new int[run], wt = new int[run];
        int[] pos = new int[n];
        Array.Copy(off, pos, n);
        for (int i = 0; i < m; i++)
        {
            int u = eu[i], v = ev[i], w = ew[i];
            if (u == v) continue;
            adj[pos[u]] = v; wt[pos[u]] = w; pos[u]++;
            adj[pos[v]] = u; wt[pos[v]] = w; pos[v]++;
        }

        long INF = long.MaxValue / 4;
        long[] dist = new long[n];
        long[] hd = new long[2L * m + 16];
        int[] hn = new int[2 * m + 16];

        var outStream = Console.OpenStandardOutput();
        byte[] obuf = new byte[1 << 20];
        int opos = 0;

        for (int qi = 0; qi < q; qi++)
        {
            int s = src[qi];
            for (int v = 0; v < n; v++) dist[v] = INF;
            int hsize = 0;
            dist[s] = 0;
            hd[hsize] = 0; hn[hsize] = s; hsize++;
            long total = 0, far = -1, cnt = 0;
            int farNode = s;

            while (hsize > 0)
            {
                long d = hd[0];
                int v = hn[0];
                hsize--;
                hd[0] = hd[hsize]; hn[0] = hn[hsize];
                // reinsert the moved last element (hole method, 4-ary)
                long d0 = hd[hsize]; int v0 = hn[hsize];
                int i = 0;
                while (hsize > 0)
                {
                    int c = 4 * i + 1;
                    int mm = i;
                    long mv = d0;
                    int e = c + 4;
                    if (e > hsize) e = hsize;
                    for (int j = c; j < e; j++)
                    {
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
                int e1 = off[v + 1];
                for (int e = off[v]; e < e1; e++)
                {
                    int to = adj[e];
                    long nd = d + wt[e];
                    if (nd < dist[to])
                    {
                        dist[to] = nd;
                        int j = hsize;
                        hd[j] = nd; hn[j] = to; hsize++;
                        while (j > 0)
                        {
                            int par = (j - 1) >> 2;
                            if (hd[par] <= nd) break;
                            hd[j] = hd[par]; hn[j] = hn[par];
                            j = par;
                        }
                        hd[j] = nd; hn[j] = to;
                    }
                }
            }

            opos = WriteU64(obuf, opos, (ulong)s, (byte)' ');
            opos = WriteU64(obuf, opos, (ulong)cnt, (byte)' ');
            opos = WriteU64(obuf, opos, (ulong)total, (byte)' ');
            opos = WriteU64(obuf, opos, (ulong)far, (byte)' ');
            opos = WriteU64(obuf, opos, (ulong)farNode, (byte)'\n');
            if (opos > (1 << 20) - 64)
            {
                outStream.Write(obuf, 0, opos);
                opos = 0;
            }
        }
        if (opos > 0) outStream.Write(obuf, 0, opos);
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    static long Next()
    {
        byte[] d = data;
        int i = ppos, n = d.Length;
        while (i < n && (d[i] < '0' || d[i] > '9')) i++;
        long v = 0;
        while (i < n && d[i] >= '0' && d[i] <= '9')
        {
            v = v * 10 + (d[i] - '0');
            i++;
        }
        ppos = i;
        return v;
    }

    static int WriteU64(byte[] b, int o, ulong v, byte sep)
    {
        if (v == 0) b[o++] = (byte)'0';
        else
        {
            int n = 0;
            Span<byte> tmp = stackalloc byte[20];
            while (v != 0) { tmp[n++] = (byte)('0' + v % 10); v /= 10; }
            while (n > 0) b[o++] = tmp[--n];
        }
        b[o++] = sep;
        return o;
    }
}
