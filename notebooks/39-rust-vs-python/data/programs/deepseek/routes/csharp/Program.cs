using System;
using System.IO;
using System.Text;

class Program
{
    static byte[] data;
    static int pos;

    static int NextInt()
    {
        byte[] a = data;
        int n = a.Length;
        int i = pos;
        while (i < n)
        {
            int c = a[i] - 48;
            if (c >= 0 && c <= 9) break;
            ++i;
        }
        int x = 0;
        while (i < n)
        {
            int c = a[i] - 48;
            if (c < 0 || c > 9) break;
            x = x * 10 + c;
            ++i;
        }
        pos = i;
        return x;
    }

    static long[] heap;
    static int heapSize;

    static void HeapPush(long x)
    {
        long[] h = heap;
        int i = heapSize++;
        while (i > 0)
        {
            int p = (i - 1) >> 1;
            if (h[p] <= x) break;
            h[i] = h[p];
            i = p;
        }
        h[i] = x;
    }

    static long HeapPop()
    {
        long[] h = heap;
        long top = h[0];
        long x = h[--heapSize];
        int n = heapSize;
        if (n > 0)
        {
            int i = 0;
            for (;;)
            {
                int c = (i << 1) + 1;
                if (c >= n) break;
                if (c + 1 < n && h[c + 1] < h[c]) ++c;
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

        int N = NextInt();
        int M = NextInt();
        int Q = NextInt();

        int[] eu = new int[M];
        int[] ev = new int[M];
        int[] ew = new int[M];
        int[] deg = new int[N + 1];
        for (int i = 0; i < M; ++i)
        {
            int u = NextInt(), v = NextInt(), w = NextInt();
            eu[i] = u; ev[i] = v; ew[i] = w;
            ++deg[u]; ++deg[v];
        }
        int[] src = new int[Q];
        for (int i = 0; i < Q; ++i) src[i] = NextInt();

        int[] off = new int[N + 1];
        int acc = 0;
        for (int i = 0; i < N; ++i) { off[i] = acc; acc += deg[i]; }
        off[N] = acc;

        int[] fill = (int[])off.Clone();
        int[] adj = new int[2 * M];
        for (int i = 0; i < M; ++i)
        {
            int u = eu[i], v = ev[i], w = ew[i];
            int p = fill[u]++; adj[p] = (v << 10) | w;
            p = fill[v]++; adj[p] = (u << 10) | w;
        }
        eu = null; ev = null; ew = null; deg = null; fill = null;

        const int INF = 0x3f3f3f3f;
        int[] dist = new int[N];

        int shift = 0;
        while ((1L << shift) < (long)N) ++shift;
        long mask = (1L << shift) - 1L;

        heap = new long[2 * M + 16];

        var outSb = new StringBuilder(256);

        for (int qi = 0; qi < Q; ++qi)
        {
            int s = src[qi];
            Array.Fill(dist, INF);
            heapSize = 0;
            dist[s] = 0;
            HeapPush(s);

            long total = 0;
            int reach = 0;
            int far = 0;
            int farNode = s;

            while (heapSize > 0)
            {
                long key = HeapPop();
                int v = (int)(key & mask);
                int d = (int)(key >> shift);
                if (d != dist[v]) continue;

                ++reach;
                total += d;
                if (d > far) { far = d; farNode = v; }

                int end = off[v + 1];
                for (int e = off[v]; e < end; ++e)
                {
                    uint a = (uint)adj[e];
                    int u = (int)(a >> 10);
                    int nd = d + (int)(a & 1023);
                    if (nd < dist[u])
                    {
                        dist[u] = nd;
                        HeapPush(((long)nd << shift) | (long)u);
                    }
                }
            }

            outSb.Append(s).Append(' ').Append(reach).Append(' ').Append(total)
                 .Append(' ').Append(far).Append(' ').Append(farNode).Append('\n');
        }
        Console.Out.Write(outSb.ToString());
    }
}
