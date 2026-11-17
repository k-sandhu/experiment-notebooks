import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.StringTokenizer;

public class Main {
    private static final long GAMMA = 0x9E3779B97F4A7C15L;
    private static final long MUL1 = 0xBF58476D1CE4E5B9L;
    private static final long MUL2 = 0x94D049BB133111EBL;

    // Runs shorter than this are not worth a trip through the unchecked loop.
    private static final long MIN_FAST_RUN = 4;
    // Keeps the packed x displacement of one run inside its low 32 bits.
    private static final long MAX_FAST_RUN = 1L << 30;

    private static final long[] DX = {1, -1, 0, 0};
    private static final long[] DY = {0, 0, 1, -1};
    // The same moves packed as dx + dy * 2^32, so one add moves both coordinates.
    private static final long[] PACKED = {1, -1, 1L << 32, -(1L << 32)};

    /** Top two bits of the next SplitMix64 output; the final z ^ (z >>> 31) never changes them. */
    private static int direction(long s) {
        long z = (s ^ (s >>> 30)) * MUL1;
        z = (z ^ (z >>> 27)) * MUL2;
        return (int) (z >>> 62);
    }

    /** Walks one walker; stores x, y, bumps, returns at out[4 * index]. */
    private static void walk(long s, long steps, long bound, long[] out, int index) {
        final long[] dxs = DX, dys = DY, packed = PACKED;
        final long span = 2 * bound;
        long x = 0, y = 0, bumps = 0, returns = 0;
        long left = steps;
        while (left > 0) {
            long ax = Math.abs(x), ay = Math.abs(y);
            // Within `run` steps the walker can neither reach a wall nor the origin,
            // so those steps need no checks at all.
            long run = Math.min(bound - Math.max(ax, ay), ax + ay - 1);
            if (run >= MIN_FAST_RUN) {
                run = Math.min(Math.min(run, left), MAX_FAST_RUN);
                left -= run;
                long moved = 0;
                for (int i = (int) run; i > 0; i--) {
                    s += GAMMA;
                    moved += packed[direction(s)];
                }
                long dx = (int) moved;
                x += dx;
                y += (moved - dx) >> 32;
                continue;
            }
            // Checked steps near a wall or the origin, until the walker is clear again.
            long end = Math.max(left - MIN_FAST_RUN, 0);
            for (; left > end; left--) {
                s += GAMMA;
                int d = direction(s);
                long nx = x + dxs[d], ny = y + dys[d];
                if (Long.compareUnsigned(nx + bound, span) <= 0 && Long.compareUnsigned(ny + bound, span) <= 0) {
                    x = nx;
                    y = ny;
                    if ((x | y) == 0) returns++;
                } else {
                    bumps++;
                }
            }
        }
        int o = 4 * index;
        out[o] = x;
        out[o + 1] = y;
        out[o + 2] = bumps;
        out[o + 3] = returns;
    }

    public static void main(String[] args) throws IOException, InterruptedException {
        StringTokenizer fields = new StringTokenizer(new String(Files.readAllBytes(Path.of(args[0])), StandardCharsets.US_ASCII));
        int walkers = Integer.parseInt(fields.nextToken());
        long steps = Long.parseLong(fields.nextToken());
        long bound = Long.parseLong(fields.nextToken());
        long seed = Long.parseUnsignedLong(fields.nextToken());
        int workers = args.length > 1 ? Math.max(1, Integer.parseInt(args[1].trim())) : 1;

        // A walker never gets farther than `steps` from the origin, so a larger box behaves the same.
        final long box = Math.min(bound, steps);

        long[] results = new long[4 * Math.max(walkers, 0)];
        int threads = Math.min(workers, walkers);
        Worker[] pool = new Worker[Math.max(threads, 1)];
        for (int t = 0; t < threads; t++) {
            int from = (int) ((long) walkers * t / threads), to = (int) ((long) walkers * (t + 1) / threads);
            pool[t] = new Worker(from, to, seed, steps, box, results);
            if (t > 0) pool[t].start();
        }
        if (threads > 0) pool[0].run();
        for (int t = 1; t < threads; t++) pool[t].join();

        long spread = 0, bumps = 0, returns = 0, bestJ = 0, bestD = -1;
        for (int j = 0; j < walkers; j++) {
            long x = results[4 * j], y = results[4 * j + 1];
            spread += x * x + y * y;
            bumps += results[4 * j + 2];
            returns += results[4 * j + 3];
            long d = Math.abs(x) + Math.abs(y);
            if (d > bestD) {
                bestD = d;
                bestJ = j;
            }
        }
        if (bestD < 0) bestD = 0;
        StringBuilder sb = new StringBuilder(128);
        sb.append("spread ").append(spread).append("\nbumps ").append(bumps).append("\nreturns ").append(returns)
                .append("\nfarthest ").append(bestJ).append(' ').append(bestD).append('\n');
        System.out.print(sb);
    }

    /** Walks a contiguous range of walkers; a plain class avoids lambda bootstrap cost at startup. */
    private static final class Worker extends Thread {
        private final int from, to;
        private final long seed, steps, bound;
        private final long[] results;

        Worker(int from, int to, long seed, long steps, long bound, long[] results) {
            this.from = from;
            this.to = to;
            this.seed = seed;
            this.steps = steps;
            this.bound = bound;
            this.results = results;
        }

        @Override
        public void run() {
            for (int j = from; j < to; j++) walk(seed + j, steps, bound, results, j);
        }
    }
}
