import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;

public class Main {
    static final long C = 0x9E3779B97F4A7C15L;
    static final long SENT = (1L << '.') | (1L << '!') | (1L << '?');

    // table for words of length <= 12: interleaved [packedKey, id]
    static long[] stab = new long[1 << 18];
    static int sShift = 64 - 17;
    static int sSize = 0;

    // table for words of length > 12: ids
    static int[] ltab = new int[1 << 12];
    static int lShift = 64 - 12;
    static int lSize = 0;
    static byte[] store = new byte[1 << 16];
    static int storeLen = 0;

    // per-id data (ids start at 1)
    static int vocab = 0;
    static long[] idSort = new long[1 << 16];
    static long[] idHash = new long[1 << 16];
    static int[] idOff = new int[1 << 16];
    static int[] idLen = new int[1 << 16];

    // id stream (0 = sentence break)
    static int[] ids;
    static int cnt = 0;
    static int last = 0;
    static long words = 0;

    // top 20
    static int topN = 0, thr = 0;
    static final int[] topCnt = new int[20], topF = new int[20], topS = new int[20];
    static long totalPairs = 0, distinct = 0;

    public static void main(String[] args) throws IOException {
        File f = new File(args[0]);
        long size = f.length();
        ids = new int[(int) Math.min(1L << 30, Math.max(4096L, size / 5 + 4096))];
        byte[] buf = new byte[(1 << 17) + 1];
        int have = 0;
        boolean eof = false;
        try (FileInputStream in = new FileInputStream(f)) {
            while (!eof) {
                int capNow = buf.length - 1;
                while (have < capNow) {
                    int r = in.read(buf, have, capNow - have);
                    if (r < 0) {
                        eof = true;
                        break;
                    }
                    have += r;
                }
                int limit;
                if (eof) {
                    buf[have] = '\n';
                    limit = have + 1;
                } else {
                    int p = have - 1;
                    while (p >= 0 && (char) ((buf[p] | 0x20) - 'a') < 26) p--;
                    if (p < 0) {
                        buf = Arrays.copyOf(buf, capNow * 2 + 1);
                        continue;
                    }
                    limit = p + 1;
                }
                if (cnt + limit + 1 > ids.length) {
                    ids = Arrays.copyOf(ids, Math.max(ids.length + (ids.length >> 1), cnt + limit + 1));
                }
                process(buf, limit);
                if (!eof) {
                    int rem = have - limit;
                    if (rem > 0) System.arraycopy(buf, limit, buf, 0, rem);
                    have = rem;
                }
            }
        }

        final int V = vocab;
        final int n = cnt;
        final int[] seq = ids;
        int[] pos = new int[V + 2];
        countFirst(seq, n, pos);
        int sum = 0;
        for (int i = 0; i < pos.length; i++) {
            sum += pos[i];
            pos[i] = sum;
        }
        int[] out = new int[n];
        scatter(seq, n, pos, out);
        groups(out, pos, V);

        StringBuilder sb = new StringBuilder(1024);
        sb.append("words ").append(words).append('\n');
        sb.append("pairs ").append(totalPairs).append('\n');
        sb.append("distinct ").append(distinct).append('\n');
        for (int i = 0; i < topN; i++) {
            sb.append(topCnt[i]).append(' ').append(word(topF[i])).append(' ').append(word(topS[i])).append('\n');
        }
        byte[] o = sb.toString().getBytes(StandardCharsets.US_ASCII);
        System.out.write(o, 0, o.length);
        System.out.flush();
    }

    static void countFirst(int[] seq, int n, int[] pos) {
        int prev = 0;
        for (int j = 0; j < n; j++) {
            pos[prev + 1]++;
            prev = seq[j];
        }
    }

    static void scatter(int[] seq, int n, int[] pos, int[] out) {
        int prev = 0;
        for (int j = 0; j < n; j++) {
            int cur = seq[j];
            out[pos[prev]++] = cur;
            prev = cur;
        }
    }

    static void groups(int[] out, int[] pos, int V) {
        int[] c = new int[V + 1];
        long T = 0, D = 0;
        int s = pos[0];
        for (int f = 1; f <= V; f++) {
            int e = pos[f];
            for (int i = s; i < e; i++) c[out[i]]++;
            for (int i = s; i < e; i++) {
                int x = out[i];
                int m = c[x];
                if (m != 0) {
                    c[x] = 0;
                    if (x != 0) {
                        D++;
                        T += m;
                        if (m >= thr) offer(m, f, x);
                    }
                }
            }
            s = e;
        }
        totalPairs = T;
        distinct = D;
    }

    static void offer(int n, int f, int x) {
        int p;
        if (topN == 20) {
            if (n < topCnt[19] || (n == topCnt[19] && cmpPair(f, x, topF[19], topS[19]) > 0)) return;
            p = 19;
        } else {
            p = topN++;
        }
        while (p > 0 && (topCnt[p - 1] < n
                || (topCnt[p - 1] == n && cmpPair(f, x, topF[p - 1], topS[p - 1]) < 0))) {
            topCnt[p] = topCnt[p - 1];
            topF[p] = topF[p - 1];
            topS[p] = topS[p - 1];
            p--;
        }
        topCnt[p] = n;
        topF[p] = f;
        topS[p] = x;
        thr = topN == 20 ? topCnt[19] : 0;
    }

    static int cmpPair(int f1, int s1, int f2, int s2) {
        int r = cmpWord(f1, f2);
        if (r != 0) return r;
        return cmpWord(s1, s2);
    }

    static int cmpWord(int a, int b) {
        if (a == b) return 0;
        long x = idSort[a], y = idSort[b];
        if (x != y) return x < y ? -1 : 1;
        return word(a).compareTo(word(b));
    }

    static String word(int id) {
        int off = idOff[id];
        if (off >= 0) return new String(store, off, idLen[id], StandardCharsets.ISO_8859_1);
        long sk = idSort[id];
        StringBuilder sb = new StringBuilder(12);
        for (int shift = 55; shift >= 0; shift -= 5) {
            int d = (int) (sk >>> shift) & 31;
            if (d == 0) break;
            sb.append((char) ('a' + d - 1));
        }
        return sb.toString();
    }

    static void process(byte[] buf, int limit) {
        long[] tab = stab;
        int shift = sShift;
        int mask = tab.length - 1;
        int[] out = ids;
        int n = cnt;
        int lst = last;
        long w = 0;
        int i = 0;
        while (i < limit) {
            int c = buf[i++];
            int l = (c | 0x20) - 'a';
            if ((char) l < 26) {
                int start = i - 1;
                long k = l + 1;
                for (;;) {
                    l = (buf[i] | 0x20) - 'a';
                    if ((char) l >= 26) break;
                    k = Long.rotateLeft(k, 5) ^ (long) (l + 1);
                    i++;
                }
                int len = i - start;
                int id;
                if (len <= 12) {
                    int p = (int) ((k * C) >>> shift) << 1;
                    for (;;) {
                        long sk = tab[p];
                        if (sk == k) {
                            id = (int) tab[p + 1];
                            break;
                        }
                        if (sk == 0L) {
                            id = insertShort(k, len, p);
                            tab = stab;
                            shift = sShift;
                            mask = tab.length - 1;
                            break;
                        }
                        p = (p + 2) & mask;
                    }
                } else {
                    id = lookupLong(buf, start, len, k);
                }
                out[n++] = id;
                lst = id;
                w++;
            } else if ((c & ~63) == 0 && ((SENT >>> c) & 1L) != 0) {
                if (lst != 0) {
                    out[n++] = 0;
                    lst = 0;
                }
            }
        }
        cnt = n;
        last = lst;
        words += w;
    }

    static int newId() {
        int id = ++vocab;
        if (id >= idSort.length) {
            int nl = idSort.length * 2;
            idSort = Arrays.copyOf(idSort, nl);
            idHash = Arrays.copyOf(idHash, nl);
            idOff = Arrays.copyOf(idOff, nl);
            idLen = Arrays.copyOf(idLen, nl);
        }
        return id;
    }

    static int insertShort(long k, int len, int p) {
        int id = newId();
        idSort[id] = k << (60 - 5 * len);
        idOff[id] = -1;
        idLen[id] = len;
        long[] tab = stab;
        tab[p] = k;
        tab[p + 1] = id;
        if (++sSize * 2 > (tab.length >> 1)) growShort();
        return id;
    }

    static void growShort() {
        long[] old = stab;
        long[] nt = new long[old.length << 1];
        int shift = sShift - 1;
        int mask = nt.length - 1;
        for (int q = 0; q < old.length; q += 2) {
            long k = old[q];
            if (k != 0L) {
                int p = (int) ((k * C) >>> shift) << 1;
                while (nt[p] != 0L) p = (p + 2) & mask;
                nt[p] = k;
                nt[p + 1] = old[q + 1];
            }
        }
        stab = nt;
        sShift = shift;
    }

    static int lookupLong(byte[] buf, int start, int len, long k) {
        int[] tab = ltab;
        int mask = tab.length - 1;
        int p = (int) ((k * C) >>> lShift);
        long[] hs = idHash;
        int[] lens = idLen;
        for (;;) {
            int cand = tab[p];
            if (cand == 0) break;
            if (hs[cand] == k && lens[cand] == len && eq(buf, start, idOff[cand], len)) return cand;
            p = (p + 1) & mask;
        }
        int id = newId();
        long sk = 0;
        for (int j = 0; j < 12; j++) {
            sk = (sk << 5) | (long) (((buf[start + j] | 0x20) - 'a') + 1);
        }
        idSort[id] = sk;
        idHash[id] = k;
        idOff[id] = storeLen;
        idLen[id] = len;
        if (storeLen + len > store.length) {
            store = Arrays.copyOf(store, Math.max(store.length * 2, storeLen + len));
        }
        byte[] st = store;
        int base = storeLen;
        for (int j = 0; j < len; j++) st[base + j] = (byte) (buf[start + j] | 0x20);
        storeLen = base + len;
        tab[p] = id;
        if (++lSize * 2 > tab.length) growLong();
        return id;
    }

    static boolean eq(byte[] buf, int start, int off, int len) {
        byte[] st = store;
        for (int j = 0; j < len; j++) {
            if ((buf[start + j] | 0x20) != st[off + j]) return false;
        }
        return true;
    }

    static void growLong() {
        int[] old = ltab;
        int[] nt = new int[old.length << 1];
        int shift = lShift - 1;
        int mask = nt.length - 1;
        for (int q = 0; q < old.length; q++) {
            int id = old[q];
            if (id != 0) {
                int p = (int) ((idHash[id] * C) >>> shift);
                while (nt[p] != 0) p = (p + 1) & mask;
                nt[p] = id;
            }
        }
        ltab = nt;
        lShift = shift;
    }
}
