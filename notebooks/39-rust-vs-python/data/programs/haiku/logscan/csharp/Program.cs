using System;
using System.Collections.Generic;
using System.IO;
using System.Text;

// Log scan: status-class counts and latency percentiles of the busiest path templates (see SPEC.md).
//
// The file is streamed in 1 MiB chunks. Each line is checked by a hand-written matcher that accepts
// exactly the language of the SPEC regex. Path templates are interned in an open-addressing table keyed
// by bytes, so no string is created per line. Only the ten busiest templates have their latencies sorted.
internal static class Program
{
    private const int ChunkSize = 1 << 20;
    private const int TopN = 10;

    // Characters allowed in the path group: [A-Za-z0-9_/-], indexed by byte value.
    private static readonly bool[] PathChar = BuildPathTable();

    private static bool[] BuildPathTable()
    {
        var t = new bool[256];
        for (int c = 0; c < 256; c++)
        {
            t[c] = (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') ||
                   c == '_' || c == '/' || c == '-';
        }
        return t;
    }

    private static int Main(string[] args)
    {
        if (args.Length < 1)
        {
            Console.Error.WriteLine("usage: solution INPUT_PATH");
            return 2;
        }

        var scanner = new LogScanner(PathChar);
        using (var fs = new FileStream(args[0], FileMode.Open, FileAccess.Read, FileShare.Read, 1,
                   FileOptions.SequentialScan))
        {
            byte[] buf = new byte[ChunkSize];
            int start = 0;  // first byte of the unprocessed data
            int end = 0;    // one past the last byte read
            bool eof = false;
            while (true)
            {
                int nl = buf.AsSpan(start, end - start).IndexOf((byte)'\n');
                if (nl >= 0)
                {
                    scanner.Add(buf.AsSpan(start, nl));
                    start += nl + 1;
                    continue;
                }
                if (eof)
                {
                    if (start < end) scanner.Add(buf.AsSpan(start, end - start));  // last line without '\n'
                    break;
                }
                // No complete line in the buffer: move the partial line to the front and read more.
                if (start > 0)
                {
                    Buffer.BlockCopy(buf, start, buf, 0, end - start);
                    end -= start;
                    start = 0;
                }
                if (end == buf.Length) Array.Resize(ref buf, buf.Length * 2);  // one line longer than the buffer
                int n = fs.Read(buf, end, buf.Length - end);
                if (n == 0) eof = true;
                else end += n;
            }
        }

        // Write raw bytes so that '\n' is not expanded to "\r\n" on Windows.
        byte[] text = Encoding.ASCII.GetBytes(scanner.Report());
        using (Stream stdout = Console.OpenStandardOutput())
        {
            stdout.Write(text, 0, text.Length);
            stdout.Flush();
        }
        return 0;
    }

    private sealed class Template
    {
        public readonly byte[] Name;
        public readonly int Hash;
        public long Count;
        public long[] Latencies = new long[4];  // tenths of a millisecond
        public int Size;

        public Template(byte[] name, int hash)
        {
            Name = name;
            Hash = hash;
        }
    }

    private sealed class LogScanner
    {
        private readonly bool[] _pathChar;
        private long _total;
        private long _malformed;
        private readonly long[] _statusCount = new long[10];

        // Fields set by Parse for the line that matched; path offsets are relative to the line.
        private int _pathStart;
        private int _pathEnd;
        private int _statusClass;
        private long _tenths;

        private byte[] _tmpl = new byte[1024];
        private int _tmplLen;

        private readonly List<Template> _templates = new List<Template>();
        private int[] _table = new int[1 << 12];  // stores template index + 1; 0 means empty

        public LogScanner(bool[] pathChar)
        {
            _pathChar = pathChar;
        }

        public void Add(ReadOnlySpan<byte> line)
        {
            _total++;
            if (!Parse(line))
            {
                _malformed++;
                return;
            }
            _statusCount[_statusClass]++;
            BuildTemplate(line.Slice(_pathStart, _pathEnd - _pathStart));
            int h = Hash(_tmpl.AsSpan(0, _tmplLen));
            Template t = Find(h);
            t.Count++;
            if (t.Size == t.Latencies.Length) Array.Resize(ref t.Latencies, t.Size * 2);
            t.Latencies[t.Size++] = _tenths;
        }

        // Finds the template for _tmpl[0.._tmplLen), creating it if needed.
        private Template Find(int h)
        {
            int mask = _table.Length - 1;
            int i = h & mask;
            ReadOnlySpan<byte> key = _tmpl.AsSpan(0, _tmplLen);
            for (int v = _table[i]; v != 0; v = _table[i])
            {
                Template t = _templates[v - 1];
                if (t.Hash == h && t.Name.AsSpan().SequenceEqual(key)) return t;
                i = (i + 1) & mask;
            }
            var created = new Template(key.ToArray(), h);
            _templates.Add(created);
            _table[i] = _templates.Count;
            if (_templates.Count * 2 > _table.Length) Grow();
            return created;
        }

        private void Grow()
        {
            var bigger = new int[_table.Length * 2];
            int mask = bigger.Length - 1;
            for (int k = 0; k < _templates.Count; k++)
            {
                int i = _templates[k].Hash & mask;
                while (bigger[i] != 0) i = (i + 1) & mask;
                bigger[i] = k + 1;
            }
            _table = bigger;
        }

        private static int Hash(ReadOnlySpan<byte> b)
        {
            uint h = 0x811c9dc5;  // FNV-1a
            foreach (byte c in b) h = (h ^ c) * 0x01000193;
            h ^= h >> 16;
            h *= 0x85ebca6b;
            return (int)(h ^ (h >> 13));
        }

        // Path template: each non-empty all-digit segment becomes {id}. Writes into _tmpl.
        private void BuildTemplate(ReadOnlySpan<byte> path)
        {
            if (_tmpl.Length < 4 * path.Length + 4) _tmpl = new byte[4 * path.Length + 4];
            int n = 0;
            int s = 0;
            int len = path.Length;
            while (true)
            {
                int e = s;
                bool digits = true;
                while (e < len && path[e] != (byte)'/')
                {
                    digits &= IsDigit(path[e]);
                    e++;
                }
                if (e > s && digits)
                {
                    "{id}"u8.CopyTo(_tmpl.AsSpan(n));
                    n += 4;
                }
                else
                {
                    path.Slice(s, e - s).CopyTo(_tmpl.AsSpan(n));
                    n += e - s;
                }
                if (e == len) break;
                _tmpl[n++] = (byte)'/';
                s = e + 1;
            }
            _tmplLen = n;
        }

        // Matches one line (without its '\n') against the SPEC regex. Returns false if malformed.
        private bool Parse(ReadOnlySpan<byte> l)
        {
            int len = l.Length;
            if (len < 25) return false;
            ReadOnlySpan<byte> ts = "dddd-dd-ddTdd:dd:dd.dddZ"u8;
            for (int i = 0; i < 24; i++)
            {
                if (ts[i] == 'd' ? !IsDigit(l[i]) : l[i] != ts[i]) return false;
            }
            if (l[24] != ' ') return false;

            // Host: [a-z]+-\d+ followed by a space.
            int q = 25;
            int s = q;
            while (q < len && IsLower(l[q])) q++;
            if (q == s || q == len || l[q] != '-') return false;
            q++;
            s = q;
            while (q < len && IsDigit(l[q])) q++;
            if (q == s || q == len || l[q] != ' ') return false;
            q++;

            // Method, then a space.
            ReadOnlySpan<byte> rest = l.Slice(q);
            if (rest.StartsWith("GET "u8)) q += 4;
            else if (rest.StartsWith("POST "u8)) q += 5;
            else if (rest.StartsWith("PUT "u8)) q += 4;
            else if (rest.StartsWith("DELETE "u8)) q += 7;
            else if (rest.StartsWith("PATCH "u8)) q += 6;
            else return false;

            // Path: '/' and path characters, then an optional query running to the next space.
            if (q == len || l[q] != '/') return false;
            _pathStart = q;
            q++;
            while (q < len && _pathChar[l[q]]) q++;
            _pathEnd = q;
            if (q < len && l[q] == '?')
            {
                while (q < len && l[q] != ' ') q++;
            }
            if (q == len || l[q] != ' ') return false;
            q++;

            // Status: three digits, then a space.
            if (len - q < 4 || !IsDigit(l[q]) || !IsDigit(l[q + 1]) || !IsDigit(l[q + 2]) || l[q + 3] != ' ')
            {
                return false;
            }
            _statusClass = l[q] - '0';
            q += 4;

            // Size: \d+B followed by a space.
            s = q;
            while (q < len && IsDigit(l[q])) q++;
            if (q == s || q == len || l[q] != 'B') return false;
            q++;
            if (q == len || l[q] != ' ') return false;
            q++;

            // Latency: \d+ '.' \d 'ms' followed by a space, kept in tenths of a millisecond.
            s = q;
            long whole = 0;
            while (q < len && IsDigit(l[q]))
            {
                whole = whole * 10 + (l[q] - '0');
                q++;
            }
            if (q == s || q == len || l[q] != '.') return false;
            q++;
            if (q == len || !IsDigit(l[q])) return false;
            long frac = l[q] - '0';
            q++;
            if (len - q < 3 || l[q] != 'm' || l[q + 1] != 's' || l[q + 2] != ' ') return false;
            q += 3;
            _tenths = whole * 10 + frac;

            // User agent: "[^"]*" which must end the line.
            if (len - q < 2 || l[q] != '"' || l[len - 1] != '"') return false;
            for (int u = q + 1; u < len - 1; u++)
            {
                if (l[u] == '"') return false;
            }
            return true;
        }

        public string Report()
        {
            var sb = new StringBuilder();
            sb.Append("lines ").Append(_total).Append('\n');
            sb.Append("malformed ").Append(_malformed).Append('\n');
            for (int c = 0; c < 10; c++)
            {
                if (_statusCount[c] != 0)
                {
                    sb.Append("status ").Append(c).Append("xx ").Append(_statusCount[c]).Append('\n');
                }
            }

            // Keep the TopN busiest templates, best first, by insertion into a small sorted list.
            var top = new List<Template>(TopN + 1);
            foreach (Template t in _templates)
            {
                if (top.Count == TopN)
                {
                    if (!Better(t, top[TopN - 1])) continue;
                    top[TopN - 1] = t;
                }
                else
                {
                    top.Add(t);
                }
                for (int k = top.Count - 1; k > 0 && Better(top[k], top[k - 1]); k--)
                {
                    (top[k], top[k - 1]) = (top[k - 1], top[k]);
                }
            }

            foreach (Template t in top)
            {
                Array.Sort(t.Latencies, 0, t.Size);
                int n = t.Size;
                long p50 = t.Latencies[(50L * n + 99) / 100 - 1];
                long p95 = t.Latencies[(95L * n + 99) / 100 - 1];
                long max = t.Latencies[n - 1];
                sb.Append("path ").Append(Encoding.ASCII.GetString(t.Name)).Append(' ').Append(t.Count)
                    .Append(' ').Append(FormatTenths(p50)).Append(' ').Append(FormatTenths(p95))
                    .Append(' ').Append(FormatTenths(max)).Append('\n');
            }
            return sb.ToString();
        }

        private static bool Better(Template a, Template b)
        {
            if (a.Count != b.Count) return a.Count > b.Count;
            return a.Name.AsSpan().SequenceCompareTo(b.Name) < 0;
        }

        private static string FormatTenths(long t)
        {
            return (t / 10).ToString() + "." + (char)('0' + t % 10);
        }

        private static bool IsDigit(byte c) => (uint)(c - '0') < 10;

        private static bool IsLower(byte c) => (uint)(c - 'a') < 26;
    }
}
