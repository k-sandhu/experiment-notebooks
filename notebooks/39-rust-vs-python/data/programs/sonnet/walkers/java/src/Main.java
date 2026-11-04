import java.nio.file.Files;
import java.nio.file.Paths;

public class Main {
    static final int[] DX = {1, -1, 0, 0};
    static final int[] DY = {0, 0, 1, -1};

    static void walk(long seed, int j, long L, int B, long[] res) {
        long state = seed + j;
        int x = 0, y = 0;
        long bumps = 0, returns = 0;
        final int span = 2 * B;
        final int[] dx = DX, dy = DY;
        for (long i = 0; i < L; i++) {
            state += 0x9E3779B97F4A7C15L;
            long z = state;
            z = (z ^ (z >>> 30)) * 0xBF58476D1CE4E5B9L;
            z = (z ^ (z >>> 27)) * 0x94D049BB133111EBL;
            int d = (int) (z >>> 62);
            int nx = x + dx[d], ny = y + dy[d];
            if (Integer.compareUnsigned(nx + B, span) > 0 || Integer.compareUnsigned(ny + B, span) > 0) {
                bumps++;
            } else {
                x = nx; y = ny;
                if ((x | y) == 0) returns++;
            }
        }
        res[j * 4] = (long) x * x + (long) y * y;
        res[j * 4 + 1] = bumps;
        res[j * 4 + 2] = returns;
        res[j * 4 + 3] = Math.abs(x) + Math.abs(y);
    }

    public static void main(String[] args) throws Exception {
        String[] p = new String(Files.readAllBytes(Paths.get(args[0]))).trim().split("\\s+");
        final int J = Integer.parseInt(p[0]);
        final long L = Long.parseLong(p[1]);
        final int B = Integer.parseInt(p[2]);
        final long seed = Long.parseUnsignedLong(p[3]);
        final int W = Math.min(Math.max(1, Integer.parseInt(args[1])), J);
        final long[] res = new long[J * 4];
        Thread[] th = new Thread[W];
        for (int w = 0; w < W; w++) {
            final int ww = w;
            th[w] = new Thread(() -> {
                for (int j = ww; j < J; j += W) walk(seed, j, L, B, res);
            });
            th[w].start();
        }
        for (Thread t : th) t.join();
        long spread = 0, bumps = 0, returns = 0, bestD = -1;
        int bestJ = 0;
        for (int j = 0; j < J; j++) {
            spread += res[j * 4]; bumps += res[j * 4 + 1]; returns += res[j * 4 + 2];
            if (res[j * 4 + 3] > bestD) { bestD = res[j * 4 + 3]; bestJ = j; }
        }
        System.out.println("spread " + spread + "\nbumps " + bumps + "\nreturns " + returns + "\nfarthest " + bestJ + " " + bestD);
    }
}
