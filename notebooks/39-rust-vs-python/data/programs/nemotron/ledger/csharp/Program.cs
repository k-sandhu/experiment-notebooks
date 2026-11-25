using System;
using System.Buffers.Text;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.Json;

public static class Program
{
    private sealed class Ch
    {
        public long count;
        public long net;
    }

    static int FindDot(ReadOnlySpan<byte> s)
    {
        for (int i = 0; i < s.Length; i++)
            if (s[i] == (byte)'.') return i;
        return -1;
    }

    // Convert amount string "12", "12.5", "12.05" to integer hundredths.
    static long ParseAmount(ReadOnlySpan<byte> s)
    {
        int dot = FindDot(s);
        long h = 0;
        long fr = 0;
        int fd = 0;
        for (int i = 0; i < s.Length; i++)
        {
            byte c = s[i];
            if (c >= (byte)'0' && c <= (byte)'9')
            {
                if (i < dot || dot < 0) h = h * 10 + (c - (byte)'0');
                else { fr = fr * 10 + (c - (byte)'0'); fd++; }
            }
        }
        if (dot < 0) return h * 100;
        return fd == 1 ? h * 100 + fr * 10 : h * 100 + fr;
    }

    static void AppendLong(StringBuilder sb, long v)
    {
        sb.Append(v);
    }

    public static int Main(string[] args)
    {
        if (args.Length < 1) return 1;
        byte[] data = File.ReadAllBytes(args[0]);
        int n = data.Length;

        int firstNewline = -1;
        for (int i = 0; i < n; i++)
            if (data[i] == (byte)'\n') { firstNewline = i; break; }
        if (firstNewline < 0) firstNewline = n;

        // Parse rates from first line.
        var rateMap = new Dictionary<string, long>(StringComparer.Ordinal);
        {
            var line = data.AsSpan(0, firstNewline);
            var reader = new Utf8JsonReader(line);
            reader.Read(); // StartObject
            while (reader.Read())
            {
                if (reader.TokenType == JsonTokenType.EndObject) break;
                string name = reader.GetString();
                reader.Read(); // value
                if (name == "rates")
                {
                    while (reader.Read())
                    {
                        if (reader.TokenType == JsonTokenType.EndObject) break;
                        string cname = reader.GetString();
                        reader.Read(); // number
                        rateMap[cname] = reader.GetInt64();
                    }
                }
                else if (reader.TokenType == JsonTokenType.StartObject || reader.TokenType == JsonTokenType.StartArray)
                {
                    reader.Skip();
                }
            }
        }

        var accounts = new Dictionary<string, long>(StringComparer.Ordinal);
        var channels = new Dictionary<string, Ch>(StringComparer.Ordinal);
        long counted = 0;
        long net = 0;

        int start = firstNewline + 1;
        while (start < n)
        {
            int end = start;
            while (end < n && data[end] != (byte)'\n') end++;
            ReadOnlySpan<byte> line = data.AsSpan(start, end - start);
            start = (end < n) ? end + 1 : end;

            var reader = new Utf8JsonReader(line);
            reader.Read(); // StartObject
            string account = null;
            string type = null;
            long hundredths = 0;
            string currency = null;
            bool testTag = false;
            string channel = null;

            while (reader.Read())
            {
                if (reader.TokenType == JsonTokenType.EndObject) break;
                string name = reader.GetString();
                reader.Read(); // value token
                switch (name)
                {
                    case "account":
                        account = reader.GetString();
                        break;
                    case "type":
                        type = reader.GetString();
                        break;
                    case "amount":
                        hundredths = ParseAmount(reader.ValueSpan);
                        break;
                    case "currency":
                        currency = reader.GetString();
                        break;
                    case "tags":
                        while (reader.Read())
                        {
                            if (reader.TokenType == JsonTokenType.EndArray) break;
                            if (reader.TokenType == JsonTokenType.String &&
                                reader.ValueTextEquals("test"))
                                testTag = true;
                            else if (reader.TokenType == JsonTokenType.StartObject)
                                reader.Skip();
                        }
                        break;
                    case "meta":
                        while (reader.Read())
                        {
                            if (reader.TokenType == JsonTokenType.EndObject) break;
                            string mname = reader.GetString();
                            reader.Read(); // value
                            if (mname == "channel")
                                channel = reader.GetString();
                            else if (reader.TokenType == JsonTokenType.StartObject ||
                                     reader.TokenType == JsonTokenType.StartArray)
                                reader.Skip();
                        }
                        break;
                    default:
                        if (reader.TokenType == JsonTokenType.StartObject ||
                            reader.TokenType == JsonTokenType.StartArray)
                            reader.Skip();
                        break;
                }
            }

            if (type != null && type != "void" && !testTag)
            {
                long rate = rateMap.TryGetValue(currency, out long r) ? r : 0L;
                long usd = (hundredths * rate) / 1000000L;
                long val = (type == "credit" || type == "refund") ? usd : -usd;
                counted++;
                net += val;
                if (!channels.TryGetValue(channel, out Ch c))
                {
                    c = new Ch();
                    channels[channel] = c;
                }
                c.count++;
                c.net += val;
                accounts[account] = accounts.TryGetValue(account, out long prev) ? prev + val : val;
            }
        }

        var sb = new StringBuilder();
        sb.Append("counted ");
        AppendLong(sb, counted);
        sb.Append('\n');
        sb.Append("net ");
        AppendLong(sb, net);
        sb.Append('\n');

        // Channels sorted by name ascending (byte/ordinal).
        var chList = new List<KeyValuePair<string, Ch>>(channels.Count);
        foreach (var kv in channels) chList.Add(kv);
        chList.Sort((a, b) => string.CompareOrdinal(a.Key, b.Key));
        foreach (var e in chList)
        {
            sb.Append("channel ");
            sb.Append(e.Key);
            sb.Append(' ');
            AppendLong(sb, e.Value.count);
            sb.Append(' ');
            AppendLong(sb, e.Value.net);
            sb.Append('\n');
        }

        // Top 10 accounts: net desc, id asc.
        var acList = new List<KeyValuePair<string, long>>(accounts.Count);
        foreach (var kv in accounts) acList.Add(kv);
        acList.Sort((a, b) =>
        {
            int cmp = b.Value.CompareTo(a.Value);
            if (cmp != 0) return cmp;
            return string.CompareOrdinal(a.Key, b.Key);
        });
        int m = Math.Min(acList.Count, 10);
        for (int i = 0; i < m; i++)
        {
            sb.Append("account ");
            sb.Append(acList[i].Key);
            sb.Append(' ');
            AppendLong(sb, acList[i].Value);
            sb.Append('\n');
        }

        Console.Write(sb.ToString());
        return 0;
    }
}
