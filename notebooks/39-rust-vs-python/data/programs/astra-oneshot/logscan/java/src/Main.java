import java.io.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;

public class Main {
    private static final int[] TIMESTAMP_DIGITS = {
        0, 1, 2, 3, 5, 6, 8, 9, 11, 12, 14, 15, 17, 18, 20, 21, 22
    };
    private static final boolean[] PATH_CHAR = new boolean[256];
    private static final long LONG_DIV_10 = Long.MAX_VALUE / 10;

    static {
        for (int c = 'a'; c <= 'z'; c++) PATH_CHAR[c] = true;
        for (int c = 'A'; c <= 'Z'; c++) PATH_CHAR[c] = true;
        for (int c = '0'; c <= '9'; c++) PATH_CHAR[c] = true;
        PATH_CHAR['_'] = PATH_CHAR['/'] = PATH_CHAR['-'] = true;
    }

    private long lines;
    private long malformed;
    private final long[] statuses = new long[10];
    private Group[] table = new Group[4096];
    private int groupCount;
    private byte[] template = new byte[256];

    private static boolean digit(byte c) {
        return c >= '0' && c <= '9';
    }

    private static boolean lower(byte c) {
        return c >= 'a' && c <= 'z';
    }

    private static boolean method(byte[] b, int p, int length) {
        return switch (length) {
            case 3 -> b[p] == 'G' && b[p + 1] == 'E' && b[p + 2] == 'T'
                   || b[p] == 'P' && b[p + 1] == 'U' && b[p + 2] == 'T';
            case 4 -> b[p] == 'P' && b[p + 1] == 'O'
                   && b[p + 2] == 'S' && b[p + 3] == 'T';
            case 5 -> b[p] == 'P' && b[p + 1] == 'A'
                   && b[p + 2] == 'T' && b[p + 3] == 'C' && b[p + 4] == 'H';
            case 6 -> b[p] == 'D' && b[p + 1] == 'E'
                   && b[p + 2] == 'L' && b[p + 3] == 'E'
                   && b[p + 4] == 'T' && b[p + 5] == 'E';
            default -> false;
        };
    }

    private boolean accept(byte[] b, int s, int e) {
        if (e - s < 25) return false;
        if (b[s + 4] != '-' || b[s + 7] != '-' || b[s + 10] != 'T'
                || b[s + 13] != ':' || b[s + 16] != ':'
                || b[s + 19] != '.' || b[s + 23] != 'Z'
                || b[s + 24] != ' ') return false;

        for (int offset : TIMESTAMP_DIGITS) {
            if (!digit(b[s + offset])) return false;
        }

        int i = s + 25;
        if (i == e || !lower(b[i])) return false;
        do {
            i++;
        } while (i < e && lower(b[i]));
        if (i == e || b[i++] != '-') return false;
        if (i == e || !digit(b[i])) return false;
        do {
            i++;
        } while (i < e && digit(b[i]));
        if (i == e || b[i++] != ' ') return false;

        int methodStart = i;
        while (i < e && b[i] != ' ') i++;
        if (i == e || !method(b, methodStart, i - methodStart)) return false;
        i++;

        if (i == e || b[i] != '/') return false;
        int pathStart = i;
        while (i < e && PATH_CHAR[b[i] & 255]) i++;
        int pathEnd = i;

        if (i < e && b[i] == '?') {
            do {
                i++;
            } while (i < e && b[i] != ' ');
        }
        if (i == e || b[i++] != ' ') return false;

        if (e - i < 4 || !digit(b[i]) || !digit(b[i + 1])
                || !digit(b[i + 2]) || b[i + 3] != ' ') return false;
        int status = b[i] - '0';
        i += 4;

        if (i == e || !digit(b[i])) return false;
        do {
            i++;
        } while (i < e && digit(b[i]));
        if (e - i < 2 || b[i] != 'B' || b[i + 1] != ' ') return false;
        i += 2;

        int latencyStart = i;
        if (i == e || !digit(b[i])) return false;
        do {
            i++;
        } while (i < e && digit(b[i]));
        int dot = i;

        if (e - i < 7 || b[i] != '.' || !digit(b[i + 1])
                || b[i + 2] != 'm' || b[i + 3] != 's'
                || b[i + 4] != ' ' || b[i + 5] != '"') return false;
        int fraction = b[i + 1] - '0';
        i += 6;
        while (i < e && b[i] != '"') i++;
        if (i != e - 1) return false;

        long latency = 0;
        boolean overflow = false;
        for (int j = latencyStart; j < dot; j++) {
            int d = b[j] - '0';
            if (latency > LONG_DIV_10 || latency == LONG_DIV_10 && d > 7) {
                overflow = true;
                break;
            }
            latency = latency * 10 + d;
        }
        if (!overflow) {
            if (latency > LONG_DIV_10
                    || latency == LONG_DIV_10 && fraction > 7) {
                overflow = true;
            } else {
                latency = latency * 10 + fraction;
            }
        }

        Group group = findGroup(b, pathStart, pathEnd);
        if (overflow) {
            BigInteger value = new BigInteger(new String(
                    b, latencyStart, dot - latencyStart, StandardCharsets.US_ASCII));
            group.addBig(value.multiply(BigInteger.TEN)
                    .add(BigInteger.valueOf(fraction)));
        } else {
            group.add(latency);
        }
        statuses[status]++;
        return true;
    }

    private void ensureTemplate(int needed) {
        if (needed > template.length) {
            int capacity = (int) Math.min(Integer.MAX_VALUE - 8L,
                    Math.max((long) needed, template.length * 2L));
            template = Arrays.copyOf(template, capacity);
        }
    }

    private Group findGroup(byte[] b, int start, int end) {
        int length = 0;
        int i = start;
        while (i < end) {
            ensureTemplate(length + 1);
            template[length++] = '/';
            i++;

            int segmentStart = i;
            boolean numeric = true;
            while (i < end && b[i] != '/') {
                if (!digit(b[i])) numeric = false;
                i++;
            }
            int segmentLength = i - segmentStart;
            if (segmentLength != 0 && numeric) {
                ensureTemplate(length + 4);
                template[length++] = '{';
                template[length++] = 'i';
                template[length++] = 'd';
                template[length++] = '}';
            } else {
                ensureTemplate(length + segmentLength);
                System.arraycopy(b, segmentStart, template, length, segmentLength);
                length += segmentLength;
            }
        }

        int hash = 0x811c9dc5;
        for (int j = 0; j < length; j++) {
            hash = (hash ^ template[j]) * 0x01000193;
        }
        hash ^= hash >>> 16;

        int mask = table.length - 1;
        int slot = hash & mask;
        while (true) {
            Group group = table[slot];
            if (group == null) {
                group = new Group(Arrays.copyOf(template, length), hash);
                table[slot] = group;
                groupCount++;
                if (groupCount > table.length - (table.length >>> 2)) growTable();
                return group;
            }
            if (group.hash == hash && group.key.length == length
                    && Arrays.equals(group.key, 0, length, template, 0, length)) {
                return group;
            }
            slot = (slot + 1) & mask;
        }
    }

    private void growTable() {
        Group[] expanded = new Group[table.length << 1];
        int mask = expanded.length - 1;
        for (Group group : table) {
            if (group == null) continue;
            int slot = group.hash & mask;
            while (expanded[slot] != null) slot = (slot + 1) & mask;
            expanded[slot] = group;
        }
        table = expanded;
    }

    private void read(Path path) throws IOException {
        byte[] buffer = new byte[1 << 20];
        int used = 0;

        try (InputStream input = Files.newInputStream(path)) {
            while (true) {
                if (used == buffer.length) {
                    buffer = Arrays.copyOf(buffer, Math.toIntExact(
                            Math.min(Integer.MAX_VALUE - 8L, buffer.length * 2L)));
                    if (used == buffer.length) throw new IOException("Line too long");
                }

                int n = input.read(buffer, used, buffer.length - used);
                if (n < 0) break;
                if (n == 0) continue;

                int limit = used + n;
                int start = 0;
                for (int i = used; i < limit; i++) {
                    if (buffer[i] == '\n') {
                        lines++;
                        if (!accept(buffer, start, i)) malformed++;
                        start = i + 1;
                    }
                }
                used = limit - start;
                if (start != 0 && used != 0) {
                    System.arraycopy(buffer, start, buffer, 0, used);
                }
            }
        }
    }

    private static int compareGroups(Group a, Group b) {
        int comparison = Long.compare(b.count, a.count);
        if (comparison != 0) return comparison;
        return Arrays.compareUnsigned(a.key, b.key);
    }

    private void write() throws IOException {
        Group[] top = new Group[10];
        int topSize = 0;
        for (Group group : table) {
            if (group == null) continue;
            if (topSize == 10 && compareGroups(group, top[9]) >= 0) continue;

            int position = 0;
            while (position < topSize
                    && compareGroups(top[position], group) <= 0) position++;
            if (position < 10) {
                for (int j = Math.min(topSize, 9); j > position; j--) {
                    top[j] = top[j - 1];
                }
                top[position] = group;
                if (topSize < 10) topSize++;
            }
        }

        StringBuilder output = new StringBuilder(2048);
        output.append("lines ").append(lines).append('\n');
        output.append("malformed ").append(malformed).append('\n');
        for (int c = 0; c < 10; c++) {
            if (statuses[c] != 0) {
                output.append("status ").append(c).append("xx ")
                        .append(statuses[c]).append('\n');
            }
        }

        for (int i = 0; i < topSize; i++) {
            Group group = top[i];
            group.sort();
            output.append("path ")
                    .append(new String(group.key, StandardCharsets.US_ASCII))
                    .append(' ').append(group.count).append(' ');
            group.appendRank(output, group.count - group.count / 2);
            output.append(' ');
            group.appendRank(output, group.count - group.count / 20);
            output.append(' ');
            group.appendRank(output, group.count);
            output.append('\n');
        }

        BufferedWriter writer = new BufferedWriter(
                new OutputStreamWriter(System.out, StandardCharsets.US_ASCII));
        writer.write(output.toString());
        writer.flush();
    }

    private static final class Group {
        final byte[] key;
        final int hash;
        long count;
        long first;
        long[] values;
        int size;
        ArrayList<BigInteger> bigValues;

        Group(byte[] key, int hash) {
            this.key = key;
            this.hash = hash;
        }

        void add(long value) {
            if (size == 0) {
                first = value;
            } else {
                if (values == null) {
                    values = new long[4];
                    values[0] = first;
                } else if (size == values.length) {
                    int capacity = Math.toIntExact(Math.min(Integer.MAX_VALUE - 8L,
                            values.length + Math.max(1L, values.length / 2L)));
                    values = Arrays.copyOf(values, capacity);
                }
                values[size] = value;
            }
            size++;
            count++;
        }

        void addBig(BigInteger value) {
            if (bigValues == null) bigValues = new ArrayList<>();
            bigValues.add(value);
            count++;
        }

        void sort() {
            if (size > 1) Arrays.sort(values, 0, size);
            if (bigValues != null) bigValues.sort(null);
        }

        void appendRank(StringBuilder output, long rank) {
            if (rank <= size) {
                long value = size == 1 ? first : values[(int) (rank - 1)];
                output.append(value / 10).append('.').append(value % 10);
            } else {
                String value = bigValues.get((int) (rank - size - 1)).toString();
                int last = value.length() - 1;
                output.append(value, 0, last).append('.').append(value.charAt(last));
            }
        }
    }

    public static void main(String[] args) throws IOException {
        Main scanner = new Main();
        scanner.read(Path.of(args[0]));
        scanner.write();
    }
}
