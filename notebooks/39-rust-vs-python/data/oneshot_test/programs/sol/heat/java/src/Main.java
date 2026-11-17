import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;

public class Main {
    private static final class Input {
        final byte[] data;
        int pos;

        Input(byte[] data) {
            this.data = data;
        }

        void skipWhitespace() {
            while (pos < data.length && data[pos] <= 32) {
                pos++;
            }
        }

        long nextLong() {
            skipWhitespace();
            long value = 0;
            while (pos < data.length) {
                int c = data[pos] & 255;
                if (c < '0' || c > '9') {
                    break;
                }
                value = value * 10 + c - '0';
                pos++;
            }
            return value;
        }
    }

    private static final class Spans {
        int[] starts = new int[1024];
        int[] ends = new int[1024];
        byte[] weights = new byte[1024];
        int size;

        void add(int start, int end, int weight) {
            if (size == starts.length) {
                int capacity = starts.length + (starts.length >> 1);
                starts = Arrays.copyOf(starts, capacity);
                ends = Arrays.copyOf(ends, capacity);
                weights = Arrays.copyOf(weights, capacity);
            }
            starts[size] = start;
            ends[size] = end;
            weights[size] = (byte) weight;
            size++;
        }
    }

    public static void main(String[] args) throws Exception {
        Input input = new Input(Files.readAllBytes(Path.of(args[0])));
        int h = (int) input.nextLong();
        int w = (int) input.nextLong();
        long steps = input.nextLong();

        int stride = w + 2;
        int[] current = new int[(h + 2) * stride];
        Arrays.fill(current, -1);

        int[] rowOffsets = new int[h];
        int firstRow = -1;
        int firstCol = -1;
        boolean hasSource = false;

        for (int r = 0; r < h; r++) {
            input.skipWhitespace();
            int offset = input.pos;
            rowOffsets[r] = offset;
            int start = (r + 1) * stride + 1;

            for (int c = 0; c < w; c++) {
                int ch = input.data[offset + c];
                if (ch == '.') {
                    current[start + c] = 0;
                    if (firstRow < 0) {
                        firstRow = r;
                        firstCol = c;
                    }
                } else if (ch != '#') {
                    current[start + c] = (ch - '0') * 1000;
                    hasSource = true;
                }
            }
            input.pos += w;
        }

        if (steps == 0 || !hasSource) {
            System.out.print("sum 0\nmax 0 " + firstRow + " " + firstCol
                    + "\nchecksum 0\n");
            return;
        }

        Spans spans = new Spans();

        for (int r = 0; r < h; r++) {
            int start = (r + 1) * stride + 1;
            int end = start + w;
            int runStart = start;
            int runWeight = 0;

            for (int p = start; p <= end; p++) {
                int weight = 0;
                if (p < end && current[p] == 0) {
                    weight = 4
                            + (current[p - stride] >>> 31)
                            + (current[p + stride] >>> 31)
                            + (current[p - 1] >>> 31)
                            + (current[p + 1] >>> 31);

                    // An isolated open cell remains zero forever.
                    if (weight == 8) {
                        weight = 0;
                    }
                }

                if (weight != runWeight) {
                    if (runWeight != 0) {
                        spans.add(runStart, p, runWeight);
                    }
                    runStart = p;
                    runWeight = weight;
                }
            }
        }

        for (int i = 0; i < current.length; i++) {
            if (current[i] < 0) {
                current[i] = 0;
            }
        }

        if (spans.size != 0) {
            int[] next = current.clone();
            int[] starts = spans.starts;
            int[] ends = spans.ends;
            byte[] weights = spans.weights;
            int count = spans.size;

            for (long step = 0; step < steps; step++) {
                for (int s = 0; s < count; s++) {
                    int end = ends[s];
                    int weight = weights[s];

                    if (weight == 4) {
                        for (int p = starts[s]; p < end; p++) {
                            next[p] = ((current[p] << 2)
                                    + current[p - stride]
                                    + current[p + stride]
                                    + current[p - 1]
                                    + current[p + 1]) >>> 3;
                        }
                    } else {
                        for (int p = starts[s]; p < end; p++) {
                            next[p] = (weight * current[p]
                                    + current[p - stride]
                                    + current[p + stride]
                                    + current[p - 1]
                                    + current[p + 1]) >>> 3;
                        }
                    }
                }

                int[] temporary = current;
                current = next;
                next = temporary;

                if ((step & 63L) == 63L && Arrays.equals(current, next)) {
                    break;
                }
            }
        }

        long sum = 0;
        long checksum = 0;
        int maximum = -1;
        int maxRow = firstRow;
        int maxCol = firstCol;

        for (int r = 0; r < h; r++) {
            int offset = rowOffsets[r];
            int start = (r + 1) * stride + 1;
            long firstWeight = (long) r * w + 1;

            for (int c = 0; c < w; c++) {
                if (input.data[offset + c] == '.') {
                    int value = current[start + c];
                    sum += value;
                    checksum += (firstWeight + c) * value;
                    if (value > maximum) {
                        maximum = value;
                        maxRow = r;
                        maxCol = c;
                    }
                }
            }
        }

        StringBuilder output = new StringBuilder(100);
        output.append("sum ").append(sum)
                .append("\nmax ").append(maximum)
                .append(' ').append(maxRow)
                .append(' ').append(maxCol)
                .append("\nchecksum ").append(checksum)
                .append('\n');
        System.out.print(output);
    }
}
