import java.io.FileInputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;

public class Main {
    static byte[] sBuf;
    static int sStart, sEnd;
    static byte[] scratch = new byte[512];

    static final byte[] K_ACCOUNT = "account".getBytes(StandardCharsets.US_ASCII);
    static final byte[] K_TYPE = "type".getBytes(StandardCharsets.US_ASCII);
    static final byte[] K_TAGS = "tags".getBytes(StandardCharsets.US_ASCII);
    static final byte[] K_META = "meta".getBytes(StandardCharsets.US_ASCII);
    static final byte[] K_AMOUNT = "amount".getBytes(StandardCharsets.US_ASCII);
    static final byte[] K_CURRENCY = "currency".getBytes(StandardCharsets.US_ASCII);
    static final byte[] K_CHANNEL = "channel".getBytes(StandardCharsets.US_ASCII);
    static final byte[] K_RATES = "rates".getBytes(StandardCharsets.US_ASCII);

    static byte[][] rateKeys = new byte[0][];
    static long[] rateVals = new long[0];
    static boolean ratesDone = false;

    // per-line state
    static byte[] accBuf = new byte[64];
    static int accLen;
    static byte[] chBuf = new byte[64];
    static int chLen;
    static long hundredths;
    static long rate;
    static int typeCh;
    static boolean hasTest;

    // aggregates
    static long totalCount = 0, totalNet = 0;
    static final ByteMap channels = new ByteMap(16);
    static final ByteMap accounts = new ByteMap(1024);

    static final class ByteMap {
        int[] table;
        int mask;
        byte[][] keys;
        int[] hs;
        long[] cnt, net;
        int size;

        ByteMap(int cap) {
            table = new int[cap];
            mask = cap - 1;
            int c = Math.max(16, cap / 2);
            keys = new byte[c][];
            hs = new int[c];
            cnt = new long[c];
            net = new long[c];
        }

        int find(byte[] b, int len) {
            int h = 0;
            for (int i = 0; i < len; i++) h = h * 31 + b[i];
            h ^= h >>> 16;
            int i = h & mask;
            while (true) {
                int t = table[i];
                if (t == 0) break;
                int k = t - 1;
                if (hs[k] == h) {
                    byte[] kk = keys[k];
                    if (kk.length == len && Arrays.equals(kk, 0, len, b, 0, len)) return k;
                }
                i = (i + 1) & mask;
            }
            int k = size++;
            if (k >= keys.length) {
                int nc = keys.length * 2;
                keys = Arrays.copyOf(keys, nc);
                hs = Arrays.copyOf(hs, nc);
                cnt = Arrays.copyOf(cnt, nc);
                net = Arrays.copyOf(net, nc);
            }
            keys[k] = Arrays.copyOf(b, len);
            hs[k] = h;
            table[i] = k + 1;
            if (size * 2 > table.length) {
                int[] nt = new int[table.length * 2];
                int nm = nt.length - 1;
                for (int j = 0; j < size; j++) {
                    int x = hs[j] & nm;
                    while (nt[x] != 0) x = (x + 1) & nm;
                    nt[x] = j + 1;
                }
                table = nt;
                mask = nm;
            }
            return k;
        }
    }

    static int readString(byte[] b, int p) {
        int s = p + 1;
        int i = s;
        while (true) {
            byte c = b[i];
            if (c == '"') {
                sBuf = b;
                sStart = s;
                sEnd = i;
                return i + 1;
            }
            if (c == '\\') break;
            i++;
        }
        // slow path with escapes
        int n = i - s;
        if (scratch.length < n + 8) scratch = new byte[Math.max(scratch.length * 2, n + 8)];
        System.arraycopy(b, s, scratch, 0, n);
        while (true) {
            byte c = b[i];
            if (c == '"') {
                i++;
                break;
            }
            if (n + 8 > scratch.length) scratch = Arrays.copyOf(scratch, scratch.length * 2);
            if (c == '\\') {
                byte e = b[i + 1];
                switch (e) {
                    case 'n': scratch[n++] = 10; i += 2; break;
                    case 't': scratch[n++] = 9; i += 2; break;
                    case 'r': scratch[n++] = 13; i += 2; break;
                    case 'b': scratch[n++] = 8; i += 2; break;
                    case 'f': scratch[n++] = 12; i += 2; break;
                    case 'u': {
                        int cp = hex4(b, i + 2);
                        i += 6;
                        if (cp >= 0xD800 && cp < 0xDC00 && b[i] == '\\' && b[i + 1] == 'u') {
                            int lo = hex4(b, i + 2);
                            if (lo >= 0xDC00 && lo < 0xE000) {
                                cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
                                i += 6;
                            }
                        }
                        if (cp < 0x80) {
                            scratch[n++] = (byte) cp;
                        } else if (cp < 0x800) {
                            scratch[n++] = (byte) (0xC0 | (cp >> 6));
                            scratch[n++] = (byte) (0x80 | (cp & 0x3F));
                        } else if (cp < 0x10000) {
                            scratch[n++] = (byte) (0xE0 | (cp >> 12));
                            scratch[n++] = (byte) (0x80 | ((cp >> 6) & 0x3F));
                            scratch[n++] = (byte) (0x80 | (cp & 0x3F));
                        } else {
                            scratch[n++] = (byte) (0xF0 | (cp >> 18));
                            scratch[n++] = (byte) (0x80 | ((cp >> 12) & 0x3F));
                            scratch[n++] = (byte) (0x80 | ((cp >> 6) & 0x3F));
                            scratch[n++] = (byte) (0x80 | (cp & 0x3F));
                        }
                        break;
                    }
                    default: // '"', '\\', '/'
                        scratch[n++] = e;
                        i += 2;
                }
            } else {
                scratch[n++] = c;
                i++;
            }
        }
        sBuf = scratch;
        sStart = 0;
        sEnd = n;
        return i;
    }

    static int hex4(byte[] b, int p) {
        int v = 0;
        for (int i = 0; i < 4; i++) {
            int c = b[p + i];
            int d;
            if (c >= '0' && c <= '9') d = c - '0';
            else if (c >= 'a' && c <= 'f') d = c - 'a' + 10;
            else d = c - 'A' + 10;
            v = (v << 4) | d;
        }
        return v;
    }

    static int ws(byte[] b, int p) {
        while (b[p] <= ' ') p++;
        return p;
    }

    static int skipValue(byte[] b, int p) {
        byte c = b[p];
        if (c == '"') {
            int i = p + 1;
            while (true) {
                c = b[i++];
                if (c == '"') return i;
                if (c == '\\') i++;
            }
        }
        if (c == '{' || c == '[') {
            int depth = 1;
            int i = p + 1;
            while (depth > 0) {
                c = b[i++];
                if (c == '"') {
                    while (true) {
                        c = b[i++];
                        if (c == '"') break;
                        if (c == '\\') i++;
                    }
                } else if (c == '{' || c == '[') depth++;
                else if (c == '}' || c == ']') depth--;
            }
            return i;
        }
        int i = p;
        while (true) {
            c = b[i];
            if (c == ',' || c == '}' || c == ']' || c <= ' ') return i;
            i++;
        }
    }

    static boolean eq(byte[] a, int s, byte[] lit) {
        for (int i = 0; i < lit.length; i++) if (a[s + i] != lit[i]) return false;
        return true;
    }

    static int tagsArray(byte[] b, int p) {
        if (b[p] != '[') return skipValue(b, p);
        p++;
        p = ws(b, p);
        if (b[p] == ']') return p + 1;
        while (true) {
            p = ws(b, p);
            if (b[p] == '"') {
                p = readString(b, p);
                if (sEnd - sStart == 4) {
                    byte[] x = sBuf;
                    int s = sStart;
                    if (x[s] == 't' && x[s + 1] == 'e' && x[s + 2] == 's' && x[s + 3] == 't') hasTest = true;
                }
            } else {
                p = skipValue(b, p);
            }
            p = ws(b, p);
            if (b[p++] == ']') return p;
        }
    }

    static int metaObject(byte[] b, int p) {
        if (b[p] != '{') return skipValue(b, p);
        p++;
        p = ws(b, p);
        if (b[p] == '}') return p + 1;
        while (true) {
            p = ws(b, p);
            p = readString(b, p);
            boolean isCh = (sEnd - sStart == 7) && eq(sBuf, sStart, K_CHANNEL);
            p = ws(b, p);
            p++;
            p = ws(b, p);
            if (isCh && b[p] == '"') {
                p = readString(b, p);
                int len = sEnd - sStart;
                if (chBuf.length < len) chBuf = new byte[len * 2];
                System.arraycopy(sBuf, sStart, chBuf, 0, len);
                chLen = len;
            } else {
                p = skipValue(b, p);
            }
            p = ws(b, p);
            if (b[p++] == '}') return p;
        }
    }

    static int object(byte[] b, int p) {
        p++;
        p = ws(b, p);
        if (b[p] == '}') return p + 1;
        while (true) {
            p = ws(b, p);
            p = readString(b, p);
            int kid = 0;
            byte[] kb = sBuf;
            int ks = sStart;
            switch (sEnd - sStart) {
                case 7: if (eq(kb, ks, K_ACCOUNT)) kid = 1; break;
                case 4:
                    if (eq(kb, ks, K_TYPE)) kid = 2;
                    else if (eq(kb, ks, K_TAGS)) kid = 3;
                    else if (eq(kb, ks, K_META)) kid = 4;
                    break;
                case 6: if (eq(kb, ks, K_AMOUNT)) kid = 5; break;
                case 8: if (eq(kb, ks, K_CURRENCY)) kid = 6; break;
                default: break;
            }
            p = ws(b, p);
            p++;
            p = ws(b, p);
            switch (kid) {
                case 0:
                    p = skipValue(b, p);
                    break;
                case 1: {
                    p = readString(b, p);
                    int len = sEnd - sStart;
                    if (accBuf.length < len) accBuf = new byte[len * 2];
                    System.arraycopy(sBuf, sStart, accBuf, 0, len);
                    accLen = len;
                    break;
                }
                case 2:
                    p = readString(b, p);
                    typeCh = sEnd > sStart ? sBuf[sStart] : 0;
                    break;
                case 3:
                    p = tagsArray(b, p);
                    break;
                case 4:
                    p = metaObject(b, p);
                    break;
                case 5: {
                    p = readString(b, p);
                    byte[] x = sBuf;
                    int i = sStart, e = sEnd;
                    long whole = 0;
                    while (i < e && x[i] != '.') {
                        whole = whole * 10 + (x[i] - '0');
                        i++;
                    }
                    long h = whole * 100;
                    if (i < e) {
                        i++;
                        if (i < e) {
                            h += (x[i] - '0') * 10;
                            i++;
                            if (i < e) h += x[i] - '0';
                        }
                    }
                    hundredths = h;
                    break;
                }
                case 6: {
                    p = readString(b, p);
                    int len = sEnd - sStart;
                    long r = 0;
                    byte[][] rk = rateKeys;
                    for (int j = 0; j < rk.length; j++) {
                        byte[] k = rk[j];
                        if (k.length == len && Arrays.equals(k, 0, len, sBuf, sStart, sEnd)) {
                            r = rateVals[j];
                            break;
                        }
                    }
                    rate = r;
                    break;
                }
                default:
                    break;
            }
            p = ws(b, p);
            if (b[p++] == '}') return p;
        }
    }

    static int ratesLine(byte[] b, int p) {
        p++;
        p = ws(b, p);
        if (b[p] == '}') return p + 1;
        while (true) {
            p = ws(b, p);
            p = readString(b, p);
            boolean isRates = (sEnd - sStart == 5) && eq(sBuf, sStart, K_RATES);
            p = ws(b, p);
            p++;
            p = ws(b, p);
            if (isRates && b[p] == '{') {
                ArrayList<byte[]> ks = new ArrayList<>();
                ArrayList<Long> vs = new ArrayList<>();
                p++;
                p = ws(b, p);
                if (b[p] == '}') {
                    p++;
                } else {
                    while (true) {
                        p = ws(b, p);
                        p = readString(b, p);
                        ks.add(Arrays.copyOfRange(sBuf, sStart, sEnd));
                        p = ws(b, p);
                        p++;
                        p = ws(b, p);
                        long v = 0;
                        boolean neg = false;
                        if (b[p] == '-') {
                            neg = true;
                            p++;
                        }
                        while (b[p] >= '0' && b[p] <= '9') {
                            v = v * 10 + (b[p] - '0');
                            p++;
                        }
                        vs.add(neg ? -v : v);
                        p = ws(b, p);
                        if (b[p++] == '}') break;
                    }
                }
                rateKeys = ks.toArray(new byte[0][]);
                rateVals = new long[vs.size()];
                for (int i = 0; i < rateVals.length; i++) rateVals[i] = vs.get(i);
            } else {
                p = skipValue(b, p);
            }
            p = ws(b, p);
            if (b[p++] == '}') return p;
        }
    }

    static void process(byte[] b, int p, int limit) {
        while (true) {
            while (p < limit && b[p] <= ' ') p++;
            if (p >= limit) return;
            if (!ratesDone) {
                p = ratesLine(b, p);
                ratesDone = true;
                continue;
            }
            typeCh = 0;
            hasTest = false;
            accLen = 0;
            chLen = 0;
            hundredths = 0;
            rate = 0;
            p = object(b, p);
            if (typeCh == 'v' || hasTest) continue;
            long usd = (hundredths * rate) / 1000000L;
            if (typeCh == 'd') usd = -usd;
            totalCount++;
            totalNet += usd;
            int ci = channels.find(chBuf, chLen);
            channels.cnt[ci]++;
            channels.net[ci] += usd;
            int ai = accounts.find(accBuf, accLen);
            accounts.net[ai] += usd;
        }
    }

    static boolean before(int a, int c) {
        long na = accounts.net[a], nc = accounts.net[c];
        if (na != nc) return na > nc;
        return Arrays.compareUnsigned(accounts.keys[a], accounts.keys[c]) < 0;
    }

    public static void main(String[] args) throws IOException {
        byte[] buf = new byte[1 << 21];
        int filled = 0;
        try (FileInputStream in = new FileInputStream(args[0])) {
            while (true) {
                if (filled == buf.length) buf = Arrays.copyOf(buf, buf.length * 2);
                int n = in.read(buf, filled, buf.length - filled);
                if (n < 0) {
                    if (filled > 0) {
                        if (filled == buf.length) buf = Arrays.copyOf(buf, buf.length + 16);
                        buf[filled] = '\n';
                        process(buf, 0, filled);
                    }
                    break;
                }
                filled += n;
                int lim = filled;
                while (lim > 0 && buf[lim - 1] != '\n') lim--;
                if (lim == 0) continue;
                process(buf, 0, lim);
                System.arraycopy(buf, lim, buf, 0, filled - lim);
                filled -= lim;
            }
        }

        StringBuilder sb = new StringBuilder();
        sb.append("counted ").append(totalCount).append('\n');
        sb.append("net ").append(totalNet).append('\n');

        int cs = channels.size;
        Integer[] idx = new Integer[cs];
        String[] names = new String[cs];
        for (int i = 0; i < cs; i++) {
            idx[i] = i;
            names[i] = new String(channels.keys[i], StandardCharsets.ISO_8859_1);
        }
        Arrays.sort(idx, (x, y) -> names[x].compareTo(names[y]));
        for (int i = 0; i < cs; i++) {
            int k = idx[i];
            sb.append("channel ").append(names[k]).append(' ').append(channels.cnt[k]).append(' ')
                    .append(channels.net[k]).append('\n');
        }

        int[] top = new int[10];
        int cnt = 0;
        for (int k = 0; k < accounts.size; k++) {
            int pos = cnt;
            while (pos > 0 && before(k, top[pos - 1])) pos--;
            if (pos >= 10) continue;
            int last = Math.min(cnt, 9);
            for (int j = last; j > pos; j--) top[j] = top[j - 1];
            top[pos] = k;
            if (cnt < 10) cnt++;
        }
        for (int i = 0; i < cnt; i++) {
            int k = top[i];
            sb.append("account ").append(new String(accounts.keys[k], StandardCharsets.ISO_8859_1)).append(' ')
                    .append(accounts.net[k]).append('\n');
        }
        System.out.print(sb);
        System.out.flush();
    }
}
