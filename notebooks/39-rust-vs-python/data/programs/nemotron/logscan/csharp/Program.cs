// Log scan: summarise an access log by status class and path-template latency percentiles.
// .NET 8, BCL only, Release.

using System;
using System.Buffers.Binary;
using System.Collections.Generic;
using System.IO;
using System.Runtime.InteropServices;

class Stats {
    public int count;
    public int maxT; // max latency in tenths of a ms
    public List<int> lats = new List<int>(16);

    public void Add(int t) {
        count++;
        if (t > maxT) maxT = t;
        lats.Add(t);
    }
}

class Program {
    static bool IsDigit(byte c) => c >= (byte)'0' && c <= (byte)'9';
    static bool IsUpper(byte c) => c >= (byte)'A' && c <= (byte)'Z';
    static bool IsLower(byte c) => c >= (byte)'a' && c <= (byte)'z';

    // Strictly validates one line; if well-formed sets out fields and returns true.
    // Template is built into tb (reused char buffer), length in tlen.
    static bool ParseLine(byte[] b, int p, int end, char[] tb, ref int tlen,
                          out int statusClass, out int latencyT) {
        statusClass = 0;
        latencyT = 0;

        // 1. timestamp: \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z<space>
        if (end - p < 25) return false;
        if (!IsDigit(b[p]) || !IsDigit(b[p + 1]) || !IsDigit(b[p + 2]) || !IsDigit(b[p + 3])) return false;
        if (b[p + 4] != (byte)'-') return false;
        if (!IsDigit(b[p + 5]) || !IsDigit(b[p + 6])) return false;
        if (b[p + 7] != (byte)'-') return false;
        if (!IsDigit(b[p + 8]) || !IsDigit(b[p + 9])) return false;
        if (b[p + 10] != (byte)'T') return false;
        if (!IsDigit(b[p + 11]) || !IsDigit(b[p + 12])) return false;
        if (b[p + 13] != (byte)':') return false;
        if (!IsDigit(b[p + 14]) || !IsDigit(b[p + 15])) return false;
        if (b[p + 16] != (byte)':') return false;
        if (!IsDigit(b[p + 17]) || !IsDigit(b[p + 18])) return false;
        if (b[p + 19] != (byte)'.') return false;
        if (!IsDigit(b[p + 20]) || !IsDigit(b[p + 21]) || !IsDigit(b[p + 22])) return false;
        if (b[p + 23] != (byte)'Z' || b[p + 24] != (byte)' ') return false;
        p += 25;

        // 2. host: [a-z]+-\d+<space>
        if (p >= end || !IsLower(b[p])) return false;
        do { p++; } while (p < end && IsLower(b[p]));
        if (p >= end || b[p] != (byte)'-') return false;
        p++;
        if (p >= end || !IsDigit(b[p])) return false;
        do { p++; } while (p < end && IsDigit(b[p]));
        if (p >= end || b[p] != (byte)' ') return false;
        p++;

        // 3. method
        bool ok = false;
        if (!ok && end - p > 3 && b[p] == (byte)'G' && b[p + 1] == (byte)'E' && b[p + 2] == (byte)'T' && b[p + 3] == (byte)' ') { p += 4; ok = true; }
        if (!ok && end - p > 4 && b[p] == (byte)'P' && b[p + 1] == (byte)'O' && b[p + 2] == (byte)'S' && b[p + 3] == (byte)'T' && b[p + 4] == (byte)' ') { p += 5; ok = true; }
        if (!ok && end - p > 3 && b[p] == (byte)'P' && b[p + 1] == (byte)'U' && b[p + 2] == (byte)'T' && b[p + 3] == (byte)' ') { p += 4; ok = true; }
        if (!ok && end - p > 6 && b[p] == (byte)'D' && b[p + 1] == (byte)'E' && b[p + 2] == (byte)'L' && b[p + 3] == (byte)'E' && b[p + 4] == (byte)'T' && b[p + 5] == (byte)'E' && b[p + 6] == (byte)' ') { p += 7; ok = true; }
        if (!ok && end - p > 5 && b[p] == (byte)'P' && b[p + 1] == (byte)'A' && b[p + 2] == (byte)'T' && b[p + 3] == (byte)'C' && b[p + 4] == (byte)'H' && b[p + 5] == (byte)' ') { p += 6; ok = true; }
        if (!ok) return false;

        // 4. path + template
        tlen = 0;
        if (p >= end || b[p] != (byte)'/') return false;
        int segStart = 0;
        bool segDigits = true;
        int segLen = 0;
        bool done = false;
        for (;;) {
            if (p >= end) return false;
            byte c = b[p];
            if (c == (byte)'/') {
                if (segLen > 0 && segDigits) {
                    tlen = segStart;
                    tb[tlen++] = (char)'{';
                    tb[tlen++] = (char)'i';
                    tb[tlen++] = (char)'d';
                    tb[tlen++] = (char)'}';
                }
                if (tlen == tb.Length) Array.Resize(ref tb, tb.Length * 2);
                tb[tlen++] = (char)'/';
                ++p;
                segStart = tlen;
                segDigits = true;
                segLen = 0;
            } else if (c == (byte)' ') {
                if (segLen > 0 && segDigits) {
                    tlen = segStart;
                    tb[tlen++] = (char)'{';
                    tb[tlen++] = (char)'i';
                    tb[tlen++] = (char)'d';
                    tb[tlen++] = (char)'}';
                }
                ++p;
                done = true;
                break;
            } else if (c == (byte)'?') {
                if (segLen > 0 && segDigits) {
                    tlen = segStart;
                    tb[tlen++] = (char)'{';
                    tb[tlen++] = (char)'i';
                    tb[tlen++] = (char)'d';
                    tb[tlen++] = (char)'}';
                }
                ++p;
                while (p < end && b[p] != (byte)' ') ++p;
                if (p >= end) return false;
                ++p;
                done = true;
                break;
            } else {
                if (!IsDigit(c) && !IsUpper(c) && !IsLower(c) && c != (byte)'_' && c != (byte)'-') return false;
                if (segLen == 0) segDigits = IsDigit(c);
                else if (segDigits && !IsDigit(c)) segDigits = false;
                ++segLen;
                if (tlen == tb.Length) Array.Resize(ref tb, tb.Length * 2);
                tb[tlen++] = (char)c;
                ++p;
            }
        }
        if (!done) return false;

        // 5. status: \d{3}<space>
        if (end - p < 4) return false;
        if (!IsDigit(b[p]) || !IsDigit(b[p + 1]) || !IsDigit(b[p + 2])) return false;
        if (b[p + 3] != (byte)' ') return false;
        statusClass = b[p] - (byte)'0';
        p += 4;

        // 6. size: \d+B<space>
        if (p >= end || !IsDigit(b[p])) return false;
        do { p++; } while (p < end && IsDigit(b[p]));
        if (p >= end || b[p] != (byte)'B') return false;
        p++;
        if (p >= end || b[p] != (byte)' ') return false;
        p++;

        // 7. latency: \d+.\d ms<space>
        int ls = p;
        long ip = 0;
        while (p < end && IsDigit(b[p])) { ip = ip * 10 + (b[p] - (byte)'0'); p++; }
        if (p == ls || p >= end || b[p] != (byte)'.') return false;
        p++;
        if (p >= end || !IsDigit(b[p])) return false;
        int frac = b[p] - (byte)'0';
        p++;
        if (end - p < 3 || b[p] != (byte)'m' || b[p + 1] != (byte)'s' || b[p + 2] != (byte)' ') return false;
        p += 3;
        latencyT = (int)(ip * 10 + frac);

        // 8. "..." then end of line
        if (p >= end || b[p] != (byte)'"') return false;
        p++;
        while (p < end && b[p] != (byte)'"') p++;
        if (p >= end) return false;
        p++;
        return p == end;
    }

    static int Pos(int pct, int nn) => (pct * nn + 99) / 100 - 1; // nearest-rank, 0-based

    static void Main(string[] args) {
        byte[] b = File.ReadAllBytes(args[0]);
        int n = b.Length;
        int p = 0;
        long lines = 0, malformed = 0;
        long[] statusCount = new long[10];
        var map = new Dictionary<string, Stats>();
        char[] tb = new char[1024];
        var outStream = new BufferedStream(Console.OpenStandardOutput());
        using (outStream) {
            while (p < n) {
                int nl = p;
                while (nl < n && b[nl] != (byte)'\n') nl++;
                int lineEnd = nl;
                ++lines;
                int tlen = 0;
                if (ParseLine(b, p, lineEnd, tb, ref tlen, out int sc, out int lat)) {
                    statusCount[sc]++;
                    string key = new string(tb, 0, tlen);
                    if (!map.TryGetValue(key, out var s)) {
                        s = new Stats();
                        map[key] = s;
                    }
                    s.Add(lat);
                } else {
                    ++malformed;
                }
                p = lineEnd + 1;
            }

            var wb = System.Text.Encoding.ASCII;
            void W(string s) { outStream.Write(wb.GetBytes(s), 0, wb.GetByteCount(s)); }
            void Wl(long v) { W(v.ToString()); outStream.WriteByte((byte)'\n'); }
            void WLat(int t) { W((t / 10).ToString()); outStream.WriteByte((byte)'.'); outStream.WriteByte((byte)('0' + t % 10)); }

            W("lines "); Wl(lines);
            W("malformed "); Wl(malformed);
            for (int d = 0; d < 10; d++) {
                if (statusCount[d] != 0) {
                    W("status ");
                    outStream.WriteByte((byte)('0' + d));
                    W("xx "); Wl(statusCount[d]);
                }
            }

            var paths = new List<KeyValuePair<string, Stats>>(map);
            paths.Sort((a, b) => {
                int c = b.Value.count.CompareTo(a.Value.count);
                if (c != 0) return c;
                return string.Compare(a.Key, b.Key, StringComparison.Ordinal);
            });
            int lim = Math.Min(paths.Count, 10);
            for (int i = 0; i < lim; i++) {
                var pe = paths[i];
                var s = pe.Value;
                s.lats.Sort();
                int nn = s.lats.Count;
                W("path "); W(pe.Key); outStream.WriteByte((byte)' ');
                W(s.count.ToString()); outStream.WriteByte((byte)' ');
                WLat(s.lats[Pos(50, nn)]); outStream.WriteByte((byte)' ');
                WLat(s.lats[Pos(95, nn)]); outStream.WriteByte((byte)' ');
                WLat(s.maxT); outStream.WriteByte((byte)'\n');
            }
            outStream.Flush();
        }
    }
}
