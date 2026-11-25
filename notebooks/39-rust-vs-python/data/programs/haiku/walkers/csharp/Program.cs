using System;
using System.IO;
using System.Text;
using System.Threading;

// Random walkers: J independent SplitMix64-driven walks inside a box, spread over WORKERS threads.
static class Program
{
    // SplitMix64 increment. ulong arithmetic wraps on overflow (the project is not checked).
    const ulong Gamma = 0x9E3779B97F4A7C15UL;

    // Totals for one contiguous range of walkers.
    struct Partial
    {
        public ulong Spread;
        public long Bumps;
        public long Returns;
        public long FarDist;
        public long FarWalker;
    }

    static int Main(string[] args)
    {
        if (args.Length < 1)
        {
            Console.Error.WriteLine("usage: solution INPUT_PATH [WORKERS]");
            return 2;
        }
        string[] fields = File.ReadAllText(args[0]).Split((char[])null, StringSplitOptions.RemoveEmptyEntries);
        long walkers = long.Parse(fields[0]);
        long steps = long.Parse(fields[1]);
        long box = long.Parse(fields[2]);
        ulong seed = ulong.Parse(fields[3]);
        int workers = args.Length >= 2 ? int.Parse(args[1]) : 1;
        workers = (int)Math.Max(1, Math.Min(workers, walkers));

        // Worker w handles the contiguous walkers [first, last).
        Partial[] parts = new Partial[workers];
        Thread[] threads = new Thread[workers];
        for (int w = 0; w < workers; w++)
        {
            int id = w;
            long first = walkers * id / workers;
            long last = walkers * (id + 1) / workers;
            threads[id] = new Thread(() => parts[id] = WalkRange(seed, steps, box, first, last));
            threads[id].Start();
        }
        foreach (Thread t in threads)
        {
            t.Join();
        }

        // Parts are in walker order, so the first part holding the maximum also holds the smallest index.
        Partial total = new Partial { FarDist = -1 };
        foreach (Partial part in parts)
        {
            total.Spread += part.Spread;
            total.Bumps += part.Bumps;
            total.Returns += part.Returns;
            if (part.FarDist > total.FarDist)
            {
                total.FarDist = part.FarDist;
                total.FarWalker = part.FarWalker;
            }
        }
        if (total.FarDist < 0)
        {
            total.FarDist = 0;
        }

        // Write raw bytes so the output uses LF line endings on every platform.
        string text = "spread " + total.Spread + "\nbumps " + total.Bumps + "\nreturns " + total.Returns
            + "\nfarthest " + total.FarWalker + " " + total.FarDist + "\n";
        byte[] bytes = Encoding.ASCII.GetBytes(text);
        using (Stream stdout = Console.OpenStandardOutput())
        {
            stdout.Write(bytes, 0, bytes.Length);
        }
        return 0;
    }

    static Partial WalkRange(ulong seed, long steps, long box, long first, long last)
    {
        Partial acc = new Partial { FarDist = -1 };
        for (long j = first; j < last; j++)
        {
            WalkOne(seed, steps, box, j, ref acc);
        }
        return acc;
    }

    // Runs walker j to the end of its steps and folds its result into acc.
    // The direction is computed arithmetically rather than with a switch, so the
    // unpredictable random choice never causes a branch misprediction.
    static void WalkOne(ulong seed, long steps, long box, long j, ref Partial acc)
    {
        ulong state = seed + (ulong)j;
        long x = 0;
        long y = 0;
        long bumps = 0;
        long returns = 0;
        for (long i = 0; i < steps; i++)
        {
            state += Gamma;
            ulong z = state;
            z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9UL;
            z = (z ^ (z >> 27)) * 0x94D049BB133111EBUL;
            // z ^ (z >> 31) has the same top two bits as z, so the final mix is skipped.
            ulong d = z >> 62;
            long isY = (long)(d >> 1);
            long sign = 1 - 2 * (long)(d & 1);
            long dx = sign * (1 - isY);
            long dy = sign * isY;
            long nx = x + dx;
            long ny = y + dy;
            if (nx < -box || nx > box || ny < -box || ny > box)
            {
                bumps++;
            }
            else
            {
                x = nx;
                y = ny;
                if ((x | y) == 0)
                {
                    returns++;
                }
            }
        }
        long dist = Math.Abs(x) + Math.Abs(y);
        acc.Spread += (ulong)(x * x + y * y);
        acc.Bumps += bumps;
        acc.Returns += returns;
        // Walkers are visited in increasing order, so a strict comparison keeps the smallest index on a tie.
        if (dist > acc.FarDist)
        {
            acc.FarDist = dist;
            acc.FarWalker = j;
        }
    }
}
