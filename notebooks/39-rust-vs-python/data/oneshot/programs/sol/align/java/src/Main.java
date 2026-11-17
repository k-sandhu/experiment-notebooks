import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.Arrays;

public class Main {
    private static final class FastInput {
        private final InputStream input;
        private final byte[] buffer = new byte[1 << 16];
        private int position;
        private int limit;

        FastInput(InputStream input) {
            this.input = input;
        }

        private int read() throws IOException {
            if (position >= limit) {
                limit = input.read(buffer);
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
    }

    private static final class Solver {
        private final int[] map;
        private final int[] insertion;
        private final int[] deletion;
        private final int[][] substitution;
        private final int[][] transposed;

        private int[] target = new int[0];
        private int[] targetInsertion = new int[0];
        private int[] dp = new int[0];
        private long[] longDp = new long[0];

        Solver(int[] map, int[] insertion, int[] deletion, int[][] substitution) {
            this.map = map;
            this.insertion = insertion;
            this.deletion = deletion;
            this.substitution = substitution;

            int alphabetSize = insertion.length;
            transposed = new int[alphabetSize][alphabetSize];
            for (int i = 0; i < alphabetSize; i++) {
                for (int j = 0; j < alphabetSize; j++) {
                    transposed[j][i] = substitution[i][j];
                }
            }
        }

        long cost(String source, String destination) {
            if (source.equals(destination)) return 0;

            int[] insert = insertion;
            int[] delete = deletion;
            int[][] replace = substitution;

            if (source.length() < destination.length()) {
                String temporary = source;
                source = destination;
                destination = temporary;
                insert = deletion;
                delete = insertion;
                replace = transposed;
            }

            int n = source.length();
            int m = destination.length();
            if (target.length <= m) {
                target = new int[m + 1];
                targetInsertion = new int[m + 1];
                dp = new int[m + 1];
            }

            long bound = 0;
            for (int j = 1; j <= m; j++) {
                int letter = map[destination.charAt(j - 1) - 'A'];
                target[j] = letter;
                int value = insert[letter];
                targetInsertion[j] = value;
                bound += value;
            }
            for (int i = 0; i < n; i++) {
                bound += delete[map[source.charAt(i) - 'A']];
            }

            if (bound == 0) return 0;

            if (bound <= Integer.MAX_VALUE - 1000L) {
                dp[0] = 0;
                for (int j = 1; j <= m; j++) {
                    dp[j] = dp[j - 1] + targetInsertion[j];
                }

                for (int i = 0; i < n; i++) {
                    int letter = map[source.charAt(i) - 'A'];
                    int removal = delete[letter];
                    int[] substitutions = replace[letter];
                    int diagonal = dp[0];
                    int left = diagonal + removal;
                    dp[0] = left;

                    for (int j = 1; j <= m; j++) {
                        int above = dp[j];
                        int best = above + removal;
                        int candidate = left + targetInsertion[j];
                        if (candidate < best) best = candidate;
                        candidate = diagonal + substitutions[target[j]];
                        if (candidate < best) best = candidate;

                        dp[j] = best;
                        left = best;
                        diagonal = above;
                    }
                }
                return dp[m];
            }

            if (longDp.length <= m) {
                longDp = new long[m + 1];
            }
            longDp[0] = 0;
            for (int j = 1; j <= m; j++) {
                longDp[j] = longDp[j - 1] + targetInsertion[j];
            }

            for (int i = 0; i < n; i++) {
                int letter = map[source.charAt(i) - 'A'];
                int removal = delete[letter];
                int[] substitutions = replace[letter];
                long diagonal = longDp[0];
                long left = diagonal + removal;
                longDp[0] = left;

                for (int j = 1; j <= m; j++) {
                    long above = longDp[j];
                    long best = above + removal;
                    long candidate = left + targetInsertion[j];
                    if (candidate < best) best = candidate;
                    candidate = diagonal + substitutions[target[j]];
                    if (candidate < best) best = candidate;

                    longDp[j] = best;
                    left = best;
                    diagonal = above;
                }
            }
            return longDp[m];
        }
    }

    public static void main(String[] args) throws Exception {
        try (InputStream file = new FileInputStream(args[0])) {
            FastInput input = new FastInput(file);
            String alphabet = input.next();
            int size = alphabet.length();

            int[] map = new int[26];
            Arrays.fill(map, -1);
            for (int i = 0; i < size; i++) {
                map[alphabet.charAt(i) - 'A'] = i;
            }

            int[] insertion = new int[size];
            int[] deletion = new int[size];
            int[][] substitution = new int[size][size];

            for (int i = 0; i < size; i++) insertion[i] = input.nextInt();
            for (int i = 0; i < size; i++) deletion[i] = input.nextInt();
            for (int i = 0; i < size; i++) {
                for (int j = 0; j < size; j++) {
                    substitution[i][j] = input.nextInt();
                }
            }

            Solver solver = new Solver(map, insertion, deletion, substitution);
            int pairs = input.nextInt();
            StringBuilder output = new StringBuilder();
            long total = 0;

            for (int i = 0; i < pairs; i++) {
                String source = input.next();
                String destination = input.next();
                long result = solver.cost(source, destination);
                output.append(result).append('\n');
                total += result;
            }

            output.append("total ").append(total).append('\n');
            System.out.print(output);
        }
    }
}
