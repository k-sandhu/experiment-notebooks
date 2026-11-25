using System;
using System.IO;
using System.Globalization;

class Program {
    static byte[] data;
    static int pos;
    static long ParseLong() {
        while (pos < data.Length && data[pos] <= ' ') pos++;
        bool neg = false;
        if (data[pos] == '-') { neg = true; pos++; }
        long val = 0;
        while (pos < data.Length && data[pos] >= '0' && data[pos] <= '9') val = val * 10 + (data[pos++] - '0');
        return neg ? -val : val;
    }
    static double ParseDouble() {
        while (pos < data.Length && data[pos] <= ' ') pos++;
        int start = pos;
        while (pos < data.Length && data[pos] > ' ') pos++;
        return double.Parse(System.Text.Encoding.ASCII.GetString(data, start, pos - start), CultureInfo.InvariantCulture);
    }
    static void Main(string[] args) {
        data = File.ReadAllBytes(args[0]);
        pos = 0;
        int N = (int)ParseLong();
        long S = ParseLong();
        double dt = ParseDouble();
        double P = ParseDouble();
        double[] x = new double[N], v = new double[N], m = new double[N], k = new double[N], r = new double[N], cc = new double[N], dtm = new double[N];
        for (int i = 0; i < N; i++) {
            x[i] = ParseDouble(); v[i] = ParseDouble(); m[i] = ParseDouble();
            k[i] = ParseDouble(); r[i] = ParseDouble(); cc[i] = ParseDouble(); dtm[i] = dt / m[i];
        }
        for (long step = 0; step < S; step++) {
            double fLast = k[N-1] * (((x[0] + P) - x[N-1]) - r[N-1]);
            double prevF = fLast;
            int last = N - 1;
            for (int i = 0; i < last; i++) {
                double fi = k[i] * ((x[i+1] - x[i]) - r[i]);
                double F = (fi - prevF) - (cc[i] * v[i]);
                double nv = v[i] + dtm[i] * F;
                v[i] = nv;
                x[i] = x[i] + dt * nv;
                prevF = fi;
            }
            {
                int i = last;
                double F = (fLast - prevF) - (cc[i] * v[i]);
                double nv = v[i] + dtm[i] * F;
                v[i] = nv;
                x[i] = x[i] + dt * nv;
            }
        }
        double K = 0, U = 0, X = 0;
        for (int i = 0; i < N; i++) { K += ((0.5 * m[i]) * v[i]) * v[i]; X += x[i]; }
        for (int i = 0; i < N-1; i++) { double s = (x[i+1]-x[i])-r[i]; U += ((0.5*k[i])*s)*s; }
        { double s = ((x[0]+P)-x[N-1])-r[N-1]; U += ((0.5*k[N-1])*s)*s; }
        int J = 0; double best = Math.Abs(v[0]);
        for (int i = 1; i < N; i++) { double a = Math.Abs(v[i]); if (a > best) { best = a; J = i; } }
        Console.Out.Write(string.Format(CultureInfo.InvariantCulture, "kinetic {0:e17}\npotential {1:e17}\nposition {2:e17}\nfastest {3}\n", K, U, X, J));
    }
}
