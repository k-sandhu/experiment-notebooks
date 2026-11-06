import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;

public class Main {

    // Open-addressing map from lowercased word bytes to id.
    static int[] wordSlots; // id + 1, 0 means empty
    static int wordMask;
    static int wordCount;
    static ArrayList<byte[]> words; // id -> lowercase word bytes

    static int wordHash(byte[] buf, int len) {
        int h = 0x811c9dc5;
        for (int i = 0; i < len; ++i) {
            h ^= (buf[i] & 0xff);
            h *= 0x01000193;
        }
        return h;
    }

    static void growWords() {
        int[] old = wordSlots;
        int n = old.length * 2;
        wordSlots = new int[n];
        wordMask = n - 1;
        wordCount = 0;
        for (int v : old) {
            if (v == 0) continue;
            int id = v - 1;
            byte[] w = words.get(id);
            int h = wordHash(w, w.length) & wordMask;
            while (wordSlots[h] != 0) h = (h + 1) & wordMask;
            wordSlots[h] = v;
            ++wordCount;
        }
    }

    static int intern(byte[] buf, int len) {
        if (wordCount * 4 >= wordSlots.length * 3) growWords();
        int h = wordHash(buf, len) & wordMask;
        while (true) {
            int v = wordSlots[h];
            if (v == 0) {
                int id = wordCount++;
                words.add(Arrays.copyOf(buf, len));
                wordSlots[h] = id + 1;
                return id;
            }
            int id = v - 1;
            byte[] w = words.get(id);
            if (w.length == len) {
                boolean eq = true;
                for (int i = 0; i < len; ++i) {
                    if (w[i] != buf[i]) { eq = false; break; }
                }
                if (eq) return id;
            }
            h = (h + 1) & wordMask;
        }
    }

    // Open-addressing map from packed (id1, id2) pair key to count.
    static long[] pairKeys;   // -1L means empty (keys are always >= 0)
    static int[] pairCounts;
    static int pairMask;
    static int pairCount;

    static int pairHash(long k) {
        k ^= k >>> 33;
        k *= 0xff51afd7ed558ccdL;
        k ^= k >>> 33;
        k ^= k >>> 32;
        return (int) k;
    }

    static void growPairs() {
        long[] oldK = pairKeys;
        int[] oldC = pairCounts;
        int n = oldK.length * 2;
        pairKeys = new long[n];
        pairCounts = new int[n];
        pairMask = n - 1;
        Arrays.fill(pairKeys, -1L);
        pairCount = 0;
        for (int i = 0; i < oldK.length; ++i) {
            long k = oldK[i];
            if (k == -1L) continue;
            int h = pairHash(k) & pairMask;
            while (pairKeys[h] != -1L) h = (h + 1) & pairMask;
            pairKeys[h] = k;
            pairCounts[h] = oldC[i];
            ++pairCount;
        }
    }

    static int pairInsert(long key) {
        if ((pairCount + 1) * 4 >= pairKeys.length * 3) growPairs();
        int h = pairHash(key) & pairMask;
        while (pairKeys[h] != -1L) {
            if (pairKeys[h] == key) return h;
            h = (h + 1) & pairMask;
        }
        pairKeys[h] = key;
        pairCounts[h] = 0;
        ++pairCount;
        return h;
    }

    static int wordCmp(byte[] x, byte[] y) {
        int n = x.length < y.length ? x.length : y.length;
        for (int i = 0; i < n; ++i) {
            int cx = x[i] & 0xff;
            int cy = y[i] & 0xff;
            if (cx != cy) return cx - cy;
        }
        return x.length - y.length;
    }

    static long wordsCount;
    static long pairsCount;
    static int prevId = -1;

    static void noteWord(int id) {
        ++wordsCount;
        if (prevId >= 0) {
            ++pairsCount;
            long key = ((long) prevId << 32) | (id & 0xFFFFFFFFL);
            int idx = pairInsert(key);
            pairCounts[idx]++;
        }
        prevId = id;
    }

    public static void main(String[] args) throws Exception {
        byte[] data = Files.readAllBytes(Path.of(args[0]));

        wordSlots = new int[1 << 14];
        wordMask = wordSlots.length - 1;
        wordCount = 0;
        words = new ArrayList<>(1024);
        pairKeys = new long[1 << 16];
        pairCounts = new int[1 << 16];
        pairMask = pairKeys.length - 1;
        pairCount = 0;
        Arrays.fill(pairKeys, -1L);
        wordsCount = 0;
        pairsCount = 0;
        prevId = -1;

        byte[] buf = new byte[64];
        int blen = 0;
        int n = data.length;
        for (int i = 0; i < n; ++i) {
            int c = data[i] & 0xff;
            if ((c >= 65 && c <= 90) || (c >= 97 && c <= 122)) {
                if (blen == buf.length) buf = Arrays.copyOf(buf, buf.length * 2);
                buf[blen++] = (byte) (c | 0x20);
            } else {
                if (blen > 0) {
                    noteWord(intern(buf, blen));
                    blen = 0;
                }
                if (c == 46 || c == 33 || c == 63) prevId = -1;
            }
        }
        if (blen > 0) noteWord(intern(buf, blen));

        int distinct = pairCount;
        Entry[] ents = new Entry[distinct];
        int t = 0;
        for (int i = 0; i < pairKeys.length; ++i) {
            long k = pairKeys[i];
            if (k != -1L) {
                ents[t] = new Entry();
                ents[t].c = pairCounts[i];
                ents[t].a = (int) (k >>> 32);
                ents[t].b = (int) k;
                ++t;
            }
        }
        Arrays.sort(ents, (x, y) -> {
            if (x.c != y.c) return y.c - x.c;
            int cmp = wordCmp(words.get(x.a), words.get(y.a));
            if (cmp != 0) return cmp;
            return wordCmp(words.get(x.b), words.get(y.b));
        });

        StringBuilder sb = new StringBuilder();
        sb.append("words ").append(wordsCount).append('\n');
        sb.append("pairs ").append(pairsCount).append('\n');
        sb.append("distinct ").append(distinct).append('\n');
        int limit = distinct < 20 ? distinct : 20;
        for (int i = 0; i < limit; ++i) {
            sb.append(ents[i].c).append(' ');
            sb.append(new String(words.get(ents[i].a), java.nio.charset.StandardCharsets.US_ASCII));
            sb.append(' ');
            sb.append(new String(words.get(ents[i].b), java.nio.charset.StandardCharsets.US_ASCII));
            sb.append('\n');
        }
        System.out.print(sb);
    }

    static class Entry {
        int c, a, b;
    }
}
