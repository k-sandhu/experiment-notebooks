import java.io.BufferedOutputStream;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.util.Scanner;

public class Main {

    private static long L, B;

    public static void main(String[] args) throws Exception {
        if (args.length < 2) {
            System.exit(1);
        }
        long J, seed;
        try (InputStream in = new FileInputStream(args[0])) {
            Scanner sc = new Scanner(in);
            J = sc.nextLong();
            L = sc.nextLong();
            B = sc.nextLong();
            seed = Long.parseUnsignedLong(sc.next());
        }
        int workers = Integer.parseInt(args[1]);
        if (workers < 1) workers = 1;
        if (workers > J) workers = (int) J;

        long[] spreadArr = new long[workers];
        long[] bumpsArr = new long[workers];
        long[] retsArr = new long[workers];
        long[] bestDArr = new long[workers];
        long[] bestJArr = new long[workers];

        long chunk = (J + workers - 1) / workers;
        Thread[] threads = new Thread[workers - 1];
        for (int w = 0; w < workers; w++) {
            final int ww = w;
            final long j0 = w * chunk;
            final long j1 = Math.min(j0 + chunk, J);
            if (j0 >= j1) break;
            Runnable run = () -> walkRange(ww, j0, j1, seed, spreadArr, bumpsArr, retsArr, bestDArr, bestJArr);
            if (w == workers - 1) {
                run.run();
            } else {
                threads[w] = new Thread(run);
                threads[w].start();
            }
        }
        for (Thread t : threads) {
            if (t != null) t.join();
        }

        long spread = 0, bumps = 0, rets = 0, bestD = -1, bestJ = -1;
        for (int w = 0; w < workers; w++) {
            spread += spreadArr[w];
            bumps += bumpsArr[w];
            rets += retsArr[w];
            if (bestJArr[w] >= 0 && (bestJ < 0 || bestDArr[w] > bestD)) {
                bestD = bestDArr[w];
                bestJ = bestJArr[w];
            }
        }

        OutputStream out = new FileOutputStream(java.io.FileDescriptor.out);
        out = new BufferedOutputStream(out, 1 << 16);
        StringBuilder sb = new StringBuilder(128);
        sb.append("spread ").append(spread).append('\n');
        sb.append("bumps ").append(bumps).append('\n');
        sb.append("returns ").append(rets).append('\n');
        sb.append("farthest ").append(bestJ).append(' ').append(bestD).append('\n');
        out.write(sb.toString().getBytes(StandardCharsets.US_ASCII));
        out.flush();
    }

    private static void walkRange(int w, long j0, long j1, long seed,
                                  long[] spreadArr, long[] bumpsArr, long[] retsArr,
                                  long[] bestDArr, long[] bestJArr) {
        long spread = 0, bumps = 0, rets = 0, bestD = -1, bestJ = -1;
        long negB = -B;
        for (long j = j0; j < j1; j++) {
            long state = seed + j;
            long x = 0, y = 0;
            for (long s = 0; s < L; s++) {
                state += 0x9E3779B97F4A7C15L;
                long z = state;
                z = (z ^ (z >>> 30)) * 0xBF58476D1CE4E5B9L;
                z = (z ^ (z >>> 27)) * 0x94D049BB133111EBL;
                z = z ^ (z >>> 31);
                int d = (int) (z >>> 62);
                long dx = (d == 0 ? 1 : 0) - (d == 1 ? 1 : 0);
                long dy = (d == 2 ? 1 : 0) - (d == 3 ? 1 : 0);
                long nx = x + dx, ny = y + dy;
                if (nx > B || nx < negB || ny > B || ny < negB) {
                    bumps++;
                } else {
                    x = nx;
                    y = ny;
                    if (x == 0 && y == 0) rets++;
                }
            }
            spread += x * x + y * y;
            long D = Math.abs(x) + Math.abs(y);
            if (D > bestD) {
                bestD = D;
                bestJ = j;
            }
        }
        spreadArr[w] = spread;
        bumpsArr[w] = bumps;
        retsArr[w] = rets;
        bestDArr[w] = bestD;
        bestJArr[w] = bestJ;
    }
}
