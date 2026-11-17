using System.Text;

unsafe class Scan
{
    static byte[] arena = new byte[1 << 16];
    static int arenaLen;
    static int[] eOff = new int[256], eLen = new int[256], eCount = new int[256];
    static ulong[] eHash = new ulong[256];
    static int nEntries;
    static int[] table;
    static int tableMask;
    static int[] recTid = new int[1 << 16];
    static long[] recLat = new long[1 << 16];
    static int nRec;
    static byte[] tmpl = new byte[1024];

    static long lines, malformed;
    static readonly long[] statusCount = new long[10];

    static void GrowTable()
    {
        int cap = table == null ? 1024 : table.Length * 2;
        table = new int[cap];
        Array.Fill(table, -1);
        tableMask = cap - 1;
        for (int i = 0; i < nEntries; i++)
        {
            int h = (int)(eHash[i] & (ulong)tableMask);
            while (table[h] >= 0) h = (h + 1) & tableMask;
            table[h] = i;
        }
    }

    static int Lookup(byte[] t, int len)
    {
        ulong h = 0xcbf29ce484222325UL;
        for (int i = 0; i < len; i++) h = (h ^ t[i]) * 0x100000001b3UL;
        h ^= h >> 29;
        int slot = (int)(h & (ulong)tableMask);
        while (true)
        {
            int id = table[slot];
            if (id < 0) break;
            if (eHash[id] == h && eLen[id] == len &&
                new ReadOnlySpan<byte>(arena, eOff[id], len).SequenceEqual(new ReadOnlySpan<byte>(t, 0, len))) return id;
            slot = (slot + 1) & tableMask;
        }
        if (nEntries == eOff.Length)
        {
            int c = nEntries * 2;
            Array.Resize(ref eOff, c);
            Array.Resize(ref eLen, c);
            Array.Resize(ref eCount, c);
            Array.Resize(ref eHash, c);
        }
        if (arenaLen + len > arena.Length) Array.Resize(ref arena, Math.Max(arena.Length * 2, arenaLen + len));
        Buffer.BlockCopy(t, 0, arena, arenaLen, len);
        int nid = nEntries++;
        eOff[nid] = arenaLen;
        eLen[nid] = len;
        eCount[nid] = 0;
        eHash[nid] = h;
        arenaLen += len;
        if (nEntries * 2 > table.Length) GrowTable();
        else table[slot] = nid;
        return nid;
    }

    static bool Dig(byte c) => (uint)(c - '0') < 10u;

    static bool PathChar(byte c) =>
        (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') || c == '_' || c == '/' || c == '-';

    static bool Match(byte* p, string w)
    {
        for (int i = 0; i < w.Length; i++) if (p[i] != w[i]) return false;
        return true;
    }

    static void ProcessLine(byte* s, byte* e)
    {
        lines++;
        byte* p = s;
        if (e - s < 40) { malformed++; return; }
        if (!(Dig(p[0]) && Dig(p[1]) && Dig(p[2]) && Dig(p[3]) && p[4] == '-' && Dig(p[5]) &&
              Dig(p[6]) && p[7] == '-' && Dig(p[8]) && Dig(p[9]) && p[10] == 'T' && Dig(p[11]) &&
              Dig(p[12]) && p[13] == ':' && Dig(p[14]) && Dig(p[15]) && p[16] == ':' && Dig(p[17]) &&
              Dig(p[18]) && p[19] == '.' && Dig(p[20]) && Dig(p[21]) && Dig(p[22]) && p[23] == 'Z' &&
              p[24] == ' ')) { malformed++; return; }
        p += 25;
        byte* q = p;
        while (q < e && *q >= 'a' && *q <= 'z') q++;
        if (q == p || q >= e || *q != '-') { malformed++; return; }
        q++;
        p = q;
        while (q < e && Dig(*q)) q++;
        if (q == p || q >= e || *q != ' ') { malformed++; return; }
        p = q + 1;
        if (e - p < 8) { malformed++; return; }
        byte m = *p;
        if (m == (byte)'G' && Match(p, "GET ")) p += 4;
        else if (m == (byte)'P' && Match(p, "PUT ")) p += 4;
        else if (m == (byte)'P' && Match(p, "POST ")) p += 5;
        else if (m == (byte)'P' && Match(p, "PATCH ")) p += 6;
        else if (m == (byte)'D' && Match(p, "DELETE ")) p += 7;
        else { malformed++; return; }
        if (p >= e || *p != '/') { malformed++; return; }
        byte* pathStart = p;
        p++;
        while (p < e && PathChar(*p)) p++;
        byte* pathEnd = p;
        if (p >= e) { malformed++; return; }
        if (*p == '?')
        {
            p++;
            while (p < e && *p != ' ') p++;
            if (p >= e) { malformed++; return; }
        }
        if (*p != ' ') { malformed++; return; }
        p++;
        if (e - p < 5 || !(Dig(p[0]) && Dig(p[1]) && Dig(p[2]) && p[3] == ' ')) { malformed++; return; }
        int cls = p[0] - '0';
        p += 4;
        q = p;
        while (q < e && Dig(*q)) q++;
        if (q == p || e - q < 2 || q[0] != 'B' || q[1] != ' ') { malformed++; return; }
        p = q + 2;
        long lat = 0;
        q = p;
        while (q < e && Dig(*q)) { lat = lat * 10 + (*q - '0'); q++; }
        if (q == p || e - q < 6 || q[0] != '.' || !Dig(q[1]) || q[2] != 'm' || q[3] != 's' || q[4] != ' ' || q[5] != '"')
        { malformed++; return; }
        lat = lat * 10 + (q[1] - '0');
        p = q + 6;
        byte* last = e - 1;
        if (p > last || *last != '"') { malformed++; return; }
        if (new ReadOnlySpan<byte>(p, (int)(last - p)).IndexOf((byte)'"') >= 0) { malformed++; return; }

        statusCount[cls]++;
        int plen = (int)(pathEnd - pathStart);
        if (tmpl.Length < plen * 4 + 8) tmpl = new byte[plen * 4 + 8];
        byte[] t = tmpl;
        int o = 0;
        t[o++] = (byte)'/';
        int segStart = o;
        bool allDigits = true;
        for (byte* c = pathStart + 1; ; c++)
        {
            if (c == pathEnd || *c == '/')
            {
                if (allDigits && o > segStart)
                {
                    o = segStart;
                    t[o++] = (byte)'{'; t[o++] = (byte)'i'; t[o++] = (byte)'d'; t[o++] = (byte)'}';
                }
                if (c == pathEnd) break;
                t[o++] = (byte)'/';
                segStart = o;
                allDigits = true;
            }
            else
            {
                byte ch = *c;
                t[o++] = ch;
                allDigits &= Dig(ch);
            }
        }
        int id = Lookup(t, o);
        eCount[id]++;
        if (nRec == recTid.Length)
        {
            Array.Resize(ref recTid, nRec * 2);
            Array.Resize(ref recLat, nRec * 2);
        }
        recTid[nRec] = id;
        recLat[nRec++] = lat;
    }

    static void FmtLat(StringBuilder o, long v)
    {
        o.Append(v / 10).Append('.').Append((char)('0' + v % 10));
    }

    static int CmpEntries(int a, int b)
    {
        if (eCount[a] != eCount[b]) return eCount[a] > eCount[b] ? -1 : 1;
        return new ReadOnlySpan<byte>(arena, eOff[a], eLen[a]).SequenceCompareTo(new ReadOnlySpan<byte>(arena, eOff[b], eLen[b]));
    }

    static void Main(string[] args)
    {
        GrowTable();
        int cap = 1 << 22, have = 0;
        byte[] buf = new byte[cap];
        using (var fs = new FileStream(args[0], FileMode.Open, FileAccess.Read, FileShare.Read, 1, FileOptions.SequentialScan))
        {
            while (true)
            {
                int n = fs.Read(buf, have, cap - have);
                bool eof = n <= 0;
                if (!eof) have += n;
                int curOff = 0;
                fixed (byte* basePtr = buf)
                {
                    byte* cur = basePtr;
                    byte* end = basePtr + have;
                    while (cur < end)
                    {
                        int idx = new ReadOnlySpan<byte>(cur, (int)(end - cur)).IndexOf((byte)'\n');
                        if (idx < 0) break;
                        ProcessLine(cur, cur + idx);
                        cur += idx + 1;
                    }
                    curOff = (int)(cur - basePtr);
                    if (eof && curOff < have) ProcessLine(cur, end);
                }
                if (eof) break;
                int rest = have - curOff;
                if (curOff > 0) Buffer.BlockCopy(buf, curOff, buf, 0, rest);
                have = rest;
                if (have == cap)
                {
                    cap *= 2;
                    Array.Resize(ref buf, cap);
                }
            }
        }

        var sb = new StringBuilder();
        sb.Append("lines ").Append(lines).Append('\n');
        sb.Append("malformed ").Append(malformed).Append('\n');
        for (int c = 0; c < 10; c++)
            if (statusCount[c] != 0) sb.Append("status ").Append((char)('0' + c)).Append("xx ").Append(statusCount[c]).Append('\n');
        int[] order = new int[nEntries];
        for (int i = 0; i < nEntries; i++) order[i] = i;
        Array.Sort(order, CmpEntries);
        int top = Math.Min(10, nEntries);
        long[] v = new long[0];
        for (int k = 0; k < top; k++)
        {
            int id = order[k];
            int cnt = eCount[id];
            if (v.Length < cnt) v = new long[cnt];
            int j = 0;
            long mx = 0;
            for (int i = 0; i < nRec; i++)
            {
                if (recTid[i] == id)
                {
                    long x = recLat[i];
                    v[j++] = x;
                    if (x > mx) mx = x;
                }
            }
            int r50 = (int)((50L * cnt + 99) / 100), r95 = (int)((95L * cnt + 99) / 100);
            long p50 = -1, p95 = -1;
            if (mx < (1 << 22))
            {
                int[] hist = new int[(int)mx + 1];
                for (int i = 0; i < cnt; i++) hist[(int)v[i]]++;
                long acc = 0;
                for (int b = 0; b <= mx; b++)
                {
                    acc += hist[b];
                    if (p50 < 0 && acc >= r50) p50 = b;
                    if (acc >= r95) { p95 = b; break; }
                }
            }
            else
            {
                Array.Sort(v, 0, cnt);
                p50 = v[r50 - 1];
                p95 = v[r95 - 1];
            }
            sb.Append("path ").Append(Encoding.ASCII.GetString(arena, eOff[id], eLen[id]));
            sb.Append(' ').Append(cnt).Append(' ');
            FmtLat(sb, p50);
            sb.Append(' ');
            FmtLat(sb, p95);
            sb.Append(' ');
            FmtLat(sb, mx);
            sb.Append('\n');
        }
        using var stdout = Console.OpenStandardOutput();
        var bytes = Encoding.ASCII.GetBytes(sb.ToString());
        stdout.Write(bytes, 0, bytes.Length);
        stdout.Flush();
    }
}
