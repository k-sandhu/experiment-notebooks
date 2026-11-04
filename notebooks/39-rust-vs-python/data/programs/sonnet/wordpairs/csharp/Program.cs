using System.Text;

static class Prog
{
    const ulong PM = 0x9E3779B97F4A7C15UL;
    const ulong EMPTY = ulong.MaxValue;
    const uint NONE = uint.MaxValue;
    const int BATCH = 512;

    struct PSlot { public ulong Key; public uint Count; }

    static byte[] data;

    static int[] wstart = new int[1 << 15];
    static int[] wlen = new int[1 << 15];
    static ulong[] whash = new ulong[1 << 15];
    static int wcount = 0;
    static int[] wtab = new int[1 << 16];
    static int wmask = (1 << 16) - 1;

    static PSlot[] ptab;
    static int pmask;
    static int pshift;
    static long distinct = 0, tcount = 0;
    static ulong sink;

    static void GrowWords()
    {
        int ncap = wtab.Length * 2;
        var nt = new int[ncap];
        int nmask = ncap - 1;
        for (int id = 0; id < wcount; id++)
        {
            int p = (int)(whash[id] >> 20) & nmask;
            while (nt[p] != 0) p = (p + 1) & nmask;
            nt[p] = id + 1;
        }
        wtab = nt;
        wmask = nmask;
    }

    static int LookupWord(int start, int len, ulong h)
    {
        byte[] d = data;
        int p = (int)(h >> 20) & wmask;
        while (true)
        {
            int e = wtab[p];
            if (e == 0) break;
            int id = e - 1;
            if (whash[id] == h && wlen[id] == len)
            {
                int t = wstart[id];
                int k = 0;
                while (k < len && ((d[start + k] ^ d[t + k]) | 0x20) == 0x20) k++;
                if (k == len) return id;
            }
            p = (p + 1) & wmask;
        }
        int nid = wcount++;
        if (nid == wstart.Length)
        {
            Array.Resize(ref wstart, nid * 2);
            Array.Resize(ref wlen, nid * 2);
            Array.Resize(ref whash, nid * 2);
        }
        wstart[nid] = start;
        wlen[nid] = len;
        whash[nid] = h;
        wtab[p] = nid + 1;
        if (wcount * 2 > wtab.Length) GrowWords();
        return nid;
    }

    static void GrowPairs()
    {
        int ncap = ptab.Length * 2;
        int nshift = pshift - 1;
        var nt = new PSlot[ncap];
        Array.Fill(nt, new PSlot { Key = EMPTY, Count = 0 });
        int nmask = ncap - 1;
        foreach (var s in ptab)
        {
            if (s.Key == EMPTY) continue;
            int p = (int)((s.Key * PM) >> nshift);
            while (nt[p].Key != EMPTY) p = (p + 1) & nmask;
            nt[p] = s;
        }
        ptab = nt;
        pshift = nshift;
        pmask = nmask;
    }

    // ids[0] is the previous word (or NONE); NONE marks a sentence end.
    static void Flush(uint[] ids, int cnt)
    {
        PSlot[] tab = ptab;
        ulong acc = 0;
        int sh = pshift;
        for (int k = 1; k <= cnt; k++)
        {
            ulong key = ((ulong)ids[k - 1] << 32) | ids[k];
            acc += tab[(int)((key * PM) >> sh)].Key;
        }
        sink += acc;
        for (int k = 1; k <= cnt; k++)
        {
            uint a = ids[k - 1], b = ids[k];
            if (a == NONE || b == NONE) continue;
            tcount++;
            ulong key = ((ulong)a << 32) | b;
            PSlot[] t = ptab;
            int p = (int)((key * PM) >> pshift);
            while (true)
            {
                ref PSlot s = ref t[p];
                if (s.Key == key) { s.Count++; break; }
                if (s.Key == EMPTY)
                {
                    s.Key = key;
                    s.Count = 1;
                    distinct++;
                    if (distinct * 10 > (long)t.Length * 7) GrowPairs();
                    break;
                }
                p = (p + 1) & pmask;
            }
        }
    }

    static int CmpWords(uint x, uint y)
    {
        if (x == y) return 0;
        int sx = wstart[x], sy = wstart[y], lx = wlen[x], ly = wlen[y];
        int n = Math.Min(lx, ly);
        for (int i = 0; i < n; i++)
        {
            int cx = data[sx + i] | 0x20, cy = data[sy + i] | 0x20;
            if (cx != cy) return cx < cy ? -1 : 1;
        }
        return lx.CompareTo(ly);
    }

    static bool Better(uint cx, uint ax, uint bx, uint cy, uint ay, uint by)
    {
        if (cx != cy) return cx > cy;
        int c = CmpWords(ax, ay);
        if (c != 0) return c < 0;
        return CmpWords(bx, by) < 0;
    }

    static void AppendWord(StringBuilder sb, uint id)
    {
        int s = wstart[id], l = wlen[id];
        for (int i = 0; i < l; i++) sb.Append((char)(data[s + i] | 0x20));
    }

    static int Main(string[] args)
    {
        byte[] raw = File.ReadAllBytes(args[0]);
        int n = raw.Length;
        Array.Resize(ref raw, n + 1);
        raw[n] = 10;
        data = raw;
        byte[] d = raw;

        int pcap = 1 << 16;
        while (pcap < n / 12 && pcap < (1 << 28)) pcap <<= 1;
        pshift = 64 - System.Numerics.BitOperations.TrailingZeroCount(pcap);
        pmask = pcap - 1;
        ptab = new PSlot[pcap];
        Array.Fill(ptab, new PSlot { Key = EMPTY, Count = 0 });

        long W = 0;
        uint[] ids = new uint[BATCH + 1];
        ids[0] = NONE;
        int cnt = 0;
        int i = 0;
        while (i < n)
        {
            uint c = d[i];
            if (((c | 0x20) - 'a') < 26u)
            {
                int st = i;
                ulong h = 0xcbf29ce484222325UL;
                do
                {
                    h = (h ^ (c | 0x20)) * 0x100000001b3UL;
                    c = d[++i];
                } while (((c | 0x20) - 'a') < 26u);
                h ^= h >> 29;
                h *= PM;
                h ^= h >> 32;
                ids[++cnt] = (uint)LookupWord(st, i - st, h);
                W++;
                if (cnt == BATCH)
                {
                    Flush(ids, cnt);
                    ids[0] = ids[BATCH];
                    cnt = 0;
                }
            }
            else
            {
                if (c == '.' || c == '!' || c == '?')
                {
                    if (ids[cnt] != NONE)
                    {
                        ids[++cnt] = NONE;
                        if (cnt == BATCH)
                        {
                            Flush(ids, cnt);
                            ids[0] = ids[BATCH];
                            cnt = 0;
                        }
                    }
                }
                i++;
            }
        }
        Flush(ids, cnt);

        var tc = new uint[21];
        var ta = new uint[21];
        var tb = new uint[21];
        int nt = 0;
        foreach (var s in ptab)
        {
            if (s.Key == EMPTY) continue;
            uint count = s.Count;
            if (nt == 20 && count < tc[19]) continue;
            uint a = (uint)(s.Key >> 32), b = (uint)s.Key;
            if (nt == 20 && !Better(count, a, b, tc[19], ta[19], tb[19])) continue;
            int j = nt < 20 ? nt++ : 19;
            while (j > 0 && Better(count, a, b, tc[j - 1], ta[j - 1], tb[j - 1]))
            {
                tc[j] = tc[j - 1]; ta[j] = ta[j - 1]; tb[j] = tb[j - 1];
                j--;
            }
            tc[j] = count; ta[j] = a; tb[j] = b;
        }

        var sb = new StringBuilder();
        sb.Append("words ").Append(W).Append("\npairs ").Append(tcount).Append("\ndistinct ").Append(distinct).Append('\n');
        for (int k = 0; k < nt; k++)
        {
            sb.Append(tc[k]).Append(' ');
            AppendWord(sb, ta[k]);
            sb.Append(' ');
            AppendWord(sb, tb[k]);
            sb.Append('\n');
        }
        using (var stdout = Console.OpenStandardOutput())
        {
            var bytes = Encoding.ASCII.GetBytes(sb.ToString());
            stdout.Write(bytes, 0, bytes.Length);
        }
        if (sink == 42) Console.Error.WriteLine();
        return 0;
    }
}
