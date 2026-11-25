// Ledger: streaming JSON Lines scanner with exact integer currency conversion.
using System.Numerics;
using System.Runtime.CompilerServices;
using System.Runtime.Intrinsics;
using System.Text;

unsafe
{
    if (args.Length < 1) return 1;
    var ledger = new Ledger();
    ledger.Run(args[0]);
    ledger.Print();
    return 0;
}

/// <summary>Open-addressing table interning byte strings to dense indices, with per-entry totals.</summary>
sealed class Interner
{
    int[] _slots = new int[1024]; // index + 1, 0 = empty
    int[] _slotHash = new int[1024];
    int _mask = 1023;
    public byte[][] Keys = new byte[64][];
    public long[] Sum = new long[64];
    public long[] Count = new long[64];
    public int Size;

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    static unsafe int Hash(byte* s, int n)
    {
        ulong h = 0x9E3779B97F4A7C15UL ^ (ulong)n;
        while (n >= 8)
        {
            h = (h ^ Unsafe.ReadUnaligned<ulong>(s)) * 0xbf58476d1ce4e5b9UL;
            h ^= h >> 31;
            s += 8;
            n -= 8;
        }
        ulong w = 0;
        for (int i = 0; i < n; i++) w |= (ulong)s[i] << (8 * i);
        h = (h ^ w) * 0x94d049bb133111ebUL;
        h ^= h >> 29;
        return (int)h;
    }

    public unsafe int Find(byte* s, int n)
    {
        int h = Hash(s, n);
        var key = new ReadOnlySpan<byte>(s, n);
        for (int i = h & _mask; ; i = (i + 1) & _mask)
        {
            int slot = _slots[i];
            if (slot == 0) return -1;
            if (_slotHash[i] == h && key.SequenceEqual(Keys[slot - 1])) return slot - 1;
        }
    }

    public unsafe int Intern(byte* s, int n)
    {
        int h = Hash(s, n);
        var key = new ReadOnlySpan<byte>(s, n);
        for (int i = h & _mask; ; i = (i + 1) & _mask)
        {
            int slot = _slots[i];
            if (slot == 0)
            {
                if (Size == Keys.Length)
                {
                    Array.Resize(ref Keys, Size * 2);
                    Array.Resize(ref Sum, Size * 2);
                    Array.Resize(ref Count, Size * 2);
                }
                Keys[Size] = key.ToArray();
                _slots[i] = ++Size;
                _slotHash[i] = h;
                if (Size * 2 > _slots.Length) Grow();
                return Size - 1;
            }
            if (_slotHash[i] == h && key.SequenceEqual(Keys[slot - 1])) return slot - 1;
        }
    }

    void Grow()
    {
        int[] os = _slots, oh = _slotHash;
        _slots = new int[os.Length * 2];
        _slotHash = new int[os.Length * 2];
        _mask = _slots.Length - 1;
        for (int j = 0; j < os.Length; j++)
        {
            if (os[j] == 0) continue;
            int i = oh[j] & _mask;
            while (_slots[i] != 0) i = (i + 1) & _mask;
            _slots[i] = os[j];
            _slotHash[i] = oh[j];
        }
    }
}

/// <summary>Growable byte buffer for decoded strings; pinned so it can be addressed by pointer.</summary>
sealed unsafe class Scratch
{
    public byte[] Data = GC.AllocateUninitializedArray<byte>(256, pinned: true);
    public byte* Ptr;
    public Scratch() { fixed (byte* p = Data) Ptr = p; }

    public void Ensure(int n)
    {
        if (n <= Data.Length) return;
        var d = GC.AllocateUninitializedArray<byte>(Math.Max(n, Data.Length * 2), pinned: true);
        Data.CopyTo(d, 0);
        Data = d;
        fixed (byte* p = Data) Ptr = p;
    }
}

sealed unsafe class Ledger
{

    readonly Interner _currencies = new();
    readonly Interner _channels = new();
    readonly Interner _accounts = new();
    long _counted, _net;

    readonly Scratch _sKey = new(), _sAcc = new(), _sChan = new(), _sType = new(), _sAmt = new(), _sCur = new(), _sTag = new();

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    static bool IsWs(byte c) => c == ' ' || c == '\n' || c == '\r' || c == '\t';

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    static byte* SkipWs(byte* p)
    {
        while (IsWs(*p)) p++;
        return p;
    }

    static int HexVal(byte c) => c <= '9' ? c - '0' : (c | 0x20) - 'a' + 10;

    static int Hex4(byte* p) => (HexVal(p[0]) << 12) | (HexVal(p[1]) << 8) | (HexVal(p[2]) << 4) | HexVal(p[3]);

    /// <summary>First quote or backslash at or after p, 16 bytes at a time (the buffer has slack for over-reads).</summary>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    static byte* FindQuoteOrEscape(byte* p)
    {
        var q = Vector128.Create((byte)'"');
        var bs = Vector128.Create((byte)0x5C);
        while (true)
        {
            var x = Vector128.Load(p);
            uint m = (Vector128.Equals(x, q) | Vector128.Equals(x, bs)).ExtractMostSignificantBits();
            if (m != 0) return p + BitOperations.TrailingZeroCount(m);
            p += 16;
        }
    }

    /// <summary>Parses the string whose opening quote is at p; the result points into the input unless it had escapes.</summary>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    byte* ParseStr(byte* p, out byte* s, out int n, Scratch scratch)
    {
        byte* b = ++p;
        while (true)
        {
            byte c = *p;
            if (c == '"')
            {
                s = b;
                n = (int)(p - b);
                return p + 1;
            }
            if (c == '\\') return DecodeStr(b, p, out s, out n, scratch);
            p++;
        }
    }

    [MethodImpl(MethodImplOptions.NoInlining)]
    static byte* DecodeStr(byte* b, byte* p, out byte* s, out int n, Scratch scratch)
    {
        int len = (int)(p - b);
        scratch.Ensure(len + 16);
        new ReadOnlySpan<byte>(b, len).CopyTo(scratch.Data);
        while (true)
        {
            scratch.Ensure(len + 8);
            byte* o = scratch.Ptr;
            byte c = *p;
            if (c == '"') break;
            if (c != '\\')
            {
                o[len++] = c;
                p++;
                continue;
            }
            byte e = p[1];
            p += 2;
            switch (e)
            {
                case (byte)'n': o[len++] = (byte)'\n'; break;
                case (byte)'t': o[len++] = (byte)'\t'; break;
                case (byte)'r': o[len++] = (byte)'\r'; break;
                case (byte)'b': o[len++] = (byte)'\b'; break;
                case (byte)'f': o[len++] = (byte)'\f'; break;
                case (byte)'u':
                    {
                        int cp = Hex4(p);
                        p += 4;
                        if (cp >= 0xD800 && cp < 0xDC00 && p[0] == '\\' && p[1] == 'u')
                        {
                            int lo = Hex4(p + 2);
                            if (lo >= 0xDC00 && lo < 0xE000)
                            {
                                cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
                                p += 6;
                            }
                        }
                        if (cp < 0x80) o[len++] = (byte)cp;
                        else if (cp < 0x800)
                        {
                            o[len++] = (byte)(0xC0 | (cp >> 6));
                            o[len++] = (byte)(0x80 | (cp & 0x3F));
                        }
                        else if (cp < 0x10000)
                        {
                            o[len++] = (byte)(0xE0 | (cp >> 12));
                            o[len++] = (byte)(0x80 | ((cp >> 6) & 0x3F));
                            o[len++] = (byte)(0x80 | (cp & 0x3F));
                        }
                        else
                        {
                            o[len++] = (byte)(0xF0 | (cp >> 18));
                            o[len++] = (byte)(0x80 | ((cp >> 12) & 0x3F));
                            o[len++] = (byte)(0x80 | ((cp >> 6) & 0x3F));
                            o[len++] = (byte)(0x80 | (cp & 0x3F));
                        }
                        break;
                    }
                default: o[len++] = e; break;
            }
        }
        s = scratch.Ptr;
        n = len;
        return p + 1;
    }

    byte* SkipStrBody(byte* p)
    {
        while (true)
        {
            p = FindQuoteOrEscape(p);
            if (*p == '"') return p + 1;
            p += 2;
        }
    }

    byte* SkipContainer(byte* p)
    {
        int depth = 1;
        p++;
        while (true)
        {
            var q = Vector128.Create((byte)'"');
            var bracketMask = Vector128.Create((byte)0xD9); // {, }, [, ] all become 0x59 (so do Y, _, y, DEL)
            var brackets = Vector128.Create((byte)0x59);
            uint m;
            while (true)
            {
                var x = Vector128.Load(p);
                m = (Vector128.Equals(x, q) | Vector128.Equals(x & bracketMask, brackets)).ExtractMostSignificantBits();
                if (m != 0) break;
                p += 16;
            }
            p += BitOperations.TrailingZeroCount(m);
            byte c = *p++;
            if (c == '"') p = SkipStrBody(p);
            else if (c == '{' || c == '[') depth++;
            else if (c == '}' || c == ']')
            {
                if (--depth == 0) return p;
            }
        }
    }

    byte* SkipVal(byte* p)
    {
        byte c = *p;
        if (c == '"') return SkipStrBody(p + 1);
        if (c == '{' || c == '[') return SkipContainer(p);
        while (!(c == ',' || c == '}' || c == ']' || IsWs(c))) c = *++p;
        return p;
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    static bool Is(byte* s, int n, ReadOnlySpan<byte> lit) => n == lit.Length && new ReadOnlySpan<byte>(s, n).SequenceEqual(lit);

    byte* ParseRates(byte* p)
    {
        p = SkipWs(p + 1);
        if (*p == '}') return p + 1;
        while (true)
        {
            p = ParseStr(p, out byte* k, out int kn, _sKey);
            bool isRates = Is(k, kn, "rates"u8);
            p = SkipWs(SkipWs(p) + 1);
            if (isRates && *p == '{')
            {
                p = SkipWs(p + 1);
                if (*p != '}')
                {
                    while (true)
                    {
                        p = ParseStr(p, out byte* cs, out int cn, _sCur);
                        int id = _currencies.Intern(cs, cn);
                        p = SkipWs(SkipWs(p) + 1);
                        bool neg = false;
                        if (*p == '-')
                        {
                            neg = true;
                            p++;
                        }
                        long v = 0;
                        while (*p >= '0' && *p <= '9') v = v * 10 + (*p++ - '0');
                        p = SkipVal(p);
                        _currencies.Sum[id] = neg ? -v : v;
                        p = SkipWs(p);
                        if (*p == ',')
                        {
                            p = SkipWs(p + 1);
                            continue;
                        }
                        break;
                    }
                }
                p++;
            }
            else
            {
                p = SkipVal(p);
            }
            p = SkipWs(p);
            if (*p == ',')
            {
                p = SkipWs(p + 1);
                continue;
            }
            return p + 1;
        }
    }

    byte* ParseTx(byte* p)
    {
        byte* acc = null, chan = null, cur = null, amt = null;
        int accN = 0, chanN = 0, curN = 0, amtN = 0;
        long sign = 0;
        bool test = false;

        p = SkipWs(p + 1);
        if (*p == '}') return p + 1;
        while (true)
        {
            p = ParseStr(p, out byte* k, out int kn, _sKey);
            p = SkipWs(SkipWs(p) + 1);
            if (kn == 4 && Is(k, kn, "type"u8))
            {
                p = ParseStr(p, out byte* t, out int tn, _sType);
                if (Is(t, tn, "credit"u8) || Is(t, tn, "refund"u8)) sign = 1;
                else if (Is(t, tn, "debit"u8)) sign = -1;
                else sign = 0;
            }
            else if (kn == 4 && Is(k, kn, "tags"u8))
            {
                p = SkipWs(p + 1);
                if (*p != ']')
                {
                    while (true)
                    {
                        if (*p == '"')
                        {
                            p = ParseStr(p, out byte* tg, out int tgn, _sTag);
                            if (Is(tg, tgn, "test"u8)) test = true;
                        }
                        else
                        {
                            p = SkipVal(p);
                        }
                        p = SkipWs(p);
                        if (*p == ',')
                        {
                            p = SkipWs(p + 1);
                            continue;
                        }
                        break;
                    }
                }
                p++;
            }
            else if (kn == 4 && Is(k, kn, "meta"u8))
            {
                p = SkipWs(p + 1);
                if (*p != '}')
                {
                    while (true)
                    {
                        p = ParseStr(p, out byte* mk, out int mkn, _sKey);
                        bool isChan = Is(mk, mkn, "channel"u8);
                        p = SkipWs(SkipWs(p) + 1);
                        if (isChan && *p == '"') p = ParseStr(p, out chan, out chanN, _sChan);
                        else p = SkipVal(p);
                        p = SkipWs(p);
                        if (*p == ',')
                        {
                            p = SkipWs(p + 1);
                            continue;
                        }
                        break;
                    }
                }
                p++;
            }
            else if (kn == 6 && Is(k, kn, "amount"u8)) p = ParseStr(p, out amt, out amtN, _sAmt);
            else if (kn == 7 && Is(k, kn, "account"u8)) p = ParseStr(p, out acc, out accN, _sAcc);
            else if (kn == 8 && Is(k, kn, "currency"u8)) p = ParseStr(p, out cur, out curN, _sCur);
            else p = SkipVal(p);

            p = SkipWs(p);
            if (*p == ',')
            {
                p = SkipWs(p + 1);
                continue;
            }
            p++;
            break;
        }

        if (sign == 0 || test) return p;

        long hund = 0;
        int i = 0;
        while (i < amtN && amt[i] != '.') hund = hund * 10 + (amt[i++] - '0');
        hund *= 100;
        if (i < amtN)
        {
            i++;
            if (i < amtN) hund += (amt[i] - '0') * 10;
            if (i + 1 < amtN) hund += amt[i + 1] - '0';
        }
        int cid = _currencies.Find(cur, curN);
        long rate = cid < 0 ? 0 : _currencies.Sum[cid];
        long v = hund * rate / 1000000 * sign;

        _counted++;
        _net += v;
        int ch = _channels.Intern(chan, chanN);
        _channels.Count[ch]++;
        _channels.Sum[ch] += v;
        int ac = _accounts.Intern(acc, accN);
        _accounts.Sum[ac] += v;
        return p;
    }

    public void Run(string path)
    {
        const int slack = 64;
        int capacity = 8 << 20;
        byte[] buf = GC.AllocateUninitializedArray<byte>(capacity + slack, pinned: true);
        int n = 0;
        bool first = true;
        using var fs = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read, 1, FileOptions.SequentialScan);
        while (true)
        {
            if (n == capacity)
            {
                var nb = GC.AllocateUninitializedArray<byte>(capacity * 2 + slack, pinned: true);
                Buffer.BlockCopy(buf, 0, nb, 0, n);
                buf = nb;
                capacity *= 2;
            }
            int got = fs.Read(buf, n, capacity - n);
            bool eof = got == 0;
            n += got;
            int lim;
            if (eof)
            {
                if (n == 0) break;
                if (buf[n - 1] != '\n') buf[n++] = (byte)'\n';
                lim = n;
            }
            else
            {
                lim = buf.AsSpan(0, n).LastIndexOf((byte)'\n') + 1;
                if (lim == 0) continue;
            }
            byte saved = buf[lim];
            buf[lim] = 0; // sentinel stops whitespace skipping
            fixed (byte* b = buf)
            {
                byte* p = b;
                byte* stop = b + lim;
                while (true)
                {
                    p = SkipWs(p);
                    if (p >= stop) break;
                    if (first)
                    {
                        p = ParseRates(p);
                        first = false;
                    }
                    else
                    {
                        p = ParseTx(p);
                    }
                }
            }
            buf[lim] = saved;
            Buffer.BlockCopy(buf, lim, buf, 0, n - lim);
            n -= lim;
            if (eof) break;
        }
    }

    static int CompareBytes(byte[] a, byte[] b) => a.AsSpan().SequenceCompareTo(b);

    public void Print()
    {
        var sb = new StringBuilder();
        sb.Append("counted ").Append(_counted).Append('\n').Append("net ").Append(_net).Append('\n');
        var ch = Enumerable.Range(0, _channels.Size).ToArray();
        Array.Sort(ch, (x, y) => CompareBytes(_channels.Keys[x], _channels.Keys[y]));
        foreach (int c in ch)
        {
            sb.Append("channel ").Append(Encoding.Latin1.GetString(_channels.Keys[c]))
              .Append(' ').Append(_channels.Count[c]).Append(' ').Append(_channels.Sum[c]).Append('\n');
        }
        var ac = Enumerable.Range(0, _accounts.Size).ToArray();
        Array.Sort(ac, (x, y) =>
        {
            long sx = _accounts.Sum[x], sy = _accounts.Sum[y];
            if (sx != sy) return sx > sy ? -1 : 1;
            return CompareBytes(_accounts.Keys[x], _accounts.Keys[y]);
        });
        for (int k = 0; k < Math.Min(10, ac.Length); k++)
        {
            int a = ac[k];
            sb.Append("account ").Append(Encoding.Latin1.GetString(_accounts.Keys[a])).Append(' ').Append(_accounts.Sum[a]).Append('\n');
        }
        using var stdout = Console.OpenStandardOutput();
        stdout.Write(Encoding.Latin1.GetBytes(sb.ToString()));
    }
}
