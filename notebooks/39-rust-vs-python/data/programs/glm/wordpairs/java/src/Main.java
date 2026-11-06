import java.io.*;
import java.nio.file.*;

public class Main {
    // ---- word table: open addressing, ids into a byte arena ----
    static int[] wSlot;   // id+1, 0 = empty
    static int[] wHash;
    static int[] wOff;
    static int[] wLen;
    static byte[] wArena;
    static int wArenaLen = 0;
    static int wMask, wCount = 0;

    static void wInit(int cap) {
        int c = 1 << 16;
        wSlot = new int[c];
        wHash = new int[c];
        wMask = c - 1;
        wOff = new int[256];
        wLen = new int[256];
        wArena = new byte[1 << 16];
    }

    static void wGrow() {
        int cap = wMask + 1, cap2 = cap * 2;
        int[] s2 = new int[cap2], h2 = new int[cap2];
        int m2 = cap2 - 1;
        for (int i = 0; i < cap; i++) {
            if (wSlot[i] != 0) {
                int j = wHash[i] & m2;
                while (s2[j] != 0) j = (j + 1) & m2;
                s2[j] = wSlot[i];
                h2[j] = wHash[i];
            }
        }
        wSlot = s2;
        wHash = h2;
        wMask = m2;
    }

    static int wordFindOrAdd(byte[] w, int n, int h) {
        int i = h & wMask;
        while (wSlot[i] != 0) {
            int id = wSlot[i] - 1;
            if (wHash[i] == h && wLen[id] == n && regionEquals(id, w, n)) return id;
            i = (i + 1) & wMask;
        }
        if ((long)(wCount + 1) * 3 > (long)(wMask + 1) * 2) {
            wGrow();
            i = h & wMask;
            while (wSlot[i] != 0) i = (i + 1) & wMask;
        }
        int id = wCount++;
        int o = wArenaLen;
        if (wArenaLen + n > wArena.length) {
            int nc = wArena.length;
            while (wArenaLen + n > nc) nc *= 2;
            byte[] a2 = new byte[nc];
            System.arraycopy(wArena, 0, a2, 0, wArenaLen);
            wArena = a2;
        }
        System.arraycopy(w, 0, wArena, wArenaLen, n);
        wArenaLen += n;
        if (id == wOff.length) {
            wOff = java.util.Arrays.copyOf(wOff, id * 2);
            wLen = java.util.Arrays.copyOf(wLen, id * 2);
        }
        wOff[id] = o;
        wLen[id] = n;
        wSlot[i] = id + 1;
        wHash[i] = h;
        return id;
    }

    static boolean regionEquals(int id, byte[] w, int n) {
        int o = wOff[id];
        for (int i = 0; i < n; i++)
            if (wArena[o + i] != w[i]) return false;
        return true;
    }

    static int cmpWords(int a, int b) {
        int la = wLen[a], lb = wLen[b];
        int oa = wOff[a], ob = wOff[b];
        int m = Math.min(la, lb);
        for (int i = 0; i < m; i++) {
            int d = (wArena[oa + i] & 0xFF) - (wArena[ob + i] & 0xFF);
            if (d != 0) return d;
        }
        return la - lb;
    }

    // ---- pair table: open addressing on packed (id1,id2) ----
    static long[] pKey;
    static int[] pCnt;
    static long pMask, pCount = 0;
    static final long PEMPTY = -1L;

    static long mixKey(long x) {
        x *= 0x9E3779B97F4A7C15L;
        x ^= x >>> 32;
        x *= 0xBF58476D1CE4E5B9L;
        x ^= x >>> 29;
        return x;
    }

    static void pGrow() {
        long cap = pMask + 1, cap2 = cap * 2, m2 = cap2 - 1;
        long[] k2 = new long[(int)cap2];
        int[] c2 = new int[(int)cap2];
        java.util.Arrays.fill(k2, PEMPTY);
        for (int i = 0; i < (int)cap; i++) {
            if (pKey[i] != PEMPTY) {
                int j = (int)(mixKey(pKey[i]) & m2);
                while (k2[j] != PEMPTY) j = (int)((j + 1) & m2);
                k2[j] = pKey[i];
                c2[j] = pCnt[i];
            }
        }
        pKey = k2;
        pCnt = c2;
        pMask = m2;
    }

    static void pairAdd(long key) {
        int i = (int)(mixKey(key) & pMask);
        while (pKey[i] != PEMPTY) {
            if (pKey[i] == key) {
                pCnt[i]++;
                return;
            }
            i = (i + 1) & (int)pMask;
        }
        if ((pCount + 1) * 3 > (pMask + 1) * 2) {
            pGrow();
            i = (int)(mixKey(key) & pMask);
            while (pKey[i] != PEMPTY) i = (i + 1) & (int)pMask;
        }
        pKey[i] = key;
        pCnt[i] = 1;
        pCount++;
    }

    static int hashBytes(byte[] w, int n) {
        int h = (int)2166136261L;
        for (int i = 0; i < n; i++) {
            h ^= w[i] & 0xFF;
            h *= 16777619;
        }
        return h == 0 ? 1 : h;
    }

    static long totalWords = 0, totalPairs = 0;

    public static void main(String[] args) throws IOException {
        if (args.length < 1) return;
        byte[] data = Files.readAllBytes(Paths.get(args[0]));
        int n = data.length;
        wInit(0);
        pKey = new long[1 << 20];
        java.util.Arrays.fill(pKey, PEMPTY);
        pCnt = new int[1 << 20];
        pMask = (1 << 20) - 1;

        byte[] wbuf = new byte[64];
        int wl = 0;
        int prev = -1;

        for (int i = 0; i < n; i++) {
            int c = data[i] & 0xFF;
            int lc = c | 0x20;
            if (lc - 'a' < 26 && lc >= 'a') {
                if (wl == wbuf.length) {
                    byte[] b2 = new byte[wbuf.length * 2];
                    System.arraycopy(wbuf, 0, b2, 0, wl);
                    wbuf = b2;
                }
                wbuf[wl++] = (byte)lc;
            } else {
                if (wl > 0) {
                    totalWords++;
                    int id = wordFindOrAdd(wbuf, wl, hashBytes(wbuf, wl));
                    if (prev >= 0) {
                        totalPairs++;
                        pairAdd(((long)prev << 32) | id);
                    }
                    prev = id;
                    wl = 0;
                }
                if (c == '.' || c == '!' || c == '?') prev = -1;
            }
        }
        if (wl > 0) {
            totalWords++;
            int id = wordFindOrAdd(wbuf, wl, hashBytes(wbuf, wl));
            if (prev >= 0) {
                totalPairs++;
                pairAdd(((long)prev << 32) | id);
            }
        }

        // collect top 20 with a bounded min-heap
        int hc = 0;
        int[] hCnt = new int[21], hId1 = new int[21], hId2 = new int[21];
        for (int i = 0; i < (int)(pMask + 1); i++) {
            if (pKey[i] == PEMPTY) continue;
            int c1 = pCnt[i];
            int id1 = (int)(pKey[i] >>> 32), id2 = (int)pKey[i];
            if (hc < 20) {
                // insert
                int p = hc++;
                hCnt[p] = c1; hId1[p] = id1; hId2[p] = id2;
                while (p > 0) {
                    int par = (p - 1) / 2;
                    // heap property: parent must be worse than children; bubble up a worse child
                    if (worse(hCnt[p], hId1[p], hId2[p], hCnt[par], hId1[par], hId2[par]) <= 0) break;
                    swap(hCnt, hId1, hId2, p, par);
                    p = par;
                }
            } else if (worse(c1, id1, id2, hCnt[0], hId1[0], hId2[0]) < 0) {
                // replace root, sift down
                hCnt[0] = c1; hId1[0] = id1; hId2[0] = id2;
                siftDown(hCnt, hId1, hId2, hc);
            }
        }

        // pop heap into array (worst first), then sort best-first
        int m = hc;
        int[] rCnt = new int[m], rId1 = new int[m], rId2 = new int[m];
        for (int idx = m - 1; idx >= 0; idx--) {
            rCnt[idx] = hCnt[0]; rId1[idx] = hId1[0]; rId2[idx] = hId2[0];
            hc--;
            hCnt[0] = hCnt[hc]; hId1[0] = hId1[hc]; hId2[0] = hId2[hc];
            siftDown(hCnt, hId1, hId2, hc);
        }
        // insertion sort (m <= 20), best first
        for (int a = 1; a < m; a++) {
            int c = rCnt[a], i1 = rId1[a], i2 = rId2[a];
            int b = a - 1;
            while (b >= 0 && worse(rCnt[b], rId1[b], rId2[b], c, i1, i2) > 0) {
                rCnt[b + 1] = rCnt[b]; rId1[b + 1] = rId1[b]; rId2[b + 1] = rId2[b];
                b--;
            }
            rCnt[b + 1] = c; rId1[b + 1] = i1; rId2[b + 1] = i2;
        }

        // output
        ByteArrayOutputStream bo = new ByteArrayOutputStream(4096);
        BufferedWriter bw = new BufferedWriter(new OutputStreamWriter(bo, java.nio.charset.StandardCharsets.ISO_8859_1), 8192);
        bw.write("words " + totalWords + "\n");
        bw.write("pairs " + totalPairs + "\n");
        bw.write("distinct " + pCount + "\n");
        for (int idx = 0; idx < m; idx++) {
            bw.write(Integer.toString(rCnt[idx]));
            bw.write(' ');
            bw.write(new String(wArena, wOff[rId1[idx]], wLen[rId1[idx]], java.nio.charset.StandardCharsets.ISO_8859_1));
            bw.write(' ');
            bw.write(new String(wArena, wOff[rId2[idx]], wLen[rId2[idx]], java.nio.charset.StandardCharsets.ISO_8859_1));
            bw.write('\n');
        }
        bw.flush();
        System.out.write(bo.toByteArray());
        System.out.flush();
    }

    // negative if (c1,w1) ranks better (earlier in output) than (c2,w2)
    static int worse(int c1, int i1a, int i1b, int c2, int i2a, int i2b) {
        if (c1 != c2) return c2 - c1;
        int d = cmpWords(i1a, i2a);
        if (d != 0) return d;
        return cmpWords(i1b, i2b);
    }

    // heap holds the worst element at the root; push it down among its children
    static void siftDown(int[] hCnt, int[] hId1, int[] hId2, int size) {
        int p = 0;
        while (true) {
            int l = 2 * p + 1, r = l + 1, s = p;
            if (l < size && worse(hCnt[l], hId1[l], hId2[l], hCnt[s], hId1[s], hId2[s]) > 0) s = l;
            if (r < size && worse(hCnt[r], hId1[r], hId2[r], hCnt[s], hId1[s], hId2[s]) > 0) s = r;
            if (s == p) break;
            swap(hCnt, hId1, hId2, p, s);
            p = s;
        }
    }

    static void swap(int[] a, int[] b, int[] c, int i, int j) {
        int t = a[i]; a[i] = a[j]; a[j] = t;
        t = b[i]; b[i] = b[j]; b[j] = t;
        t = c[i]; c[i] = c[j]; c[j] = t;
    }
}
