import java.io.*;
import java.nio.charset.StandardCharsets;

public class Main {
    private static final class FastInput implements Closeable {
        private final InputStream in;
        private final byte[] buffer = new byte[65536];
        private int position, limit;

        FastInput(String path) throws IOException {
            in = new FileInputStream(path);
        }

        private int read() throws IOException {
            if (position >= limit) {
                limit = in.read(buffer);
                position = 0;
                if (limit < 0) return -1;
            }
            return buffer[position++] & 255;
        }

        int nextInt() throws IOException {
            int c;
            do {
                c = read();
            } while (c <= 32 && c >= 0);

            int value = 0;
            while (c > 32) {
                value = value * 10 + c - '0';
                c = read();
            }
            return value;
        }

        String next() throws IOException {
            int c;
            do {
                c = read();
            } while (c <= 32 && c >= 0);

            StringBuilder result = new StringBuilder();
            while (c > 32) {
                result.append((char) c);
                c = read();
            }
            return result.toString();
        }

        public void close() throws IOException {
            in.close();
        }
    }

    private static byte[] encode(String value, int[] mapping) {
        byte[] result = new byte[value.length()];
        for (int i = 0; i < result.length; i++) {
            result[i] = (byte) mapping[value.charAt(i)];
        }
        return result;
    }

    private static long alignment(
            byte[] source, byte[] target,
            int[] insertion, int[] deletion, int[][] substitution) {

        int n = source.length;
        int m = target.length;
        int[] targetInsertion = new int[m];
        for (int j = 0; j < m; j++) {
            targetInsertion[j] = insertion[target[j]];
        }

        if ((long) n + m <= Integer.MAX_VALUE / 1000L) {
            int[] dp = new int[m + 1];
            for (int j = 0; j < m; j++) {
                dp[j + 1] = dp[j] + targetInsertion[j];
            }

            for (int i = 0; i < n; i++) {
                int letter = source[i];
                int deleteCost = deletion[letter];
                int[] substitutions = substitution[letter];
                int diagonal = dp[0];
                int left = diagonal + deleteCost;
                dp[0] = left;

                for (int j = 0; j < m; j++) {
                    int above = dp[j + 1];
                    int best = above + deleteCost;
                    int inserted = left + targetInsertion[j];
                    if (inserted < best) best = inserted;
                    int replaced = diagonal + substitutions[target[j]];
                    if (replaced < best) best = replaced;

                    dp[j + 1] = best;
                    diagonal = above;
                    left = best;
                }
            }
            return dp[m];
        }

        long[] dp = new long[m + 1];
        for (int j = 0; j < m; j++) {
            dp[j + 1] = dp[j] + targetInsertion[j];
        }

        for (int i = 0; i < n; i++) {
            int letter = source[i];
            int deleteCost = deletion[letter];
            int[] substitutions = substitution[letter];
            long diagonal = dp[0];
            long left = diagonal + deleteCost;
            dp[0] = left;

            for (int j = 0; j < m; j++) {
                long above = dp[j + 1];
                long best = above + deleteCost;
                long inserted = left + targetInsertion[j];
                if (inserted < best) best = inserted;
                long replaced = diagonal + substitutions[target[j]];
                if (replaced < best) best = replaced;

                dp[j + 1] = best;
                diagonal = above;
                left = best;
            }
        }
        return dp[m];
    }

    public static void main(String[] args) throws IOException {
        try (FastInput input = new FastInput(args[0])) {
            String alphabet = input.next();
            int size = alphabet.length();
            int[] mapping = new int[128];
            for (int i = 0; i < size; i++) {
                mapping[alphabet.charAt(i)] = i;
            }

            int[] insertion = new int[size];
            int[] deletion = new int[size];
            for (int i = 0; i < size; i++) {
                insertion[i] = input.nextInt();
            }
            for (int i = 0; i < size; i++) {
                deletion[i] = input.nextInt();
            }

            int[][] substitution = new int[size][size];
            int[][] transposed = new int[size][size];
            for (int i = 0; i < size; i++) {
                for (int j = 0; j < size; j++) {
                    int cost = input.nextInt();
                    substitution[i][j] = cost;
                    transposed[j][i] = cost;
                }
            }

            int pairs = input.nextInt();
            long total = 0;
            BufferedWriter output = new BufferedWriter(
                    new OutputStreamWriter(System.out, StandardCharsets.US_ASCII));

            for (int p = 0; p < pairs; p++) {
                String s = input.next();
                String t = input.next();
                long cost;

                if (s.equals(t)) {
                    cost = 0;
                } else {
                    byte[] source = encode(s, mapping);
                    byte[] target = encode(t, mapping);

                    if (target.length <= source.length) {
                        cost = alignment(
                                source, target, insertion, deletion, substitution);
                    } else {
                        cost = alignment(
                                target, source, deletion, insertion, transposed);
                    }
                }

                total += cost;
                output.write(Long.toString(cost));
                output.write('\n');
            }

            output.write("total ");
            output.write(Long.toString(total));
            output.write('\n');
            output.flush();
        }
    }
}
