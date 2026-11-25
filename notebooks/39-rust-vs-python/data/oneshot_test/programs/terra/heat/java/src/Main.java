import java.io.BufferedInputStream;
import java.io.FileInputStream;
import java.io.IOException;

public class Main {
    private static final class FastInput implements AutoCloseable {
        private final BufferedInputStream in;

        FastInput(String path) throws IOException {
            in = new BufferedInputStream(new FileInputStream(path), 1 << 16);
        }

        int nextInt() throws IOException {
            int c;
            do {
                c = in.read();
            } while (c <= ' ' && c != -1);

            int value = 0;
            while (c > ' ') {
                value = value * 10 + c - '0';
                c = in.read();
            }
            return value;
        }

        int nextCell() throws IOException {
            int c;
            do {
                c = in.read();
            } while (c <= ' ' && c != -1);
            return c;
        }

        @Override
        public void close() throws IOException {
            in.close();
        }
    }

    public static void main(String[] args) throws Exception {
        try (FastInput input = new FastInput(args[0])) {
            int h = input.nextInt();
            int w = input.nextInt();
            int steps = input.nextInt();

            int stride = w + 2;
            int size = (h + 2) * stride;
            int[] current = new int[size];
            int[] next = new int[size];
            byte[] passable = new byte[size];

            int[] openPositions = new int[h * w];
            int[] originalPositions = new int[h * w];
            int openCount = 0;

            for (int r = 0; r < h; r++) {
                int base = (r + 1) * stride + 1;
                for (int c = 0; c < w; c++) {
                    int ch = input.nextCell();
                    int pos = base + c;
                    if (ch == '.') {
                        passable[pos] = 1;
                        openPositions[openCount] = pos;
                        originalPositions[openCount] = r * w + c;
                        openCount++;
                    } else if (ch != '#') {
                        passable[pos] = 1;
                        int value = (ch - '0') * 1000;
                        current[pos] = value;
                        next[pos] = value;
                    }
                }
            }

            byte[] coefficient = new byte[size];
            for (int i = 0; i < openCount; i++) {
                int p = openPositions[i];
                coefficient[p] = (byte) (8
                        - passable[p - stride]
                        - passable[p + stride]
                        - passable[p - 1]
                        - passable[p + 1]);
            }

            for (int step = 0; step < steps; step++) {
                for (int i = 0; i < openCount; i++) {
                    int p = openPositions[i];
                    next[p] = (coefficient[p] * current[p]
                            + current[p - stride]
                            + current[p + stride]
                            + current[p - 1]
                            + current[p + 1]) >> 3;
                }
                int[] temp = current;
                current = next;
                next = temp;
            }

            long sum = 0;
            long checksum = 0;
            int max = -1;
            int maxPosition = 0;

            for (int i = 0; i < openCount; i++) {
                int value = current[openPositions[i]];
                int position = originalPositions[i];
                sum += value;
                checksum += (long) value * (position + 1L);
                if (value > max) {
                    max = value;
                    maxPosition = position;
                }
            }

            System.out.print("sum " + sum
                    + "\nmax " + max + " " + (maxPosition / w) + " " + (maxPosition % w)
                    + "\nchecksum " + checksum + "\n");
        }
    }
}
