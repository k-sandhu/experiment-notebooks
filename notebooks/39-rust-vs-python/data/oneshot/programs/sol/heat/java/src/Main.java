import java.nio.file.Files;
import java.nio.file.Path;

public class Main {
    private static final class Input {
        private final byte[] data;
        private int position;

        Input(byte[] data) {
            this.data = data;
        }

        int nextInt() {
            while (data[position] <= 32) {
                position++;
            }
            int value = 0;
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

        int nextCell() {
            while (data[position] <= 32) {
                position++;
            }
            return data[position++];
        }
    }

    public static void main(String[] args) throws Exception {
        Input input = new Input(Files.readAllBytes(Path.of(args[0])));
        int height = input.nextInt();
        int width = input.nextInt();
        int steps = input.nextInt();

        int stride = width + 2;
        int size = (height + 2) * stride;
        int[] current = new int[size];
        int[] next = new int[size];
        byte[] active = new byte[size];
        int[] open = new int[height * width];
        int openCount = 0;
        boolean hasSource = false;

        for (int r = 0; r < height; r++) {
            int p = (r + 1) * stride + 1;
            for (int c = 0; c < width; c++, p++) {
                int ch = input.nextCell();
                if (ch == '.') {
                    active[p] = 1;
                    open[openCount++] = p;
                } else if (ch != '#') {
                    active[p] = 1;
                    int value = (ch - '0') * 1000;
                    current[p] = value;
                    next[p] = value;
                    hasSource = true;
                }
            }
        }

        if (hasSource && steps > 0) {
            byte[] coefficient = new byte[openCount];
            for (int i = 0; i < openCount; i++) {
                int p = open[i];
                coefficient[i] = (byte) (
                    8 - active[p - stride] - active[p + stride]
                      - active[p - 1] - active[p + 1]
                );
            }

            for (int step = 0; step < steps; step++) {
                for (int i = 0; i < openCount; i++) {
                    int p = open[i];
                    next[p] = (
                        current[p] * coefficient[i]
                        + current[p - stride]
                        + current[p + stride]
                        + current[p - 1]
                        + current[p + 1]
                    ) >>> 3;
                }
                int[] swap = current;
                current = next;
                next = swap;
            }
        }

        long sum = 0;
        long checksum = 0;
        int maximum = -1;
        int maximumRow = 0;
        int maximumColumn = 0;

        for (int i = 0; i < openCount; i++) {
            int p = open[i];
            int value = current[p];
            int row = p / stride - 1;
            int column = p % stride - 1;

            sum += value;
            checksum += (long) value * ((long) row * width + column + 1);

            if (value > maximum) {
                maximum = value;
                maximumRow = row;
                maximumColumn = column;
            }
        }

        StringBuilder output = new StringBuilder(100);
        output.append("sum ").append(sum).append('\n');
        output.append("max ").append(maximum).append(' ')
              .append(maximumRow).append(' ').append(maximumColumn).append('\n');
        output.append("checksum ").append(checksum).append('\n');
        System.out.print(output);
    }
}
