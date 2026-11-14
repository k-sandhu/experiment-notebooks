using System.Globalization;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using System.Runtime.Intrinsics;
using System.Runtime.Intrinsics.X86;
using System.Text;

static unsafe class Program
{
    static ReadOnlySpan<char> Next(string s, ref int pos)
    {
        int n = s.Length;
        while (pos < n && s[pos] <= ' ') pos++;
        int start = pos;
        while (pos < n && s[pos] > ' ') pos++;
        return s.AsSpan(start, pos - start);
    }

    static double* Alloc(int n)
    {
        nuint bytes = (nuint)(n + 8) * 8;
        double* p = (double*)NativeMemory.AlignedAlloc(bytes, 64);
        NativeMemory.Clear(p, bytes);
        return p;
    }

    static string Fmt(double d)
    {
        if (double.IsNaN(d)) return "nan";
        if (double.IsPositiveInfinity(d)) return "inf";
        if (double.IsNegativeInfinity(d)) return "-inf";
        string s = d.ToString("e16", CultureInfo.InvariantCulture);
        int e = s.IndexOf('e');
        if (e < 0) return s;
        int exp = int.Parse(s.AsSpan(e + 1), NumberStyles.AllowLeadingSign, CultureInfo.InvariantCulture);
        string mant = s.Substring(0, e);
        int a = Math.Abs(exp);
        return mant + (exp < 0 ? "e-" : "e+") + (a < 10 ? "0" : "") + a.ToString(CultureInfo.InvariantCulture);
    }

    [MethodImpl(MethodImplOptions.AggressiveOptimization)]
    static void Simulate(double* x, double* v, double* m, double* k, double* r, double* c,
                         int N, long S, double dt, double P)
    {
        int nv = Avx2.IsSupported ? (N & ~3) : 0;
        Vector256<double> vdt = Vector256.Create(dt);

        for (long step = 0; step < S; step++)
        {
            x[N] = x[0] + P;
            double fprev = k[N - 1] * ((x[N] - x[N - 1]) - r[N - 1]);
            int i = 0;

            if (nv > 0)
            {
                Vector256<double> carry = Vector256.Create(fprev);
                for (; i < nv; i += 4)
                {
                    Vector256<double> xi = Avx.LoadVector256(x + i);
                    Vector256<double> xn = Avx.LoadVector256(x + i + 1);
                    Vector256<double> f = Avx.Multiply(
                        Avx.LoadVector256(k + i),
                        Avx.Subtract(Avx.Subtract(xn, xi), Avx.LoadVector256(r + i)));
                    Vector256<double> fp = Avx.Blend(Avx2.Permute4x64(f, 0x90), carry, 0x01);
                    carry = Avx2.Permute4x64(f, 0xFF);
                    Vector256<double> vi = Avx.LoadVector256(v + i);
                    Vector256<double> F = Avx.Subtract(
                        Avx.Subtract(f, fp),
                        Avx.Multiply(Avx.LoadVector256(c + i), vi));
                    Vector256<double> vn = Avx.Add(vi,
                        Avx.Multiply(vdt, Avx.Divide(F, Avx.LoadVector256(m + i))));
                    Avx.Store(v + i, vn);
                    Avx.Store(x + i, Avx.Add(xi, Avx.Multiply(vdt, vn)));
                }
                fprev = carry.ToScalar();
            }

            for (; i < N; i++)
            {
                double f = k[i] * ((x[i + 1] - x[i]) - r[i]);
                double F = (f - fprev) - (c[i] * v[i]);
                fprev = f;
                double vn = v[i] + dt * (F / m[i]);
                v[i] = vn;
                x[i] = x[i] + dt * vn;
            }
        }
    }

    static int Main(string[] args)
    {
        string text = File.ReadAllText(args[0]);
        int pos = 0;
        CultureInfo inv = CultureInfo.InvariantCulture;

        int N = int.Parse(Next(text, ref pos), NumberStyles.Integer, inv);
        long S = long.Parse(Next(text, ref pos), NumberStyles.Integer, inv);
        double dt = double.Parse(Next(text, ref pos), NumberStyles.Float, inv);
        double P = double.Parse(Next(text, ref pos), NumberStyles.Float, inv);

        double* x = Alloc(N);
        double* v = Alloc(N);
        double* m = Alloc(N);
        double* k = Alloc(N);
        double* r = Alloc(N);
        double* c = Alloc(N);

        for (int i = 0; i < N; i++)
        {
            x[i] = double.Parse(Next(text, ref pos), NumberStyles.Float, inv);
            v[i] = double.Parse(Next(text, ref pos), NumberStyles.Float, inv);
            m[i] = double.Parse(Next(text, ref pos), NumberStyles.Float, inv);
            k[i] = double.Parse(Next(text, ref pos), NumberStyles.Float, inv);
            r[i] = double.Parse(Next(text, ref pos), NumberStyles.Float, inv);
            c[i] = double.Parse(Next(text, ref pos), NumberStyles.Float, inv);
        }

        Simulate(x, v, m, k, r, c, N, S, dt, P);

        double K = 0.0, U = 0.0, X = 0.0;
        int J = 0;
        double best = Math.Abs(v[0]);
        x[N] = x[0] + P;
        for (int i = 0; i < N; i++)
        {
            double vi = v[i];
            K += ((0.5 * m[i]) * vi) * vi;
            double s = (x[i + 1] - x[i]) - r[i];
            U += ((0.5 * k[i]) * s) * s;
            X += x[i];
            double a = Math.Abs(vi);
            if (a > best)
            {
                best = a;
                J = i;
            }
        }

        StringBuilder sb = new StringBuilder(160);
        sb.Append("kinetic ").Append(Fmt(K)).Append('\n');
        sb.Append("potential ").Append(Fmt(U)).Append('\n');
        sb.Append("position ").Append(Fmt(X)).Append('\n');
        sb.Append("fastest ").Append(J.ToString(inv)).Append('\n');
        Console.Out.Write(sb.ToString());
        Console.Out.Flush();
        return 0;
    }
}
