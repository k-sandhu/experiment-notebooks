using System;
using System.IO;
using System.Text;

internal static class Program
{
    // ---- word table: open addressing, ids into a byte arena ----
    static int[] wSlot;   // id+1, 0 = empty
    static int[] wHash;
    static int[] wOff;
    static int[] wLen;
    static byte[] wArena;
    static int wArenaLen;
    static int wMask, wCount;

    static void WGrow()
    {
        int cap = wMask + 1, cap2 = cap * 2;
        int[] s2 = new int[cap2], h2 = new int[cap2];
        int m2 = cap2 - 1;
        for (int i = 0; i < cap; i++)
        {
            if (wSlot[i] != 0)
            {
                int j = wHash[i] & m2;
                while (s2[j] != 0) j = (j + 1) & m2;
                s2[j] = wSlot[i];
                h2[j] = wHash[i];
            }
        }
        wSlot = s2; wHash = h2; wMask = m2;
    }

    static unsafe int WordFindOrAdd(byte* w, int n, int h)
    {
        int i = h & wMask;
        while (wSlot[i] != 0)
        {
            int id = wSlot[i] - 1;
            if (wHash[i] == h && wLen[id] == n)
            {
                int o = wOff[id];
                bool eq = true;
                for (int k = 0; k < n; k++)
                    if (wArena[o + k] != w[k]) { eq = false; break; }
                if (eq) return id;
            }
            i = (i + 1) & wMask;
        }
        if ((long)(wCount + 1) * 3 > (long)(wMask + 1) * 2)
        {
            WGrow();
            i = h & wMask;
            while (wSlot[i] != 0) i = (i + 1) & wMask;
        }
        int nid = wCount++;
        int off = wArenaLen;
        if (wArenaLen + n > wArena.Length)
        {
            int nc = wArena.Length;
            while (wArenaLen + n > nc) nc *= 2;
            byte[] a2 = new byte[nc];
            Buffer.BlockCopy(wArena, 0, a2, 0, wArenaLen);
            wArena = a2;
        }
        for (int k = 0; k < n; k++) wArena[wArenaLen + k] = w[k];
        wArenaLen += n;
        if (nid == wOff.Length)
        {
            Array.Resize(ref wOff, nid * 2);
            Array.Resize(ref wLen, nid * 2);
        }
        wOff[nid] = off;
        wLen[nid] = n;
        wSlot[i] = nid + 1;
        wHash[i] = h;
        return nid;
    }

    static int CmpWords(int a, int b)
    {
        int la = wLen[a], lb = wLen[b];
        int oa = wOff[a], ob = wOff[b];
        int m = la < lb ? la : lb;
        for (int i = 0; i < m; i++)
        {
            int d = wArena[oa + i] - wArena[ob + i];
            if (d != 0) return d;
        }
        return la - lb;
    }

    // ---- pair table ----
    static long[] pKey;
    static int[] pCnt;
    static long pMask, pCount;
    const long PEMPTY = -1L;

    static long MixKey(long x)
    {
        x *= unchecked((long)0x9E3779B97F4A7C15L);
        x ^= x >> 32;
        x *= unchecked((long)0xBF58476D1CE4E5B9L);
        x ^= x >> 29;
        return x;
    }

    static void PGrow()
    {
        long cap = pMask + 1, cap2 = cap * 2, m2 = cap2 - 1;
        long[] k2 = new long[cap2];
        int[] c2 = new int[cap2];
        Array.Fill(k2, PEMPTY);
        for (long i = 0; i < cap; i++)
        {
            if (pKey[i] != PEMPTY)
            {
                long j = MixKey(pKey[i]) & m2;
                while (k2[j] != PEMPTY) j = (j + 1) & m2;
                k2[j] = pKey[i];
                c2[j] = pCnt[i];
            }
        }
        pKey = k2; pCnt = c2; pMask = m2;
    }

    static void PairAdd(long key)
    {
        long i = MixKey(key) & pMask;
        while (pKey[i] != PEMPTY)
        {
            if (pKey[i] == key) { pCnt[i]++; return; }
            i = (i + 1) & pMask;
        }
        if ((pCount + 1) * 3 > (pMask + 1) * 2)
        {
            PGrow();
            i = MixKey(key) & pMask;
            while (pKey[i] != PEMPTY) i = (i + 1) & pMask;
        }
        pKey[i] = key;
        pCnt[i] = 1;
        pCount++;
    }

    // negative if (c1,w1) ranks better (earlier in output) than (c2,w2)
    static int Worse(int c1, int i1a, int i1b, int c2, int i2a, int i2b)
    {
        if (c1 != c2) return c2 - c1;
        int d = CmpWords(i1a, i2a);
        if (d != 0) return d;
        return CmpWords(i1b, i2b);
    }

    static unsafe void Main(string[] args)
    {
        if (args.Length < 1) return;
        byte[] data = File.ReadAllBytes(args[0]);
        long totalWords = 0, totalPairs = 0;

        wMask = (1 << 16) - 1;
        wSlot = new int[wMask + 1];
        wHash = new int[wMask + 1];
        wOff = new int[256];
        wLen = new int[256];
        wArena = new byte[1 << 16];
        wArenaLen = 0;

        pMask = (1L << 20) - 1;
        pKey = new long[1 << 20];
        pCnt = new int[1 << 20];
        Array.Fill(pKey, PEMPTY);

        int prev = -1;
        byte[] wbuf = new byte[256];
        fixed (byte* pd = data)
        {
            byte* p = pd, end = pd + data.Length;
            int wl = 0;
            while (p < end)
            {
                int c = *p;
                int lc = c | 0x20;
                if ((uint)(lc - 'a') < 26u)
                {
                    if (wl == wbuf.Length)
                    {
                        byte[] nb = new byte[wbuf.Length * 2];
                        Buffer.BlockCopy(wbuf, 0, nb, 0, wl);
                        wbuf = nb;
                    }
                    wbuf[wl++] = (byte)lc;
                }
                else
                {
                    if (wl > 0)
                    {
                        totalWords++;
                        int h = unchecked((int)2166136261L);
                        for (int k = 0; k < wl; k++) { h ^= wbuf[k]; h *= 16777619; }
                        h = h == 0 ? 1 : h;
                        fixed (byte* wb = wbuf)
                        {
                            int id = WordFindOrAdd(wb, wl, h);
                            if (prev >= 0)
                            {
                                totalPairs++;
                                PairAdd(((long)prev << 32) | (uint)id);
                            }
                            prev = id;
                        }
                        wl = 0;
                    }
                    if (c == '.' || c == '!' || c == '?') prev = -1;
                }
                p++;
            }
            if (wl > 0)
            {
                totalWords++;
                int h = unchecked((int)2166136261L);
                for (int k = 0; k < wl; k++) { h ^= wbuf[k]; h *= 16777619; }
                h = h == 0 ? 1 : h;
                fixed (byte* wb = wbuf)
                {
                    int id = WordFindOrAdd(wb, wl, h);
                    if (prev >= 0)
                    {
                        totalPairs++;
                        PairAdd(((long)prev << 32) | (uint)id);
                    }
                }
            }
        }

        // top 20 via bounded min-heap (root = worst)
        int hc = 0;
        int[] hCnt = new int[21], hId1 = new int[21], hId2 = new int[21];
        for (long i = 0; i <= pMask; i++)
        {
            if (pKey[i] == PEMPTY) continue;
            int c1 = pCnt[i];
            int id1 = (int)(pKey[i] >> 32), id2 = (int)pKey[i];
            if (hc < 20)
            {
                int q = hc++;
                hCnt[q] = c1; hId1[q] = id1; hId2[q] = id2;
                while (q > 0)
                {
                    int par = (q - 1) / 2;
                    if (Worse(hCnt[q], hId1[q], hId2[q], hCnt[par], hId1[par], hId2[par]) <= 0) break;
                    (hCnt[q], hCnt[par]) = (hCnt[par], hCnt[q]);
                    (hId1[q], hId1[par]) = (hId1[par], hId1[q]);
                    (hId2[q], hId2[par]) = (hId2[par], hId2[q]);
                    q = par;
                }
            }
            else if (Worse(c1, id1, id2, hCnt[0], hId1[0], hId2[0]) < 0)
            {
                hCnt[0] = c1; hId1[0] = id1; hId2[0] = id2;
                SiftDown(hCnt, hId1, hId2, hc);
            }
        }

        int m = hc;
        int[] rCnt = new int[m], rId1 = new int[m], rId2 = new int[m];
        for (int idx = m - 1; idx >= 0; idx--)
        {
            rCnt[idx] = hCnt[0]; rId1[idx] = hId1[0]; rId2[idx] = hId2[0];
            hc--;
            hCnt[0] = hCnt[hc]; hId1[0] = hId1[hc]; hId2[0] = hId2[hc];
            SiftDown(hCnt, hId1, hId2, hc);
        }
        for (int a = 1; a < m; a++)
        {
            int c = rCnt[a], i1 = rId1[a], i2 = rId2[a];
            int b = a - 1;
            while (b >= 0 && Worse(rCnt[b], rId1[b], rId2[b], c, i1, i2) > 0)
            {
                rCnt[b + 1] = rCnt[b]; rId1[b + 1] = rId1[b]; rId2[b + 1] = rId2[b];
                b--;
            }
            rCnt[b + 1] = c; rId1[b + 1] = i1; rId2[b + 1] = i2;
        }

        var sb = new StringBuilder(4096);
        sb.Append("words ").Append(totalWords).Append('\n');
        sb.Append("pairs ").Append(totalPairs).Append('\n');
        sb.Append("distinct ").Append(pCount).Append('\n');
        for (int idx = 0; idx < m; idx++)
        {
            sb.Append(rCnt[idx]).Append(' ');
            sb.Append(Encoding.ASCII.GetString(wArena, wOff[rId1[idx]], wLen[rId1[idx]]));
            sb.Append(' ');
            sb.Append(Encoding.ASCII.GetString(wArena, wOff[rId2[idx]], wLen[rId2[idx]]));
            sb.Append('\n');
        }
        using var so = Console.OpenStandardOutput();
        byte[] ob = Encoding.ASCII.GetBytes(sb.ToString());
        so.Write(ob, 0, ob.Length);
    }

    static void SiftDown(int[] hCnt, int[] hId1, int[] hId2, int size)
    {
        int p = 0;
        while (true)
        {
            int l = 2 * p + 1, r = l + 1, s = p;
            if (l < size && Worse(hCnt[l], hId1[l], hId2[l], hCnt[s], hId1[s], hId2[s]) > 0) s = l;
            if (r < size && Worse(hCnt[r], hId1[r], hId2[r], hCnt[s], hId1[s], hId2[s]) > 0) s = r;
            if (s == p) break;
            (hCnt[p], hCnt[s]) = (hCnt[s], hCnt[p]);
            (hId1[p], hId1[s]) = (hId1[s], hId1[p]);
            (hId2[p], hId2[s]) = (hId2[s], hId2[p]);
            p = s;
        }
    }
}
