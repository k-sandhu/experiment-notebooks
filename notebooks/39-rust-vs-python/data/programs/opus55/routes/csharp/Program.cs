using System.Numerics;
using System.Runtime.CompilerServices;
using System.Text;

// Routes: Dijkstra from each source with a monotone radix heap on a CSR graph.
static unsafe class Program
{
    // Radix heap: keys are packed (dist << shift) | node, bucketed by the highest bit where dist differs from last.
    static readonly ulong[][] buckets = new ulong[65][];
    static readonly int[] sizes = new int[65];
    static int shift;

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    static void Push(ulong[][] bk, int[] sz, int b, ulong key)
    {
        ulong[] a = bk[b];
        int s = sz[b];
        if ((uint)s >= (uint)a.Length)
        {
            Array.Resize(ref a, s * 2);
            bk[b] = a;
        }
        a[s] = key;
        sz[b] = s + 1;
    }

    static int Main(string[] args)
    {
        byte[] buf = File.ReadAllBytes(args[0]);
        fixed (byte* bp = buf)
        {
            byte* p = bp;
            byte* endp = bp + buf.Length;

            ulong Next()
            {
                while (*p < '0' || *p > '9') p++;
                ulong x = (ulong)(*p++ - '0');
                while (p < endp && (uint)(*p - '0') <= 9) x = x * 10 + (ulong)(*p++ - '0');
                return x;
            }

            int n = (int)Next();
            int m = (int)Next();
            int q = (int)Next();

            int[] eu = new int[m], ev = new int[m], ew = new int[m];
            int[] start = new int[n + 1];
            for (int i = 0; i < m; i++)
            {
                int u = (int)Next(), v = (int)Next(), w = (int)Next();
                eu[i] = u;
                ev[i] = v;
                ew[i] = w;
                if (u != v) // self-loops never shorten a path
                {
                    start[u + 1]++;
                    start[v + 1]++;
                }
            }
            for (int i = 0; i < n; i++) start[i + 1] += start[i];
            // Neighbours of u: adj[2k] (node), adj[2k+1] (length) for k in start[u]..start[u+1).
            int[] adj = new int[2 * start[n]];
            int[] fill = new int[n];
            Array.Copy(start, fill, n);
            for (int i = 0; i < m; i++)
            {
                int u = eu[i], v = ev[i], w = ew[i];
                if (u == v) continue;
                int pu = fill[u]++ << 1;
                adj[pu] = v;
                adj[pu + 1] = w;
                int pv = fill[v]++ << 1;
                adj[pv] = u;
                adj[pv + 1] = w;
            }
            eu = ev = ew = fill = null;

            shift = n > 1 ? 32 - BitOperations.LeadingZeroCount((uint)(n - 1)) : 0;
            for (int i = 0; i < 65; i++) buckets[i] = new ulong[1024];
            ulong[] dist = new ulong[n];
            var sb = new StringBuilder();
            for (int i = 0; i < q; i++)
            {
                int s = (int)Next();
                Solve(s, start, adj, dist, sb);
            }
            using var stdout = Console.OpenStandardOutput();
            stdout.Write(Encoding.ASCII.GetBytes(sb.ToString()));
        }
        return 0;
    }

    [MethodImpl(MethodImplOptions.AggressiveOptimization)]
    static void Solve(int s, int[] start, int[] adj, ulong[] dist, StringBuilder sb)
    {
        int sh = shift;
        ulong mask = (1UL << sh) - 1;
        ulong[][] bk = buckets;
        int[] sz = sizes;
        Array.Fill(dist, ulong.MaxValue);
        Array.Clear(sz);
        ulong last = 0;
        int heapSize = 1;
        dist[s] = 0;
        Push(bk, sz, 0, (ulong)s);
        long reach = 0;
        ulong total = 0, far = 0;
        int farNode = s;
        fixed (int* ap = adj)
        fixed (int* stp = start)
        fixed (ulong* dp = dist)
        {
            while (heapSize > 0)
            {
                if (sz[0] == 0)
                {
                    int i = 1;
                    while (sz[i] == 0) i++;
                    ulong[] a = bk[i];
                    int cnt = sz[i];
                    ulong mn = ulong.MaxValue;
                    for (int j = 0; j < cnt; j++) if (a[j] < mn) mn = a[j];
                    last = mn >> sh;
                    sz[i] = 0;
                    for (int j = 0; j < cnt; j++)
                    {
                        ulong k = a[j];
                        ulong dk = k >> sh;
                        Push(bk, sz, dk == last ? 0 : 64 - BitOperations.LeadingZeroCount(dk ^ last), k);
                    }
                }
                heapSize--;
                ulong key = bk[0][--sz[0]];
                ulong d = key >> sh;
                int u = (int)(key & mask);
                if (d != dp[u]) continue;
                reach++;
                total += d;
                if (d > far)
                {
                    far = d;
                    farNode = u;
                }
                else if (d == far && u < farNode)
                {
                    farNode = u;
                }
                int* e = ap + ((long)stp[u] << 1);
                int* end = ap + ((long)stp[u + 1] << 1);
                for (; e < end; e += 2)
                {
                    int v = e[0];
                    ulong nd = d + (uint)e[1];
                    if (nd < dp[v])
                    {
                        dp[v] = nd;
                        Push(bk, sz, nd == last ? 0 : 64 - BitOperations.LeadingZeroCount(nd ^ last), (nd << sh) | (uint)v);
                        heapSize++;
                    }
                }
            }
        }
        sb.Append(s).Append(' ').Append(reach).Append(' ').Append(total).Append(' ')
          .Append(far).Append(' ').Append(farNode).Append('\n');
    }
}
