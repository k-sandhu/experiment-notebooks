using System;
using System.IO;
using System.Text;

// Shortest paths from each source with Dial's bucket queue. Edge weights are 1..1000, so a ring of
// 1024 buckets replaces a heap: the bucket of distance d is d & 1023.
static class Program
{
    const int Buckets = 1024; // greater than the largest weight (1000)
    const int Nil = -1;

    static byte[] buf;
    static int pos;

    static int NextInt()
    {
        byte[] b = buf;
        int p = pos;
        int len = b.Length;
        while (p < len && (uint)(b[p] - '0') > 9) p++;
        int x = 0;
        while (p < len && (uint)(b[p] - '0') <= 9) x = x * 10 + (b[p++] - '0');
        pos = p;
        return x;
    }

    static int Main(string[] args)
    {
        buf = File.ReadAllBytes(args[0]);
        int n = NextInt();
        int m = NextInt();
        int q = NextInt();

        // Two passes over the edge lines: the first counts degrees, the second fills the adjacency arrays.
        int edgesAt = pos;
        int[] start = new int[n + 1];
        for (int i = 0; i < m; i++)
        {
            start[NextInt() + 1]++;
            start[NextInt() + 1]++;
            NextInt();
        }
        for (int v = 0; v < n; v++) start[v + 1] += start[v];

        int[] arcTo = new int[2 * m];
        int[] arcW = new int[2 * m];
        int[] fill = new int[n];
        Array.Copy(start, fill, n);
        pos = edgesAt;
        for (int i = 0; i < m; i++)
        {
            int u = NextInt();
            int v = NextInt();
            int w = NextInt();
            int a = fill[u]++;
            arcTo[a] = v;
            arcW[a] = w;
            a = fill[v]++;
            arcTo[a] = u;
            arcW[a] = w;
        }

        long[] dist = new long[n];
        int[] head = new int[Buckets];
        int[] entNode = new int[2 * m + 1];
        int[] entNext = new int[2 * m + 1];
        var sb = new StringBuilder();
        for (int k = 0; k < q; k++)
        {
            int s = NextInt();
            Array.Fill(dist, long.MaxValue);
            Array.Fill(head, Nil);

            int used = 0;
            int pending = 0;
            dist[s] = 0;
            entNode[used] = s;
            entNext[used] = Nil;
            head[0] = used++;
            pending++;

            long reached = 0;
            long total = 0;
            long far = 0;
            int node = s;
            for (long cur = 0; pending > 0; cur++)
            {
                int b = (int)(cur & (Buckets - 1));
                int e = head[b];
                head[b] = Nil;
                while (e != Nil)
                {
                    int v = entNode[e];
                    e = entNext[e];
                    pending--;
                    if (dist[v] != cur) continue;

                    reached++;
                    total += cur;
                    if (cur > far || (cur == far && v < node))
                    {
                        far = cur;
                        node = v;
                    }
                    int end = start[v + 1];
                    for (int i = start[v]; i < end; i++)
                    {
                        int to = arcTo[i];
                        long nd = cur + arcW[i];
                        if (nd < dist[to])
                        {
                            dist[to] = nd;
                            int nb = (int)(nd & (Buckets - 1));
                            entNode[used] = to;
                            entNext[used] = head[nb];
                            head[nb] = used++;
                            pending++;
                        }
                    }
                }
            }
            sb.Append(s).Append(' ').Append(reached).Append(' ').Append(total).Append(' ')
              .Append(far).Append(' ').Append(node).Append('\n');
        }

        using (Stream stdout = Console.OpenStandardOutput())
        {
            byte[] bytes = Encoding.ASCII.GetBytes(sb.ToString());
            stdout.Write(bytes, 0, bytes.Length);
        }
        return 0;
    }
}
