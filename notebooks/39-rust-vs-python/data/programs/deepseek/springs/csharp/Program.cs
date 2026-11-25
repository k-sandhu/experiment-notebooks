using System;
using System.Globalization;
using System.IO;
using System.Runtime.CompilerServices;

class Program
{
    static void Main(string[] args)
    {
        string text = File.ReadAllText(args[0]);
        int pos = 0;
        int len = text.Length;

        double NextDouble()
        {
            while (pos < len)
            {
                char ch = text[pos];
                if (ch == ' ' || ch == '\n' || ch == '\r' || ch == '\t') pos++;
                else break;
            }
            int start = pos;
            while (pos < len)
            {
                char ch = text[pos];
                if (ch == ' ' || ch == '\n' || ch == '\r' || ch == '\t') break;
                pos++;
            }
            return double.Parse(text.AsSpan(start, pos - start), NumberStyles.Float, CultureInfo.InvariantCulture);
        }

        long NextLong()
        {
            while (pos < len)
            {
                char ch = text[pos];
                if (ch == ' ' || ch == '\n' || ch == '\r' || ch == '\t') pos++;
                else break;
            }
            long v = 0;
            while (pos < len)
            {
                char ch = text[pos];
                if (ch == ' ' || ch == '\n' || ch == '\r' || ch == '\t') break;
                v = v * 10 + (ch - '0');
                pos++;
            }
            return v;
        }

        int n = (int)NextLong();
        long steps = NextLong();
        double dt = NextDouble();
        double P = NextDouble();

        double[] x = new double[n];
        double[] v = new double[n];
        double[] m = new double[n];
        double[] k = new double[n];
        double[] r = new double[n];
        double[] c = new double[n];
        for (int i = 0; i < n; i++)
        {
            x[i] = NextDouble();
            v[i] = NextDouble();
            m[i] = NextDouble();
            k[i] = NextDouble();
            r[i] = NextDouble();
            c[i] = NextDouble();
        }

        Simulate(x, v, m, k, r, c, dt, P, n, steps, out double K, out double U, out double X, out int fastest);

        var inv = CultureInfo.InvariantCulture;
        var sb = new System.Text.StringBuilder(160);
        sb.Append("kinetic ").Append(K.ToString("E12", inv)).Append('\n');
        sb.Append("potential ").Append(U.ToString("E12", inv)).Append('\n');
        sb.Append("position ").Append(X.ToString("E12", inv)).Append('\n');
        sb.Append("fastest ").Append(fastest.ToString(inv)).Append('\n');
        Console.Out.Write(sb.ToString());
    }

    [MethodImpl(MethodImplOptions.AggressiveOptimization)]
    static unsafe void Simulate(double[] x, double[] v, double[] m, double[] k, double[] r, double[] c,
                         double dt, double P, int n, long steps,
                         out double K, out double U, out double X, out int fastest)
    {
        int last = n - 1;
        fixed (double* xp0 = x, vp0 = v, mp0 = m, kp0 = k, rp0 = r, cp0 = c)
        {
            double* xp = xp0, vp = vp0, mp = mp0, kp = kp0, rp = rp0, cp = cp0;
            double* end = xp0 + last;
            for (long t = 0; t < steps; t++)
            {
                double x0 = xp0[0];
                double xl = xp0[last];
                double sLast = ((x0 + P) - xl) - rp0[last];
                double fLast = kp0[last] * sLast;
                double fprev = fLast;

                xp = xp0; vp = vp0; mp = mp0; kp = kp0; rp = rp0; cp = cp0;
                while (xp < end)
                {
                    double s = (xp[1] - xp[0]) - rp[0];
                    double f = kp[0] * s;
                    double F = (f - fprev) - cp[0] * vp[0];
                    double nv = vp[0] + dt * (F / mp[0]);
                    vp[0] = nv;
                    xp[0] = xp[0] + dt * nv;
                    fprev = f;
                    xp++; vp++; mp++; kp++; rp++; cp++;
                }

                double Fl = (fLast - fprev) - cp0[last] * vp0[last];
                double nvl = vp0[last] + dt * (Fl / mp0[last]);
                vp0[last] = nvl;
                xp0[last] = xp0[last] + dt * nvl;
            }
        }

        double ksum = 0.0, usum = 0.0, xsum = 0.0;
        for (int i = 0; i < n; i++)
        {
            ksum += ((0.5 * m[i]) * v[i]) * v[i];
            xsum += x[i];
        }
        for (int i = 0; i < last; i++)
        {
            double s = (x[i + 1] - x[i]) - r[i];
            usum += ((0.5 * k[i]) * s) * s;
        }
        {
            double s = ((x[0] + P) - x[last]) - r[last];
            usum += ((0.5 * k[last]) * s) * s;
        }

        int fst = 0;
        double best = -1.0;
        for (int i = 0; i < n; i++)
        {
            double a = v[i] < 0 ? -v[i] : v[i];
            if (a > best) { best = a; fst = i; }
        }

        K = ksum; U = usum; X = xsum; fastest = fst;
    }
}
