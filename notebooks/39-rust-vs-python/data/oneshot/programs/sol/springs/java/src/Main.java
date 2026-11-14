import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Locale;

public class Main {
    private static final class Input {
        private final byte[] data;
        private int position;

        Input(byte[] data) {
            this.data = data;
        }

        private void skipWhitespace() {
            while (position < data.length && data[position] <= 32) {
                position++;
            }
        }

        long nextLong() {
            skipWhitespace();
            long value = 0;
            while (position < data.length) {
                int ch = data[position];
                if (ch <= 32) {
                    break;
                }
                value = value * 10 + ch - '0';
                position++;
            }
            return value;
        }

        double nextDouble() {
            skipWhitespace();
            int start = position;
            while (position < data.length && data[position] > 32) {
                position++;
            }
            return Double.parseDouble(
                new String(data, start, position - start, StandardCharsets.US_ASCII)
            );
        }
    }

    private static void simulate(
        int n, long steps, double dt, double circumference,
        double[] x, double[] v, double[] m,
        double[] k, double[] r, double[] c
    ) {
        double[] force = new double[n];
        int last = n - 1;

        for (long step = 0; step < steps; step++) {
            for (int i = 0; i < last; i++) {
                double stretch = (x[i + 1] - x[i]) - r[i];
                force[i] = k[i] * stretch;
            }
            double stretch = ((x[0] + circumference) - x[last]) - r[last];
            force[last] = k[last] * stretch;

            double totalForce = (force[0] - force[last]) - (c[0] * v[0]);
            double newVelocity = v[0] + dt * (totalForce / m[0]);
            v[0] = newVelocity;
            x[0] = x[0] + dt * newVelocity;

            for (int i = 1; i < n; i++) {
                double f = (force[i] - force[i - 1]) - (c[i] * v[i]);
                double velocity = v[i] + dt * (f / m[i]);
                v[i] = velocity;
                x[i] = x[i] + dt * velocity;
            }
        }
    }

    public static void main(String[] args) throws Exception {
        Input input = new Input(Files.readAllBytes(Path.of(args[0])));

        int n = (int) input.nextLong();
        long steps = input.nextLong();
        double dt = input.nextDouble();
        double circumference = input.nextDouble();

        double[] x = new double[n];
        double[] v = new double[n];
        double[] m = new double[n];
        double[] k = new double[n];
        double[] r = new double[n];
        double[] c = new double[n];

        for (int i = 0; i < n; i++) {
            x[i] = input.nextDouble();
            v[i] = input.nextDouble();
            m[i] = input.nextDouble();
            k[i] = input.nextDouble();
            r[i] = input.nextDouble();
            c[i] = input.nextDouble();
        }

        simulate(n, steps, dt, circumference, x, v, m, k, r, c);

        double kinetic = 0.0;
        double potential = 0.0;
        double position = 0.0;
        int fastest = 0;
        double maximumSpeed = Math.abs(v[0]);

        for (int i = 0; i < n; i++) {
            kinetic += ((0.5 * m[i]) * v[i]) * v[i];
            position += x[i];

            double speed = Math.abs(v[i]);
            if (speed > maximumSpeed) {
                maximumSpeed = speed;
                fastest = i;
            }
        }

        int last = n - 1;
        for (int i = 0; i < last; i++) {
            double stretch = (x[i + 1] - x[i]) - r[i];
            potential += ((0.5 * k[i]) * stretch) * stretch;
        }
        double stretch = ((x[0] + circumference) - x[last]) - r[last];
        potential += ((0.5 * k[last]) * stretch) * stretch;

        System.out.printf(
            Locale.ROOT,
            "kinetic %.16e%npotential %.16e%nposition %.16e%nfastest %d%n",
            kinetic, potential, position, fastest
        );
    }
}
