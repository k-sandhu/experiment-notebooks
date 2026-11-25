import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;

public class Main {
    private static final class Input {
        final byte[] data;
        int position;

        Input(byte[] data) {
            this.data = data;
        }

        long nextLong() {
            while (position < data.length && data[position] <= 32) {
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

    public static void main(String[] args) throws Exception {
        Input input = new Input(Files.readAllBytes(Path.of(args[0])));
        int height = (int) input.nextLong();
        int width = (int) input.nextLong();
        long steps = input.nextLong();

        byte[] data = input.data;
        int openCount = 0;
        int sourceCount = 0;
        for (int i = input.position; i < data.length; i++) {
            int c = data[i];
            if (c == '.') {
                openCount++;
            } else if (c >= '1' && c <= '9') {
                sourceCount++;
            }
        }

        int stride = width + 2;
        int[] mapping = new int[(height + 2) * stride];
        Arrays.fill(mapping, -1);

        int[] current = new int[openCount + sourceCount];
        int[] next = new int[current.length];
        int[] positions = new int[openCount];

        int cursor = input.position;
        int openIndex = 0;
        int sourceIndex = openCount;
        for (int row = 0; row < height; row++) {
            while (cursor < data.length && data[cursor] <= 32) {
                cursor++;
            }
            int padded = (row + 1) * stride + 1;
            int linear = row * width;
            for (int col = 0; col < width; col++) {
                int c = data[cursor++];
                if (c == '.') {
                    mapping[padded + col] = openIndex;
                    positions[openIndex++] = linear + col;
                } else if (c != '#') {
                    mapping[padded + col] = sourceIndex;
                    int value = (c - '0') * 1000;
                    current[sourceIndex] = value;
                    next[sourceIndex++] = value;
                }
            }
        }

        if (steps > 0 && sourceCount > 0) {
            int[] up = new int[openCount];
            int[] down = new int[openCount];
            int[] left = new int[openCount];
            int[] right = new int[openCount];

            for (int row = 0; row < height; row++) {
                int start = (row + 1) * stride + 1;
                int end = start + width;
                for (int p = start; p < end; p++) {
                    int i = mapping[p];
                    if (i < 0 || i >= openCount) {
                        continue;
                    }
                    int u = mapping[p - stride];
                    int d = mapping[p + stride];
                    int l = mapping[p - 1];
                    int r = mapping[p + 1];
                    up[i] = u < 0 ? i : u;
                    down[i] = d < 0 ? i : d;
                    left[i] = l < 0 ? i : l;
                    right[i] = r < 0 ? i : r;
                }
            }

            for (long step = 0; step < steps; step++) {
                int changed = 0;
                for (int i = 0; i < openCount; i++) {
                    int old = current[i];
                    int value = ((old << 2)
                            + current[up[i]]
                            + current[down[i]]
                            + current[left[i]]
                            + current[right[i]]) >>> 3;
                    next[i] = value;
                    changed |= value ^ old;
                }
                int[] temporary = current;
                current = next;
                next = temporary;
                if (changed == 0) {
                    break;
                }
            }
        }

        long sum = 0;
        long checksum = 0;
        int maximum = -1;
        int maximumPosition = 0;

        for (int i = 0; i < openCount; i++) {
            int value = current[i];
            int position = positions[i];
            sum += value;
            checksum += (long) value * (position + 1L);
            if (value > maximum) {
                maximum = value;
                maximumPosition = position;
            }
        }

        StringBuilder output = new StringBuilder(100);
        output.append("sum ").append(sum).append('\n');
        output.append("max ").append(maximum).append(' ')
                .append(maximumPosition / width).append(' ')
                .append(maximumPosition % width).append('\n');
        output.append("checksum ").append(checksum).append('\n');
        System.out.print(output);
    }
}
