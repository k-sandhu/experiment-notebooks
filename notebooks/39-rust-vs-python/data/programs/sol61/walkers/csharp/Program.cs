using System.Globalization;

internal static class Program
{
    private struct Result
    {
        public long Spread, Bumps, Returns, Walker, Distance;
    }

    private static Result Simulate(long first, long end, long steps, long bound, ulong seed)
    {
        if (steps <= int.MaxValue)
            return SimulateSmall(first, end, (int)steps, (int)Math.Min(bound, steps), seed);
        Result result = new() { Distance = -1 };
        for (long j = first; j < end; ++j)
        {
            ulong state = unchecked(seed + (ulong)j);
            long x = 0, y = 0, bumps = 0, returns = 0;
            for (long k = 0; k < steps; ++k)
            {
                ulong z;
                unchecked
                {
                    z = (state += 0x9E3779B97F4A7C15UL);
                    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9UL;
                    z = (z ^ (z >> 27)) * 0x94D049BB133111EBUL;
                }
                // The last SplitMix xor does not affect the direction bits.
                int d = (int)(z >> 62);
                int axis = d >> 1;
                int delta = 1 - 2 * (d & 1);
                long nx = x + (delta & (axis - 1));
                long ny = y + (delta & -axis);
                if (nx > bound || nx < -bound || ny > bound || ny < -bound)
                {
                    ++bumps;
                }
                else
                {
                    x = nx;
                    y = ny;
                    if ((x | y) == 0) ++returns;
                }
            }
            result.Spread += x * x + y * y;
            result.Bumps += bumps;
            result.Returns += returns;
            long distance = Math.Abs(x) + Math.Abs(y);
            if (distance > result.Distance)
            {
                result.Distance = distance;
                result.Walker = j;
            }
        }
        return result;
    }

    private static Result SimulateSmall(long first, long end, int steps, int bound, ulong seed)
    {
        Result result = new() { Distance = -1 };
        uint limit = (uint)bound * 2;
        for (long j = first; j < end; ++j)
        {
            ulong state = unchecked(seed + (ulong)j);
            int x = 0, y = 0, bumps = 0, returns = 0;
            for (int k = 0; k < steps; ++k)
            {
                ulong z;
                unchecked
                {
                    z = (state += 0x9E3779B97F4A7C15UL);
                    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9UL;
                    z = (z ^ (z >> 27)) * 0x94D049BB133111EBUL;
                }
                int d = (int)(z >> 62);
                int axis = d >> 1;
                int delta = 1 - 2 * (d & 1);
                int nx = x + (delta & (axis - 1));
                int ny = y + (delta & -axis);
                if ((uint)(nx + bound) > limit || (uint)(ny + bound) > limit)
                {
                    ++bumps;
                }
                else
                {
                    x = nx;
                    y = ny;
                    if ((x | y) == 0) ++returns;
                }
            }
            result.Spread += (long)x * x + (long)y * y;
            result.Bumps += bumps;
            result.Returns += returns;
            int distance = Math.Abs(x) + Math.Abs(y);
            if (distance > result.Distance)
            {
                result.Distance = distance;
                result.Walker = j;
            }
        }
        return result;
    }

    public static void Main(string[] args)
    {
        string[] fields = File.ReadAllText(args[0]).Split((char[])null,
            StringSplitOptions.RemoveEmptyEntries);
        long walkers = long.Parse(fields[0], CultureInfo.InvariantCulture);
        long steps = long.Parse(fields[1], CultureInfo.InvariantCulture);
        long bound = long.Parse(fields[2], CultureInfo.InvariantCulture);
        ulong seed = ulong.Parse(fields[3], CultureInfo.InvariantCulture);
        int workers = int.Parse(args[1], CultureInfo.InvariantCulture);
        var results = new Result[workers];
        var threads = new Thread[workers - 1];
        long q = walkers / workers, r = walkers % workers;
        for (int w = 1; w < workers; ++w)
        {
            int index = w;
            long first = q * w + Math.Min(w, r);
            long end = first + q + (w < r ? 1 : 0);
            threads[w - 1] = new Thread(() =>
                results[index] = Simulate(first, end, steps, bound, seed));
            threads[w - 1].Start();
        }
        results[0] = Simulate(0, q + (r > 0 ? 1 : 0), steps, bound, seed);
        foreach (Thread thread in threads) thread.Join();
        Result total = new() { Distance = -1 };
        foreach (Result result in results)
        {
            total.Spread += result.Spread;
            total.Bumps += result.Bumps;
            total.Returns += result.Returns;
            if (result.Distance > total.Distance ||
                (result.Distance == total.Distance && result.Walker < total.Walker))
            {
                total.Distance = result.Distance;
                total.Walker = result.Walker;
            }
        }
        Console.Write($"spread {total.Spread}\nbumps {total.Bumps}\nreturns {total.Returns}\n" +
            $"farthest {total.Walker} {Math.Max(0, total.Distance)}\n");
    }
}
