import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;

// Word pairs: count adjacent word pairs within sentences, report totals and top 20.
public class Main {

    // Open-addressing map: long key -> int count. cnt == 0 marks an empty slot.
    static long[] pKeys;
    static int[] pCnt;
    static long pMask;
    static long pFilled;

    // Word interning: words live in the (lowercased) input buffer.
    static byte[] buf;
    static int[] wTab;   // slot -> id + 1
    static int[] wOff, wLen, wHsh;
    static long wMask;
    static int wCount;

    static long words, pairs;

    static boolean isLetter(int c) {
        return (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z');
    }

    public static void main(String[] args) throws IOException {
        buf = Files.readAllBytes(Paths.get(args[0]));
        int n = buf.length;
        for (int i = 0; i < n; i++) {
            byte c = buf[i];
            if (c >= 'A' && c <= 'Z') buf[i] = (byte) (c + 32);
        }

        int ps = 1 << 20;
        while (ps < n / 8) ps <<= 1; // distinct pairs scale with input size; avoid rehashing
        pKeys = new long[ps];
        pCnt = new int[ps];
        pMask = ps - 1;
        pFilled = 0;

        wTab = new int[1 << 16];
        wMask = (1 << 16) - 1;
        wOff = new int[1 << 16];
        wLen = new int[1 << 16];
        wHsh = new int[1 << 16];
        wCount = 0;

        int prev = -1; // no previous word in current sentence
        int i = 0;
        while (i < n) {
            int c = buf[i] & 0xff;
            if ((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z')) {
                int start = i;
                int h = 0x811C9DC5;
                do {
                    h = (h ^ (buf[i] & 0xff)) * 0x01000193;
                    i++;
                } while (i < n && isLetter(buf[i] & 0xff));
                int id = intern(start, i - start, h);
                words++;
                if (prev >= 0) {
                    addPair(((long) prev << 32) | id);
                    pairs++;
                }
                prev = id;
            } else {
                if (c == '.' || c == '!' || c == '?') prev = -1;
                i++;
            }
        }

        // Keep the 20 best pairs in a min-heap while scanning the pair table.
        long[] hKey = new long[20];
        int[] hCnt = new int[20];
        int hn = 0;
        for (long j = 0; j <= pMask; j++) {
            int cnt = pCnt[(int) j];
            if (cnt == 0) continue;
            long key = pKeys[(int) j];
            if (hn < 20) {
                int k = hn++;
                hKey[k] = key;
                hCnt[k] = cnt;
                while (k > 0) {
                    int p = (k - 1) / 2;
                    if (worse(key, cnt, hKey[p], hCnt[p])) {
                        long tk = hKey[p]; hKey[p] = hKey[k]; hKey[k] = tk;
                        int tc = hCnt[p]; hCnt[p] = hCnt[k]; hCnt[k] = tc;
                        k = p;
                    } else break;
                }
            } else if (worse(hKey[0], hCnt[0], key, cnt)) {
                hKey[0] = key;
                hCnt[0] = cnt;
                int k = 0;
                for (;;) {
                    int l = 2 * k + 1, r = l + 1, m = k;
                    if (l < hn && worse(hKey[l], hCnt[l], hKey[m], hCnt[m])) m = l;
                    if (r < hn && worse(hKey[r], hCnt[r], hKey[m], hCnt[m])) m = r;
                    if (m == k) break;
                    long tk = hKey[m]; hKey[m] = hKey[k]; hKey[k] = tk;
                    int tc = hCnt[m]; hCnt[m] = hCnt[k]; hCnt[k] = tc;
                    k = m;
                }
            }
        }
        // Selection sort of the <=20 entries: count desc, then words asc.
        for (int a = 0; a < hn; a++) {
            int best = a;
            for (int b = a + 1; b < hn; b++) {
                if (hCnt[b] > hCnt[best]
                        || (hCnt[b] == hCnt[best] && cmpWords(hKey[b], hKey[best]) < 0)) {
                    best = b;
                }
            }
            if (best != a) {
                long tk = hKey[a]; hKey[a] = hKey[best]; hKey[best] = tk;
                int tc = hCnt[a]; hCnt[a] = hCnt[best]; hCnt[best] = tc;
            }
        }

        StringBuilder sb = new StringBuilder(64 + hn * 48);
        sb.append("words ").append(words).append('\n');
        sb.append("pairs ").append(pairs).append('\n');
        sb.append("distinct ").append(pFilled).append('\n');
        for (int k = 0; k < hn; k++) {
            long key = hKey[k];
            int w1 = (int) (key >>> 32), w2 = (int) key;
            sb.append(hCnt[k]).append(' ');
            sb.append(new String(buf, wOff[w1], wLen[w1], java.nio.charset.StandardCharsets.ISO_8859_1));
            sb.append(' ');
            sb.append(new String(buf, wOff[w2], wLen[w2], java.nio.charset.StandardCharsets.ISO_8859_1));
            sb.append('\n');
        }
        System.out.print(sb);
        System.out.flush();
    }

    static boolean worse(long ka, int ca, long kb, int cb) {
        if (ca != cb) return ca < cb;
        return cmpWords(ka, kb) > 0;
    }

    static int cmpWords(long a, long b) {
        int c = cmpWord((int) (a >>> 32), (int) (b >>> 32));
        if (c != 0) return c;
        return cmpWord((int) a, (int) b);
    }

    static int cmpWord(int a, int b) {
        int o1 = wOff[a], l1 = wLen[a], o2 = wOff[b], l2 = wLen[b];
        int m = Math.min(l1, l2);
        for (int k = 0; k < m; k++) {
            int d = (buf[o1 + k] & 0xff) - (buf[o2 + k] & 0xff);
            if (d != 0) return d;
        }
        return l1 - l2;
    }

    static void addPair(long key) {
        if ((pFilled + 1) * 4 > (pMask + 1) * 3) growPairs();
        int i = mix(key) & (int) pMask;
        for (;;) {
            if (pCnt[i] == 0) {
                pKeys[i] = key;
                pCnt[i] = 1;
                pFilled++;
                return;
            }
            if (pKeys[i] == key) {
                pCnt[i]++;
                return;
            }
            i = (i + 1) & (int) pMask;
        }
    }

    static void growPairs() {
        long[] ok = pKeys;
        int[] oc = pCnt;
        int ns = ok.length * 2;
        pKeys = new long[ns];
        pCnt = new int[ns];
        pMask = ns - 1;
        for (int j = 0; j < ok.length; j++) {
            int c = oc[j];
            if (c != 0) {
                long key = ok[j];
                int i = mix(key) & (int) pMask;
                while (pCnt[i] != 0) i = (i + 1) & (int) pMask;
                pKeys[i] = key;
                pCnt[i] = c;
            }
        }
    }

    static int mix(long x) {
        x += 0x9E3779B97F4A7C15L;
        x = (x ^ (x >>> 30)) * 0xBF58476D1CE4E5B9L;
        x = (x ^ (x >>> 27)) * 0x94D049BB133111EBL;
        return (int) (x ^ (x >>> 31));
    }

    static int intern(int o, int l, int h) {
        if ((wCount + 1) * 2 > wMask + 1) growWords();
        int i = h & (int) wMask;
        for (;;) {
            int slot = wTab[i];
            if (slot == 0) {
                int id = wCount++;
                wOff[id] = o;
                wLen[id] = l;
                wHsh[id] = h;
                wTab[i] = id + 1;
                return id;
            }
            int id = slot - 1;
            if (wHsh[id] == h && wLen[id] == l && eqBytes(wOff[id], o, l)) return id;
            i = (i + 1) & (int) wMask;
        }
    }

    static boolean eqBytes(int a, int b, int l) {
        for (int k = 0; k < l; k++) if (buf[a + k] != buf[b + k]) return false;
        return true;
    }

    static void growWords() {
        int[] ot = wTab;
        int ns = ot.length * 2;
        wTab = new int[ns];
        wMask = ns - 1;
        for (int j = 0; j < ot.length; j++) {
            int slot = ot[j];
            if (slot != 0) {
                int id = slot - 1;
                int i = wHsh[id] & (int) wMask;
                while (wTab[i] != 0) i = (i + 1) & (int) wMask;
                wTab[i] = id + 1;
            }
        }
    }
}
