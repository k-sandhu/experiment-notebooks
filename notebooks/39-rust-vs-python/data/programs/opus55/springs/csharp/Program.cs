using System.Globalization;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using System.Runtime.Intrinsics;
using System.Runtime.Intrinsics.X86;
using System.Text;

unsafe static class Program
{
    static int Main(string[] args)
    {
        byte[] data = File.ReadAllBytes(args[0]);
        int pos = 0;

        ReadOnlySpan<byte> Token()
        {
            while (pos < data.Length && data[pos] <= (byte)' ') pos++;
            int start = pos;
            while (pos < data.Length && data[pos] > (byte)' ') pos++;
            return new ReadOnlySpan<byte>(data, start, pos - start);
        }
        double Num() => double.Parse(Token(), NumberStyles.Float, CultureInfo.InvariantCulture);

        int n = int.Parse(Token(), NumberStyles.Integer, CultureInfo.InvariantCulture);
        long steps = long.Parse(Token(), NumberStyles.Integer, CultureInfo.InvariantCulture);
        double dt = Num();
        double P = Num();

        // Aligned buffers with padding lanes past n (k = r = c = 0, m = 1); padding never feeds real lanes.
        nuint cap = (nuint)n + 8;
        double* Alloc()
        {
            double* p = (double*)NativeMemory.AlignedAlloc(cap * sizeof(double), 32);
            new Span<double>(p, (int)cap).Clear();
            return p;
        }
        double* x = Alloc(), v = Alloc(), m = Alloc(), k = Alloc(), r = Alloc(), c = Alloc(), fa = Alloc();
        for (int i = n; i < (int)cap; i++) m[i] = 1.0;
        for (int i = 0; i < n; i++)
        {
            x[i] = Num();
            v[i] = Num();
            m[i] = Num();
            k[i] = Num();
            r[i] = Num();
            c[i] = Num();
        }

        if (Avx.IsSupported)
            SimulateAvx(n, steps, dt, P, x, v, m, k, r, c);
        else
            SimulateScalar(n, steps, dt, P, x, v, m, k, r, c, fa);

        double K = 0.0, U = 0.0, X = 0.0, best = -1.0;
        int J = 0;
        x[n] = x[0] + P;
        for (int i = 0; i < n; i++)
        {
            K += ((0.5 * m[i]) * v[i]) * v[i];
            double st = (x[i + 1] - x[i]) - r[i];
            U += ((0.5 * k[i]) * st) * st;
            X += x[i];
            double a = Math.Abs(v[i]);
            if (a > best)
            {
                best = a;
                J = i;
            }
        }

        var sb = new StringBuilder();
        sb.Append("kinetic ").Append(K.ToString("R", CultureInfo.InvariantCulture)).Append('\n');
        sb.Append("potential ").Append(U.ToString("R", CultureInfo.InvariantCulture)).Append('\n');
        sb.Append("position ").Append(X.ToString("R", CultureInfo.InvariantCulture)).Append('\n');
        sb.Append("fastest ").Append(J.ToString(CultureInfo.InvariantCulture)).Append('\n');
        using var stdout = Console.OpenStandardOutput();
        stdout.Write(Encoding.ASCII.GetBytes(sb.ToString()));
        return 0;
    }

    // One fused pass per step over 4-lane blocks. x[n] is the ghost x[0] + P closing the ring.
    [MethodImpl(MethodImplOptions.AggressiveOptimization)]
    static void SimulateAvx(int n, long steps, double dt, double P, double* x, double* v, double* m, double* k,
                            double* r, double* c)
    {
        int blocks = (n + 3) / 4;
        Vector256<double> vdt = Vector256.Create(dt);
        for (long s = 0; s < steps; s++)
        {
            x[n] = x[0] + P;
            double flast = k[n - 1] * ((x[n] - x[n - 1]) - r[n - 1]);
            Vector256<double> prev = Vector256.Create(flast);
            for (int b = 0; b < blocks; b++)
            {
                int i = b * 4;
                Vector256<double> xi = Avx.LoadAlignedVector256(x + i);
                Vector256<double> xn = Avx.LoadVector256(x + i + 1);
                Vector256<double> f = Avx.Multiply(Avx.LoadAlignedVector256(k + i),
                    Avx.Subtract(Avx.Subtract(xn, xi), Avx.LoadAlignedVector256(r + i)));
                // fs = [prev3, f0, f1, f2]
                Vector256<double> t = Avx.Permute2x128(prev, f, 0x21);
                Vector256<double> fs = Avx.Shuffle(t, f, 5);
                Vector256<double> vi = Avx.LoadAlignedVector256(v + i);
                Vector256<double> F = Avx.Subtract(Avx.Subtract(f, fs), Avx.Multiply(Avx.LoadAlignedVector256(c + i), vi));
                vi = Avx.Add(vi, Avx.Multiply(vdt, Avx.Divide(F, Avx.LoadAlignedVector256(m + i))));
                Avx.StoreAligned(v + i, vi);
                Avx.StoreAligned(x + i, Avx.Add(xi, Avx.Multiply(vdt, vi)));
                prev = f;
            }
        }
    }

    // Portable fallback. fa[0] holds f[n-1] (the f[-1] wrap-around), fa[i+1] holds f[i].
    [MethodImpl(MethodImplOptions.AggressiveOptimization)]
    static void SimulateScalar(int n, long steps, double dt, double P, double* x, double* v, double* m, double* k,
                               double* r, double* c, double* fa)
    {
        for (long s = 0; s < steps; s++)
        {
            x[n] = x[0] + P;
            for (int i = 0; i < n; i++) fa[i + 1] = k[i] * ((x[i + 1] - x[i]) - r[i]);
            fa[0] = fa[n];
            for (int i = 0; i < n; i++)
            {
                double F = (fa[i + 1] - fa[i]) - (c[i] * v[i]);
                double nv = v[i] + dt * (F / m[i]);
                v[i] = nv;
                x[i] = x[i] + dt * nv;
            }
        }
    }
}
