using System;
using System.IO;
using System.Threading;
using System.Threading.Tasks;

internal static class Program
{
    private const ulong C = 0x9E3779B97F4A7C15UL;
    private const ulong M1 = 0xBF58476D1CE4E5B9UL;
    private const ulong M2 = 0x94D049BB133111EBUL;

    private sealed class Result
    {
        public ulong spread;
        public ulong bumps;
        public ulong returns;
        public ulong farDist;
        public ulong farIdx;
    }

    // Simulate walkers [start, end) and return partial results.
    private static Result RunChunk(ulong start, ulong end, ulong L, ulong B, ulong seed)
    {
        long b = (long)B;
        ulong spread = 0, bumps = 0, returns = 0;
        ulong farDist = 0, farIdx = start;
        for (ulong j = start; j < end; ++j)
        {
            ulong state = seed + j;  // (SEED + j) mod 2^64
            long x = 0, y = 0;
            ulong b2 = 0, r2 = 0;
            for (ulong s = L; s != 0; --s)
            {
                state += C;
                ulong z = state;
                z ^= z >> 30;
                z *= M1;
                z ^= z >> 27;
                z *= M2;
                ulong r = z ^ (z >> 31);
                int d = (int)(r >> 62);
                bool bumped;
                if (d == 0) {
                    if (x < b) { ++x; bumped = false; } else bumped = true;
                } else if (d == 1) {
                    if (x > -b) { --x; bumped = false; } else bumped = true;
                } else if (d == 2) {
                    if (y < b) { ++y; bumped = false; } else bumped = true;
                } else {
                    if (y > -b) { --y; bumped = false; } else bumped = true;
                }
                if (bumped) {
                    ++b2;
                } else if (x == 0 && y == 0) {
                    ++r2;
                }
            }
            spread += (ulong)((long)x * x + (long)y * y);
            bumps += b2;
            returns += r2;
            ulong dist = (ulong)((x < 0 ? -x : x) + (y < 0 ? -y : y));
            // Strictly greater keeps the smallest walker index on ties.
            if (dist > farDist) {
                farDist = dist;
                farIdx = j;
            }
        }
        return new Result { spread = spread, bumps = bumps, returns = returns, farDist = farDist, farIdx = farIdx };
    }

    private static ulong ParseU64(string s) {
        ulong v = 0;
        foreach (char c in s) {
            if (c < '0' || c > '9') break;
            v = v * 10 + (ulong)(c - '0');
        }
        return v;
    }

    public static int Main(string[] args)
    {
        string[] parts = File.ReadAllText(args[0]).Split((char[])null, StringSplitOptions.RemoveEmptyEntries);
        ulong J = ParseU64(parts[0]);
        ulong L = ParseU64(parts[1]);
        ulong B = ParseU64(parts[2]);
        ulong seed = ParseU64(parts[3]);

        int workers = int.Parse(args[1]);
        if (workers < 1) workers = 1;
        int nThreads = J == 0 ? 0 : (int)Math.Min((ulong)workers, J);

        Result[] results = new Result[nThreads];
        if (nThreads > 0) {
            ulong chunk = (J + (ulong)nThreads - 1) / (ulong)nThreads;
            Task[] tasks = new Task[nThreads];
            for (int i = 0; i < nThreads; ++i) {
                int idx = i;
                ulong start = (ulong)i * chunk;
                ulong end = start + chunk;
                if (end > J) end = J;
                tasks[i] = Task.Run(() => results[idx] = RunChunk(start, end, L, B, seed));
            }
            Task.WaitAll(tasks);
        }

        ulong spread = 0, bumps = 0, returns = 0;
        ulong farDist = 0, farIdx = 0;
        for (int i = 0; i < nThreads; ++i) {
            Result r = results[i];
            spread += r.spread;
            bumps += r.bumps;
            returns += r.returns;
            if (r.farDist > farDist || (r.farDist == farDist && r.farIdx < farIdx)) {
                farDist = r.farDist;
                farIdx = r.farIdx;
            }
        }

        Console.WriteLine("spread " + spread);
        Console.WriteLine("bumps " + bumps);
        Console.WriteLine("returns " + returns);
        Console.WriteLine("farthest " + farIdx + " " + farDist);
        return 0;
    }
}
