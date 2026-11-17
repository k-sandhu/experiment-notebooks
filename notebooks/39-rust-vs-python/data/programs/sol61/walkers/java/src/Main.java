import java.io.FileInputStream;

public final class Main {
    private static final class Result {
        long spread, bumps, returns, walker, distance = -1;
    }

    private static final class Worker extends Thread {
        private final long first, end, steps, bound, seed;
        Result result;

        Worker(long first, long end, long steps, long bound, long seed) {
            this.first = first;
            this.end = end;
            this.steps = steps;
            this.bound = bound;
            this.seed = seed;
        }

        @Override
        public void run() {
            result = simulate(first, end, steps, bound, seed);
        }
    }

    private static Result simulate(long first, long end, long steps, long bound, long seed) {
        if (steps <= Integer.MAX_VALUE) {
            return simulateSmall(first, end, (int)steps, (int)Math.min(bound, steps), seed);
        }
        Result result = new Result();
        for (long j = first; j < end; ++j) {
            long state = seed + j;
            long x = 0, y = 0, bumps = 0, returns = 0;
            for (long k = 0; k < steps; ++k) {
                long z = (state += 0x9E3779B97F4A7C15L);
                z = (z ^ (z >>> 30)) * 0xBF58476D1CE4E5B9L;
                z = (z ^ (z >>> 27)) * 0x94D049BB133111EBL;
                // The last SplitMix xor leaves these two bits unchanged.
                int d = (int)(z >>> 62);
                int axis = d >>> 1;
                int delta = 1 - 2 * (d & 1);
                long nx = x + (delta & (axis - 1));
                long ny = y + (delta & -axis);
                if (nx > bound || nx < -bound || ny > bound || ny < -bound) {
                    ++bumps;
                } else {
                    x = nx;
                    y = ny;
                    if ((x | y) == 0) ++returns;
                }
            }
            result.spread += x * x + y * y;
            result.bumps += bumps;
            result.returns += returns;
            long distance = Math.abs(x) + Math.abs(y);
            if (distance > result.distance) {
                result.distance = distance;
                result.walker = j;
            }
        }
        return result;
    }

    private static Result simulateSmall(long first, long end, int steps, int bound, long seed) {
        Result result = new Result();
        int limit = 2 * bound + Integer.MIN_VALUE;
        for (long j = first; j < end; ++j) {
            long state = seed + j;
            int x = 0, y = 0, bumps = 0, returns = 0;
            for (int k = 0; k < steps; ++k) {
                long z = (state += 0x9E3779B97F4A7C15L);
                z = (z ^ (z >>> 30)) * 0xBF58476D1CE4E5B9L;
                z = (z ^ (z >>> 27)) * 0x94D049BB133111EBL;
                int d = (int)(z >>> 62);
                int axis = d >>> 1;
                int delta = 1 - 2 * (d & 1);
                int nx = x + (delta & (axis - 1));
                int ny = y + (delta & -axis);
                // Unsigned interval checks, biased into the signed int range.
                if (nx + bound + Integer.MIN_VALUE > limit ||
                    ny + bound + Integer.MIN_VALUE > limit) {
                    ++bumps;
                } else {
                    x = nx;
                    y = ny;
                    if ((x | y) == 0) ++returns;
                }
            }
            result.spread += (long)x * x + (long)y * y;
            result.bumps += bumps;
            result.returns += returns;
            int distance = Math.abs(x) + Math.abs(y);
            if (distance > result.distance) {
                result.distance = distance;
                result.walker = j;
            }
        }
        return result;
    }

    public static void main(String[] args) throws Exception {
        byte[] input;
        try (FileInputStream stream = new FileInputStream(args[0])) {
            input = stream.readAllBytes();
        }
        long[] fields = new long[4];
        int position = 0;
        for (int i = 0; i < fields.length; ++i) {
            while (position < input.length && input[position] <= ' ') ++position;
            if (position < input.length && input[position] == '+') ++position;
            long value = 0;
            // Overflow deliberately wraps for the unsigned 64-bit seed.
            while (position < input.length && input[position] > ' ') {
                value = value * 10 + input[position++] - '0';
            }
            fields[i] = value;
        }
        long walkers = fields[0], steps = fields[1], bound = fields[2], seed = fields[3];
        int workers = Integer.parseInt(args[1]);
        Worker[] threads = new Worker[workers - 1];
        long q = walkers / workers, r = walkers % workers;
        for (int w = 1; w < workers; ++w) {
            long first = q * w + Math.min(w, r);
            long end = first + q + (w < r ? 1 : 0);
            threads[w - 1] = new Worker(first, end, steps, bound, seed);
            threads[w - 1].start();
        }
        Result total = simulate(0, q + (r > 0 ? 1 : 0), steps, bound, seed);
        for (Worker thread : threads) {
            thread.join();
            Result result = thread.result;
            total.spread += result.spread;
            total.bumps += result.bumps;
            total.returns += result.returns;
            if (result.distance > total.distance ||
                (result.distance == total.distance && result.walker < total.walker)) {
                total.distance = result.distance;
                total.walker = result.walker;
            }
        }
        StringBuilder output = new StringBuilder(128);
        output.append("spread ").append(total.spread).append("\nbumps ").append(total.bumps)
            .append("\nreturns ").append(total.returns).append("\nfarthest ")
            .append(total.walker).append(' ').append(Math.max(0, total.distance)).append('\n');
        System.out.print(output);
    }
}
