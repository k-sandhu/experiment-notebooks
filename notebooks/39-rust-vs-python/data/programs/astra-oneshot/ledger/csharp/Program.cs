using System;
using System.Buffers;
using System.Globalization;
using System.IO;
using System.Text;
using System.Text.Json;

static class Program
{
    private static readonly ByteTable Rates = new(16);
    private static readonly ByteTable Channels = new(16);
    private static readonly ByteTable Accounts = new(1024);

    private static readonly JsonReaderState InitialState = new(
        new JsonReaderOptions { MaxDepth = int.MaxValue });

    private static long counted;
    private static long net;

    public static void Main(string[] args)
    {
        CultureInfo.CurrentCulture = CultureInfo.InvariantCulture;

        using (var input = new FileStream(
            args[0], FileMode.Open, FileAccess.Read, FileShare.Read,
            1, FileOptions.SequentialScan))
        {
            byte[] buffer = new byte[1 << 20];
            int retained = 0;
            bool firstLine = true;

            while (true)
            {
                if (retained == buffer.Length)
                    Array.Resize(ref buffer, checked(buffer.Length * 2));

                int read = input.Read(buffer.AsSpan(retained));
                if (read == 0)
                    break;

                int end = retained + read;
                int start = 0;
                int search = retained;

                while (true)
                {
                    int offset = buffer.AsSpan(search, end - search)
                        .IndexOf((byte)'\n');

                    if (offset < 0)
                        break;

                    int newline = search + offset;
                    ReadOnlySpan<byte> line = buffer.AsSpan(start, newline - start);

                    if (firstLine)
                    {
                        ReadRates(line);
                        firstLine = false;
                    }
                    else
                    {
                        ReadTransaction(line);
                    }

                    start = newline + 1;
                    search = start;
                }

                retained = end - start;
                if (retained != 0 && start != 0)
                    buffer.AsSpan(start, retained).CopyTo(buffer);
            }
        }

        WriteOutput();
    }

    private static void ReadRates(ReadOnlySpan<byte> line)
    {
        if (line.Length >= 3 &&
            line[0] == 0xEF && line[1] == 0xBB && line[2] == 0xBF)
            line = line[3..];

        var reader = new Utf8JsonReader(line, true, InitialState);
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
                int index = Rates.GetToken(ref reader);
                reader.Read();

                // A rate outside Int64 can only have zero amounts if its
                // integer products are guaranteed to fit in Int64.
                Rates.Entries[index].Net =
                    reader.TryGetInt64(out long rate) ? rate : 0;
            }
        }
    }

    private static void ReadTransaction(ReadOnlySpan<byte> line)
    {
        var reader = new Utf8JsonReader(line, true, InitialState);
        Utf8JsonReader account = default;
        Utf8JsonReader currency = default;
        Utf8JsonReader amount = default;
        Utf8JsonReader channel = default;
        bool debit = false;

        reader.Read();

        while (reader.Read() && reader.TokenType != JsonTokenType.EndObject)
        {
            int field = GetField(ref reader);
            reader.Read();

            switch (field)
            {
                case 1: // account
                    account = reader;
                    break;

                case 2: // type
                    if (reader.ValueTextEquals("void"u8))
                        return;
                    debit = reader.ValueTextEquals("debit"u8);
                    break;

                case 3: // amount
                    amount = reader;
                    break;

                case 4: // currency
                    currency = reader;
                    break;

                case 5: // tags
                    while (reader.Read() &&
                           reader.TokenType != JsonTokenType.EndArray)
                    {
                        if (reader.ValueTextEquals("test"u8))
                            return;
                    }
                    break;

                case 6: // meta
                    while (reader.Read() &&
                           reader.TokenType != JsonTokenType.EndObject)
                    {
                        bool isChannel = reader.ValueTextEquals("channel"u8);
                        reader.Read();

                        if (isChannel)
                            channel = reader;
                        else
                            reader.Skip();
                    }
                    break;

                default:
                    reader.Skip();
                    break;
            }
        }

        int currencyIndex = Rates.GetToken(ref currency);
        long rateValue = Rates.Entries[currencyIndex].Net;
        long value = rateValue == 0
            ? 0
            : unchecked(ReadHundredths(ref amount) * rateValue) / 1_000_000;

        if (debit)
            value = -value;

        int accountIndex = Accounts.GetToken(ref account);
        int channelIndex = Channels.GetToken(ref channel);

        Accounts.Add(accountIndex, value);
        Channels.Add(channelIndex, value);
        counted++;
        net += value;
    }

    private static int GetField(ref Utf8JsonReader reader)
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

    private static long ReadHundredths(ref Utf8JsonReader reader)
    {
        if (!reader.ValueIsEscaped)
            return ParseHundredths(reader.ValueSpan);

        byte[] rented = null;
        int length = reader.ValueSpan.Length;
        Span<byte> decoded = length <= 256
            ? stackalloc byte[256]
            : (rented = ArrayPool<byte>.Shared.Rent(length));

        try
        {
            int written = reader.CopyString(decoded);
            return ParseHundredths(decoded[..written]);
        }
        finally
        {
            if (rented != null)
                ArrayPool<byte>.Shared.Return(rented);
        }
    }

    private static long ParseHundredths(ReadOnlySpan<byte> text)
    {
        long value = 0;
        int fractionalDigits = -1;

        foreach (byte c in text)
        {
            if (c == (byte)'.')
            {
                fractionalDigits = 0;
            }
            else
            {
                value = unchecked(value * 10 + c - (byte)'0');
                if (fractionalDigits >= 0)
                    fractionalDigits++;
            }
        }

        if (fractionalDigits < 0)
            return unchecked(value * 100);
        if (fractionalDigits == 1)
            return unchecked(value * 10);
        return value;
    }

    private static int CompareAccounts(int left, int right)
    {
        ref Entry a = ref Accounts.Entries[left];
        ref Entry b = ref Accounts.Entries[right];

        int comparison = b.Net.CompareTo(a.Net);
        return comparison != 0
            ? comparison
            : ((ReadOnlySpan<byte>)a.Key).SequenceCompareTo(b.Key);
    }

    private static void WriteOutput()
    {
        using var output = new StreamWriter(
            Console.OpenStandardOutput(), new UTF8Encoding(false), 1 << 16);
        output.NewLine = "\n";

        output.Write("counted ");
        output.WriteLine(counted);
        output.Write("net ");
        output.WriteLine(net);

        int[] channelOrder = new int[Channels.Count];
        for (int i = 0; i < channelOrder.Length; i++)
            channelOrder[i] = i;

        Array.Sort(channelOrder, (a, b) =>
            ((ReadOnlySpan<byte>)Channels.Entries[a].Key)
                .SequenceCompareTo(Channels.Entries[b].Key));

        foreach (int index in channelOrder)
        {
            ref Entry entry = ref Channels.Entries[index];
            output.Write("channel ");
            output.Write(Encoding.UTF8.GetString(entry.Key));
            output.Write(' ');
            output.Write(entry.Count);
            output.Write(' ');
            output.WriteLine(entry.Net);
        }

        Span<int> best = stackalloc int[10];
        int bestCount = 0;

        for (int i = 0; i < Accounts.Count; i++)
        {
            int position = 0;
            while (position < bestCount &&
                   CompareAccounts(best[position], i) <= 0)
                position++;

            if (position == 10)
                continue;

            int last = Math.Min(bestCount, 9);
            for (int j = last; j > position; j--)
                best[j] = best[j - 1];

            best[position] = i;
            if (bestCount < 10)
                bestCount++;
        }

        for (int i = 0; i < bestCount; i++)
        {
            ref Entry entry = ref Accounts.Entries[best[i]];
            output.Write("account ");
            output.Write(Encoding.UTF8.GetString(entry.Key));
            output.Write(' ');
            output.WriteLine(entry.Net);
        }
    }

    private struct Entry
    {
        public byte[] Key;
        public long Net;
        public long Count;
        public uint Hash;
        public int Next;
    }

    private sealed class ByteTable
    {
        public Entry[] Entries;
        public int Count;
        private int[] buckets;

        public ByteTable(int capacity)
        {
            Entries = new Entry[capacity];
            buckets = new int[capacity];
        }

        public void Add(int index, long value)
        {
            ref Entry entry = ref Entries[index];
            entry.Net += value;
            entry.Count++;
        }

        public int GetToken(ref Utf8JsonReader reader)
        {
            if (!reader.ValueIsEscaped)
                return GetOrAdd(reader.ValueSpan);

            int length = reader.ValueSpan.Length;
            byte[] rented = null;
            Span<byte> decoded = length <= 256
                ? stackalloc byte[256]
                : (rented = ArrayPool<byte>.Shared.Rent(length));

            try
            {
                int written = reader.CopyString(decoded);
                return GetOrAdd(decoded[..written]);
            }
            finally
            {
                if (rented != null)
                    ArrayPool<byte>.Shared.Return(rented);
            }
        }

        private int GetOrAdd(ReadOnlySpan<byte> key)
        {
            uint hash = 2166136261;
            foreach (byte c in key)
                hash = unchecked((hash ^ c) * 16777619);

            int bucket = (int)(hash & (uint)(buckets.Length - 1));

            for (int link = buckets[bucket]; link != 0;)
            {
                int index = link - 1;
                ref Entry entry = ref Entries[index];

                if (entry.Hash == hash && key.SequenceEqual(entry.Key))
                    return index;

                link = entry.Next;
            }

            if (Count == Entries.Length)
            {
                Grow();
                bucket = (int)(hash & (uint)(buckets.Length - 1));
            }

            int added = Count++;
            Entries[added] = new Entry
            {
                Key = key.ToArray(),
                Hash = hash,
                Next = buckets[bucket]
            };
            buckets[bucket] = added + 1;
            return added;
        }

        private void Grow()
        {
            int capacity = checked(Entries.Length * 2);
            Array.Resize(ref Entries, capacity);
            buckets = new int[capacity];

            for (int i = 0; i < Count; i++)
            {
                ref Entry entry = ref Entries[i];
                int bucket = (int)(entry.Hash & (uint)(capacity - 1));
                entry.Next = buckets[bucket];
                buckets[bucket] = i + 1;
            }
        }
    }
}
