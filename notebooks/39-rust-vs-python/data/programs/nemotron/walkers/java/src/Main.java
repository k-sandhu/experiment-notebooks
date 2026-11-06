import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.List;

public class Main {

    private static final long C1 = 0x9E3779B97F4A7C15L;
    private static final long C2 = 0xBF58476D1CE4E5B9L;
    private static final long C3 = 0x94D049BB133111EBL;

    private static final class Result {
        long spread;
        long bumps;
        long returns;
        long farDist;
        int farWalker;
    }

    // SplitMix64: advance state by the constant; the walker loop scrambles it.
    private static long advance(long state) {
        return state + C1;
    }

    // Simulate walkers [start, end). Integer sums and the (distance, index)
    // order are reduction-order independent, so the result does not depend on
    // how walkers are split across threads.
    private static Result runRange(long start, long end, long L, int B, long seed) {
        Result res = new Result();
        if (start < end) res.farWalker = (int) start;
        int twoB = 2 * B;
        for (long j = start; j < end; ++j) {
            long state = seed + j;
            int x = 0, y = 0;
            long b = 0, r = 0;
            for (long t = 0; t < L; ++t) {
                state = advance(state);
                long z = state;
                z = (z ^ (z >>> 30)) * C2;
                z = (z ^ (z >>> 27)) * C3;
                long rnd = z ^ (z >>> 31);
                int d = (int) (rnd >>> 62);
                int nx, ny;
                switch (d) {
                    case 0: nx = x + 1; ny = y; break;
                    case 1: nx = x - 1; ny = y; break;
                    case 2: nx = x; ny = y + 1; break;
                    default: nx = x; ny = y - 1; break;
                }
                int vx = nx + B;
                int vy = ny + B;
                if (vx >= 0 && vx <= twoB && vy >= 0 && vy <= twoB) {
                    x = nx;
                    y = ny;
                    if (x == 0 && y == 0) ++r;
                } else {
                    ++b;
                }
            }
            res.spread += (long) x * x + (long) y * y;
            res.bumps += b;
            res.returns += r;
            int dist = (x < 0 ? -x : x) + (y < 0 ? -y : y);
            if (dist > res.farDist) {
                res.farDist = dist;
                res.farWalker = (int) j;
            }
        }
        return res;
    }

    private static void merge(Result into, Result other) {
        into.spread += other.spread;
        into.bumps += other.bumps;
        into.returns += other.returns;
        if (other.farDist > into.farDist ||
            (other.farDist == into.farDist && other.farWalker < into.farWalker)) {
            into.farDist = other.farDist;
            into.farWalker = other.farWalker;
        }
    }

    public static void main(String[] args) throws Exception {
        String text = Files.readString(Paths.get(args[0]));
        List<String> parts = List.of(text.trim().split("\\s+"));
        long J = Long.parseLong(parts.get(0));
        long L = Long.parseLong(parts.get(1));
        int B = Integer.parseInt(parts.get(2));
        // SEED is unsigned 64-bit; parseUnsignedLong keeps the exact bit pattern.
        long seed = Long.parseUnsignedLong(parts.get(3));
        int W = Integer.parseInt(args[1]);
        if (W < 1) W = 1;
        if (W > 32) W = 32;

        Result[] results = new Result[W];
        Thread[] threads = new Thread[W];
        for (int i = 0; i < W; ++i) {
            long start = i * J / W;
            long end = (i + 1) * J / W;
            final int idx = i;
            threads[i] = new Thread(() -> results[idx] = runRange(start, end, L, B, seed));
            threads[i].start();
        }
        for (Thread t : threads) t.join();

        Result total = results[0];
        for (int i = 1; i < W; ++i) merge(total, results[i]);

        System.out.println("spread " + total.spread);
        System.out.println("bumps " + total.bumps);
        System.out.println("returns " + total.returns);
        System.out.println("farthest " + total.farWalker + " " + total.farDist);
    }
}
