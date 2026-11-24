using System;
using System.IO;
using System.Numerics;
using System.Runtime.CompilerServices;
using System.Text;

sealed class Scanner
{
    public byte[] Data;
    public int Pos;
    public Scanner(string path) { Data = File.ReadAllBytes(path); }
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public int Read()
    {
        byte[] data = Data;
        int p = Pos;
        while (data[p] <= 32) ++p;
        int x = 0;
        do { x = x * 10 + data[p++] - 48; }
        while (p < data.Length && data[p] >= 48 && data[p] <= 57);
        Pos = p;
        return x;
    }
}

// Queued distances span at most 1,000. Bitmap searches skip empty buckets.
sealed class BucketQueue
{
    readonly int[] head = new int[1024];
    readonly uint[] bits = new uint[32];
    public readonly int[] Next, Prev;
    public uint Summary;
    int current;
    public BucketQueue(int n) { Next = new int[n]; Prev = new int[n]; }
    public void Reset()
    {
        Array.Fill(head, -1); Array.Clear(bits); Summary = 0; current = 0;
    }
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public void Insert(int v, int b)
    {
        int h = head[b]; Next[v] = h; Prev[v] = -1;
        if (h >= 0) Prev[h] = v;
        else { bits[b >> 5] |= 1u << (b & 31); Summary |= 1u << (b >> 5); }
        head[b] = v;
    }
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public void Remove(int v, int b)
    {
        int p = Prev[v], n = Next[v];
        if (p >= 0) Next[p] = n; else head[b] = n;
        if (n >= 0) Prev[n] = p;
        if (head[b] < 0)
        {
            int g = b >> 5;
            bits[g] &= ~(1u << (b & 31));
            if (bits[g] == 0) Summary &= ~(1u << g);
        }
    }
    public int Pop()
    {
        int b = current;
        if (head[b] < 0)
        {
            int g = b >> 5;
            uint word = bits[g] & (uint.MaxValue << (b & 31));
            if (word == 0)
            {
                uint groups = Summary & (0xfffffffeu << g);
                if (groups == 0) groups = Summary;
                g = BitOperations.TrailingZeroCount(groups); word = bits[g];
            }
            current = b = (g << 5) + BitOperations.TrailingZeroCount(word);
        }
        int v = head[b]; Remove(v, b); return v;
    }
}

static class Program
{
    static void Main(string[] args)
    {
        var input = new Scanner(args[0]);
        int n = input.Read(), m = input.Read(), q = input.Read(), edgeStart = input.Pos;
        var offset = new int[n + 1];
        for (int i = 0; i < m; ++i)
        {
            int u = input.Read(), v = input.Read(); input.Read();
            if (u != v) { ++offset[u + 1]; ++offset[v + 1]; }
        }
        for (int i = 1; i <= n; ++i) offset[i] += offset[i - 1];
        var to = new int[offset[n]];
        var weight = new ushort[offset[n]];
        var queue = new BucketQueue(n);
        Array.Copy(offset, queue.Next, n);
        input.Pos = edgeStart;
        for (int i = 0; i < m; ++i)
        {
            int u = input.Read(), v = input.Read(), w = input.Read();
            if (u == v) continue;
            int a = queue.Next[u]++, b = queue.Next[v]++;
            to[a] = v; weight[a] = (ushort)w;
            to[b] = u; weight[b] = (ushort)w;
        }
        var sources = new int[q];
        for (int i = 0; i < q; ++i) sources[i] = input.Read();
        input.Data = null;
        var dist = new long[n];
        var output = new StringBuilder();
        foreach (int s in sources)
        {
            Array.Fill(dist, long.MaxValue);
            queue.Reset(); dist[s] = 0; queue.Insert(s, 0);
            long reached = 0, total = 0, far = 0;
            int farNode = s;
            while (queue.Summary != 0)
            {
                int u = queue.Pop();
                long d = dist[u]; ++reached; total += d;
                if (d > far) { far = d; farNode = u; }
                else if (d == far && u < farNode) farNode = u;
                for (int e = offset[u], end = offset[u + 1]; e < end; ++e)
                {
                    int v = to[e];
                    long nd = d + weight[e], old = dist[v];
                    if (nd >= old) continue;
                    if (old != long.MaxValue) queue.Remove(v, (int)(old & 1023));
                    dist[v] = nd; queue.Insert(v, (int)(nd & 1023));
                }
            }
            output.Append(s).Append(' ').Append(reached).Append(' ').Append(total).Append(' ')
                  .Append(far).Append(' ').Append(farNode).Append('\n');
        }
        Console.Write(output);
    }
}
