using System;
using System.Collections.Generic;
using System.IO;
using System.Text;

internal static class Program
{
    internal sealed class Key
    {
        public byte[] A = null!;
        public int Len;

        public bool Equals(Key? o)
        {
            if (ReferenceEquals(this, o)) return true;
            if (o is null || o.Len != Len) return false;
            byte[] x = A, y = o.A;
            for (int i = 0; i < Len; i++) if (x[i] != y[i]) return false;
            return true;
        }

        public override bool Equals(object? o) => o is Key k && Equals(k);

        public override int GetHashCode()
        {
            byte[] x = A;
            int h = 0;
            for (int i = 0; i < Len; i++) h = h * 31 + x[i];
            return h;
        }
    }

    internal sealed class Agg
    {
        public long Count;
        public long[] Lats = new long[16];
        public int N;

        public void Add(long v)
        {
            if (N == Lats.Length)
            {
                var nv = new long[N << 1];
                Array.Copy(Lats, nv, N);
                Lats = nv;
            }
            Lats[N++] = v;
        }
    }

    private static byte[] _scratch = new byte[512];
    private static readonly Key _lookupKey = new Key { A = _scratch };
    private static int _parsedCls;
    private static long _parsedLat;

    private static int Main(string[] args)
    {
        byte[] buf = File.ReadAllBytes(args[0]);
        int n = buf.Length;

        long lines = 0, malformed = 0;
        var statusCnt = new long[10];
        var aggs = new Dictionary<Key, Agg>(256);

        int i = 0;
        var bufSpan = buf.AsSpan();
        while (i < n)
        {
            int j = bufSpan.Slice(i).IndexOf((byte)'\n');
            j = j < 0 ? n : j + i;
            lines++;
            if (ParseLine(buf, i, j))
            {
                statusCnt[_parsedCls]++;
                var k = _lookupKey;
                if (!aggs.TryGetValue(k, out var a))
                {
                    var cp = new byte[k.Len];
                    Array.Copy(_scratch, cp, k.Len);
                    a = new Agg
                    {
                        Count = 1,
                    };
                    a.Lats[0] = _parsedLat;
                    a.N = 1;
                    aggs[new Key { A = cp, Len = k.Len }] = a;
                }
                else
                {
                    a.Count++;
                    a.Add(_parsedLat);
                }
            }
            else
            {
                malformed++;
            }
            i = j + 1;
        }

        var keys = new List<Key>(aggs.Count);
        foreach (var key in aggs.Keys) keys.Add(key);
        keys.Sort((x, y) =>
        {
            long cx = aggs[x].Count, cy = aggs[y].Count;
            if (cx != cy) return cx > cy ? -1 : 1;
            return CompareKeys(x, y);
        });

        var sb = new StringBuilder(4096);
        sb.Append("lines ").Append(lines).Append('\n');
        sb.Append("malformed ").Append(malformed).Append('\n');
        for (int d = 0; d < 10; d++)
        {
            if (statusCnt[d] == 0) continue;
            sb.Append("status ").Append(d).Append("xx ").Append(statusCnt[d]).Append('\n');
        }
        int top = Math.Min(10, keys.Count);
        for (int t = 0; t < top; t++)
        {
            var k = keys[t];
            var a = aggs[k];
            long[] l = new long[a.N];
            Array.Copy(a.Lats, l, a.N);
            Array.Sort(l);
            int m = l.Length;
            sb.Append("path ").Append(Encoding.ASCII.GetString(k.A, 0, k.Len))
              .Append(' ').Append(a.Count)
              .Append(' ').Append(Tenths(l[(50 * m + 99) / 100 - 1]))
              .Append(' ').Append(Tenths(l[(95 * m + 99) / 100 - 1]))
              .Append(' ').Append(Tenths(l[m - 1])).Append('\n');
        }
        using var stdout = Console.OpenStandardOutput();
        var bytes = Encoding.ASCII.GetBytes(sb.ToString());
        stdout.Write(bytes, 0, bytes.Length);
        return 0;
    }

    private static string Tenths(long v) => (v / 10) + "." + (v % 10);

    private static int CompareKeys(Key x, Key y)
    {
        int lim = Math.Min(x.Len, y.Len);
        byte[] a = x.A, b = y.A;
        for (int i = 0; i < lim; i++)
        {
            int c = a[i] - b[i];
            if (c != 0) return c;
        }
        return x.Len - y.Len;
    }

    private static bool ParseLine(byte[] buf, int s, int e)
    {
        int p = s;
        if (e - p < 26) return false;
        if (buf[p + 4] != (byte)'-' || buf[p + 7] != (byte)'-' || buf[p + 10] != (byte)'T' || buf[p + 13] != (byte)':'
            || buf[p + 16] != (byte)':' || buf[p + 19] != (byte)'.' || buf[p + 23] != (byte)'Z' || buf[p + 24] != (byte)' ')
            return false;
        for (int t = 0; t < TsDigits.Length; t++)
        {
            byte c = buf[p + TsDigits[t]];
            if (c < (byte)'0' || c > (byte)'9') return false;
        }
        p += 25;
        int s0 = p;
        while (p < e && buf[p] >= (byte)'a' && buf[p] <= (byte)'z') p++;
        if (p == s0 || p + 1 >= e || buf[p] != (byte)'-') return false;
        p++;
        int d0 = p;
        while (p < e && IsDig(buf[p])) p++;
        if (p == d0 || p + 1 >= e || buf[p] != (byte)' ') return false;
        p++;
        // method
        if (e - p >= 4 && buf[p] == 'G' && Match(buf, p, "ET ")) p += 4;
        else if (e - p >= 5 && buf[p] == 'P' && Match(buf, p, "OST ")) p += 5;
        else if (e - p >= 4 && buf[p] == 'P' && Match(buf, p, "UT ")) p += 4;
        else if (e - p >= 7 && buf[p] == 'D' && Match(buf, p, "ELETE ")) p += 7;
        else if (e - p >= 6 && buf[p] == 'P' && Match(buf, p, "ATCH ")) p += 6;
        else return false;
        // path
        if (buf[p] != (byte)'/') return false;
        int tl = 0;
        int need = ((e - p) << 2) + 16;
        if (_scratch.Length < need)
        {
            int cap = _scratch.Length;
            while (cap < need) cap <<= 1;
            _scratch = new byte[cap];
            _lookupKey.A = _scratch;
        }
        byte[] sc = _scratch;
        while (true)
        {
            int segStart = tl;
            while (p < e && IsSeg(buf[p])) { sc[tl++] = buf[p]; p++; }
            bool allDig = tl > segStart;
            for (int q = segStart; allDig && q < tl; q++) allDig = IsDig(sc[q]);
            if (allDig)
            {
                tl = segStart;
                sc[tl++] = (byte)'{'; sc[tl++] = (byte)'i'; sc[tl++] = (byte)'d'; sc[tl++] = (byte)'}';
            }
            if (p < e && buf[p] == (byte)'/') { sc[tl++] = (byte)'/'; p++; continue; }
            break;
        }
        if (p < e && buf[p] == (byte)'?') { p++; while (p < e && buf[p] != (byte)' ') p++; }
        if (p + 1 >= e || buf[p] != (byte)' ') return false;
        p++;
        // status
        if (e - p < 4 || !IsDig(buf[p]) || !IsDig(buf[p + 1]) || !IsDig(buf[p + 2])) return false;
        int cls = buf[p] - '0';
        p += 3;
        if (p + 1 >= e || buf[p] != (byte)' ') return false;
        p++;
        // size
        int b0 = p;
        while (p < e && IsDig(buf[p])) p++;
        if (p == b0 || e - p < 2 || buf[p] != (byte)'B' || buf[p + 1] != (byte)' ') return false;
        p += 2;
        // latency
        int l0 = p;
        while (p < e && IsDig(buf[p])) p++;
        if (p == l0 || e - p < 5 || buf[p] != (byte)'.' || !IsDig(buf[p + 1]) || buf[p + 2] != (byte)'m' || buf[p + 3] != (byte)'s' || buf[p + 4] != (byte)' ')
            return false;
        long v;
        if (p - l0 > 18)
        {
            v = 1_000_000_000_000_000L;  // saturate absurdly large latencies
        }
        else
        {
            v = 0;
            while (l0 < p) v = v * 10 + (buf[l0++] - '0');
            v = v * 10 + (buf[p + 1] - '0');
            if (v > 1_000_000_000_000_000L) v = 1_000_000_000_000_000L;
        }
        p += 5;
        // user agent
        if (buf[p] != (byte)'"') return false;
        p++;
        while (p < e && buf[p] != (byte)'"') p++;
        if (p != e - 1) return false;

        _lookupKey.Len = tl;
        _parsedCls = cls;
        _parsedLat = v;
        return true;
    }

    private static bool Match(byte[] buf, int p, string lit)
    {
        for (int i = 0; i < lit.Length; i++)
            if (buf[p + 1 + i] != (byte)lit[i]) return false;
        return true;
    }

    private static readonly int[] TsDigits = { 0, 1, 2, 3, 5, 6, 8, 9, 11, 12, 14, 15, 17, 18, 20, 21, 22 };

    private static bool IsDig(byte c) => c >= (byte)'0' && c <= (byte)'9';

    private static bool IsSeg(byte c)
        => (c >= (byte)'A' && c <= (byte)'Z') || (c >= (byte)'a' && c <= (byte)'z') || (c >= (byte)'0' && c <= (byte)'9')
           || c == (byte)'_' || c == (byte)'-';
}
