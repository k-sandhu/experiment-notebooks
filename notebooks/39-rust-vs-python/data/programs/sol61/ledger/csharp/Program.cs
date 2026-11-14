using System;
using System.Collections.Generic;
using System.IO;
using System.Text;

internal static class Program
{
    private struct Entry
    {
        public byte[] Key;
        public uint Hash;
        public long Count, Net;
    }
    // Compare UTF-8 spans directly, allocating an identifier only on first use.
    private sealed class Totals
    {
        public Entry[] Entries = new Entry[16];
        private int size;
        private static uint Hash(ReadOnlySpan<byte> key)
        {
            uint h = 2166136261;
            foreach (byte c in key) h = unchecked((h ^ c) * 16777619);
            return h;
        }
        private void Grow()
        {
            var next = new Entry[checked(Entries.Length * 2)];
            foreach (Entry e in Entries)
            {
                if (e.Key is null) continue;
                int slot = (int)(e.Hash & (uint)(next.Length - 1));
                while (next[slot].Key is not null) slot = (slot + 1) & (next.Length - 1);
                next[slot] = e;
            }
            Entries = next;
        }
        private ref Entry GetOrAdd(ReadOnlySpan<byte> key)
        {
            if (size >= Entries.Length * 3 / 4) Grow();
            uint h = Hash(key);
            int slot = (int)(h & (uint)(Entries.Length - 1));
            for (;;)
            {
                ref Entry e = ref Entries[slot];
                if (e.Key is null)
                {
                    e.Key = key.ToArray(); e.Hash = h; ++size;
                    return ref e;
                }
                if (e.Hash == h && key.SequenceEqual(e.Key)) return ref e;
                slot = (slot + 1) & (Entries.Length - 1);
            }
        }
        public void Set(ReadOnlySpan<byte> key, long value) => GetOrAdd(key).Net = value;
        public void Add(ReadOnlySpan<byte> key, long value)
        {
            ref Entry e = ref GetOrAdd(key);
            ++e.Count; e.Net = unchecked(e.Net + value);
        }
        public long Get(ReadOnlySpan<byte> key)
        {
            uint h = Hash(key);
            int slot = (int)(h & (uint)(Entries.Length - 1));
            for (;;)
            {
                ref Entry e = ref Entries[slot];
                if (e.Key is null) throw new KeyNotFoundException();
                if (e.Hash == h && key.SequenceEqual(e.Key)) return e.Net;
                slot = (slot + 1) & (Entries.Length - 1);
            }
        }
    }
    private ref struct Json
    {
        private ReadOnlySpan<byte> data;
        private int p;
        public Json(ReadOnlySpan<byte> data) { this.data = data; p = 0; }
        public void Ws() { while (data[p] <= 32) ++p; }
        public void Take() { Ws(); ++p; }
        public bool More(byte end)
        {
            Ws();
            if (data[p] == ',') { ++p; Ws(); }
            if (data[p] == end) { ++p; return false; }
            return true;
        }
        public ReadOnlySpan<byte> Str()
        {
            Ws(); int start = ++p;
            while (data[p] != '"' && data[p] != '\\') ++p;
            if (data[p] == '"') return data.Slice(start, p++ - start);
            p = start - 1; SkipString();
            int end = p - 1, n = 0;
            byte[] decoded = new byte[end - start];
            for (int i = start; i < end;)
            {
                byte c = data[i++];
                if (c != '\\') { decoded[n++] = c; continue; }
                c = data[i++];
                switch (c)
                {
                    case (byte)'b': decoded[n++] = 8; break;
                    case (byte)'f': decoded[n++] = 12; break;
                    case (byte)'n': decoded[n++] = 10; break;
                    case (byte)'r': decoded[n++] = 13; break;
                    case (byte)'t': decoded[n++] = 9; break;
                    case (byte)'u':
                        int cp = Hex4(ref i);
                        if (cp >= 0xd800 && cp <= 0xdbff && i + 6 <= end && data[i] == '\\' && data[i + 1] == 'u')
                        {
                            int saved = i; i += 2;
                            int low = Hex4(ref i);
                            if (low >= 0xdc00 && low <= 0xdfff) cp = 0x10000 + ((cp - 0xd800) << 10) + low - 0xdc00;
                            else i = saved;
                        }
                        Utf8(decoded, ref n, cp); break;
                    default: decoded[n++] = c; break;
                }
            }
            return decoded.AsSpan(0, n);
        }
        private int Hex4(ref int i)
        {
            int n = 0;
            for (int k = 0; k < 4; ++k)
            {
                byte c = data[i++];
                n = n * 16 + (c <= '9' ? c - '0' : (c | 32) - 'a' + 10);
            }
            return n;
        }
        private static void Utf8(byte[] s, ref int n, int cp)
        {
            if (cp < 0x80) s[n++] = (byte)cp;
            else if (cp < 0x800)
            {
                s[n++] = (byte)(0xc0 | (cp >> 6)); s[n++] = (byte)(0x80 | (cp & 63));
            }
            else if (cp < 0x10000)
            {
                s[n++] = (byte)(0xe0 | (cp >> 12)); s[n++] = (byte)(0x80 | ((cp >> 6) & 63)); s[n++] = (byte)(0x80 | (cp & 63));
            }
            else
            {
                s[n++] = (byte)(0xf0 | (cp >> 18)); s[n++] = (byte)(0x80 | ((cp >> 12) & 63));
                s[n++] = (byte)(0x80 | ((cp >> 6) & 63)); s[n++] = (byte)(0x80 | (cp & 63));
            }
        }
        public void SkipString()
        {
            ++p;
            while (data[p] != '"') { if (data[p] == '\\') ++p; ++p; }
            ++p;
        }
        public void Skip()
        {
            Ws();
            if (data[p] == '"') { SkipString(); return; }
            if (data[p] == '{' || data[p] == '[')
            {
                int depth = 1; ++p;
                while (depth != 0)
                {
                    byte c = data[p];
                    if (c == '"') { SkipString(); continue; }
                    ++p;
                    if (c == '{' || c == '[') ++depth;
                    else if (c == '}' || c == ']') --depth;
                }
            }
            else while (data[p] > 32 && data[p] != ',' && data[p] != '}' && data[p] != ']') ++p;
        }
        public long Integer()
        {
            Ws(); bool negative = data[p] == '-';
            if (negative) ++p;
            int start = p, digits = 0, fraction = 0;
            bool dot = false;
            while ((data[p] >= '0' && data[p] <= '9') || data[p] == '.')
            {
                if (data[p] == '.') dot = true;
                else { ++digits; if (dot) ++fraction; }
                ++p;
            }
            int end = p;
            long exponent = 0, cap = 1L << 60;
            if (data[p] == 'e' || data[p] == 'E')
            {
                ++p; bool eneg = data[p] == '-';
                if (data[p] == '+' || data[p] == '-') ++p;
                while (data[p] >= '0' && data[p] <= '9')
                {
                    exponent = exponent > cap / 10 ? cap : Math.Min(cap, exponent * 10 + data[p] - '0'); ++p;
                }
                if (eneg) exponent = -exponent;
            }
            long scale = exponent - fraction, keep = digits + Math.Min(scale, 0);
            ulong n = 0;
            for (int i = start; i < end && keep > 0; ++i) if (data[i] != '.')
            {
                n = unchecked(n * 10 + data[i] - '0'); --keep;
            }
            if (scale >= 64) n = 0;
            else for (long i = 0; i < scale; ++i) n = unchecked(n * 10);
            return negative ? unchecked((long)(0UL - n)) : unchecked((long)n);
        }
    }
    private static readonly Totals Rates = new(), Accounts = new(), Channels = new();
    private static long counted, net;
    private static long Hundredths(ReadOnlySpan<byte> s)
    {
        long n = 0; int i = 0;
        while (i < s.Length && s[i] != '.') n = unchecked(n * 10 + s[i++] - '0');
        n = unchecked(n * 100);
        if (i < s.Length)
        {
            ++i; n = unchecked(n + (s[i++] - '0') * 10);
            if (i < s.Length) n = unchecked(n + s[i] - '0');
        }
        return n;
    }
    private static void Header(ReadOnlySpan<byte> line)
    {
        var j = new Json(line); j.Take();
        while (j.More((byte)'}'))
        {
            var key = j.Str(); j.Take();
            if (!key.SequenceEqual("rates"u8)) { j.Skip(); continue; }
            j.Take();
            while (j.More((byte)'}'))
            {
                var name = j.Str(); j.Take();
                Rates.Set(name, j.Integer());
            }
        }
    }
    private static void Transaction(ReadOnlySpan<byte> line)
    {
        var j = new Json(line); j.Take();
        ReadOnlySpan<byte> account = default, channel = default, currency = default;
        long amount = 0;
        bool debit = false;
        while (j.More((byte)'}'))
        {
            var key = j.Str(); j.Take();
            if (key.SequenceEqual("account"u8)) account = j.Str();
            else if (key.SequenceEqual("currency"u8)) currency = j.Str();
            else if (key.SequenceEqual("amount"u8)) amount = Hundredths(j.Str());
            else if (key.SequenceEqual("type"u8))
            {
                var type = j.Str();
                if (type.SequenceEqual("void"u8)) return;
                debit = type.SequenceEqual("debit"u8);
            }
            else if (key.SequenceEqual("tags"u8))
            {
                j.Take();
                while (j.More((byte)']')) if (j.Str().SequenceEqual("test"u8)) return;
            }
            else if (key.SequenceEqual("meta"u8))
            {
                j.Take();
                while (j.More((byte)'}'))
                {
                    var metaKey = j.Str(); j.Take();
                    if (metaKey.SequenceEqual("channel"u8)) channel = j.Str();
                    else j.Skip();
                }
            }
            else j.Skip();
        }
        long product = unchecked(amount * Rates.Get(currency));
        long value = product / 1_000_000;
        if (product < 0 && product % 1_000_000 != 0) --value;
        if (debit) value = -value;
        ++counted; net = unchecked(net + value);
        Accounts.Add(account, value);
        Channels.Add(channel, value);
    }
    private static bool Better(Entry a, Entry b) =>
        a.Net != b.Net ? a.Net > b.Net : a.Key.AsSpan().SequenceCompareTo(b.Key) < 0;
    private static void Output()
    {
        var output = new StringBuilder();
        output.Append("counted ").Append(counted).Append("\nnet ").Append(net).Append('\n');
        var channels = new List<Entry>();
        foreach (Entry e in Channels.Entries) if (e.Key is not null) channels.Add(e);
        channels.Sort((a, b) => a.Key.AsSpan().SequenceCompareTo(b.Key));
        foreach (Entry c in channels)
            output.Append("channel ").Append(Encoding.UTF8.GetString(c.Key)).Append(' ').Append(c.Count).Append(' ').Append(c.Net).Append('\n');
        var top = new Entry[10];
        int length = 0;
        foreach (Entry a in Accounts.Entries)
        {
            if (a.Key is null) continue;
            int pos = 0;
            while (pos < length && !Better(a, top[pos])) ++pos;
            if (pos == 10) continue;
            int last = Math.Min(length, 9);
            for (int i = last; i > pos; --i) top[i] = top[i - 1];
            top[pos] = a;
            if (length < 10) ++length;
        }
        for (int i = 0; i < length; ++i)
            output.Append("account ").Append(Encoding.UTF8.GetString(top[i].Key)).Append(' ').Append(top[i].Net).Append('\n');
        Console.Write(output);
    }
    public static int Main(string[] args)
    {
        if (args.Length == 0) return 1;
        using var input = new FileStream(args[0], FileMode.Open, FileAccess.Read, FileShare.Read, 1 << 16, FileOptions.SequentialScan);
        byte[] buffer = new byte[1 << 20];
        int used = 0;
        bool first = true;
        for (;;)
        {
            if (used == buffer.Length) Array.Resize(ref buffer, checked(buffer.Length * 2));
            int n = input.Read(buffer, used, buffer.Length - used);
            if (n == 0) break;
            int end = used + n, start = 0;
            while (start < end)
            {
                int offset = buffer.AsSpan(start, end - start).IndexOf((byte)'\n');
                if (offset < 0) break;
                var line = buffer.AsSpan(start, offset);
                if (first) { Header(line); first = false; }
                else Transaction(line);
                start += offset + 1;
            }
            used = end - start;
            buffer.AsSpan(start, used).CopyTo(buffer);
        }
        if (used != 0)
        {
            if (first) Header(buffer.AsSpan(0, used));
            else Transaction(buffer.AsSpan(0, used));
        }
        Output();
        return 0;
    }
}
