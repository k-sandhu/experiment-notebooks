using System.Text;

static class Program
{
    static byte[] buf;
    static int pos;

    static int ReadInt()
    {
        byte[] b = buf;
        int p = pos;
        while (b[p] < (byte)'0') p++;
        int x = 0;
        while (p < b.Length && b[p] >= (byte)'0') { x = x * 10 + (b[p] - '0'); p++; }
        pos = p;
        return x;
    }

    static void Main(string[] args)
    {
        buf = File.ReadAllBytes(args[0]);
        int n = ReadInt(), m = ReadInt(), q = ReadInt();
        int[] eu = new int[m], ev = new int[m], ew = new int[m];
        int[] start = new int[n + 2];
        for (int i = 0; i < m; i++)
        {
            int u = ReadInt(), v = ReadInt(), w = ReadInt();
            eu[i] = u; ev[i] = v; ew[i] = w;
            if (u != v) { start[u + 2]++; start[v + 2]++; }
        }
        for (int i = 2; i <= n + 1; i++) start[i] += start[i - 1];
        int[] adj = new int[start[n + 1]];
        for (int i = 0; i < m; i++)
        {
            int u = eu[i], v = ev[i], w = ew[i];
            if (u == v) continue;
            adj[start[u + 1]++] = v * 1024 + w;
            adj[start[v + 1]++] = u * 1024 + w;
        }
        const long INF = long.MaxValue;
        long[] dist = new long[n];
        ulong[] h = new ulong[adj.Length + 2];
        var sb = new StringBuilder();
        for (int qi = 0; qi < q; qi++)
        {
            int s = ReadInt();
            Array.Fill(dist, INF);
            int hs = 0;
            dist[s] = 0;
            h[hs++] = (ulong)s;
            while (hs > 0)
            {
                ulong top = h[0];
                ulong last = h[--hs];
                if (hs > 0)
                {
                    int i = 0;
                    for (;;)
                    {
                        int c = 2 * i + 1;
                        if (c >= hs) break;
                        if (c + 1 < hs && h[c + 1] < h[c]) c++;
                        if (h[c] >= last) break;
                        h[i] = h[c];
                        i = c;
                    }
                    h[i] = last;
                }
                int u = (int)(top & 0xffffffffUL);
                long d = (long)(top >> 32);
                if (d != dist[u]) continue;
                for (int e = start[u], ee = start[u + 1]; e < ee; e++)
                {
                    int x = adj[e];
                    int v = x >> 10;
                    long nd = d + (x & 1023);
                    if (nd < dist[v])
                    {
                        dist[v] = nd;
                        ulong key = ((ulong)nd << 32) | (uint)v;
                        int i = hs++;
                        while (i > 0)
                        {
                            int par = (i - 1) >> 1;
                            if (h[par] <= key) break;
                            h[i] = h[par];
                            i = par;
                        }
                        h[i] = key;
                    }
                }
            }
            long total = 0, far = 0, cnt = 0;
            for (int i = 0; i < n; i++)
            {
                long d = dist[i];
                if (d != INF)
                {
                    cnt++;
                    total += d;
                    if (d > far) far = d;
                }
            }
            int node = 0;
            for (int i = 0; i < n; i++) if (dist[i] == far) { node = i; break; }
            sb.Append(s).Append(' ').Append(cnt).Append(' ').Append(total).Append(' ')
              .Append(far).Append(' ').Append(node).Append('\n');
        }
        Console.Out.Write(sb.ToString());
        Console.Out.Flush();
    }
}
