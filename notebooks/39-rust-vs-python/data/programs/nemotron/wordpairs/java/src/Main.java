import java.io.BufferedWriter;
import java.io.OutputStreamWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;

// Word pairs benchmark - Java 23.
// Single pass: lowercase words in place, intern them to ids, emit packed
// (prevId, curId) pairs within sentences, sort the packed pairs, count runs,
// keep the top 20 by (count desc, word1 asc, word2 asc).
public class Main {

    static boolean isLetter(int c) {
        c |= 0x20;
        return c >= 'a' && c <= 'z';
    }

    // Open-addressing map from lowercase word to a dense id.
    // Lookup compares against the input buffer region directly, so only
    // distinct words are turned into String objects.
    static final class WordMap {
        String[] keys;
        int[] hashes;
        int[] ids;
        int mask;
        int occupied;
        int growAt;
        final ArrayList<String> words; // id -> word

        WordMap(int cap) {
            keys = new String[cap];
            hashes = new int[cap];
            ids = new int[cap];
            mask = cap - 1;
            growAt = (int) (cap * 0.75);
            words = new ArrayList<>();
        }

        private void grow() {
            String[] oldKeys = keys;
            int[] oldHashes = hashes;
            int[] oldIds = ids;
            int newCap = oldKeys.length * 2;
            keys = new String[newCap];
            hashes = new int[newCap];
            ids = new int[newCap];
            mask = newCap - 1;
            growAt = (int) (newCap * 0.75);
            for (int i = 0; i < oldKeys.length; i++) {
                String k = oldKeys[i];
                if (k != null) {
                    int h = oldHashes[i] & mask;
                    int pos = h;
                    while (keys[pos] != null) pos = (pos + 1) & mask;
                    keys[pos] = k;
                    hashes[pos] = oldHashes[i];
                    ids[pos] = oldIds[i];
                }
            }
        }

        static int hashBytes(byte[] data, int start, int len) {
            int h = (int) 2166136261L;
            for (int i = 0; i < len; i++) {
                h = (h * 16777619) ^ (data[start + i] & 0xFF);
            }
            return h;
        }

        static boolean equalsBytes(String k, byte[] data, int start, int len) {
            if (k.length() != len) return false;
            for (int i = 0; i < len; i++) {
                if (k.charAt(i) != (data[start + i] & 0xFF)) return false;
            }
            return true;
        }

        int getOrPut(byte[] data, int start, int len, int hash) {
            int pos = hash & mask;
            while (true) {
                String k = keys[pos];
                if (k == null) {
                    String s = new String(data, start, len, StandardCharsets.US_ASCII);
                    keys[pos] = s;
                    hashes[pos] = hash;
                    ids[pos] = occupied;
                    words.add(s);
                    int id = occupied++;
                    if (occupied >= growAt) grow();
                    return id;
                }
                if (hashes[pos] == hash && equalsBytes(k, data, start, len)) {
                    return ids[pos];
                }
                pos = (pos + 1) & mask;
            }
        }
    }

    // Top-N bookkeeping (N = 20), ordered best-first.
    static long[] bestCount = new long[20];
    static int[] bestW1 = new int[20];
    static int[] bestW2 = new int[20];
    static int bestn = 0;
    static ArrayList<String> words;

    static boolean better(long c1, int a1, int b1, long c2, int a2, int b2) {
        if (c1 != c2) return c1 > c2;
        int cmp = words.get(a1).compareTo(words.get(a2));
        if (cmp != 0) return cmp < 0;
        return words.get(b1).compareTo(words.get(b2)) < 0;
    }

    static void consider(long count, int w1, int w2) {
        if (bestn < 20) {
            int pos = bestn;
            while (pos > 0 && better(count, w1, w2, bestCount[pos - 1], bestW1[pos - 1], bestW2[pos - 1])) {
                bestCount[pos] = bestCount[pos - 1];
                bestW1[pos] = bestW1[pos - 1];
                bestW2[pos] = bestW2[pos - 1];
                pos--;
            }
            bestCount[pos] = count;
            bestW1[pos] = w1;
            bestW2[pos] = w2;
            bestn++;
        } else if (better(count, w1, w2, bestCount[19], bestW1[19], bestW2[19])) {
            long c = count;
            int a = w1;
            int b = w2;
            int pos = 19;
            while (pos > 0 && better(c, a, b, bestCount[pos - 1], bestW1[pos - 1], bestW2[pos - 1])) {
                bestCount[pos] = bestCount[pos - 1];
                bestW1[pos] = bestW1[pos - 1];
                bestW2[pos] = bestW2[pos - 1];
                pos--;
            }
            bestCount[pos] = c;
            bestW1[pos] = a;
            bestW2[pos] = b;
        }
    }

    public static void main(String[] args) throws Exception {
        byte[] data = Files.readAllBytes(Path.of(args[0]));
        int n = data.length;
        WordMap map = new WordMap(1 << 14);
        words = map.words;
        long[] pairs = new long[1 << 20];
        int pairCount = 0;
        int prevId = 0;
        boolean havePrev = false;
        long wordTotal = 0, pairTotal = 0;

        int i = 0;
        while (i < n) {
            while (i < n) {
                int c = data[i] & 0xFF;
                if (isLetter(c)) break;
                if (c == '.' || c == '!' || c == '?') havePrev = false;
                i++;
            }
            if (i >= n) break;
            int start = i;
            int h = (int) 2166136261L;
            while (i < n) {
                int c = data[i] & 0xFF;
                if (!isLetter(c)) break;
                if (c >= 'A' && c <= 'Z') c += 32;
                data[i] = (byte) c;
                h = (h * 16777619) ^ c;
                i++;
            }
            int len = i - start;
            int id = map.getOrPut(data, start, len, h);
            wordTotal++;
            if (havePrev) {
                pairTotal++;
                if (pairCount == pairs.length) {
                    long[] nb = new long[pairs.length * 2];
                    System.arraycopy(pairs, 0, nb, 0, pairCount);
                    pairs = nb;
                }
                pairs[pairCount++] = ((long) prevId << 32) | (id & 0xFFFFFFFFL);
            }
            prevId = id;
            havePrev = true;
        }

        Arrays.sort(pairs, 0, pairCount);

        int k = 0;
        long distinct = 0;
        while (k < pairCount) {
            int j = k + 1;
            while (j < pairCount && pairs[j] == pairs[k]) j++;
            consider(j - k, (int) (pairs[k] >>> 32), (int) (pairs[k] & 0xFFFFFFFFL));
            distinct++;
            k = j;
        }

        BufferedWriter out =
            new BufferedWriter(new OutputStreamWriter(System.out, StandardCharsets.US_ASCII));
        out.write("words ");
        out.write(Long.toString(wordTotal));
        out.write('\n');
        out.write("pairs ");
        out.write(Long.toString(pairTotal));
        out.write('\n');
        out.write("distinct ");
        out.write(Long.toString(distinct));
        out.write('\n');
        for (int t = 0; t < bestn; t++) {
            out.write(Long.toString(bestCount[t]));
            out.write(' ');
            out.write(words.get(bestW1[t]));
            out.write(' ');
            out.write(words.get(bestW2[t]));
            out.write('\n');
        }
        out.flush();
    }
}
