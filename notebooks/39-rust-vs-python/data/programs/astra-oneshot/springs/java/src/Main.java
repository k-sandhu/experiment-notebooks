import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Locale;

public class Main {
    private static final class Input {
        private final byte[] data;
        private int position;

        Input(String path) throws Exception {
            data = Files.readAllBytes(Path.of(path));
        }

        String next() {
            while (position < data.length && data[position] <= 32) {
                position++;
            }
            int start = position;
            while (position < data.length && data[position] > 32) {
                position++;
            }
            return new String(data, start, position - start,
                    StandardCharsets.US_ASCII);
        }

        double nextDouble() {
            return Double.parseDouble(next());
        }
    }

    public static void main(String[] args) throws Exception {
        Input input = new Input(args[0]);
        int n = Integer.parseInt(input.next());
        long steps = Long.parseLong(input.next());
        double dt = input.nextDouble();
        double circumference = input.nextDouble();

        double[] x = new double[n];
        double[] v = new double[n];
        double[] m = new double[n];
        double[] k = new double[n];
        double[] r = new double[n];
        double[] c = new double[n];
        double[] f = new double[n];

        for (int i = 0; i < n; i++) {
            x[i] = input.nextDouble();
            v[i] = input.nextDouble();
            m[i] = input.nextDouble();
            k[i] = input.nextDouble();
            r[i] = input.nextDouble();
            c[i] = input.nextDouble();
        }

        int last = n - 1;
        for (long step = 0; step < steps; step++) {
            for (int i = 0; i < last; i++) {
                double stretch = (x[i + 1] - x[i]) - r[i];
                f[i] = k[i] * stretch;
            }
            double lastStretch = ((x[0] + circumference) - x[last]) - r[last];
            f[last] = k[last] * lastStretch;

            double force0 = (f[0] - f[last]) - (c[0] * v[0]);
            double velocity0 = v[0] + dt * (force0 / m[0]);
            v[0] = velocity0;
            x[0] = x[0] + dt * velocity0;

            for (int i = 1; i < n; i++) {
                double force = (f[i] - f[i - 1]) - (c[i] * v[i]);
                double velocity = v[i] + dt * (force / m[i]);
                v[i] = velocity;
                x[i] = x[i] + dt * velocity;
            }
        }

        double kinetic = 0.0;
        double potential = 0.0;
        double positionSum = 0.0;
        int fastest = 0;
        double greatestSpeed = Math.abs(v[0]);

        for (int i = 0; i < n; i++) {
            kinetic += ((0.5 * m[i]) * v[i]) * v[i];
            positionSum += x[i];

            double speed = Math.abs(v[i]);
            if (speed > greatestSpeed) {
                greatestSpeed = speed;
                fastest = i;
            }
        }

        for (int i = 0; i < last; i++) {
            double stretch = (x[i + 1] - x[i]) - r[i];
            potential += ((0.5 * k[i]) * stretch) * stretch;
        }
        double stretch = ((x[0] + circumference) - x[last]) - r[last];
        potential += ((0.5 * k[last]) * stretch) * stretch;

        System.out.printf(Locale.ROOT,
                "kinetic %.16e%npotential %.16e%nposition %.16e%nfastest %d%n",
                kinetic, potential, positionSum, fastest);
    }
}
