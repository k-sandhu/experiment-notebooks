import java.nio.file.Files;
import java.nio.file.Path;
import java.util.StringTokenizer;

public class Main {
    private static final class Worker implements Runnable {
        final long start, end, steps, bound, seed;
        long spread, bumps, returns;
        long farthestWalker = Long.MAX_VALUE;
        long farthestDistance = -1;

        Worker(long start, long end, long steps, long bound, long seed) {
            this.start = start;
            this.end = end;
            this.steps = steps;
            this.bound = bound;
            this.seed = seed;
        }

        @Override
        public void run() {
            long totalSpread = 0;
            long totalBumps = 0;
            long totalReturns = 0;
            long bestWalker = Long.MAX_VALUE;
            long bestDistance = -1;

            /*
             * Encode [-bound, bound] as [Long.MIN_VALUE, upper].
             * Stepping below the lower endpoint wraps to Long.MAX_VALUE,
             * so either boundary violation is detected by one comparison.
             */
            final long origin = Long.MIN_VALUE + bound;
            final long upper = origin + bound;
            final long stepCount = steps;

            for (long walker = start; walker < end; walker++) {
                long state = seed + walker;
                long x = origin;
                long y = origin;

                for (long s = 0; s < stepCount; s++) {
                    state += 0x9E3779B97F4A7C15L;
                    long z = state;
                    z = (z ^ (z >>> 30)) * 0xBF58476D1CE4E5B9L;
                    z = (z ^ (z >>> 27)) * 0x94D049BB133111EBL;

                    // The final xor with z >>> 31 cannot change the top two bits.
                    int direction = (int) (z >>> 62);
                    int axis = direction >>> 1;
                    int sign = 1 - ((direction & 1) << 1);

                    long nextX = x + (sign & (axis - 1));
                    long nextY = y + (sign & -axis);

                    if (nextX > upper || nextY > upper) {
                        totalBumps++;
                    } else {
                        x = nextX;
                        y = nextY;
                        if (((x ^ origin) | (y ^ origin)) == 0) {
                            totalReturns++;
                        }
                    }
                }

                long finalX = x - origin;
                long finalY = y - origin;
                totalSpread += finalX * finalX + finalY * finalY;

                long distance = Math.abs(finalX) + Math.abs(finalY);
                if (distance > bestDistance) {
                    bestDistance = distance;
                    bestWalker = walker;
                }
            }

            spread = totalSpread;
            bumps = totalBumps;
            returns = totalReturns;
            farthestWalker = bestWalker;
            farthestDistance = bestDistance;
        }
    }

    public static void main(String[] args) throws Exception {
        StringTokenizer input =
                new StringTokenizer(Files.readString(Path.of(args[0])));

        long walkers = Long.parseLong(input.nextToken());
        long steps = Long.parseLong(input.nextToken());
        long bound = Long.parseLong(input.nextToken());
        long seed = Long.parseUnsignedLong(input.nextToken());
        int workerCount = Integer.parseInt(args[1]);

        Worker[] workers = new Worker[workerCount];
        Thread[] threads = new Thread[workerCount];

        long base = walkers / workerCount;
        long remainder = walkers % workerCount;
        long start = 0;

        for (int i = 0; i < workerCount; i++) {
            long count = base + (i < remainder ? 1 : 0);
            long end = start + count;
            workers[i] = new Worker(start, end, steps, bound, seed);
            start = end;
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
        long farthestWalker = Long.MAX_VALUE;
        long farthestDistance = -1;

        for (Worker worker : workers) {
            spread += worker.spread;
            bumps += worker.bumps;
            returns += worker.returns;

            if (worker.farthestDistance > farthestDistance
                    || (worker.farthestDistance == farthestDistance
                    && worker.farthestWalker < farthestWalker)) {
                farthestDistance = worker.farthestDistance;
                farthestWalker = worker.farthestWalker;
            }
        }

        System.out.print(
                "spread " + spread + "\n"
                + "bumps " + bumps + "\n"
                + "returns " + returns + "\n"
                + "farthest " + farthestWalker + " " + farthestDistance + "\n");
    }
}
