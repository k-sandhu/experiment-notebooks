import java.io.IOException;
import java.math.BigDecimal;
import java.math.MathContext;
import java.math.RoundingMode;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;

public class Main {
    // Cache block size: 8 arrays * 8 bytes * 256 = 16 KB, fits in L1.
    private static final int CHUNK = 256;

    private static byte[] buf;
    private static int pos;

    private static String next() {
        final byte[] b = buf;
        final int n = b.length;
        int p = pos;
        while (p < n && b[p] <= ' ') p++;
        final int s = p;
        while (p < n && b[p] > ' ') p++;
        pos = p;
        return new String(b, s, p - s, StandardCharsets.ISO_8859_1);
    }

    // f[i] = k[i] * ((x[i+1] - x[i]) - r[i]) for i in [a, e), e <= n-1
    private static void forces(double[] x, double[] r, double[] k, double[] f, int a, int e) {
        for (int i = a; i < e; i++) {
            f[i] = k[i] * ((x[i + 1] - x[i]) - r[i]);
        }
    }

    // fp[i] holds f[i-1]
    private static void velocities(double[] v, double[] f, double[] fp, double[] c, double[] m,
                                   double dt, int a, int b) {
        for (int i = a; i < b; i++) {
            v[i] = v[i] + dt * (((f[i] - fp[i]) - c[i] * v[i]) / m[i]);
        }
    }

    private static void positions(double[] x, double[] v, double dt, int a, int b) {
        for (int i = a; i < b; i++) {
            x[i] = x[i] + dt * v[i];
        }
    }

    private static void step(double[] x, double[] v, double[] m, double[] k, double[] r, double[] c,
                             double[] f, double[] fp, int n, double dt, double p) {
        final int last = n - 1;
        // Last spring uses old x[0] and old x[n-1]; compute before anything is updated.
        final double fl = k[last] * (((x[0] + p) - x[last]) - r[last]);
        fp[0] = fl;
        for (int a = 0; a < n; a += CHUNK) {
            final int b = Math.min(a + CHUNK, n);
            final int e = Math.min(b, last);
            // Uses x[a..e] (x[e] belongs to the next chunk or is still old), all old values.
            forces(x, r, k, f, a, e);
            if (b == n) {
                f[last] = fl;
            }
            System.arraycopy(f, a, fp, a + 1, b - a);
            velocities(v, f, fp, c, m, dt, a, b);
            positions(x, v, dt, a, b);
        }
    }

    private static void fmt(StringBuilder sb, double d) {
        if (d != d || Double.isInfinite(d)) {
            sb.append(d);
            return;
        }
        if (d == 0.0) {
            if (1.0 / d < 0) sb.append('-');
            sb.append("0.0000000000000000e+00");
            return;
        }
        BigDecimal bd = new BigDecimal(d).round(new MathContext(17, RoundingMode.HALF_EVEN));
        String digits = bd.unscaledValue().abs().toString();
        int len = digits.length();
        int exp = len - 1 - bd.scale();
        if (d < 0) sb.append('-');
        sb.append(digits.charAt(0)).append('.');
        sb.append(digits, 1, len);
        for (int i = len; i < 17; i++) sb.append('0');
        sb.append('e').append(exp < 0 ? '-' : '+');
        int ae = Math.abs(exp);
        if (ae < 10) sb.append('0');
        sb.append(ae);
    }

    public static void main(String[] args) throws IOException {
        buf = Files.readAllBytes(Paths.get(args[0]));
        pos = 0;

        final int n = Integer.parseInt(next());
        final long steps = Long.parseLong(next());
        final double dt = Double.parseDouble(next());
        final double p = Double.parseDouble(next());

        final double[] x = new double[n];
        final double[] v = new double[n];
        final double[] m = new double[n];
        final double[] k = new double[n];
        final double[] r = new double[n];
        final double[] c = new double[n];
        for (int i = 0; i < n; i++) {
            x[i] = Double.parseDouble(next());
            v[i] = Double.parseDouble(next());
            m[i] = Double.parseDouble(next());
            k[i] = Double.parseDouble(next());
            r[i] = Double.parseDouble(next());
            c[i] = Double.parseDouble(next());
        }
        buf = null;

        final double[] f = new double[n];
        final double[] fp = new double[n + 1];

        for (long t = 0; t < steps; t++) {
            step(x, v, m, k, r, c, f, fp, n, dt, p);
        }

        double kin = 0.0, pot = 0.0, sumX = 0.0;
        int best = 0;
        double bestAbs = Math.abs(v[0]);
        for (int i = 0; i < n; i++) {
            final double vi = v[i];
            kin += ((0.5 * m[i]) * vi) * vi;
            sumX += x[i];
            final double av = Math.abs(vi);
            if (av > bestAbs) {
                bestAbs = av;
                best = i;
            }
        }
        final int last = n - 1;
        for (int i = 0; i < last; i++) {
            final double s = (x[i + 1] - x[i]) - r[i];
            pot += ((0.5 * k[i]) * s) * s;
        }
        {
            final double s = ((x[0] + p) - x[last]) - r[last];
            pot += ((0.5 * k[last]) * s) * s;
        }

        StringBuilder sb = new StringBuilder(160);
        sb.append("kinetic ");
        fmt(sb, kin);
        sb.append('\n');
        sb.append("potential ");
        fmt(sb, pot);
        sb.append('\n');
        sb.append("position ");
        fmt(sb, sumX);
        sb.append('\n');
        sb.append("fastest ").append(best).append('\n');

        byte[] out = sb.toString().getBytes(StandardCharsets.ISO_8859_1);
        System.out.write(out, 0, out.length);
        System.out.flush();
    }
}
