using System.Globalization;
using System.Text;

internal static class Program
{
    private static int Main(string[] args)
    {
        if (args.Length < 1) return 1;
        byte[] buf = File.ReadAllBytes(args[0]);
        int pos = 0;

        double Next()
        {
            while (pos < buf.Length && (buf[pos] == 32 || buf[pos] == 10 || buf[pos] == 13 || buf[pos] == 9)) pos++;
            int start = pos;
            while (pos < buf.Length && buf[pos] != 32 && buf[pos] != 10 && buf[pos] != 13 && buf[pos] != 9) pos++;
            return double.Parse(Encoding.ASCII.GetString(buf, start, pos - start).AsSpan(), NumberStyles.Float, CultureInfo.InvariantCulture);
        }

        int n = (int)Next();
        int s = (int)Next();
        double dt = Next();
        double P = Next();

        double[] x = new double[n], v = new double[n], m = new double[n];
        double[] k = new double[n], r = new double[n], c = new double[n], f = new double[n];
        for (int i = 0; i < n; i++)
        {
            x[i] = Next();
            v[i] = Next();
            m[i] = Next();
            k[i] = Next();
            r[i] = Next();
            c[i] = Next();
        }

        for (int step = 0; step < s; step++)
        {
            for (int i = 0; i < n - 1; i++)
                f[i] = k[i] * ((x[i + 1] - x[i]) - r[i]);
            f[n - 1] = k[n - 1] * (((x[0] + P) - x[n - 1]) - r[n - 1]);

            {
                double F = (f[0] - f[n - 1]) - (c[0] * v[0]);
                double nv = v[0] + dt * (F / m[0]);
                x[0] = x[0] + dt * nv;
                v[0] = nv;
            }
            for (int i = 1; i < n; i++)
            {
                double F = (f[i] - f[i - 1]) - (c[i] * v[i]);
                double nv = v[i] + dt * (F / m[i]);
                x[i] = x[i] + dt * nv;
                v[i] = nv;
            }
        }

        double K = 0.0, U = 0.0, X = 0.0;
        int J = 0;
        double best = 0.0;
        for (int i = 0; i < n; i++)
        {
            K += ((0.5 * m[i]) * v[i]) * v[i];
            X += x[i];
            double av = v[i] < 0 ? -v[i] : v[i];
            if (av > best) { best = av; J = i; }
        }
        for (int i = 0; i < n - 1; i++)
        {
            double sp = (x[i + 1] - x[i]) - r[i];
            U += ((0.5 * k[i]) * sp) * sp;
        }
        {
            double sp = ((x[0] + P) - x[n - 1]) - r[n - 1];
            U += ((0.5 * k[n - 1]) * sp) * sp;
        }

        var sb = new StringBuilder(200);
        sb.Append("kinetic ").Append(K.ToString("e17", CultureInfo.InvariantCulture)).Append('\n');
        sb.Append("potential ").Append(U.ToString("e17", CultureInfo.InvariantCulture)).Append('\n');
        sb.Append("position ").Append(X.ToString("e17", CultureInfo.InvariantCulture)).Append('\n');
        sb.Append("fastest ").Append(J).Append('\n');
        Console.Out.Write(sb.ToString());
        return 0;
    }
}
