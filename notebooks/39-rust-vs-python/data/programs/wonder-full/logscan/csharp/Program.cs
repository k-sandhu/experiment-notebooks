using System;
using System.IO;
using System.Text;

class Program
{
    static byte[] d;
    static int n, i, pathS, pathE, statusDigit, latency;
    static readonly bool[] pathCharTab = MakeTab();
    static bool[] MakeTab()
    {
        var t = new bool[256];
        for (int c = 0; c < 256; c++)
            t[c] = (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || c == '_' || c == '/' || c == '-';
        return t;
    }
    static bool IsDigit(byte c) => c >= '0' && c <= '9';

    static bool ParseLine()
    {
        int i = Program.i; byte[] d = Program.d; int n = Program.n;
        bool Fail() { Program.i = i; return false; }
        if (i + 25 > n) return Fail();
        if (!(IsDigit(d[i]) && IsDigit(d[i+1]) && IsDigit(d[i+2]) && IsDigit(d[i+3]) && d[i+4] == '-' &&
              IsDigit(d[i+5]) && IsDigit(d[i+6]) && d[i+7] == '-' && IsDigit(d[i+8]) && IsDigit(d[i+9]) &&
              d[i+10] == 'T' && IsDigit(d[i+11]) && IsDigit(d[i+12]) && d[i+13] == ':' && IsDigit(d[i+14]) &&
              IsDigit(d[i+15]) && d[i+16] == ':' && IsDigit(d[i+17]) && IsDigit(d[i+18]) && d[i+19] == '.' &&
              IsDigit(d[i+20]) && IsDigit(d[i+21]) && IsDigit(d[i+22]) && d[i+23] == 'Z' && d[i+24] == ' ')) return Fail();
        i += 25;
        { int s = i; while (i < n && d[i] >= 'a' && d[i] <= 'z') i++; if (i == s) return Fail(); }
        if (i >= n || d[i] != '-') return Fail(); i++;
        { int s = i; while (i < n && IsDigit(d[i])) i++; if (i == s) return Fail(); }
        if (i >= n || d[i] != ' ') return Fail(); i++;
        if (i >= n) return Fail();
        switch (d[i])
        {
            case (byte)'G':
                if (i + 4 <= n && d[i+1] == 'E' && d[i+2] == 'T' && d[i+3] == ' ') i += 4; else return Fail(); break;
            case (byte)'D':
                if (i + 7 <= n && d[i+1] == 'E' && d[i+2] == 'L' && d[i+3] == 'E' && d[i+4] == 'T' && d[i+5] == 'E' && d[i+6] == ' ') i += 7; else return Fail(); break;
            case (byte)'P':
                if (i + 1 >= n) return Fail();
                if (d[i+1] == 'O') { if (i + 5 <= n && d[i+2] == 'S' && d[i+3] == 'T' && d[i+4] == ' ') i += 5; else return Fail(); }
                else if (d[i+1] == 'U') { if (i + 4 <= n && d[i+2] == 'T' && d[i+3] == ' ') i += 4; else return Fail(); }
                else if (d[i+1] == 'A') { if (i + 6 <= n && d[i+2] == 'T' && d[i+3] == 'C' && d[i+4] == 'H' && d[i+5] == ' ') i += 6; else return Fail(); }
                else return Fail();
                break;
            default: return Fail();
        }
        if (i >= n || d[i] != '/') return Fail();
        pathS = i; i++;
        while (i < n && pathCharTab[d[i]]) i++;
        pathE = i;
        if (i < n && d[i] == '?') { i++; while (i < n && d[i] != ' ' && d[i] != '\n') i++; }
        if (i >= n || d[i] != ' ') return Fail(); i++;
        if (i + 3 > n || !IsDigit(d[i]) || !IsDigit(d[i+1]) || !IsDigit(d[i+2])) return Fail();
        statusDigit = d[i] - '0'; i += 3;
        if (i >= n || d[i] != ' ') return Fail(); i++;
        { int s = i; while (i < n && IsDigit(d[i])) i++; if (i == s) return Fail(); }
        if (i >= n || d[i] != 'B') return Fail(); i++;
        if (i >= n || d[i] != ' ') return Fail(); i++;
        { int s = i; long v = 0; while (i < n && IsDigit(d[i])) { v = v * 10 + (d[i] - '0'); i++; } if (i == s) return Fail();
          if (i >= n || d[i] != '.') return Fail(); i++;
          if (i >= n || !IsDigit(d[i])) return Fail(); v = v * 10 + (d[i] - '0'); i++;
          latency = (int)v; }
        if (i + 2 > n || d[i] != 'm' || d[i+1] != 's') return Fail(); i += 2;
        if (i >= n || d[i] != ' ') return Fail(); i++;
        if (i >= n || d[i] != '"') return Fail(); i++;
        while (i < n && d[i] != '"' && d[i] != '\n') i++;
        if (i >= n || d[i] != '"') return Fail(); i++;
        if (i < n && d[i] != '\n') return Fail();
        Program.i = i; return true;
    }

    static ulong HashBytes(byte[] s, int len)
    {
        ulong h = 1469598103934665603UL;
        for (int k = 0; k < len; k++) { h ^= s[k]; h *= 1099511628211UL; }
        h ^= h >> 33; h *= 0xff51afd7ed558ccdUL; h ^= h >> 33; h *= 0xc4ceb9fe1a85ec53UL; h ^= h >> 33;
        return h;
    }

    static int CompareTemplates(byte[] arena, int offA, int lenA, int offB, int lenB)
    {
        int m = Math.Min(lenA, lenB);
        int c = arena.AsSpan(offA, m).SequenceCompareTo(arena.AsSpan(offB, m));
        if (c != 0) return c;
        return lenA - lenB;
    }

    static void Main(string[] args)
    {
        d = File.ReadAllBytes(args[0]);
        n = d.Length; i = 0;
        long lines = 0, malformed = 0;
        long[] statusCnt = new long[10];

        byte[] arena = new byte[1 << 16]; int arenaLen = 0;
        int[] offs = new int[1024], lens = new int[1024], counts = new int[1024];
        ulong[] hashes = new ulong[1024];
        int templates = 0;
        int tableSize = 1024; int[] table = new int[tableSize]; Array.Fill(table, -1); int mask = tableSize - 1;

        int est = n / 100 + 16;
        int[] lats = new int[est], ids = new int[est]; int pairs = 0;
        byte[] scratch = new byte[256];

        while (i < n)
        {
            lines++;
            if (ParseLine())
            {
                statusCnt[statusDigit]++;
                int pathLen = pathE - pathS;
                int need = pathLen * 3 + 8;
                if (scratch.Length < need) scratch = new byte[need];
                int sl = 0; int j = pathS;
                while (true)
                {
                    int segS = j; bool allDig = true;
                    while (j < pathE && d[j] != '/') { if (!IsDigit(d[j])) allDig = false; j++; }
                    if (j > segS && allDig) { scratch[sl++] = (byte)'{'; scratch[sl++] = (byte)'i'; scratch[sl++] = (byte)'d'; scratch[sl++] = (byte)'}'; }
                    else if (j > segS) { Array.Copy(d, segS, scratch, sl, j - segS); sl += j - segS; }
                    if (j >= pathE) break;
                    scratch[sl++] = (byte)'/'; j++;
                }
                ulong h = HashBytes(scratch, sl);
                int hidx = (int)h & mask; int id = -1;
                while (true)
                {
                    int t = table[hidx];
                    if (t == -1) break;
                    if (hashes[t] == h && lens[t] == sl && arena.AsSpan(offs[t], sl).SequenceEqual(scratch.AsSpan(0, sl))) { id = t; break; }
                    hidx = (hidx + 1) & mask;
                }
                if (id == -1)
                {
                    if ((templates + 1) * 10 > tableSize * 7)
                    {
                        int ns = tableSize * 2; int[] nt = new int[ns]; Array.Fill(nt, -1); int nm = ns - 1;
                        for (int t = 0; t < templates; t++) { int hh = (int)hashes[t] & nm; while (nt[hh] != -1) hh = (hh + 1) & nm; nt[hh] = t; }
                        table = nt; tableSize = ns; mask = nm;
                        hidx = (int)h & mask; while (table[hidx] != -1) hidx = (hidx + 1) & mask;
                    }
                    if (templates == offs.Length)
                    {
                        int nc = offs.Length * 2;
                        Array.Resize(ref offs, nc); Array.Resize(ref lens, nc); Array.Resize(ref counts, nc); Array.Resize(ref hashes, nc);
                    }
                    if (arenaLen + sl > arena.Length) Array.Resize(ref arena, Math.Max(arena.Length * 2, arenaLen + sl));
                    id = templates++;
                    table[hidx] = id;
                    offs[id] = arenaLen; Array.Copy(scratch, 0, arena, arenaLen, sl); arenaLen += sl;
                    lens[id] = sl; counts[id] = 0; hashes[id] = h;
                }
                counts[id]++;
                if (pairs == lats.Length) { int nc = lats.Length * 2; Array.Resize(ref lats, nc); Array.Resize(ref ids, nc); }
                lats[pairs] = latency; ids[pairs] = id; pairs++;
                if (i < n) i++;
            }
            else
            {
                malformed++;
                while (i < n && d[i] != '\n') i++;
                if (i < n) i++;
            }
        }
        d = null;

        int[] order = new int[templates];
        for (int k = 0; k < templates; k++) order[k] = k;
        byte[] ar = arena; int[] of = offs, ln = lens, ct = counts;
        Array.Sort(order, (a, b) =>
        {
            if (ct[a] != ct[b]) return ct[b].CompareTo(ct[a]);
            return CompareTemplates(ar, of[a], ln[a], of[b], ln[b]);
        });
        int K = Math.Min(templates, 10);
        int[][] tops = new int[K][];
        int[] slot = new int[templates]; Array.Fill(slot, -1);
        for (int k = 0; k < K; k++) { slot[order[k]] = k; tops[k] = new int[counts[order[k]]]; }
        int[] fill = new int[K];
        for (int q = 0; q < pairs; q++) { int s = slot[ids[q]]; if (s >= 0) tops[s][fill[s]++] = lats[q]; }
        for (int k = 0; k < K; k++) Array.Sort(tops[k]);

        var outSb = new StringBuilder(1024);
        outSb.Append("lines ").Append(lines).Append('\n');
        outSb.Append("malformed ").Append(malformed).Append('\n');
        for (int dig = 0; dig < 10; dig++) if (statusCnt[dig] > 0)
            outSb.Append("status ").Append(dig).Append("xx ").Append(statusCnt[dig]).Append('\n');
        for (int k = 0; k < K; k++)
        {
            int id = order[k]; int[] vec = tops[k]; long nn = vec.Length;
            int p50 = vec[(50 * nn + 99) / 100 - 1];
            int p95 = vec[(95 * nn + 99) / 100 - 1];
            int mx = vec[vec.Length - 1];
            outSb.Append("path ");
            outSb.Append(Encoding.ASCII.GetString(arena, offs[id], lens[id]));
            outSb.Append(' ').Append(counts[id]).Append(' ');
            AppendLat(outSb, p50); outSb.Append(' '); AppendLat(outSb, p95); outSb.Append(' '); AppendLat(outSb, mx); outSb.Append('\n');
        }
        Console.Out.Write(outSb.ToString());
    }
    static void AppendLat(StringBuilder sb, int v) { sb.Append(v / 10).Append('.').Append(v % 10); }
}
