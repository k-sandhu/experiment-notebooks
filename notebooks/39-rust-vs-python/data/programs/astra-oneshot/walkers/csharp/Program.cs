using System;
using System.Globalization;
using System.IO;
using System.Runtime.CompilerServices;
using System.Threading;

internal static class Program
{
    private struct Result
    {
        public long Spread;
        public long Bumps;
        public long Returns;
        public long FarthestWalker;
        public long FarthestDistance;
    }

    [MethodImpl(MethodImplOptions.AggressiveOptimization)]
    private static Result Simulate(
        long first, long count, long steps, long bound, ulong seed)
    {
        unchecked
        {
            Result result = new Result
            {
                FarthestWalker = long.MaxValue,
                FarthestDistance = -1
            };

            ulong offset = (ulong)bound;
            ulong width = offset * 2;
            long end = first + count;

            for (long walker = first; walker < end; walker++)
            {
                ulong state = seed + (ulong)walker;
                long x = 0;
                long y = 0;
                long bumps = 0;
                long returns = 0;

                for (long step = 0; step < steps; step++)
                {
                    state += 0x9E3779B97F4A7C15UL;
                    ulong z = state;
                    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9UL;
                    z = (z ^ (z >> 27)) * 0x94D049BB133111EBUL;

                    // The final XOR with z >> 31 cannot change the top two bits.
                    long verticalMask = -(long)(z >> 63);
                    long delta = 1L - (long)((z >> 61) & 2UL);
                    long coordinate = x ^ ((x ^ y) & verticalMask);
                    long next = coordinate + delta;

                    if ((ulong)next + offset <= width)
                    {
                        x += delta & ~verticalMask;
                        y += delta & verticalMask;
                        returns += (x | y) == 0 ? 1L : 0L;
                    }
                    else
                    {
                        bumps++;
                    }
                }

                result.Spread += x * x + y * y;
                result.Bumps += bumps;
                result.Returns += returns;

                long distance = Math.Abs(x) + Math.Abs(y);
                if (distance > result.FarthestDistance)
                {
                    result.FarthestDistance = distance;
                    result.FarthestWalker = walker;
                }
            }

            return result;
        }
    }

    private static void Main(string[] args)
    {
        string[] input = File.ReadAllText(args[0]).Split(
            (char[])null, StringSplitOptions.RemoveEmptyEntries);

        var culture = CultureInfo.InvariantCulture;
        long walkers = long.Parse(input[0], culture);
        long steps = long.Parse(input[1], culture);
        long bound = long.Parse(input[2], culture);
        ulong seed = ulong.Parse(input[3], culture);
        int workers = int.Parse(args[1], culture);

        var results = new Result[workers];
        var threads = new Thread[workers - 1];

        long quotient = walkers / workers;
        long remainder = walkers % workers;

        for (int worker = 1; worker < workers; worker++)
        {
            int slot = worker;
            long first = quotient * worker + Math.Min((long)worker, remainder);
            long count = quotient + (worker < remainder ? 1L : 0L);

            threads[worker - 1] = new Thread(() =>
            {
                results[slot] = Simulate(first, count, steps, bound, seed);
            });
            threads[worker - 1].Start();
        }

        results[0] = Simulate(
            0, quotient + (remainder > 0 ? 1L : 0L), steps, bound, seed);

        foreach (Thread thread in threads)
            thread.Join();

        long spread = 0;
        long bumps = 0;
        long returns = 0;
        long farthestWalker = long.MaxValue;
        long farthestDistance = -1;

        foreach (Result result in results)
        {
            spread += result.Spread;
            bumps += result.Bumps;
            returns += result.Returns;

            if (result.FarthestDistance > farthestDistance ||
                (result.FarthestDistance == farthestDistance &&
                 result.FarthestWalker < farthestWalker))
            {
                farthestDistance = result.FarthestDistance;
                farthestWalker = result.FarthestWalker;
            }
        }

        Console.Write(
            $"spread {spread}\n" +
            $"bumps {bumps}\n" +
            $"returns {returns}\n" +
            $"farthest {farthestWalker} {farthestDistance}\n");
    }
}
