import java.io.FileInputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;

public final class Main {
    private static final byte[] STAMP = "0000-00-00T00:00:00.000Z ".getBytes(StandardCharsets.US_ASCII);
    private static final boolean[] PATH = new boolean[256];
    static {
        for (int c = 0; c < 256; c++)
            PATH[c] = digit(c) || c >= 'A' && c <= 'Z' || c >= 'a' && c <= 'z' || c == '_' || c == '/' || c == '-';
    }
    private static boolean digit(int c) { return c >= '0' && c <= '9'; }

    // The reusable lookup key avoids creating a String or boxing a latency per request.
    private static final class Group {
        byte[] key;
        int length, hash, size;
        long[] values;
        ArrayList<String> large;
        Group(byte[] key) { this.key = key; }
        Group(Group probe) {
            key = Arrays.copyOf(probe.key, probe.length);
            length = probe.length;
            hash = probe.hash;
        }
        @Override public int hashCode() { return hash; }
        @Override public boolean equals(Object other) {
            if (!(other instanceof Group g) || hash != g.hash || length != g.length) return false;
            return Arrays.equals(key, 0, length, g.key, 0, length);
        }
        void add(long value) {
            if (values == null) values = new long[4];
            else if (size == values.length) values = Arrays.copyOf(values, size * 2);
            values[size++] = value;
        }
        long count() { return (long) size + (large == null ? 0 : large.size()); }
    }

    private final HashMap<Group, Group> groups = new HashMap<>();
    private final Group probe = new Group(new byte[256]);
    private final long[] statuses = new long[10];
    private long lines, malformed;

    private static boolean method(byte[] b, int start, int length, String name) {
        if (length != name.length()) return false;
        for (int j = 0; j < length; j++) if (b[start+j] != name.charAt(j)) return false;
        return true;
    }

    private boolean parse(byte[] b, int from, int end) {
        if (end - from < 50) return false;
        for (int j = 0; j < STAMP.length; j++)
            if (STAMP[j] == '0' ? !digit(b[from+j]) : b[from+j] != STAMP[j]) return false;
        int i = from + 25, start = i;
        while (i < end && b[i] >= 'a' && b[i] <= 'z') i++;
        if (i == start || i == end || b[i++] != '-') return false;
        start = i;
        while (i < end && digit(b[i])) i++;
        if (i == start || i == end || b[i++] != ' ') return false;
        start = i;
        while (i < end && b[i] != ' ') i++;
        int length = i - start;
        if (i == end || !(method(b,start,length,"GET") || method(b,start,length,"POST") ||
            method(b,start,length,"PUT") || method(b,start,length,"DELETE") || method(b,start,length,"PATCH"))) return false;
        i++;
        if (i == end || b[i] != '/') return false;
        int pathStart = i;
        while (i < end && PATH[b[i] & 255]) i++;
        int pathEnd = i;
        if (i < end && b[i] == '?') while (i < end && b[i] != ' ') i++;
        if (i == end || b[i++] != ' ') return false;
        if (end - i < 4 || !digit(b[i]) || !digit(b[i+1]) || !digit(b[i+2]) || b[i+3] != ' ') return false;
        int status = b[i] - '0';
        i += 4;
        start = i;
        while (i < end && digit(b[i])) i++;
        if (i == start || end - i < 2 || b[i] != 'B' || b[i+1] != ' ') return false;
        i += 2;
        start = i;
        while (i < end && b[i] == '0') i++;
        int significant = i;
        while (i < end && digit(b[i])) i++;
        int decimal = i;
        if (i == start || end - i < 7 || b[i] != '.' || !digit(b[i+1]) || b[i+2] != 'm' ||
            b[i+3] != 's' || b[i+4] != ' ' || b[i+5] != '"' || b[end-1] != '"') return false;
        for (int j = i+6; j < end-1; j++) if (b[j] == '"') return false;

        int needed = (pathEnd - pathStart) * 3;
        if (probe.key.length < needed) probe.key = new byte[Math.max(needed, probe.key.length * 2)];
        byte[] key = probe.key;
        int p = pathStart, used = 0;
        while (p < pathEnd) {
            key[used++] = '/';
            start = ++p;
            boolean numeric = true;
            while (p < pathEnd && b[p] != '/') { numeric &= digit(b[p]); p++; }
            if (p != start && numeric) {
                key[used++] = '{'; key[used++] = 'i'; key[used++] = 'd'; key[used++] = '}';
            } else {
                System.arraycopy(b, start, key, used, p - start);
                used += p - start;
            }
        }
        int hash = 0;
        for (int j = 0; j < used; j++) hash = hash * 31 + key[j];
        probe.length = used;
        probe.hash = hash;
        Group g = groups.get(probe);
        if (g == null) { g = new Group(probe); groups.put(g, g); }
        if (decimal - significant <= 14) {
            long value = 0;
            for (int j = significant; j < decimal; j++) value = value * 10 + b[j] - '0';
            g.add(value * 10 + b[decimal+1] - '0');
        } else {
            if (g.large == null) g.large = new ArrayList<>();
            g.large.add(new String(b, significant, decimal-significant, StandardCharsets.US_ASCII) + (char) b[decimal+1]);
        }
        statuses[status]++;
        return true;
    }

    private void read(String path) throws IOException {
        byte[] buffer = new byte[1 << 20];
        int used = 0;
        try (FileInputStream input = new FileInputStream(path)) {
            for (;;) {
                int got = input.read(buffer, used, buffer.length - used);
                if (got < 0) break;
                int end = used + got, begin = 0;
                for (int i = 0; i < end; i++) {
                    if (buffer[i] != '\n') continue;
                    lines++;
                    if (!parse(buffer, begin, i)) malformed++;
                    begin = i+1;
                }
                used = end - begin;
                System.arraycopy(buffer, begin, buffer, 0, used);
                if (used == buffer.length) buffer = Arrays.copyOf(buffer, buffer.length * 2);
            }
        }
    }

    private static int compare(Group a, Group b) {
        int c = Long.compare(b.count(), a.count());
        return c != 0 ? c : Arrays.compareUnsigned(a.key, b.key);
    }
    private static String format(long value) { return value / 10 + "." + value % 10; }
    private static String at(Group g, int rank) {
        if (rank < g.size) return format(g.values[rank]);
        String s = g.large.get(rank - g.size);
        return s.substring(0, s.length()-1) + '.' + s.charAt(s.length()-1);
    }
    private void output() {
        StringBuilder out = new StringBuilder();
        out.append("lines ").append(lines).append("\nmalformed ").append(malformed).append('\n');
        for (int c = 0; c < 10; c++)
            if (statuses[c] != 0) out.append("status ").append(c).append("xx ").append(statuses[c]).append('\n');
        Group[] top = new Group[10];
        int size = 0;
        for (Group g : groups.values()) {
            int pos = size;
            while (pos > 0 && compare(g, top[pos-1]) < 0) pos--;
            if (pos >= 10) continue;
            for (int j = Math.min(size, 9); j > pos; j--) top[j] = top[j-1];
            top[pos] = g;
            if (size < 10) size++;
        }
        for (int j = 0; j < size; j++) {
            Group g = top[j];
            if (g.size > 1) Arrays.sort(g.values, 0, g.size);
            if (g.large != null) g.large.sort((a,b) -> a.length() != b.length() ? Integer.compare(a.length(), b.length()) : a.compareTo(b));
            int count = (int) g.count();
            out.append("path ").append(new String(g.key, StandardCharsets.US_ASCII)).append(' ').append(count).append(' ')
               .append(at(g, (count-1)/2)).append(' ').append(at(g, count-1-count/20)).append(' ')
               .append(at(g, count-1)).append('\n');
        }
        System.out.print(out);
    }
    public static void main(String[] args) throws IOException {
        if (args.length == 0) System.exit(1);
        Main scanner = new Main();
        scanner.read(args[0]);
        scanner.output();
    }
}
