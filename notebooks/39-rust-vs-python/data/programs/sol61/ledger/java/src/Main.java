import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

public final class Main {
    // Selective UTF-8 parser. Ignored values need neither decoding nor objects.
    static final class Json {
        byte[] b;
        int p;
        void reset(byte[] b, int start) { this.b = b; p = start; }
        void ws() { while (b[p] <= 32) ++p; }
        void take() { ws(); ++p; }
        boolean more(int end) {
            ws();
            if (b[p] == ',') { ++p; ws(); }
            if (b[p] == end) { ++p; return false; }
            return true;
        }
        static int hex(char c) { return c <= '9' ? c - '0' : (c | 32) - 'a' + 10; }
        String str() {
            ws(); int start = ++p;
            while (b[p] != '"' && b[p] != '\\') ++p;
            if (b[p] == '"') return new String(b, start, p++ - start, StandardCharsets.UTF_8);
            while (b[p] != '"') { if (b[p] == '\\') ++p; ++p; }
            String raw = new String(b, start, p++ - start, StandardCharsets.UTF_8);
            StringBuilder out = new StringBuilder(raw.length());
            for (int i = 0; i < raw.length(); ++i) {
                char c = raw.charAt(i);
                if (c != '\\') { out.append(c); continue; }
                switch (c = raw.charAt(++i)) {
                    case 'b': out.append('\b'); break;
                    case 'f': out.append('\f'); break;
                    case 'n': out.append('\n'); break;
                    case 'r': out.append('\r'); break;
                    case 't': out.append('\t'); break;
                    case 'u':
                        int cp = 0;
                        for (int k = 0; k < 4; ++k) cp = cp * 16 + hex(raw.charAt(++i));
                        out.append((char)cp); break;
                    default: out.append(c);
                }
            }
            return out.toString();
        }
        void text(Slice out) {
            ws(); int start = ++p;
            while (b[p] != '"' && b[p] != '\\') ++p;
            if (b[p] == '"') { out.b = b; out.start = start; out.end = p++; return; }
            p = start - 1;
            out.b = utf8(str());
            out.start = 0; out.end = out.b.length;
        }
        static byte[] utf8(String s) {
            // Preserve lone escaped surrogates as distinct keys as well.
            byte[] out = new byte[Math.multiplyExact(s.length(), 3)];
            int n = 0;
            for (int i = 0; i < s.length();) {
                int cp = s.codePointAt(i); i += Character.charCount(cp);
                if (cp < 0x80) out[n++] = (byte)cp;
                else if (cp < 0x800) {
                    out[n++] = (byte)(0xc0 | (cp >> 6)); out[n++] = (byte)(0x80 | (cp & 63));
                } else if (cp < 0x10000) {
                    out[n++] = (byte)(0xe0 | (cp >> 12)); out[n++] = (byte)(0x80 | ((cp >> 6) & 63));
                    out[n++] = (byte)(0x80 | (cp & 63));
                } else {
                    out[n++] = (byte)(0xf0 | (cp >> 18)); out[n++] = (byte)(0x80 | ((cp >> 12) & 63));
                    out[n++] = (byte)(0x80 | ((cp >> 6) & 63)); out[n++] = (byte)(0x80 | (cp & 63));
                }
            }
            return Arrays.copyOf(out, n);
        }
        boolean eq(int start, int length, String s) {
            if (length != s.length()) return false;
            for (int i = 0; i < length; ++i) if (b[start + i] != s.charAt(i)) return false;
            return true;
        }
        static int field(String key) {
            return switch (key) {
                case "account" -> 1; case "type" -> 2; case "amount" -> 3;
                case "currency" -> 4; case "tags" -> 5; case "meta" -> 6;
                case "channel" -> 7; case "rates" -> 8; default -> 0;
            };
        }
        int field() {
            ws(); int start = ++p;
            while (b[p] != '"' && b[p] != '\\') ++p;
            if (b[p] == '\\') { p = start - 1; return field(str()); }
            int n = p++ - start;
            return switch (n) {
                case 4 -> eq(start, n, "type") ? 2 : eq(start, n, "tags") ? 5 : eq(start, n, "meta") ? 6 : 0;
                case 5 -> eq(start, n, "rates") ? 8 : 0;
                case 6 -> eq(start, n, "amount") ? 3 : 0;
                case 7 -> eq(start, n, "account") ? 1 : eq(start, n, "channel") ? 7 : 0;
                case 8 -> eq(start, n, "currency") ? 4 : 0;
                default -> 0;
            };
        }
        int label() {
            ws(); int start = ++p;
            while (b[p] != '"' && b[p] != '\\') ++p;
            if (b[p] == '\\') {
                p = start - 1;
                return switch (str()) { case "void" -> 1; case "debit" -> 2; case "test" -> 3; default -> 0; };
            }
            int n = p++ - start;
            return eq(start, n, "void") ? 1 : eq(start, n, "debit") ? 2 : eq(start, n, "test") ? 3 : 0;
        }
        void skipString() {
            ++p;
            while (b[p] != '"') { if (b[p] == '\\') ++p; ++p; }
            ++p;
        }
        void skip() {
            ws();
            if (b[p] == '"') { skipString(); return; }
            if (b[p] == '{' || b[p] == '[') {
                int depth = 1; ++p;
                while (depth != 0) {
                    byte c = b[p];
                    if (c == '"') { skipString(); continue; }
                    ++p;
                    if (c == '{' || c == '[') ++depth;
                    else if (c == '}' || c == ']') --depth;
                }
            } else while (b[p] > 32 && b[p] != ',' && b[p] != '}' && b[p] != ']') ++p;
        }
        long integer() {
            ws(); boolean negative = b[p] == '-';
            if (negative) ++p;
            int start = p, digits = 0, fraction = 0;
            boolean dot = false;
            while (b[p] >= '0' && b[p] <= '9' || b[p] == '.') {
                if (b[p] == '.') dot = true;
                else { ++digits; if (dot) ++fraction; }
                ++p;
            }
            int end = p;
            long exponent = 0, cap = 1L << 60;
            if (b[p] == 'e' || b[p] == 'E') {
                ++p; boolean eneg = b[p] == '-';
                if (b[p] == '+' || b[p] == '-') ++p;
                while (b[p] >= '0' && b[p] <= '9') {
                    exponent = exponent > cap / 10 ? cap : Math.min(cap, exponent * 10 + b[p] - '0'); ++p;
                }
                if (eneg) exponent = -exponent;
            }
            long scale = exponent - fraction, keep = digits + Math.min(scale, 0);
            long n = 0;
            for (int i = start; i < end && keep > 0; ++i) if (b[i] != '.') {
                n = n * 10 + b[i] - '0'; --keep;
            }
            if (scale >= 64) n = 0;
            else for (long i = 0; i < scale; ++i) n *= 10;
            return negative ? -n : n;
        }
        long amount() {
            ws(); int start = ++p;
            while (b[p] != '"' && b[p] != '\\') ++p;
            if (b[p] == '\\') {
                p = start - 1; return hundredths(str());
            }
            int end = p++, i = start;
            long n = 0;
            while (i < end && b[i] != '.') n = n * 10 + b[i++] - '0';
            n *= 100;
            if (i < end) { ++i; n += (b[i++] - '0') * 10; if (i < end) n += b[i] - '0'; }
            return n;
        }
    }
    static final class Slice { byte[] b; int start, end; }
    // Open addressing keeps values unboxed and lets lookups use input bytes.
    static final class Totals {
        byte[][] keys = new byte[16][];
        int[] hashes = new int[16];
        long[] counts = new long[16], nets = new long[16];
        int size;
        static int hash(Slice s) {
            int h = 0x811c9dc5;
            for (int i = s.start; i < s.end; ++i) h = (h ^ (s.b[i] & 255)) * 0x01000193;
            return h;
        }
        void grow() {
            int n = Math.multiplyExact(keys.length, 2), mask = n - 1;
            byte[][] newKeys = new byte[n][];
            int[] newHashes = new int[n];
            long[] newCounts = new long[n], newNets = new long[n];
            for (int i = 0; i < keys.length; ++i) {
                if (keys[i] == null) continue;
                int slot = hashes[i] & mask;
                while (newKeys[slot] != null) slot = (slot + 1) & mask;
                newKeys[slot] = keys[i]; newHashes[slot] = hashes[i];
                newCounts[slot] = counts[i]; newNets[slot] = nets[i];
            }
            keys = newKeys; hashes = newHashes; counts = newCounts; nets = newNets;
        }
        int find(Slice s, boolean insert) {
            if (insert && size >= keys.length * 3 / 4) grow();
            int h = hash(s), mask = keys.length - 1, slot = h & mask;
            for (;;) {
                byte[] key = keys[slot];
                if (key == null) {
                    if (!insert) throw new IllegalArgumentException("Unknown currency");
                    keys[slot] = Arrays.copyOfRange(s.b, s.start, s.end);
                    hashes[slot] = h; ++size;
                    return slot;
                }
                if (hashes[slot] == h && Arrays.equals(s.b, s.start, s.end, key, 0, key.length)) return slot;
                slot = (slot + 1) & mask;
            }
        }
        void set(Slice s, long value) { int i = find(s, true); nets[i] = value; }
        long get(Slice s) { return nets[find(s, false)]; }
        void add(Slice s, long value) { int i = find(s, true); ++counts[i]; nets[i] += value; }
    }
    final Totals rates = new Totals(), accounts = new Totals(), channels = new Totals();
    final Slice account = new Slice(), currency = new Slice(), channel = new Slice(), value = new Slice();
    final Json j = new Json();
    long count, net;
    static long hundredths(String s) {
        long n = 0; int i = 0;
        while (i < s.length() && s.charAt(i) != '.') n = n * 10 + s.charAt(i++) - '0';
        n *= 100;
        if (i < s.length()) { ++i; n += (s.charAt(i++) - '0') * 10; if (i < s.length()) n += s.charAt(i) - '0'; }
        return n;
    }
    void header(byte[] b, int start) {
        j.reset(b, start); j.take();
        while (j.more('}')) {
            int key = j.field(); j.take();
            if (key != 8) { j.skip(); continue; }
            j.take();
            while (j.more('}')) { j.text(value); j.take(); rates.set(value, j.integer()); }
        }
    }
    void transaction(byte[] b, int start) {
        j.reset(b, start); j.take();
        long amount = 0;
        boolean debit = false;
        while (j.more('}')) {
            int field = j.field(); j.take();
            switch (field) {
                case 1: j.text(account); break;
                case 2:
                    int type = j.label();
                    if (type == 1) return;
                    debit = type == 2; break;
                case 3: amount = j.amount(); break;
                case 4: j.text(currency); break;
                case 5:
                    j.take(); while (j.more(']')) if (j.label() == 3) return;
                    break;
                case 6:
                    j.take();
                    while (j.more('}')) {
                        int key = j.field(); j.take();
                        if (key == 7) j.text(channel); else j.skip();
                    }
                    break;
                default: j.skip();
            }
        }
        long value = Math.floorDiv(amount * rates.get(currency), 1_000_000L);
        if (debit) value = -value;
        ++count; net += value;
        accounts.add(account, value);
        channels.add(channel, value);
    }
    boolean better(int a, int b) {
        long x = accounts.nets[a], y = accounts.nets[b];
        return x != y ? x > y : Arrays.compareUnsigned(accounts.keys[a], accounts.keys[b]) < 0;
    }
    void output() {
        StringBuilder out = new StringBuilder();
        out.append("counted ").append(count).append("\nnet ").append(net).append('\n');
        ArrayList<Integer> names = new ArrayList<>(channels.size);
        for (int i = 0; i < channels.keys.length; ++i) if (channels.keys[i] != null) names.add(i);
        names.sort((a, b) -> Arrays.compareUnsigned(channels.keys[a], channels.keys[b]));
        for (int i : names)
            out.append("channel ").append(new String(channels.keys[i], StandardCharsets.UTF_8))
                .append(' ').append(channels.counts[i]).append(' ').append(channels.nets[i]).append('\n');
        int[] top = new int[10];
        int length = 0;
        for (int a = 0; a < accounts.keys.length; ++a) {
            if (accounts.keys[a] == null) continue;
            int pos = 0;
            while (pos < length && !better(a, top[pos])) ++pos;
            if (pos == 10) continue;
            for (int i = Math.min(length, 9); i > pos; --i) top[i] = top[i - 1];
            top[pos] = a;
            if (length < 10) ++length;
        }
        for (int k = 0; k < length; ++k) {
            int a = top[k];
            out.append("account ").append(new String(accounts.keys[a], StandardCharsets.UTF_8))
                .append(' ').append(accounts.nets[a]).append('\n');
        }
        System.out.print(out);
    }
    public static void main(String[] args) throws Exception {
        if (args.length == 0) System.exit(1);
        Main ledger = new Main();
        byte[] buffer = new byte[1 << 20];
        int used = 0;
        boolean first = true;
        try (InputStream in = new FileInputStream(args[0])) {
            for (;;) {
                if (used == buffer.length) buffer = Arrays.copyOf(buffer, Math.multiplyExact(buffer.length, 2));
                int n = in.read(buffer, used, buffer.length - used);
                if (n < 0) break;
                int end = used + n, start = 0;
                for (int i = 0; i < end; ++i) if (buffer[i] == '\n') {
                    if (first) { ledger.header(buffer, start); first = false; }
                    else ledger.transaction(buffer, start);
                    start = i + 1;
                }
                used = end - start;
                System.arraycopy(buffer, start, buffer, 0, used);
            }
            if (used != 0) {
                if (first) ledger.header(buffer, 0); else ledger.transaction(buffer, 0);
            }
        }
        ledger.output();
    }
}
