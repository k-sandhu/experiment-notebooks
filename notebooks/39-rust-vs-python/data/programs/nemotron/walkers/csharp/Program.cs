using System;
using System.IO;
using System.Threading;

namespace Solution;

internal static class Program
{
    private const ulong C1 = 0x9E3779B97F4A7C15;
    private const ulong C2 = 0xBF58476D1CE4E5B9;
    private const ulong C3 = 0x94D049BB133111EB;

    private sealed class Result
    {
        public ulong spread;
        public ulong bumps;
        public ulong returns;
        public int farDist;
        public int farWalker;
    }

    // SplitMix64: advance state by the constant; the walker loop scrambles it.
    private static ulong Advance(ulong state)
    {
        return state + C1;
    }

    // Simulate walkers [start, end).
    private static Result RunRange(long start, long end, long L, int B, ulong seed)
    {
        var res = new Result { farDist = 0, farWalker = (int)start };
        int twoB = 2 * B;
        for (long j = start; j < end; ++j)
        {
            ulong state = seed + (ulong)j;
            int x = 0, y = 0;
            ulong b = 0, r = 0;
            for (long t = 0; t < L; ++t)
            {
                state = Advance(state);
                ulong z = state;
                z = (z ^ (z >> 30)) * C2;
                z = (z ^ (z >> 27)) * C3;
                ulong rnd = z ^ (z >> 31);
                int d = (int)(rnd >> 62);
                int nx, ny;
                if (d == 0) { nx = x + 1; ny = y; }
                else if (d == 1) { nx = x - 1; ny = y; }
                else if (d == 2) { nx = x; ny = y + 1; }
                else { nx = x; ny = y - 1; }

                int vx = nx + B;
                int vy = ny + B;
                if (vx >= 0 && vx <= twoB && vy >= 0 && vy <= twoB)
                {
                    x = nx;
                    y = ny;
                    if (x == 0 && y == 0) ++r;
                }
                else
                {
                    ++b;
                }
            }
            res.spread += (ulong)x * (ulong)x + (ulong)y * (ulong)y;
            res.bumps += b;
            res.returns += r;
            int dist = (x < 0 ? -x : x) + (y < 0 ? -y : y);
            if (dist > res.farDist)
            {
                res.farDist = dist;
                res.farWalker = (int)j;
            }
        }
        return res;
    }

    private static void Merge(Result into, Result other)
    {
        into.spread += other.spread;
        into.bumps += other.bumps;
        into.returns += other.returns;
        if (other.farDist > into.farDist ||
            (other.farDist == into.farDist && other.farWalker < into.farWalker))
        {
            into.farDist = other.farDist;
            into.farWalker = other.farWalker;
        }
    }

    private static int Main(string[] args)
    {
        string text = File.ReadAllText(args[0]);
        string[] parts = text.Split(new[] { ' ', '\t', '\n', '\r' }, StringSplitOptions.RemoveEmptyEntries);
        long J = long.Parse(parts[0]);
        long L = long.Parse(parts[1]);
        int B = int.Parse(parts[2]);
        ulong seed = ulong.Parse(parts[3]);
        int W = int.Parse(args[1]);
        if (W < 1) W = 1;
        if (W > 32) W = 32;

        var results = new Result[W];
        var threads = new Thread[W];
        for (int i = 0; i < W; ++i)
        {
            long start = i * J / W;
            long end = (i + 1) * J / W;
            int idx = i;
            threads[i] = new Thread(() => results[idx] = RunRange(start, end, L, B, seed));
            threads[i].Start();
        }
        for (int i = 0; i < W; ++i) threads[i].Join();

        var total = results[0];
        for (int i = 1; i < W; ++i) Merge(total, results[i]);

        Console.WriteLine("spread " + total.spread);
        Console.WriteLine("bumps " + total.bumps);
        Console.WriteLine("returns " + total.returns);
        Console.WriteLine("farthest " + total.farWalker + " " + total.farDist);
        return 0;
    }
}
