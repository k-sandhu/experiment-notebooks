using System.Globalization;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using System.Threading;

static class Program
{
    const ulong Gamma = 0x9E3779B97F4A7C15UL;
    const ulong Mul1 = 0xBF58476D1CE4E5B9UL;
    const ulong Mul2 = 0x94D049BB133111EBUL;

    // Runs shorter than this are not worth a trip through the unchecked loop.
    const long MinFastRun = 4;
    // Keeps the packed x displacement of one run inside its low 32 bits.
    const long MaxFastRun = 1L << 30;

    // Moves for directions 0..3, and the same moves packed as dx + dy * 2^32 so one add moves both coordinates.
    static ReadOnlySpan<long> Dx => new long[] { 1, -1, 0, 0 };
    static ReadOnlySpan<long> Dy => new long[] { 0, 0, 1, -1 };
    static ReadOnlySpan<ulong> Packed => new ulong[] { 1, ulong.MaxValue, 1UL << 32, unchecked(0UL - (1UL << 32)) };

    struct WalkResult
    {
        public long X, Y, Bumps, Returns;
    }

    // Top two bits of the next SplitMix64 output; the final z ^ (z >> 31) never changes them.
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    static int Direction(ulong s)
    {
        ulong z = (s ^ (s >> 30)) * Mul1;
        z = (z ^ (z >> 27)) * Mul2;
        return (int)(z >> 62);
    }

    static WalkResult Walk(ulong s, long steps, long bound)
    {
        ReadOnlySpan<long> dxs = Dx, dys = Dy;
        ReadOnlySpan<ulong> packed = Packed;
        ulong span = (ulong)(2 * bound);
        long x = 0, y = 0, bumps = 0, returns = 0;
        long left = steps;
        while (left > 0)
        {
            long ax = Math.Abs(x), ay = Math.Abs(y);
            // Within `run` steps the walker can neither reach a wall nor the origin,
            // so those steps need no checks at all.
            long run = Math.Min(bound - Math.Max(ax, ay), ax + ay - 1);
            if (run >= MinFastRun)
            {
                run = Math.Min(Math.Min(run, left), MaxFastRun);
                left -= run;
                ulong moved = 0;
                for (long i = run; i > 0; i--)
                {
                    s += Gamma;
                    moved += Unsafe.Add(ref MemoryMarshal.GetReference(packed), Direction(s));
                }
                long dx = (int)moved;
                x += dx;
                y += (long)(moved - (ulong)dx) >> 32;
                continue;
            }
            // Checked steps near a wall or the origin, until the walker is clear again.
            long end = Math.Max(left - MinFastRun, 0);
            for (; left > end; left--)
            {
                s += Gamma;
                int d = Direction(s);
                long nx = x + dxs[d], ny = y + dys[d];
                if ((ulong)(nx + bound) <= span && (ulong)(ny + bound) <= span)
                {
                    x = nx;
                    y = ny;
                    if ((x | y) == 0) returns++;
                }
                else
                {
                    bumps++;
                }
            }
        }
        return new WalkResult { X = x, Y = y, Bumps = bumps, Returns = returns };
    }

    static void WalkRange(int from, int to, ulong seed, long steps, long bound, WalkResult[] results)
    {
        for (int j = from; j < to; j++) results[j] = Walk(seed + (ulong)j, steps, bound);
    }

    static int Main(string[] args)
    {
        string[] fields = File.ReadAllText(args[0]).Split((char[])null, StringSplitOptions.RemoveEmptyEntries);
        int walkers = int.Parse(fields[0], CultureInfo.InvariantCulture);
        long steps = long.Parse(fields[1], CultureInfo.InvariantCulture);
        long bound = long.Parse(fields[2], CultureInfo.InvariantCulture);
        ulong seed = ulong.Parse(fields[3], CultureInfo.InvariantCulture);
        int workers = args.Length > 1 ? Math.Max(1, int.Parse(args[1], CultureInfo.InvariantCulture)) : 1;

        // A walker never gets farther than `steps` from the origin, so a larger box behaves the same.
        bound = Math.Min(bound, steps);

        var results = new WalkResult[Math.Max(walkers, 0)];
        int threads = Math.Min(workers, walkers);
        var pool = new Thread[Math.Max(threads, 1)];
        for (int t = 1; t < threads; t++)
        {
            int from = (int)((long)walkers * t / threads), to = (int)((long)walkers * (t + 1) / threads);
            pool[t] = new Thread(() => WalkRange(from, to, seed, steps, bound, results));
            pool[t].Start();
        }
        if (threads > 0) WalkRange(0, walkers / threads, seed, steps, bound, results);
        for (int t = 1; t < threads; t++) pool[t].Join();

        long spread = 0, bumps = 0, returns = 0, bestJ = 0, bestD = -1;
        for (int j = 0; j < walkers; j++)
        {
            ref WalkResult r = ref results[j];
            spread += r.X * r.X + r.Y * r.Y;
            bumps += r.Bumps;
            returns += r.Returns;
            long d = Math.Abs(r.X) + Math.Abs(r.Y);
            if (d > bestD)
            {
                bestD = d;
                bestJ = j;
            }
        }
        if (bestD < 0) bestD = 0;
        Console.Out.Write(string.Create(CultureInfo.InvariantCulture,
            $"spread {spread}\nbumps {bumps}\nreturns {returns}\nfarthest {bestJ} {bestD}\n"));
        return 0;
    }
}
