import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;

public class Main {
    // Compact primitive records; widen automatically for larger vocabularies.
    static final class PairList {
        int[] narrow;
        long[] wide;
        int size;
        PairList(int estimate) { narrow = new int[Math.max(16, estimate)]; }
        void add(int a, int b) {
            if (wide == null && (a > 65535 || b > 65535)) {
                wide = new long[narrow.length];
                for (int i = 0; i < size; ++i)
                    wide[i] = ((long)(narrow[i] >>> 16) << 32) | (narrow[i] & 65535);
                narrow = null;
            }
            if (wide == null) {
                if (size == narrow.length) narrow = Arrays.copyOf(narrow, narrow.length * 2);
                narrow[size++] = (a << 16) | b;
            } else {
                if (size == wide.length) wide = Arrays.copyOf(wide, wide.length * 2);
                wide[size++] = ((long)a << 32) | (b & 0xffffffffL);
            }
        }
        void sort() {
            if (size < 2048) {
                if (wide == null) Arrays.sort(narrow, 0, size); else Arrays.sort(wide, 0, size);
                return;
            }
            int[] offsets = new int[2048];
            if (wide == null) {
                int variation = 0, first = narrow[0];
                for (int i = 0; i < size; ++i) variation |= narrow[i] ^ first;
                if (variation == 0) return;
                int[] scratch = new int[size];
                for (int shift = 0; shift < 32; shift += 11) {
                    if (((variation >>> shift) & 2047) == 0) continue;
                    Arrays.fill(offsets, 0);
                    for (int i = 0; i < size; ++i) ++offsets[(narrow[i] >>> shift) & 2047];
                    int total = 0;
                    for (int j = 0; j < offsets.length; ++j) { int count = offsets[j]; offsets[j] = total; total += count; }
                    for (int i = 0; i < size; ++i) scratch[offsets[(narrow[i] >>> shift) & 2047]++] = narrow[i];
                    int[] swap = narrow; narrow = scratch; scratch = swap;
                }
            } else {
                long variation = 0, first = wide[0];
                for (int i = 0; i < size; ++i) variation |= wide[i] ^ first;
                if (variation == 0) return;
                long[] scratch = new long[size];
                for (int shift = 0; shift < 64; shift += 11) {
                    if (((variation >>> shift) & 2047) == 0) continue;
                    Arrays.fill(offsets, 0);
                    for (int i = 0; i < size; ++i) ++offsets[(int)(wide[i] >>> shift) & 2047];
                    int total = 0;
                    for (int j = 0; j < offsets.length; ++j) { int count = offsets[j]; offsets[j] = total; total += count; }
                    for (int i = 0; i < size; ++i) scratch[offsets[(int)(wide[i] >>> shift) & 2047]++] = wide[i];
                    long[] swap = wide; wide = scratch; scratch = swap;
                }
            }
        }
        long key(int i) {
            return wide != null ? wide[i] : ((long)(narrow[i] >>> 16) << 32) | (narrow[i] & 65535);
        }
    }
    static final class Vocabulary {
        final byte[] data;
        int[] slots = new int[1024], starts = new int[1024], lengths = new int[1024], hashes = new int[1024];
        int size = 1; // Zero is reserved for an empty slot / no previous word.
        Vocabulary(byte[] data) { this.data = data; }
        int intern(int start, int length, int hash) {
            int mask = slots.length - 1, p = hash & mask;
            while (slots[p] != 0) {
                int id = slots[p];
                if (hashes[id] == hash && lengths[id] == length &&
                    Arrays.equals(data, start, start + length, data, starts[id], starts[id] + length)) return id;
                p = (p + 1) & mask;
            }
            if (size >= slots.length - slots.length / 4) {
                slots = new int[slots.length * 2]; mask = slots.length - 1;
                for (int id = 1; id < size; ++id) {
                    int q = hashes[id] & mask;
                    while (slots[q] != 0) q = (q + 1) & mask;
                    slots[q] = id;
                }
                p = hash & mask; while (slots[p] != 0) p = (p + 1) & mask;
            }
            if (size == starts.length) {
                starts = Arrays.copyOf(starts, size * 2);
                lengths = Arrays.copyOf(lengths, size * 2);
                hashes = Arrays.copyOf(hashes, size * 2);
            }
            int id = size++;
            starts[id] = start; lengths[id] = length; hashes[id] = hash; slots[p] = id;
            return id;
        }
        String word(int id) { return new String(data, starts[id], lengths[id], StandardCharsets.US_ASCII); }
    }
    static boolean better(long ak, long ac, long bk, long bc, int[] rank) {
        if (ac != bc) return ac > bc;
        int a = rank[(int)(ak >>> 32)], b = rank[(int)(bk >>> 32)];
        return a != b ? a < b : rank[(int)ak] < rank[(int)bk];
    }
    public static void main(String[] args) throws Exception {
        byte[] data = Files.readAllBytes(Path.of(args[0]));
        Vocabulary vocabulary = new Vocabulary(data);
        PairList pairs = new PairList(data.length / 6);
        long wordCount = 0, pairCount = 0;
        int previous = 0, i = 0;
        while (i < data.length) {
            int c = data[i] | 32;
            if (c >= 'a' && c <= 'z') {
                int start = i, h = 0x811c9dc5;
                do {
                    data[i++] = (byte)c; h = (h ^ c) * 16777619;
                    if (i == data.length) break;
                    c = data[i] | 32;
                } while (c >= 'a' && c <= 'z');
                int id = vocabulary.intern(start, i - start, h);
                ++wordCount;
                if (previous != 0) { pairs.add(previous, id); ++pairCount; }
                previous = id;
            } else {
                int raw = data[i++];
                if (raw == '.' || raw == '!' || raw == '?') previous = 0;
            }
        }
        Integer[] order = new Integer[vocabulary.size - 1];
        String[] words = new String[vocabulary.size];
        for (i = 1; i < vocabulary.size; ++i) { order[i - 1] = i; words[i] = vocabulary.word(i); }
        Arrays.sort(order, (a, b) -> words[a].compareTo(words[b]));
        int[] rank = new int[vocabulary.size];
        for (i = 0; i < order.length; ++i) rank[order[i]] = i;
        long[] topKeys = new long[20], topCounts = new long[20];
        int used = 0, distinct = 0;
        pairs.sort();
        for (i = 0; i < pairs.size;) {
            int start = i;
            long key = pairs.key(i++);
            while (i < pairs.size && pairs.key(i) == key) ++i;
            long count = i - start;
            ++distinct;
            if (used == 20 && !better(key, count, topKeys[19], topCounts[19], rank)) continue;
            int p = Math.min(used, 19);
            while (p > 0 && better(key, count, topKeys[p - 1], topCounts[p - 1], rank)) {
                topKeys[p] = topKeys[p - 1]; topCounts[p] = topCounts[p - 1]; --p;
            }
            topKeys[p] = key; topCounts[p] = count;
            if (used < 20) ++used;
        }
        StringBuilder out = new StringBuilder();
        out.append("words ").append(wordCount).append("\npairs ").append(pairCount)
           .append("\ndistinct ").append(distinct).append('\n');
        for (i = 0; i < used; ++i) out.append(topCounts[i]).append(' ')
            .append(words[(int)(topKeys[i] >>> 32)]).append(' ').append(words[(int)topKeys[i]]).append('\n');
        System.out.print(out);
    }
}
