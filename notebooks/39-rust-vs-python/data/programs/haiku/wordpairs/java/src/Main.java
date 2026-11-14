import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;

// Counts adjacent word pairs within sentences and prints the 20 most frequent ones (see SPEC.md).
//
// One pass over the whole input: letters form words, which are looked up in an open-addressing
// vocabulary table; each pair of neighbouring words is counted in an open-addressing table kept in
// a flat int array (three ints per slot), so no boxing happens on the hot path.
public final class Main {
    // Byte classes.
    private static final byte SEPARATOR = 0;
    private static final byte LETTER = 1;
    private static final byte SENTENCE_END = 2;
    private static final byte[] CLASS = new byte[256];

    static {
        for (int c = 'A'; c <= 'Z'; c++) {
            CLASS[c] = LETTER;
            CLASS[c + 32] = LETTER;
        }
        CLASS['.'] = SENTENCE_END;
        CLASS['!'] = SENTENCE_END;
        CLASS['?'] = SENTENCE_END;
    }

    private static final int FNV_OFFSET = 0x811C9DC5;
    private static final int FNV_PRIME = 0x01000193;
    private static final int NO_WORD = -1;
    private static final int TOP = 20;

    private Main() {
    }

    static int mixPair(int a, int b) {
        int h = (a * 0x9E3779B1) ^ b;
        h ^= h >>> 16;
        h *= 0x85EBCA6B;
        h ^= h >>> 13;
        return h;
    }

    // Maps lower-cased words to dense ids in first-seen order.
    static final class Vocab {
        private static final int INITIAL_SLOTS = 1 << 16;

        private int[] table = new int[INITIAL_SLOTS]; // id + 1, 0 = empty
        private int[] hashes = new int[1024];
        private String[] words = new String[1024];
        private int size;

        // buf[start..start+len) holds letters in either case; h is the FNV-1a hash of their lower-case form.
        int find(byte[] buf, int start, int len, int h) {
            int mask = table.length - 1;
            int idx = h & mask;
            int v;
            while ((v = table[idx]) != 0) {
                int id = v - 1;
                if (hashes[id] == h && sameFolded(words[id], buf, start, len)) {
                    return id;
                }
                idx = (idx + 1) & mask;
            }
            int id = size;
            byte[] lower = new byte[len];
            for (int j = 0; j < len; j++) {
                lower[j] = (byte) (buf[start + j] | 0x20);
            }
            if (id == words.length) {
                words = Arrays.copyOf(words, id * 2);
                hashes = Arrays.copyOf(hashes, id * 2);
            }
            words[id] = new String(lower, StandardCharsets.ISO_8859_1);
            hashes[id] = h;
            table[idx] = id + 1;
            size = id + 1;
            if (size * 2L > table.length) {
                rehash();
            }
            return id;
        }

        String word(int id) {
            return words[id];
        }

        int size() {
            return size;
        }

        private static boolean sameFolded(String w, byte[] buf, int start, int len) {
            if (w.length() != len) {
                return false;
            }
            for (int j = 0; j < len; j++) {
                if (w.charAt(j) != (buf[start + j] | 0x20)) {
                    return false;
                }
            }
            return true;
        }

        private void rehash() {
            int[] bigger = new int[table.length * 2];
            int mask = bigger.length - 1;
            for (int id = 0; id < size; id++) {
                int idx = hashes[id] & mask;
                while (bigger[idx] != 0) {
                    idx = (idx + 1) & mask;
                }
                bigger[idx] = id + 1;
            }
            table = bigger;
        }
    }

    // Counts ordered pairs of word ids. Slot k is data[3k..3k+2] = (first, second, count); count 0 = empty.
    static final class PairCounter {
        private static final int INITIAL_SLOTS = 1 << 20;

        private int[] data = new int[INITIAL_SLOTS * 3];
        private int mask = INITIAL_SLOTS - 1;
        private long distinct;

        void add(int a, int b) {
            int idx = mixPair(a, b) & mask;
            while (true) {
                int p = idx * 3;
                if (data[p + 2] == 0) {
                    data[p] = a;
                    data[p + 1] = b;
                    data[p + 2] = 1;
                    if (++distinct * 4 > (mask + 1) * 3L) {
                        grow();
                    }
                    return;
                }
                if (data[p] == a && data[p + 1] == b) {
                    data[p + 2]++;
                    return;
                }
                idx = (idx + 1) & mask;
            }
        }

        long distinct() {
            return distinct;
        }

        private void grow() {
            int cap = (mask + 1) * 2;
            int[] bigger = new int[cap * 3];
            int m = cap - 1;
            for (int s = 0; s < data.length; s += 3) {
                if (data[s + 2] == 0) {
                    continue;
                }
                int idx = mixPair(data[s], data[s + 1]) & m;
                while (bigger[idx * 3 + 2] != 0) {
                    idx = (idx + 1) & m;
                }
                System.arraycopy(data, s, bigger, idx * 3, 3);
            }
            data = bigger;
            mask = m;
        }
    }

    // Entry k of a top list is t[3k..3k+2] = (count, first id, second id).
    private static boolean better(int[] t, int x, int y, int[] rank) {
        int cx = t[3 * x];
        int cy = t[3 * y];
        if (cx != cy) {
            return cx > cy;
        }
        int ax = rank[t[3 * x + 1]];
        int ay = rank[t[3 * y + 1]];
        if (ax != ay) {
            return ax < ay;
        }
        return rank[t[3 * x + 2]] < rank[t[3 * y + 2]];
    }

    private static void swapEntries(int[] t, int x, int y) {
        for (int k = 0; k < 3; k++) {
            int tmp = t[3 * x + k];
            t[3 * x + k] = t[3 * y + k];
            t[3 * y + k] = tmp;
        }
    }

    public static void main(String[] args) throws IOException {
        if (args.length < 1) {
            System.err.println("usage: run INPUT_PATH");
            System.exit(2);
        }
        byte[] buf = Files.readAllBytes(Path.of(args[0]));
        Vocab vocab = new Vocab();
        PairCounter pairs = new PairCounter();
        long words = 0;
        long total = 0;
        int prev = NO_WORD;
        int n = buf.length;
        int i = 0;
        while (i < n) {
            byte cls = CLASS[buf[i] & 0xFF];
            if (cls == LETTER) {
                int start = i;
                int h = FNV_OFFSET;
                do {
                    h = (h ^ ((buf[i] & 0xFF) | 0x20)) * FNV_PRIME;
                    i++;
                } while (i < n && CLASS[buf[i] & 0xFF] == LETTER);
                int id = vocab.find(buf, start, i - start, h);
                words++;
                if (prev != NO_WORD) {
                    pairs.add(prev, id);
                    total++;
                }
                prev = id;
            } else {
                if (cls == SENTENCE_END) {
                    prev = NO_WORD;
                }
                i++;
            }
        }

        // Rank words by byte order so ties can be broken with integer comparisons.
        int vocabSize = vocab.size();
        Integer[] order = new Integer[vocabSize];
        for (int k = 0; k < vocabSize; k++) {
            order[k] = k;
        }
        Arrays.sort(order, (x, y) -> vocab.word(x).compareTo(vocab.word(y)));
        int[] rank = new int[vocabSize];
        for (int r = 0; r < vocabSize; r++) {
            rank[order[r]] = r;
        }

        int[] top = new int[3 * (TOP + 1)];
        int k = 0;
        int[] data = pairs.data;
        for (int s = 0; s < data.length; s += 3) {
            int c = data[s + 2];
            if (c == 0) {
                continue;
            }
            int j = k;
            top[3 * j] = c;
            top[3 * j + 1] = data[s];
            top[3 * j + 2] = data[s + 1];
            if (k == TOP && !better(top, TOP, TOP - 1, rank)) {
                continue;
            }
            if (k < TOP) {
                k++;
            }
            while (j > 0 && better(top, j, j - 1, rank)) {
                swapEntries(top, j, j - 1);
                j--;
            }
        }

        StringBuilder out = new StringBuilder();
        out.append("words ").append(words).append('\n');
        out.append("pairs ").append(total).append('\n');
        out.append("distinct ").append(pairs.distinct()).append('\n');
        for (int r = 0; r < k; r++) {
            out.append(top[3 * r]).append(' ')
                    .append(vocab.word(top[3 * r + 1])).append(' ')
                    .append(vocab.word(top[3 * r + 2])).append('\n');
        }
        System.out.print(out);
        System.out.flush();
    }
}
