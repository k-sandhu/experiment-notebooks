import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

public class Main {
    private static byte[] buf;
    private static int pos;

    private static void skipSpace() {
        while (pos < buf.length && buf[pos] <= ' ') pos++;
    }

    private static String token() {
        skipSpace();
        int start = pos;
        while (pos < buf.length && buf[pos] > ' ') pos++;
        return new String(buf, start, pos - start, java.nio.charset.StandardCharsets.ISO_8859_1);
    }

    private static final double[] POW10 = {
        1e0, 1e1, 1e2, 1e3, 1e4, 1e5, 1e6, 1e7, 1e8, 1e9, 1e10, 1e11,
        1e12, 1e13, 1e14, 1e15, 1e16, 1e17, 1e18, 1e19, 1e20, 1e21, 1e22
    };

    // Clinger's fast path: when the decimal mantissa fits in 53 bits and the power of ten is at most 1e22,
    // one exact-operand multiply or divide is correctly rounded. Anything else goes to Double.parseDouble.
    private static double num() {
        skipSpace();
        final byte[] b = buf;
        final int start = pos;
        int p = pos;
        boolean neg = false;
        if (p < b.length && (b[p] == '-' || b[p] == '+')) {
            neg = b[p] == '-';
            p++;
        }
        long mant = 0;
        int digits = 0, exp = 0;
        boolean any = false;
        while (p < b.length && b[p] >= '0' && b[p] <= '9') {
            any = true;
            if (mant != 0 || b[p] != '0') {
                mant = mant * 10 + (b[p] - '0');
                digits++;
            }
            if (digits > 18) return slowNum(start);
            p++;
        }
        if (p < b.length && b[p] == '.') {
            p++;
            while (p < b.length && b[p] >= '0' && b[p] <= '9') {
                any = true;
                if (mant != 0 || b[p] != '0') {
                    mant = mant * 10 + (b[p] - '0');
                    digits++;
                }
                if (digits > 18) return slowNum(start);
                exp--;
                p++;
            }
        }
        if (!any) return slowNum(start);
        if (p < b.length && (b[p] == 'e' || b[p] == 'E')) {
            p++;
            boolean eneg = false;
            if (p < b.length && (b[p] == '-' || b[p] == '+')) {
                eneg = b[p] == '-';
                p++;
            }
            int e = 0;
            boolean edig = false;
            while (p < b.length && b[p] >= '0' && b[p] <= '9') {
                edig = true;
                if (e < 100000) e = e * 10 + (b[p] - '0');
                p++;
            }
            if (!edig) return slowNum(start);
            exp += eneg ? -e : e;
        }
        if (p < b.length && b[p] > ' ') return slowNum(start);
        if (mant >= (1L << 53) || exp < -22 || exp > 22) return slowNum(start);
        pos = p;
        double d = (double) mant;
        d = exp < 0 ? d / POW10[-exp] : d * POW10[exp];
        return neg ? -d : d;
    }

    private static double slowNum(int start) {
        pos = start;
        return Double.parseDouble(token());
    }

    // One fused pass per step; x[n] is the ghost x[0] + P closing the ring. Each spring force is computed
    // from old positions just before its left mass moves, and carried to the next mass in fprev.
    private static void simulate(int n, long steps, double dt, double P, double[] x, double[] v, double[] m,
                                 double[] k, double[] r, double[] c) {
        for (long s = 0; s < steps; s++) {
            x[n] = x[0] + P;
            step(n, dt, x, v, m, k, r, c);
        }
    }

    private static void step(int n, double dt, double[] x, double[] v, double[] m, double[] k, double[] r,
                             double[] c) {
        double fprev = k[n - 1] * ((x[n] - x[n - 1]) - r[n - 1]);
        double xi = x[0];
        for (int i = 0; i < n; i++) {
            double xn = x[i + 1];
            double f = k[i] * ((xn - xi) - r[i]);
            double vi = v[i];
            double F = (f - fprev) - (c[i] * vi);
            vi = vi + dt * (F / m[i]);
            v[i] = vi;
            x[i] = xi + dt * vi;
            fprev = f;
            xi = xn;
        }
    }

    public static void main(String[] args) throws IOException {
        buf = Files.readAllBytes(Path.of(args[0]));
        pos = 0;
        int n = Integer.parseInt(token());
        long steps = Long.parseLong(token());
        double dt = num();
        double P = num();

        double[] x = new double[n + 1], v = new double[n], m = new double[n];
        double[] k = new double[n], r = new double[n], c = new double[n];
        for (int i = 0; i < n; i++) {
            x[i] = num();
            v[i] = num();
            m[i] = num();
            k[i] = num();
            r[i] = num();
            c[i] = num();
        }

        simulate(n, steps, dt, P, x, v, m, k, r, c);

        double K = 0.0, U = 0.0, X = 0.0, best = -1.0;
        int J = 0;
        x[n] = x[0] + P;
        for (int i = 0; i < n; i++) {
            K += ((0.5 * m[i]) * v[i]) * v[i];
            double st = (x[i + 1] - x[i]) - r[i];
            U += ((0.5 * k[i]) * st) * st;
            X += x[i];
            double a = Math.abs(v[i]);
            if (a > best) {
                best = a;
                J = i;
            }
        }
        System.out.print("kinetic " + K + "\npotential " + U + "\nposition " + X + "\nfastest " + J + "\n");
    }
}
