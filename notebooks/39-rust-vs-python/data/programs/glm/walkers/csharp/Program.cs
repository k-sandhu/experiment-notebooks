using System;
using System.IO;
using System.Text;
using System.Threading;

internal static class Program
{
    private static long L, B;

    private sealed class Slot
    {
        public long Spread, Bumps, Rets, BestD = -1, BestJ = -1;
    }

    private static int Main(string[] args)
    {
        if (args.Length < 2) return 1;
        long J, seed;
        {
            using var fs = new FileStream(args[0], FileMode.Open, FileAccess.Read);
            using var sr = new StreamReader(fs);
            var parts = sr.ReadToEnd().Split((char[])null, StringSplitOptions.RemoveEmptyEntries);
            J = long.Parse(parts[0]);
            L = long.Parse(parts[1]);
            B = long.Parse(parts[2]);
            seed = (long)ulong.Parse(parts[3]);
        }
        int workers = int.Parse(args[1]);
        if (workers < 1) workers = 1;
        if (workers > J) workers = (int)J;

        var slots = new Slot[workers];
        long chunk = (J + workers - 1) / workers;
        var threads = new Thread[workers];
        for (int w = 0; w < workers; w++)
        {
            long j0 = w * chunk;
            long j1 = Math.Min(j0 + chunk, J);
            if (j0 >= j1) break;
            var slot = new Slot();
            slots[w] = slot;
            var t = new Thread(() => WalkRange(j0, j1, seed, slot));
            if (w == workers - 1)
            {
                WalkRange(j0, j1, seed, slot);
            }
            else
            {
                threads[w] = t;
                t.Start();
            }
        }
        for (int w = 0; w < workers; w++) threads[w]?.Join();

        long spread = 0, bumps = 0, rets = 0, bestD = -1, bestJ = -1;
        foreach (var s in slots)
        {
            if (s == null) continue;
            spread += s.Spread;
            bumps += s.Bumps;
            rets += s.Rets;
            if (s.BestJ >= 0 && (bestJ < 0 || s.BestD > bestD))
            {
                bestD = s.BestD;
                bestJ = s.BestJ;
            }
        }

        var sb = new StringBuilder(128);
        sb.Append("spread ").Append(spread).Append('\n');
        sb.Append("bumps ").Append(bumps).Append('\n');
        sb.Append("returns ").Append(rets).Append('\n');
        sb.Append("farthest ").Append(bestJ).Append(' ').Append(bestD).Append('\n');
        using var stdout = Console.OpenStandardOutput();
        var bytes = Encoding.ASCII.GetBytes(sb.ToString());
        stdout.Write(bytes, 0, bytes.Length);
        return 0;
    }

    private static void WalkRange(long j0, long j1, long seed, Slot slot)
    {
        long spread = 0, bumps = 0, rets = 0, bestD = -1, bestJ = -1;
        long negB = -B;
        for (long j = j0; j < j1; j++)
        {
            ulong state = (ulong)seed + (ulong)j;
            long x = 0, y = 0;
            for (long s = 0; s < L; s++)
            {
                state += 0x9E3779B97F4A7C15UL;
                ulong z = state;
                z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9UL;
                z = (z ^ (z >> 27)) * 0x94D049BB133111EBUL;
                z = z ^ (z >> 31);
                int d = (int)(z >> 62);
                long dx = (d == 0 ? 1 : 0) - (d == 1 ? 1 : 0);
                long dy = (d == 2 ? 1 : 0) - (d == 3 ? 1 : 0);
                long nx = x + dx, ny = y + dy;
                if (nx > B || nx < negB || ny > B || ny < negB)
                {
                    bumps++;
                }
                else
                {
                    x = nx;
                    y = ny;
                    if (x == 0 && y == 0) rets++;
                }
            }
            spread += x * x + y * y;
            long D = Math.Abs(x) + Math.Abs(y);
            if (D > bestD)
            {
                bestD = D;
                bestJ = j;
            }
        }
        slot.Spread = spread;
        slot.Bumps = bumps;
        slot.Rets = rets;
        slot.BestD = bestD;
        slot.BestJ = bestJ;
    }
}
