using System;
using System.IO;
using System.Numerics;
using System.Runtime.CompilerServices;
using System.Text;

internal static class Program
{
    private sealed class InputReader
    {
        private readonly byte[] data;
        private int position;

        public InputReader(string path)
        {
            data = File.ReadAllBytes(path);
        }

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public int ReadInt()
        {
            byte[] bytes = data;
            int p = position;

            while (bytes[p] <= 32)
                p++;

            int value = 0;
            while (p < bytes.Length)
            {
                uint digit = (uint)(bytes[p] - '0');
                if (digit > 9)
                    break;

                value = value * 10 + (int)digit;
                p++;
            }

            position = p;
            return value;
        }
    }

    private static void Main(string[] args)
    {
        var input = new InputReader(args[0]);

        int n = input.ReadInt();
        int m = input.ReadInt();
        int q = input.ReadInt();

        var offsets = new int[n + 1];
        var from = new int[m];
        var to = new int[m];
        var weights = new ushort[m];

        for (int i = 0; i < m; i++)
        {
            int u = input.ReadInt();
            int v = input.ReadInt();
            int w = input.ReadInt();

            from[i] = u;
            to[i] = v;
            weights[i] = (ushort)w;

            if (u != v)
            {
                offsets[u + 1]++;
                offsets[v + 1]++;
            }
        }

        var sources = new int[q];
        for (int i = 0; i < q; i++)
            sources[i] = input.ReadInt();

        for (int i = 1; i <= n; i++)
            offsets[i] += offsets[i - 1];

        var edges = new ulong[offsets[n]];
        var cursor = (int[])offsets.Clone();

        for (int i = 0; i < m; i++)
        {
            int u = from[i];
            int v = to[i];
            if (u == v)
                continue;

            ulong w = weights[i];
            edges[cursor[u]++] = ((ulong)(uint)v << 10) | w;
            edges[cursor[v]++] = ((ulong)(uint)u << 10) | w;
        }

        var distance = new long[n];
        var previous = new int[n];
        var next = new int[n];
        var heads = new int[1024];
        var occupied = new ulong[16];
        var output = new StringBuilder();

        foreach (int source in sources)
        {
            Solve(
                source, offsets, edges, distance, previous, next,
                heads, occupied, output);
        }

        Console.Write(output.ToString());
    }

    private static void Solve(
        int source,
        int[] offsets,
        ulong[] edges,
        long[] distance,
        int[] previous,
        int[] next,
        int[] heads,
        ulong[] occupied,
        StringBuilder output)
    {
        Array.Fill(distance, long.MaxValue);
        Array.Fill(heads, -1);
        Array.Clear(occupied);

        distance[source] = 0;
        previous[source] = -1;
        next[source] = -1;
        heads[0] = source;
        occupied[0] = 1;

        uint occupiedGroups = 1;
        int bucket = 0;

        int reachable = 0;
        long total = 0;
        long farthest = 0;
        int farthestNode = source;

        while (occupiedGroups != 0)
        {
            int group = bucket >> 6;
            ulong candidates =
                occupied[group] & (ulong.MaxValue << (bucket & 63));

            if (candidates == 0)
            {
                uint laterGroups =
                    occupiedGroups & (uint.MaxValue << (group + 1));

                group = BitOperations.TrailingZeroCount(
                    laterGroups != 0 ? laterGroups : occupiedGroups);

                candidates = occupied[group];
            }

            bucket = (group << 6) + BitOperations.TrailingZeroCount(candidates);

            long currentDistance = distance[heads[bucket]];
            int bucketCount = 0;
            int smallestNode = int.MaxValue;

            while (heads[bucket] != -1)
            {
                int u = heads[bucket];
                int following = next[u];
                heads[bucket] = following;

                if (following != -1)
                    previous[following] = -1;

                bucketCount++;
                if (u < smallestNode)
                    smallestNode = u;

                int end = offsets[u + 1];
                for (int e = offsets[u]; e < end; e++)
                {
                    ulong edge = edges[e];
                    int v = (int)(edge >> 10);
                    long candidateDistance = currentDistance + (long)(edge & 1023);

                    long oldDistance = distance[v];
                    if (candidateDistance >= oldDistance)
                        continue;

                    if (oldDistance != long.MaxValue)
                    {
                        int oldBucket = (int)(oldDistance & 1023);
                        int p = previous[v];
                        int nx = next[v];

                        if (p == -1)
                            heads[oldBucket] = nx;
                        else
                            next[p] = nx;

                        if (nx != -1)
                            previous[nx] = p;

                        if (heads[oldBucket] == -1)
                        {
                            int oldGroup = oldBucket >> 6;
                            occupied[oldGroup] &=
                                ~(1UL << (oldBucket & 63));

                            if (occupied[oldGroup] == 0)
                                occupiedGroups &= ~(1U << oldGroup);
                        }
                    }

                    distance[v] = candidateDistance;

                    int newBucket = (int)(candidateDistance & 1023);
                    int oldHead = heads[newBucket];

                    previous[v] = -1;
                    next[v] = oldHead;

                    if (oldHead != -1)
                    {
                        previous[oldHead] = v;
                    }
                    else
                    {
                        int newGroup = newBucket >> 6;
                        occupied[newGroup] |= 1UL << (newBucket & 63);
                        occupiedGroups |= 1U << newGroup;
                    }

                    heads[newBucket] = v;
                }
            }

            reachable += bucketCount;
            total += currentDistance * bucketCount;
            farthest = currentDistance;
            farthestNode = smallestNode;

            occupied[group] &= ~(1UL << (bucket & 63));
            if (occupied[group] == 0)
                occupiedGroups &= ~(1U << group);

            bucket = (bucket + 1) & 1023;
        }

        output.Append(source).Append(' ')
              .Append(reachable).Append(' ')
              .Append(total).Append(' ')
              .Append(farthest).Append(' ')
              .Append(farthestNode).Append('\n');
    }
}
