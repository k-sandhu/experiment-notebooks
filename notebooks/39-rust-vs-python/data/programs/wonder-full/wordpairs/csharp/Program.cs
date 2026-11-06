using System;
using System.IO;
using System.Text;

class Program
{
    static ulong Mix64(ulong x)
    {
        x += 0x9e3779b97f4a7c15UL;
        x = (x ^ (x >> 30)) * 0xbf58476d1ce4e5b9UL;
        x = (x ^ (x >> 27)) * 0x94d049bb133111ebUL;
        return x ^ (x >> 31);
    }
    static bool Better(int c1, int a1, int b1, int c2, int a2, int b2, int[] rk)
    {
        if (c1 != c2) return c1 > c2;
        if (rk[a1] != rk[a2]) return rk[a1] < rk[a2];
        return rk[b1] < rk[b2];
    }
    static int FindWorst(int[] C, int[] A, int[] B, int n, int[] rk)
    {
        int w = 0;
        for (int q = 1; q < n; q++) if (Better(C[w], A[w], B[w], C[q], A[q], B[q], rk)) w = q;
        return w;
    }

    static void Main(string[] args)
    {
        byte[] data = File.ReadAllBytes(args[0]);
        int n = data.Length;

        int wcap = 1024;
        while (wcap < (1 << 17) && (long)wcap * 64 < n) wcap <<= 1;
        int[] wtab = new int[wcap];
        Array.Fill(wtab, -1);
        int wmask = wcap - 1;

        byte[] arena = new byte[1 << 20];
        int arenaLen = 0;
        int[] woff = new int[65536];
        int[] wlen = new int[65536];
        ulong[] whash = new ulong[65536];
        int V = 0;

        int est = n / 6 + 1024;
        if (est > (1 << 24)) est = 1 << 24;
        if (est < 1024) est = 1024;
        ulong[] pairs = new ulong[est];
        int pc = 0;

        long W = 0;
        int prev = -1;
        int i = 0;
        while (i < n)
        {
            int b = data[i];
            int lo = b | 32;
            if ((uint)(lo - 97) < 26)
            {
                int start = i;
                ulong h = 14695981039346656037UL;
                for (;;)
                {
                    h ^= (ulong)lo;
                    h *= 1099511628211UL;
                    i++;
                    if (i >= n) break;
                    b = data[i]; lo = b | 32;
                    if ((uint)(lo - 97) >= 26) break;
                }
                int len = i - start;
                ulong mh = Mix64(h);
                int idx = (int)mh & wmask;
                int id;
                for (;;)
                {
                    id = wtab[idx];
                    if (id < 0)
                    {
                        id = V++;
                        wtab[idx] = id;
                        if (V >= whash.Length)
                        {
                            int nc = whash.Length << 1;
                            Array.Resize(ref whash, nc);
                            Array.Resize(ref woff, nc);
                            Array.Resize(ref wlen, nc);
                        }
                        whash[id] = mh;
                        woff[id] = arenaLen;
                        wlen[id] = len;
                        if (arenaLen + len > arena.Length)
                        {
                            int nc = arena.Length;
                            while (nc < arenaLen + len) nc <<= 1;
                            Array.Resize(ref arena, nc);
                        }
                        for (int k = 0; k < len; k++) arena[arenaLen++] = (byte)(data[start + k] | 32);
                        if (V * 4 > wcap * 3)
                        {
                            int ncap = wcap << 1;
                            int[] nt = new int[ncap];
                            Array.Fill(nt, -1);
                            int nmask = ncap - 1;
                            for (int wi = 0; wi < V; wi++)
                            {
                                int j = (int)whash[wi] & nmask;
                                while (nt[j] >= 0) j = (j + 1) & nmask;
                                nt[j] = wi;
                            }
                            wtab = nt; wcap = ncap; wmask = nmask;
                        }
                        break;
                    }
                    if (whash[id] == mh && wlen[id] == len)
                    {
                        int off = woff[id];
                        bool eq = true;
                        for (int k = 0; k < len; k++)
                            if (arena[off + k] != (byte)(data[start + k] | 32)) { eq = false; break; }
                        if (eq) break;
                    }
                    idx = (idx + 1) & wmask;
                }
                W++;
                if (prev >= 0)
                {
                    if (pc == pairs.Length) Array.Resize(ref pairs, pairs.Length << 1);
                    pairs[pc++] = ((ulong)(uint)prev << 32) | (uint)id;
                }
                prev = id;
            }
            else
            {
                if (b == '.' || b == '!' || b == '?') prev = -1;
                i++;
            }
        }
        long T = pc;
        data = null;

        int[] ids = new int[V];
        for (int k = 0; k < V; k++) ids[k] = k;
        byte[] ar = arena; int[] wo = woff, wl = wlen;
        Array.Sort(ids, (a, b) =>
        {
            int la = wl[a], lb = wl[b], oa = wo[a], ob = wo[b];
            int m = la < lb ? la : lb;
            for (int k = 0; k < m; k++)
            {
                int diff = ar[oa + k] - ar[ob + k];
                if (diff != 0) return diff;
            }
            return la - lb;
        });
        int[] rankv = new int[V];
        for (int k = 0; k < V; k++) rankv[ids[k]] = k;

        int[] topC = new int[20], topA = new int[20], topB = new int[20];
        int topN = 0, worst = 0;
        long D = 0;
        if (pc > 0 && V <= 65536)
        {
            uint[] keys = new uint[pc];
            for (int k = 0; k < pc; k++) { ulong v = pairs[k]; keys[k] = ((uint)(v >> 32) << 16) | (uint)v; }
            pairs = null;
            uint[] aux = new uint[pc];
            uint[] src = keys, dst = aux;
            int[] cnt = new int[65536];
            for (int shift = 0; shift < 32; shift += 16)
            {
                Array.Clear(cnt, 0, cnt.Length);
                for (int k = 0; k < pc; k++) cnt[(int)(src[k] >> shift) & 0xFFFF]++;
                int sum = 0;
                for (int k = 0; k < 65536; k++) { int t = cnt[k]; cnt[k] = sum; sum += t; }
                for (int k = 0; k < pc; k++) { uint v = src[k]; dst[cnt[(int)(v >> shift) & 0xFFFF]++] = v; }
                (src, dst) = (dst, src);
            }
            int kk = 0;
            while (kk < pc)
            {
                int j = kk + 1;
                uint v = src[kk];
                while (j < pc && src[j] == v) j++;
                int c = j - kk;
                D++;
                int a = (int)(v >> 16), bb = (int)(v & 0xFFFF);
                if (topN < 20)
                {
                    topC[topN] = c; topA[topN] = a; topB[topN] = bb; topN++;
                    if (topN == 20) worst = FindWorst(topC, topA, topB, topN, rankv);
                }
                else if (Better(c, a, bb, topC[worst], topA[worst], topB[worst], rankv))
                {
                    topC[worst] = c; topA[worst] = a; topB[worst] = bb;
                    worst = FindWorst(topC, topA, topB, topN, rankv);
                }
                kk = j;
            }
        }
        else if (pc > 0)
        {
            ulong[] aux = new ulong[pc];
            ulong[] src = pairs, dst = aux;
            int[] cnt = new int[65536];
            for (int shift = 0; shift < 64; shift += 16)
            {
                Array.Clear(cnt, 0, cnt.Length);
                for (int k = 0; k < pc; k++) cnt[(int)(src[k] >> shift) & 0xFFFF]++;
                int sum = 0;
                for (int k = 0; k < 65536; k++) { int t = cnt[k]; cnt[k] = sum; sum += t; }
                for (int k = 0; k < pc; k++) { ulong v = src[k]; dst[cnt[(int)(v >> shift) & 0xFFFF]++] = v; }
                (src, dst) = (dst, src);
            }
            int k2 = 0;
            while (k2 < pc)
            {
                int j = k2 + 1;
                ulong v = src[k2];
                while (j < pc && src[j] == v) j++;
                int c = j - k2;
                D++;
                int a = (int)(v >> 32), bb = (int)v;
                if (topN < 20)
                {
                    topC[topN] = c; topA[topN] = a; topB[topN] = bb; topN++;
                    if (topN == 20) worst = FindWorst(topC, topA, topB, topN, rankv);
                }
                else if (Better(c, a, bb, topC[worst], topA[worst], topB[worst], rankv))
                {
                    topC[worst] = c; topA[worst] = a; topB[worst] = bb;
                    worst = FindWorst(topC, topA, topB, topN, rankv);
                }
                k2 = j;
            }
        }
        for (int a = 1; a < topN; a++)
        {
            int c = topC[a], x = topA[a], y = topB[a], b = a - 1;
            while (b >= 0 && Better(c, x, y, topC[b], topA[b], topB[b], rankv))
            {
                topC[b + 1] = topC[b]; topA[b + 1] = topA[b]; topB[b + 1] = topB[b]; b--;
            }
            topC[b + 1] = c; topA[b + 1] = x; topB[b + 1] = y;
        }
        var sb = new StringBuilder(1024);
        sb.Append("words ").Append(W).Append('\n');
        sb.Append("pairs ").Append(T).Append('\n');
        sb.Append("distinct ").Append(D).Append('\n');
        for (int k = 0; k < topN; k++)
        {
            sb.Append(topC[k]).Append(' ');
            int a = topA[k], b = topB[k];
            for (int q = 0; q < wl[a]; q++) sb.Append((char)ar[wo[a] + q]);
            sb.Append(' ');
            for (int q = 0; q < wl[b]; q++) sb.Append((char)ar[wo[b] + q]);
            sb.Append('\n');
        }
        Console.Out.Write(sb.ToString());
    }
}
