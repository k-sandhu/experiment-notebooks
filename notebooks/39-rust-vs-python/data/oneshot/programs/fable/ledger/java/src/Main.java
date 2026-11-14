import java.io.FileDescriptor;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.lang.invoke.MethodHandles;
import java.lang.invoke.VarHandle;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;

public class Main {
    private static final VarHandle LONG =
            MethodHandles.byteArrayViewVarHandle(long[].class, ByteOrder.LITTLE_ENDIAN);
    private static final long ONES = 0x0101010101010101L;
    private static final long HIGH = 0x8080808080808080L;
    private static final long QUOTES = 0x2222222222222222L;
    private static final long BSLASH = 0x5C5C5C5C5C5C5C5CL;
    private static final long NEWLINES = 0x0A0A0A0A0A0A0A0AL;
    private static final long HASH_K = 0x9E3779B97F4A7C15L;
    private static final int CHUNK = 1 << 20;

    private static final byte[] AMOUNT = {'a', 'm', 'o', 'u', 'n', 't'};
    private static final byte[] ACCOUNT = {'a', 'c', 'c', 'o', 'u', 'n', 't'};
    private static final byte[] CURRENCY = {'c', 'u', 'r', 'r', 'e', 'n', 'c', 'y'};
    private static final byte[] CHANNEL = {'c', 'h', 'a', 'n', 'n', 'e', 'l'};
    private static final byte[] RATES = {'r', 'a', 't', 'e', 's'};

    static final class Table {
        long[] slots;
        int mask;
        int size;
        long[] keyPos;
        long[] sum;
        int[] cnt;
        byte[] arena;
        int arenaLen;

        Table(int cap) {
            slots = new long[cap];
            mask = cap - 1;
            int ec = Math.max(16, cap >> 1);
            keyPos = new long[ec];
            sum = new long[ec];
            cnt = new int[ec];
            arena = new byte[1024];
        }

        int get(byte[] b, int o, int l) {
            long h = 0;
            int i = o;
            final int e = o + l;
            while (e - i >= 8) {
                h = (h ^ (long) LONG.get(b, i)) * HASH_K;
                h ^= h >>> 29;
                i += 8;
            }
            if (i < e) {
                long w = (long) LONG.get(b, i) & (-1L >>> (64 - ((e - i) << 3)));
                h = (h ^ w) * HASH_K;
            }
            h ^= h >>> 32;
            final int hh = (int) h;
            final int m = mask;
            final long[] sl = slots;
            int pos = hh & m;
            while (true) {
                long s = sl[pos];
                if (s == 0) break;
                if ((int) (s >>> 32) == hh) {
                    int idx = (int) s - 1;
                    long kp = keyPos[idx];
                    int ko = (int) (kp >>> 32);
                    int kl = (int) kp;
                    if (kl == l && Arrays.equals(arena, ko, ko + l, b, o, e)) return idx;
                }
                pos = (pos + 1) & m;
            }
            return insert(b, o, l, hh, pos);
        }

        private int insert(byte[] b, int o, int l, int hh, int pos) {
            int idx = size;
            if (idx == keyPos.length) {
                int nc = idx * 2;
                keyPos = Arrays.copyOf(keyPos, nc);
                sum = Arrays.copyOf(sum, nc);
                cnt = Arrays.copyOf(cnt, nc);
            }
            if (arenaLen + l > arena.length) {
                arena = Arrays.copyOf(arena, Math.max(arena.length * 2, arenaLen + l));
            }
            System.arraycopy(b, o, arena, arenaLen, l);
            keyPos[idx] = ((long) arenaLen << 32) | l;
            arenaLen += l;
            slots[pos] = ((long) hh << 32) | (idx + 1);
            size = idx + 1;
            if (size * 2 > slots.length) rehash();
            return idx;
        }

        private void rehash() {
            long[] old = slots;
            int nc = old.length * 2;
            long[] ns = new long[nc];
            int m = nc - 1;
            for (long s : old) {
                if (s != 0) {
                    int pos = (int) (s >>> 32) & m;
                    while (ns[pos] != 0) pos = (pos + 1) & m;
                    ns[pos] = s;
                }
            }
            slots = ns;
            mask = m;
        }

        int off(int idx) {
            return (int) (keyPos[idx] >>> 32);
        }

        int len(int idx) {
            return (int) keyPos[idx];
        }

        String name(int idx) {
            return new String(arena, off(idx), len(idx), StandardCharsets.ISO_8859_1);
        }
    }

    private static final Table accounts = new Table(1 << 12);
    private static final Table channels = new Table(64);
    private static final Table currencies = new Table(64);

    private static long counted = 0;
    private static long net = 0;
    private static boolean ratesDone = false;

    // result of last readStr
    private static byte[] sB;
    private static int sOff;
    private static int sLen;
    private static byte[] scratch = new byte[256];
    private static int chRes = -1;

    // returns index of first '"' or '\\' at or after p
    private static int scanStr(byte[] b, int p) {
        while (true) {
            long w = (long) LONG.get(b, p);
            long x = w ^ QUOTES;
            long y = w ^ BSLASH;
            long m = ((x - ONES) & ~x | (y - ONES) & ~y) & HIGH;
            if (m != 0) return p + (Long.numberOfTrailingZeros(m) >>> 3);
            p += 8;
        }
    }

    // p is just after the opening quote; returns index just after the closing quote
    private static int skipStr(byte[] b, int p) {
        while (true) {
            p = scanStr(b, p);
            if (b[p] == '"') return p + 1;
            p += 2;
        }
    }

    // p is just after the opening quote; sets sB/sOff/sLen; returns index just after the closing quote
    private static int readStr(byte[] b, int p) {
        int e = scanStr(b, p);
        if (b[e] == '"') {
            sB = b;
            sOff = p;
            sLen = e - p;
            return e + 1;
        }
        return readStrSlow(b, p, e);
    }

    private static int hex(int c) {
        if (c <= '9') return c - '0';
        return (c | 0x20) - 'a' + 10;
    }

    private static int hex4(byte[] b, int i) {
        return hex(b[i]) << 12 | hex(b[i + 1]) << 8 | hex(b[i + 2]) << 4 | hex(b[i + 3]);
    }

    private static int readStrSlow(byte[] b, int p, int firstEsc) {
        int end = skipStr(b, firstEsc) - 1; // index of closing quote
        int raw = end - p;
        if (scratch.length < raw + 8) scratch = new byte[raw * 2 + 16];
        byte[] s = scratch;
        int n = 0;
        int i = p;
        while (i < end) {
            byte c = b[i++];
            if (c != '\\') {
                s[n++] = c;
                continue;
            }
            c = b[i++];
            switch (c) {
                case 'n': s[n++] = '\n'; break;
                case 't': s[n++] = '\t'; break;
                case 'r': s[n++] = '\r'; break;
                case 'b': s[n++] = '\b'; break;
                case 'f': s[n++] = '\f'; break;
                case 'u': {
                    int cp = hex4(b, i);
                    i += 4;
                    if (cp >= 0xD800 && cp <= 0xDBFF && i + 6 <= end && b[i] == '\\' && b[i + 1] == 'u') {
                        int lo = hex4(b, i + 2);
                        if (lo >= 0xDC00 && lo <= 0xDFFF) {
                            cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
                            i += 6;
                        }
                    }
                    if (cp < 0x80) {
                        s[n++] = (byte) cp;
                    } else if (cp < 0x800) {
                        s[n++] = (byte) (0xC0 | (cp >> 6));
                        s[n++] = (byte) (0x80 | (cp & 0x3F));
                    } else if (cp < 0x10000) {
                        s[n++] = (byte) (0xE0 | (cp >> 12));
                        s[n++] = (byte) (0x80 | ((cp >> 6) & 0x3F));
                        s[n++] = (byte) (0x80 | (cp & 0x3F));
                    } else {
                        s[n++] = (byte) (0xF0 | (cp >> 18));
                        s[n++] = (byte) (0x80 | ((cp >> 12) & 0x3F));
                        s[n++] = (byte) (0x80 | ((cp >> 6) & 0x3F));
                        s[n++] = (byte) (0x80 | (cp & 0x3F));
                    }
                    break;
                }
                default:
                    s[n++] = c; // '"', '\\', '/'
            }
        }
        sB = s;
        sOff = 0;
        sLen = n;
        return end + 1;
    }

    private static boolean delim(byte c) {
        return c == ',' || c == '}' || c == ']' || c <= ' ';
    }

    // p is just after the opening bracket; returns index just after the matching close
    private static int skipContainer(byte[] b, int p) {
        int depth = 1;
        while (true) {
            byte c = b[p++];
            if (c == '"') {
                p = skipStr(b, p);
            } else {
                int k = c | 0x20;
                if (k == 0x7B) {
                    depth++;
                } else if (k == 0x7D) {
                    if (--depth == 0) return p;
                }
            }
        }
    }

    private static int skipValue(byte[] b, int p) {
        byte c = b[p];
        if (c == '"') return skipStr(b, p + 1);
        if (c == '{' || c == '[') return skipContainer(b, p + 1);
        p++;
        while (!delim(b[p])) p++;
        return p;
    }

    private static int nextLine(byte[] b, int p) {
        while (true) {
            long w = (long) LONG.get(b, p) ^ NEWLINES;
            long m = (w - ONES) & ~w & HIGH;
            if (m != 0) return p + (Long.numberOfTrailingZeros(m) >>> 3) + 1;
            p += 8;
        }
    }

    private static boolean eq(byte[] b, int o, byte[] lit) {
        for (int i = 0; i < lit.length; i++) {
            if (b[o + i] != lit[i]) return false;
        }
        return true;
    }

    // p just after '['; returns index after ']' or -1 if a tag equals "test"
    private static int parseTags(byte[] b, int p) {
        while (true) {
            while (b[p] <= ' ') p++;
            byte c = b[p];
            if (c == '"') {
                p = readStr(b, p + 1);
                if (sLen == 4) {
                    byte[] s = sB;
                    int o = sOff;
                    if (s[o] == 't' && s[o + 1] == 'e' && s[o + 2] == 's' && s[o + 3] == 't') return -1;
                }
            } else if (c == ',') {
                p++;
            } else if (c == ']') {
                return p + 1;
            } else {
                p = skipValue(b, p);
            }
        }
    }

    // p just after '{'; sets chRes; returns a position inside the line at or after the end of meta
    // (when 'last' is true it may return early, the caller then jumps to the next line)
    private static int parseMeta(byte[] b, int p, boolean last) {
        chRes = -1;
        while (true) {
            while (b[p] <= ' ') p++;
            byte c = b[p];
            if (c == '"') {
                p = readStr(b, p + 1);
                boolean isCh = sLen == 7 && eq(sB, sOff, CHANNEL);
                while (b[p] <= ' ') p++;
                p++;
                while (b[p] <= ' ') p++;
                if (isCh && b[p] == '"') {
                    p = readStr(b, p + 1);
                    chRes = channels.get(sB, sOff, sLen);
                    if (last) return p;
                    return skipContainer(b, p);
                }
                p = skipValue(b, p);
            } else if (c == ',') {
                p++;
            } else {
                return p + 1;
            }
        }
    }

    // p just after the top-level '{' of the first line; returns start of next line
    private static int parseRates(byte[] b, int p) {
        final Table cur = currencies;
        while (true) {
            while (b[p] <= ' ') p++;
            byte c = b[p];
            if (c == '"') {
                p = readStr(b, p + 1);
                boolean isRates = sLen == 5 && eq(sB, sOff, RATES);
                while (b[p] <= ' ') p++;
                p++;
                while (b[p] <= ' ') p++;
                if (isRates && b[p] == '{') {
                    p++;
                    while (true) {
                        while (b[p] <= ' ') p++;
                        c = b[p];
                        if (c == '"') {
                            p = readStr(b, p + 1);
                            int idx = cur.get(sB, sOff, sLen);
                            while (b[p] <= ' ') p++;
                            p++;
                            while (b[p] <= ' ') p++;
                            boolean neg = false;
                            if (b[p] == '-') {
                                neg = true;
                                p++;
                            }
                            long v = 0;
                            while ((c = b[p]) >= '0' && c <= '9') {
                                v = v * 10 + (c - '0');
                                p++;
                            }
                            while (!delim(b[p])) p++;
                            cur.sum[idx] = neg ? -v : v;
                        } else if (c == ',') {
                            p++;
                        } else {
                            p++;
                            break;
                        }
                    }
                } else {
                    p = skipValue(b, p);
                }
            } else if (c == ',') {
                p++;
            } else {
                break;
            }
        }
        return nextLine(b, p);
    }

    private static void process(byte[] b, int p, int end) {
        final Table accT = accounts, curT = currencies, chT = channels;
        long cnt = counted, nt = net;
        boolean rd = ratesDone;
        while (true) {
            while (p < end && b[p] != '{') p++;
            if (p >= end) break;
            p++;
            if (!rd) {
                rd = true;
                p = parseRates(b, p);
                continue;
            }
            int seen = 0, sign = 1, acc = -1, ch = -1;
            long hund = 0, rate = 0;
            boolean skip = false;
            while (true) {
                byte c;
                while ((c = b[p]) <= ' ') p++;
                if (c == '"') {
                    p = readStr(b, p + 1);
                    final byte[] kb = sB;
                    final int ko = sOff, kl = sLen;
                    while (b[p] <= ' ') p++;
                    p++;
                    while (b[p] <= ' ') p++;
                    int f = 0;
                    switch (kl) {
                        case 4: {
                            byte k0 = kb[ko];
                            if (k0 == 't') {
                                byte k1 = kb[ko + 1];
                                if (k1 == 'y') {
                                    if (kb[ko + 2] == 'p' && kb[ko + 3] == 'e') f = 1;
                                } else if (k1 == 'a') {
                                    if (kb[ko + 2] == 'g' && kb[ko + 3] == 's') f = 16;
                                }
                            } else if (k0 == 'm' && kb[ko + 1] == 'e' && kb[ko + 2] == 't' && kb[ko + 3] == 'a') {
                                f = 32;
                            }
                            break;
                        }
                        case 6:
                            if (eq(kb, ko, AMOUNT)) f = 2;
                            break;
                        case 7:
                            if (eq(kb, ko, ACCOUNT)) f = 8;
                            break;
                        case 8:
                            if (eq(kb, ko, CURRENCY)) f = 4;
                            break;
                        default:
                            break;
                    }
                    c = b[p];
                    if (f == 0) {
                        p = skipValue(b, p);
                        continue;
                    }
                    if (f <= 8) {
                        if (c != '"') {
                            p = skipValue(b, p);
                            continue;
                        }
                        p = readStr(b, p + 1);
                        final byte[] vb = sB;
                        final int vo = sOff, vl = sLen;
                        if (f == 1) {
                            if (vl == 4 && vb[vo] == 'v' && vb[vo + 1] == 'o' && vb[vo + 2] == 'i' && vb[vo + 3] == 'd') {
                                skip = true;
                            } else {
                                sign = (vl == 5 && vb[vo] == 'd') ? -1 : 1;
                            }
                        } else if (f == 2) {
                            long v = 0;
                            int i = vo;
                            final int e = vo + vl;
                            byte d;
                            while (i < e && (d = vb[i]) != '.') {
                                v = v * 10 + (d - '0');
                                i++;
                            }
                            v *= 100;
                            if (i < e) {
                                i++;
                                int fd = e - i;
                                if (fd >= 1) v += (vb[i] - '0') * 10;
                                if (fd >= 2) v += (vb[i + 1] - '0');
                            }
                            hund = v;
                        } else if (f == 4) {
                            rate = curT.sum[curT.get(vb, vo, vl)];
                        } else {
                            acc = accT.get(vb, vo, vl);
                        }
                    } else if (f == 16) {
                        if (c != '[') {
                            p = skipValue(b, p);
                            continue;
                        }
                        int q = parseTags(b, p + 1);
                        if (q < 0) {
                            skip = true;
                        } else {
                            p = q;
                        }
                    } else {
                        if (c != '{') {
                            p = skipValue(b, p);
                            continue;
                        }
                        p = parseMeta(b, p + 1, (seen | 32) == 63);
                        ch = chRes;
                    }
                    seen |= f;
                    if (skip || seen == 63) break;
                } else if (c == ',') {
                    p++;
                } else {
                    break;
                }
            }
            p = nextLine(b, p);
            if (!skip) {
                long usd = hund * rate / 1000000L;
                long v = sign < 0 ? -usd : usd;
                cnt++;
                nt += v;
                if (ch >= 0) {
                    chT.cnt[ch]++;
                    chT.sum[ch] += v;
                }
                if (acc >= 0) {
                    accT.cnt[acc] = 1;
                    accT.sum[acc] += v;
                }
            }
        }
        counted = cnt;
        net = nt;
        ratesDone = rd;
    }

    private static boolean better(Table t, int a, int b) {
        long sa = t.sum[a], sb = t.sum[b];
        if (sa != sb) return sa > sb;
        int oa = t.off(a), la = t.len(a), ob = t.off(b), lb = t.len(b);
        return Arrays.compareUnsigned(t.arena, oa, oa + la, t.arena, ob, ob + lb) < 0;
    }

    public static void main(String[] args) throws Exception {
        byte[] buf = new byte[CHUNK + 8];
        int len = 0;
        try (FileInputStream in = new FileInputStream(args[0])) {
            while (true) {
                int free = buf.length - 8 - len;
                if (free < 65536) {
                    buf = Arrays.copyOf(buf, (buf.length - 8) * 2 + 8);
                    free = buf.length - 8 - len;
                }
                int n = in.read(buf, len, free);
                if (n < 0) {
                    if (len > 0) {
                        if (buf[len - 1] != '\n') buf[len++] = '\n';
                        process(buf, 0, len);
                    }
                    break;
                }
                int lo = len;
                len += n;
                int last = len - 1;
                while (last >= lo && buf[last] != '\n') last--;
                if (last < lo) continue;
                int end = last + 1;
                process(buf, 0, end);
                int rem = len - end;
                if (rem > 0) System.arraycopy(buf, end, buf, 0, rem);
                len = rem;
            }
        }

        StringBuilder sb = new StringBuilder(1024);
        sb.append("counted ").append(counted).append('\n');
        sb.append("net ").append(net).append('\n');

        final Table ct = channels;
        int nc = 0;
        Integer[] chIdx = new Integer[ct.size];
        for (int i = 0; i < ct.size; i++) {
            if (ct.cnt[i] > 0) chIdx[nc++] = i;
        }
        Arrays.sort(chIdx, 0, nc, (x, y) -> {
            int ox = ct.off(x), lx = ct.len(x), oy = ct.off(y), ly = ct.len(y);
            return Arrays.compareUnsigned(ct.arena, ox, ox + lx, ct.arena, oy, oy + ly);
        });
        for (int i = 0; i < nc; i++) {
            int idx = chIdx[i];
            sb.append("channel ").append(ct.name(idx)).append(' ')
                    .append(ct.cnt[idx]).append(' ').append(ct.sum[idx]).append('\n');
        }

        final Table at = accounts;
        int[] top = new int[10];
        int k = 0;
        for (int i = 0; i < at.size; i++) {
            if (at.cnt[i] == 0) continue;
            if (k == 10 && !better(at, i, top[9])) continue;
            int j = (k < 10) ? k++ : 9;
            while (j > 0 && better(at, i, top[j - 1])) {
                top[j] = top[j - 1];
                j--;
            }
            top[j] = i;
        }
        for (int i = 0; i < k; i++) {
            int idx = top[i];
            sb.append("account ").append(at.name(idx)).append(' ').append(at.sum[idx]).append('\n');
        }

        FileOutputStream out = new FileOutputStream(FileDescriptor.out);
        out.write(sb.toString().getBytes(StandardCharsets.ISO_8859_1));
        out.flush();
    }
}
