// Log scan: reads the file in large chunks, matches each line with a hand-written
// pointer-based parser and interns path templates in an open-addressing hash table.
using System.Runtime.CompilerServices;
using System.Text;

static unsafe class Program
{
    const byte C_DIGIT = 1, C_LOWER = 2, C_PATH = 4;
    static readonly byte[] CTArr = BuildTable();

    static byte[] BuildTable()
    {
        var t = new byte[256];
        for (int c = '0'; c <= '9'; c++) t[c] |= C_DIGIT | C_PATH;
        for (int c = 'a'; c <= 'z'; c++) t[c] |= C_LOWER | C_PATH;
        for (int c = 'A'; c <= 'Z'; c++) t[c] |= C_PATH;
        t['_'] |= C_PATH;
        t['-'] |= C_PATH;
        t['/'] |= C_PATH;
        return t;
    }

    // Template table
    static byte[] arena = new byte[1 << 16];
    static int arenaLen;
    static int[] tOff = new int[256], tLen = new int[256], tCount = new int[256];
    static int nTemplates;
    static int[] slotId = new int[1024]; // id + 1, 0 = empty
    static uint[] slotHash = new uint[1024];
    static int mask = 1023;

    // Per well-formed line
    static int[] ids = new int[1 << 20];
    static long[] lats = new long[1 << 20];
    static int nGood;

    static long lines, malformed;
    static readonly long[] status = new long[10];

    static byte[] tbuf = new byte[4096];

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    static bool IsDigit(byte c) => (uint)(c - '0') < 10;

    static int Intern(byte* key, int len, uint h)
    {
        var keySpan = new ReadOnlySpan<byte>(key, len);
        int i = (int)h & mask;
        for (;;)
        {
            int s = slotId[i];
            if (s == 0) break;
            if (slotHash[i] == h)
            {
                int id = s - 1;
                if (tLen[id] == len && keySpan.SequenceEqual(new ReadOnlySpan<byte>(arena, tOff[id], len)))
                {
                    tCount[id]++;
                    return id;
                }
            }
            i = (i + 1) & mask;
        }
        int nid = nTemplates++;
        if (nid == tOff.Length)
        {
            Array.Resize(ref tOff, nid * 2);
            Array.Resize(ref tLen, nid * 2);
            Array.Resize(ref tCount, nid * 2);
        }
        if (arenaLen + len > arena.Length) Array.Resize(ref arena, Math.Max(arena.Length * 2, arenaLen + len));
        keySpan.CopyTo(arena.AsSpan(arenaLen));
        tOff[nid] = arenaLen;
        tLen[nid] = len;
        tCount[nid] = 1;
        arenaLen += len;
        slotId[i] = nid + 1;
        slotHash[i] = h;
        if (nTemplates * 2 > slotId.Length) Grow();
        return nid;
    }

    static void Grow()
    {
        int[] oldId = slotId;
        uint[] oldHash = slotHash;
        slotId = new int[oldId.Length * 2];
        slotHash = new uint[oldId.Length * 2];
        mask = slotId.Length - 1;
        for (int j = 0; j < oldId.Length; j++)
        {
            if (oldId[j] == 0) continue;
            int i = (int)oldHash[j] & mask;
            while (slotId[i] != 0) i = (i + 1) & mask;
            slotId[i] = oldId[j];
            slotHash[i] = oldHash[j];
        }
    }

    // Parses the line starting at p (terminated by '\n'). Returns the start of the next line
    // if well-formed, otherwise null; failPos receives a position inside the line. lim bounds the buffer.
    static byte* ParseLine(byte* p, byte* lim, byte* ct, out byte* failPos)
    {
        failPos = p;
        if (!(IsDigit(p[0]) && IsDigit(p[1]) && IsDigit(p[2]) && IsDigit(p[3]) && p[4] == '-' && IsDigit(p[5]) &&
              IsDigit(p[6]) && p[7] == '-' && IsDigit(p[8]) && IsDigit(p[9]) && p[10] == 'T' && IsDigit(p[11]) &&
              IsDigit(p[12]) && p[13] == ':' && IsDigit(p[14]) && IsDigit(p[15]) && p[16] == ':' && IsDigit(p[17]) &&
              IsDigit(p[18]) && p[19] == '.' && IsDigit(p[20]) && IsDigit(p[21]) && IsDigit(p[22]) && p[23] == 'Z' &&
              p[24] == ' '))
            return null;
        p += 25;
        // Host: [a-z]+-\d+
        if ((ct[*p] & C_LOWER) == 0) goto Fail;
        do p++; while ((ct[*p] & C_LOWER) != 0);
        if (*p != '-') goto Fail;
        p++;
        if (!IsDigit(*p)) goto Fail;
        do p++; while (IsDigit(*p));
        if (*p != ' ') goto Fail;
        p++;
        // Method
        switch (*p)
        {
            case (byte)'G':
                if (p[1] != 'E' || p[2] != 'T') goto Fail;
                p += 3;
                break;
            case (byte)'P':
                if (p[1] == 'U' && p[2] == 'T') p += 3;
                else if (p[1] == 'O' && p[2] == 'S' && p[3] == 'T') p += 4;
                else if (p[1] == 'A' && p[2] == 'T' && p[3] == 'C' && p[4] == 'H') p += 5;
                else goto Fail;
                break;
            case (byte)'D':
                if (p[1] != 'E' || p[2] != 'L' || p[3] != 'E' || p[4] != 'T' || p[5] != 'E') goto Fail;
                p += 6;
                break;
            default:
                goto Fail;
        }
        if (*p != ' ') goto Fail;
        p++;
        // Path, building the template as we go.
        if (*p != '/') goto Fail;
        p++;
        byte[] t = tbuf;
        int o = 0;
        t[o++] = (byte)'/';
        byte c;
        for (;;)
        {
            byte* seg = p;
            bool allDigit = true;
            while (((ct[c = *p] & C_PATH) != 0) && c != '/')
            {
                allDigit &= IsDigit(c);
                p++;
            }
            int n = (int)(p - seg);
            if (o + n + 13 > t.Length)
            {
                Array.Resize(ref tbuf, (o + n + 13) * 2);
                t = tbuf;
            }
            if (n != 0 && allDigit)
            {
                t[o] = (byte)'{';
                t[o + 1] = (byte)'i';
                t[o + 2] = (byte)'d';
                t[o + 3] = (byte)'}';
                o += 4;
            }
            else
            {
                new ReadOnlySpan<byte>(seg, n).CopyTo(t.AsSpan(o));
                o += n;
            }
            if (c != '/') break;
            t[o++] = (byte)'/';
            p++;
        }
        if (c == '?')
        {
            do p++; while (*p != ' ' && *p != '\n');
        }
        if (*p != ' ') goto Fail;
        p++;
        // Status
        if (!(IsDigit(p[0]) && IsDigit(p[1]) && IsDigit(p[2]) && p[3] == ' ')) goto Fail;
        int cls = p[0] - '0';
        p += 4;
        // Size
        if (!IsDigit(*p)) goto Fail;
        do p++; while (IsDigit(*p));
        if (p[0] != 'B' || p[1] != ' ') goto Fail;
        p += 2;
        // Latency
        if (!IsDigit(*p)) goto Fail;
        long lat = 0;
        do lat = lat * 10 + (*p++ - '0'); while (IsDigit(*p));
        if (p[0] != '.' || !IsDigit(p[1]) || p[2] != 'm' || p[3] != 's' || p[4] != ' ' || p[5] != '"') goto Fail;
        lat = lat * 10 + (p[1] - '0');
        p += 6;
        // User agent
        {
            int q = new ReadOnlySpan<byte>(p, (int)(lim - p)).IndexOfAny((byte)'"', (byte)'\n');
            p += q;
        }
        if (*p != '"' || p[1] != '\n') goto Fail;

        int id;
        fixed (byte* tp = t)
        {
            // Hash 8 bytes at a time; tbuf always has at least 8 bytes of slack after o.
            ulong hh = 0x9E3779B97F4A7C15ul ^ (ulong)o;
            int i = 0;
            for (; i + 8 <= o; i += 8)
            {
                hh = (hh ^ *(ulong*)(tp + i)) * 0xFF51AFD7ED558CCDul;
                hh ^= hh >> 29;
            }
            if (i < o)
            {
                ulong w = *(ulong*)(tp + i) & (ulong.MaxValue >> (64 - 8 * (o - i)));
                hh = (hh ^ w) * 0xFF51AFD7ED558CCDul;
                hh ^= hh >> 29;
            }
            hh *= 0xC4CEB9FE1A85EC53ul;
            id = Intern(tp, o, (uint)(hh ^ (hh >> 32)));
        }
        status[cls]++;
        if (nGood == ids.Length)
        {
            Array.Resize(ref ids, nGood * 2);
            Array.Resize(ref lats, nGood * 2);
        }
        ids[nGood] = id;
        lats[nGood] = lat;
        nGood++;
        return p + 2;

    Fail:
        failPos = p;
        return null;
    }

    // Processes all lines in [buf, lastNl]; returns the start of the unprocessed tail.
    static byte* ProcessLines(byte* buf, byte* lastNl, byte* ct)
    {
        byte* p = buf;
        long nLines = 0, nBad = 0;
        while (p <= lastNl)
        {
            nLines++;
            byte* r = ParseLine(p, lastNl + 1, ct, out byte* fail);
            if (r != null)
            {
                p = r;
            }
            else
            {
                nBad++;
                int q = new ReadOnlySpan<byte>(fail, (int)(lastNl - fail) + 1).IndexOf((byte)'\n');
                p = fail + q + 1;
            }
        }
        lines += nLines;
        malformed += nBad;
        return p;
    }

    static int CompareTemplates(int a, int b)
    {
        if (tCount[a] != tCount[b]) return tCount[a] > tCount[b] ? -1 : 1;
        return new ReadOnlySpan<byte>(arena, tOff[a], tLen[a]).SequenceCompareTo(new ReadOnlySpan<byte>(arena, tOff[b], tLen[b]));
    }

    // Quickselect: places the k-th smallest at a[k], partitioned around it.
    static void Select(long[] a, int lo, int hi, int k)
    {
        while (hi > lo)
        {
            int mid = (lo + hi) >>> 1;
            if (a[mid] < a[lo]) (a[mid], a[lo]) = (a[lo], a[mid]);
            if (a[hi] < a[lo]) (a[hi], a[lo]) = (a[lo], a[hi]);
            if (a[hi] < a[mid]) (a[hi], a[mid]) = (a[mid], a[hi]);
            long pivot = a[mid];
            int i = lo, j = hi;
            while (i <= j)
            {
                while (a[i] < pivot) i++;
                while (a[j] > pivot) j--;
                if (i <= j)
                {
                    (a[i], a[j]) = (a[j], a[i]);
                    i++;
                    j--;
                }
            }
            if (k <= j) hi = j;
            else if (k >= i) lo = i;
            else return;
        }
    }

    static void FmtLat(StringBuilder sb, long v) => sb.Append(v / 10).Append('.').Append((char)('0' + v % 10));

    static void Main(string[] args)
    {
        int cap = 1 << 22;
        byte[] buf = new byte[cap + 8];
        int have = 0;
        using (var fs = new FileStream(args[0], FileMode.Open, FileAccess.Read, FileShare.Read, 1, FileOptions.SequentialScan))
        fixed (byte* ct = CTArr)
        {
            for (;;)
            {
                int n = fs.Read(buf, have, cap - have);
                have += n;
                if (have == 0) break;
                int lastNl = buf.AsSpan(0, have).LastIndexOf((byte)'\n');
                if (lastNl < 0)
                {
                    if (n == 0)
                    {
                        buf[have] = (byte)'\n';
                        lastNl = have;
                        have++;
                    }
                    else
                    {
                        if (have < cap) continue;
                        cap *= 2;
                        Array.Resize(ref buf, cap + 8);
                        continue;
                    }
                }
                int p;
                fixed (byte* bp = buf) p = (int)(ProcessLines(bp, bp + lastNl, ct) - bp);
                int rest = have - p;
                Buffer.BlockCopy(buf, p, buf, 0, rest);
                have = rest;
                if (n == 0 && have == 0) break;
            }
        }

        int[] top = new int[10];
        int nTop = 0;
        for (int id = 0; id < nTemplates; id++)
        {
            if (nTop == 10 && CompareTemplates(id, top[9]) >= 0) continue;
            int pos = nTop < 10 ? nTop++ : 9;
            while (pos > 0 && CompareTemplates(id, top[pos - 1]) < 0)
            {
                top[pos] = top[pos - 1];
                pos--;
            }
            top[pos] = id;
        }

        int[] rank = new int[nTemplates];
        Array.Fill(rank, -1);
        long[][] buckets = new long[nTop][];
        int[] fill = new int[nTop];
        for (int r = 0; r < nTop; r++)
        {
            rank[top[r]] = r;
            buckets[r] = new long[tCount[top[r]]];
        }
        for (int i = 0; i < nGood; i++)
        {
            int r = rank[ids[i]];
            if (r >= 0) buckets[r][fill[r]++] = lats[i];
        }

        var sb = new StringBuilder(1024);
        sb.Append("lines ").Append(lines).Append('\n');
        sb.Append("malformed ").Append(malformed).Append('\n');
        for (int c = 0; c < 10; c++)
            if (status[c] != 0) sb.Append("status ").Append(c).Append("xx ").Append(status[c]).Append('\n');
        for (int r = 0; r < nTop; r++)
        {
            long[] v = buckets[r];
            int n = v.Length;
            int k50 = (int)((50L * n + 99) / 100 - 1), k95 = (int)((95L * n + 99) / 100 - 1);
            Select(v, 0, n - 1, k50);
            long p50 = v[k50];
            Select(v, k50, n - 1, k95);
            long p95 = v[k95];
            long mx = p95;
            for (int i = k95 + 1; i < n; i++) if (v[i] > mx) mx = v[i];
            int id = top[r];
            sb.Append("path ").Append(Encoding.Latin1.GetString(arena, tOff[id], tLen[id])).Append(' ').Append(n).Append(' ');
            FmtLat(sb, p50);
            sb.Append(' ');
            FmtLat(sb, p95);
            sb.Append(' ');
            FmtLat(sb, mx);
            sb.Append('\n');
        }
        using var stdout = Console.OpenStandardOutput();
        stdout.Write(Encoding.Latin1.GetBytes(sb.ToString()));
    }
}
