using System.Numerics;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using System.Text;

static unsafe class Program
{
    struct Bucket
    {
        public int* Ptr;
        public int Cnt;
        public int Cap;
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    static byte* Next(byte* p, byte* end, out int value)
    {
        while (p < end && (uint)(*p - '0') > 9u) p++;
        int x = 0;
        uint c;
        while ((c = (uint)(*p - '0')) <= 9u)
        {
            x = x * 10 + (int)c;
            p++;
        }
        value = x;
        return p;
    }

    static byte[] ReadFile(string path, out int len)
    {
        using (var fs = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read, 1, FileOptions.SequentialScan))
        {
            int total = (int)fs.Length;
            byte[] buf = GC.AllocateUninitializedArray<byte>(total + 1);
            int got = 0;
            while (got < total)
            {
                int r = fs.Read(buf, got, total - got);
                if (r <= 0) break;
                got += r;
            }
            buf[got] = 0;
            len = got;
            return buf;
        }
    }

    static int Main(string[] args)
    {
        byte[] buf = ReadFile(args[0], out int len);
        var sb = new StringBuilder(512);
        Solve(buf, len, sb);
        byte[] bytes = Encoding.ASCII.GetBytes(sb.ToString());
        using (var o = Console.OpenStandardOutput())
        {
            o.Write(bytes, 0, bytes.Length);
            o.Flush();
        }
        return 0;
    }

    [MethodImpl(MethodImplOptions.AggressiveOptimization)]
    static void Solve(byte[] buf, int len, StringBuilder sb)
    {
        int n, m, q;
        int[] off, eu, ev, ew, src;
        int cnt = 0;
        int maxW = 0, minW = int.MaxValue;

        fixed (byte* bp = buf)
        {
            byte* p = bp;
            byte* end = bp + len;
            p = Next(p, end, out n);
            p = Next(p, end, out m);
            p = Next(p, end, out q);

            off = new int[n + 2];
            eu = GC.AllocateUninitializedArray<int>(m);
            ev = GC.AllocateUninitializedArray<int>(m);
            ew = GC.AllocateUninitializedArray<int>(m);

            for (int i = 0; i < m; i++)
            {
                p = Next(p, end, out int u);
                p = Next(p, end, out int v);
                p = Next(p, end, out int w);
                if (u == v) continue;
                eu[cnt] = u;
                ev[cnt] = v;
                ew[cnt] = w;
                cnt++;
                off[u + 2]++;
                off[v + 2]++;
                if (w > maxW) maxW = w;
                if (w < minW) minW = w;
            }

            src = new int[q];
            for (int i = 0; i < q; i++)
            {
                p = Next(p, end, out int s);
                src[i] = s;
            }
        }

        for (int i = 2; i <= n + 1; i++) off[i] += off[i - 1];

        bool fast = n <= (1 << 21) && (cnt == 0 || (minW >= 1 && maxW <= 1023));

        if (fast)
        {
            uint[] adj = GC.AllocateUninitializedArray<uint>(2 * cnt);
            for (int i = 0; i < cnt; i++)
            {
                int u = eu[i], v = ev[i], w = ew[i];
                adj[off[u + 1]++] = (uint)((v << 10) | w);
                adj[off[v + 1]++] = (uint)((u << 10) | w);
            }
            RunFast(n, off, adj, src, sb);
        }
        else
        {
            int[] adjV = new int[2 * cnt];
            int[] adjW = new int[2 * cnt];
            for (int i = 0; i < cnt; i++)
            {
                int u = eu[i], v = ev[i], w = ew[i];
                int a = off[u + 1]++;
                adjV[a] = v; adjW[a] = w;
                int b = off[v + 1]++;
                adjV[b] = u; adjW[b] = w;
            }
            RunSlow(n, off, adjV, adjW, src, sb);
        }
    }

    [MethodImpl(MethodImplOptions.NoInlining)]
    static void Grow(Bucket* t)
    {
        int nc = t->Cap == 0 ? 64 : t->Cap * 2;
        t->Ptr = (int*)NativeMemory.Realloc(t->Ptr, (nuint)nc * 4);
        t->Cap = nc;
    }

    [MethodImpl(MethodImplOptions.AggressiveOptimization)]
    static void RunFast(int n, int[] offArr, uint[] adjArr, int[] src, StringBuilder sb)
    {
        int[] distArr = new int[Math.Max(n, 1)];
        Bucket* bk = (Bucket*)NativeMemory.AllocZeroed(1024, (nuint)sizeof(Bucket));
        ulong* bm = stackalloc ulong[16];
        for (int i = 0; i < 16; i++) bm[i] = 0;

        fixed (int* off = offArr)
        fixed (uint* adj = adjArr)
        fixed (int* dist = distArr)
        {
            for (int si = 0; si < src.Length; si++)
            {
                int s = src[si];
                new Span<int>(dist, n).Fill(int.MaxValue);
                dist[s] = 0;

                {
                    Bucket* t0 = bk;
                    if (t0->Cap == 0) Grow(t0);
                    t0->Ptr[0] = s;
                    t0->Cnt = 1;
                    bm[0] |= 1UL;
                }

                long total = 0;
                int reach = 0;
                int far = 0;
                int node = s;
                int d = 0;
                int b = 0;

                while (true)
                {
                    Bucket* cb = bk + b;
                    int* arr = cb->Ptr;
                    int c0 = cb->Cnt;
                    cb->Cnt = 0;
                    bm[b >> 6] &= ~(1UL << b);

                    int valid = 0;
                    int minNode = int.MaxValue;
                    for (int i = 0; i < c0; i++)
                    {
                        int u = arr[i];
                        if (dist[u] != d) continue;
                        valid++;
                        if (u < minNode) minNode = u;
                        uint* e = adj + off[u];
                        uint* ee = adj + off[u + 1];
                        for (; e < ee; e++)
                        {
                            uint x = *e;
                            int v = (int)(x >> 10);
                            int nd = d + (int)(x & 1023u);
                            if (nd < dist[v])
                            {
                                dist[v] = nd;
                                int nb = nd & 1023;
                                Bucket* t = bk + nb;
                                int c = t->Cnt;
                                if (c == t->Cap) Grow(t);
                                t->Ptr[c] = v;
                                t->Cnt = c + 1;
                                bm[nb >> 6] |= 1UL << nb;
                            }
                        }
                    }

                    if (valid > 0)
                    {
                        reach += valid;
                        total += (long)d * valid;
                        far = d;
                        node = minNode;
                    }

                    int idx = -1;
                    int wi = b >> 6;
                    ulong mk = bm[wi] & (~0UL << b);
                    if (mk != 0)
                    {
                        idx = (wi << 6) + BitOperations.TrailingZeroCount(mk);
                    }
                    else
                    {
                        for (int k = 1; k <= 16; k++)
                        {
                            int w2 = (wi + k) & 15;
                            ulong m2 = bm[w2];
                            if (m2 != 0)
                            {
                                idx = (w2 << 6) + BitOperations.TrailingZeroCount(m2);
                                break;
                            }
                        }
                    }
                    if (idx < 0) break;
                    d += (idx - b) & 1023;
                    b = idx;
                }

                sb.Append(s).Append(' ').Append(reach).Append(' ').Append(total).Append(' ').Append(far).Append(' ').Append(node).Append('\n');
            }
        }

        for (int i = 0; i < 1024; i++)
        {
            if (bk[i].Ptr != null) NativeMemory.Free(bk[i].Ptr);
        }
        NativeMemory.Free(bk);
    }

    [MethodImpl(MethodImplOptions.AggressiveOptimization)]
    static void RunSlow(int n, int[] off, int[] adjV, int[] adjW, int[] src, StringBuilder sb)
    {
        long[] dist = new long[Math.Max(n, 1)];
        var pq = new PriorityQueue<int, long>();
        for (int si = 0; si < src.Length; si++)
        {
            int s = src[si];
            Array.Fill(dist, long.MaxValue);
            dist[s] = 0;
            pq.Enqueue(s, 0);
            long total = 0;
            long reach = 0;
            long far = -1;
            int node = s;
            while (pq.TryDequeue(out int u, out long du))
            {
                if (du != dist[u]) continue;
                reach++;
                total += du;
                if (du > far) { far = du; node = u; }
                else if (u < node) node = u;
                int e1 = off[u + 1];
                for (int e = off[u]; e < e1; e++)
                {
                    int v = adjV[e];
                    long nd = du + adjW[e];
                    if (nd < dist[v])
                    {
                        dist[v] = nd;
                        pq.Enqueue(v, nd);
                    }
                }
            }
            sb.Append(s).Append(' ').Append(reach).Append(' ').Append(total).Append(' ').Append(far).Append(' ').Append(node).Append('\n');
        }
    }
}
