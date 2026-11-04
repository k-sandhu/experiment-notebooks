import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.Locale;

public class Main {
    public static void main(String[] args) throws Exception {
        String text = new String(Files.readAllBytes(Paths.get(args[0])), StandardCharsets.ISO_8859_1);
        String[] t = text.trim().split("\\s+");
        int p = 0;
        int n = (int) Double.parseDouble(t[p++]);
        long steps = (long) Double.parseDouble(t[p++]);
        double dt = Double.parseDouble(t[p++]);
        double P = Double.parseDouble(t[p++]);
        double[] x = new double[n], v = new double[n], m = new double[n], k = new double[n], r = new double[n], c = new double[n];
        for (int i = 0; i < n; i++) {
            x[i] = Double.parseDouble(t[p++]);
            v[i] = Double.parseDouble(t[p++]);
            m[i] = Double.parseDouble(t[p++]);
            k[i] = Double.parseDouble(t[p++]);
            r[i] = Double.parseDouble(t[p++]);
            c[i] = Double.parseDouble(t[p++]);
        }
        double[] fa = new double[n + 1];
        int n1 = n - 1;
        for (long s = 0; s < steps; s++) {
            double last = k[n1] * (((x[0] + P) - x[n1]) - r[n1]);
            for (int i = 0; i < n1; i++) {
                fa[i + 1] = k[i] * ((x[i + 1] - x[i]) - r[i]);
            }
            fa[n] = last;
            fa[0] = last;
            for (int i = 0; i < n; i++) {
                double F = (fa[i + 1] - fa[i]) - (c[i] * v[i]);
                double nv = v[i] + dt * (F / m[i]);
                v[i] = nv;
                x[i] = x[i] + dt * nv;
            }
        }
        double kin = 0, pot = 0, pos = 0, best = -1;
        int bi = 0;
        for (int i = 0; i < n; i++) {
            kin += ((0.5 * m[i]) * v[i]) * v[i];
            double st = (i < n1) ? ((x[i + 1] - x[i]) - r[i]) : (((x[0] + P) - x[n1]) - r[n1]);
            pot += ((0.5 * k[i]) * st) * st;
            pos += x[i];
            double a = Math.abs(v[i]);
            if (a > best) { best = a; bi = i; }
        }
        System.out.print(String.format(Locale.ROOT, "kinetic %.12e\npotential %.12e\nposition %.12e\nfastest %d\n", kin, pot, pos, bi));
    }
}
