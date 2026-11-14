using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Numerics;
using System.Runtime.InteropServices;
using System.Text;
using System.Text.Json;

internal static class Program
{
    private struct Rate
    {
        public long Value;
        public bool OutsideInt64;
    }

    private struct ChannelTotal
    {
        public long Count;
        public long Net;
    }

    private static readonly Dictionary<string, Rate> Rates = new(StringComparer.Ordinal);
    private static readonly Dictionary<string, long> Accounts = new(StringComparer.Ordinal);
    private static readonly Dictionary<string, ChannelTotal> Channels = new(StringComparer.Ordinal);

    private static readonly JsonReaderOptions ReaderOptions = new()
    {
        MaxDepth = int.MaxValue
    };

    private static long totalCount;
    private static long totalNet;

    private static void Main(string[] args)
    {
        using var input = new FileStream(
            args[0], FileMode.Open, FileAccess.Read, FileShare.Read,
            1 << 20, FileOptions.SequentialScan);

        byte[] buffer = new byte[1 << 20];
        int start = 0;
        int end = 0;
        bool firstLine = true;

        while (true)
        {
            if (end == buffer.Length)
            {
                if (start != 0)
                {
                    Buffer.BlockCopy(buffer, start, buffer, 0, end - start);
                    end -= start;
                    start = 0;
                }
                else
                {
                    Array.Resize(ref buffer, checked(buffer.Length * 2));
                }
            }

            int read = input.Read(buffer, end, buffer.Length - end);
            if (read == 0)
                break;

            end += read;

            while (start < end)
            {
                int offset = buffer.AsSpan(start, end - start).IndexOf((byte)'\n');
                if (offset < 0)
                    break;

                int length = offset;
                if (length > 0 && buffer[start + length - 1] == (byte)'\r')
                    length--;

                ReadOnlySpan<byte> line = buffer.AsSpan(start, length);
                if (firstLine)
                {
                    if (line.StartsWith("\xEF\xBB\xBF"u8))
                        line = line[3..];

                    ReadRates(line);
                    firstLine = false;
                }
                else
                {
                    ReadTransaction(line);
                }

                start += offset + 1;
            }

            if (start == end)
            {
                start = 0;
                end = 0;
            }
        }

        using var output = new StreamWriter(Console.OpenStandardOutput(), new UTF8Encoding(false), 1 << 16);
        output.Write("counted ");
        output.WriteLine(totalCount.ToString(CultureInfo.InvariantCulture));
        output.Write("net ");
        output.WriteLine(totalNet.ToString(CultureInfo.InvariantCulture));

        var channelNames = new List<string>(Channels.Keys);
        channelNames.Sort(StringComparer.Ordinal);
        foreach (string name in channelNames)
        {
            ChannelTotal value = Channels[name];
            output.Write("channel ");
            output.Write(name);
            output.Write(' ');
            output.Write(value.Count.ToString(CultureInfo.InvariantCulture));
            output.Write(' ');
            output.WriteLine(value.Net.ToString(CultureInfo.InvariantCulture));
        }

        var top = new KeyValuePair<string, long>[10];
        int topCount = 0;

        foreach (var entry in Accounts)
        {
            int position = 0;
            while (position < topCount)
            {
                var current = top[position];
                if (entry.Value > current.Value ||
                    (entry.Value == current.Value &&
                     string.CompareOrdinal(entry.Key, current.Key) < 0))
                {
                    break;
                }
                position++;
            }

            if (position >= 10)
                continue;

            int newCount = Math.Min(topCount + 1, 10);
            for (int i = newCount - 1; i > position; i--)
                top[i] = top[i - 1];

            top[position] = entry;
            topCount = newCount;
        }

        for (int i = 0; i < topCount; i++)
        {
            output.Write("account ");
            output.Write(top[i].Key);
            output.Write(' ');
            output.WriteLine(top[i].Value.ToString(CultureInfo.InvariantCulture));
        }
    }

    private static void ReadRates(ReadOnlySpan<byte> line)
    {
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
                string currency = reader.GetString();
                reader.Read();

                Rate rate;
                if (reader.TryGetInt64(out long value))
                {
                    rate = new Rate { Value = value };
                }
                else
                {
                    BigInteger big = BigInteger.Parse(
                        Encoding.UTF8.GetString(reader.ValueSpan),
                        CultureInfo.InvariantCulture);

                    rate = big >= long.MinValue && big <= long.MaxValue
                        ? new Rate { Value = (long)big }
                        : new Rate { OutsideInt64 = true };
                }

                Rates[currency] = rate;
            }
        }
    }

    private static void ReadTransaction(ReadOnlySpan<byte> line)
    {
        var reader = new Utf8JsonReader(line, ReaderOptions);
        reader.Read();

        string account = null;
        string currency = null;
        string channel = null;
        long hundredths = 0;
        bool debit = false;

        while (reader.Read() && reader.TokenType != JsonTokenType.EndObject)
        {
            if (reader.ValueTextEquals("account"u8))
            {
                reader.Read();
                account = reader.GetString();
            }
            else if (reader.ValueTextEquals("currency"u8))
            {
                reader.Read();
                currency = reader.GetString();
            }
            else if (reader.ValueTextEquals("amount"u8))
            {
                reader.Read();
                hundredths = ReadAmount(ref reader);
            }
            else if (reader.ValueTextEquals("type"u8))
            {
                reader.Read();
                if (reader.ValueTextEquals("void"u8))
                    return;
                debit = reader.ValueTextEquals("debit"u8);
            }
            else if (reader.ValueTextEquals("tags"u8))
            {
                reader.Read();
                while (reader.Read() && reader.TokenType != JsonTokenType.EndArray)
                {
                    if (reader.ValueTextEquals("test"u8))
                        return;
                }
            }
            else if (reader.ValueTextEquals("meta"u8))
            {
                reader.Read();
                while (reader.Read() && reader.TokenType != JsonTokenType.EndObject)
                {
                    bool isChannel = reader.ValueTextEquals("channel"u8);
                    reader.Read();
                    if (isChannel)
                        channel = reader.GetString();
                    else
                        reader.Skip();
                }
            }
            else
            {
                reader.Read();
                reader.Skip();
            }
        }

        Rate rate = Rates[currency];
        long usd = 0;

        if (!rate.OutsideInt64)
        {
            long product = unchecked(hundredths * rate.Value);
            usd = product / 1_000_000;
            if (product < 0 && product % 1_000_000 != 0)
                usd--;
        }

        long signedValue = debit ? -usd : usd;
        totalCount++;
        totalNet += signedValue;

        ref long accountNet = ref CollectionsMarshal.GetValueRefOrAddDefault(
            Accounts, account, out _);
        accountNet += signedValue;

        ref ChannelTotal channelTotal = ref CollectionsMarshal.GetValueRefOrAddDefault(
            Channels, channel, out _);
        channelTotal.Count++;
        channelTotal.Net += signedValue;
    }

    private static long ReadAmount(ref Utf8JsonReader reader)
    {
        long value = 0;
        int fractionalDigits = -1;

        if (!reader.ValueIsEscaped)
        {
            foreach (byte c in reader.ValueSpan)
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
        }
        else
        {
            string text = reader.GetString();
            foreach (char c in text)
            {
                if (c == '.')
                {
                    fractionalDigits = 0;
                }
                else
                {
                    value = unchecked(value * 10 + c - '0');
                    if (fractionalDigits >= 0)
                        fractionalDigits++;
                }
            }
        }

        if (fractionalDigits < 0)
            return unchecked(value * 100);
        if (fractionalDigits == 1)
            return unchecked(value * 10);
        return value;
    }
}
