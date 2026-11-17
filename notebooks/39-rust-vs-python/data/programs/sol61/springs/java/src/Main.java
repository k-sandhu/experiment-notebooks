import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import com.fasterxml.jackson.core.io.NumberInput;

public class Main {
    private static final class Input {
        final char[] data;
        int at;
        Input(String path) throws Exception {
            data = Files.readString(Path.of(path), StandardCharsets.US_ASCII).toCharArray();
        }
        String token() {
            int length = data.length;
            while (at < length && data[at] <= ' ') ++at;
            int start = at;
            while (at < length && data[at] > ' ') ++at;
            return new String(data, start, at - start);
        }
        double number() {
            int length = data.length;
            while (at < length && data[at] <= ' ') ++at;
            int start = at;
            while (at < length && data[at] > ' ') ++at;
            return NumberInput.parseDouble(data, start, at - start, true);
        }
    }

    private static void simulate(int n, long steps, double dt, double p,
                                 double[] x, double[] v, double[] m,
                                 double[] k, double[] r, double[] c) {
        int last = n - 1;
        for (long step = 0; step < steps; ++step) {
            double current = x[0];
            double lastForce = k[last] * (((current + p) - x[last]) - r[last]);
            double previousForce = lastForce;
            // Retain old neighbors before overwriting positions in place.
            for (int i = 0; i < last; ++i) {
                double next = x[i + 1];
                double force = k[i] * ((next - current) - r[i]);
                double net = (force - previousForce) - c[i] * v[i];
                double velocity = v[i] + dt * (net / m[i]);
                v[i] = velocity;
                x[i] = current + dt * velocity;
                current = next;
                previousForce = force;
            }
            double net = (lastForce - previousForce) - c[last] * v[last];
            double velocity = v[last] + dt * (net / m[last]);
            v[last] = velocity;
            x[last] = current + dt * velocity;
        }
    }

    public static void main(String[] args) throws Exception {
        Input input = new Input(args[0]);
        int n = Integer.parseInt(input.token());
        long steps = Long.parseLong(input.token());
        double dt = input.number(), p = input.number();
        double[] x = new double[n + 1], v = new double[n], m = new double[n];
        double[] k = new double[n], r = new double[n], c = new double[n];
        for (int i = 0; i < n; ++i) {
            x[i] = input.number(); v[i] = input.number(); m[i] = input.number();
            k[i] = input.number(); r[i] = input.number(); c[i] = input.number();
        }
        simulate(n, steps, dt, p, x, v, m, k, r, c);
        x[n] = x[0] + p;
        double kinetic = 0, potential = 0, position = 0;
        int fastest = 0;
        double speed = Math.abs(v[0]);
        for (int i = 0; i < n; ++i) {
            kinetic += ((0.5 * m[i]) * v[i]) * v[i];
            double stretch = (x[i + 1] - x[i]) - r[i];
            potential += ((0.5 * k[i]) * stretch) * stretch;
            position += x[i];
            if (Math.abs(v[i]) > speed) { speed = Math.abs(v[i]); fastest = i; }
        }
        System.out.print("kinetic " + kinetic + "\npotential " + potential
                + "\nposition " + position + "\nfastest " + fastest + "\n");
    }
}
