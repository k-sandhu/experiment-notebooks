import java.io.File;
import java.util.Locale;
import java.util.Scanner;

public class Main {
    public static void main(String[] args) throws Exception {
        Scanner sc = new Scanner(new File(args[0]));
        int N = sc.nextInt();
        int S = sc.nextInt();
        double dt = sc.nextDouble();
        double P = sc.nextDouble();
        double[] x = new double[N];
        double[] v = new double[N];
        double[] m = new double[N];
        double[] k = new double[N];
        double[] r = new double[N];
        double[] c = new double[N];
        double[] f = new double[N];
        for (int i = 0; i < N; ++i) {
            x[i] = sc.nextDouble();
            v[i] = sc.nextDouble();
            m[i] = sc.nextDouble();
            k[i] = sc.nextDouble();
            r[i] = sc.nextDouble();
            c[i] = sc.nextDouble();
        }
        sc.close();

        final int nm1 = N - 1;
        for (int step = 0; step < S; ++step) {
            // Stretches and spring forces from the old positions (read-only).
            for (int i = 0; i < nm1; ++i) {
                f[i] = k[i] * ((x[i + 1] - x[i]) - r[i]);
            }
            f[nm1] = k[nm1] * (((x[0] + P) - x[nm1]) - r[nm1]);

            // Forces, then velocities, then positions. f is read-only here.
            double F = (f[0] - f[nm1]) - (c[0] * v[0]);
            v[0] = v[0] + dt * (F / m[0]);
            x[0] = x[0] + dt * v[0];
            for (int i = 1; i < N; ++i) {
                F = (f[i] - f[i - 1]) - (c[i] * v[i]);
                v[i] = v[i] + dt * (F / m[i]);
                x[i] = x[i] + dt * v[i];
            }
        }

        double K = 0.0;
        double U = 0.0;
        double X = 0.0;
        int J = 0;
        double best = -1.0;
        for (int i = 0; i < N; ++i) {
            double xnext = (i + 1 < N) ? x[i + 1] : x[0] + P;
            double s = (xnext - x[i]) - r[i];
            U += ((0.5 * k[i]) * s) * s;
            K += ((0.5 * m[i]) * v[i]) * v[i];
            X += x[i];
            double av = v[i] < 0.0 ? -v[i] : v[i];
            if (av > best) {  // strict: on a tie the smallest index wins
                best = av;
                J = i;
            }
        }

        System.out.printf(Locale.ROOT, "kinetic %.12e%n", K);
        System.out.printf(Locale.ROOT, "potential %.12e%n", U);
        System.out.printf(Locale.ROOT, "position %.12e%n", X);
        System.out.println("fastest " + J);
    }
}
