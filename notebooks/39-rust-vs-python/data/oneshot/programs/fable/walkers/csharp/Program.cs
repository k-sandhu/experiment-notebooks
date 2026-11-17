using System.Runtime.CompilerServices;
using System.Runtime.Intrinsics;
using System.Runtime.Intrinsics.X86;

static class Program
{
    const ulong Gamma = 0x9E3779B97F4A7C15UL;
    const ulong M1 = 0xBF58476D1CE4E5B9UL;
    const ulong M2 = 0x94D049BB133111EBUL;

    sealed class Acc
    {
        public long Spread, Bumps, Returns;
        public long BestD = -1, BestJ = long.MaxValue;

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public void Add(long j, long x, long y, long b, long r)
        {
            Spread += x * x + y * y;
            Bumps += b;
            Returns += r;
            long d = Math.Abs(x) + Math.Abs(y);
            if (d > BestD || (d == BestD && j < BestJ))
            {
                BestD = d;
                BestJ = j;
            }
        }
    }

    static long sJ, sL, sB;
    static ulong sSeed;
    static long sNext, sUnits, sChunk;
    static bool sVector;

    static int Main(string[] args)
    {
        string[] tok = File.ReadAllText(args[0]).Split((char[])null, StringSplitOptions.RemoveEmptyEntries);
        long J = long.Parse(tok[0]);
        long L = long.Parse(tok[1]);
        ulong Bu = ulong.Parse(tok[2]);
        ulong seed = ulong.Parse(tok[3]);

        int workers = 1;
        if (args.Length > 1 && int.TryParse(args[1], out int w) && w > 0) workers = w;

        // A walker can never be farther than L from the origin, so clamping B to L is equivalent.
        long B = (long)Math.Min(Bu, (ulong)Math.Max(L, 1));
        if (B < 1) B = 1;

        sJ = J; sL = L; sB = B; sSeed = seed;
        sVector = Avx2.IsSupported && B <= (1L << 30);
        sUnits = sVector ? (J + 3) / 4 : J;

        long threadsL = Math.Min((long)workers, sUnits);
        if (threadsL < 1) threadsL = 1;
        int threads = (int)threadsL;

        long chunk = sUnits / ((long)threads * 16);
        if (chunk < 1) chunk = 1;
        if (chunk > 4096) chunk = 4096;
        sChunk = chunk;
        sNext = 0;

        Acc[] accs = new Acc[threads];
        for (int i = 0; i < threads; i++) accs[i] = new Acc();

        Thread[] ts = new Thread[threads - 1];
        for (int i = 0; i < ts.Length; i++)
        {
            ts[i] = new Thread(Worker);
            ts[i].Start(accs[i + 1]);
        }
        Worker(accs[0]);
        for (int i = 0; i < ts.Length; i++) ts[i].Join();

        long spread = 0, bumps = 0, returns = 0, bestD = -1, bestJ = long.MaxValue;
        for (int i = 0; i < threads; i++)
        {
            Acc a = accs[i];
            spread += a.Spread;
            bumps += a.Bumps;
            returns += a.Returns;
            if (a.BestD > bestD || (a.BestD == bestD && a.BestJ < bestJ))
            {
                bestD = a.BestD;
                bestJ = a.BestJ;
            }
        }

        Console.Out.Write("spread " + spread.ToString() + "\n" +
                          "bumps " + bumps.ToString() + "\n" +
                          "returns " + returns.ToString() + "\n" +
                          "farthest " + bestJ.ToString() + " " + bestD.ToString() + "\n");
        Console.Out.Flush();
        return 0;
    }

    static void Worker(object o)
    {
        Acc acc = (Acc)o;
        long chunk = sChunk;
        long units = sUnits;
        bool vec = sVector;
        while (true)
        {
            long start = Interlocked.Add(ref sNext, chunk) - chunk;
            if (start >= units) break;
            long end = Math.Min(start + chunk, units);
            if (vec)
            {
                for (long u = start; u < end; u++) RunGroup(u * 4, acc);
            }
            else
            {
                for (long u = start; u < end; u++) RunScalar(u, acc);
            }
        }
    }

    [MethodImpl(MethodImplOptions.AggressiveOptimization)]
    static void RunGroup(long j0, Acc acc)
    {
        ulong b = sSeed + (ulong)j0;
        long L = sL;
        int B = (int)sB;

        Vector256<ulong> s = Vector256.Create(b, b + 1, b + 2, b + 3);
        Vector256<ulong> gamma = Vector256.Create(Gamma);
        Vector256<ulong> m1 = Vector256.Create(M1);
        Vector256<ulong> m2 = Vector256.Create(M2);
        Vector256<int> xorc = Vector256.Create(0, 2, 0, 2, 0, 2, 0, 2);
        Vector256<float> table = Vector256.Create(1, -1, 0, 0, 1, -1, 0, 0).AsSingle();
        Vector256<int> hi = Vector256.Create(B);
        Vector256<int> lo = Vector256.Create(-B);
        Vector256<long> zero = Vector256<long>.Zero;

        Vector256<int> p = Vector256<int>.Zero;
        Vector256<long> bumps = Vector256<long>.Zero;
        Vector256<long> rets = Vector256<long>.Zero;

        if (Avx512DQ.VL.IsSupported)
        {
            for (long i = 0; i < L; i++)
            {
                s = Avx2.Add(s, gamma);
                Vector256<ulong> z = Avx2.Xor(s, Avx2.ShiftRightLogical(s, 30));
                z = Avx512DQ.VL.MultiplyLow(z, m1);
                z = Avx2.Xor(z, Avx2.ShiftRightLogical(z, 27));
                z = Avx512DQ.VL.MultiplyLow(z, m2);

                Vector256<int> hh = Avx2.Shuffle(z.AsInt32(), 0xF5);
                Vector256<int> idx = Avx2.Xor(Avx2.ShiftRightLogical(hh, 30), xorc);
                Vector256<int> delta = Avx.PermuteVar(table, idx).AsInt32();

                Vector256<int> np = Avx2.Min(Avx2.Max(Avx2.Add(p, delta), lo), hi);
                bumps = Avx2.Subtract(bumps, Avx2.CompareEqual(np.AsInt64(), p.AsInt64()));
                rets = Avx2.Subtract(rets, Avx2.CompareEqual(np.AsInt64(), zero));
                p = np;
            }
        }
        else
        {
            Vector256<uint> m1l = m1.AsUInt32();
            Vector256<uint> m1h = Vector256.Create(M1 >> 32).AsUInt32();
            Vector256<uint> m2l = m2.AsUInt32();
            Vector256<uint> m2h = Vector256.Create(M2 >> 32).AsUInt32();

            for (long i = 0; i < L; i++)
            {
                s = Avx2.Add(s, gamma);
                Vector256<ulong> z = Avx2.Xor(s, Avx2.ShiftRightLogical(s, 30));

                Vector256<uint> zl = z.AsUInt32();
                Vector256<uint> zh = Avx2.ShiftRightLogical(z, 32).AsUInt32();
                Vector256<ulong> t1 = Avx2.Multiply(zl, m1l);
                Vector256<ulong> t2 = Avx2.Multiply(zh, m1l);
                Vector256<ulong> t3 = Avx2.Multiply(zl, m1h);
                z = Avx2.Add(t1, Avx2.ShiftLeftLogical(Avx2.Add(t2, t3), 32));

                z = Avx2.Xor(z, Avx2.ShiftRightLogical(z, 27));

                zl = z.AsUInt32();
                zh = Avx2.ShiftRightLogical(z, 32).AsUInt32();
                t1 = Avx2.Multiply(zl, m2l);
                t2 = Avx2.Multiply(zh, m2l);
                t3 = Avx2.Multiply(zl, m2h);
                // low dword of each qword of u == high dword of the 64-bit product
                Vector256<ulong> u = Avx2.Add(Avx2.Add(Avx2.ShiftRightLogical(t1, 32), t2), t3);

                Vector256<int> hh = Avx2.Shuffle(u.AsInt32(), 0xA0);
                Vector256<int> idx = Avx2.Xor(Avx2.ShiftRightLogical(hh, 30), xorc);
                Vector256<int> delta = Avx.PermuteVar(table, idx).AsInt32();

                Vector256<int> np = Avx2.Min(Avx2.Max(Avx2.Add(p, delta), lo), hi);
                bumps = Avx2.Subtract(bumps, Avx2.CompareEqual(np.AsInt64(), p.AsInt64()));
                rets = Avx2.Subtract(rets, Avx2.CompareEqual(np.AsInt64(), zero));
                p = np;
            }
        }

        long J = sJ;
        for (int k = 0; k < 4; k++)
        {
            long j = j0 + k;
            if (j >= J) break;
            long x = p.GetElement(2 * k);
            long y = p.GetElement(2 * k + 1);
            acc.Add(j, x, y, bumps.GetElement(k), rets.GetElement(k));
        }
    }

    [MethodImpl(MethodImplOptions.AggressiveOptimization)]
    static void RunScalar(long j, Acc acc)
    {
        ulong s = sSeed + (ulong)j;
        long L = sL;
        long B = sB;
        long x = 0, y = 0, bumps = 0, rets = 0;
        for (long i = 0; i < L; i++)
        {
            s += Gamma;
            ulong z = s;
            z = (z ^ (z >> 30)) * M1;
            z = (z ^ (z >> 27)) * M2;
            long sgn = 1 - (long)((z >> 61) & 2);
            if ((long)z >= 0)
            {
                long nx = x + sgn;
                if (nx > B || nx < -B) bumps++;
                else
                {
                    x = nx;
                    if ((x | y) == 0) rets++;
                }
            }
            else
            {
                long ny = y + sgn;
                if (ny > B || ny < -B) bumps++;
                else
                {
                    y = ny;
                    if ((x | y) == 0) rets++;
                }
            }
        }
        acc.Add(j, x, y, bumps, rets);
    }
}
