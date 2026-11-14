using System;
using System.Buffers;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.Json;

internal static class Program
{
    private static readonly JsonReaderOptions ReaderOptions = new()
    {
        MaxDepth = int.MaxValue
    };

    private readonly struct Rate
    {
        public readonly byte[] Name;
        public readonly long Value;

        public Rate(byte[] name, long value)
        {
            Name = name;
            Value = value;
        }
    }

    private struct Entry
    {
        public string Name;
        public uint Hash;
        public long Count;
        public long Net;
    }

    private sealed class NameTable
    {
        private int[] buckets;
        public Entry[] Items;
        public int Used;

        public NameTable(int capacity)
        {
            buckets = new int[capacity];
            Items = new Entry[capacity * 3 / 4];
        }

        public void Add(ReadOnlySpan<byte> name, bool escaped, long value)
        {
            if (!escaped)
            {
                AddDecoded(name, value);
                return;
            }

            if (name.Length <= 256)
            {
                Span<byte> decoded = stackalloc byte[name.Length];
                int length = UnescapeAscii(name, decoded);
                AddDecoded(decoded[..length], value);
            }
            else
            {
                byte[] buffer = ArrayPool<byte>.Shared.Rent(name.Length);
                try
                {
                    int length = UnescapeAscii(name, buffer);
                    AddDecoded(buffer.AsSpan(0, length), value);
                }
                finally
                {
                    ArrayPool<byte>.Shared.Return(buffer);
                }
            }
        }

        private void AddDecoded(ReadOnlySpan<byte> name, long value)
        {
            uint hash = 2166136261;
            unchecked
            {
                foreach (byte b in name)
                    hash = (hash ^ b) * 16777619;
            }

            if (Used == Items.Length)
                Grow();

            int mask = buckets.Length - 1;
            int slot = (int)(hash & (uint)mask);

            while (true)
            {
                int index = buckets[slot] - 1;
                if (index < 0)
                {
                    index = Used++;
                    Items[index] = new Entry
                    {
                        Name = Encoding.ASCII.GetString(name),
                        Hash = hash,
                        Count = 1,
                        Net = value
                    };
                    buckets[slot] = index + 1;
                    return;
                }

                ref Entry entry = ref Items[index];
                if (entry.Hash == hash && EqualsAscii(entry.Name, name))
                {
                    entry.Count++;
                    entry.Net = unchecked(entry.Net + value);
                    return;
                }

                slot = (slot + 1) & mask;
            }
        }

        private void Grow()
        {
            int[] replacement = new int[buckets.Length * 2];
            int mask = replacement.Length - 1;

            for (int i = 0; i < Used; i++)
            {
                int slot = (int)(Items[i].Hash & (uint)mask);
                while (replacement[slot] != 0)
                    slot = (slot + 1) & mask;
                replacement[slot] = i + 1;
            }

            buckets = replacement;
            Array.Resize(ref Items, Items.Length * 2);
        }

        private static bool EqualsAscii(string text, ReadOnlySpan<byte> bytes)
        {
            if (text.Length != bytes.Length)
                return false;

            for (int i = 0; i < bytes.Length; i++)
            {
                if (text[i] != bytes[i])
                    return false;
            }
            return true;
        }
    }

    private static int Hex(byte value) =>
        value <= (byte)'9' ? value - '0' : (value | 32) - 'a' + 10;

    private static int UnescapeAscii(ReadOnlySpan<byte> source, Span<byte> destination)
    {
        int written = 0;
        for (int i = 0; i < source.Length; i++)
        {
            byte value = source[i];
            if (value == (byte)'\\')
            {
                value = source[++i];
                switch (value)
                {
                    case (byte)'u':
                        value = (byte)(
                            (Hex(source[i + 1]) << 12) |
                            (Hex(source[i + 2]) << 8) |
                            (Hex(source[i + 3]) << 4) |
                            Hex(source[i + 4]));
                        i += 4;
                        break;
                    case (byte)'b': value = 8; break;
                    case (byte)'f': value = 12; break;
                    case (byte)'n': value = 10; break;
                    case (byte)'r': value = 13; break;
                    case (byte)'t': value = 9; break;
                }
            }

            destination[written++] = value;
        }
        return written;
    }

    private static long ParseHundredths(ReadOnlySpan<byte> amount, bool escaped)
    {
        unchecked
        {
            long value = 0;
            int fractionalDigits = -1;

            for (int i = 0; i < amount.Length; i++)
            {
                byte digit = amount[i];
                if (escaped && digit == (byte)'\\')
                {
                    digit = (byte)(
                        (Hex(amount[i + 2]) << 12) |
                        (Hex(amount[i + 3]) << 8) |
                        (Hex(amount[i + 4]) << 4) |
                        Hex(amount[i + 5]));
                    i += 5;
                }

                if (digit == (byte)'.')
                {
                    fractionalDigits = 0;
                }
                else
                {
                    value = value * 10 + digit - '0';
                    if (fractionalDigits >= 0)
                        fractionalDigits++;
                }
            }

            if (fractionalDigits < 0)
                value *= 100;
            else if (fractionalDigits == 1)
                value *= 10;

            return value;
        }
    }

    private static long ReadRate(ref Utf8JsonReader reader)
    {
        if (reader.TryGetInt64(out long value))
            return value;

        // Modular parsing also handles unusually large integer rates:
        // the task guarantees that the eventual product fits in Int64.
        ReadOnlySpan<byte> text = reader.ValueSpan;
        bool negative = text[0] == (byte)'-';
        value = 0;
        unchecked
        {
            for (int i = negative ? 1 : 0; i < text.Length; i++)
                value = value * 10 + text[i] - '0';
            return negative ? -value : value;
        }
    }

    private static Rate[] ReadRates(ReadOnlySpan<byte> line)
    {
        if (line.StartsWith("\uFEFF"u8))
            line = line[3..];

        var rates = new List<Rate>();
        var reader = new Utf8JsonReader(line, ReaderOptions);
        reader.Read();

        while (reader.Read() && reader.TokenType != JsonTokenType.EndObject)
        {
            bool isRates = reader.ValueTextEquals("rates"u8);
            reader.Read();

            if (!isRates)
            {
                reader.Skip();
                continue;
            }

            while (reader.Read() && reader.TokenType != JsonTokenType.EndObject)
            {
                byte[] name = Encoding.UTF8.GetBytes(reader.GetString());
                reader.Read();
                rates.Add(new Rate(name, ReadRate(ref reader)));
            }
        }

        return rates.ToArray();
    }

    private static int Field(ref Utf8JsonReader reader)
    {
        if (!reader.ValueIsEscaped)
        {
            ReadOnlySpan<byte> key = reader.ValueSpan;
            switch (key.Length)
            {
                case 4:
                    if (key.SequenceEqual("type"u8)) return 2;
                    if (key.SequenceEqual("tags"u8)) return 5;
                    if (key.SequenceEqual("meta"u8)) return 6;
                    break;
                case 6:
                    if (key.SequenceEqual("amount"u8)) return 3;
                    break;
                case 7:
                    if (key.SequenceEqual("account"u8)) return 1;
                    break;
                case 8:
                    if (key.SequenceEqual("currency"u8)) return 4;
                    break;
            }
            return 0;
        }

        if (reader.ValueTextEquals("account"u8)) return 1;
        if (reader.ValueTextEquals("type"u8)) return 2;
        if (reader.ValueTextEquals("amount"u8)) return 3;
        if (reader.ValueTextEquals("currency"u8)) return 4;
        if (reader.ValueTextEquals("tags"u8)) return 5;
        if (reader.ValueTextEquals("meta"u8)) return 6;
        return 0;
    }

    private static void ProcessTransaction(
        ReadOnlySpan<byte> line,
        Rate[] rates,
        NameTable accounts,
        NameTable channels,
        ref long counted,
        ref long net)
    {
        var reader = new Utf8JsonReader(line, ReaderOptions);
        ReadOnlySpan<byte> account = default;
        ReadOnlySpan<byte> channel = default;
        ReadOnlySpan<byte> amount = default;
        bool accountEscaped = false;
        bool channelEscaped = false;
        bool amountEscaped = false;
        bool debit = false;
        long rate = 0;

        reader.Read();
        while (reader.Read() && reader.TokenType != JsonTokenType.EndObject)
        {
            int field = Field(ref reader);
            reader.Read();

            switch (field)
            {
                case 1:
                    account = reader.ValueSpan;
                    accountEscaped = reader.ValueIsEscaped;
                    break;

                case 2:
                    if (reader.ValueTextEquals("void"u8))
                        return;
                    debit = reader.ValueTextEquals("debit"u8);
                    break;

                case 3:
                    amount = reader.ValueSpan;
                    amountEscaped = reader.ValueIsEscaped;
                    break;

                case 4:
                    for (int i = 0; i < rates.Length; i++)
                    {
                        if (reader.ValueTextEquals(rates[i].Name))
                        {
                            rate = rates[i].Value;
                            break;
                        }
                    }
                    break;

                case 5:
                    while (reader.Read() && reader.TokenType != JsonTokenType.EndArray)
                    {
                        if (reader.ValueTextEquals("test"u8))
                            return;
                    }
                    break;

                case 6:
                    while (reader.Read() && reader.TokenType != JsonTokenType.EndObject)
                    {
                        bool isChannel = reader.ValueTextEquals("channel"u8);
                        reader.Read();
                        if (isChannel)
                        {
                            channel = reader.ValueSpan;
                            channelEscaped = reader.ValueIsEscaped;
                        }
                        else
                        {
                            reader.Skip();
                        }
                    }
                    break;

                default:
                    reader.Skip();
                    break;
            }
        }

        long product = rate == 0
            ? 0
            : unchecked(ParseHundredths(amount, amountEscaped) * rate);

        long value = product / 1_000_000;
        if (product < 0 && product % 1_000_000 != 0)
            value--;

        if (debit)
            value = unchecked(-value);

        counted++;
        net = unchecked(net + value);
        accounts.Add(account, accountEscaped, value);
        channels.Add(channel, channelEscaped, value);
    }

    private static bool AccountBefore(Entry a, Entry b) =>
        a.Net > b.Net ||
        (a.Net == b.Net && StringComparer.Ordinal.Compare(a.Name, b.Name) <= 0);

    private static void WriteOutput(
        long counted, long net, NameTable channels, NameTable accounts)
    {
        Array.Sort(
            channels.Items, 0, channels.Used,
            Comparer<Entry>.Create(
                static (a, b) => StringComparer.Ordinal.Compare(a.Name, b.Name)));

        Entry[] best = new Entry[Math.Min(10, accounts.Used)];
        int bestCount = 0;

        for (int i = 0; i < accounts.Used; i++)
        {
            Entry candidate = accounts.Items[i];
            int position = 0;
            while (position < bestCount && AccountBefore(best[position], candidate))
                position++;

            if (position >= best.Length)
                continue;

            int newCount = Math.Min(best.Length, bestCount + 1);
            for (int j = newCount - 1; j > position; j--)
                best[j] = best[j - 1];

            best[position] = candidate;
            bestCount = newCount;
        }

        using var writer = new StreamWriter(
            Console.OpenStandardOutput(), new UTF8Encoding(false), 65536);
        writer.NewLine = "\n";

        writer.Write("counted ");
        writer.WriteLine(counted);
        writer.Write("net ");
        writer.WriteLine(net);

        for (int i = 0; i < channels.Used; i++)
        {
            Entry entry = channels.Items[i];
            writer.Write("channel ");
            writer.Write(entry.Name);
            writer.Write(' ');
            writer.Write(entry.Count);
            writer.Write(' ');
            writer.WriteLine(entry.Net);
        }

        for (int i = 0; i < bestCount; i++)
        {
            writer.Write("account ");
            writer.Write(best[i].Name);
            writer.Write(' ');
            writer.WriteLine(best[i].Net);
        }
    }

    public static void Main(string[] args)
    {
        var accounts = new NameTable(1024);
        var channels = new NameTable(16);
        Rate[] rates = null;
        long counted = 0;
        long net = 0;

        using var input = new FileStream(args[0], new FileStreamOptions
        {
            Mode = FileMode.Open,
            Access = FileAccess.Read,
            Share = FileShare.Read,
            Options = FileOptions.SequentialScan,
            BufferSize = 1
        });

        byte[] buffer = ArrayPool<byte>.Shared.Rent(1 << 20);
        try
        {
            int retained = 0;

            while (true)
            {
                if (retained == buffer.Length)
                {
                    byte[] larger = ArrayPool<byte>.Shared.Rent(
                        checked(buffer.Length * 2));
                    buffer.AsSpan(0, retained).CopyTo(larger);
                    ArrayPool<byte>.Shared.Return(buffer);
                    buffer = larger;
                }

                int read = input.Read(buffer, retained, buffer.Length - retained);
                if (read == 0)
                    break;

                int available = retained + read;
                int start = 0;

                while (start < available)
                {
                    int relativeEnd = buffer.AsSpan(start, available - start)
                        .IndexOf((byte)'\n');
                    if (relativeEnd < 0)
                        break;

                    ReadOnlySpan<byte> line = buffer.AsSpan(start, relativeEnd);
                    if (rates is null)
                    {
                        rates = ReadRates(line);
                    }
                    else
                    {
                        ProcessTransaction(
                            line, rates, accounts, channels, ref counted, ref net);
                    }

                    start += relativeEnd + 1;
                }

                retained = available - start;
                if (retained > 0 && start > 0)
                    buffer.AsSpan(start, retained).CopyTo(buffer);
            }
        }
        finally
        {
            ArrayPool<byte>.Shared.Return(buffer);
        }

        WriteOutput(counted, net, channels, accounts);
    }
}
