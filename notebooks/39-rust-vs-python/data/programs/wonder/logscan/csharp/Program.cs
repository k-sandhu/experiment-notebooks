using System;
using System.Collections.Generic;
using System.IO;
using System.Text;

sealed class Entry
{
    public byte[] Key;
    public int[] Lats = new int[16];
    public int Size;
    public int Mx;
    public void Add(int v)
    {
        if (Size == Lats.Length) Array.Resize(ref Lats, Lats.Length * 2);
        Lats[Size++] = v;
        if (v > Mx) Mx = v;
    }
}

static class Program
{
    static bool IsDig(byte c) => (uint)(c - '0') <= 9;
    static bool IsLow(byte c) => (uint)(c - 'a') <= 25;
    static bool IsPathCh(byte c) => (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') || c == '_' || c == '/' || c == '-';

    static int Main(string[] args)
    {
        if (args.Length < 1) return 1;
        byte[] data = File.ReadAllBytes(args[0]);
        long total = 0, malformed = 0;
        long[] statusCnt = new long[10];

        var entries = new List<Entry>(1024);
        int tcap = 1024;
        int[] slots = new int[tcap];
        int usedSlots = 0;
        byte[] tmp = new byte[256];

        int n = data.Length;
        int pos = 0;
        while (pos < n)
        {
            int lineStart = pos;
            int nl = Array.IndexOf(data, (byte)'\n', pos);
            int lineEnd;
            if (nl >= 0) { lineEnd = nl; pos = nl + 1; }
            else { lineEnd = n; pos = n; }
            total++;
            int ln = lineEnd - lineStart;
            int b = lineStart;
            bool ok = true;
            int statusClass = 0;
            int latency = 0;
            int pathStart = 0, pathEnd = 0;

            if (ln < 25) ok = false;
            else if (!(IsDig(data[b]) && IsDig(data[b+1]) && IsDig(data[b+2]) && IsDig(data[b+3]) && data[b+4]=='-' && IsDig(data[b+5]) && IsDig(data[b+6]) && data[b+7]=='-' && IsDig(data[b+8]) && IsDig(data[b+9]) && data[b+10]=='T' && IsDig(data[b+11]) && IsDig(data[b+12]) && data[b+13]==':' && IsDig(data[b+14]) && IsDig(data[b+15]) && data[b+16]==':' && IsDig(data[b+17]) && IsDig(data[b+18]) && data[b+19]=='.' && IsDig(data[b+20]) && IsDig(data[b+21]) && IsDig(data[b+22]) && data[b+23]=='Z' && data[b+24]==' ')) ok = false;
            else
            {
                int i = 25;
                int st = i;
                while (i < ln && IsLow(data[b+i])) i++;
                if (i == st) ok = false;
                else if (i >= ln || data[b+i] != '-') ok = false;
                else
                {
                    i++; st = i;
                    while (i < ln && IsDig(data[b+i])) i++;
                    if (i == st || i >= ln || data[b+i] != ' ') ok = false;
                    else
                    {
                        i++;
                        int rem = ln - i;
                        if (rem >= 4 && data[b+i]=='G' && data[b+i+1]=='E' && data[b+i+2]=='T' && data[b+i+3]==' ') i += 4;
                        else if (rem >= 4 && data[b+i]=='P' && data[b+i+1]=='U' && data[b+i+2]=='T' && data[b+i+3]==' ') i += 4;
                        else if (rem >= 5 && data[b+i]=='P' && data[b+i+1]=='O' && data[b+i+2]=='S' && data[b+i+3]=='T' && data[b+i+4]==' ') i += 5;
                        else if (rem >= 6 && data[b+i]=='P' && data[b+i+1]=='A' && data[b+i+2]=='T' && data[b+i+3]=='C' && data[b+i+4]=='H' && data[b+i+5]==' ') i += 6;
                        else if (rem >= 7 && data[b+i]=='D' && data[b+i+1]=='E' && data[b+i+2]=='L' && data[b+i+3]=='E' && data[b+i+4]=='T' && data[b+i+5]=='E' && data[b+i+6]==' ') i += 7;
                        else ok = false;
                        if (ok)
                        {
                            if (i >= ln || data[b+i] != '/') ok = false;
                            else
                            {
                                pathStart = i;
                                while (i < ln && data[b+i] != ' ' && data[b+i] != '?')
                                {
                                    if (!IsPathCh(data[b+i])) { ok = false; break; }
                                    i++;
                                }
                                if (ok)
                                {
                                    pathEnd = i;
                                    if (i < ln && data[b+i] == '?')
                                    {
                                        i++;
                                        while (i < ln && data[b+i] != ' ') i++;
                                    }
                                    if (i >= ln || data[b+i] != ' ') ok = false;
                                    else
                                    {
                                        i++;
                                        if (i + 4 > ln || !IsDig(data[b+i]) || !IsDig(data[b+i+1]) || !IsDig(data[b+i+2]) || data[b+i+3] != ' ') ok = false;
                                        else
                                        {
                                            statusClass = data[b+i] - '0';
                                            i += 4;
                                            st = i;
                                            while (i < ln && IsDig(data[b+i])) i++;
                                            if (i == st || i >= ln || data[b+i] != 'B') ok = false;
                                            else
                                            {
                                                i++;
                                                if (i >= ln || data[b+i] != ' ') ok = false;
                                                else
                                                {
                                                    i++;
                                                    st = i; int v = 0;
                                                    while (i < ln && IsDig(data[b+i])) { v = v * 10 + (data[b+i] - '0'); i++; }
                                                    if (i == st || i >= ln || data[b+i] != '.') ok = false;
                                                    else
                                                    {
                                                        i++;
                                                        if (i >= ln || !IsDig(data[b+i])) ok = false;
                                                        else
                                                        {
                                                            v = v * 10 + (data[b+i] - '0'); i++; latency = v;
                                                            if (i + 2 > ln || data[b+i] != 'm' || data[b+i+1] != 's') ok = false;
                                                            else
                                                            {
                                                                i += 2;
                                                                if (i >= ln || data[b+i] != ' ') ok = false;
                                                                else
                                                                {
                                                                    i++;
                                                                    if (i >= ln || data[b+i] != '"') ok = false;
                                                                    else if (data[b+ln-1] != '"' || i + 1 >= ln) ok = false;
                                                                    else if (Array.IndexOf(data, (byte)'"', b+i+1, (ln-1)-(i+1)) >= 0) ok = false;
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            if (!ok) { malformed++; continue; }
            statusCnt[statusClass]++;

            if (tmp.Length < (pathEnd - pathStart) + 16) tmp = new byte[(pathEnd - pathStart) + 64];
            int tlen = 0;
            int p = pathStart;
            while (true)
            {
                int segStart = p;
                while (p < pathEnd && data[b+p] != '/') p++;
                int segLen = p - segStart;
                bool allDig = segLen > 0;
                if (allDig) for (int k = segStart; k < p; k++) if (!IsDig(data[b+k])) { allDig = false; break; }
                int need = tlen + (allDig ? 4 : segLen) + 1;
                if (need > tmp.Length) Array.Resize(ref tmp, tmp.Length * 2 + 32);
                if (allDig) { tmp[tlen++] = (byte)'{'; tmp[tlen++] = (byte)'i'; tmp[tlen++] = (byte)'d'; tmp[tlen++] = (byte)'}'; }
                else if (segLen > 0) { Array.Copy(data, b + segStart, tmp, tlen, segLen); tlen += segLen; }
                if (p >= pathEnd) break;
                tmp[tlen++] = (byte)'/';
                p++;
            }

            ulong h = 1469598103934665603UL;
            for (int k = 0; k < tlen; k++) { h ^= tmp[k]; h *= 1099511628211UL; }

            if ((usedSlots + 1) * 10 > tcap * 7)
            {
                int ncap = tcap * 2;
                int[] nslots = new int[ncap];
                int mask2 = ncap - 1;
                for (int ei = 0; ei < entries.Count; ei++)
                {
                    Entry en = entries[ei];
                    ulong hh = 1469598103934665603UL;
                    foreach (byte ch in en.Key) { hh ^= ch; hh *= 1099511628211UL; }
                    int idx2 = (int)(hh & (ulong)mask2);
                    while (nslots[idx2] != 0) idx2 = (idx2 + 1) & mask2;
                    nslots[idx2] = ei + 1;
                }
                slots = nslots; tcap = ncap;
            }
            int mask = tcap - 1;
            int idx = (int)(h & (ulong)mask);
            Entry found = null;
            while (true)
            {
                int v = slots[idx];
                if (v == 0) break;
                Entry en = entries[v - 1];
                if (en.Key.Length == tlen)
                {
                    bool eq = true;
                    for (int k = 0; k < tlen; k++) if (en.Key[k] != tmp[k]) { eq = false; break; }
                    if (eq) { found = en; break; }
                }
                idx = (idx + 1) & mask;
            }
            if (found != null) found.Add(latency);
            else
            {
                var en = new Entry();
                en.Key = new byte[tlen];
                Array.Copy(tmp, en.Key, tlen);
                en.Add(latency);
                entries.Add(en);
                slots[idx] = entries.Count;
                usedSlots++;
            }
        }

        entries.Sort((x, y) =>
        {
            if (x.Size != y.Size) return y.Size.CompareTo(x.Size);
            int ml = Math.Min(x.Key.Length, y.Key.Length);
            for (int k = 0; k < ml; k++) if (x.Key[k] != y.Key[k]) return x.Key[k].CompareTo(y.Key[k]);
            return x.Key.Length.CompareTo(y.Key.Length);
        });
        int top = Math.Min(10, entries.Count);
        var sb = new StringBuilder(4096);
        sb.Append("lines ").Append(total).Append('\n');
        sb.Append("malformed ").Append(malformed).Append('\n');
        for (int c = 0; c < 10; c++) if (statusCnt[c] > 0) sb.Append("status ").Append((char)('0' + c)).Append("xx ").Append(statusCnt[c]).Append('\n');
        for (int ti = 0; ti < top; ti++)
        {
            Entry en = entries[ti];
            Array.Sort(en.Lats, 0, en.Size);
            long nn = en.Size;
            long r50 = (50 * nn + 99) / 100;
            long r95 = (95 * nn + 99) / 100;
            int p50 = en.Lats[r50 - 1];
            int p95 = en.Lats[r95 - 1];
            sb.Append("path ");
            foreach (byte ch in en.Key) sb.Append((char)ch);
            sb.Append(' ').Append(nn).Append(' ');
            sb.Append(p50 / 10).Append('.').Append(p50 % 10).Append(' ');
            sb.Append(p95 / 10).Append('.').Append(p95 % 10).Append(' ');
            sb.Append(en.Mx / 10).Append('.').Append(en.Mx % 10).Append('\n');
        }
        Console.Out.Write(sb.ToString());
        return 0;
    }
}
