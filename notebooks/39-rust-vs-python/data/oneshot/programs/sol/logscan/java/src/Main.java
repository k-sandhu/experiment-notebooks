import java.io.FileInputStream;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;

public class Main {
    private static final long DIV10 = Long.MAX_VALUE / 10;
    private static final int LAST_DIGIT = (int) (Long.MAX_VALUE % 10);

    private long lines;
    private long malformed;
    private final long[] statuses = new long[10];

    private Entry[] table = new Entry[1024];
    private int entryCount;
    private int resizeAt = 768;
    private byte[] templateBuffer = new byte[128];

    private static final class Entry {
        final byte[] key;
        final int hash;
        long count;
        long[] values;
        int size;
        ArrayList<BigInteger> large;

        Entry(byte[] key, int hash) {
            this.key = key;
            this.hash = hash;
        }

        void add(long value) {
            if (values == null) {
                values = new long[1];
            } else if (size == values.length) {
                int capacity = (int) Math.min(
                        Integer.MAX_VALUE - 8L, (long) values.length * 2);
                values = Arrays.copyOf(values, capacity);
            }
            values[size++] = value;
            count++;
        }

        void add(BigInteger value) {
            if (large == null) {
                large = new ArrayList<>();
            }
            large.add(value);
            count++;
        }

        void sort() {
            if (size > 1) {
                Arrays.sort(values, 0, size);
            }
            if (large != null) {
                large.sort(null);
            }
        }
    }

    private static boolean digit(int c) {
        return c >= '0' && c <= '9';
    }

    private static boolean pathCharacter(int c) {
        return (c >= 'a' && c <= 'z')
                || (c >= 'A' && c <= 'Z')
                || (c >= '0' && c <= '9')
                || c == '_' || c == '/' || c == '-';
    }

    private boolean process(byte[] b, int start, int end) {
        if (end - start < 50) {
            return false;
        }

        if (b[start + 4] != '-' || b[start + 7] != '-'
                || b[start + 10] != 'T' || b[start + 13] != ':'
                || b[start + 16] != ':' || b[start + 19] != '.'
                || b[start + 23] != 'Z' || b[start + 24] != ' ') {
            return false;
        }

        if (!digit(b[start]) || !digit(b[start + 1])
                || !digit(b[start + 2]) || !digit(b[start + 3])
                || !digit(b[start + 5]) || !digit(b[start + 6])
                || !digit(b[start + 8]) || !digit(b[start + 9])
                || !digit(b[start + 11]) || !digit(b[start + 12])
                || !digit(b[start + 14]) || !digit(b[start + 15])
                || !digit(b[start + 17]) || !digit(b[start + 18])
                || !digit(b[start + 20]) || !digit(b[start + 21])
                || !digit(b[start + 22])) {
            return false;
        }

        int p = start + 25;
        int fieldStart = p;
        while (p < end && b[p] >= 'a' && b[p] <= 'z') {
            p++;
        }
        if (p == fieldStart || p >= end || b[p] != '-') {
            return false;
        }

        fieldStart = ++p;
        while (p < end && digit(b[p])) {
            p++;
        }
        if (p == fieldStart || p >= end || b[p] != ' ') {
            return false;
        }

        int methodStart = ++p;
        while (p < end && b[p] != ' ') {
            p++;
        }
        if (p == end) {
            return false;
        }

        boolean validMethod = switch (p - methodStart) {
            case 3 ->
                    (b[methodStart] == 'G'
                            && b[methodStart + 1] == 'E'
                            && b[methodStart + 2] == 'T')
                    || (b[methodStart] == 'P'
                            && b[methodStart + 1] == 'U'
                            && b[methodStart + 2] == 'T');
            case 4 ->
                    b[methodStart] == 'P'
                            && b[methodStart + 1] == 'O'
                            && b[methodStart + 2] == 'S'
                            && b[methodStart + 3] == 'T';
            case 5 ->
                    b[methodStart] == 'P'
                            && b[methodStart + 1] == 'A'
                            && b[methodStart + 2] == 'T'
                            && b[methodStart + 3] == 'C'
                            && b[methodStart + 4] == 'H';
            case 6 ->
                    b[methodStart] == 'D'
                            && b[methodStart + 1] == 'E'
                            && b[methodStart + 2] == 'L'
                            && b[methodStart + 3] == 'E'
                            && b[methodStart + 4] == 'T'
                            && b[methodStart + 5] == 'E';
            default -> false;
        };
        if (!validMethod) {
            return false;
        }

        p++;
        if (p >= end || b[p] != '/') {
            return false;
        }
        int pathStart = p++;
        while (p < end && pathCharacter(b[p])) {
            p++;
        }
        int pathEnd = p;

        if (p < end && b[p] == '?') {
            p++;
            while (p < end && b[p] != ' ') {
                p++;
            }
        }
        if (p >= end || b[p] != ' ') {
            return false;
        }
        p++;

        if (end - p < 4
                || !digit(b[p]) || !digit(b[p + 1]) || !digit(b[p + 2])
                || b[p + 3] != ' ') {
            return false;
        }
        int statusClass = b[p] - '0';
        p += 4;

        fieldStart = p;
        while (p < end && digit(b[p])) {
            p++;
        }
        if (p == fieldStart || end - p < 2
                || b[p] != 'B' || b[p + 1] != ' ') {
            return false;
        }
        p += 2;

        int latencyStart = p;
        long latency = 0;
        boolean overflow = false;
        while (p < end && digit(b[p])) {
            int d = b[p] - '0';
            if (!overflow) {
                if (latency > DIV10
                        || (latency == DIV10 && d > LAST_DIGIT)) {
                    overflow = true;
                } else {
                    latency = latency * 10 + d;
                }
            }
            p++;
        }
        int latencyEnd = p;

        if (p == latencyStart || end - p < 7
                || b[p] != '.' || !digit(b[p + 1])
                || b[p + 2] != 'm' || b[p + 3] != 's'
                || b[p + 4] != ' ' || b[p + 5] != '"'
                || b[end - 1] != '"') {
            return false;
        }

        for (int q = p + 6; q < end - 1; q++) {
            if (b[q] == '"') {
                return false;
            }
        }

        int fraction = b[p + 1] - '0';
        if (!overflow) {
            if (latency > DIV10
                    || (latency == DIV10 && fraction > LAST_DIGIT)) {
                overflow = true;
            } else {
                latency = latency * 10 + fraction;
            }
        }

        Entry entry = templateEntry(b, pathStart, pathEnd);
        if (overflow) {
            BigInteger value = new BigInteger(new String(
                    b, latencyStart, latencyEnd - latencyStart,
                    StandardCharsets.US_ASCII));
            entry.add(value.multiply(BigInteger.TEN)
                    .add(BigInteger.valueOf(fraction)));
        } else {
            entry.add(latency);
        }
        statuses[statusClass]++;
        return true;
    }

    private void ensureTemplateCapacity(int needed) {
        if (needed > templateBuffer.length) {
            int capacity = (int) Math.min(
                    Integer.MAX_VALUE - 8L,
                    Math.max((long) needed, (long) templateBuffer.length * 2));
            templateBuffer = Arrays.copyOf(templateBuffer, capacity);
        }
    }

    private Entry templateEntry(byte[] source, int start, int end) {
        int length = 0;
        int p = start;

        while (p < end) {
            if (source[p] == '/') {
                ensureTemplateCapacity(length + 1);
                templateBuffer[length++] = '/';
                p++;
            } else {
                int segmentStart = p;
                boolean numeric = true;
                while (p < end && source[p] != '/') {
                    if (!digit(source[p])) {
                        numeric = false;
                    }
                    p++;
                }

                if (numeric) {
                    ensureTemplateCapacity(length + 4);
                    templateBuffer[length++] = '{';
                    templateBuffer[length++] = 'i';
                    templateBuffer[length++] = 'd';
                    templateBuffer[length++] = '}';
                } else {
                    int segmentLength = p - segmentStart;
                    ensureTemplateCapacity(length + segmentLength);
                    System.arraycopy(source, segmentStart,
                            templateBuffer, length, segmentLength);
                    length += segmentLength;
                }
            }
        }

        int hash = 0x811c9dc5;
        for (int i = 0; i < length; i++) {
            hash = (hash ^ templateBuffer[i]) * 0x01000193;
        }
        hash ^= hash >>> 16;
        hash *= 0x85ebca6b;
        hash ^= hash >>> 13;
        hash *= 0xc2b2ae35;
        hash ^= hash >>> 16;

        int mask = table.length - 1;
        int slot = hash & mask;
        Entry entry;

        while ((entry = table[slot]) != null) {
            if (entry.hash == hash && entry.key.length == length
                    && Arrays.equals(entry.key, 0, length,
                            templateBuffer, 0, length)) {
                return entry;
            }
            slot = (slot + 1) & mask;
        }

        if (entryCount >= resizeAt) {
            growTable();
            mask = table.length - 1;
            slot = hash & mask;
            while (table[slot] != null) {
                slot = (slot + 1) & mask;
            }
        }

        entry = new Entry(Arrays.copyOf(templateBuffer, length), hash);
        table[slot] = entry;
        entryCount++;
        return entry;
    }

    private void growTable() {
        Entry[] old = table;
        Entry[] next = new Entry[old.length << 1];
        int mask = next.length - 1;
        for (Entry entry : old) {
            if (entry != null) {
                int slot = entry.hash & mask;
                while (next[slot] != null) {
                    slot = (slot + 1) & mask;
                }
                next[slot] = entry;
            }
        }
        table = next;
        resizeAt = next.length - (next.length >>> 2);
    }

    private void scan(String path) throws IOException {
        try (FileInputStream input = new FileInputStream(path)) {
            byte[] buffer = new byte[1 << 20];
            int used = 0;

            while (true) {
                if (used == buffer.length) {
                    int capacity = (int) Math.min(
                            Integer.MAX_VALUE - 8L, (long) buffer.length * 2);
                    buffer = Arrays.copyOf(buffer, capacity);
                }

                int read = input.read(buffer, used, buffer.length - used);
                if (read < 0) {
                    break;
                }

                int end = used + read;
                int lineStart = 0;
                for (int i = used; i < end; i++) {
                    if (buffer[i] == '\n') {
                        lines++;
                        if (!process(buffer, lineStart, i)) {
                            malformed++;
                        }
                        lineStart = i + 1;
                    }
                }

                used = end - lineStart;
                if (used > 0 && lineStart > 0) {
                    System.arraycopy(buffer, lineStart, buffer, 0, used);
                }
            }
        }
    }

    private static boolean better(Entry a, Entry b) {
        if (a.count != b.count) {
            return a.count > b.count;
        }
        int length = Math.min(a.key.length, b.key.length);
        for (int i = 0; i < length; i++) {
            if (a.key[i] != b.key[i]) {
                return a.key[i] < b.key[i];
            }
        }
        return a.key.length < b.key.length;
    }

    private static void appendLatency(StringBuilder out, long value) {
        out.append(value / 10).append('.').append(value % 10);
    }

    private static void appendLatency(StringBuilder out, BigInteger value) {
        String digits = value.toString();
        int length = digits.length();
        if (length == 1) {
            out.append("0.").append(digits);
        } else {
            out.append(digits, 0, length - 1)
                    .append('.').append(digits.charAt(length - 1));
        }
    }

    private static void appendRank(StringBuilder out, Entry entry, long rank) {
        if (rank <= entry.size) {
            appendLatency(out, entry.values[(int) (rank - 1)]);
        } else {
            appendLatency(out, entry.large.get((int) (rank - entry.size - 1)));
        }
    }

    private void output() {
        StringBuilder out = new StringBuilder(2048);
        out.append("lines ").append(lines).append('\n');
        out.append("malformed ").append(malformed).append('\n');

        for (int i = 0; i < statuses.length; i++) {
            if (statuses[i] != 0) {
                out.append("status ").append(i).append("xx ")
                        .append(statuses[i]).append('\n');
            }
        }

        Entry[] top = new Entry[10];
        int topSize = 0;
        for (Entry entry : table) {
            if (entry == null) {
                continue;
            }

            int position = 0;
            while (position < topSize && !better(entry, top[position])) {
                position++;
            }
            if (position == 10) {
                continue;
            }

            for (int j = Math.min(topSize, 9); j > position; j--) {
                top[j] = top[j - 1];
            }
            top[position] = entry;
            if (topSize < 10) {
                topSize++;
            }
        }

        for (int i = 0; i < topSize; i++) {
            Entry entry = top[i];
            entry.sort();

            out.append("path ")
                    .append(new String(entry.key, StandardCharsets.US_ASCII))
                    .append(' ').append(entry.count).append(' ');

            appendRank(out, entry, entry.count / 2 + entry.count % 2);
            out.append(' ');
            appendRank(out, entry, entry.count - entry.count / 20);
            out.append(' ');
            appendRank(out, entry, entry.count);
            out.append('\n');
        }

        System.out.print(out);
    }

    public static void main(String[] args) throws Exception {
        Main program = new Main();
        program.scan(args[0]);
        program.output();
    }
}
