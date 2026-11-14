using System;
using System.IO;
using System.Numerics;
using System.Text;

class Program
{
    static byte[] data;
    static int pos;

    static int NextInt()
    {
        while (data[pos] <= (byte)' ') pos++;
        int x = 0;
        while (data[pos] > (byte)' ')
        {
            x = x * 10 + (data[pos] - '0');
            pos++;
        }
        return x;
    }

    // Monotone circular bucket queue (Dial) with a bitset to skip empty ranges.
    sealed class DialQueue
    {
        public int nb;
        public int words;
        public long cur;
        public ulong[] bits;
        public int[][] buckets;
        public int[] bsize;

        public void Init(int maxW)
        {
            nb = maxW + 1;
            if (nb < 2) nb = 2;
            words = (nb + 63) >> 6;
            bits = new ulong[words];
            buckets = new int[nb][];
            bsize = new int[nb];
            for (int i = 0; i < nb; i++) buckets[i] = new int[64];
        }

        public void Clear()
        {
            for (int i = 0; i < nb; i++) bsize[i] = 0;
            Array.Clear(bits, 0, words);
            cur = 0;
        }

        public void Push(int node, int idx)
        {
            int[] b = buckets[idx];
            int c = bsize[idx];
            if (c == b.Length)
            {
                b = new int[c << 1];
                Array.Copy(buckets[idx], b, c);
                buckets[idx] = b;
            }
            b[c] = node;
            bsize[idx] = c + 1;
            bits[idx >> 6] |= 1UL << (idx & 63);
        }

        public int NextSetBit(int p)
        {
            int wi = p >> 6;
            ulong w = bits[wi] & (~0UL << (p & 63));
            if (w != 0UL) return (wi << 6) + BitOperations.TrailingZeroCount(w);
            for (int i = wi + 1; i < words; i++)
            {
                if (bits[i] != 0UL) return (i << 6) + BitOperations.TrailingZeroCount(bits[i]);
            }
            for (int i = 0; i < wi; i++)
            {
                if (bits[i] != 0UL) return (i << 6) + BitOperations.TrailingZeroCount(bits[i]);
            }
            ulong low = bits[wi] & ((1UL << (p & 63)) - 1);
            if (low != 0UL) return (wi << 6) + BitOperations.TrailingZeroCount(low);
            return -1;
        }
    }

    static void RunInt(int N, int Q, int[] src, int[] off, int[] at, int[] aw,
                       int maxW, long[] output)
    {
        const int INF = int.MaxValue;
        int[] dist = new int[N];
        var dq = new DialQueue();
        dq.Init(maxW);
        int nb = dq.nb;

        for (int qi = 0; qi < Q; qi++)
        {
            int s = src[qi];
            Array.Fill(dist, INF);
            dq.Clear();
            dist[s] = 0;
            dq.Push(s, 0);

            long reach = 0, total = 0, far = -1;
            int farNode = -1;

            for (;;)
            {
                int p = (int)(dq.cur % nb);
                int idx = dq.NextSetBit(p);
                if (idx < 0) break;
                int offset = idx - p;
                if (offset < 0) offset += nb;
                dq.cur += offset;
                int d = (int)dq.cur;

                int[] bk = dq.buckets[idx];
                while (dq.bsize[idx] > 0)
                {
                    int c = dq.bsize[idx] - 1;
                    int u = bk[c];
                    dq.bsize[idx] = c;
                    if (dist[u] != d) continue;

                    reach++;
                    total += d;
                    if (d > far) { far = d; farNode = u; }
                    else if (d == far && u < farNode) farNode = u;

                    int end = off[u + 1];
                    for (int e = off[u]; e < end; e++)
                    {
                        int v = at[e];
                        int w = aw[e];
                        int nd = d + w;
                        if (nd < dist[v])
                        {
                            dist[v] = nd;
                            int idx2 = idx + w;
                            if (idx2 >= nb) idx2 -= nb;
                            dq.Push(v, idx2);
                        }
                    }
                }
                dq.bits[idx >> 6] &= ~(1UL << (idx & 63));
            }

            output[qi * 5 + 0] = s;
            output[qi * 5 + 1] = reach;
            output[qi * 5 + 2] = total;
            output[qi * 5 + 3] = far;
            output[qi * 5 + 4] = farNode;
        }
    }

    static void RunLong(int N, int Q, int[] src, int[] off, int[] at, int[] aw,
                        int maxW, long[] output)
    {
        const long INF = long.MaxValue;
        long[] dist = new long[N];
        var dq = new DialQueue();
        dq.Init(maxW);
        int nb = dq.nb;

        for (int qi = 0; qi < Q; qi++)
        {
            int s = src[qi];
            Array.Fill(dist, INF);
            dq.Clear();
            dist[s] = 0;
            dq.Push(s, 0);

            long reach = 0, total = 0, far = -1;
            int farNode = -1;

            for (;;)
            {
                int p = (int)(dq.cur % nb);
                int idx = dq.NextSetBit(p);
                if (idx < 0) break;
                int offset = idx - p;
                if (offset < 0) offset += nb;
                dq.cur += offset;
                long d = dq.cur;

                int[] bk = dq.buckets[idx];
                while (dq.bsize[idx] > 0)
                {
                    int c = dq.bsize[idx] - 1;
                    int u = bk[c];
                    dq.bsize[idx] = c;
                    if (dist[u] != d) continue;

                    reach++;
                    total += d;
                    if (d > far) { far = d; farNode = u; }
                    else if (d == far && u < farNode) farNode = u;

                    int end = off[u + 1];
                    for (int e = off[u]; e < end; e++)
                    {
                        int v = at[e];
                        int w = aw[e];
                        long nd = d + w;
                        if (nd < dist[v])
                        {
                            dist[v] = nd;
                            int idx2 = idx + w;
                            if (idx2 >= nb) idx2 -= nb;
                            dq.Push(v, idx2);
                        }
                    }
                }
                dq.bits[idx >> 6] &= ~(1UL << (idx & 63));
            }

            output[qi * 5 + 0] = s;
            output[qi * 5 + 1] = reach;
            output[qi * 5 + 2] = total;
            output[qi * 5 + 3] = far;
            output[qi * 5 + 4] = farNode;
        }
    }

    static void Main(string[] args)
    {
        using (var fs = new FileStream(args[0], FileMode.Open, FileAccess.Read))
        {
            int len = (int)fs.Length;
            data = new byte[len + 1];
            int got = 0;
            while (got < len)
            {
                int r = fs.Read(data, got, len - got);
                if (r <= 0) break;
                got += r;
            }
            data[got] = 0;
        }
        pos = 0;

        int N = NextInt();
        int M = NextInt();
        int Q = NextInt();

        int[] eu = new int[M];
        int[] ev = new int[M];
        int[] ew = new int[M];
        int[] deg = new int[N];
        int maxW = 0;

        for (int i = 0; i < M; i++)
        {
            int u = NextInt();
            int v = NextInt();
            int w = NextInt();
            eu[i] = u; ev[i] = v; ew[i] = w;
            deg[u]++;
            deg[v]++;
            if (w > maxW) maxW = w;
        }

        int[] off = new int[N + 1];
        int acc = 0;
        for (int i = 0; i < N; i++)
        {
            off[i] = acc;
            acc += deg[i];
        }
        off[N] = acc;

        int[] at = new int[acc];
        int[] aw = new int[acc];
        int[] cur = new int[N + 1];
        Array.Copy(off, cur, N + 1);
        for (int i = 0; i < M; i++)
        {
            int u = eu[i], v = ev[i], w = ew[i];
            at[cur[u]] = v; aw[cur[u]] = w; cur[u]++;
            at[cur[v]] = u; aw[cur[v]] = w; cur[v]++;
        }

        int[] src = new int[Q];
        for (int i = 0; i < Q; i++) src[i] = NextInt();

        eu = null; ev = null; ew = null; deg = null; cur = null;
        data = null;

        long[] output = new long[Q * 5];
        if ((long)N * maxW < int.MaxValue - 1L)
            RunInt(N, Q, src, off, at, aw, maxW, output);
        else
            RunLong(N, Q, src, off, at, aw, maxW, output);

        var sb = new StringBuilder(256);
        for (int qi = 0; qi < Q; qi++)
        {
            sb.Append(output[qi * 5]).Append(' ')
              .Append(output[qi * 5 + 1]).Append(' ')
              .Append(output[qi * 5 + 2]).Append(' ')
              .Append(output[qi * 5 + 3]).Append(' ')
              .Append(output[qi * 5 + 4]).Append('\n');
        }
        Console.Out.Write(sb);
        Console.Out.Flush();
    }
}
