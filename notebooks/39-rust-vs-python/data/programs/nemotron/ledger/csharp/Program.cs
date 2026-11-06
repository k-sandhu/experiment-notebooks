using System;
using System.Collections.Generic;
using System.IO;
using System.Text;

public class Program
{
    static byte[] file;
    static int pos;
    static int limit;

    static bool IsWS(int b) => b == ' ' || b == '\t' || b == '\r' || b == '\n';

    static StringBuilder sb = new StringBuilder();

    static bool ScanString()
    {
        sb.Clear();
        int i = pos + 1;
        while (i < limit)
        {
            int c = file[i++] & 0xFF;
            if (c == '"') { pos = i; return true; }
            if (c == '\\')
            {
                if (i >= limit) return false;
                int e = file[i++] & 0xFF;
                switch (e)
                {
                    case '"': sb.Append('"'); break;
                    case '\\': sb.Append('\\'); break;
                    case '/': sb.Append('/'); break;
                    case 'n': sb.Append('\n'); break;
                    case 'r': sb.Append('\r'); break;
                    case 't': sb.Append('\t'); break;
                    case 'b': sb.Append('\b'); break;
                    case 'f': sb.Append('\f'); break;
                    case 'u':
                    {
                        if (i + 6 >= limit) return false;
                        int cp = 0;
                        for (int k = 0; k < 4; k++) { int h = file[i++] & 0xFF; cp <<= 4;
                            if (h >= '0' && h <= '9') cp += h - '0';
                            else if (h >= 'a' && h <= 'f') cp += h - 'a' + 10;
                            else if (h >= 'A' && h <= 'F') cp += h - 'A' + 10;
                            else return false; }
                        if (cp >= 0xD800 && cp <= 0xDBFF && i + 1 < limit && file[i] == (byte)'\\' && file[i + 1] == (byte)'u')
                        {
                            i += 2;
                            int cp2 = 0;
                            for (int k = 0; k < 4; k++) { int h = file[i++] & 0xFF; cp2 <<= 4;
                                if (h >= '0' && h <= '9') cp2 += h - '0';
                                else if (h >= 'a' && h <= 'f') cp2 += h - 'a' + 10;
                                else if (h >= 'A' && h <= 'F') cp2 += h - 'A' + 10;
                                else return false; }
                            cp = 0x10000 + ((cp - 0xD800) << 10) + (cp2 - 0xDC00);
                        }
                        sb.Append(char.ConvertFromUtf32(cp));
                        break;
                    }
                    default: return false;
                }
            }
            else sb.Append((char)c);
        }
        return false;
    }

    static void SkipScalar()
    {
        while (pos < limit)
        {
            int b = file[pos] & 0xFF;
            if (b == ',' || b == '}' || b == ']' || IsWS(b)) return;
            pos++;
        }
    }

    enum Kind { RATES, COUNTED, SKIPPED, BAD }

    static string acct, typ, amt, cur, chan;
    static bool hasTest;
    static long usd;

    static Kind ParseLine()
    {
        int i = pos;
        while (i < limit && IsWS(file[i])) i++;
        if (i >= limit || file[i] != '{') return Kind.BAD;
        i++; // skip outer {
        pos = i;

        int depth = 1;
        string key = null;
        bool haveKey = false;
        int keyDepth = 0;

        bool inRates = false; int ratesDepth = 0;
        bool inMeta = false; int metaDepth = 0;
        bool inTags = false; int tagsDepth = 0;

        acct = null; typ = null; amt = null; cur = null; chan = null;
        hasTest = false;
        bool isRates = false;

        while (pos < limit && depth > 0)
        {
            int c = file[pos] & 0xFF;
            if (c == '"')
            {
                if (!ScanString()) return Kind.BAD;
                while (pos < limit && IsWS(file[pos])) pos++;
                if (pos < limit && file[pos] == ':')
                {
                    key = sb.ToString();
                    keyDepth = depth;
                    haveKey = true;
                    pos++; while (pos < limit && IsWS(file[pos])) pos++;
                    if (pos >= limit) return Kind.BAD;
                    int nxt = file[pos] & 0xFF;
                    if (nxt == '"')
                    {
                        if (!ScanString()) return Kind.BAD;
                        if (haveKey)
                        {
                            if (keyDepth == 1)
                            {
                                if (key == "account") acct = sb.ToString();
                                else if (key == "type") typ = sb.ToString();
                                else if (key == "currency") cur = sb.ToString();
                                else if (key == "amount") amt = sb.ToString();
                            }
                            else if (inMeta && depth == metaDepth && key == "channel") chan = sb.ToString();
                        }
                        haveKey = false;
                    }
                    else if (nxt == '{')
                    {
                        depth++; pos++;
                        if (haveKey && keyDepth == 1 && key == "rates") { inRates = true; ratesDepth = depth; isRates = true; }
                        else if (haveKey && keyDepth == 1 && key == "meta") { metaDepth = depth; inMeta = true; }
                        haveKey = false;
                    }
                    else if (nxt == '[')
                    {
                        depth++; pos++;
                        if (haveKey && keyDepth == 1 && key == "tags") { inTags = true; tagsDepth = depth; }
                        haveKey = false;
                    }
                    else
                    {
                        if (inRates && depth == ratesDepth && haveKey)
                        {
                            long v = 0; bool any = false;
                            while (pos < limit) { int h = file[pos] & 0xFF; if (h < '0' || h > '9') break; v = v * 10 + (h - '0'); pos++; any = true; }
                            if (!any) return Kind.BAD;
                            rates[key] = v;
                        }
                        else SkipScalar();
                        haveKey = false;
                    }
                }
                else
                {
                    if (inTags && depth == tagsDepth && sb.ToString() == "test") hasTest = true;
                    haveKey = false;
                }
            }
            else if (c == '{' || c == '[')
            {
                depth++; pos++; haveKey = false;
            }
            else if (c == '}' || c == ']')
            {
                depth--; pos++;
                if (inMeta && depth == metaDepth - 1) inMeta = false;
                if (inTags && depth == tagsDepth - 1) inTags = false;
                haveKey = false;
            }
            else pos++;
        }

        if (isRates) return Kind.RATES;
        if (typ == "void") return Kind.SKIPPED;
        if (hasTest) return Kind.SKIPPED;

        long dollars = 0; int j = 0;
        while (j < amt.Length && amt[j] >= '0' && amt[j] <= '9') { dollars = dollars * 10 + (amt[j] - '0'); j++; }
        long cents = 0;
        if (j < amt.Length && amt[j] == '.')
        {
            j++; int nd = 0;
            while (j < amt.Length && amt[j] >= '0' && amt[j] <= '9' && nd < 2) { cents = cents * 10 + (amt[j] - '0'); j++; nd++; }
            while (nd < 2) { cents *= 10; nd++; }
        }
        long hundredths = dollars * 100 + cents;

        if (!rates.TryGetValue(cur, out long rate)) return Kind.BAD;
        usd = (hundredths * rate) / 1000000L;
        if (typ == "debit") usd = -usd;
        return Kind.COUNTED;
    }

    static readonly Dictionary<string, long> rates = new Dictionary<string, long>();
    static readonly Dictionary<string, long[]> channels = new Dictionary<string, long[]>();
    static readonly Dictionary<string, long> accounts = new Dictionary<string, long>();
    static long totalCount, totalNet;

    public static void Main(string[] args)
    {
        file = File.ReadAllBytes(args[0]);
        limit = file.Length;
        pos = 0;

        var outb = new StringBuilder();
        while (pos < limit)
        {
            int lineStart = pos;
            while (pos < limit && file[pos] != '\n') pos++;
            int end = pos;
            int ln = end - lineStart;
            if (ln > 0)
            {
                int curLimit = limit;
                limit = end;
                pos = lineStart;
                Kind k = ParseLine();
                limit = curLimit;
                pos = end + 1; // skip newline
                if (k == Kind.RATES) { }
                else if (k == Kind.BAD) { }
                else if (k == Kind.SKIPPED) { }
                else
                {
                    totalCount++;
                    totalNet += usd;
                    if (!channels.TryGetValue(chan, out var c)) { c = new long[2]; channels[chan] = c; }
                    c[0]++; c[1] += usd;
                    accounts[acct] = accounts.TryGetValue(acct, out var v) ? v + usd : usd;
                }
            }
            else
            {
                pos = end + 1; // skip blank line / newline
            }
        }

        outb.Append("counted ").Append(totalCount).Append('\n');
        outb.Append("net ").Append(totalNet).Append('\n');

        var chNames = new List<string>(channels.Keys);
        chNames.Sort();
        foreach (var name in chNames)
        {
            var c = channels[name];
            outb.Append("channel ").Append(name).Append(' ').Append(c[0]).Append(' ').Append(c[1]).Append('\n');
        }

        var accts = new List<KeyValuePair<string, long>>(accounts);
        accts.Sort((a, b) => {
            int cmp = b.Value.CompareTo(a.Value);
            if (cmp != 0) return cmp;
            return string.Compare(a.Key, b.Key, StringComparison.Ordinal);
        });
        int lim = Math.Min(10, accts.Count);
        for (int k = 0; k < lim; k++)
        {
            outb.Append("account ").Append(accts[k].Key).Append(' ').Append(accts[k].Value).Append('\n');
        }

        // Write bytes without newline translation
        var bytes = Encoding.UTF8.GetBytes(outb.ToString());
        var stdout = Console.OpenStandardOutput();
        stdout.Write(bytes, 0, bytes.Length);
        stdout.Flush();
    }
}
