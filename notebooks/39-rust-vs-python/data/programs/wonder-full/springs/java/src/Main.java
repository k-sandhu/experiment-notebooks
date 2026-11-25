import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;

public class Main {
    static byte[] data;
    static int pos;

    static void skipWs() {
        while (pos < data.length && data[pos] <= ' ') pos++;
    }
    static long nextLong() {
        skipWs();
        long sign = 1;
        if (pos < data.length && data[pos] == '-') { sign = -1; pos++; }
        else if (pos < data.length && data[pos] == '+') pos++;
        long val = 0;
        while (pos < data.length && data[pos] >= '0' && data[pos] <= '9') {
            val = val * 10 + (data[pos] - '0');
            pos++;
        }
        return val * sign;
    }
    static double nextDouble() {
        skipWs();
        int start = pos;
        while (pos < data.length && data[pos] > ' ') pos++;
        return Double.parseDouble(new String(data, start, pos - start, StandardCharsets.US_ASCII));
    }

    public static void main(String[] args) throws Exception {
        data = Files.readAllBytes(Path.of(args[0]));
        pos = 0;
        int N = (int) nextLong();
        long S = nextLong();
        double dt = nextDouble();
        double P = nextDouble();

        if (N <= 0) {
            System.out.print("kinetic 0.000000000000e+00\npotential 0.000000000000e+00\nposition 0.000000000000e+00\nfastest 0\n");
            return;
        }

        double[] x = new double[N];
        double[] v = new double[N];
        double[] m = new double[N];
        double[] k = new double[N];
        double[] r = new double[N];
        double[] c = new double[N];
        double[] a = new double[N];

        for (int i = 0; i < N; i++) {
            x[i] = nextDouble();
            v[i] = nextDouble();
            m[i] = nextDouble();
            k[i] = nextDouble();
            r[i] = nextDouble();
            c[i] = nextDouble();
            a[i] = dt / m[i];
        }
        data = null;

        int nm1 = N - 1;
        for (long step = 0; step < S; step++) {
            double fLast = k[nm1] * (((x[0] + P) - x[nm1]) - r[nm1]);
            double fPrev = fLast;
            double xcur = x[0];
            for (int i = 0; i < nm1; i++) {
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
                double F = (fLast - fPrev) - c[nm1] * v[nm1];
                double nv = v[nm1] + a[nm1] * F;
                v[nm1] = nv;
                x[nm1] = x[nm1] + dt * nv;
            }
        }

        double K = 0.0, U = 0.0, X = 0.0;
        int J = 0;
        double best = Math.abs(v[0]);
        for (int i = 0; i < N; i++) {
            K += ((0.5 * m[i]) * v[i]) * v[i];
            X += x[i];
            double av = Math.abs(v[i]);
            if (av > best) { best = av; J = i; }
        }
        for (int i = 0; i < nm1; i++) {
            double s = (x[i + 1] - x[i]) - r[i];
            U += ((0.5 * k[i]) * s) * s;
        }
        {
            double s = ((x[0] + P) - x[nm1]) - r[nm1];
            U += ((0.5 * k[nm1]) * s) * s;
        }

        String out = String.format(java.util.Locale.ROOT,
            "kinetic %.12e\npotential %.12e\nposition %.12e\nfastest %d\n", K, U, X, J);
        System.out.print(out);
    }
}
