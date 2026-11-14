using System;
using System.Globalization;
using System.IO;
using System.Runtime.CompilerServices;
using System.Text;

internal static class Program
{
    private static string text = "";
    private static int pos;

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    private static ReadOnlySpan<char> NextToken()
    {
        int len = text.Length;
        while (pos < len && text[pos] <= ' ') pos++;
        int start = pos;
        while (pos < len && text[pos] > ' ') pos++;
        return text.AsSpan(start, pos - start);
    }

    private static long NextLong() => long.Parse(NextToken(), CultureInfo.InvariantCulture);
    private static double NextDouble() => double.Parse(NextToken(), NumberStyles.Float, CultureInfo.InvariantCulture);

    private static void Main(string[] args)
    {
        text = Encoding.ASCII.GetString(File.ReadAllBytes(args[0]));
        pos = 0;
        int N = (int)NextLong();
        long S = NextLong();
        double dt = NextDouble();
        double P = NextDouble();

        if (N <= 0)
        {
            Console.Out.Write("kinetic 0.000000000000e+00\npotential 0.000000000000e+00\nposition 0.000000000000e+00\nfastest 0\n");
            return;
        }

        double[] x = new double[N];
        double[] v = new double[N];
        double[] m = new double[N];
        double[] k = new double[N];
        double[] r = new double[N];
        double[] c = new double[N];
        double[] a = new double[N]; // dt / m

        for (int i = 0; i < N; i++)
        {
            x[i] = NextDouble();
            v[i] = NextDouble();
            m[i] = NextDouble();
            k[i] = NextDouble();
            r[i] = NextDouble();
            c[i] = NextDouble();
            a[i] = dt / m[i];
        }
        text = "";

        int nm1 = N - 1;
        // Fused pass: x[i] is only needed for f[i] and f[i-1], both computed
        // before x[i] is updated, so one in-place sweep suffices.
        for (long step = 0; step < S; step++)
        {
            double fLast = k[nm1] * (((x[0] + P) - x[nm1]) - r[nm1]);
            double fPrev = fLast;
            double xcur = x[0];
            for (int i = 0; i < nm1; i++)
            {
                double xnext = x[i + 1];
                double fi = k[i] * ((xnext - xcur) - r[i]);
                double vi = v[i];
                double nv = vi + a[i] * ((fi - fPrev) - c[i] * vi);
                v[i] = nv;
                x[i] = xcur + dt * nv;
                fPrev = fi;
                xcur = xnext;
            }
            {
                double vi = v[nm1];
                double nv = vi + a[nm1] * ((fLast - fPrev) - c[nm1] * vi);
                v[nm1] = nv;
                x[nm1] = x[nm1] + dt * nv;
            }
        }

        double K = 0.0, U = 0.0, X = 0.0;
        int J = 0;
        double best = Math.Abs(v[0]);
        for (int i = 0; i < N; i++)
        {
            K += ((0.5 * m[i]) * v[i]) * v[i];
            X += x[i];
            double av = Math.Abs(v[i]);
            if (av > best) { best = av; J = i; }
        }
        for (int i = 0; i < nm1; i++)
        {
            double s = (x[i + 1] - x[i]) - r[i];
            U += ((0.5 * k[i]) * s) * s;
        }
        {
            double s = ((x[0] + P) - x[nm1]) - r[nm1];
            U += ((0.5 * k[nm1]) * s) * s;
        }

        Console.Out.Write(string.Create(CultureInfo.InvariantCulture,
            $"kinetic {K:E12}\npotential {U:E12}\nposition {X:E12}\nfastest {J}\n"));
    }
}
