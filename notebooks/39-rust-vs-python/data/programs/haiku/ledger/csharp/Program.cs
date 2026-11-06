using System.Runtime.InteropServices;
using System.Text;

// Streams a JSON Lines file through unmanaged buffers, parses only the fields it needs
// with pointers, and sums converted amounts per channel and per account with exact integer arithmetic.
public static class Program {
    public static void Main(string[] args) {
        if (args.Length < 1) {
            Console.Error.WriteLine("usage: solution INPUT_PATH");
            Environment.Exit(2);
        }
        var ledger = new Ledger();
        ledger.Run(args[0]);
        ledger.Print();
    }
}

// A decoded JSON string: N bytes at P.
public unsafe struct Field {
    public byte* P;
    public int N;
}

// Growable unmanaged byte buffer; holds decoded strings and output.
public sealed unsafe class ByteBuf {
    public byte* P;
    public int N;
    private int cap;

    public ByteBuf(int capacity) {
        cap = capacity;
        P = (byte*)NativeMemory.Alloc((nuint)cap);
    }

    public void Add(byte c) {
        if (N == cap) {
            cap *= 2;
            P = (byte*)NativeMemory.Realloc(P, (nuint)cap);
        }
        P[N++] = c;
    }
}

// Maps byte-string keys to dense indexes, with a sum and a count per key.
public sealed unsafe class KeyIndex {
    public byte[][] Keys = new byte[1024][];
    public long[] Sums = new long[1024];
    public long[] Counts = new long[1024];
    public int Size;
    private int[] slots = new int[2048];
    private int mask = 2047;

    public int Find(byte* a, int l) {
        int h = Hash(a, l) & mask;
        for (;;) {
            int s = slots[h];
            if (s == 0) break;
            byte[] k = Keys[s - 1];
            if (k.Length == l && new ReadOnlySpan<byte>(a, l).SequenceEqual(k)) return s - 1;
            h = (h + 1) & mask;
        }
        if (Size == Keys.Length) {
            Array.Resize(ref Keys, Size * 2);
            Array.Resize(ref Sums, Size * 2);
            Array.Resize(ref Counts, Size * 2);
        }
        Keys[Size] = new ReadOnlySpan<byte>(a, l).ToArray();
        slots[h] = Size + 1;
        Size++;
        if (Size * 2 > slots.Length) Grow();
        return Size - 1;
    }

    private static int Hash(byte* a, int l) {
        uint h = 2166136261;  // FNV-1a
        for (int i = 0; i < l; i++) h = (h ^ a[i]) * 16777619;
        return (int)((h ^ (h >> 15)) & 0x7FFFFFFF);
    }

    private void Grow() {
        slots = new int[slots.Length * 2];
        mask = slots.Length - 1;
        for (int i = 0; i < Size; i++) {
            byte[] k = Keys[i];
            int h;
            fixed (byte* kp = k) h = Hash(kp, k.Length) & mask;
            while (slots[h] != 0) h = (h + 1) & mask;
            slots[h] = i + 1;
        }
    }
}

public sealed unsafe class Ledger {
    private byte* buf;
    private int cap = 1 << 22;
    private bool haveRates;
    private bool testFlag;
    private readonly List<byte[]> rateNames = new();
    private readonly List<long> rateValues = new();
    private long counted;
    private long net;
    private readonly KeyIndex channels = new();
    private readonly KeyIndex accounts = new();

    private readonly ByteBuf keyScratch = new(64);
    private readonly ByteBuf typeScratch = new(64);
    private readonly ByteBuf accountScratch = new(64);
    private readonly ByteBuf currencyScratch = new(64);
    private readonly ByteBuf amountScratch = new(64);
    private readonly ByteBuf channelScratch = new(64);
    private readonly ByteBuf tagScratch = new(64);

    private Field key;
    private Field type;
    private Field account;
    private Field currency;
    private Field amount;
    private Field channel;
    private Field tag;

    public void Run(string path) {
        buf = (byte*)NativeMemory.Alloc((nuint)cap);
        using var fs = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read, 1);
        int carry = 0;
        for (;;) {
            if (carry == cap) {
                cap *= 2;
                buf = (byte*)NativeMemory.Realloc(buf, (nuint)cap);
            }
            int got = fs.Read(new Span<byte>(buf + carry, cap - carry));
            int end = carry + got;
            int stop = 0;
            if (got == 0) {
                stop = end;  // end of file: the last line may lack a newline
            } else {
                for (int i = end; i > 0; i--) {
                    if (buf[i - 1] == (byte)'\n') {
                        stop = i;
                        break;
                    }
                }
            }
            ProcessLines(stop);
            carry = end - stop;
            Buffer.MemoryCopy(buf + stop, buf, cap, carry);
            if (got == 0) break;
        }
    }

    private void ProcessLines(int n) {
        byte* end = buf + n;
        byte* p = buf;
        while (p < end) {
            byte* e = p;
            while (e < end && *e != (byte)'\n') e++;
            byte* q = p;
            while (q < e && (*q == ' ' || *q == '\t' || *q == '\r')) q++;
            if (q < e) {
                if (haveRates) {
                    ParseTxn(q);
                } else {
                    ParseRates(q);
                    haveRates = true;
                }
            }
            p = e + 1;
        }
    }

    // Skipping and reading helpers. Each returns the position after the item.

    private static byte* SkipWs(byte* p) {
        while (*p == ' ' || *p == '\t' || *p == '\r' || *p == '\n') p++;
        return p;
    }

    private static byte* SkipString(byte* p) {
        p++;
        while (*p != '"') p += (*p == '\\') ? 2 : 1;
        return p + 1;
    }

    private static byte* SkipValue(byte* p) {
        if (*p == '"') return SkipString(p);
        if (*p == '{' || *p == '[') {
            int depth = 0;
            for (;;) {
                byte c = *p;
                if (c == '"') {
                    p = SkipString(p);
                    continue;
                }
                if (c == '{' || c == '[') {
                    depth++;
                } else if (c == '}' || c == ']') {
                    if (--depth == 0) return p + 1;
                }
                p++;
            }
        }
        while (*p != ',' && *p != '}' && *p != ']' && *p != ' ' && *p != '\t' && *p != '\r' && *p != '\n') p++;
        return p;
    }

    // p points at an opening quote. Sets f to the decoded value and returns the position after the closing quote.
    private static byte* ReadString(byte* p, ByteBuf scratch, ref Field f) {
        byte* start = ++p;
        bool escaped = false;
        while (*p != '"') {
            if (*p == '\\') {
                escaped = true;
                p++;
            }
            p++;
        }
        if (escaped) {
            scratch.N = 0;
            Decode(start, p, scratch);
            f.P = scratch.P;
            f.N = scratch.N;
        } else {
            f.P = start;
            f.N = (int)(p - start);
        }
        return p + 1;
    }

    private static void Decode(byte* p, byte* e, ByteBuf s) {
        while (p < e) {
            if (*p != '\\') {
                s.Add(*p++);
                continue;
            }
            byte c = p[1];
            p += 2;
            switch (c) {
                case (byte)'b': s.Add(8); break;
                case (byte)'f': s.Add(12); break;
                case (byte)'n': s.Add(10); break;
                case (byte)'r': s.Add(13); break;
                case (byte)'t': s.Add(9); break;
                case (byte)'u': {
                    uint cp = Hex4(p);
                    p += 4;
                    if (cp >= 0xD800 && cp <= 0xDBFF && p[0] == '\\' && p[1] == 'u') {
                        uint lo = Hex4(p + 2);
                        if (lo >= 0xDC00 && lo <= 0xDFFF) {
                            cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
                            p += 6;
                        }
                    }
                    AppendUtf8(s, cp);
                    break;
                }
                default: s.Add(c); break;  // \" \\ \/
            }
        }
    }

    private static uint Hex4(byte* p) {
        uint v = 0;
        for (int i = 0; i < 4; i++) {
            int c = p[i];
            v = v * 16 + (uint)(c <= '9' ? c - '0' : (c | 0x20) - 'a' + 10);
        }
        return v;
    }

    private static void AppendUtf8(ByteBuf s, uint cp) {
        if (cp < 0x80) {
            s.Add((byte)cp);
        } else if (cp < 0x800) {
            s.Add((byte)(0xC0 | (cp >> 6)));
            s.Add((byte)(0x80 | (cp & 0x3F)));
        } else if (cp < 0x10000) {
            s.Add((byte)(0xE0 | (cp >> 12)));
            s.Add((byte)(0x80 | ((cp >> 6) & 0x3F)));
            s.Add((byte)(0x80 | (cp & 0x3F)));
        } else {
            s.Add((byte)(0xF0 | (cp >> 18)));
            s.Add((byte)(0x80 | ((cp >> 12) & 0x3F)));
            s.Add((byte)(0x80 | ((cp >> 6) & 0x3F)));
            s.Add((byte)(0x80 | (cp & 0x3F)));
        }
    }

    private static bool Eq(in Field f, ReadOnlySpan<byte> lit) {
        return new ReadOnlySpan<byte>(f.P, f.N).SequenceEqual(lit);
    }

    private void ParseRates(byte* p) {
        p = SkipWs(p + 1);  // '{'
        if (*p == '}') return;
        for (;;) {
            p = SkipWs(p);
            p = ReadString(p, keyScratch, ref key);
            p = SkipWs(SkipWs(p) + 1);  // ':'
            if (Eq(key, "rates"u8)) {
                p = ParseRatesObject(p);
            } else {
                p = SkipValue(p);
            }
            p = SkipWs(p);
            if (*p++ == '}') return;  // otherwise it was ','
        }
    }

    private byte* ParseRatesObject(byte* p) {
        p = SkipWs(p + 1);  // '{'
        if (*p == '}') return p + 1;
        for (;;) {
            p = SkipWs(p);
            p = ReadString(p, keyScratch, ref key);
            p = SkipWs(SkipWs(p) + 1);  // ':'
            bool neg = *p == '-';
            if (neg) p++;
            long v = 0;
            while (*p >= '0' && *p <= '9') v = v * 10 + (*p++ - '0');
            rateNames.Add(new ReadOnlySpan<byte>(key.P, key.N).ToArray());
            rateValues.Add(neg ? -v : v);
            p = SkipWs(p);
            if (*p++ == '}') return p;  // otherwise it was ','
        }
    }

    private void ParseTxn(byte* p) {
        type.N = 0;
        account.N = 0;
        currency.N = 0;
        amount.N = 0;
        channel.N = 0;
        testFlag = false;
        p = SkipWs(p + 1);  // '{'
        if (*p == '}') return;
        for (;;) {
            p = SkipWs(p);
            p = ReadString(p, keyScratch, ref key);
            p = SkipWs(SkipWs(p) + 1);  // ':'
            if (Eq(key, "account"u8)) {
                p = ReadString(p, accountScratch, ref account);
            } else if (Eq(key, "type"u8)) {
                p = ReadString(p, typeScratch, ref type);
            } else if (Eq(key, "currency"u8)) {
                p = ReadString(p, currencyScratch, ref currency);
            } else if (Eq(key, "amount"u8)) {
                if (*p == '"') {
                    p = ReadString(p, amountScratch, ref amount);
                } else {
                    byte* e = SkipValue(p);
                    amount.P = p;
                    amount.N = (int)(e - p);
                    p = e;
                }
            } else if (Eq(key, "tags"u8)) {
                p = ParseTags(p);
            } else if (Eq(key, "meta"u8)) {
                p = ParseMeta(p);
            } else {
                p = SkipValue(p);
            }
            p = SkipWs(p);
            if (*p++ == '}') break;  // otherwise it was ','
        }

        if (Eq(type, "void"u8) || testFlag) return;
        int r = -1;
        for (int i = 0; i < rateNames.Count; i++) {
            if (new ReadOnlySpan<byte>(currency.P, currency.N).SequenceEqual(rateNames[i])) {
                r = i;
                break;
            }
        }
        if (r < 0) return;

        long usd = Hundredths(amount) * rateValues[r] / 1000000L;
        long value = Eq(type, "debit"u8) ? -usd : usd;

        counted++;
        net += value;
        int c = channels.Find(channel.P, channel.N);
        channels.Counts[c]++;
        channels.Sums[c] += value;
        int a = accounts.Find(account.P, account.N);
        accounts.Sums[a] += value;
    }

    private byte* ParseTags(byte* p) {
        p = SkipWs(p + 1);  // '['
        if (*p == ']') return p + 1;
        for (;;) {
            p = SkipWs(p);
            if (*p == '"') {
                p = ReadString(p, tagScratch, ref tag);
                if (Eq(tag, "test"u8)) testFlag = true;
            } else {
                p = SkipValue(p);
            }
            p = SkipWs(p);
            if (*p++ == ']') return p;  // otherwise it was ','
        }
    }

    private byte* ParseMeta(byte* p) {
        p = SkipWs(p + 1);  // '{'
        if (*p == '}') return p + 1;
        for (;;) {
            p = SkipWs(p);
            p = ReadString(p, keyScratch, ref key);
            p = SkipWs(SkipWs(p) + 1);  // ':'
            if (Eq(key, "channel"u8) && *p == '"') {
                p = ReadString(p, channelScratch, ref channel);
            } else {
                p = SkipValue(p);
            }
            p = SkipWs(p);
            if (*p++ == '}') return p;  // otherwise it was ','
        }
    }

    // Parses an amount such as "12", "12.5" or "12.05" into hundredths.
    private static long Hundredths(in Field a) {
        long v = 0;
        int i = 0;
        for (; i < a.N && a.P[i] != '.'; i++) v = v * 10 + (a.P[i] - '0');
        v *= 100;
        if (i < a.N) {
            i++;
            long frac = 0;
            int digits = 0;
            for (; digits < 2 && i < a.N; i++, digits++) frac = frac * 10 + (a.P[i] - '0');
            if (digits == 1) frac *= 10;
            v += frac;
        }
        return v;
    }

    public void Print() {
        var sb = new StringBuilder();
        sb.Append("counted ").Append(counted).Append("\nnet ").Append(net).Append('\n');

        var chanOrder = new int[channels.Size];
        for (int i = 0; i < chanOrder.Length; i++) chanOrder[i] = i;
        Array.Sort(chanOrder, (x, y) => channels.Keys[x].AsSpan().SequenceCompareTo(channels.Keys[y]));
        foreach (int i in chanOrder) {
            sb.Append("channel ").Append(Encoding.Latin1.GetString(channels.Keys[i]))
              .Append(' ').Append(channels.Counts[i]).Append(' ').Append(channels.Sums[i]).Append('\n');
        }

        var accOrder = new int[accounts.Size];
        for (int i = 0; i < accOrder.Length; i++) accOrder[i] = i;
        Array.Sort(accOrder, (x, y) => {
            if (accounts.Sums[x] != accounts.Sums[y]) return accounts.Sums[y].CompareTo(accounts.Sums[x]);
            return accounts.Keys[x].AsSpan().SequenceCompareTo(accounts.Keys[y]);
        });
        for (int k = 0; k < Math.Min(10, accOrder.Length); k++) {
            int i = accOrder[k];
            sb.Append("account ").Append(Encoding.Latin1.GetString(accounts.Keys[i]))
              .Append(' ').Append(accounts.Sums[i]).Append('\n');
        }

        using var stdout = Console.OpenStandardOutput();
        stdout.Write(Encoding.Latin1.GetBytes(sb.ToString()));
        stdout.Flush();
    }
}
