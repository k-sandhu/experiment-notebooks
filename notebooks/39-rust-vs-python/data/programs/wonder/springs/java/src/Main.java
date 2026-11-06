import java.nio.file.Files;
import java.nio.file.Paths;

public class Main {
    static byte[] data;
    static int pos;
    static long parseLong() {
        while (pos < data.length && data[pos] <= ' ') pos++;
        boolean neg = false;
        if (data[pos] == '-') { neg = true; pos++; }
        long val = 0;
        while (pos < data.length && data[pos] >= '0' && data[pos] <= '9') {
            val = val * 10 + (data[pos++] - '0');
        }
        return neg ? -val : val;
    }
    static double parseDouble() {
        while (pos < data.length && data[pos] <= ' ') pos++;
        int start = pos;
        while (pos < data.length && data[pos] > ' ') pos++;
        return Double.parseDouble(new String(data, start, pos - start, java.nio.charset.StandardCharsets.US_ASCII));
    }
    public static void main(String[] args) throws Exception {
        data = Files.readAllBytes(Paths.get(args[0]));
        pos = 0;
        int N = (int) parseLong();
        long S = parseLong();
        double dt = parseDouble();
        double P = parseDouble();
        double[] x = new double[N], v = new double[N], m = new double[N], k = new double[N], r = new double[N], c = new double[N], dtm = new double[N];
        for (int i = 0; i < N; i++) {
            x[i] = parseDouble(); v[i] = parseDouble(); m[i] = parseDouble();
            k[i] = parseDouble(); r[i] = parseDouble(); c[i] = parseDouble(); dtm[i] = dt / m[i];
        }
        for (long step = 0; step < S; step++) {
            double fLast = k[N-1] * (((x[0] + P) - x[N-1]) - r[N-1]);
            double prevF = fLast;
            int last = N - 1;
            for (int i = 0; i < last; i++) {
                double fi = k[i] * ((x[i+1] - x[i]) - r[i]);
                double F = (fi - prevF) - (c[i] * v[i]);
                double nv = v[i] + dtm[i] * F;
                v[i] = nv;
                x[i] = x[i] + dt * nv;
                prevF = fi;
            }
            {
                int i = last;
                double F = (fLast - prevF) - (c[i] * v[i]);
                double nv = v[i] + dtm[i] * F;
                v[i] = nv;
                x[i] = x[i] + dt * nv;
            }
        }
        double K = 0, U = 0, X = 0;
        for (int i = 0; i < N; i++) { K += ((0.5 * m[i]) * v[i]) * v[i]; X += x[i]; }
        for (int i = 0; i < N-1; i++) { double s = (x[i+1]-x[i])-r[i]; U += ((0.5*k[i])*s)*s; }
        { double s = ((x[0]+P)-x[N-1])-r[N-1]; U += ((0.5*k[N-1])*s)*s; }
        int J = 0; double best = Math.abs(v[0]);
        for (int i = 1; i < N; i++) { double a = Math.abs(v[i]); if (a > best) { best = a; J = i; } }
        StringBuilder sb = new StringBuilder(128);
        sb.append("kinetic ").append(String.format(java.util.Locale.US, "%.17e", K)).append('\n');
        sb.append("potential ").append(String.format(java.util.Locale.US, "%.17e", U)).append('\n');
        sb.append("position ").append(String.format(java.util.Locale.US, "%.17e", X)).append('\n');
        sb.append("fastest ").append(J).append('\n');
        System.out.print(sb.toString());
    }
}
