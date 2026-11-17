import java.io.*;
import java.nio.file.*;

public class Main {
    static long mix64(long x) {
        x ^= x >>> 32;
        x *= 0xd6e8feb86659fd93L;
        x ^= x >>> 32;
        return x;
    }

    public static void main(String[] args) throws Exception {
        byte[] buf = Files.readAllBytes(Path.of(args[0]));
        int n = buf.length;

        int wcap = 1 << 17;
        int wmask = wcap - 1;
        int[] wtab = new int[wcap];
        java.util.Arrays.fill(wtab, -1);
        int[] whash = new int[wcap];
        byte[] arena = new byte[1 << 19];
        int arenaSize = 0;
        int[] woff = new int[45000];
        int[] wlen = new int[45000];
        int vocab = 0;

        int pcap = 1 << 21;
        int pmask = pcap - 1;
        long[] pkeys = new long[pcap];
        java.util.Arrays.fill(pkeys, -1L);
        int[] pcounts = new int[pcap];
        int psize = 0;

        long W = 0, T = 0;
        int prev = -1;
        int i = 0;
        while (i < n) {
            int c = buf[i] & 0xFF;
            if ((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z')) {
                int start = i;
                int h = 0x811c9dc5;
                while (i < n) {
                    int b = buf[i] & 0xFF;
                    if (!((b >= 'A' && b <= 'Z') || (b >= 'a' && b <= 'z'))) break;
                    int low = (b >= 'A' && b <= 'Z') ? b + 32 : b;
                    h ^= low;
                    h *= 0x01000193;
                    i++;
                }
                int len = i - start;
                int id;
                int idx = h & wmask;
                while (true) {
                    int cur = wtab[idx];
                    if (cur < 0) {
                        id = vocab++;
                        if (vocab > woff.length) {
                            woff = java.util.Arrays.copyOf(woff, woff.length * 2);
                            wlen = java.util.Arrays.copyOf(wlen, wlen.length * 2);
                        }
                        if (arenaSize + len > arena.length) {
                            int nc = arena.length;
                            while (nc < arenaSize + len) nc *= 2;
                            arena = java.util.Arrays.copyOf(arena, nc);
                        }
                        int off = arenaSize;
                        for (int j = 0; j < len; j++) {
                            int b = buf[start + j] & 0xFF;
                            arena[arenaSize++] = (byte) ((b >= 'A' && b <= 'Z') ? b + 32 : b);
                        }
                        woff[id] = off;
                        wlen[id] = len;
                        wtab[idx] = id; whash[idx] = h;
                        if (vocab * 2 > wcap) {
                            int ncap = wcap * 2, nmask = ncap - 1;
                            int[] nt = new int[ncap]; java.util.Arrays.fill(nt, -1);
                            int[] nh = new int[ncap];
                            for (int k = 0; k < wcap; k++) {
                                int v = wtab[k]; if (v < 0) continue;
                                int p = whash[k] & nmask;
                                while (nt[p] != -1) p = (p + 1) & nmask;
                                nt[p] = v; nh[p] = whash[k];
                            }
                            wtab = nt; whash = nh; wcap = ncap; wmask = nmask;
                        }
                        break;
                    }
                    if (whash[idx] == h && wlen[cur] == len) {
                        int off = woff[cur];
                        boolean eq = true;
                        for (int j = 0; j < len; j++) {
                            int b = buf[start + j] & 0xFF;
                            int low = (b >= 'A' && b <= 'Z') ? b + 32 : b;
                            if ((arena[off + j] & 0xFF) != low) { eq = false; break; }
                        }
                        if (eq) { id = cur; break; }
                    }
                    idx = (idx + 1) & wmask;
                }
                W++;
                if (prev >= 0) {
                    T++;
                    long key = ((long) prev << 32) | (id & 0xffffffffL);
                    int pi = (int) (mix64(key) & pmask);
                    while (true) {
                        long k = pkeys[pi];
                        if (k == -1L) {
                            pkeys[pi] = key; pcounts[pi] = 1; psize++;
                            if ((long) psize * 10 > (long) pcap * 7) {
                                int ncap = pcap * 2, nmask = ncap - 1;
                                long[] nk = new long[ncap]; java.util.Arrays.fill(nk, -1L);
                                int[] nc = new int[ncap];
                                for (int k2 = 0; k2 < pcap; k2++) {
                                    long kk = pkeys[k2]; if (kk == -1L) continue;
                                    int p = (int) (mix64(kk) & nmask);
                                    while (nk[p] != -1L) p = (p + 1) & nmask;
                                    nk[p] = kk; nc[p] = pcounts[k2];
                                }
                                pkeys = nk; pcounts = nc; pcap = ncap; pmask = nmask;
                            }
                            break;
                        }
                        if (k == key) { pcounts[pi]++; break; }
                        pi = (pi + 1) & pmask;
                    }
                }
                prev = id;
            } else {
                if (c == '.' || c == '!' || c == '?') prev = -1;
                i++;
            }
        }

        // top20
        int[] tc = new int[20];
        int[] ta = new int[20];
        int[] tb = new int[20];
        int tsz = 0;
        // helpers inline via loops; use local references
        for (int k = 0; k < pcap; k++) {
            long key = pkeys[k];
            if (key == -1L) continue;
            int cnt = pcounts[k];
            int a = (int) (key >> 32);
            int b = (int) key;
            if (tsz == 20) {
                // compare candidate vs worst (index 19)
                if (!better(cnt, a, b, tc[19], ta[19], tb[19], arena, woff, wlen)) continue;
                int pos = 19;
                while (pos > 0 && better(cnt, a, b, tc[pos - 1], ta[pos - 1], tb[pos - 1], arena, woff, wlen)) {
                    tc[pos] = tc[pos - 1]; ta[pos] = ta[pos - 1]; tb[pos] = tb[pos - 1]; pos--;
                }
                tc[pos] = cnt; ta[pos] = a; tb[pos] = b;
            } else {
                int pos = tsz++;
                while (pos > 0 && better(cnt, a, b, tc[pos - 1], ta[pos - 1], tb[pos - 1], arena, woff, wlen)) {
                    tc[pos] = tc[pos - 1]; ta[pos] = ta[pos - 1]; tb[pos] = tb[pos - 1]; pos--;
                }
                tc[pos] = cnt; ta[pos] = a; tb[pos] = b;
            }
        }

        StringBuilder sb = new StringBuilder(1024);
        sb.append("words ").append(W).append('\n');
        sb.append("pairs ").append(T).append('\n');
        sb.append("distinct ").append(psize).append('\n');
        for (int k = 0; k < tsz; k++) {
            sb.append(tc[k]).append(' ');
            sb.append(new String(arena, woff[ta[k]], wlen[ta[k]], java.nio.charset.StandardCharsets.US_ASCII));
            sb.append(' ');
            sb.append(new String(arena, woff[tb[k]], wlen[tb[k]], java.nio.charset.StandardCharsets.US_ASCII));
            sb.append('\n');
        }
        System.out.write(sb.toString().getBytes(java.nio.charset.StandardCharsets.US_ASCII));
        System.out.flush();
    }

    static int wordCmp(int a, int b, byte[] arena, int[] woff, int[] wlen) {
        if (a == b) return 0;
        int oa = woff[a], ob = woff[b];
        int la = wlen[a], lb = wlen[b];
        int m = Math.min(la, lb);
        for (int j = 0; j < m; j++) {
            int d = (arena[oa + j] & 0xFF) - (arena[ob + j] & 0xFF);
            if (d != 0) return d;
        }
        return la - lb;
    }

    static boolean better(int c1, int a1, int b1, int c2, int a2, int b2, byte[] arena, int[] woff, int[] wlen) {
        if (c1 != c2) return c1 > c2;
        int cmp = wordCmp(a1, a2, arena, woff, wlen);
        if (cmp != 0) return cmp < 0;
        return wordCmp(b1, b2, arena, woff, wlen) < 0;
    }
}
