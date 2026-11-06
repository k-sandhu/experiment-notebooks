using System;
using System.IO;
using System.Text;

class Program
{
    static readonly int[] LOWER = new int[256];

    static byte[] B;
    static ulong[] tab = new ulong[4096 * 3];
    static int mask = 4095;
    static int nWords = 0;
    static int[] wOff = new int[1 << 12];
    static int[] wLen = new int[1 << 12];

    static ulong MixKey(ulong p0, ulong p1, int len)
    {
        ulong h = p0 * 0x9E3779B97F4A7C15UL;
        h ^= (p1 + (ulong)len) * 0xC2B2AE3D27D4EB4FUL;
        h ^= h >> 29;
        h *= 0xBF58476D1CE4E5B9UL;
        h ^= h >> 32;
        return h;
    }

    static void Rehash(int slots)
    {
        ulong[] t = new ulong[slots * 3];
        for (int q = 0; q < t.Length; q++) t[q] = ulong.MaxValue;
        int m = slots - 1;
        int oldSlots = tab.Length / 3;
        for (int s = 0; s < oldSlots; s++)
        {
            ulong idl = tab[s * 3 + 2];
            if ((int)idl < 0) continue;
            ulong p0 = tab[s * 3], p1 = tab[s * 3 + 1];
            int len = (int)(idl >> 32);
            int idx = (int)MixKey(p0, p1, len) & m;
            while ((int)t[idx * 3 + 2] >= 0) idx = (idx + 1) & m;
            t[idx * 3] = p0;
            t[idx * 3 + 1] = p1;
            t[idx * 3 + 2] = idl;
        }
        tab = t;
        mask = m;
    }

    static void GrowWords()
    {
        int nc = wOff.Length + (wOff.Length >> 1) + 16;
        Array.Resize(ref wOff, nc);
        Array.Resize(ref wLen, nc);
    }

    static bool EqTail(int a, int b, int len)
    {
        byte[] d = B;
        for (int i = 16; i < len; i++)
            if (d[a + i] != d[b + i]) return false;
        return true;
    }

    static int Intern(ulong p0, ulong p1, int len, int off)
    {
        int idx = (int)MixKey(p0, p1, len) & mask;
        ulong[] t = tab;
        for (;;)
        {
            ulong idl = t[idx * 3 + 2];
            int id = (int)idl;
            if (id < 0) break;
            if ((int)(idl >> 32) == len && t[idx * 3] == p0 && t[idx * 3 + 1] == p1)
            {
                if (len <= 16 || EqTail(wOff[id], off, len)) return id;
            }
            idx = (idx + 1) & mask;
        }
        if (nWords == wOff.Length) GrowWords();
        int nid = nWords++;
        wOff[nid] = off;
        wLen[nid] = len;
        t[idx * 3] = p0;
        t[idx * 3 + 1] = p1;
        t[idx * 3 + 2] = ((ulong)(uint)len << 32) | (uint)nid;
        if (nWords * 10 > (t.Length / 3) * 7) Rehash((t.Length / 3) * 2);
        return nid;
    }

    static ulong GetLong(byte[] b, int o)
    {
        return (ulong)b[o]
             | ((ulong)b[o + 1] << 8)
             | ((ulong)b[o + 2] << 16)
             | ((ulong)b[o + 3] << 24)
             | ((ulong)b[o + 4] << 32)
             | ((ulong)b[o + 5] << 40)
             | ((ulong)b[o + 6] << 48)
             | ((ulong)b[o + 7] << 56);
    }

    static int CmpWord(int x, int y)
    {
        int ox = wOff[x], oy = wOff[y];
        int lx = wLen[x], ly = wLen[y];
        int l = lx < ly ? lx : ly;
        byte[] d = B;
        for (int i = 0; i < l; i++)
        {
            int a = d[ox + i], b = d[oy + i];
            if (a != b) return a - b;
        }
        return lx - ly;
    }

    static bool Better(int c1, int a1, int a2, int c2, int b1, int b2)
    {
        if (c1 != c2) return c1 > c2;
        int c = CmpWord(a1, b1);
        if (c != 0) return c < 0;
        return CmpWord(a2, b2) < 0;
    }

    static bool Worse(int c1, int a1, int a2, int c2, int b1, int b2)
    {
        return Better(c2, b1, b2, c1, a1, a2);
    }

    static void Main(string[] args)
    {
        for (int c = 'a'; c <= 'z'; c++) LOWER[c] = c;
        for (int c = 'A'; c <= 'Z'; c++) LOWER[c] = c + 32;
        for (int t = 0; t < tab.Length; t++) tab[t] = ulong.MaxValue;

        byte[] raw = File.ReadAllBytes(args[0]);
        int n = raw.Length;
        B = new byte[n + 16];
        Array.Copy(raw, B, n);
        byte[] b = B;
        raw = null;

        int cap = Math.Max(1024, n / 6 + 1024);
        ulong[] pairs = new ulong[cap];
        int np = 0;
        int prev = -1;
        int i = 0;
        long W = 0, T = 0;
        int[] low = LOWER;

        while (i < n)
        {
            int lc = low[b[i]];
            if (lc != 0)
            {
                int start = i;
                do
                {
                    b[i] = (byte)lc;
                    i++;
                    lc = (i < n) ? low[b[i]] : 0;
                } while (lc != 0);
                int len = i - start;

                ulong r0 = GetLong(b, start);
                ulong p0 = (len >= 8) ? r0 : (r0 & ((1UL << (8 * len)) - 1));
                ulong p1 = 0;
                if (len > 8)
                {
                    ulong r1 = GetLong(b, start + 8);
                    int rem = len - 8;
                    p1 = (rem >= 8) ? r1 : (r1 & ((1UL << (8 * rem)) - 1));
                }

                int id = Intern(p0, p1, len, start);
                W++;
                if (prev >= 0)
                {
                    if (np == pairs.Length)
                        Array.Resize(ref pairs, pairs.Length + (pairs.Length >> 1) + 64);
                    pairs[np++] = ((ulong)(uint)prev << 32) | (uint)id;
                    T++;
                }
                prev = id;
            }
            else
            {
                int c = b[i];
                if (c == '.' || c == '!' || c == '?') prev = -1;
                i++;
            }
        }

        ulong[] keys = pairs;
        if (np > 1)
        {
            ulong orAll = 0;
            for (int k = 0; k < np; k++) orAll |= pairs[k];
            ulong[] tmp = new ulong[np];
            ulong[] src = pairs, dst = tmp;
            int[] cnt = new int[256];
            for (int pass = 0; pass < 8; pass++)
            {
                int shift = pass * 8;
                if (((orAll >> shift) & 0xFFUL) == 0) continue;
                Array.Clear(cnt, 0, 256);
                for (int k = 0; k < np; k++)
                    cnt[(int)((src[k] >> shift) & 0xFF)]++;
                int sum = 0;
                for (int d = 0; d < 256; d++)
                {
                    int c = cnt[d];
                    cnt[d] = sum;
                    sum += c;
                }
                for (int k = 0; k < np; k++)
                {
                    ulong key = src[k];
                    dst[cnt[(int)((key >> shift) & 0xFF)]++] = key;
                }
                ulong[] t = src;
                src = dst;
                dst = t;
            }
            keys = src;
        }

        int[] bestC = new int[20];
        int[] bestA = new int[20];
        int[] bestB = new int[20];
        int bn = 0;
        long distinct = 0;

        int kk = 0;
        while (kk < np)
        {
            int j = kk + 1;
            ulong key = keys[kk];
            while (j < np && keys[j] == key) j++;
            int c = j - kk;
            int a = (int)(key >> 32);
            int b2 = (int)(key & 0xFFFFFFFFUL);
            if (bn < 20)
            {
                bestC[bn] = c; bestA[bn] = a; bestB[bn] = b2;
                int idx = bn++;
                while (idx > 0)
                {
                    int p = (idx - 1) >> 1;
                    if (Worse(bestC[idx], bestA[idx], bestB[idx],
                              bestC[p], bestA[p], bestB[p]))
                    {
                        int t = bestC[idx]; bestC[idx] = bestC[p]; bestC[p] = t;
                        t = bestA[idx]; bestA[idx] = bestA[p]; bestA[p] = t;
                        t = bestB[idx]; bestB[idx] = bestB[p]; bestB[p] = t;
                        idx = p;
                    }
                    else break;
                }
            }
            else if (Better(c, a, b2, bestC[0], bestA[0], bestB[0]))
            {
                bestC[0] = c; bestA[0] = a; bestB[0] = b2;
                int idx = 0;
                for (;;)
                {
                    int l = 2 * idx + 1, r = l + 1, w = idx;
                    if (l < bn && Worse(bestC[l], bestA[l], bestB[l],
                                        bestC[w], bestA[w], bestB[w])) w = l;
                    if (r < bn && Worse(bestC[r], bestA[r], bestB[r],
                                        bestC[w], bestA[w], bestB[w])) w = r;
                    if (w == idx) break;
                    int t = bestC[idx]; bestC[idx] = bestC[w]; bestC[w] = t;
                    t = bestA[idx]; bestA[idx] = bestA[w]; bestA[w] = t;
                    t = bestB[idx]; bestB[idx] = bestB[w]; bestB[w] = t;
                    idx = w;
                }
            }
            distinct++;
            kk = j;
        }

        for (int q = 1; q < bn; q++)
        {
            int cq = bestC[q], aq = bestA[q], bq = bestB[q];
            int r = q - 1;
            while (r >= 0 && Better(cq, aq, bq, bestC[r], bestA[r], bestB[r]))
            {
                bestC[r + 1] = bestC[r]; bestA[r + 1] = bestA[r]; bestB[r + 1] = bestB[r];
                r--;
            }
            bestC[r + 1] = cq; bestA[r + 1] = aq; bestB[r + 1] = bq;
        }

        StringBuilder sb = new StringBuilder(512);
        sb.Append("words ").Append(W).Append('\n');
        sb.Append("pairs ").Append(T).Append('\n');
        sb.Append("distinct ").Append(distinct).Append('\n');
        for (int q = 0; q < bn; q++)
        {
            sb.Append(bestC[q]).Append(' ');
            sb.Append(Encoding.ASCII.GetString(b, wOff[bestA[q]], wLen[bestA[q]]));
            sb.Append(' ');
            sb.Append(Encoding.ASCII.GetString(b, wOff[bestB[q]], wLen[bestB[q]]));
            sb.Append('\n');
        }
        byte[] outBytes = Encoding.ASCII.GetBytes(sb.ToString());
        using (Stream stdout = Console.OpenStandardOutput())
        {
            stdout.Write(outBytes, 0, outBytes.Length);
            stdout.Flush();
        }
    }
}
