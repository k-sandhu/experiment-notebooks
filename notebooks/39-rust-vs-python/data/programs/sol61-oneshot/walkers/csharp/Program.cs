using System;
using System.Globalization;
using System.IO;
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

    private static Result Simulate(
        long walkerCount, long steps, long bound, ulong seed,
        int worker, int workerCount)
    {
        unchecked
        {
            long quotient = walkerCount / workerCount;
            long remainder = walkerCount % workerCount;
            long start = quotient * worker + Math.Min((long)worker, remainder);
            long count = quotient + (worker < remainder ? 1 : 0);
            long end = start + count;
            ulong width = (ulong)bound * 2UL;

            Result result = new Result
            {
                FarthestWalker = -1,
                FarthestDistance = -1
            };

            for (long j = start; j < end; j++)
            {
                ulong state = seed + (ulong)j;
                long x = 0;
                long y = 0;
                long bumps = 0;
                long returns = 0;

                for (long i = 0; i < steps; i++)
                {
                    state += 0x9E3779B97F4A7C15UL;
                    ulong z = state;
                    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9UL;
                    z = (z ^ (z >> 27)) * 0x94D049BB133111EBUL;

                    // The final XOR with z >> 31 cannot change the top two bits.
                    int direction = (int)(z >> 62);
                    int axis = direction >> 1;
                    int delta = 1 - ((direction & 1) << 1);

                    long nx = x + (delta & (axis - 1));
                    long ny = y + (delta & -axis);

                    if ((ulong)(nx + bound) > width ||
                        (ulong)(ny + bound) > width)
                    {
                        bumps++;
                    }
                    else
                    {
                        x = nx;
                        y = ny;
                        returns += (x | y) == 0 ? 1L : 0L;
                    }
                }

                result.Spread += x * x + y * y;
                result.Bumps += bumps;
                result.Returns += returns;

                long distance = Math.Abs(x) + Math.Abs(y);
                if (distance > result.FarthestDistance)
                {
                    result.FarthestDistance = distance;
                    result.FarthestWalker = j;
                }
            }

            return result;
        }
    }

    private static void Main(string[] args)
    {
        string[] input = File.ReadAllText(args[0]).Split(
            (char[])null, StringSplitOptions.RemoveEmptyEntries);

        long walkers = long.Parse(input[0], CultureInfo.InvariantCulture);
        long steps = long.Parse(input[1], CultureInfo.InvariantCulture);
        long bound = long.Parse(input[2], CultureInfo.InvariantCulture);
        ulong seed = ulong.Parse(input[3], CultureInfo.InvariantCulture);
        int workers = int.Parse(args[1], CultureInfo.InvariantCulture);

        Result[] results = new Result[workers];
        Thread[] threads = new Thread[workers - 1];

        for (int i = 0; i < threads.Length; i++)
        {
            int worker = i;
            threads[i] = new Thread(() =>
            {
                results[worker] = Simulate(
                    walkers, steps, bound, seed, worker, workers);
            });
            threads[i].Start();
        }

        results[workers - 1] = Simulate(
            walkers, steps, bound, seed, workers - 1, workers);

        for (int i = 0; i < threads.Length; i++)
            threads[i].Join();

        long spread = 0;
        long bumps = 0;
        long returns = 0;
        long farthestWalker = -1;
        long farthestDistance = -1;

        for (int i = 0; i < workers; i++)
        {
            Result result = results[i];
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
