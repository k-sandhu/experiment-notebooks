import java.nio.file.Files;
import java.nio.file.Path;

public class Main {
    // SplitMix64 increment. Java long arithmetic wraps exactly like unsigned 64-bit arithmetic.
    private static final long GAMMA = 0x9E3779B97F4A7C15L;

    // Totals for one contiguous range of walkers.
    static final class Partial {
        long spread;
        long bumps;
        long returns;
        long farDist = -1;
        long farWalker;
    }

    // A named class rather than a lambda: lambdas and string concatenation bootstrap through invokedynamic,
    // which costs noticeable startup time.
    static final class Worker extends Thread {
        private final long seed;
        private final long steps;
        private final long box;
        private final long first;
        private final long last;
        private final Partial acc;

        Worker(long seed, long steps, long box, long first, long last, Partial acc) {
            this.seed = seed;
            this.steps = steps;
            this.box = box;
            this.first = first;
            this.last = last;
            this.acc = acc;
        }

        @Override
        public void run() {
            walkRange(seed, steps, box, first, last, acc);
        }
    }

    public static void main(String[] args) throws Exception {
        String[] fields = Files.readString(Path.of(args[0])).trim().split("\\s+");
        long walkers = Long.parseLong(fields[0]);
        long steps = Long.parseLong(fields[1]);
        long box = Long.parseLong(fields[2]);
        long seed = Long.parseUnsignedLong(fields[3]);
        int workers = args.length >= 2 ? Integer.parseInt(args[1]) : 1;
        workers = (int) Math.max(1, Math.min(workers, walkers));

        // Worker w handles the contiguous walkers [first, last).
        Partial[] parts = new Partial[workers];
        Worker[] threads = new Worker[workers];
        for (int w = 0; w < workers; w++) {
            long first = walkers * w / workers;
            long last = walkers * (w + 1) / workers;
            parts[w] = new Partial();
            threads[w] = new Worker(seed, steps, box, first, last, parts[w]);
            threads[w].start();
        }
        for (Worker t : threads) {
            t.join();
        }

        // Parts are in walker order, so the first part holding the maximum also holds the smallest index.
        Partial total = new Partial();
        for (Partial part : parts) {
            total.spread += part.spread;
            total.bumps += part.bumps;
            total.returns += part.returns;
            if (part.farDist > total.farDist) {
                total.farDist = part.farDist;
                total.farWalker = part.farWalker;
            }
        }
        if (total.farDist < 0) {
            total.farDist = 0;
        }

        // print() rather than println(): the expected output uses LF line endings on every platform.
        StringBuilder out = new StringBuilder();
        out.append("spread ").append(total.spread)
                .append("\nbumps ").append(total.bumps)
                .append("\nreturns ").append(total.returns)
                .append("\nfarthest ").append(total.farWalker).append(' ').append(total.farDist).append('\n');
        System.out.print(out);
        System.out.flush();
    }

    static void walkRange(long seed, long steps, long box, long first, long last, Partial acc) {
        for (long j = first; j < last; j++) {
            walkOne(seed, steps, box, j, acc);
        }
    }

    // Runs walker j to the end of its steps and folds its result into acc.
    // The direction is computed arithmetically rather than with a switch, so the
    // unpredictable random choice never causes a branch misprediction.
    static void walkOne(long seed, long steps, long box, long j, Partial acc) {
        long state = seed + j;
        long x = 0;
        long y = 0;
        long bumps = 0;
        long returns = 0;
        for (long i = 0; i < steps; i++) {
            state += GAMMA;
            long z = state;
            z = (z ^ (z >>> 30)) * 0xBF58476D1CE4E5B9L;
            z = (z ^ (z >>> 27)) * 0x94D049BB133111EBL;
            // z ^ (z >>> 31) has the same top two bits as z, so the final mix is skipped.
            long d = z >>> 62;
            long isY = d >>> 1;
            long sign = 1 - 2 * (d & 1);
            long dx = sign * (1 - isY);
            long dy = sign * isY;
            long nx = x + dx;
            long ny = y + dy;
            if (nx < -box || nx > box || ny < -box || ny > box) {
                bumps++;
            } else {
                x = nx;
                y = ny;
                if ((x | y) == 0) {
                    returns++;
                }
            }
        }
        long dist = Math.abs(x) + Math.abs(y);
        acc.spread += x * x + y * y;
        acc.bumps += bumps;
        acc.returns += returns;
        // Walkers are visited in increasing order, so a strict comparison keeps the smallest index on a tie.
        if (dist > acc.farDist) {
            acc.farDist = dist;
            acc.farWalker = j;
        }
    }
}
