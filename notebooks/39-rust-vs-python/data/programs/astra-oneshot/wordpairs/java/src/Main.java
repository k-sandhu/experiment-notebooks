import java.io.BufferedOutputStream;
import java.io.FileInputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;

public class Main {
    private static final int FNV_OFFSET = 0x811c9dc5;

    private static int mix32(int x) {
        x ^= x >>> 16;
        x *= 0x85ebca6b;
        x ^= x >>> 13;
        x *= 0xc2b2ae35;
        return x ^ (x >>> 16);
    }

    private static int pairHash(long x) {
        x ^= x >>> 33;
        x *= 0xff51afd7ed558ccdL;
        x ^= x >>> 33;
        x *= 0xc4ceb9fe1a85ec53L;
        x ^= x >>> 33;
        return (int) x;
    }

    private static final class Dictionary {
        byte[][] words = new byte[1024][];
        int[] hashes = new int[1024];
        int[] table = new int[4096];
        int size;
        int limit = (4096 * 7) / 10;

        int intern(byte[] bytes, int length, int rawHash) {
            int hash = mix32(rawHash);
            int mask = table.length - 1;
            int slot = hash & mask;

            while (true) {
                int id = table[slot];
                if (id == 0) {
                    break;
                }
                if (hashes[id] == hash) {
                    byte[] existing = words[id];
                    if (existing.length == length
                            && Arrays.equals(existing, 0, length, bytes, 0, length)) {
                        return id;
                    }
                }
                slot = (slot + 1) & mask;
            }

            if (size >= limit) {
                growTable();
                mask = table.length - 1;
                slot = hash & mask;
                while (table[slot] != 0) {
                    slot = (slot + 1) & mask;
                }
            }

            int id = size + 1;
            if (id == words.length) {
                int capacity = words.length << 1;
                words = Arrays.copyOf(words, capacity);
                hashes = Arrays.copyOf(hashes, capacity);
            }

            words[id] = Arrays.copyOf(bytes, length);
            hashes[id] = hash;
            table[slot] = id;
            size = id;
            return id;
        }

        private void growTable() {
            int capacity = table.length << 1;
            int[] replacement = new int[capacity];
            int mask = capacity - 1;

            for (int id = 1; id <= size; id++) {
                int slot = hashes[id] & mask;
                while (replacement[slot] != 0) {
                    slot = (slot + 1) & mask;
                }
                replacement[slot] = id;
            }

            table = replacement;
            limit = (int) (capacity * 0.7);
        }

        int[] lexicalRanks() {
            Integer[] order = new Integer[size];
            for (int i = 0; i < size; i++) {
                order[i] = i + 1;
            }

            byte[][] vocabulary = words;
            Arrays.sort(order,
                    (a, b) -> Arrays.compareUnsigned(vocabulary[a], vocabulary[b]));

            int[] ranks = new int[size + 1];
            for (int i = 0; i < order.length; i++) {
                ranks[order[i]] = i;
            }
            return ranks;
        }
    }

    private static final class PairCounter {
        long[] keys = new long[1 << 16];
        long[] counts = new long[1 << 16];
        int size;
        int limit = ((1 << 16) * 7) / 10;

        void add(long key) {
            long[] currentKeys = keys;
            int mask = currentKeys.length - 1;
            int hash = pairHash(key);
            int slot = hash & mask;

            while (true) {
                long existing = currentKeys[slot];
                if (existing == key) {
                    counts[slot]++;
                    return;
                }
                if (existing == 0) {
                    break;
                }
                slot = (slot + 1) & mask;
            }

            if (size >= limit) {
                grow();
                currentKeys = keys;
                mask = currentKeys.length - 1;
                slot = hash & mask;
                while (currentKeys[slot] != 0) {
                    slot = (slot + 1) & mask;
                }
            }

            currentKeys[slot] = key;
            counts[slot] = 1;
            size++;
        }

        private void grow() {
            long[] oldKeys = keys;
            long[] oldCounts = counts;
            int capacity = oldKeys.length << 1;
            long[] newKeys = new long[capacity];
            long[] newCounts = new long[capacity];
            int mask = capacity - 1;

            for (int i = 0; i < oldKeys.length; i++) {
                long key = oldKeys[i];
                if (key != 0) {
                    int slot = pairHash(key) & mask;
                    while (newKeys[slot] != 0) {
                        slot = (slot + 1) & mask;
                    }
                    newKeys[slot] = key;
                    newCounts[slot] = oldCounts[i];
                }
            }

            keys = newKeys;
            counts = newCounts;
            limit = (int) (capacity * 0.7);
        }
    }

    private static final class TopPairs {
        final long[] keys = new long[20];
        final long[] counts = new long[20];
        final long[] lexical = new long[20];
        int size;

        private static boolean worse(long countA, long lexA,
                                     long countB, long lexB) {
            return countA < countB || (countA == countB && lexA > lexB);
        }

        void offer(long key, long count, int[] ranks) {
            if (size == 20 && count < counts[0]) {
                return;
            }

            long lex = ((long) ranks[(int) (key >>> 32)] << 32)
                    | (ranks[(int) key] & 0xffffffffL);

            if (size < 20) {
                int position = size++;
                while (position > 0) {
                    int parent = (position - 1) >>> 1;
                    if (!worse(count, lex, counts[parent], lexical[parent])) {
                        break;
                    }
                    copy(parent, position);
                    position = parent;
                }
                set(position, key, count, lex);
                return;
            }

            if (!worse(counts[0], lexical[0], count, lex)) {
                return;
            }

            int position = 0;
            while (true) {
                int child = position * 2 + 1;
                if (child >= size) {
                    break;
                }

                int right = child + 1;
                if (right < size
                        && worse(counts[right], lexical[right],
                                 counts[child], lexical[child])) {
                    child = right;
                }

                if (!worse(counts[child], lexical[child], count, lex)) {
                    break;
                }
                copy(child, position);
                position = child;
            }
            set(position, key, count, lex);
        }

        private void copy(int from, int to) {
            keys[to] = keys[from];
            counts[to] = counts[from];
            lexical[to] = lexical[from];
        }

        private void set(int position, long key, long count, long lex) {
            keys[position] = key;
            counts[position] = count;
            lexical[position] = lex;
        }

        void sortBestFirst() {
            for (int i = 1; i < size; i++) {
                long key = keys[i];
                long count = counts[i];
                long lex = lexical[i];
                int j = i - 1;

                while (j >= 0 && worse(counts[j], lexical[j], count, lex)) {
                    copy(j, j + 1);
                    j--;
                }
                set(j + 1, key, count, lex);
            }
        }
    }

    private static void writeAscii(OutputStream out, String text) throws Exception {
        out.write(text.getBytes(StandardCharsets.US_ASCII));
    }

    public static void main(String[] args) throws Exception {
        Dictionary dictionary = new Dictionary();
        PairCounter pairCounter = new PairCounter();

        long totalWords = 0;
        long totalPairs = 0;
        int previous = 0;

        byte[] inputBuffer = new byte[1 << 20];
        byte[] wordBuffer = new byte[64];
        int wordLength = 0;
        int wordHash = FNV_OFFSET;

        try (FileInputStream input = new FileInputStream(args[0])) {
            int bytesRead;
            while ((bytesRead = input.read(inputBuffer)) != -1) {
                for (int i = 0; i < bytesRead; i++) {
                    int b = inputBuffer[i] & 0xff;
                    int lower = b | 32;

                    if (lower >= 'a' && lower <= 'z') {
                        if (wordLength == wordBuffer.length) {
                            wordBuffer = Arrays.copyOf(
                                    wordBuffer, wordBuffer.length << 1);
                        }
                        wordBuffer[wordLength++] = (byte) lower;
                        wordHash = (wordHash ^ lower) * 0x01000193;
                    } else {
                        if (wordLength != 0) {
                            int id = dictionary.intern(
                                    wordBuffer, wordLength, wordHash);
                            totalWords++;
                            if (previous != 0) {
                                pairCounter.add(((long) previous << 32)
                                        | (id & 0xffffffffL));
                                totalPairs++;
                            }
                            previous = id;
                            wordLength = 0;
                            wordHash = FNV_OFFSET;
                        }

                        if (b == '.' || b == '!' || b == '?') {
                            previous = 0;
                        }
                    }
                }
            }
        }

        if (wordLength != 0) {
            int id = dictionary.intern(wordBuffer, wordLength, wordHash);
            totalWords++;
            if (previous != 0) {
                pairCounter.add(((long) previous << 32) | (id & 0xffffffffL));
                totalPairs++;
            }
        }

        TopPairs top = new TopPairs();
        if (pairCounter.size != 0) {
            int[] ranks = dictionary.lexicalRanks();
            long[] keys = pairCounter.keys;
            long[] counts = pairCounter.counts;

            for (int i = 0; i < keys.length; i++) {
                if (keys[i] != 0) {
                    top.offer(keys[i], counts[i], ranks);
                }
            }
            top.sortBestFirst();
        }

        BufferedOutputStream output = new BufferedOutputStream(System.out, 65536);
        writeAscii(output, "words " + totalWords + "\n"
                + "pairs " + totalPairs + "\n"
                + "distinct " + pairCounter.size + "\n");

        for (int i = 0; i < top.size; i++) {
            long key = top.keys[i];
            writeAscii(output, Long.toString(top.counts[i]));
            output.write(' ');
            output.write(dictionary.words[(int) (key >>> 32)]);
            output.write(' ');
            output.write(dictionary.words[(int) key]);
            output.write('\n');
        }
        output.flush();
    }
}
