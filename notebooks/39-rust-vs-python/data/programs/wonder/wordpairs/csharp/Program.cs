using System;
using System.IO;
using System.Text;

class Program
{
    static ulong Mix64(ulong x)
    {
        x ^= x >> 32;
        x *= 0xd6e8feb86659fd93UL;
        x ^= x >> 32;
        return x;
    }

    static bool IsLetter(byte b) => (b >= (byte)'A' && b <= (byte)'Z') || (b >= (byte)'a' && b <= (byte)'z');
    static byte ToLow(byte b) => (b >= (byte)'A' && b <= (byte)'Z') ? (byte)(b + 32) : b;

    static int WordCmp(int a, int b, byte[] arena, int[] woff, int[] wlen)
    {
        if (a == b) return 0;
        int oa = woff[a], ob = woff[b];
        int la = wlen[a], lb = wlen[b];
        int m = la < lb ? la : lb;
        for (int j = 0; j < m; j++)
        {
            int d = arena[oa + j] - arena[ob + j];
            if (d != 0) return d;
        }
        return la - lb;
    }
    static bool Better(int c1, int a1, int b1, int c2, int a2, int b2, byte[] arena, int[] woff, int[] wlen)
    {
        if (c1 != c2) return c1 > c2;
        int cmp = WordCmp(a1, a2, arena, woff, wlen);
        if (cmp != 0) return cmp < 0;
        return WordCmp(b1, b2, arena, woff, wlen) < 0;
    }

    static void Main(string[] args)
    {
        byte[] buf = File.ReadAllBytes(args[0]);
        int n = buf.Length;

        int wcap = 1 << 17, wmask = wcap - 1;
        int[] wtab = new int[wcap];
        Array.Fill(wtab, -1);
        int[] whash = new int[wcap];
        byte[] arena = new byte[1 << 19];
        int arenaSize = 0;
        int[] woff = new int[45000];
        int[] wlen = new int[45000];
        int vocab = 0;

        int pcap = 1 << 21, pmask = pcap - 1;
        ulong[] pkeys = new ulong[pcap];
        Array.Fill(pkeys, ulong.MaxValue);
        int[] pcounts = new int[pcap];
        int psize = 0;

        long W = 0, T = 0;
        int prev = -1;
        int i = 0;
        while (i < n)
        {
            byte c = buf[i];
            if (IsLetter(c))
            {
                int start = i;
                int h = unchecked((int)0x811c9dc5);
                while (i < n && IsLetter(buf[i]))
                {
                    h ^= ToLow(buf[i]);
                    h = unchecked(h * 0x01000193);
                    i++;
                }
                int len = i - start;
                int id;
                int idx = h & wmask;
                while (true)
                {
                    int cur = wtab[idx];
                    if (cur < 0)
                    {
                        id = vocab++;
                        if (vocab > woff.Length)
                        {
                            Array.Resize(ref woff, woff.Length * 2);
                            Array.Resize(ref wlen, wlen.Length * 2);
                        }
                        if (arenaSize + len > arena.Length)
                        {
                            int nc = arena.Length;
                            while (nc < arenaSize + len) nc *= 2;
                            Array.Resize(ref arena, nc);
                        }
                        int off = arenaSize;
                        for (int j = 0; j < len; j++) arena[arenaSize++] = ToLow(buf[start + j]);
                        woff[id] = off; wlen[id] = len;
                        wtab[idx] = id; whash[idx] = h;
                        if (vocab * 2 > wcap)
                        {
                            int ncap = wcap * 2, nmask = ncap - 1;
                            int[] nt = new int[ncap]; Array.Fill(nt, -1);
                            int[] nh = new int[ncap];
                            for (int k = 0; k < wcap; k++)
                            {
                                int v = wtab[k]; if (v < 0) continue;
                                int p = whash[k] & nmask;
                                while (nt[p] != -1) p = (p + 1) & nmask;
                                nt[p] = v; nh[p] = whash[k];
                            }
                            wtab = nt; whash = nh; wcap = ncap; wmask = nmask;
                        }
                        break;
                    }
                    if (whash[idx] == h && wlen[cur] == len)
                    {
                        int off = woff[cur];
                        bool eq = true;
                        for (int j = 0; j < len; j++)
                            if (arena[off + j] != ToLow(buf[start + j])) { eq = false; break; }
                        if (eq) { id = cur; break; }
                    }
                    idx = (idx + 1) & wmask;
                }
                W++;
                if (prev >= 0)
                {
                    T++;
                    ulong key = ((ulong)(uint)prev << 32) | (uint)id;
                    int pi = (int)(Mix64(key) & (ulong)pmask);
                    while (true)
                    {
                        ulong k = pkeys[pi];
                        if (k == ulong.MaxValue)
                        {
                            pkeys[pi] = key; pcounts[pi] = 1; psize++;
                            if ((long)psize * 10 > (long)pcap * 7)
                            {
                                int ncap = pcap * 2, nmask = ncap - 1;
                                ulong[] nk = new ulong[ncap]; Array.Fill(nk, ulong.MaxValue);
                                int[] nc2 = new int[ncap];
                                for (int k2 = 0; k2 < pcap; k2++)
                                {
                                    ulong kk = pkeys[k2]; if (kk == ulong.MaxValue) continue;
                                    int p = (int)(Mix64(kk) & (ulong)nmask);
                                    while (nk[p] != ulong.MaxValue) p = (p + 1) & nmask;
                                    nk[p] = kk; nc2[p] = pcounts[k2];
                                }
                                pkeys = nk; pcounts = nc2; pcap = ncap; pmask = nmask;
                            }
                            break;
                        }
                        if (k == key) { pcounts[pi]++; break; }
                        pi = (pi + 1) & pmask;
                    }
                }
                prev = id;
            }
            else
            {
                if (c == (byte)'.' || c == (byte)'!' || c == (byte)'?') prev = -1;
                i++;
            }
        }

        int[] tc = new int[20]; int[] ta = new int[20]; int[] tb = new int[20];
        int tsz = 0;
        for (int k = 0; k < pcap; k++)
        {
            ulong key = pkeys[k];
            if (key == ulong.MaxValue) continue;
            int cnt = pcounts[k];
            int a = (int)(key >> 32);
            int b = (int)(key & 0xffffffffUL);
            if (tsz == 20)
            {
                if (!Better(cnt, a, b, tc[19], ta[19], tb[19], arena, woff, wlen)) continue;
                int pos = 19;
                while (pos > 0 && Better(cnt, a, b, tc[pos - 1], ta[pos - 1], tb[pos - 1], arena, woff, wlen))
                { tc[pos] = tc[pos - 1]; ta[pos] = ta[pos - 1]; tb[pos] = tb[pos - 1]; pos--; }
                tc[pos] = cnt; ta[pos] = a; tb[pos] = b;
            }
            else
            {
                int pos = tsz++;
                while (pos > 0 && Better(cnt, a, b, tc[pos - 1], ta[pos - 1], tb[pos - 1], arena, woff, wlen))
                { tc[pos] = tc[pos - 1]; ta[pos] = ta[pos - 1]; tb[pos] = tb[pos - 1]; pos--; }
                tc[pos] = cnt; ta[pos] = a; tb[pos] = b;
            }
        }

        var sb = new StringBuilder(1024);
        sb.Append("words ").Append(W).Append('\n');
        sb.Append("pairs ").Append(T).Append('\n');
        sb.Append("distinct ").Append(psize).Append('\n');
        for (int k = 0; k < tsz; k++)
        {
            sb.Append(tc[k]).Append(' ');
            sb.Append(Encoding.ASCII.GetString(arena, woff[ta[k]], wlen[ta[k]]));
            sb.Append(' ');
            sb.Append(Encoding.ASCII.GetString(arena, woff[tb[k]], wlen[tb[k]]));
            sb.Append('\n');
        }
        using (var stdout = Console.OpenStandardOutput())
        {
            byte[] outb = Encoding.ASCII.GetBytes(sb.ToString());
            stdout.Write(outb, 0, outb.Length);
        }
    }
}
