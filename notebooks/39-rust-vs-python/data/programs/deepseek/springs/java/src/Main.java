import java.io.BufferedInputStream;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.Locale;

public class Main {
    private byte[] buf;
    private int pos;
    private int len;

    private double nextDouble() {
        while (pos < len) {
            byte b = buf[pos];
            if (b == ' ' || b == '\n' || b == '\r' || b == '\t') pos++;
            else break;
        }
        int start = pos;
        while (pos < len) {
            byte b = buf[pos];
            if (b == ' ' || b == '\n' || b == '\r' || b == '\t') break;
            pos++;
        }
        return Double.parseDouble(new String(buf, start, pos - start, java.nio.charset.StandardCharsets.ISO_8859_1));
    }

    private long nextLong() {
        while (pos < len) {
            byte b = buf[pos];
            if (b == ' ' || b == '\n' || b == '\r' || b == '\t') pos++;
            else break;
        }
        int start = pos;
        while (pos < len) {
            byte b = buf[pos];
            if (b == ' ' || b == '\n' || b == '\r' || b == '\t') break;
            pos++;
        }
        long v = 0;
        for (int i = start; i < pos; i++) v = v * 10 + (buf[i] - '0');
        return v;
    }

    public static void main(String[] args) throws IOException {
        Main main = new Main();
        main.run(args[0]);
    }

    private void run(String path) throws IOException {
        try (InputStream in = new BufferedInputStream(new FileInputStream(path), 1 << 16)) {
            buf = in.readAllBytes();
        }
        pos = 0;
        len = buf.length;

        int n = (int) nextLong();
        long steps = nextLong();
        double dt = nextDouble();
        double P = nextDouble();

        double[] x = new double[n];
        double[] v = new double[n];
        double[] m = new double[n];
        double[] k = new double[n];
        double[] r = new double[n];
        double[] c = new double[n];
        for (int i = 0; i < n; i++) {
            x[i] = nextDouble();
            v[i] = nextDouble();
            m[i] = nextDouble();
            k[i] = nextDouble();
            r[i] = nextDouble();
            c[i] = nextDouble();
        }

        int last = n - 1;
        for (long t = 0; t < steps; t++) {
            double x0 = x[0];
            double xl = x[last];
            double sLast = ((x0 + P) - xl) - r[last];
            double fLast = k[last] * sLast;
            double fprev = fLast;

            for (int i = 0; i < last; i++) {
                double s = (x[i + 1] - x[i]) - r[i];
                double f = k[i] * s;
                double F = (f - fprev) - c[i] * v[i];
                double nv = v[i] + dt * (F / m[i]);
                v[i] = nv;
                x[i] = x[i] + dt * nv;
                fprev = f;
            }

            double F = (fLast - fprev) - c[last] * v[last];
            double nv = v[last] + dt * (F / m[last]);
            v[last] = nv;
            x[last] = x[last] + dt * nv;
        }

        double K = 0.0, U = 0.0, X = 0.0;
        for (int i = 0; i < n; i++) {
            K += ((0.5 * m[i]) * v[i]) * v[i];
            X += x[i];
        }
        for (int i = 0; i < last; i++) {
            double s = (x[i + 1] - x[i]) - r[i];
            U += ((0.5 * k[i]) * s) * s;
        }
        {
            double s = ((x[0] + P) - x[last]) - r[last];
            U += ((0.5 * k[last]) * s) * s;
        }

        int fastest = 0;
        double best = -1.0;
        for (int i = 0; i < n; i++) {
            double a = v[i] < 0 ? -v[i] : v[i];
            if (a > best) { best = a; fastest = i; }
        }

        StringBuilder sb = new StringBuilder(128);
        sb.append("kinetic ").append(String.format(Locale.ROOT, "%.12e", K)).append('\n');
        sb.append("potential ").append(String.format(Locale.ROOT, "%.12e", U)).append('\n');
        sb.append("position ").append(String.format(Locale.ROOT, "%.12e", X)).append('\n');
        sb.append("fastest ").append(fastest).append('\n');
        System.out.print(sb);
    }
}
