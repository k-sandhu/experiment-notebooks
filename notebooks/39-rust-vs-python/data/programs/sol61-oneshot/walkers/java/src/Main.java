import java.nio.file.Files;
import java.nio.file.Path;

public class Main {
    private static final class Parser {
        private final byte[] data;
        private int position;

        Parser(byte[] data) {
            this.data = data;
        }

        long nextLong() {
            while (position < data.length && data[position] <= ' ') {
                position++;
            }
            long value = 0;
            while (position < data.length) {
                int c = data[position];
                if (c < '0' || c > '9') {
                    break;
                }
                value = value * 10 + c - '0';
                position++;
            }
            return value;
        }
    }

    private static final class Worker implements Runnable {
        private final long first;
        private final long end;
        private final long steps;
        private final long bound;
        private final long seed;

        long spread;
        long bumps;
        long returns;
        long farthestIndex;
        long farthestDistance = -1;

        Worker(long first, long end, long steps, long bound, long seed) {
            this.first = first;
            this.end = end;
            this.steps = steps;
            this.bound = bound;
            this.seed = seed;
        }

        @Override
        public void run() {
            final long lowerBound = -bound;
            long totalSpread = 0;
            long totalBumps = 0;
            long totalReturns = 0;
            long bestDistance = -1;
            long bestIndex = 0;

            for (long walker = first; walker < end; walker++) {
                long state = seed + walker;
                long x = 0;
                long y = 0;
                long walkerBumps = 0;
                long walkerReturns = 0;

                for (long remaining = steps; remaining != 0; remaining--) {
                    state += 0x9E3779B97F4A7C15L;
                    long r = state;
                    r = (r ^ (r >>> 30)) * 0xBF58476D1CE4E5B9L;
                    r = (r ^ (r >>> 27)) * 0x94D049BB133111EBL;
                    r ^= r >>> 31;

                    long axisMask = r >> 63;
                    long delta = 1L - ((r >>> 61) & 2L);
                    long nextX = x + (delta & ~axisMask);
                    long nextY = y + (delta & axisMask);

                    if (nextX < lowerBound || nextX > bound
                            || nextY < lowerBound || nextY > bound) {
                        walkerBumps++;
                    } else {
                        x = nextX;
                        y = nextY;
                        if ((x | y) == 0) {
                            walkerReturns++;
                        }
                    }
                }

                totalSpread += x * x + y * y;
                totalBumps += walkerBumps;
                totalReturns += walkerReturns;

                long distance = Math.abs(x) + Math.abs(y);
                if (distance > bestDistance) {
                    bestDistance = distance;
                    bestIndex = walker;
                }
            }

            spread = totalSpread;
            bumps = totalBumps;
            returns = totalReturns;
            farthestIndex = bestIndex;
            farthestDistance = bestDistance;
        }
    }

    public static void main(String[] args) throws Exception {
        Parser input = new Parser(Files.readAllBytes(Path.of(args[0])));
        long walkers = input.nextLong();
        long steps = input.nextLong();
        long bound = input.nextLong();
        long seed = input.nextLong();
        int workerCount = Integer.parseInt(args[1]);

        Worker[] workers = new Worker[workerCount];
        Thread[] threads = new Thread[workerCount];

        long base = walkers / workerCount;
        long extra = walkers % workerCount;
        long first = 0;

        for (int i = 0; i < workerCount; i++) {
            long count = base + (i < extra ? 1 : 0);
            long end = first + count;
            workers[i] = new Worker(first, end, steps, bound, seed);
            first = end;
        }

        for (int i = 1; i < workerCount; i++) {
            threads[i] = new Thread(workers[i]);
            threads[i].start();
        }

        workers[0].run();

        for (int i = 1; i < workerCount; i++) {
            threads[i].join();
        }

        long spread = 0;
        long bumps = 0;
        long returns = 0;
        long farthestIndex = 0;
        long farthestDistance = -1;

        for (Worker worker : workers) {
            spread += worker.spread;
            bumps += worker.bumps;
            returns += worker.returns;

            if (worker.farthestDistance > farthestDistance
                    || (worker.farthestDistance == farthestDistance
                    && worker.farthestIndex < farthestIndex)) {
                farthestDistance = worker.farthestDistance;
                farthestIndex = worker.farthestIndex;
            }
        }

        StringBuilder output = new StringBuilder(128);
        output.append("spread ").append(spread).append('\n');
        output.append("bumps ").append(bumps).append('\n');
        output.append("returns ").append(returns).append('\n');
        output.append("farthest ").append(farthestIndex)
                .append(' ').append(farthestDistance).append('\n');
        System.out.print(output);
    }
}
