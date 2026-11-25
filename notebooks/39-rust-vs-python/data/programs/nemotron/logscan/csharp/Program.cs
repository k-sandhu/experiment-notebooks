using System;
using System.IO;
using System.Text;

// Summarise a web server access log (see SPEC.md).
// Single pass over the input: validate every line against the grammar, count
// status classes, group latency tenths by path template, then report the top 10.

sealed class Stats
{
    public int count;
    public int[] lat = new int[16];
    public int len;

    public void Add(int v)
    {
        if (len == lat.Length)
        {
            int[] nw = new int[lat.Length * 2];
            Array.Copy(lat, 0, nw, 0, len);
            lat = nw;
        }
        lat[len++] = v;
    }
}

// Open-addressing map from path template -> Stats. Keys are interned strings;
// lookups compare the raw char buffer against stored strings, so only unique
// templates are ever allocated as strings.
sealed class TMap
{
    internal string[] keys;
    internal Stats[] vals;
    internal int mask;
    internal int size;

    public TMap(int cap)
    {
        keys = new string[cap];
        vals = new Stats[cap];
        mask = cap - 1;
    }

    public Stats FindOrAdd(ReadOnlySpan<char> buf, int len)
    {
        uint h = Hash(buf.Slice(0, len));
        for (int slot = (int)(h & mask); ; slot = (slot + 1) & mask)
        {
            string k = keys[slot];
            if (k == null)
            {
                keys[slot] = buf.Slice(0, len).ToString();
                var st = new Stats();
                vals[slot] = st;
                if (++size * 4 > keys.Length * 3) Grow();
                return st;
            }
            if (k.Length == len && Equals(k, buf.Slice(0, len))) return vals[slot];
        }
    }

    private static bool Equals(string k, ReadOnlySpan<char> b)
    {
        if (k.Length != b.Length) return false;
        for (int i = 0; i < k.Length; i++) if (k[i] != b[i]) return false;
        return true;
    }

    private void Grow()
    {
        string[] oldK = keys;
        Stats[] oldV = vals;
        int cap = oldK.Length * 2;
        keys = new string[cap];
        vals = new Stats[cap];
        mask = cap - 1;
        size = 0;
        for (int i = 0; i < oldK.Length; i++)
        {
            string k = oldK[i];
            if (k != null) Put0(k, oldV[i]);
        }
    }

    private void Put0(string k, Stats v)
    {
        uint h = HashStr(k);
        for (int slot = (int)(h & mask); ; slot = (slot + 1) & mask)
        {
            if (keys[slot] == null)
            {
                keys[slot] = k;
                vals[slot] = v;
                ++size;
                return;
            }
        }
    }

    private static uint Hash(ReadOnlySpan<char> b)
    {
        uint h = 2166136261;
        foreach (char c in b) { h ^= (byte)c; h *= 16777619; }
        return h;
    }

    private static uint HashStr(string s)
    {
        uint h = 2166136261;
        foreach (char c in s) { h ^= (byte)c; h *= 16777619; }
        return h;
    }
}

static class Program
{
    // Result of parsing one line.
    struct Res
    {
        public int cls;
        public int lat; // tenths of a ms
        public int pathStart;
        public int pathEnd;
    }

    static bool IsDig(byte c) { return c >= '0' && c <= '9'; }
    static bool PathChar(byte c) =>
        (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') ||
        c == '_' || c == '/' || c == '-';

    // Validates one line (without its newline) against the SPEC.md regex and
    // extracts status class, latency (tenths of a ms) and the path span.
    static bool ParseLine(byte[] d, int start, int end, ref Res r)
    {
        int len = end - start;
        if (len < 49) return false; // shortest possible well-formed line

        // timestamp: \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z<sp>
        if (d[start + 4] != '-' || d[start + 7] != '-' || d[start + 10] != 'T' ||
            d[start + 13] != ':' || d[start + 16] != ':' || d[start + 19] != '.' ||
            d[start + 23] != 'Z' || d[start + 24] != ' ')
            return false;
        if (!IsDig(d[start]) || !IsDig(d[start + 1]) || !IsDig(d[start + 2]) || !IsDig(d[start + 3]) ||
            !IsDig(d[start + 5]) || !IsDig(d[start + 6]) || !IsDig(d[start + 8]) || !IsDig(d[start + 9]) ||
            !IsDig(d[start + 11]) || !IsDig(d[start + 12]) || !IsDig(d[start + 14]) || !IsDig(d[start + 15]) ||
            !IsDig(d[start + 17]) || !IsDig(d[start + 18]) || !IsDig(d[start + 20]) || !IsDig(d[start + 21]) ||
            !IsDig(d[start + 22]))
            return false;

        // host: [a-z]+-\d+<sp>
        int h = start + 25;
        if (h >= end || d[h] < 'a' || d[h] > 'z') return false;
        do { ++h; } while (h < end && d[h] >= 'a' && d[h] <= 'z');
        if (h >= end || d[h] != '-') return false;
        ++h;
        if (h >= end || !IsDig(d[h])) return false;
        do { ++h; } while (h < end && IsDig(d[h]));
        if (h >= end || d[h] != ' ') return false;
        ++h; // method

        int mlen = 0;
        int rem = end - h;
        if (rem >= 3 && Match(d, h, "GET")) mlen = 3;
        else if (rem >= 3 && Match(d, h, "PUT")) mlen = 3;
        else if (rem >= 4 && Match(d, h, "POST")) mlen = 4;
        else if (rem >= 6 && Match(d, h, "DELETE")) mlen = 6;
        else if (rem >= 5 && Match(d, h, "PATCH")) mlen = 5;
        if (mlen == 0) return false;
        h += mlen;
        if (h >= end || d[h] != ' ') return false;
        ++h;

        // path: /[A-Za-z0-9_/-]* then optional \?[^ ]* then <sp>
        if (h >= end || d[h] != '/') return false;
        int pathStart = h;
        ++h;
        while (h < end)
        {
            byte c = d[h];
            if (c == ' ' || c == '?') break;
            if (!PathChar(c)) return false;
            ++h;
        }
        int pathEnd = h;
        if (h < end && d[h] == '?')
        {
            ++h;
            while (h < end && d[h] != ' ') ++h;
        }
        if (h >= end || d[h] != ' ') return false;
        ++h;

        // status: \d{3}<sp>
        if (end - h < 3 || !IsDig(d[h]) || !IsDig(d[h + 1]) || !IsDig(d[h + 2])) return false;
        r.cls = d[h] - '0';
        h += 3;
        if (h >= end || d[h] != ' ') return false;
        ++h;

        // size: \d+B<sp>
        if (h >= end || !IsDig(d[h])) return false;
        do { ++h; } while (h < end && IsDig(d[h]));
        if (h >= end || d[h] != 'B') return false;
        ++h;
        if (h >= end || d[h] != ' ') return false;
        ++h;

        // latency: \d+.\dms "<ua>"<end>
        long lat = 0;
        if (h >= end || !IsDig(d[h])) return false;
        do { lat = lat * 10 + (d[h] - '0'); ++h; } while (h < end && IsDig(d[h]));
        if (h >= end || d[h] != '.') return false;
        ++h;
        if (h >= end || !IsDig(d[h])) return false;
        lat = lat * 10 + (d[h] - '0');
        ++h;
        if (end - h < 4 || d[h] != 'm' || d[h + 1] != 's' || d[h + 2] != ' ' || d[h + 3] != '"')
            return false;
        h += 4;
        while (h < end && d[h] != '"') ++h;
        if (h >= end || d[h] != '"') return false;
        ++h;
        if (h != end) return false;

        r.pathStart = pathStart;
        r.pathEnd = pathEnd;
        r.lat = (int)lat;
        return true;
    }

    static bool Match(byte[] d, int pos, string lit)
    {
        for (int i = 0; i < lit.Length; i++) if (d[pos + i] != (byte)lit[i]) return false;
        return true;
    }

    static int Main(string[] args)
    {
        byte[] data = File.ReadAllBytes(args[0]);
        int n = data.Length;
        int p = 0;
        long nLines = 0, nMalformed = 0;
        int[] statusCount = new int[10];
        var map = new TMap(1 << 14);
        char[] tmplArr = new char[128];
        Res res = default;

        while (p < n)
        {
            ++nLines;
            int lineStart = p;
            int e = p;
            while (e < n && data[e] != '\n') ++e;
            // line is [lineStart, e)

            if (ParseLine(data, lineStart, e, ref res))
            {
                ++statusCount[res.cls];

                // path template: split on '/', replace all-digit segments with {id}
                Span<char> tmpl = tmplArr;
                int tlen = 1;
                tmpl[0] = '/';
                int segStart = res.pathStart + 1;
                int i = segStart;
                for (;;)
                {
                    if (i == res.pathEnd || data[i] == '/')
                    {
                        int seglen = i - segStart;
                        if (seglen > 0)
                        {
                            bool allDig = true;
                            for (int j = segStart; j < i; j++)
                            {
                                if (!IsDig(data[j])) { allDig = false; break; }
                            }
                            if (allDig)
                            {
                                tmpl[tlen++] = '{';
                                tmpl[tlen++] = 'i';
                                tmpl[tlen++] = 'd';
                                tmpl[tlen++] = '}';
                            }
                            else
                            {
                                for (int j = segStart; j < i; j++) tmpl[tlen++] = (char)data[j];
                            }
                        }
                        if (i < res.pathEnd) tmpl[tlen++] = '/';
                        segStart = i + 1;
                    }
                    if (i == res.pathEnd) break;
                    ++i;
                }

                Stats st = map.FindOrAdd(tmpl.Slice(0, tlen), tlen);
                ++st.count;
                st.Add(res.lat);
            }
            else
            {
                ++nMalformed;
            }
            p = e + 1;
        }

        // collect items and sort: count descending, then template ascending (byte order)
        int m = 0;
        for (int slot = 0; slot < map.keys.Length; slot++) if (map.keys[slot] != null) m++;
        var items = new (string name, Stats st)[m];
        int k = 0;
        for (int slot = 0; slot < map.keys.Length; slot++)
        {
            if (map.keys[slot] != null) { items[k] = (map.keys[slot], map.vals[slot]); k++; }
        }
        Array.Sort(items, (a, b) =>
        {
            int cmp = b.st.count.CompareTo(a.st.count);
            if (cmp != 0) return cmp;
            return string.CompareOrdinal(a.name, b.name); // byte order
        });

        StringBuilder sb = new StringBuilder(8192);
        sb.Append("lines ").Append(nLines).Append('\n');
        sb.Append("malformed ").Append(nMalformed).Append('\n');
        for (int c = 0; c < 10; c++)
        {
            if (statusCount[c] != 0)
                sb.Append("status ").Append((char)('0' + c)).Append("xx ").Append(statusCount[c]).Append('\n');
        }
        int top = m < 10 ? m : 10;
        for (int i = 0; i < top; i++)
        {
            var (name, st) = items[i];
            Array.Sort(st.lat, 0, st.len);
            int nn = st.len;
            sb.Append("path ").Append(name).Append(' ').Append(st.count).Append(' ');
            AppendLat(sb, Lat(st.lat, nn, 50));
            sb.Append(' ');
            AppendLat(sb, Lat(st.lat, nn, 95));
            sb.Append(' ');
            AppendLat(sb, st.lat[nn - 1]);
            sb.Append('\n');
        }

        byte[] outb = Encoding.ASCII.GetBytes(sb.ToString());
        using var stdout = Console.OpenStandardOutput();
        stdout.Write(outb, 0, outb.Length);
        return 0;
    }

    static int Lat(int[] lat, int nn, int pct) => lat[((long)pct * nn + 99) / 100 - 1];

    static void AppendLat(StringBuilder sb, int t)
    {
        sb.Append(t / 10).Append('.').Append(t % 10);
    }
}
