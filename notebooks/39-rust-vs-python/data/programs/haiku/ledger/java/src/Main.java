import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.Arrays;

import static java.nio.charset.StandardCharsets.ISO_8859_1;

// Streams a JSON Lines file, parses only the fields it needs straight from bytes,
// and sums converted amounts per channel and per account with exact integer arithmetic.
public class Main {
    private static final byte[] EMPTY = new byte[0];
    private static final byte[] K_ACCOUNT = lit("account");
    private static final byte[] K_TYPE = lit("type");
    private static final byte[] K_CURRENCY = lit("currency");
    private static final byte[] K_AMOUNT = lit("amount");
    private static final byte[] K_TAGS = lit("tags");
    private static final byte[] K_META = lit("meta");
    private static final byte[] K_CHANNEL = lit("channel");
    private static final byte[] K_RATES = lit("rates");
    private static final byte[] V_TEST = lit("test");
    private static final byte[] V_VOID = lit("void");
    private static final byte[] V_DEBIT = lit("debit");

    // A decoded string: bytes [o, o + l) of a.
    private static final class Str {
        byte[] a = EMPTY;
        int o;
        int l;
    }

    // Reusable storage for strings that contain escapes.
    private static final class Scratch {
        byte[] a = new byte[64];
        int n;

        void add(int c) {
            if (n == a.length) a = Arrays.copyOf(a, n * 2);
            a[n++] = (byte) c;
        }
    }

    // Maps byte-string keys to dense indexes, with a sum and a count per key.
    private static final class KeyIndex {
        byte[][] keys = new byte[1024][];
        long[] sums = new long[1024];
        long[] counts = new long[1024];
        int size;
        int[] slots = new int[2048];
        int mask = 2047;

        int find(byte[] a, int o, int l) {
            int h = hash(a, o, l) & mask;
            for (;;) {
                int s = slots[h];
                if (s == 0) break;
                byte[] k = keys[s - 1];
                if (k.length == l && Arrays.equals(k, 0, l, a, o, o + l)) return s - 1;
                h = (h + 1) & mask;
            }
            if (size == keys.length) {
                keys = Arrays.copyOf(keys, size * 2);
                sums = Arrays.copyOf(sums, size * 2);
                counts = Arrays.copyOf(counts, size * 2);
            }
            keys[size] = Arrays.copyOfRange(a, o, o + l);
            slots[h] = size + 1;
            size++;
            if (size * 2 > slots.length) grow();
            return size - 1;
        }

        private static int hash(byte[] a, int o, int l) {
            int h = 0x811c9dc5;  // FNV-1a
            for (int i = o; i < o + l; i++) h = (h ^ a[i]) * 16777619;
            return h ^ (h >>> 15);
        }

        private void grow() {
            slots = new int[slots.length * 2];
            mask = slots.length - 1;
            for (int i = 0; i < size; i++) {
                int h = hash(keys[i], 0, keys[i].length) & mask;
                while (slots[h] != 0) h = (h + 1) & mask;
                slots[h] = i + 1;
            }
        }
    }

    private byte[] buf = new byte[1 << 22];
    private boolean haveRates;
    private boolean testFlag;
    private byte[][] rateName = new byte[16][];
    private long[] rateValue = new long[16];
    private int rateCount;
    private long counted;
    private long net;
    private final KeyIndex channels = new KeyIndex();
    private final KeyIndex accounts = new KeyIndex();

    private final Scratch keyScratch = new Scratch();
    private final Scratch typeScratch = new Scratch();
    private final Scratch accountScratch = new Scratch();
    private final Scratch currencyScratch = new Scratch();
    private final Scratch amountScratch = new Scratch();
    private final Scratch channelScratch = new Scratch();
    private final Scratch tagScratch = new Scratch();

    private final Str key = new Str();
    private final Str type = new Str();
    private final Str account = new Str();
    private final Str currency = new Str();
    private final Str amount = new Str();
    private final Str channel = new Str();
    private final Str tag = new Str();

    public static void main(String[] args) throws IOException {
        if (args.length < 1) {
            System.err.println("usage: java Main INPUT_PATH");
            System.exit(2);
        }
        Main m = new Main();
        try (InputStream in = new FileInputStream(args[0])) {
            m.run(in);
        }
        m.print();
    }

    private static byte[] lit(String s) {
        return s.getBytes(ISO_8859_1);
    }

    private void run(InputStream in) throws IOException {
        int carry = 0;
        for (;;) {
            if (carry == buf.length) buf = Arrays.copyOf(buf, buf.length * 2);
            int got = in.read(buf, carry, buf.length - carry);
            int end = got < 0 ? carry : carry + got;
            int stop = 0;
            if (got < 0) {
                stop = end;  // end of file: the last line may lack a newline
            } else {
                for (int i = end; i > 0; i--) {
                    if (buf[i - 1] == '\n') {
                        stop = i;
                        break;
                    }
                }
            }
            processLines(stop);
            carry = end - stop;
            System.arraycopy(buf, stop, buf, 0, carry);
            if (got < 0) break;
        }
    }

    private void processLines(int n) {
        byte[] b = buf;
        int p = 0;
        while (p < n) {
            int e = p;
            while (e < n && b[e] != '\n') e++;
            int q = p;
            while (q < e && (b[q] == ' ' || b[q] == '\t' || b[q] == '\r')) q++;
            if (q < e) {
                if (haveRates) {
                    parseTxn(q);
                } else {
                    parseRates(q);
                    haveRates = true;
                }
            }
            p = e + 1;
        }
    }

    // Object and array helpers. Each returns the position after the item.

    private int skipWs(int p) {
        byte[] b = buf;
        while (b[p] == ' ' || b[p] == '\t' || b[p] == '\r' || b[p] == '\n') p++;
        return p;
    }

    private int skipString(int p) {
        byte[] b = buf;
        p++;
        while (b[p] != '"') p += (b[p] == '\\') ? 2 : 1;
        return p + 1;
    }

    private int skipValue(int p) {
        byte[] b = buf;
        if (b[p] == '"') return skipString(p);
        if (b[p] == '{' || b[p] == '[') {
            int depth = 0;
            for (;;) {
                byte c = b[p];
                if (c == '"') {
                    p = skipString(p);
                    continue;
                }
                if (c == '{' || c == '[') {
                    depth++;
                } else if (c == '}' || c == ']') {
                    if (--depth == 0) return p + 1;
                }
                p++;
            }
        }
        while (b[p] != ',' && b[p] != '}' && b[p] != ']' && b[p] != ' ' && b[p] != '\t' && b[p] != '\r' && b[p] != '\n') p++;
        return p;
    }

    // p points at an opening quote. Sets out to the decoded value and returns the position after the closing quote.
    private int readString(int p, Scratch s, Str out) {
        byte[] b = buf;
        int start = ++p;
        boolean escaped = false;
        while (b[p] != '"') {
            if (b[p] == '\\') {
                escaped = true;
                p++;
            }
            p++;
        }
        if (escaped) {
            s.n = 0;
            decode(start, p, s);
            out.a = s.a;
            out.o = 0;
            out.l = s.n;
        } else {
            out.a = b;
            out.o = start;
            out.l = p - start;
        }
        return p + 1;
    }

    private void decode(int p, int e, Scratch s) {
        byte[] b = buf;
        while (p < e) {
            if (b[p] != '\\') {
                s.add(b[p++]);
                continue;
            }
            int c = b[p + 1];
            p += 2;
            switch (c) {
                case 'b' -> s.add(8);
                case 'f' -> s.add(12);
                case 'n' -> s.add(10);
                case 'r' -> s.add(13);
                case 't' -> s.add(9);
                case 'u' -> {
                    int cp = hex4(p);
                    p += 4;
                    if (cp >= 0xD800 && cp <= 0xDBFF && b[p] == '\\' && b[p + 1] == 'u') {
                        int lo = hex4(p + 2);
                        if (lo >= 0xDC00 && lo <= 0xDFFF) {
                            cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
                            p += 6;
                        }
                    }
                    appendUtf8(s, cp);
                }
                default -> s.add(c);  // \" \\ \/
            }
        }
    }

    private int hex4(int p) {
        int v = 0;
        for (int i = 0; i < 4; i++) {
            int c = buf[p + i];
            v = v * 16 + (c <= '9' ? c - '0' : (c | 0x20) - 'a' + 10);
        }
        return v;
    }

    private static void appendUtf8(Scratch s, int cp) {
        if (cp < 0x80) {
            s.add(cp);
        } else if (cp < 0x800) {
            s.add(0xC0 | (cp >> 6));
            s.add(0x80 | (cp & 0x3F));
        } else if (cp < 0x10000) {
            s.add(0xE0 | (cp >> 12));
            s.add(0x80 | ((cp >> 6) & 0x3F));
            s.add(0x80 | (cp & 0x3F));
        } else {
            s.add(0xF0 | (cp >> 18));
            s.add(0x80 | ((cp >> 12) & 0x3F));
            s.add(0x80 | ((cp >> 6) & 0x3F));
            s.add(0x80 | (cp & 0x3F));
        }
    }

    private static boolean eq(Str s, byte[] lit) {
        return s.l == lit.length && Arrays.equals(s.a, s.o, s.o + s.l, lit, 0, lit.length);
    }

    private void parseRates(int p) {
        byte[] b = buf;
        p++;  // '{'
        p = skipWs(p);
        if (b[p] == '}') return;
        for (;;) {
            p = skipWs(p);
            p = readString(p, keyScratch, key);
            p = skipWs(p) + 1;  // ':'
            p = skipWs(p);
            if (eq(key, K_RATES)) {
                p = parseRatesObject(p);
            } else {
                p = skipValue(p);
            }
            p = skipWs(p);
            if (b[p++] == '}') return;  // otherwise it was ','
        }
    }

    private int parseRatesObject(int p) {
        byte[] b = buf;
        p++;  // '{'
        p = skipWs(p);
        if (b[p] == '}') return p + 1;
        for (;;) {
            p = skipWs(p);
            p = readString(p, keyScratch, key);
            p = skipWs(p) + 1;  // ':'
            p = skipWs(p);
            boolean neg = b[p] == '-';
            if (neg) p++;
            long v = 0;
            while (b[p] >= '0' && b[p] <= '9') v = v * 10 + (b[p++] - '0');
            if (rateCount == rateName.length) {
                rateName = Arrays.copyOf(rateName, rateCount * 2);
                rateValue = Arrays.copyOf(rateValue, rateCount * 2);
            }
            rateName[rateCount] = Arrays.copyOfRange(key.a, key.o, key.o + key.l);
            rateValue[rateCount++] = neg ? -v : v;
            p = skipWs(p);
            if (b[p++] == '}') return p;  // otherwise it was ','
        }
    }

    private void parseTxn(int p) {
        byte[] b = buf;
        type.l = 0;
        account.l = 0;
        currency.l = 0;
        amount.l = 0;
        channel.l = 0;
        boolean test = false;
        p++;  // '{'
        p = skipWs(p);
        if (b[p] == '}') return;
        for (;;) {
            p = skipWs(p);
            p = readString(p, keyScratch, key);
            p = skipWs(p) + 1;  // ':'
            p = skipWs(p);
            if (eq(key, K_ACCOUNT)) {
                p = readString(p, accountScratch, account);
            } else if (eq(key, K_TYPE)) {
                p = readString(p, typeScratch, type);
            } else if (eq(key, K_CURRENCY)) {
                p = readString(p, currencyScratch, currency);
            } else if (eq(key, K_AMOUNT)) {
                if (b[p] == '"') {
                    p = readString(p, amountScratch, amount);
                } else {
                    int e = skipValue(p);
                    amount.a = b;
                    amount.o = p;
                    amount.l = e - p;
                    p = e;
                }
            } else if (eq(key, K_TAGS)) {
                p = parseTags(p);
                test = testFlag;
            } else if (eq(key, K_META)) {
                p = parseMeta(p);
            } else {
                p = skipValue(p);
            }
            p = skipWs(p);
            if (b[p++] == '}') break;  // otherwise it was ','
        }

        if (eq(type, V_VOID) || test) return;
        int r = -1;
        for (int i = 0; i < rateCount; i++) {
            if (rateName[i].length == currency.l
                    && Arrays.equals(rateName[i], 0, currency.l, currency.a, currency.o, currency.o + currency.l)) {
                r = i;
                break;
            }
        }
        if (r < 0) return;

        long h = hundredths(amount);
        long usd = h * rateValue[r] / 1000000L;
        long value = eq(type, V_DEBIT) ? -usd : usd;

        counted++;
        net += value;
        int c = channels.find(channel.a, channel.o, channel.l);
        channels.counts[c]++;
        channels.sums[c] += value;
        int a = accounts.find(account.a, account.o, account.l);
        accounts.sums[a] += value;
    }

    private int parseTags(int p) {
        byte[] b = buf;
        testFlag = false;
        p++;  // '['
        p = skipWs(p);
        if (b[p] == ']') return p + 1;
        for (;;) {
            p = skipWs(p);
            if (b[p] == '"') {
                p = readString(p, tagScratch, tag);
                if (eq(tag, V_TEST)) testFlag = true;
            } else {
                p = skipValue(p);
            }
            p = skipWs(p);
            if (b[p++] == ']') return p;  // otherwise it was ','
        }
    }

    private int parseMeta(int p) {
        byte[] b = buf;
        p++;  // '{'
        p = skipWs(p);
        if (b[p] == '}') return p + 1;
        for (;;) {
            p = skipWs(p);
            p = readString(p, keyScratch, key);
            p = skipWs(p) + 1;  // ':'
            p = skipWs(p);
            if (eq(key, K_CHANNEL) && b[p] == '"') {
                p = readString(p, channelScratch, channel);
            } else {
                p = skipValue(p);
            }
            p = skipWs(p);
            if (b[p++] == '}') return p;  // otherwise it was ','
        }
    }

    private static long hundredths(Str a) {
        long v = 0;
        int i = 0;
        for (; i < a.l && a.a[a.o + i] != '.'; i++) v = v * 10 + (a.a[a.o + i] - '0');
        v *= 100;
        if (i < a.l) {
            i++;
            long frac = 0;
            int digits = 0;
            for (; digits < 2 && i < a.l; i++, digits++) frac = frac * 10 + (a.a[a.o + i] - '0');
            if (digits == 1) frac *= 10;
            v += frac;
        }
        return v;
    }

    private void print() throws IOException {
        StringBuilder sb = new StringBuilder();
        sb.append("counted ").append(counted).append("\nnet ").append(net).append('\n');

        Integer[] chanOrder = new Integer[channels.size];
        for (int i = 0; i < chanOrder.length; i++) chanOrder[i] = i;
        Arrays.sort(chanOrder, (x, y) -> Arrays.compareUnsigned(channels.keys[x], channels.keys[y]));
        for (int i : chanOrder) {
            sb.append("channel ").append(new String(channels.keys[i], ISO_8859_1))
                    .append(' ').append(channels.counts[i]).append(' ').append(channels.sums[i]).append('\n');
        }

        Integer[] accOrder = new Integer[accounts.size];
        for (int i = 0; i < accOrder.length; i++) accOrder[i] = i;
        Arrays.sort(accOrder, (x, y) -> {
            if (accounts.sums[x] != accounts.sums[y]) return Long.compare(accounts.sums[y], accounts.sums[x]);
            return Arrays.compareUnsigned(accounts.keys[x], accounts.keys[y]);
        });
        for (int k = 0; k < Math.min(10, accOrder.length); k++) {
            int i = accOrder[k];
            sb.append("account ").append(new String(accounts.keys[i], ISO_8859_1))
                    .append(' ').append(accounts.sums[i]).append('\n');
        }

        System.out.write(sb.toString().getBytes(ISO_8859_1));
        System.out.flush();
    }
}
