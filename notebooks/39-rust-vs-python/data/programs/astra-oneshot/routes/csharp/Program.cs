using System;
using System.Collections.Generic;
using System.IO;
using System.Numerics;
using System.Runtime.CompilerServices;
using System.Text;

internal static class Program
{
    private sealed class FastReader
    {
        private readonly byte[] data;
        private int position;

        public FastReader(string path)
        {
            data = File.ReadAllBytes(path);
        }

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public int ReadInt()
        {
            int p = position;
            while (data[p] <= 32)
                p++;

            int value = 0;
            do
            {
                value = value * 10 + data[p] - '0';
                p++;
            }
            while (p < data.Length && data[p] > 32);

            position = p;
            return value;
        }
    }

    private static void ReadGraph(
        string path,
        out int[] offsets,
        out ulong[] edges,
        out int[] sources)
    {
        var reader = new FastReader(path);
        int n = reader.ReadInt();
        int m = reader.ReadInt();
        int q = reader.ReadInt();

        int[] degree = new int[n];
        int[] from = new int[m];
        int[] to = new int[m];
        ushort[] weights = new ushort[m];
        int roadCount = 0;

        for (int i = 0; i < m; i++)
        {
            int u = reader.ReadInt();
            int v = reader.ReadInt();
            int w = reader.ReadInt();

            if (u == v)
                continue;

            from[roadCount] = u;
            to[roadCount] = v;
            weights[roadCount] = (ushort)w;
            roadCount++;
            degree[u]++;
            degree[v]++;
        }

        sources = new int[q];
        for (int i = 0; i < q; i++)
            sources[i] = reader.ReadInt();

        offsets = new int[n + 1];
        int edgeCount = 0;
        for (int i = 0; i < n; i++)
        {
            offsets[i] = edgeCount;
            edgeCount += degree[i];
            degree[i] = offsets[i];
        }
        offsets[n] = edgeCount;

        edges = new ulong[edgeCount];
        for (int i = 0; i < roadCount; i++)
        {
            int u = from[i];
            int v = to[i];
            ulong w = weights[i];

            edges[degree[u]++] = ((ulong)(uint)v << 10) | w;
            edges[degree[v]++] = ((ulong)(uint)u << 10) | w;
        }
    }

    private sealed class Solver
    {
        private readonly int[] offsets;
        private readonly ulong[] edges;
        private readonly long[] distances;
        private readonly int[] previous;
        private readonly int[] next;
        private readonly int[] heads = new int[1024];
        private readonly ulong[] masks = new ulong[16];

        public Solver(int[] offsets, ulong[] edges)
        {
            this.offsets = offsets;
            this.edges = edges;

            int n = offsets.Length - 1;
            distances = new long[n];
            previous = new int[n];
            next = new int[n];
        }

        public string Run(int source)
        {
            int[] offsets = this.offsets;
            ulong[] edges = this.edges;
            long[] distances = this.distances;
            int[] previous = this.previous;
            int[] next = this.next;
            int[] heads = this.heads;
            ulong[] masks = this.masks;

            Array.Fill(distances, long.MaxValue);
            Array.Fill(heads, -1);
            Array.Clear(masks);

            distances[source] = 0;
            previous[source] = -1;
            next[source] = -1;
            heads[0] = source;
            masks[0] = 1;

            ulong nonemptyGroups = 1;
            int cursor = 0;
            int reachable = 0;
            long total = 0;
            long far = 0;
            int farNode = source;

            while (nonemptyGroups != 0)
            {
                int group = cursor >> 6;
                ulong candidates =
                    masks[group] & (ulong.MaxValue << (cursor & 63));

                if (candidates == 0)
                {
                    ulong laterGroups =
                        nonemptyGroups & (ulong.MaxValue << (group + 1));

                    if (laterGroups == 0)
                        laterGroups = nonemptyGroups;

                    group = BitOperations.TrailingZeroCount(laterGroups);
                    candidates = masks[group];
                }

                int bucket =
                    (group << 6) + BitOperations.TrailingZeroCount(candidates);
                cursor = bucket;

                int node = heads[bucket];
                int following = next[node];
                heads[bucket] = following;

                if (following >= 0)
                {
                    previous[following] = -1;
                }
                else
                {
                    masks[group] &= ~(1UL << (bucket & 63));
                    if (masks[group] == 0)
                        nonemptyGroups &= ~(1UL << group);
                }

                long distance = distances[node];
                reachable++;
                total += distance;

                if (distance > far)
                {
                    far = distance;
                    farNode = node;
                }
                else if (distance == far && node < farNode)
                {
                    farNode = node;
                }

                int end = offsets[node + 1];
                for (int e = offsets[node]; e < end; e++)
                {
                    ulong edge = edges[e];
                    int neighbor = (int)(edge >> 10);
                    long candidate = distance + (long)(edge & 1023UL);
                    long oldDistance = distances[neighbor];

                    if (candidate >= oldDistance)
                        continue;

                    if (oldDistance != long.MaxValue)
                    {
                        int oldBucket = (int)(oldDistance & 1023);
                        int before = previous[neighbor];
                        int after = next[neighbor];

                        if (before >= 0)
                            next[before] = after;
                        else
                            heads[oldBucket] = after;

                        if (after >= 0)
                            previous[after] = before;

                        if (before < 0 && after < 0)
                        {
                            int oldGroup = oldBucket >> 6;
                            masks[oldGroup] &= ~(1UL << (oldBucket & 63));

                            if (masks[oldGroup] == 0)
                                nonemptyGroups &= ~(1UL << oldGroup);
                        }
                    }

                    distances[neighbor] = candidate;

                    int newBucket = (int)(candidate & 1023);
                    int oldHead = heads[newBucket];
                    previous[neighbor] = -1;
                    next[neighbor] = oldHead;
                    heads[newBucket] = neighbor;

                    if (oldHead >= 0)
                    {
                        previous[oldHead] = neighbor;
                    }
                    else
                    {
                        int newGroup = newBucket >> 6;
                        masks[newGroup] |= 1UL << (newBucket & 63);
                        nonemptyGroups |= 1UL << newGroup;
                    }
                }
            }

            return $"{source} {reachable} {total} {far} {farNode}";
        }
    }

    private static void Main(string[] args)
    {
        ReadGraph(args[0], out int[] offsets, out ulong[] edges, out int[] sources);

        var solver = new Solver(offsets, edges);
        var cache = new Dictionary<int, string>();
        var output = new StringBuilder();

        foreach (int source in sources)
        {
            if (!cache.TryGetValue(source, out string result))
            {
                result = solver.Run(source);
                cache.Add(source, result);
            }

            output.Append(result).Append('\n');
        }

        Console.Write(output.ToString());
    }
}
