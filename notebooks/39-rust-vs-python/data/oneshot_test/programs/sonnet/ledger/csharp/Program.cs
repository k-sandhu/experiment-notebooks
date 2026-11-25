using System.Buffers;
using System.Numerics;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using System.Text;

sealed class ByteMap
{
    const ulong K = 0x9E3779B97F4A7C15UL;
    int[] table;
    int mask;
    public byte[][] Keys;
    public int[] Hashes;
    public long[] A;
    public long[] B;
    public int Count;

    public ByteMap(int cap)
    {
        table = new int[cap];
        mask = cap - 1;
        Keys = new byte[cap / 2][];
        Hashes = new int[cap / 2];
        A = new long[cap / 2];
        B = new long[cap / 2];
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    static int Hash(ReadOnlySpan<byte> s)
    {
        int n = s.Length;
        ulong h = (ulong)n * K;
        int i = 0;
        ref byte r = ref MemoryMarshal.GetReference(s);
        while (i + 8 <= n)
        {
            h = (BitOperations.RotateLeft(h, 23) ^ Unsafe.ReadUnaligned<ulong>(ref Unsafe.Add(ref r, i))) * K;
            i += 8;
        }
        if (i < n)
        {
            ulong t = 0;
            for (int j = i; j < n; j++) t |= (ulong)s[j] << ((j - i) * 8);
            h = (BitOperations.RotateLeft(h, 23) ^ t) * K;
        }
        h ^= h >> 32;
        h *= K;
        h ^= h >> 29;
        return (int)h;
    }

    public int Find(ReadOnlySpan<byte> s, bool insert)
    {
        int h = Hash(s);
        int idx = h & mask;
        while (true)
        {
            int e = table[idx];
            if (e == 0) break;
            int k = e - 1;
            if (Hashes[k] == h && Keys[k].AsSpan().SequenceEqual(s)) return k;
            idx = (idx + 1) & mask;
        }
        if (!insert) return -1;
        if (Count == Keys.Length)
        {
            int nl = Keys.Length * 2;
            Array.Resize(ref Keys, nl);
            Array.Resize(ref Hashes, nl);
            Array.Resize(ref A, nl);
            Array.Resize(ref B, nl);
        }
        int id = Count++;
        Keys[id] = s.ToArray();
        Hashes[id] = h;
        table[idx] = id + 1;
        if (Count * 2 > table.Length) Rehash();
        return id;
    }

    void Rehash()
    {
        int nc = table.Length * 2;
        table = new int[nc];
        mask = nc - 1;
        for (int k = 0; k < Count; k++)
        {
            int idx = Hashes[k] & mask;
            while (table[idx] != 0) idx = (idx + 1) & mask;
            table[idx] = k + 1;
        }
    }
}

static class Program
{
    static readonly SearchValues<byte> Struct = SearchValues.Create("\"{}[]"u8);
    static ByteMap rates = new ByteMap(64);
    static ByteMap chans = new ByteMap(64);
    static ByteMap accts = new ByteMap(1 << 16);
    static long total, net;

    static void SkipWs(ReadOnlySpan<byte> s, ref int p)
    {
        while (p < s.Length && s[p] <= (byte)' ') p++;
    }

    static ReadOnlySpan<byte> ReadString(ReadOnlySpan<byte> s, ref int p, out bool esc)
    {
        esc = false;
        p++;
        int start = p;
        while (true)
        {
            int i = s.Slice(p).IndexOfAny((byte)'"', (byte)'\\');
            if (i < 0) throw new FormatException("unterminated string");
            if (s[p + i] == (byte)'"')
            {
                int end = p + i;
                p = end + 1;
                return s.Slice(start, end - start);
            }
            esc = true;
            p += i + 2;
        }
    }

    static ReadOnlySpan<byte> Str(ReadOnlySpan<byte> s, ref int p)
    {
        var raw = ReadString(s, ref p, out bool esc);
        return esc ? Unescape(raw) : raw;
    }

    static int Hex4(ReadOnlySpan<byte> r, int i)
    {
        int v = 0;
        for (int k = 0; k < 4; k++)
        {
            int c = r[i + k];
            int d = c <= '9' ? c - '0' : (c | 0x20) - 'a' + 10;
            v = (v << 4) | d;
        }
        return v;
    }

    static byte[] Unescape(ReadOnlySpan<byte> r)
    {
        byte[] o = new byte[r.Length + 4];
        int n = 0;
        for (int i = 0; i < r.Length; i++)
        {
            byte b = r[i];
            if (b != (byte)'\\') { o[n++] = b; continue; }
            i++;
            byte e = r[i];
            switch (e)
            {
                case (byte)'n': o[n++] = 10; break;
                case (byte)'t': o[n++] = 9; break;
                case (byte)'r': o[n++] = 13; break;
                case (byte)'b': o[n++] = 8; break;
                case (byte)'f': o[n++] = 12; break;
                case (byte)'u':
                    {
                        int cp = Hex4(r, i + 1);
                        i += 4;
                        if (cp >= 0xD800 && cp <= 0xDBFF && i + 6 < r.Length + 0 && r[i + 1] == (byte)'\\' && r[i + 2] == (byte)'u')
                        {
                            int lo = Hex4(r, i + 3);
                            if (lo >= 0xDC00 && lo <= 0xDFFF)
                            {
                                cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
                                i += 6;
                            }
                        }
                        if (cp < 0x80) o[n++] = (byte)cp;
                        else if (cp < 0x800)
                        {
                            o[n++] = (byte)(0xC0 | (cp >> 6));
                            o[n++] = (byte)(0x80 | (cp & 0x3F));
                        }
                        else if (cp < 0x10000)
                        {
                            o[n++] = (byte)(0xE0 | (cp >> 12));
                            o[n++] = (byte)(0x80 | ((cp >> 6) & 0x3F));
                            o[n++] = (byte)(0x80 | (cp & 0x3F));
                        }
                        else
                        {
                            o[n++] = (byte)(0xF0 | (cp >> 18));
                            o[n++] = (byte)(0x80 | ((cp >> 12) & 0x3F));
                            o[n++] = (byte)(0x80 | ((cp >> 6) & 0x3F));
                            o[n++] = (byte)(0x80 | (cp & 0x3F));
                        }
                        break;
                    }
                default: o[n++] = e; break; // " \ /
            }
        }
        return o.AsSpan(0, n).ToArray();
    }

    static void SkipValue(ReadOnlySpan<byte> s, ref int p)
    {
        if (p >= s.Length) return;
        byte c = s[p];
        if (c == (byte)'"')
        {
            ReadString(s, ref p, out _);
            return;
        }
        if (c == (byte)'{' || c == (byte)'[')
        {
            int depth = 0;
            while (true)
            {
                int i = s.Slice(p).IndexOfAny(Struct);
                if (i < 0) { p = s.Length; return; }
                p += i;
                byte d = s[p];
                if (d == (byte)'"')
                {
                    ReadString(s, ref p, out _);
                    continue;
                }
                if (d == (byte)'{' || d == (byte)'[') depth++;
                else depth--;
                p++;
                if (depth == 0) return;
            }
        }
        while (p < s.Length)
        {
            byte d = s[p];
            if (d == (byte)',' || d == (byte)'}' || d == (byte)']' || d <= (byte)' ') break;
            p++;
        }
    }

    static void ParseRates(ReadOnlySpan<byte> s)
    {
        int p = 0;
        SkipWs(s, ref p);
        p++; // {
        while (true)
        {
            SkipWs(s, ref p);
            if (p >= s.Length) break;
            byte c = s[p];
            if (c == (byte)'}') break;
            if (c == (byte)',') { p++; continue; }
            var key = Str(s, ref p);
            SkipWs(s, ref p);
            p++; // :
            SkipWs(s, ref p);
            if (key.SequenceEqual("rates"u8) && p < s.Length && s[p] == (byte)'{')
            {
                p++;
                while (true)
                {
                    SkipWs(s, ref p);
                    if (p >= s.Length) break;
                    byte d = s[p];
                    if (d == (byte)'}') { p++; break; }
                    if (d == (byte)',') { p++; continue; }
                    var cur = Str(s, ref p);
                    SkipWs(s, ref p);
                    p++; // :
                    SkipWs(s, ref p);
                    long v = 0;
                    while (p < s.Length && s[p] >= (byte)'0' && s[p] <= (byte)'9')
                    {
                        v = v * 10 + (s[p] - '0');
                        p++;
                    }
                    int idx = rates.Find(cur, true);
                    rates.A[idx] = v;
                }
            }
            else SkipValue(s, ref p);
        }
    }

    static bool HasTest(ReadOnlySpan<byte> s, ref int p)
    {
        bool found = false;
        p++; // [
        while (p < s.Length)
        {
            SkipWs(s, ref p);
            if (p >= s.Length) break;
            byte c = s[p];
            if (c == (byte)']') { p++; break; }
            if (c == (byte)',') { p++; continue; }
            if (c == (byte)'"')
            {
                var v = Str(s, ref p);
                if (v.SequenceEqual("test"u8)) found = true;
            }
            else SkipValue(s, ref p);
        }
        return found;
    }

    static ReadOnlySpan<byte> ParseMeta(ReadOnlySpan<byte> s, ref int p)
    {
        ReadOnlySpan<byte> chan = default;
        p++; // {
        while (p < s.Length)
        {
            SkipWs(s, ref p);
            if (p >= s.Length) break;
            byte c = s[p];
            if (c == (byte)'}') { p++; break; }
            if (c == (byte)',') { p++; continue; }
            var key = Str(s, ref p);
            SkipWs(s, ref p);
            p++; // :
            SkipWs(s, ref p);
            if (key.SequenceEqual("channel"u8) && p < s.Length && s[p] == (byte)'"')
                chan = Str(s, ref p);
            else
                SkipValue(s, ref p);
        }
        return chan;
    }

    static long ParseAmount(ReadOnlySpan<byte> v)
    {
        long ip = 0;
        int i = 0, n = v.Length;
        while (i < n && v[i] != (byte)'.')
        {
            ip = ip * 10 + (v[i] - '0');
            i++;
        }
        long frac = 0;
        int digits = 0;
        if (i < n)
        {
            i++;
            while (i < n)
            {
                frac = frac * 10 + (v[i] - '0');
                digits++;
                i++;
            }
        }
        if (digits == 1) frac *= 10;
        return ip * 100 + frac;
    }

    static void Tx(ReadOnlySpan<byte> s)
    {
        int p = 0;
        int n = s.Length;
        ReadOnlySpan<byte> acct = default, cur = default, chan = default;
        long hund = 0;
        int sign = 0;
        bool test = false;
        p++; // {
        while (true)
        {
            SkipWs(s, ref p);
            if (p >= n) break;
            byte c = s[p];
            if (c == (byte)'}') break;
            if (c == (byte)',') { p++; continue; }
            var key = Str(s, ref p);
            SkipWs(s, ref p);
            p++; // :
            SkipWs(s, ref p);
            if (p >= n) break;
            bool isStr = s[p] == (byte)'"';
            if (key.SequenceEqual("account"u8) && isStr) acct = Str(s, ref p);
            else if (key.SequenceEqual("type"u8) && isStr)
            {
                var t = Str(s, ref p);
                if (t.SequenceEqual("credit"u8) || t.SequenceEqual("refund"u8)) sign = 1;
                else if (t.SequenceEqual("debit"u8)) sign = -1;
                else sign = 0;
            }
            else if (key.SequenceEqual("amount"u8) && isStr) hund = ParseAmount(Str(s, ref p));
            else if (key.SequenceEqual("currency"u8) && isStr) cur = Str(s, ref p);
            else if (key.SequenceEqual("tags"u8) && s[p] == (byte)'[') { if (HasTest(s, ref p)) test = true; }
            else if (key.SequenceEqual("meta"u8) && s[p] == (byte)'{') chan = ParseMeta(s, ref p);
            else SkipValue(s, ref p);
        }
        if (sign == 0 || test) return;
        int ri = rates.Find(cur, false);
        long rate = ri >= 0 ? rates.A[ri] : 0;
        long usd = hund * rate / 1000000;
        long signed = sign > 0 ? usd : -usd;
        total++;
        net += signed;
        int ci = chans.Find(chan, true);
        chans.A[ci]++;
        chans.B[ci] += signed;
        int ai = accts.Find(acct, true);
        accts.B[ai] += signed;
    }

    static bool first = true;

    static void Line(ReadOnlySpan<byte> s)
    {
        int p = 0;
        SkipWs(s, ref p);
        if (p >= s.Length) return;
        if (first)
        {
            first = false;
            ParseRates(s);
            return;
        }
        Tx(s.Slice(p));
    }

    static int CmpAcct(int a, int b)
    {
        long x = accts.B[a], y = accts.B[b];
        if (x != y) return x > y ? -1 : 1;
        return accts.Keys[a].AsSpan().SequenceCompareTo(accts.Keys[b]);
    }

    static void Main(string[] args)
    {
        using var fs = new FileStream(args[0], FileMode.Open, FileAccess.Read, FileShare.Read, 1, FileOptions.SequentialScan);
        byte[] buf = new byte[4 << 20];
        int len = 0;
        while (true)
        {
            int r = fs.Read(buf, len, buf.Length - len);
            if (r <= 0) break;
            len += r;
            int pos = 0;
            while (true)
            {
                int nl = buf.AsSpan(pos, len - pos).IndexOf((byte)'\n');
                if (nl < 0) break;
                Line(buf.AsSpan(pos, nl));
                pos += nl + 1;
            }
            int rem = len - pos;
            if (rem > 0 && pos > 0) Buffer.BlockCopy(buf, pos, buf, 0, rem);
            len = rem;
            if (len == buf.Length) Array.Resize(ref buf, buf.Length * 2);
        }
        if (len > 0) Line(buf.AsSpan(0, len));

        var sb = new StringBuilder();
        sb.Append("counted ").Append(total).Append('\n');
        sb.Append("net ").Append(net).Append('\n');

        int cc = chans.Count;
        int[] ci = new int[cc];
        for (int i = 0; i < cc; i++) ci[i] = i;
        Array.Sort(ci, (a, b) => chans.Keys[a].AsSpan().SequenceCompareTo(chans.Keys[b]));
        foreach (int i in ci)
        {
            sb.Append("channel ").Append(Encoding.UTF8.GetString(chans.Keys[i])).Append(' ')
              .Append(chans.A[i]).Append(' ').Append(chans.B[i]).Append('\n');
        }

        int[] top = new int[10];
        int tc = 0;
        for (int i = 0; i < accts.Count; i++)
        {
            if (tc == 10 && CmpAcct(i, top[9]) >= 0) continue;
            int j = tc < 10 ? tc++ : 9;
            while (j > 0 && CmpAcct(i, top[j - 1]) < 0)
            {
                top[j] = top[j - 1];
                j--;
            }
            top[j] = i;
        }
        for (int k = 0; k < tc; k++)
        {
            int i = top[k];
            sb.Append("account ").Append(Encoding.UTF8.GetString(accts.Keys[i])).Append(' ')
              .Append(accts.B[i]).Append('\n');
        }

        var o = Console.OpenStandardOutput();
        byte[] ob = Encoding.UTF8.GetBytes(sb.ToString());
        o.Write(ob, 0, ob.Length);
        o.Flush();
    }
}
