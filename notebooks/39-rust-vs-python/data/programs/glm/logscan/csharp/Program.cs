using System;
using System.IO;
using System.Text;

internal static class Program
{
    // ---- open-addressing hash map: template -> stats ----
    private static byte[][] keys = new byte[64][];
    private static long[] hashes = new long[64];
    private static long[] counts = new long[64];
    private static int[][] lats = new int[64][];
    private static int[] latLens = new int[64];
    private static int numEntries;
    private static int[] table = new int[1024];
    private static int tmask = 1023;
    private static int used;

    private static void PutEntry(byte[] buf, int len, long h)
    {
        if (numEntries == keys.Length)
        {
            Array.Resize(ref keys, numEntries * 2);
            Array.Resize(ref hashes, numEntries * 2);
            Array.Resize(ref counts, numEntries * 2);
            Array.Resize(ref lats, numEntries * 2);
            Array.Resize(ref latLens, numEntries * 2);
        }
        var k = new byte[len];
        Buffer.BlockCopy(buf, 0, k, 0, len);
        keys[numEntries] = k;
        hashes[numEntries] = h;
        lats[numEntries] = new int[16];
        numEntries++;
    }

    private static int Lookup(byte[] buf, int len, long h)
    {
        int i = (int)(h & tmask);
        while (table[i] != 0)
        {
            int e = table[i] - 1;
            if (hashes[e] == h)
            {
                byte[] k = keys[e];
                if (k.Length == len)
                {
                    bool eq = true;
                    for (int z = 0; z < len; z++)
                    {
                        if (k[z] != buf[z]) { eq = false; break; }
                    }
                    if (eq) return e;
                }
            }
            i = (i + 1) & tmask;
        }
        PutEntry(buf, len, h);
        table[i] = numEntries;
        used++;
        if (used * 10 >= table.Length * 7) Rehash();
        return numEntries - 1;
    }

    private static void Rehash()
    {
        int ncap = table.Length * 2;
        table = new int[ncap];
        tmask = ncap - 1;
        for (int e = 0; e < numEntries; e++)
        {
            int i = (int)(hashes[e] & tmask);
            while (table[i] != 0) i = (i + 1) & tmask;
            table[i] = e + 1;
        }
    }

    private static int tlen, tenths, cls, ps, pe;
    private static byte[] tbGlobal = new byte[512];

    private static unsafe bool Parse(byte* d, int baseIdx, int n)
    {
        byte[] tb = tbGlobal;
        if (n < 50) return false;
        byte* s = d + baseIdx;
        int end = n;
        int i = 0;
        // timestamp: dddd-dd-ddTdd:dd:dd.dddZ
        if (!(Digit(s[0]) && Digit(s[1]) && Digit(s[2]) && Digit(s[3]) && s[4] == '-' &&
              Digit(s[5]) && Digit(s[6]) && s[7] == '-' && Digit(s[8]) && Digit(s[9]) &&
              s[10] == 'T' && Digit(s[11]) && Digit(s[12]) && s[13] == ':' &&
              Digit(s[14]) && Digit(s[15]) && s[16] == ':' && Digit(s[17]) && Digit(s[18]) &&
              s[19] == '.' && Digit(s[20]) && Digit(s[21]) && Digit(s[22]) && s[23] == 'Z'))
            return false;
        i = 24;
        if (s[i++] != (byte)' ') return false;
        // host [a-z]+-\d+
        int st = i;
        while (i < end && s[i] >= (byte)'a' && s[i] <= (byte)'z') i++;
        if (i == st || i >= end || s[i] != (byte)'-') return false;
        i++;
        st = i;
        while (i < end && Digit(s[i])) i++;
        if (i == st || i >= end || s[i] != (byte)' ') return false;
        i++;
        int rem = end - i;
        if (rem >= 4 && s[i] == (byte)'G' && s[i + 1] == (byte)'E' && s[i + 2] == (byte)'T' && s[i + 3] == (byte)' ') i += 4;
        else if (rem >= 4 && s[i] == (byte)'P' && s[i + 1] == (byte)'U' && s[i + 2] == (byte)'T' && s[i + 3] == (byte)' ') i += 4;
        else if (rem >= 5 && s[i] == (byte)'P' && s[i + 1] == (byte)'O' && s[i + 2] == (byte)'S' && s[i + 3] == (byte)'T' && s[i + 4] == (byte)' ') i += 5;
        else if (rem >= 6 && s[i] == (byte)'P' && s[i + 1] == (byte)'A' && s[i + 2] == (byte)'T' && s[i + 3] == (byte)'C' && s[i + 4] == (byte)'H' && s[i + 5] == (byte)' ') i += 6;
        else if (rem >= 7 && s[i] == (byte)'D' && s[i + 1] == (byte)'E' && s[i + 2] == (byte)'L' && s[i + 3] == (byte)'E' && s[i + 4] == (byte)'T' && s[i + 5] == (byte)'E' && s[i + 6] == (byte)' ') i += 7;
        else return false;
        if (end - i < 17) return false;
        if (s[i] != (byte)'/') return false;
        ps = i;
        i++;
        while (i < end)
        {
            uint c = s[i];
            if ((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') ||
                c == (byte)'_' || c == (byte)'-' || c == (byte)'/') i++;
            else break;
        }
        pe = i;
        if (i < end && s[i] == (byte)'?')
        {
            i++;
            while (i < end && s[i] != (byte)' ') i++;
        }
        if (i >= end || s[i] != (byte)' ') return false;
        i++;
        if (end - i < 15) return false;
        if (!(Digit(s[i]) && Digit(s[i + 1]) && Digit(s[i + 2]))) return false;
        cls = s[i] - (byte)'0';
        i += 3;
        if (s[i++] != (byte)' ') return false;
        if (end - i < 11) return false;
        st = i;
        while (i < end && Digit(s[i])) i++;
        if (i == st || s[i] != (byte)'B') return false;
        i++;
        if (s[i++] != (byte)' ') return false;
        st = i;
        long v = 0;
        int nd = 0;
        while (i < end && Digit(s[i]))
        {
            if (nd < 15) v = v * 10 + (s[i] - (byte)'0');
            i++; nd++;
        }
        if (i == st || s[i] != (byte)'.') return false;
        i++;
        if (!Digit(s[i])) return false;
        v = v * 10 + (s[i] - (byte)'0');
        i++;
        if (s[i] != (byte)'m' || s[i + 1] != (byte)'s' || s[i + 2] != (byte)' ') return false;
        tenths = v > 0xFFFFFFFFL ? unchecked((int)0xFFFFFFFFL) : (int)v;
        i += 3;
        if (s[i] != (byte)'"') return false;
        i++;
        while (i < end && s[i] != (byte)'"') i++;
        if (i + 1 != end) return false;

        // build template
        int need = (pe - ps) * 5 + 8;
        if (tb.Length < need) tbGlobal = tb = new byte[need * 2];
        int t = 0;
        int k = ps;
        while (k < pe)
        {
            tb[t++] = (byte)'/';
            k++;
            int s0 = k;
            while (k < pe && s[k] != (byte)'/') k++;
            int slen = k - s0;
            bool dig = slen > 0;
            for (int z = 0; dig && z < slen; z++)
                if (!Digit(s[s0 + z])) { dig = false; break; }
            if (dig)
            {
                tb[t] = (byte)'{'; tb[t + 1] = (byte)'i'; tb[t + 2] = (byte)'d'; tb[t + 3] = (byte)'}';
                t += 4;
            }
            else
            {
                for (int z = 0; z < slen; z++) tb[t + z] = s[s0 + z];
                t += slen;
            }
        }
        tlen = t;
        return true;
    }

    private static bool Digit(byte c) => c >= (byte)'0' && c <= (byte)'9';

    private static int Main(string[] args)
    {
        string path = args[0];
        byte[] d;
        using (var fs = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read, 1 << 20, FileOptions.SequentialScan))
        {
            long sz = fs.Length;
            d = new byte[sz];
            int off = 0;
            while (off < sz)
            {
                int r = fs.Read(d, off, (int)(sz - off));
                if (r <= 0) break;
                off += r;
            }
        }

        int n = d.Length;
        long lines = 0, malformed = 0;
        long[] clsCount = new long[10];

        unsafe
        {
            fixed (byte* dp = d)
            {
                int i = 0;
                while (i < n)
                {
                    int rel = new ReadOnlySpan<byte>(dp + i, n - i).IndexOf((byte)'\n');
                    int le = rel < 0 ? n : i + rel;
                    int len = le - i;
                    lines++;

                    if (Parse(dp, i, len))
                    {
                        int t = tlen;
                        long h = 2166136261L;
                        byte[] tb = tbGlobal;
                        for (int z = 0; z < t; z++) { h ^= (tb[z] & 0xFFL); h *= 16777619L; }
                        int e = Lookup(tb, t, h);
                        counts[e]++;
                        int[] la = lats[e];
                        if (latLens[e] == la.Length)
                        {
                            var nl = new int[la.Length * 2];
                            Buffer.BlockCopy(la, 0, nl, 0, la.Length * 4);
                            lats[e] = la = nl;
                        }
                        la[latLens[e]++] = tenths;
                        clsCount[cls]++;
                    }
                    else
                    {
                        malformed++;
                    }
                    i = le + 1;
                }
            }
        }

        int[] ord = new int[numEntries];
        for (int e = 0; e < numEntries; e++) ord[e] = e;
        Array.Sort(ord, (a, b) =>
        {
            if (counts[a] != counts[b]) return counts[a] > counts[b] ? -1 : 1;
            byte[] ka = keys[a], kb = keys[b];
            int la2 = ka.Length, lb2 = kb.Length, mn = la2 < lb2 ? la2 : lb2;
            for (int z = 0; z < mn; z++)
            {
                int ca = ka[z] & 0xFF, cb = kb[z] & 0xFF;
                if (ca != cb) return ca < cb ? -1 : 1;
            }
            return la2.CompareTo(lb2);
        });

        var sb = new StringBuilder(512);
        sb.Append("lines ").Append(lines).Append('\n');
        sb.Append("malformed ").Append(malformed).Append('\n');
        for (int dd = 0; dd < 10; dd++)
            if (clsCount[dd] > 0) sb.Append("status ").Append(dd).Append("xx ").Append(clsCount[dd]).Append('\n');
        int top = Math.Min(10, numEntries);
        var latin1 = Encoding.GetEncoding(28591);
        for (int r = 0; r < top; r++)
        {
            int e = ord[r];
            int[] la = new int[latLens[e]];
            Buffer.BlockCopy(lats[e], 0, la, 0, latLens[e] * 4);
            Array.Sort(la);
            int nn = la.Length;
            int p50 = la[(50 * nn + 99) / 100 - 1];
            int p95 = la[(95 * nn + 99) / 100 - 1];
            int mx = la[nn - 1];
            sb.Append("path ").Append(latin1.GetString(keys[e], 0, keys[e].Length))
              .Append(' ').Append(counts[e]).Append(' ')
              .Append(p50 / 10).Append('.').Append(p50 % 10).Append(' ')
              .Append(p95 / 10).Append('.').Append(p95 % 10).Append(' ')
              .Append(mx / 10).Append('.').Append(mx % 10).Append('\n');
        }
        var outBytes = latin1.GetBytes(sb.ToString());
        using (var so = Console.OpenStandardOutput())
            so.Write(outBytes, 0, outBytes.Length);
        return 0;
    }
}
