import java.nio.file.Files;
import java.nio.file.Path;

public final class Main {
    private static final class Input {
        final byte[] data;
        int position, start, length;
        Input(String path) throws Exception { data = Files.readAllBytes(Path.of(path)); }
        void token() {
            while (position < data.length && data[position] <= 32) ++position;
            start = position;
            while (position < data.length && data[position] > 32) ++position;
            length = position - start;
        }
        int number() {
            token();
            int value = 0;
            for (int i = start; i < position; ++i) value = value * 10 + data[i] - 48;
            return value;
        }
    }

    private static final class Alignment {
        final int[][] ins = new int[2][26], del = new int[2][26];
        final int[][][] sub = new int[2][26][26];
        final int[][] profile = new int[26][];
        int[] insertion = new int[0], row32 = new int[0];
        long[] row64 = new long[0];

        long cost(byte[] data, int s, int n, int t, int m) {
            if (n == m) {
                int j = 0;
                while (j < n && data[s + j] == data[t + j]) ++j;
                if (j == n) return 0;
            }
            int direction = 0;
            if (n < m) {
                int swap = s; s = t; t = swap;
                swap = n; n = m; m = swap;
                direction = 1;
            }
            final int[] deletion = del[direction], insert = ins[direction];
            if (insertion.length < m) insertion = new int[m];
            long bound = 0;
            int used = 0;
            for (int i = 0; i < n; ++i) {
                int c = data[s + i] - 65;
                bound += deletion[c];
                used |= 1 << c;
            }
            for (int j = 0; j < m; ++j) {
                int value = insert[data[t + j] - 65];
                insertion[j] = value;
                bound += value;
            }
            if (bound == 0) return 0;
            for (int c = 0; c < 26; ++c) {
                if ((used & (1 << c)) == 0) continue;
                if (profile[c] == null || profile[c].length < m) profile[c] = new int[m];
                final int[] costs = profile[c], table = sub[direction][c];
                for (int j = 0; j < m; ++j) costs[j] = table[data[t + j] - 65];
            }
            if (bound <= Integer.MAX_VALUE - 1000)
                return evaluate32(data, s, n, m, deletion);
            return evaluate64(data, s, n, m, deletion);
        }

        private int evaluate32(byte[] data, int s, int n, int m, int[] deletion) {
            if (row32.length < m) row32 = new int[m];
            final int[] row = row32, insert = insertion;
            int prefix = 0;
            for (int j = 0; j < m; ++j) row[j] = prefix += insert[j];
            int boundary = 0;
            for (int i = 0; i < n; ++i) {
                final int c = data[s + i] - 65, d = deletion[c];
                final int[] costs = profile[c];
                int diagonal = boundary, left = boundary += d;
                for (int j = 0; j < m; ++j) {
                    int above = row[j];
                    left = Math.min(Math.min(above + d, left + insert[j]), diagonal + costs[j]);
                    row[j] = left;
                    diagonal = above;
                }
            }
            return row[m - 1];
        }

        private long evaluate64(byte[] data, int s, int n, int m, int[] deletion) {
            if (row64.length < m) row64 = new long[m];
            final long[] row = row64;
            final int[] insert = insertion;
            long prefix = 0;
            for (int j = 0; j < m; ++j) row[j] = prefix += insert[j];
            long boundary = 0;
            for (int i = 0; i < n; ++i) {
                final int c = data[s + i] - 65, d = deletion[c];
                final int[] costs = profile[c];
                long diagonal = boundary, left = boundary += d;
                for (int j = 0; j < m; ++j) {
                    long above = row[j];
                    left = Math.min(Math.min(above + d, left + insert[j]), diagonal + costs[j]);
                    row[j] = left;
                    diagonal = above;
                }
            }
            return row[m - 1];
        }
    }

    public static void main(String[] args) throws Exception {
        Input input = new Input(args[0]);
        input.token();
        final int alphabet = input.start, size = input.length;
        Alignment solver = new Alignment();
        for (int i = 0; i < size; ++i) solver.ins[0][input.data[alphabet + i] - 65] = input.number();
        for (int i = 0; i < size; ++i) solver.del[0][input.data[alphabet + i] - 65] = input.number();
        for (int i = 0; i < size; ++i)
            for (int j = 0; j < size; ++j)
                solver.sub[0][input.data[alphabet + i] - 65][input.data[alphabet + j] - 65] = input.number();
        for (int i = 0; i < 26; ++i) {
            solver.ins[1][i] = solver.del[0][i];
            solver.del[1][i] = solver.ins[0][i];
            for (int j = 0; j < 26; ++j) solver.sub[1][i][j] = solver.sub[0][j][i];
        }
        int pairs = input.number();
        long total = 0;
        StringBuilder output = new StringBuilder();
        for (int p = 0; p < pairs; ++p) {
            input.token();
            int s = input.start, n = input.length;
            input.token();
            long result = solver.cost(input.data, s, n, input.start, input.length);
            total += result;
            output.append(result).append('\n');
        }
        output.append("total ").append(total).append('\n');
        System.out.print(output);
    }
}
