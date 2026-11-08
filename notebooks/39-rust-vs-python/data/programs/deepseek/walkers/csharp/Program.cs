using System;
using System.IO;
using System.Text;
using System.Threading;

internal static class Program
{
    private const ulong Gamma = 0x9E3779B97F4A7C15UL;
    private const ulong C1 = 0xBF58476D1CE4E5B9UL;
    private const ulong C2 = 0x94D049BB133111EBUL;

    private static ulong[] spread;
    private static ulong[] bumps;
    private static ulong[] returns;
    private static long[] fx;
    private static long[] fy;

    private static void RunWalker(ulong state, ulong steps, long b, int j)
    {
        long x = 0, y = 0;
        ulong nbumps = 0, nreturns = 0;
        long nb = -b;

        for (ulong k = 0; k < steps; ++k)
        {
            state += Gamma;
            ulong z = state;
            z = (z ^ (z >> 30)) * C1;
            z = (z ^ (z >> 27)) * C2;
            z ^= z >> 31;

            ulong d = z >> 62;
            long dir = 1 - 2 * (long)(d & 1);
            long mx = d < 2 ? -1L : 0L;
            long dx = dir & mx;
            long dy = dir & ~mx;
            long nx = x + dx, ny = y + dy;
            long ox = (nx > b ? 1L : 0L) - (nx < nb ? 1L : 0L);
            long oy = (ny > b ? 1L : 0L) - (ny < nb ? 1L : 0L);
            nx -= ox;
            ny -= oy;
            nbumps += (ox | oy) != 0 ? 1UL : 0UL;
            nreturns += (nx | ny) == 0 ? 1UL : 0UL;
            x = nx;
            y = ny;
        }

        spread[j] = (ulong)(x * x + y * y);
        bumps[j] = nbumps;
        returns[j] = nreturns;
        fx[j] = x;
        fy[j] = y;
    }

    private static void RunWalker2(ulong s0, ulong s1, ulong steps, long b, int j0, int j1)
    {
        long x0 = 0, y0 = 0, x1 = 0, y1 = 0;
        ulong b0 = 0, r0 = 0, b1 = 0, r1 = 0;
        long nb = -b;

        for (ulong k = 0; k < steps; ++k)
        {
            s0 += Gamma;
            ulong z0 = s0;
            z0 = (z0 ^ (z0 >> 30)) * C1;
            z0 = (z0 ^ (z0 >> 27)) * C2;
            z0 ^= z0 >> 31;

            s1 += Gamma;
            ulong z1 = s1;
            z1 = (z1 ^ (z1 >> 30)) * C1;
            z1 = (z1 ^ (z1 >> 27)) * C2;
            z1 ^= z1 >> 31;

            ulong d0 = z0 >> 62;
            long dir0 = 1 - 2 * (long)(d0 & 1);
            long mx0 = d0 < 2 ? -1L : 0L;
            long nx0 = x0 + (dir0 & mx0);
            long ny0 = y0 + (dir0 & ~mx0);
            long ox0 = (nx0 > b ? 1L : 0L) - (nx0 < nb ? 1L : 0L);
            long oy0 = (ny0 > b ? 1L : 0L) - (ny0 < nb ? 1L : 0L);
            nx0 -= ox0;
            ny0 -= oy0;
            b0 += (ox0 | oy0) != 0 ? 1UL : 0UL;
            r0 += (nx0 | ny0) == 0 ? 1UL : 0UL;
            x0 = nx0;
            y0 = ny0;

            ulong d1 = z1 >> 62;
            long dir1 = 1 - 2 * (long)(d1 & 1);
            long mx1 = d1 < 2 ? -1L : 0L;
            long nx1 = x1 + (dir1 & mx1);
            long ny1 = y1 + (dir1 & ~mx1);
            long ox1 = (nx1 > b ? 1L : 0L) - (nx1 < nb ? 1L : 0L);
            long oy1 = (ny1 > b ? 1L : 0L) - (ny1 < nb ? 1L : 0L);
            nx1 -= ox1;
            ny1 -= oy1;
            b1 += (ox1 | oy1) != 0 ? 1UL : 0UL;
            r1 += (nx1 | ny1) == 0 ? 1UL : 0UL;
            x1 = nx1;
            y1 = ny1;
        }

        spread[j0] = (ulong)(x0 * x0 + y0 * y0);
        bumps[j0] = b0;
        returns[j0] = r0;
        fx[j0] = x0;
        fy[j0] = y0;
        spread[j1] = (ulong)(x1 * x1 + y1 * y1);
        bumps[j1] = b1;
        returns[j1] = r1;
        fx[j1] = x1;
        fy[j1] = y1;
    }

    private static void RunRange(ulong seed, ulong steps, long b, int start, int end)
    {
        int j = start;
        for (; j + 1 < end; j += 2)
            RunWalker2(seed + (ulong)j, seed + (ulong)(j + 1), steps, b, j, j + 1);
        if (j < end)
            RunWalker(seed + (ulong)j, steps, b, j);
    }

    private static int Main(string[] args)
    {
        string text = File.ReadAllText(args[0]);
        string[] tok = text.Split((char[])null, StringSplitOptions.RemoveEmptyEntries);
        int J = int.Parse(tok[0]);
        ulong L = ulong.Parse(tok[1]);
        long B = long.Parse(tok[2]);
        ulong seed = ulong.Parse(tok[3]);

        int workers = int.Parse(args[1].Trim());
        if (workers < 1) workers = 1;
        if (workers > J) workers = J;
        if (workers < 1) workers = 1;

        spread = new ulong[J];
        bumps = new ulong[J];
        returns = new ulong[J];
        fx = new long[J];
        fy = new long[J];

        if (J > 0)
        {
            if (workers == 1)
            {
                RunRange(seed, L, B, 0, J);
            }
            else
            {
                Thread[] threads = new Thread[workers];
                int baseCount = J / workers;
                int rem = J % workers;
                int start = 0;
                for (int t = 0; t < workers; ++t)
                {
                    int cnt = baseCount + (t < rem ? 1 : 0);
                    int s = start;
                    int e = start + cnt;
                    start = e;
                    threads[t] = new Thread(() => RunRange(seed, L, B, s, e));
                    threads[t].Start();
                }
                for (int t = 0; t < workers; ++t)
                    threads[t].Join();
            }
        }

        ulong totalSpread = 0, totalBumps = 0, totalReturns = 0;
        long bestDist = 0;
        int bestJ = 0;
        for (int j = 0; j < J; ++j)
        {
            totalSpread += spread[j];
            totalBumps += bumps[j];
            totalReturns += returns[j];
            long ax = fx[j] < 0 ? -fx[j] : fx[j];
            long ay = fy[j] < 0 ? -fy[j] : fy[j];
            long d = ax + ay;
            if (d > bestDist)
            {
                bestDist = d;
                bestJ = j;
            }
        }

        var sb = new StringBuilder(96);
        sb.Append("spread ").Append(totalSpread).Append('\n');
        sb.Append("bumps ").Append(totalBumps).Append('\n');
        sb.Append("returns ").Append(totalReturns).Append('\n');
        sb.Append("farthest ").Append(bestJ).Append(' ').Append(bestDist).Append('\n');
        Console.Out.Write(sb.ToString());
        return 0;
    }
}
