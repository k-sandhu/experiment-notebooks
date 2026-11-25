import java.io.FileInputStream;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;

public class Main {
    private static final long FNV_OFFSET = 0xcbf29ce484222325L;
    private static final long FNV_PRIME = 0x100000001b3L;

    private static int hashIndex(long x, int mask) {
        x ^= x >>> 33;
        x *= 0xff51afd7ed558ccdL;
        x ^= x >>> 33;
        x *= 0xc4ceb9fe1a85ec53L;
        x ^= x >>> 33;
        return ((int) x) & mask;
    }

    private static final class Dictionary {
        byte[][] words = new byte[4096][];
        long[] hashes = new long[4096];
        int[] table = new int[8192];
        int size;
        int threshold = 6144;

        int intern(byte[] token, int length, long hash) {
            int mask = table.length - 1;
            int p = hashIndex(hash, mask);
            int entry;

            while ((entry = table[p]) != 0) {
                int id = entry - 1;
                byte[] word = words[id];
                if (hashes[id] == hash && word.length == length
                        && Arrays.equals(word, 0, length, token, 0, length)) {
                    return id;
                }
                p = (p + 1) & mask;
            }

            if (size >= threshold) {
                growTable();
                mask = table.length - 1;
                p = hashIndex(hash, mask);
                while (table[p] != 0) {
                    p = (p + 1) & mask;
                }
            }

            if (size == words.length) {
                int capacity = words.length << 1;
                words = Arrays.copyOf(words, capacity);
                hashes = Arrays.copyOf(hashes, capacity);
            }

            int id = size++;
            words[id] = Arrays.copyOf(token, length);
            hashes[id] = hash;
            table[p] = id + 1;
            return id;
        }

        private void growTable() {
            int[] replacement = new int[table.length << 1];
            int mask = replacement.length - 1;
            for (int id = 0; id < size; id++) {
                int p = hashIndex(hashes[id], mask);
                while (replacement[p] != 0) {
                    p = (p + 1) & mask;
                }
                replacement[p] = id + 1;
            }
            table = replacement;
            threshold = table.length - (table.length >>> 2);
        }
    }

    private static final class PairCounts {
        long[] keys = new long[1 << 16];
        int[] counts = new int[1 << 16];
        long[] wideCounts;
        int size;
        int threshold = (1 << 16) * 3 / 4;

        void add(long key) {
            int mask = keys.length - 1;
            int p = hashIndex(key, mask);
            long existing;

            while ((existing = keys[p]) != 0) {
                if (existing == key) {
                    if (counts != null) {
                        int next = counts[p] + 1;
                        counts[p] = next;
                        if (next == 0) {
                            promote(p);
                        }
                    } else {
                        wideCounts[p]++;
                    }
                    return;
                }
                p = (p + 1) & mask;
            }

            if (size >= threshold) {
                grow();
                mask = keys.length - 1;
                p = hashIndex(key, mask);
                while (keys[p] != 0) {
                    p = (p + 1) & mask;
                }
            }

            keys[p] = key;
            if (counts != null) {
                counts[p] = 1;
            } else {
                wideCounts[p] = 1;
            }
            size++;
        }

        private void promote(int overflowIndex) {
            wideCounts = new long[counts.length];
            for (int i = 0; i < counts.length; i++) {
                wideCounts[i] = Integer.toUnsignedLong(counts[i]);
            }
            wideCounts[overflowIndex] = 1L << 32;
            counts = null;
        }

        private void grow() {
            long[] oldKeys = keys;
            int capacity = oldKeys.length << 1;
            long[] newKeys = new long[capacity];
            int mask = capacity - 1;

            if (counts != null) {
                int[] oldCounts = counts;
                int[] newCounts = new int[capacity];
                for (int i = 0; i < oldKeys.length; i++) {
                    long key = oldKeys[i];
                    if (key != 0) {
                        int p = hashIndex(key, mask);
                        while (newKeys[p] != 0) {
                            p = (p + 1) & mask;
                        }
                        newKeys[p] = key;
                        newCounts[p] = oldCounts[i];
                    }
                }
                counts = newCounts;
            } else {
                long[] oldCounts = wideCounts;
                long[] newCounts = new long[capacity];
                for (int i = 0; i < oldKeys.length; i++) {
                    long key = oldKeys[i];
                    if (key != 0) {
                        int p = hashIndex(key, mask);
                        while (newKeys[p] != 0) {
                            p = (p + 1) & mask;
                        }
                        newKeys[p] = key;
                        newCounts[p] = oldCounts[i];
                    }
                }
                wideCounts = newCounts;
            }

            keys = newKeys;
            threshold = capacity - (capacity >>> 2);
        }
    }

    private static int compareWords(byte[] a, byte[] b) {
        int mismatch = Arrays.mismatch(a, b);
        if (mismatch < 0) {
            return 0;
        }
        if (mismatch == a.length) {
            return -1;
        }
        if (mismatch == b.length) {
            return 1;
        }
        return a[mismatch] - b[mismatch];
    }

    private static void sortWords(
            int[] ids, int[] temporary, int from, int to, byte[][] words) {
        if (to - from <= 1) {
            return;
        }

        int middle = (from + to) >>> 1;
        sortWords(ids, temporary, from, middle, words);
        sortWords(ids, temporary, middle, to, words);

        if (compareWords(words[ids[middle - 1]], words[ids[middle]]) <= 0) {
            return;
        }

        System.arraycopy(ids, from, temporary, from, to - from);
        int left = from;
        int right = middle;
        int destination = from;

        while (left < middle && right < to) {
            if (compareWords(words[temporary[left]], words[temporary[right]]) <= 0) {
                ids[destination++] = temporary[left++];
            } else {
                ids[destination++] = temporary[right++];
            }
        }
        while (left < middle) {
            ids[destination++] = temporary[left++];
        }
        while (right < to) {
            ids[destination++] = temporary[right++];
        }
    }

    public static void main(String[] args) throws Exception {
        Dictionary dictionary = new Dictionary();
        PairCounts pairCounts = new PairCounts();

        byte[] input = new byte[1 << 20];
        byte[] token = new byte[64];
        int tokenLength = 0;
        long wordHash = FNV_OFFSET;
        int previous = -1;
        long totalWords = 0;
        long totalPairs = 0;

        try (FileInputStream stream = new FileInputStream(args[0])) {
            int length;
            while ((length = stream.read(input)) != -1) {
                for (int i = 0; i < length; i++) {
                    int original = input[i] & 0xff;
                    int lower = original | 32;

                    if (lower >= 'a' && lower <= 'z') {
                        if (tokenLength == token.length) {
                            token = Arrays.copyOf(
                                    token, token.length + (token.length >>> 1) + 1);
                        }
                        token[tokenLength++] = (byte) lower;
                        wordHash = (wordHash ^ lower) * FNV_PRIME;
                    } else {
                        if (tokenLength != 0) {
                            int current = dictionary.intern(token, tokenLength, wordHash);
                            totalWords++;
                            if (previous >= 0) {
                                long key = ((long) (previous + 1) << 32)
                                        | ((current + 1L) & 0xffffffffL);
                                pairCounts.add(key);
                                totalPairs++;
                            }
                            previous = current;
                            tokenLength = 0;
                            wordHash = FNV_OFFSET;
                        }

                        if (original == '.' || original == '!' || original == '?') {
                            previous = -1;
                        }
                    }
                }
            }
        }

        if (tokenLength != 0) {
            int current = dictionary.intern(token, tokenLength, wordHash);
            totalWords++;
            if (previous >= 0) {
                long key = ((long) (previous + 1) << 32)
                        | ((current + 1L) & 0xffffffffL);
                pairCounts.add(key);
                totalPairs++;
            }
        }

        StringBuilder output = new StringBuilder(1024);
        output.append("words ").append(totalWords).append('\n');
        output.append("pairs ").append(totalPairs).append('\n');
        output.append("distinct ").append(pairCounts.size).append('\n');

        if (pairCounts.size != 0) {
            int vocabularySize = dictionary.size;
            int[] ids = new int[vocabularySize];
            for (int i = 0; i < vocabularySize; i++) {
                ids[i] = i;
            }
            sortWords(ids, new int[vocabularySize], 0, vocabularySize, dictionary.words);

            int[] ranks = new int[vocabularySize];
            for (int i = 0; i < vocabularySize; i++) {
                ranks[ids[i]] = i;
            }

            long[] bestKeys = new long[20];
            long[] bestCounts = new long[20];
            long[] bestLexical = new long[20];
            int bestSize = 0;

            long[] keys = pairCounts.keys;
            int[] counts = pairCounts.counts;
            long[] wideCounts = pairCounts.wideCounts;

            for (int i = 0; i < keys.length; i++) {
                long key = keys[i];
                if (key == 0) {
                    continue;
                }

                long count = counts != null
                        ? Integer.toUnsignedLong(counts[i])
                        : wideCounts[i];

                if (bestSize == 20 && count < bestCounts[19]) {
                    continue;
                }

                int first = (int) (key >>> 32) - 1;
                int second = (int) key - 1;
                long lexical = ((long) ranks[first] << 32)
                        | (ranks[second] & 0xffffffffL);

                if (bestSize == 20 && count == bestCounts[19]
                        && lexical >= bestLexical[19]) {
                    continue;
                }

                int position;
                if (bestSize < 20) {
                    position = bestSize++;
                } else {
                    position = 19;
                }

                while (position > 0
                        && (count > bestCounts[position - 1]
                        || (count == bestCounts[position - 1]
                        && lexical < bestLexical[position - 1]))) {
                    bestKeys[position] = bestKeys[position - 1];
                    bestCounts[position] = bestCounts[position - 1];
                    bestLexical[position] = bestLexical[position - 1];
                    position--;
                }

                bestKeys[position] = key;
                bestCounts[position] = count;
                bestLexical[position] = lexical;
            }

            for (int i = 0; i < bestSize; i++) {
                long key = bestKeys[i];
                int first = (int) (key >>> 32) - 1;
                int second = (int) key - 1;
                output.append(bestCounts[i]).append(' ')
                        .append(new String(dictionary.words[first], StandardCharsets.US_ASCII))
                        .append(' ')
                        .append(new String(dictionary.words[second], StandardCharsets.US_ASCII))
                        .append('\n');
            }
        }

        System.out.print(output);
    }
}
