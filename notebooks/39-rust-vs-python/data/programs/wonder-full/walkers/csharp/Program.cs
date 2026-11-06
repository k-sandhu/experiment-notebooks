using System;
using System.IO;
using System.Threading;

class Program
{
    const ulong GOLD = 0x9E3779B97F4A7C15UL;
    const ulong C1 = 0xBF58476D1CE4E5B9UL;
    const ulong C2 = 0x94D049BB133111EBUL;
    static readonly int[] DX = { 1, -1, 0, 0 };
    static readonly int[] DY = { 0, 0, 1, -1 };

    struct Partial
    {
        public long Spread, Bumps, Returns, FarIdx, FarDist;
    }

    static int Dir(ulong state)
    {
        ulong z = state;
        z = (z ^ (z >> 30)) * C1;
        z = (z ^ (z >> 27)) * C2;
        return (int)(z >> 62);
    }

    static void RunRange(long begin, long end, long L, int B, ulong seed, Partial[] parts, int slot)
    {
        long spread = 0, bumps = 0, returns = 0;
        long farIdx = begin, farDist = -1;
        // Coordinates offset by +B into unsigned [0, 2B]; one compare per axis.
        uint UB = (uint)B * 2u;
        uint ORG = (uint)B;
        long L4 = L & ~3L;
        var dx = DX; var dy = DY;
        for (long j = begin; j < end; j++)
        {
            ulong state = seed + (ulong)j;
            uint ux = ORG, uy = ORG;
            long b = 0, r = 0;
            long i = 0;
            for (; i < L4; i += 4)
            {
                ulong s0 = state + GOLD;
                ulong s1 = s0 + GOLD;
                ulong s2 = s1 + GOLD;
                ulong s3 = s2 + GOLD;
                state = s3;
                int d0 = Dir(s0), d1 = Dir(s1), d2 = Dir(s2), d3 = Dir(s3);
                {
                    uint nx = ux + (uint)dx[d0], ny = uy + (uint)dy[d0];
                    if (nx > UB || ny > UB) b++; else { ux = nx; uy = ny; if ((ux == ORG) & (uy == ORG)) r++; }
                }
                {
                    uint nx = ux + (uint)dx[d1], ny = uy + (uint)dy[d1];
                    if (nx > UB || ny > UB) b++; else { ux = nx; uy = ny; if ((ux == ORG) & (uy == ORG)) r++; }
                }
                {
                    uint nx = ux + (uint)dx[d2], ny = uy + (uint)dy[d2];
                    if (nx > UB || ny > UB) b++; else { ux = nx; uy = ny; if ((ux == ORG) & (uy == ORG)) r++; }
                }
                {
                    uint nx = ux + (uint)dx[d3], ny = uy + (uint)dy[d3];
                    if (nx > UB || ny > UB) b++; else { ux = nx; uy = ny; if ((ux == ORG) & (uy == ORG)) r++; }
                }
            }
            for (; i < L; i++)
            {
                state += GOLD;
                int d = Dir(state);
                uint nx = ux + (uint)dx[d], ny = uy + (uint)dy[d];
                if (nx > UB || ny > UB) b++; else { ux = nx; uy = ny; if ((ux == ORG) & (uy == ORG)) r++; }
            }
            bumps += b; returns += r;
            long x = (long)ux - B, y = (long)uy - B;
            spread += x * x + y * y;
            long dist = (x < 0 ? -x : x) + (y < 0 ? -y : y);
            if (dist > farDist) { farDist = dist; farIdx = j; }
        }
        parts[slot] = new Partial { Spread = spread, Bumps = bumps, Returns = returns, FarIdx = farIdx, FarDist = farDist };
    }

    static void Main(string[] args)
    {
        byte[] data = File.ReadAllBytes(args[0]);
        ulong[] vals = new ulong[4];
        int idx = 0, p = 0;
        while (idx < 4 && p < data.Length)
        {
            while (p < data.Length && (data[p] < (byte)'0' || data[p] > (byte)'9')) p++;
            if (p >= data.Length) break;
            ulong v = 0;
            while (p < data.Length && data[p] >= (byte)'0' && data[p] <= (byte)'9')
            {
                v = v * 10 + (ulong)(data[p] - (byte)'0'); p++;
            }
            vals[idx++] = v;
        }
        long J = (long)vals[0], L = (long)vals[1];
        int B = vals[2] > int.MaxValue ? int.MaxValue : (int)vals[2];
        ulong seed = vals[3];

        int workers = args.Length >= 2 ? int.Parse(args[1]) : Environment.ProcessorCount;
        if (workers < 1) workers = 1;
        if (workers > 32) workers = 32;
        if (J > 0 && workers > J) workers = (int)J;
        if (workers < 1) workers = 1;

        if (J <= 0)
        {
            Console.Write("spread 0\nbumps 0\nreturns 0\nfarthest 0 0\n");
            return;
        }
        var parts = new Partial[workers];
        var ranges = new (long, long)[workers];
        long baseN = J / workers, rem = J % workers, start = 0;
        for (int w = 0; w < workers; w++)
        {
            long cnt = baseN + (w < rem ? 1 : 0);
            ranges[w] = (start, start + cnt); start += cnt;
        }
        if (workers == 1)
        {
            RunRange(ranges[0].Item1, ranges[0].Item2, L, B, seed, parts, 0);
        }
        else
        {
            var th = new Thread[workers - 1];
            for (int w = 1; w < workers; w++)
            {
                int ww = w;
                th[w - 1] = new Thread(() => RunRange(ranges[ww].Item1, ranges[ww].Item2, L, B, seed, parts, ww));
                th[w - 1].Start();
            }
            RunRange(ranges[0].Item1, ranges[0].Item2, L, B, seed, parts, 0);
            foreach (var t in th) t.Join();
        }
        long spread = 0, bumps = 0, returns = 0, farIdx = 0, farDist = -1;
        foreach (var pt in parts)
        {
            spread += pt.Spread; bumps += pt.Bumps; returns += pt.Returns;
            if (pt.FarDist > farDist) { farDist = pt.FarDist; farIdx = pt.FarIdx; }
        }
        if (farDist < 0) farDist = 0;
        Console.Write($"spread {spread}\nbumps {bumps}\nreturns {returns}\nfarthest {farIdx} {farDist}\n");
    }
}
