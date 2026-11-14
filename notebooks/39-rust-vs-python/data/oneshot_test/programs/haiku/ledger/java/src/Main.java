import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;

public final class Main {

    static final class Table {
        byte[][] keys = new byte[256][];
        long[] sums = new long[256];
        long[] counts = new long[256];
        int[] hashes = new int[256];
        int size;
        int[] slots = new int[512];
        int mask = 511;

        static int hash(byte[] a, int off, int len) {
            int h = 0x811C9DC5;
            int end = off + len;
            for (int i = off; i < end; i++) h = (h ^ a[i]) * 0x01000193;
            h ^= h >>> 15;
            h *= 0x2C1B3C6D;
            h ^= h >>> 12;
            return h;
        }

        static boolean same(byte[] k, byte[] a, int off, int len) {
            for (int i = 0; i < len; i++) if (k[i] != a[off + i]) return false;
            return true;
        }

        int find(byte[] a, int off, int len, int h) {
            int[] sl = slots;
            int m = mask;
            int s = h & m;
            while (true) {
                int v = sl[s];
                if (v == 0) return -1;
                int idx = v - 1;
                if (hashes[idx] == h) {
                    byte[] k = keys[idx];
                    if (k.length == len && same(k, a, off, len)) return idx;
                }
                s = (s + 1) & m;
            }
        }

        int findOrAdd(byte[] a, int off, int len) {
            int h = hash(a, off, len);
            int idx = find(a, off, len, h);
            if (idx >= 0) return idx;
            idx = size++;
            if (idx == keys.length) {
                int cap = keys.length << 1;
                keys = Arrays.copyOf(keys, cap);
                sums = Arrays.copyOf(sums, cap);
                counts = Arrays.copyOf(counts, cap);
                hashes = Arrays.copyOf(hashes, cap);
            }
            keys[idx] = Arrays.copyOfRange(a, off, off + len);
            hashes[idx] = h;
            if (size * 2 > slots.length) rehash();
            else place(idx, h);
            return idx;
        }

        void place(int idx, int h) {
            int s = h & mask;
            while (slots[s] != 0) s = (s + 1) & mask;
            slots[s] = idx + 1;
        }

        void rehash() {
            int cap = slots.length << 1;
            slots = new int[cap];
            mask = cap - 1;
            for (int i = 0; i < size; i++) place(i, hashes[i]);
        }
    }

    static byte[] ascii(String s) {
        return s.getBytes(StandardCharsets.US_ASCII);
    }

    static final byte[] K_RATES = ascii("rates");
    static final byte[] K_ACCOUNT = ascii("account");
    static final byte[] K_TYPE = ascii("type");
    static final byte[] K_AMOUNT = ascii("amount");
    static final byte[] K_CURRENCY = ascii("currency");
    static final byte[] K_TAGS = ascii("tags");
    static final byte[] K_META = ascii("meta");
    static final byte[] K_CHANNEL = ascii("channel");
    static final byte[] T_TEST = ascii("test");
    static final byte[] T_CREDIT = ascii("credit");
    static final byte[] T_DEBIT = ascii("debit");
    static final byte[] T_REFUND = ascii("refund");
    static final byte[] T_VOID = ascii("void");

    static byte[] b;
    static int p, e;
    static int sOff, sLen;
    static boolean haveRates;
    static final Table rates = new Table();
    static final Table accounts = new Table();
    static final Table channels = new Table();
    static long totalN, totalNet;
    static int accOff, accLen, chOff, chLen, curOff, curLen, typeCode;
    static long hund;
    static boolean test;

    public static void main(String[] args) throws IOException {
        try (InputStream in = new FileInputStream(args[0])) {
            byte[] buf = new byte[1 << 22];
            int filled = 0;
            while (true) {
                if (filled == buf.length) buf = Arrays.copyOf(buf, buf.length << 1);
                int r = in.read(buf, filled, buf.length - filled);
                if (r < 0) break;
                filled += r;
                b = buf;
                int s = 0, k = 0;
                while (true) {
                    while (k < filled && buf[k] != '\n') k++;
                    if (k >= filled) break;
                    if (k > s) handle(s, k);
                    k++;
                    s = k;
                }
                int rem = filled - s;
                System.arraycopy(buf, s, buf, 0, rem);
                filled = rem;
            }
            if (filled > 0) {
                b = buf;
                handle(0, filled);
            }
        }
        output();
    }

    static void handle(int s, int end) {
        p = s;
        e = end;
        skipWs();
        if (p >= e) return;
        if (!haveRates) {
            haveRates = true;
            parseRates();
        } else {
            transaction();
        }
    }

    static void skipWs() {
        byte[] a = b;
        int i = p;
        while (i < e) {
            byte c = a[i];
            if (c != ' ' && c != '\n' && c != '\r' && c != '\t') break;
            i++;
        }
        p = i;
    }

    static void skipString() {
        int q = p + 1;
        while (b[q] != '"') {
            if (b[q] == '\\') q++;
            q++;
        }
        p = q + 1;
    }

    static void skipValue() {
        skipWs();
        int c = b[p];
        if (c == '"') {
            skipString();
            return;
        }
        if (c == '{' || c == '[') {
            int depth = 0;
            do {
                c = b[p];
                if (c == '"') {
                    skipString();
                    continue;
                }
                if (c == '{' || c == '[') depth++;
                else if (c == '}' || c == ']') depth--;
                p++;
            } while (depth > 0);
            return;
        }
        while (p < e) {
            c = b[p];
            if (c == ',' || c == '}' || c == ']' || c == ' ' || c == '\t' || c == '\r' || c == '\n') break;
            p++;
        }
    }

    static void readString() {
        byte[] a = b;
        int start = p + 1;
        int q = start;
        while (true) {
            byte c = a[q];
            if (c == '"') {
                sOff = start;
                sLen = q - start;
                p = q + 1;
                return;
            }
            if (c == '\\') {
                decodeString(start);
                return;
            }
            q++;
        }
    }

    static int hex4(byte[] a, int i) {
        int v = 0;
        for (int k = 0; k < 4; k++) {
            int c = a[i + k];
            int d = c <= '9' ? c - '0' : (c | 0x20) - 'a' + 10;
            v = (v << 4) | d;
        }
        return v;
    }

    static int putUtf8(byte[] a, int w, int cp) {
        if (cp < 0x80) {
            a[w++] = (byte) cp;
        } else if (cp < 0x800) {
            a[w++] = (byte) (0xC0 | (cp >> 6));
            a[w++] = (byte) (0x80 | (cp & 0x3F));
        } else if (cp < 0x10000) {
            a[w++] = (byte) (0xE0 | (cp >> 12));
            a[w++] = (byte) (0x80 | ((cp >> 6) & 0x3F));
            a[w++] = (byte) (0x80 | (cp & 0x3F));
        } else {
            a[w++] = (byte) (0xF0 | (cp >> 18));
            a[w++] = (byte) (0x80 | ((cp >> 12) & 0x3F));
            a[w++] = (byte) (0x80 | ((cp >> 6) & 0x3F));
            a[w++] = (byte) (0x80 | (cp & 0x3F));
        }
        return w;
    }

    // Decodes escapes in place; decoded output is never longer than the raw input.
    static void decodeString(int start) {
        byte[] a = b;
        int r = start, w = start;
        while (true) {
            int c = a[r];
            if (c == '"') break;
            if (c != '\\') {
                a[w++] = (byte) c;
                r++;
                continue;
            }
            int d = a[r + 1];
            r += 2;
            switch (d) {
                case '"': a[w++] = (byte) '"'; break;
                case '\\': a[w++] = (byte) '\\'; break;
                case '/': a[w++] = (byte) '/'; break;
                case 'b': a[w++] = 8; break;
                case 'f': a[w++] = 12; break;
                case 'n': a[w++] = (byte) '\n'; break;
                case 'r': a[w++] = (byte) '\r'; break;
                case 't': a[w++] = (byte) '\t'; break;
                case 'u': {
                    int cp = hex4(a, r);
                    r += 4;
                    if (cp >= 0xD800 && cp <= 0xDBFF && a[r] == '\\' && a[r + 1] == 'u') {
                        int lo = hex4(a, r + 2);
                        if (lo >= 0xDC00 && lo <= 0xDFFF) {
                            cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
                            r += 6;
                        }
                    }
                    w = putUtf8(a, w, cp);
                    break;
                }
                default:
                    a[w++] = (byte) d;
            }
        }
        sOff = start;
        sLen = w - start;
        p = r + 1;
    }

    static boolean eq(int off, int len, byte[] lit) {
        if (len != lit.length) return false;
        byte[] a = b;
        for (int i = 0; i < len; i++) if (a[off + i] != lit[i]) return false;
        return true;
    }

    static int typeOf() {
        if (eq(sOff, sLen, T_CREDIT)) return 0;
        if (eq(sOff, sLen, T_DEBIT)) return 1;
        if (eq(sOff, sLen, T_REFUND)) return 2;
        if (eq(sOff, sLen, T_VOID)) return 3;
        return -1;
    }

    static long parseHund(int off, int len) {
        long whole = 0, frac = 0;
        int fd = 0;
        boolean dot = false;
        int end = off + len;
        byte[] a = b;
        for (int i = off; i < end; i++) {
            int c = a[i];
            if (c == '.') {
                dot = true;
            } else if (dot) {
                if (fd < 2) {
                    frac = frac * 10 + (c - '0');
                    fd++;
                }
            } else {
                whole = whole * 10 + (c - '0');
            }
        }
        if (fd == 1) frac *= 10;
        return whole * 100 + frac;
    }

    static void tags() {
        p++;
        skipWs();
        if (b[p] == ']') {
            p++;
            return;
        }
        while (true) {
            skipWs();
            if (b[p] == '"') {
                readString();
                if (eq(sOff, sLen, T_TEST)) test = true;
            } else {
                skipValue();
            }
            skipWs();
            if (b[p] == ',') {
                p++;
                continue;
            }
            p++;
            return;
        }
    }

    static void meta() {
        p++;
        skipWs();
        if (b[p] == '}') {
            p++;
            return;
        }
        while (true) {
            skipWs();
            readString();
            int ko = sOff, kl = sLen;
            skipWs();
            p++;
            skipWs();
            if (eq(ko, kl, K_CHANNEL) && b[p] == '"') {
                readString();
                chOff = sOff;
                chLen = sLen;
            } else {
                skipValue();
            }
            skipWs();
            if (b[p] == ',') {
                p++;
                continue;
            }
            p++;
            return;
        }
    }

    static void transaction() {
        accLen = -1;
        chLen = -1;
        curLen = -1;
        typeCode = -1;
        hund = 0;
        test = false;
        p++; // '{'
        skipWs();
        if (b[p] == '}') return;
        while (true) {
            skipWs();
            readString();
            int ko = sOff, kl = sLen;
            skipWs();
            p++; // ':'
            skipWs();
            if (eq(ko, kl, K_ACCOUNT)) {
                if (b[p] == '"') {
                    readString();
                    accOff = sOff;
                    accLen = sLen;
                } else {
                    skipValue();
                }
            } else if (eq(ko, kl, K_TYPE)) {
                if (b[p] == '"') {
                    readString();
                    typeCode = typeOf();
                } else {
                    skipValue();
                }
            } else if (eq(ko, kl, K_AMOUNT)) {
                if (b[p] == '"') {
                    readString();
                    hund = parseHund(sOff, sLen);
                } else {
                    skipValue();
                }
            } else if (eq(ko, kl, K_CURRENCY)) {
                if (b[p] == '"') {
                    readString();
                    curOff = sOff;
                    curLen = sLen;
                } else {
                    skipValue();
                }
            } else if (eq(ko, kl, K_TAGS)) {
                if (b[p] == '[') tags();
                else skipValue();
            } else if (eq(ko, kl, K_META)) {
                if (b[p] == '{') meta();
                else skipValue();
            } else {
                skipValue();
            }
            skipWs();
            if (b[p] == ',') {
                p++;
                continue;
            }
            break;
        }
        finish();
    }

    static void finish() {
        if (typeCode < 0 || typeCode == 3 || test) return;
        if (accLen < 0 || chLen < 0 || curLen < 0) return;
        int ri = rates.find(b, curOff, curLen, Table.hash(b, curOff, curLen));
        long rate = ri >= 0 ? rates.sums[ri] : 0L;
        long usd = hund * rate / 1000000L;
        long signed = typeCode == 1 ? -usd : usd;
        totalN++;
        totalNet += signed;
        int ci = channels.findOrAdd(b, chOff, chLen);
        channels.counts[ci]++;
        channels.sums[ci] += signed;
        int ai = accounts.findOrAdd(b, accOff, accLen);
        accounts.sums[ai] += signed;
    }

    static void parseRates() {
        // p is at the opening '{' of the top-level object
        p++;
        skipWs();
        if (b[p] == '}') return;
        while (true) {
            skipWs();
            readString();
            boolean isRates = eq(sOff, sLen, K_RATES);
            skipWs();
            p++;
            skipWs();
            if (isRates && b[p] == '{') {
                p++;
                skipWs();
                if (b[p] == '}') {
                    p++;
                } else {
                    while (true) {
                        skipWs();
                        readString();
                        int idx = rates.findOrAdd(b, sOff, sLen);
                        skipWs();
                        p++;
                        skipWs();
                        long v = 0;
                        while (p < e && b[p] >= '0' && b[p] <= '9') {
                            v = v * 10 + (b[p] - '0');
                            p++;
                        }
                        rates.sums[idx] = v;
                        skipWs();
                        if (b[p] == ',') {
                            p++;
                            continue;
                        }
                        p++;
                        break;
                    }
                }
            } else {
                skipValue();
            }
            skipWs();
            if (b[p] == ',') {
                p++;
                continue;
            }
            return;
        }
    }

    static int cmpBytes(byte[] x, byte[] y) {
        int n = Math.min(x.length, y.length);
        for (int i = 0; i < n; i++) {
            int d = (x[i] & 0xff) - (y[i] & 0xff);
            if (d != 0) return d;
        }
        return x.length - y.length;
    }

    static boolean better(Table t, int a, int c) {
        if (t.sums[a] != t.sums[c]) return t.sums[a] > t.sums[c];
        return cmpBytes(t.keys[a], t.keys[c]) < 0;
    }

    static void output() {
        StringBuilder sb = new StringBuilder();
        sb.append("counted ").append(totalN).append('\n');
        sb.append("net ").append(totalNet).append('\n');

        int nc = channels.size;
        Integer[] order = new Integer[nc];
        for (int i = 0; i < nc; i++) order[i] = i;
        Arrays.sort(order, (x, y) -> cmpBytes(channels.keys[x.intValue()], channels.keys[y.intValue()]));
        for (int i : order) {
            sb.append("channel ")
              .append(new String(channels.keys[i], StandardCharsets.UTF_8))
              .append(' ')
              .append(channels.counts[i])
              .append(' ')
              .append(channels.sums[i])
              .append('\n');
        }

        int na = accounts.size;
        int[] top = new int[10];
        int nt = 0;
        for (int i = 0; i < na; i++) {
            if (nt == 10 && !better(accounts, i, top[9])) continue;
            int j = nt < 10 ? nt : 9;
            while (j > 0 && better(accounts, i, top[j - 1])) {
                top[j] = top[j - 1];
                j--;
            }
            top[j] = i;
            if (nt < 10) nt++;
        }
        for (int t = 0; t < nt; t++) {
            int i = top[t];
            sb.append("account ")
              .append(new String(accounts.keys[i], StandardCharsets.UTF_8))
              .append(' ')
              .append(accounts.sums[i])
              .append('\n');
        }

        byte[] out = sb.toString().getBytes(StandardCharsets.UTF_8);
        System.out.write(out, 0, out.length);
        System.out.flush();
    }
}
