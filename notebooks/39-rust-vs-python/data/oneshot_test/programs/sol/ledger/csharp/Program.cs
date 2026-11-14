using System;
using System.Buffers;
using System.IO;
using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json;

internal static class Program
{
    private const int End = -1;
    private const int Unknown = 0;
    private const int Account = 1;
    private const int Type = 2;
    private const int Amount = 3;
    private const int Currency = 4;
    private const int Tags = 5;
    private const int Meta = 6;
    private const int Channel = 7;
    private const int Rates = 8;

    private static readonly SearchValues<byte> Structural =
        SearchValues.Create("\"{}[]"u8);

    public static void Main(string[] args)
    {
        var ledger = new Ledger();
        byte[] buffer = new byte[1 << 20];
        int held = 0;
        bool first = true;

        using (var input = new FileStream(
            args[0], FileMode.Open, FileAccess.Read, FileShare.Read,
            bufferSize: 1, options: FileOptions.SequentialScan))
        {
            while (true)
            {
                if (held == buffer.Length)
                    Array.Resize(ref buffer, checked(buffer.Length * 2));

                int read = input.Read(buffer, held, buffer.Length - held);
                if (read == 0)
                    break;

                int length = held + read;
                int start = 0;

                while (start < length)
                {
                    int relative = buffer.AsSpan(start, length - start)
                        .IndexOf((byte)'\n');

                    if (relative < 0)
                        break;

                    int end = start + relative;
                    ReadOnlySpan<byte> line = buffer.AsSpan(start, end - start);

                    if (first)
                    {
                        ledger.ReadRates(line);
                        first = false;
                    }
                    else
                    {
                        ledger.ProcessTransaction(line);
                    }

                    start = end + 1;
                }

                held = length - start;
                if (held != 0)
                    Buffer.BlockCopy(buffer, start, buffer, 0, held);
            }
        }

        if (held != 0)
        {
            if (first)
                ledger.ReadRates(buffer.AsSpan(0, held));
            else
                ledger.ProcessTransaction(buffer.AsSpan(0, held));
        }

        ledger.WriteOutput();
    }

    private readonly struct Token
    {
        public readonly int Start;
        public readonly int Length;
        public readonly bool Escaped;

        public Token(int start, int length, bool escaped)
        {
            Start = start;
            Length = length;
            Escaped = escaped;
        }
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    private static ReadOnlySpan<byte> Raw(ReadOnlySpan<byte> data, Token token) =>
        data.Slice(token.Start + 1, token.Length - 2);

    private static ReadOnlySpan<byte> Decode(
        ReadOnlySpan<byte> data, Token token, ref byte[] scratch)
    {
        ReadOnlySpan<byte> raw = Raw(data, token);
        if (!token.Escaped)
            return raw;

        if (scratch.Length < raw.Length)
            scratch = new byte[raw.Length];

        var reader = new Utf8JsonReader(data.Slice(token.Start, token.Length));
        reader.Read();
        int length = reader.CopyString(scratch.AsSpan());
        return scratch.AsSpan(0, length);
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    private static int Hex(byte c)
    {
        if (c <= (byte)'9')
            return c - '0';
        return (c | 32) - 'a' + 10;
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    private static int Hex4(ReadOnlySpan<byte> value, int position) =>
        (Hex(value[position]) << 12) |
        (Hex(value[position + 1]) << 8) |
        (Hex(value[position + 2]) << 4) |
        Hex(value[position + 3]);

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    private static int Classify(ReadOnlySpan<byte> data, Token token)
    {
        ReadOnlySpan<byte> name = Raw(data, token);
        return token.Escaped ? ClassifyEscaped(name) : ClassifyPlain(name);
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    private static int ClassifyPlain(ReadOnlySpan<byte> name)
    {
        switch (name.Length)
        {
            case 4:
                if (name.SequenceEqual("type"u8)) return Type;
                if (name.SequenceEqual("tags"u8)) return Tags;
                if (name.SequenceEqual("meta"u8)) return Meta;
                break;
            case 5:
                if (name.SequenceEqual("rates"u8)) return Rates;
                break;
            case 6:
                if (name.SequenceEqual("amount"u8)) return Amount;
                break;
            case 7:
                if (name.SequenceEqual("account"u8)) return Account;
                if (name.SequenceEqual("channel"u8)) return Channel;
                break;
            case 8:
                if (name.SequenceEqual("currency"u8)) return Currency;
                break;
        }

        return Unknown;
    }

    private static int ClassifyEscaped(ReadOnlySpan<byte> raw)
    {
        if (raw.Length > 48)
            return Unknown;

        Span<byte> decoded = stackalloc byte[8];
        int written = 0;

        for (int i = 0; i < raw.Length;)
        {
            int c = raw[i++];
            if (c == '\\')
            {
                if (raw[i++] != (byte)'u')
                    return Unknown;

                c = Hex4(raw, i);
                i += 4;
            }

            if (c > 127 || written == decoded.Length)
                return Unknown;

            decoded[written++] = (byte)c;
        }

        return ClassifyPlain(decoded.Slice(0, written));
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    private static bool Matches(
        ReadOnlySpan<byte> data, Token token, ReadOnlySpan<byte> expected)
    {
        ReadOnlySpan<byte> raw = Raw(data, token);
        if (!token.Escaped)
            return raw.SequenceEqual(expected);

        return MatchesEscaped(raw, expected);
    }

    private static bool MatchesEscaped(
        ReadOnlySpan<byte> raw, ReadOnlySpan<byte> expected)
    {
        int position = 0;

        for (int i = 0; i < expected.Length; i++)
        {
            if (position == raw.Length)
                return false;

            int c = raw[position++];
            if (c == '\\')
            {
                if (raw[position++] != (byte)'u')
                    return false;

                c = Hex4(raw, position);
                position += 4;
            }

            if (c != expected[i])
                return false;
        }

        return position == raw.Length;
    }

    private ref struct Parser
    {
        private readonly ReadOnlySpan<byte> _data;
        private int _position;

        public Parser(ReadOnlySpan<byte> data)
        {
            _data = data;
            _position = 0;
        }

        public ReadOnlySpan<byte> Data => _data;

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        private void SkipWhitespace()
        {
            while (_data[_position] <= 32)
                _position++;
        }

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public void BeginObject()
        {
            SkipWhitespace();
            _position++;
        }

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public void BeginArray()
        {
            SkipWhitespace();
            _position++;
        }

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public bool NextName(out Token name)
        {
            SkipWhitespace();

            if (_data[_position] == (byte)',')
            {
                _position++;
                SkipWhitespace();
            }

            if (_data[_position] == (byte)'}')
            {
                _position++;
                name = default;
                return false;
            }

            name = ReadString();
            SkipWhitespace();
            _position++;
            SkipWhitespace();
            return true;
        }

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public int NextField()
        {
            return NextName(out Token name) ? Classify(_data, name) : End;
        }

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public bool NextArrayElement()
        {
            SkipWhitespace();

            if (_data[_position] == (byte)',')
            {
                _position++;
                SkipWhitespace();
            }

            if (_data[_position] == (byte)']')
            {
                _position++;
                return false;
            }

            return true;
        }

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public Token ReadString()
        {
            int start = _position;
            int position = start + 1;
            bool escaped = false;

            while (true)
            {
                position += _data.Slice(position)
                    .IndexOfAny((byte)'"', (byte)'\\');

                if (_data[position] == (byte)'"')
                    break;

                escaped = true;
                position += 2;
            }

            _position = position + 1;
            return new Token(start, _position - start, escaped);
        }

        public long ReadRate()
        {
            bool negative = _data[_position] == (byte)'-';
            if (negative)
                _position++;

            ulong limit = negative ? 0x8000000000000000UL : long.MaxValue;
            ulong cutoff = limit / 10;
            uint lastDigit = (uint)(limit % 10);
            ulong value = 0;
            bool overflow = false;

            while (_position < _data.Length)
            {
                uint digit = (uint)(_data[_position] - '0');
                if (digit > 9)
                    break;

                if (!overflow)
                {
                    if (value > cutoff || (value == cutoff && digit > lastDigit))
                        overflow = true;
                    else
                        value = value * 10 + digit;
                }

                _position++;
            }

            // Such a rate can only have zero-valued amounts under the
            // guaranteed signed-64-bit product bound.
            if (overflow)
                return 0;

            return negative ? unchecked(-(long)value) : (long)value;
        }

        public void SkipValue()
        {
            byte first = _data[_position];

            if (first == (byte)'"')
            {
                ReadString();
                return;
            }

            if (first == (byte)'{' || first == (byte)'[')
            {
                int depth = 1;
                int position = _position + 1;

                while (depth != 0)
                {
                    position += _data.Slice(position).IndexOfAny(Structural);
                    byte c = _data[position++];

                    if (c == (byte)'"')
                    {
                        while (true)
                        {
                            position += _data.Slice(position)
                                .IndexOfAny((byte)'"', (byte)'\\');

                            if (_data[position] == (byte)'"')
                            {
                                position++;
                                break;
                            }

                            position += 2;
                        }
                    }
                    else if (c == (byte)'{' || c == (byte)'[')
                    {
                        depth++;
                    }
                    else
                    {
                        depth--;
                    }
                }

                _position = position;
                return;
            }

            while (_position < _data.Length)
            {
                byte c = _data[_position];
                if (c <= 32 || c == (byte)',' || c == (byte)'}' || c == (byte)']')
                    break;
                _position++;
            }
        }
    }

    private struct Entry
    {
        public byte[] Key;
        public long Net;
        public long Count;
        public uint Hash;
    }

    private sealed class ByteTable
    {
        private Entry[] _entries;
        private int[] _buckets;
        private int _count;
        private int _resizeAt;

        public ByteTable(int initialCapacity)
        {
            _entries = new Entry[initialCapacity];
            _buckets = new int[initialCapacity * 2];
            _resizeAt = _buckets.Length - (_buckets.Length >> 2);
        }

        public Entry[] Entries => _entries;
        public int Count => _count;

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        private static uint HashKey(ReadOnlySpan<byte> key)
        {
            uint hash = 2166136261;
            foreach (byte b in key)
                hash = unchecked((hash ^ b) * 16777619);
            return hash;
        }

        public long FindNet(ReadOnlySpan<byte> key)
        {
            uint hash = HashKey(key);
            int mask = _buckets.Length - 1;
            int slot = (int)(hash & (uint)mask);

            while (true)
            {
                int index = _buckets[slot] - 1;
                if (index < 0)
                    throw new InvalidDataException("Unknown currency.");

                ref Entry entry = ref _entries[index];
                if (entry.Hash == hash && key.SequenceEqual(entry.Key))
                    return entry.Net;

                slot = (slot + 1) & mask;
            }
        }

        public ref Entry GetOrAdd(ReadOnlySpan<byte> key)
        {
            uint hash = HashKey(key);
            int mask = _buckets.Length - 1;
            int slot = (int)(hash & (uint)mask);

            while (true)
            {
                int index = _buckets[slot] - 1;
                if (index < 0)
                    break;

                ref Entry entry = ref _entries[index];
                if (entry.Hash == hash && key.SequenceEqual(entry.Key))
                    return ref entry;

                slot = (slot + 1) & mask;
            }

            if (_count >= _resizeAt)
            {
                GrowBuckets();
                mask = _buckets.Length - 1;
                slot = (int)(hash & (uint)mask);

                while (_buckets[slot] != 0)
                    slot = (slot + 1) & mask;
            }

            if (_count == _entries.Length)
                Array.Resize(ref _entries, checked(_entries.Length * 2));

            int added = _count++;
            _entries[added].Key = key.ToArray();
            _entries[added].Hash = hash;
            _buckets[slot] = added + 1;
            return ref _entries[added];
        }

        private void GrowBuckets()
        {
            int[] buckets = new int[checked(_buckets.Length * 2)];
            int mask = buckets.Length - 1;

            for (int i = 0; i < _count; i++)
            {
                int slot = (int)(_entries[i].Hash & (uint)mask);
                while (buckets[slot] != 0)
                    slot = (slot + 1) & mask;
                buckets[slot] = i + 1;
            }

            _buckets = buckets;
            _resizeAt = buckets.Length - (buckets.Length >> 2);
        }
    }

    private sealed class Ledger
    {
        private readonly ByteTable _rates = new ByteTable(16);
        private readonly ByteTable _accounts = new ByteTable(1024);
        private readonly ByteTable _channels = new ByteTable(16);
        private byte[] _scratch = new byte[256];
        private long _count;
        private long _net;

        public void ReadRates(ReadOnlySpan<byte> line)
        {
            if (line.Length >= 3 &&
                line[0] == 0xEF && line[1] == 0xBB && line[2] == 0xBF)
            {
                line = line.Slice(3);
            }

            var parser = new Parser(line);
            parser.BeginObject();

            int field;
            while ((field = parser.NextField()) != End)
            {
                if (field != Rates)
                {
                    parser.SkipValue();
                    continue;
                }

                parser.BeginObject();
                while (parser.NextName(out Token currency))
                {
                    long rate = parser.ReadRate();
                    ref Entry entry = ref _rates.GetOrAdd(
                        Decode(line, currency, ref _scratch));
                    entry.Net = rate;
                }
            }
        }

        public void ProcessTransaction(ReadOnlySpan<byte> line)
        {
            var parser = new Parser(line);
            parser.BeginObject();

            Token account = default;
            Token amount = default;
            Token currency = default;
            Token channel = default;
            bool debit = false;

            int field;
            while ((field = parser.NextField()) != End)
            {
                switch (field)
                {
                    case Account:
                        account = parser.ReadString();
                        break;

                    case Amount:
                        amount = parser.ReadString();
                        break;

                    case Currency:
                        currency = parser.ReadString();
                        break;

                    case Type:
                    {
                        Token type = parser.ReadString();
                        if (Matches(line, type, "void"u8))
                            return;
                        debit = Matches(line, type, "debit"u8);
                        break;
                    }

                    case Tags:
                        if (HasTestTag(ref parser))
                            return;
                        break;

                    case Meta:
                        channel = ReadChannel(ref parser);
                        break;

                    default:
                        parser.SkipValue();
                        break;
                }
            }

            long rate = _rates.FindNet(Decode(line, currency, ref _scratch));
            long usd = 0;

            if (rate != 0)
            {
                long hundredths = ParseAmount(Decode(line, amount, ref _scratch));
                long product = unchecked(hundredths * rate);
                usd = product / 1_000_000;

                if (product < 0 && product % 1_000_000 != 0)
                    usd--;
            }

            if (debit)
                usd = unchecked(-usd);

            _count++;
            _net = unchecked(_net + usd);

            ref Entry accountEntry = ref _accounts.GetOrAdd(
                Decode(line, account, ref _scratch));
            accountEntry.Net = unchecked(accountEntry.Net + usd);

            ref Entry channelEntry = ref _channels.GetOrAdd(
                Decode(line, channel, ref _scratch));
            channelEntry.Count++;
            channelEntry.Net = unchecked(channelEntry.Net + usd);
        }

        private static bool HasTestTag(ref Parser parser)
        {
            parser.BeginArray();
            while (parser.NextArrayElement())
            {
                Token tag = parser.ReadString();
                if (Matches(parser.Data, tag, "test"u8))
                    return true;
            }

            return false;
        }

        private static Token ReadChannel(ref Parser parser)
        {
            Token channel = default;
            parser.BeginObject();

            int field;
            while ((field = parser.NextField()) != End)
            {
                if (field == Channel)
                    channel = parser.ReadString();
                else
                    parser.SkipValue();
            }

            return channel;
        }

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        private static long ParseAmount(ReadOnlySpan<byte> amount)
        {
            long whole = 0;
            int position = 0;

            while (position < amount.Length && amount[position] != (byte)'.')
            {
                whole = unchecked(whole * 10 + amount[position] - '0');
                position++;
            }

            long result = unchecked(whole * 100);
            if (position == amount.Length)
                return result;

            position++;
            int fraction = (amount[position++] - '0') * 10;
            if (position < amount.Length)
                fraction += amount[position] - '0';

            return unchecked(result + fraction);
        }

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        private static bool Better(in Entry a, in Entry b)
        {
            if (a.Net != b.Net)
                return a.Net > b.Net;

            return a.Key.AsSpan().SequenceCompareTo(b.Key) < 0;
        }

        public void WriteOutput()
        {
            using var writer = new StreamWriter(
                Console.OpenStandardOutput(), new UTF8Encoding(false), 65536);
            writer.NewLine = "\n";

            writer.Write("counted ");
            writer.Write(_count);
            writer.Write('\n');
            writer.Write("net ");
            writer.Write(_net);
            writer.Write('\n');

            Entry[] channels = _channels.Entries;
            int[] order = new int[_channels.Count];

            for (int i = 0; i < order.Length; i++)
                order[i] = i;

            Array.Sort(order, (a, b) =>
                channels[a].Key.AsSpan().SequenceCompareTo(channels[b].Key));

            foreach (int index in order)
            {
                ref Entry entry = ref channels[index];
                writer.Write("channel ");
                writer.Write(Encoding.UTF8.GetString(entry.Key));
                writer.Write(' ');
                writer.Write(entry.Count);
                writer.Write(' ');
                writer.Write(entry.Net);
                writer.Write('\n');
            }

            Entry[] accounts = _accounts.Entries;
            int[] top = new int[10];
            int topCount = 0;

            for (int i = 0; i < _accounts.Count; i++)
            {
                int position = topCount;

                while (position > 0 &&
                       Better(in accounts[i], in accounts[top[position - 1]]))
                {
                    position--;
                }

                if (position >= 10)
                    continue;

                int newCount = Math.Min(topCount + 1, 10);
                for (int j = newCount - 1; j > position; j--)
                    top[j] = top[j - 1];

                top[position] = i;
                topCount = newCount;
            }

            for (int i = 0; i < topCount; i++)
            {
                ref Entry entry = ref accounts[top[i]];
                writer.Write("account ");
                writer.Write(Encoding.UTF8.GetString(entry.Key));
                writer.Write(' ');
                writer.Write(entry.Net);
                writer.Write('\n');
            }
        }
    }
}
