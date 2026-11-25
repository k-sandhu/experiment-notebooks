import java.io.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;

public class Main {
    private static final BigInteger HUNDRED = BigInteger.valueOf(100);

    static final class Entry {
        final String key;
        final int hash;
        long value;
        long count;
        BigInteger big;

        Entry(String key, int hash) {
            this.key = key;
            this.hash = hash;
        }
    }

    static final class Table {
        Entry[] entries;
        int size;
        int threshold;

        Table(int capacity) {
            entries = new Entry[capacity];
            threshold = capacity * 2 / 3;
        }

        Entry find(char[] chars, int length, int hash, boolean create) {
            Entry[] a = entries;
            int mask = a.length - 1;
            int slot = (hash ^ (hash >>> 16)) & mask;

            for (;;) {
                Entry e = a[slot];
                if (e == null) {
                    if (!create) return null;
                    e = new Entry(new String(chars, 0, length), hash);
                    a[slot] = e;
                    if (++size >= threshold) grow();
                    return e;
                }
                if (e.hash == hash && same(e.key, chars, length)) return e;
                slot = (slot + 1) & mask;
            }
        }

        private static boolean same(String s, char[] chars, int length) {
            if (s.length() != length) return false;
            for (int i = 0; i < length; i++) {
                if (s.charAt(i) != chars[i]) return false;
            }
            return true;
        }

        private void grow() {
            Entry[] old = entries;
            Entry[] next = new Entry[old.length << 1];
            int mask = next.length - 1;
            for (Entry e : old) {
                if (e != null) {
                    int slot = (e.hash ^ (e.hash >>> 16)) & mask;
                    while (next[slot] != null) slot = (slot + 1) & mask;
                    next[slot] = e;
                }
            }
            entries = next;
            threshold = next.length * 2 / 3;
        }

        Entry[] toArray() {
            Entry[] result = new Entry[size];
            int n = 0;
            for (Entry e : entries) {
                if (e != null) result[n++] = e;
            }
            return result;
        }
    }

    static final class Lines implements Closeable {
        final InputStream input;
        byte[] data = new byte[1 << 20];
        int position;
        int limit;
        int start;
        boolean eof;

        Lines(String path) throws IOException {
            input = new FileInputStream(path);
        }

        boolean next() throws IOException {
            if (eof) return false;
            int beginning = position;
            int scan = position;

            for (;;) {
                while (scan < limit) {
                    if (data[scan++] == '\n') {
                        start = beginning;
                        position = scan;
                        return true;
                    }
                }

                int remaining = limit - beginning;
                if (beginning != 0 && remaining != 0) {
                    System.arraycopy(data, beginning, data, 0, remaining);
                }
                if (remaining == data.length) {
                    data = Arrays.copyOf(data, data.length << 1);
                }

                beginning = 0;
                scan = remaining;
                position = 0;
                limit = remaining;

                int n = input.read(data, remaining, data.length - remaining);
                if (n < 0) {
                    eof = true;
                    if (remaining == 0) return false;
                    start = 0;
                    position = limit;
                    return true;
                }
                limit += n;
            }
        }

        public void close() throws IOException {
            input.close();
        }
    }

    static final class Ledger {
        byte[] bytes;
        int p;
        char[] chars = new char[128];
        int length;
        int hash;

        final Table rates = new Table(16);
        final Table accounts = new Table(1024);
        final Table channels = new Table(16);

        long counted;
        long net;
        BigInteger amountBig;

        void whitespace() {
            byte[] b = bytes;
            int x = p;
            while ((b[x] & 255) <= 32) x++;
            p = x;
        }

        void skipString() {
            byte[] b = bytes;
            int x = p + 1;
            for (;;) {
                int c = b[x++];
                if (c == '"') {
                    p = x;
                    return;
                }
                if (c == '\\') x++;
            }
        }

        void skipValue() {
            byte[] b = bytes;
            int x = p;
            int c = b[x];

            if (c == '"') {
                skipString();
                return;
            }
            if (c == '{' || c == '[') {
                int depth = 1;
                x++;
                while (depth != 0) {
                    c = b[x++];
                    if (c == '"') {
                        for (;;) {
                            c = b[x++];
                            if (c == '"') break;
                            if (c == '\\') x++;
                        }
                    } else if (c == '{' || c == '[') {
                        depth++;
                    } else if (c == '}' || c == ']') {
                        depth--;
                    }
                }
            } else {
                while ((b[x] & 255) > 32
                        && b[x] != ',' && b[x] != '}' && b[x] != ']') {
                    x++;
                }
            }
            p = x;
        }

        static int hex(int c) {
            if (c <= '9') return c - '0';
            return (c | 32) - 'a' + 10;
        }

        void readString() {
            byte[] b = bytes;
            char[] out = chars;
            int x = p + 1;
            int n = 0;
            int h = 0;

            for (;;) {
                int c = b[x++] & 255;
                if (c == '"') break;

                if (c == '\\') {
                    c = b[x++] & 255;
                    switch (c) {
                        case 'b': c = '\b'; break;
                        case 'f': c = '\f'; break;
                        case 'n': c = '\n'; break;
                        case 'r': c = '\r'; break;
                        case 't': c = '\t'; break;
                        case 'u':
                            c = (hex(b[x] & 255) << 12)
                                    | (hex(b[x + 1] & 255) << 8)
                                    | (hex(b[x + 2] & 255) << 4)
                                    | hex(b[x + 3] & 255);
                            x += 4;
                            break;
                        default:
                            break;
                    }
                } else if (c >= 128) {
                    if (c < 224) {
                        c = ((c & 31) << 6) | (b[x++] & 63);
                    } else if (c < 240) {
                        c = ((c & 15) << 12)
                                | ((b[x++] & 63) << 6)
                                | (b[x++] & 63);
                    } else {
                        int codePoint = ((c & 7) << 18)
                                | ((b[x++] & 63) << 12)
                                | ((b[x++] & 63) << 6)
                                | (b[x++] & 63);
                        codePoint -= 0x10000;
                        if (n + 2 > out.length) {
                            out = Arrays.copyOf(out, out.length << 1);
                        }
                        char high = (char) (0xD800 | (codePoint >>> 10));
                        out[n++] = high;
                        h = 31 * h + high;
                        c = 0xDC00 | (codePoint & 1023);
                    }
                }

                if (n == out.length) {
                    out = Arrays.copyOf(out, out.length << 1);
                }
                out[n++] = (char) c;
                h = 31 * h + c;
            }

            chars = out;
            length = n;
            hash = h;
            p = x;
        }

        boolean textEquals(String s) {
            if (length != s.length()) return false;
            for (int i = 0; i < length; i++) {
                if (chars[i] != s.charAt(i)) return false;
            }
            return true;
        }

        boolean rawEquals(int start, int length, String s) {
            if (length != s.length()) return false;
            for (int i = 0; i < length; i++) {
                if (bytes[start + i] != s.charAt(i)) return false;
            }
            return true;
        }

        int field() {
            int opening = p;
            int start = opening + 1;
            int x = start;
            while (bytes[x] != '"' && bytes[x] != '\\') x++;

            if (bytes[x] == '\\') {
                readString();
                return switch (length) {
                    case 4 -> textEquals("type") ? 3
                            : textEquals("tags") ? 6
                            : textEquals("meta") ? 7 : 0;
                    case 5 -> textEquals("rates") ? 1 : 0;
                    case 6 -> textEquals("amount") ? 4 : 0;
                    case 7 -> textEquals("account") ? 2
                            : textEquals("channel") ? 8 : 0;
                    case 8 -> textEquals("currency") ? 5 : 0;
                    default -> 0;
                };
            }

            p = x + 1;
            int n = x - start;
            return switch (n) {
                case 4 -> rawEquals(start, n, "type") ? 3
                        : rawEquals(start, n, "tags") ? 6
                        : rawEquals(start, n, "meta") ? 7 : 0;
                case 5 -> rawEquals(start, n, "rates") ? 1 : 0;
                case 6 -> rawEquals(start, n, "amount") ? 4 : 0;
                case 7 -> rawEquals(start, n, "account") ? 2
                        : rawEquals(start, n, "channel") ? 8 : 0;
                case 8 -> rawEquals(start, n, "currency") ? 5 : 0;
                default -> 0;
            };
        }

        void header(byte[] data, int start) {
            bytes = data;
            p = start;
            if ((bytes[p] & 255) == 239
                    && (bytes[p + 1] & 255) == 187
                    && (bytes[p + 2] & 255) == 191) {
                p += 3;
            }
            whitespace();
            p++;
            whitespace();
            if (bytes[p] == '}') return;

            for (;;) {
                int f = field();
                whitespace();
                p++;
                whitespace();
                if (f == 1) readRates();
                else skipValue();
                whitespace();
                if (bytes[p++] == '}') return;
                whitespace();
            }
        }

        void readRates() {
            p++;
            whitespace();
            if (bytes[p] == '}') {
                p++;
                return;
            }

            for (;;) {
                readString();
                Entry rate = rates.find(chars, length, hash, true);
                whitespace();
                p++;
                whitespace();

                int start = p;
                if (bytes[p] == '-') p++;
                while (bytes[p] >= '0' && bytes[p] <= '9') p++;
                String number = new String(bytes, start, p - start,
                        StandardCharsets.US_ASCII);
                try {
                    rate.value = Long.parseLong(number);
                    rate.big = null;
                } catch (NumberFormatException ex) {
                    rate.big = new BigInteger(number);
                }

                whitespace();
                if (bytes[p++] == '}') return;
                whitespace();
            }
        }

        long readAmount() {
            readString();
            long value = 0;
            int decimal = -1;
            boolean overflow = false;

            for (int i = 0; i < length; i++) {
                int c = chars[i];
                if (c == '.') {
                    decimal = i;
                } else if (!overflow) {
                    int digit = c - '0';
                    if (value > 922337203685477580L
                            || (value == 922337203685477580L && digit > 7)) {
                        overflow = true;
                    } else {
                        value = value * 10 + digit;
                    }
                }
            }

            int factor = decimal < 0 ? 100
                    : length - decimal - 1 == 1 ? 10 : 1;
            amountBig = null;
            if (!overflow && value <= Long.MAX_VALUE / factor) {
                return value * factor;
            }

            String digits = new String(chars, 0, length).replace(".", "");
            amountBig = new BigInteger(digits);
            if (factor == 100) amountBig = amountBig.multiply(HUNDRED);
            else if (factor == 10) amountBig = amountBig.multiply(BigInteger.TEN);
            return 0;
        }

        void transaction(byte[] data, int start) {
            bytes = data;
            p = start;
            whitespace();
            p++;

            int accountPosition = 0;
            int currencyPosition = 0;
            int amountPosition = 0;
            int channelPosition = 0;
            boolean debit = false;

            for (;;) {
                whitespace();
                if (bytes[p] == '}') {
                    p++;
                    break;
                }
                int f = field();
                whitespace();
                p++;
                whitespace();

                switch (f) {
                    case 2:
                        accountPosition = p;
                        skipString();
                        break;
                    case 3:
                        readString();
                        if (textEquals("void")) return;
                        debit = textEquals("debit");
                        break;
                    case 4:
                        amountPosition = p;
                        skipString();
                        break;
                    case 5:
                        currencyPosition = p;
                        skipString();
                        break;
                    case 6:
                        p++;
                        whitespace();
                        while (bytes[p] != ']') {
                            readString();
                            if (textEquals("test")) return;
                            whitespace();
                            if (bytes[p] == ',') {
                                p++;
                                whitespace();
                            }
                        }
                        p++;
                        break;
                    case 7:
                        p++;
                        whitespace();
                        if (bytes[p] != '}') {
                            for (;;) {
                                int mf = field();
                                whitespace();
                                p++;
                                whitespace();
                                if (mf == 8) channelPosition = p;
                                skipValue();
                                whitespace();
                                if (bytes[p++] == '}') break;
                                whitespace();
                            }
                        } else {
                            p++;
                        }
                        break;
                    default:
                        skipValue();
                        break;
                }

                whitespace();
                if (bytes[p++] == '}') break;
            }

            p = currencyPosition;
            readString();
            Entry rate = rates.find(chars, length, hash, false);

            long usd;
            if (rate.big == null && rate.value == 0) {
                usd = 0;
            } else {
                p = amountPosition;
                long amount = readAmount();
                long product;
                if (amountBig == null && rate.big == null) {
                    product = amount * rate.value;
                } else {
                    BigInteger a = amountBig != null
                            ? amountBig : BigInteger.valueOf(amount);
                    BigInteger r = rate.big != null
                            ? rate.big : BigInteger.valueOf(rate.value);
                    product = a.multiply(r).longValue();
                }
                usd = Math.floorDiv(product, 1_000_000L);
            }

            long signed = debit ? -usd : usd;
            counted++;
            net += signed;

            p = accountPosition;
            readString();
            Entry account = accounts.find(chars, length, hash, true);
            account.value += signed;

            p = channelPosition;
            readString();
            Entry channel = channels.find(chars, length, hash, true);
            channel.count++;
            channel.value += signed;
        }

        static boolean better(Entry a, Entry b) {
            return a.value > b.value
                    || (a.value == b.value && a.key.compareTo(b.key) < 0);
        }

        void output() throws IOException {
            BufferedWriter out = new BufferedWriter(
                    new OutputStreamWriter(System.out, StandardCharsets.UTF_8),
                    1 << 16);

            out.write("counted ");
            out.write(Long.toString(counted));
            out.write('\n');
            out.write("net ");
            out.write(Long.toString(net));
            out.write('\n');

            Entry[] sortedChannels = channels.toArray();
            Arrays.sort(sortedChannels, (a, b) -> a.key.compareTo(b.key));
            for (Entry e : sortedChannels) {
                out.write("channel ");
                out.write(e.key);
                out.write(' ');
                out.write(Long.toString(e.count));
                out.write(' ');
                out.write(Long.toString(e.value));
                out.write('\n');
            }

            Entry[] top = new Entry[10];
            int size = 0;
            for (Entry e : accounts.entries) {
                if (e == null) continue;
                if (size == 10 && !better(e, top[9])) continue;

                int at;
                if (size < 10) {
                    at = size++;
                } else {
                    at = 9;
                }
                while (at > 0 && better(e, top[at - 1])) {
                    top[at] = top[at - 1];
                    at--;
                }
                top[at] = e;
            }

            for (int i = 0; i < size; i++) {
                out.write("account ");
                out.write(top[i].key);
                out.write(' ');
                out.write(Long.toString(top[i].value));
                out.write('\n');
            }
            out.flush();
        }
    }

    public static void main(String[] args) throws Exception {
        Ledger ledger = new Ledger();
        try (Lines lines = new Lines(args[0])) {
            if (lines.next()) {
                ledger.header(lines.data, lines.start);
                while (lines.next()) {
                    ledger.transaction(lines.data, lines.start);
                }
            }
        }
        ledger.output();
    }
}
