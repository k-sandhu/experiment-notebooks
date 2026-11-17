import java.io.FileInputStream;
import java.io.IOException;
import java.io.PrintStream;
import java.io.ByteArrayOutputStream;
import java.lang.invoke.MethodHandles;
import java.lang.invoke.VarHandle;
import java.nio.ByteOrder;
import java.util.Arrays;

// Ledger: streaming JSON Lines scanner with exact integer currency conversion.
public class Main {

    /** Open-addressing table interning byte strings to dense indices, with per-entry sums. */
    static final class Interner {
        int[] slots = new int[1024]; // index + 1, 0 = empty
        int[] slotHash = new int[1024];
        int mask = 1023;
        byte[][] keys = new byte[64][];
        long[] sum = new long[64];
        long[] count = new long[64];
        int size;

        static int hash(byte[] b, int off, int len) {
            int h = len * 0x9E3779B1;
            for (int i = 0; i < len; i++) h = (h ^ b[off + i]) * 0x01000193;
            return h ^ (h >>> 15);
        }

        int find(byte[] b, int off, int len) {
            int h = hash(b, off, len);
            for (int i = h & mask; ; i = (i + 1) & mask) {
                int s = slots[i];
                if (s == 0) return -1;
                if (slotHash[i] == h && Arrays.equals(keys[s - 1], 0, keys[s - 1].length, b, off, off + len)) return s - 1;
            }
        }

        int intern(byte[] b, int off, int len) {
            int h = hash(b, off, len);
            for (int i = h & mask; ; i = (i + 1) & mask) {
                int s = slots[i];
                if (s == 0) {
                    if (size == keys.length) {
                        keys = Arrays.copyOf(keys, size * 2);
                        sum = Arrays.copyOf(sum, size * 2);
                        count = Arrays.copyOf(count, size * 2);
                    }
                    keys[size] = Arrays.copyOfRange(b, off, off + len);
                    slots[i] = ++size;
                    slotHash[i] = h;
                    if (size * 2 > slots.length) grow();
                    return size - 1;
                }
                if (slotHash[i] == h) {
                    byte[] k = keys[s - 1];
                    if (Arrays.equals(k, 0, k.length, b, off, off + len)) return s - 1;
                }
            }
        }

        void grow() {
            int[] os = slots, oh = slotHash;
            slots = new int[os.length * 2];
            slotHash = new int[os.length * 2];
            mask = slots.length - 1;
            for (int j = 0; j < os.length; j++) {
                if (os[j] == 0) continue;
                int i = oh[j] & mask;
                while (slots[i] != 0) i = (i + 1) & mask;
                slots[i] = os[j];
                slotHash[i] = oh[j];
            }
        }
    }

    static final boolean[] WS = new boolean[256];
    static final boolean[] STRUCT = new boolean[256];
    static {
        WS[' '] = WS['\t'] = WS['\n'] = WS['\r'] = true;
        STRUCT['"'] = STRUCT['{'] = STRUCT['}'] = STRUCT['['] = STRUCT[']'] = true;
    }

    final Interner currencies = new Interner();
    final Interner channels = new Interner();
    final Interner accounts = new Interner();
    long counted, net;

    byte[] buf;

    // Result of the last parseStr: bytes [strOff, strOff + strLen) of strBuf.
    byte[] strBuf;
    int strOff, strLen;

    // Scratch buffers for strings with escapes, one per field that must survive until the object ends.
    static final int K_KEY = 0, K_ACC = 1, K_CHAN = 2, K_TYPE = 3, K_AMT = 4, K_CUR = 5, K_TAG = 6;
    final byte[][] scratch = new byte[7][64];

    int skipWs(int i) {
        final byte[] b = buf;
        while (WS[b[i] & 0xFF]) i++;
        return i;
    }

    static int hexVal(byte c) {
        if (c >= '0' && c <= '9') return c - '0';
        if (c >= 'a' && c <= 'f') return c - 'a' + 10;
        return c - 'A' + 10;
    }

    int hex4(int i) {
        final byte[] b = buf;
        return (hexVal(b[i]) << 12) | (hexVal(b[i + 1]) << 8) | (hexVal(b[i + 2]) << 4) | hexVal(b[i + 3]);
    }

    /** Parses the string whose opening quote is at i; result in strBuf/strOff/strLen. */
    int parseStr(int i, int slot) {
        final byte[] b = buf;
        int start = ++i;
        for (;;) {
            byte c = b[i];
            if (c == '"') {
                strBuf = b;
                strOff = start;
                strLen = i - start;
                return i + 1;
            }
            if (c == '\\') return decodeStr(start, i, slot);
            i++;
        }
    }

    int decodeStr(int start, int i, int slot) {
        final byte[] b = buf;
        byte[] out = scratch[slot];
        int n = 0;
        int need = (i - start) + 8;
        if (out.length < need) out = new byte[need * 2];
        System.arraycopy(b, start, out, 0, i - start);
        n = i - start;
        for (;;) {
            if (out.length < n + 8) out = Arrays.copyOf(out, out.length * 2);
            byte c = b[i];
            if (c == '"') break;
            if (c != '\\') {
                out[n++] = c;
                i++;
                continue;
            }
            byte e = b[i + 1];
            i += 2;
            switch (e) {
                case 'n' -> out[n++] = '\n';
                case 't' -> out[n++] = '\t';
                case 'r' -> out[n++] = '\r';
                case 'b' -> out[n++] = '\b';
                case 'f' -> out[n++] = '\f';
                case 'u' -> {
                    int cp = hex4(i);
                    i += 4;
                    if (cp >= 0xD800 && cp < 0xDC00 && b[i] == '\\' && b[i + 1] == 'u') {
                        int lo = hex4(i + 2);
                        if (lo >= 0xDC00 && lo < 0xE000) {
                            cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
                            i += 6;
                        }
                    }
                    if (cp < 0x80) {
                        out[n++] = (byte) cp;
                    } else if (cp < 0x800) {
                        out[n++] = (byte) (0xC0 | (cp >> 6));
                        out[n++] = (byte) (0x80 | (cp & 0x3F));
                    } else if (cp < 0x10000) {
                        out[n++] = (byte) (0xE0 | (cp >> 12));
                        out[n++] = (byte) (0x80 | ((cp >> 6) & 0x3F));
                        out[n++] = (byte) (0x80 | (cp & 0x3F));
                    } else {
                        out[n++] = (byte) (0xF0 | (cp >> 18));
                        out[n++] = (byte) (0x80 | ((cp >> 12) & 0x3F));
                        out[n++] = (byte) (0x80 | ((cp >> 6) & 0x3F));
                        out[n++] = (byte) (0x80 | (cp & 0x3F));
                    }
                }
                default -> out[n++] = e;
            }
        }
        scratch[slot] = out;
        strBuf = out;
        strOff = 0;
        strLen = n;
        return i + 1;
    }

    static final VarHandle LONGS = MethodHandles.byteArrayViewVarHandle(long[].class, ByteOrder.LITTLE_ENDIAN);
    static final long ONES = 0x0101010101010101L;
    static final long HIGHS = 0x8080808080808080L;
    static final long QUOTES = ONES * '"';
    static final long BACKSLASHES = ONES * 0x5C;
    static final long BRACKET_MASK = ONES * 0xD9; // {, }, [, ] all become 0x59 (so do Y, _, y, DEL)
    static final long BRACKETS = ONES * 0x59;

    /** High bit set in each zero byte of v; the lowest set bit is always exact. */
    static long zeroBytes(long v) {
        return (v - ONES) & ~v & HIGHS;
    }

    /** Index of the first quote or backslash at or after i, scanning 8 bytes at a time (buf has slack). */
    int findQuoteOrEscape(int i) {
        final byte[] b = buf;
        for (;;) {
            long w = (long) LONGS.get(b, i);
            long m = zeroBytes(w ^ QUOTES) | zeroBytes(w ^ BACKSLASHES);
            if (m != 0) return i + (Long.numberOfTrailingZeros(m) >>> 3);
            i += 8;
        }
    }

    int skipStrBody(int i) {
        final byte[] b = buf;
        for (;;) {
            i = findQuoteOrEscape(i);
            if (b[i] == '"') return i + 1;
            i += 2;
        }
    }

    int skipContainer(int i) {
        final byte[] b = buf;
        int depth = 1;
        i++;
        for (;;) {
            long w = (long) LONGS.get(b, i);
            long m = zeroBytes(w ^ QUOTES) | zeroBytes((w & BRACKET_MASK) ^ BRACKETS);
            if (m == 0) {
                i += 8;
                continue;
            }
            i += Long.numberOfTrailingZeros(m) >>> 3;
            byte c = b[i++];
            if (c == '"') {
                i = skipStrBody(i);
            } else if (c == '{' || c == '[') {
                depth++;
            } else if (c == '}' || c == ']') {
                if (--depth == 0) return i;
            }
        }
    }

    int skipVal(int i) {
        final byte[] b = buf;
        byte c = b[i];
        if (c == '"') return skipStrBody(i + 1);
        if (c == '{' || c == '[') return skipContainer(i);
        while (!(c == ',' || c == '}' || c == ']' || WS[c & 0xFF])) c = b[++i];
        return i;
    }

    /** True if the last parsed string equals the ASCII literal. */
    static final byte[] L_ACCOUNT = "account".getBytes();
    static final byte[] L_AMOUNT = "amount".getBytes();
    static final byte[] L_CHANNEL = "channel".getBytes();
    static final byte[] L_CREDIT = "credit".getBytes();
    static final byte[] L_CURRENCY = "currency".getBytes();
    static final byte[] L_DEBIT = "debit".getBytes();
    static final byte[] L_META = "meta".getBytes();
    static final byte[] L_RATES = "rates".getBytes();
    static final byte[] L_REFUND = "refund".getBytes();
    static final byte[] L_TAGS = "tags".getBytes();
    static final byte[] L_TEST = "test".getBytes();
    static final byte[] L_TYPE = "type".getBytes();

    boolean strIs(byte[] lit) {
        int n = lit.length;
        if (strLen != n) return false;
        final byte[] s = strBuf;
        final int o = strOff;
        for (int k = 0; k < n; k++) if (s[o + k] != lit[k]) return false;
        return true;
    }

    int parseRates(int i) {
        final byte[] b = buf;
        i = skipWs(i + 1);
        if (b[i] == '}') return i + 1;
        for (;;) {
            i = parseStr(i, K_KEY);
            boolean isRates = strIs(L_RATES);
            i = skipWs(skipWs(i) + 1);
            if (isRates && b[i] == '{') {
                i = skipWs(i + 1);
                if (b[i] != '}') {
                    for (;;) {
                        i = parseStr(i, K_CUR);
                        int id = currencies.intern(strBuf, strOff, strLen);
                        i = skipWs(skipWs(i) + 1);
                        boolean neg = false;
                        if (b[i] == '-') {
                            neg = true;
                            i++;
                        }
                        long v = 0;
                        while (b[i] >= '0' && b[i] <= '9') v = v * 10 + (b[i++] - '0');
                        i = skipVal(i);
                        currencies.sum[id] = neg ? -v : v;
                        i = skipWs(i);
                        if (b[i] == ',') {
                            i = skipWs(i + 1);
                            continue;
                        }
                        break;
                    }
                }
                i++;
            } else {
                i = skipVal(i);
            }
            i = skipWs(i);
            if (b[i] == ',') {
                i = skipWs(i + 1);
                continue;
            }
            return i + 1;
        }
    }

    int parseTx(int i) {
        final byte[] b = buf;
        byte[] accB = null, chanB = null, curB = null, amtB = null;
        int accO = 0, accL = 0, chanO = 0, chanL = 0, curO = 0, curL = 0, amtO = 0, amtL = 0;
        int sign = 0;
        boolean test = false;

        i = skipWs(i + 1);
        if (b[i] == '}') return i + 1;
        for (;;) {
            i = parseStr(i, K_KEY);
            int kl = strLen;
            int kind = 0; // 1 type, 2 tags, 3 meta, 4 amount, 5 account, 6 currency
            if (kl == 4) {
                if (strIs(L_TYPE)) kind = 1;
                else if (strIs(L_TAGS)) kind = 2;
                else if (strIs(L_META)) kind = 3;
            } else if (kl == 6) {
                if (strIs(L_AMOUNT)) kind = 4;
            } else if (kl == 7) {
                if (strIs(L_ACCOUNT)) kind = 5;
            } else if (kl == 8) {
                if (strIs(L_CURRENCY)) kind = 6;
            }
            i = skipWs(skipWs(i) + 1);
            switch (kind) {
                case 1 -> {
                    i = parseStr(i, K_TYPE);
                    if (strIs(L_CREDIT) || strIs(L_REFUND)) sign = 1;
                    else if (strIs(L_DEBIT)) sign = -1;
                    else sign = 0;
                }
                case 2 -> {
                    i = skipWs(i + 1);
                    if (b[i] != ']') {
                        for (;;) {
                            if (b[i] == '"') {
                                i = parseStr(i, K_TAG);
                                if (strIs(L_TEST)) test = true;
                            } else {
                                i = skipVal(i);
                            }
                            i = skipWs(i);
                            if (b[i] == ',') {
                                i = skipWs(i + 1);
                                continue;
                            }
                            break;
                        }
                    }
                    i++;
                }
                case 3 -> {
                    i = skipWs(i + 1);
                    if (b[i] != '}') {
                        for (;;) {
                            i = parseStr(i, K_KEY);
                            boolean isChan = strIs(L_CHANNEL);
                            i = skipWs(skipWs(i) + 1);
                            if (isChan && b[i] == '"') {
                                i = parseStr(i, K_CHAN);
                                chanB = strBuf;
                                chanO = strOff;
                                chanL = strLen;
                            } else {
                                i = skipVal(i);
                            }
                            i = skipWs(i);
                            if (b[i] == ',') {
                                i = skipWs(i + 1);
                                continue;
                            }
                            break;
                        }
                    }
                    i++;
                }
                case 4 -> {
                    i = parseStr(i, K_AMT);
                    amtB = strBuf;
                    amtO = strOff;
                    amtL = strLen;
                }
                case 5 -> {
                    i = parseStr(i, K_ACC);
                    accB = strBuf;
                    accO = strOff;
                    accL = strLen;
                }
                case 6 -> {
                    i = parseStr(i, K_CUR);
                    curB = strBuf;
                    curO = strOff;
                    curL = strLen;
                }
                default -> i = skipVal(i);
            }
            i = skipWs(i);
            if (b[i] == ',') {
                i = skipWs(i + 1);
                continue;
            }
            i++;
            break;
        }

        if (sign == 0 || test) return i;

        long hund = 0;
        int k = 0;
        while (k < amtL && amtB[amtO + k] != '.') hund = hund * 10 + (amtB[amtO + k++] - '0');
        hund *= 100;
        if (k < amtL) {
            k++;
            if (k < amtL) hund += (amtB[amtO + k] - '0') * 10;
            if (k + 1 < amtL) hund += amtB[amtO + k + 1] - '0';
        }
        int cid = currencies.find(curB, curO, curL);
        long rate = cid < 0 ? 0 : currencies.sum[cid];
        long v = hund * rate / 1000000 * sign;

        counted++;
        net += v;
        int ch = channels.intern(chanB, chanO, chanL);
        channels.count[ch]++;
        channels.sum[ch] += v;
        int ac = accounts.intern(accB, accO, accL);
        accounts.sum[ac] += v;
        return i;
    }

    /** Parses all complete objects in buf[0, lim); buf[lim] holds a 0 sentinel. */
    boolean process(int lim, boolean first) {
        int i = 0;
        for (;;) {
            i = skipWs(i);
            if (i >= lim) return first;
            if (first) {
                i = parseRates(i);
                first = false;
            } else {
                i = parseTx(i);
            }
        }
    }

    void run(String path) throws IOException {
        final int slack = 64;
        buf = new byte[(8 << 20) + slack];
        int capacity = buf.length - slack;
        int n = 0;
        boolean first = true;
        try (FileInputStream in = new FileInputStream(path)) {
            for (;;) {
                if (n == capacity) {
                    buf = Arrays.copyOf(buf, capacity * 2 + slack);
                    capacity *= 2;
                }
                int got = in.read(buf, n, capacity - n);
                boolean eof = got < 0;
                if (!eof) n += got;
                int lim;
                if (eof) {
                    if (n == 0) break;
                    if (buf[n - 1] != '\n') buf[n++] = '\n';
                    lim = n;
                } else {
                    int j = n;
                    while (j > 0 && buf[j - 1] != '\n') j--;
                    if (j == 0) continue;
                    lim = j;
                }
                byte saved = buf[lim];
                buf[lim] = 0;
                first = process(lim, first);
                buf[lim] = saved;
                System.arraycopy(buf, lim, buf, 0, n - lim);
                n -= lim;
                if (eof) break;
            }
        }
        print();
    }

    void print() {
        ByteArrayOutputStream out = new ByteArrayOutputStream(1024);
        StringBuilder sb = new StringBuilder();
        sb.append("counted ").append(counted).append('\n').append("net ").append(net).append('\n');
        out.writeBytes(sb.toString().getBytes());

        Integer[] ch = new Integer[channels.size];
        for (int i = 0; i < ch.length; i++) ch[i] = i;
        Arrays.sort(ch, (x, y) -> Arrays.compareUnsigned(channels.keys[x], channels.keys[y]));
        for (int c : ch) {
            out.writeBytes("channel ".getBytes());
            out.writeBytes(channels.keys[c]);
            out.writeBytes((" " + channels.count[c] + " " + channels.sum[c] + "\n").getBytes());
        }

        Integer[] ac = new Integer[accounts.size];
        for (int i = 0; i < ac.length; i++) ac[i] = i;
        Arrays.sort(ac, (x, y) -> {
            long sx = accounts.sum[x], sy = accounts.sum[y];
            if (sx != sy) return sx > sy ? -1 : 1;
            return Arrays.compareUnsigned(accounts.keys[x], accounts.keys[y]);
        });
        for (int k = 0; k < Math.min(10, ac.length); k++) {
            int a = ac[k];
            out.writeBytes("account ".getBytes());
            out.writeBytes(accounts.keys[a]);
            out.writeBytes((" " + accounts.sum[a] + "\n").getBytes());
        }
        PrintStream ps = new PrintStream(new java.io.FileOutputStream(java.io.FileDescriptor.out), false);
        ps.writeBytes(out.toByteArray());
        ps.flush();
    }

    public static void main(String[] args) throws IOException {
        new Main().run(args[0]);
    }
}
