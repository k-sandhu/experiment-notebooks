import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.charset.StandardCharsets;
import java.util.Locale;

public class Main {
    private static int pos;
    private static byte[] buf;

    private static void skipWs() {
        while (pos < buf.length) {
            byte b = buf[pos];
            if (b == ' ' || b == '\n' || b == '\r' || b == '\t') pos++;
            else break;
        }
    }

    private static double nextd() {
        skipWs();
        int start = pos;
        while (pos < buf.length) {
            byte b = buf[pos];
            if (b == ' ' || b == '\n' || b == '\r' || b == '\t') break;
            pos++;
        }
        return Double.parseDouble(new String(buf, start, pos - start, StandardCharsets.US_ASCII));
    }

    public static void main(String[] args) throws IOException {
        buf = Files.readAllBytes(Path.of(args[0]));
        int n = (int) nextd();
        int s = (int) nextd();
        double dt = nextd();
        double P = nextd();

        double[] x = new double[n], v = new double[n], m = new double[n];
        double[] k = new double[n], r = new double[n], c = new double[n], f = new double[n];
        for (int i = 0; i < n; i++) {
            x[i] = nextd();
            v[i] = nextd();
            m[i] = nextd();
            k[i] = nextd();
            r[i] = nextd();
            c[i] = nextd();
        }

        for (int step = 0; step < s; step++) {
            for (int i = 0; i < n - 1; i++) {
                f[i] = k[i] * ((x[i + 1] - x[i]) - r[i]);
            }
            f[n - 1] = k[n - 1] * (((x[0] + P) - x[n - 1]) - r[n - 1]);

            {
                double F = (f[0] - f[n - 1]) - (c[0] * v[0]);
                double nv = v[0] + dt * (F / m[0]);
                x[0] = x[0] + dt * nv;
                v[0] = nv;
            }
            for (int i = 1; i < n; i++) {
                double F = (f[i] - f[i - 1]) - (c[i] * v[i]);
                double nv = v[i] + dt * (F / m[i]);
                x[i] = x[i] + dt * nv;
                v[i] = nv;
            }
        }

        double K = 0.0, U = 0.0, X = 0.0;
        int J = 0;
        double best = 0.0;
        for (int i = 0; i < n; i++) {
            K += ((0.5 * m[i]) * v[i]) * v[i];
            X += x[i];
            double av = v[i] < 0 ? -v[i] : v[i];
            if (av > best) { best = av; J = i; }
        }
        for (int i = 0; i < n - 1; i++) {
            double sp = (x[i + 1] - x[i]) - r[i];
            U += ((0.5 * k[i]) * sp) * sp;
        }
        {
            double sp = ((x[0] + P) - x[n - 1]) - r[n - 1];
            U += ((0.5 * k[n - 1]) * sp) * sp;
        }

        StringBuilder sb = new StringBuilder(160);
        sb.append("kinetic ").append(String.format(Locale.ROOT, "%.17e", K)).append('\n');
        sb.append("potential ").append(String.format(Locale.ROOT, "%.17e", U)).append('\n');
        sb.append("position ").append(String.format(Locale.ROOT, "%.17e", X)).append('\n');
        sb.append("fastest ").append(J).append('\n');
        System.out.print(sb);
    }
}
