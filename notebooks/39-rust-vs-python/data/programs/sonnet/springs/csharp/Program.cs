using System.Globalization;
using System.Runtime.Intrinsics;

static class Program
{
    static unsafe void Main(string[] args)
    {
        string[] t = File.ReadAllText(args[0]).Split((char[])null, StringSplitOptions.RemoveEmptyEntries);
        var ic = CultureInfo.InvariantCulture;
        int p = 0;
        int n = (int)double.Parse(t[p++], ic);
        long steps = (long)double.Parse(t[p++], ic);
        double dt = double.Parse(t[p++], ic);
        double P = double.Parse(t[p++], ic);
        double[] x = new double[n + 8], v = new double[n + 8], m = new double[n + 8], k = new double[n + 8],
                 r = new double[n + 8], c = new double[n + 8], fa = new double[n + 8];
        for (int i = 0; i < n; i++)
        {
            x[i] = double.Parse(t[p++], ic);
            v[i] = double.Parse(t[p++], ic);
            m[i] = double.Parse(t[p++], ic);
            k[i] = double.Parse(t[p++], ic);
            r[i] = double.Parse(t[p++], ic);
            c[i] = double.Parse(t[p++], ic);
        }
        int n1 = n - 1;
        bool simd = Vector256.IsHardwareAccelerated;
        fixed (double* X = x, V = v, M = m, K = k, R = r, C = c, FA = fa)
        {
            var vdt = Vector256.Create(dt);
            for (long s = 0; s < steps; s++)
            {
                double last = K[n1] * (((X[0] + P) - X[n1]) - R[n1]);
                int i = 0;
                if (simd)
                {
                    for (; i + 4 <= n1; i += 4)
                    {
                        var st = (Vector256.Load(X + i + 1) - Vector256.Load(X + i)) - Vector256.Load(R + i);
                        (Vector256.Load(K + i) * st).Store(FA + i + 1);
                    }
                }
                for (; i < n1; i++) FA[i + 1] = K[i] * ((X[i + 1] - X[i]) - R[i]);
                FA[n] = last;
                FA[0] = last;
                i = 0;
                if (simd)
                {
                    for (; i + 4 <= n; i += 4)
                    {
                        var vv = Vector256.Load(V + i);
                        var F = (Vector256.Load(FA + i + 1) - Vector256.Load(FA + i)) - (Vector256.Load(C + i) * vv);
                        var nv = vv + vdt * (F / Vector256.Load(M + i));
                        nv.Store(V + i);
                        (Vector256.Load(X + i) + vdt * nv).Store(X + i);
                    }
                }
                for (; i < n; i++)
                {
                    double F = (FA[i + 1] - FA[i]) - (C[i] * V[i]);
                    V[i] = V[i] + dt * (F / M[i]);
                    X[i] = X[i] + dt * V[i];
                }
            }
            double kin = 0, pot = 0, pos = 0, best = -1;
            int bi = 0;
            for (int i = 0; i < n; i++)
            {
                kin += ((0.5 * M[i]) * V[i]) * V[i];
                double st = (i < n1) ? ((X[i + 1] - X[i]) - R[i]) : (((X[0] + P) - X[n1]) - R[n1]);
                pot += ((0.5 * K[i]) * st) * st;
                pos += X[i];
                double a = Math.Abs(V[i]);
                if (a > best) { best = a; bi = i; }
            }
            Console.Out.Write("kinetic " + kin.ToString("e12", ic) + "\npotential " + pot.ToString("e12", ic) +
                "\nposition " + pos.ToString("e12", ic) + "\nfastest " + bi.ToString(ic) + "\n");
        }
    }
}
