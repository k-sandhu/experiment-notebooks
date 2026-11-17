import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Locale;

// Springs on a ring: explicit time stepping of N masses joined by N springs (see SPEC.md).
//
// Each step runs in two passes over flat double arrays, so the JIT can vectorize the loops.
// The arithmetic keeps the spec's operation order, so the results match the reference
// bit for bit, apart from summation order in the final sums.
public class Main {

    public static void main(String[] args) throws IOException {
        if (args.length < 1) {
            System.err.println("usage: run INPUT_PATH");
            System.exit(1);
        }
        Ring ring = Ring.read(Path.of(args[0]));
        int n = ring.n;

        for (long s = 0; s < ring.steps; s++) {
            ring.step();
        }

        double p = ring.circumference;
        double[] x = ring.x, v = ring.v, m = ring.m, k = ring.k, r = ring.r;

        double kinetic = 0.0;
        for (int i = 0; i < n; i++) {
            kinetic += ((0.5 * m[i]) * v[i]) * v[i];
        }

        double potential = 0.0;
        for (int i = 0; i + 1 < n; i++) {
            double s = (x[i + 1] - x[i]) - r[i];
            potential += ((0.5 * k[i]) * s) * s;
        }
        double sLast = ((x[0] + p) - x[n - 1]) - r[n - 1];
        potential += ((0.5 * k[n - 1]) * sLast) * sLast;

        double position = 0.0;
        for (int i = 0; i < n; i++) {
            position += x[i];
        }

        int fastest = 0;
        for (int i = 1; i < n; i++) {
            if (Math.abs(v[i]) > Math.abs(v[fastest])) {
                fastest = i;
            }
        }

        System.out.printf(Locale.ROOT, "kinetic %.16e%n", kinetic);
        System.out.printf(Locale.ROOT, "potential %.16e%n", potential);
        System.out.printf(Locale.ROOT, "position %.16e%n", position);
        System.out.printf(Locale.ROOT, "fastest %d%n", fastest);
    }
}

final class Ring {
    final int n;
    final long steps;
    final double dt;
    final double circumference;
    final double[] x, v, m, k, r, c;
    private final double[] f;  // spring forces for the current step

    private Ring(int n, long steps, double dt, double circumference) {
        this.n = n;
        this.steps = steps;
        this.dt = dt;
        this.circumference = circumference;
        this.x = new double[n];
        this.v = new double[n];
        this.m = new double[n];
        this.k = new double[n];
        this.r = new double[n];
        this.c = new double[n];
        this.f = new double[n];
    }

    static Ring read(Path path) throws IOException {
        byte[] text = Files.readAllBytes(path);
        Tokens tokens = new Tokens(text);
        int n = Integer.parseInt(tokens.next());
        long steps = Long.parseLong(tokens.next());
        double dt = Double.parseDouble(tokens.next());
        double circumference = Double.parseDouble(tokens.next());

        Ring ring = new Ring(n, steps, dt, circumference);
        for (int i = 0; i < n; i++) {
            ring.x[i] = Double.parseDouble(tokens.next());
            ring.v[i] = Double.parseDouble(tokens.next());
            ring.m[i] = Double.parseDouble(tokens.next());
            ring.k[i] = Double.parseDouble(tokens.next());
            ring.r[i] = Double.parseDouble(tokens.next());
            ring.c[i] = Double.parseDouble(tokens.next());
        }
        return ring;
    }

    // One time step (SPEC.md, "One time step").
    void step() {
        final int n = this.n;
        final double p = circumference;
        final double dt = this.dt;
        final double[] x = this.x, v = this.v, m = this.m, k = this.k, r = this.r, c = this.c, f = this.f;

        // Pass 1: spring forces from the old positions. Spring n-1 wraps around to mass 0.
        for (int i = 0; i + 1 < n; i++) {
            f[i] = k[i] * ((x[i + 1] - x[i]) - r[i]);
        }
        f[n - 1] = k[n - 1] * (((x[0] + p) - x[n - 1]) - r[n - 1]);

        // Pass 2: velocity from the forces (old velocity), then position from the new velocity.
        // Mass 0 uses the force of spring n-1 as its left neighbour.
        v[0] = v[0] + dt * (((f[0] - f[n - 1]) - (c[0] * v[0])) / m[0]);
        for (int i = 1; i < n; i++) {
            v[i] = v[i] + dt * (((f[i] - f[i - 1]) - (c[i] * v[i])) / m[i]);
        }
        for (int i = 0; i < n; i++) {
            x[i] = x[i] + dt * v[i];
        }
    }
}

// Splits the file on whitespace and returns each token as a string.
final class Tokens {
    private final byte[] text;
    private int pos = 0;

    Tokens(byte[] text) {
        this.text = text;
    }

    String next() {
        while (pos < text.length && text[pos] <= ' ') {
            pos++;
        }
        int start = pos;
        while (pos < text.length && text[pos] > ' ') {
            pos++;
        }
        return new String(text, start, pos - start, StandardCharsets.ISO_8859_1);
    }
}
