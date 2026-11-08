using System;
using System.Collections.Generic;
using System.IO;
using System.Text;

sealed class IntList
{
    public int[] a = new int[8];
    public int n;
    public void Add(int v)
    {
        if (n == a.Length) Array.Resize(ref a, n << 1);
        a[n++] = v;
    }
}

sealed class Table
{
    public ulong[] hash;
    public int[] id;
    public byte[][] keys;
    public int mask;
    public int size;

    public Table(int cap)
    {
        int c = 16;
        while (c < cap) c <<= 1;
        hash = new ulong[c];
        id = new int[c];
        keys = new byte[c][];
        Array.Fill(id, -1);
        mask = c - 1;
    }

    void Resize()
    {
        int nc = id.Length << 1;
        var nh = new ulong[nc];
        var ni = new int[nc];
        var nk = new byte[nc][];
        Array.Fill(ni, -1);
        int nm = nc - 1;
        for (int i = 0; i < id.Length; i++)
        {
            if (id[i] >= 0)
            {
                int p = (int)hash[i] & nm;
                while (ni[p] >= 0) p = (p + 1) & nm;
                ni[p] = id[i];
                nh[p] = hash[i];
                nk[p] = keys[i];
            }
        }
        hash = nh; id = ni; keys = nk; mask = nm;
    }

    public int Find(byte[] s, int len, ulong h)
    {
        int p = (int)h & mask;
        while (true)
        {
            int v = id[p];
            if (v < 0) return -1;
            if (hash[p] == h)
            {
                byte[] k = keys[p];
                if (k.Length == len)
                {
                    int i = 0;
                    while (i < len && k[i] == s[i]) i++;
                    if (i == len) return v;
                }
            }
            p = (p + 1) & mask;
        }
    }

    public void Put(byte[] key, int len, ulong h, int v)
    {
        if ((size + 1) << 1 > id.Length) Resize();
        int p = (int)h & mask;
        while (id[p] >= 0) p = (p + 1) & mask;
        id[p] = v;
        hash[p] = h;
        var k = new byte[len];
        Array.Copy(key, k, len);
        keys[p] = k;
        size++;
    }
}

static unsafe class Program
{
    static List<byte[]> names;
    static List<IntList> lists;
    static List<int> maxes;
    static Table table;
    static byte[] scratch;
    static long lines, malformed;
    static long[] statusCount;

    static bool IsDig(byte c) => (uint)(c - (byte)'0') <= 9u;

    static bool IsPathCh(byte c) =>
        (c >= (byte)'A' && c <= (byte)'Z') || (c >= (byte)'a' && c <= (byte)'z') ||
        (c >= (byte)'0' && c <= (byte)'9') || c == (byte)'_' || c == (byte)'-' || c == (byte)'/';

    static bool TsOk(byte* p)
    {
        return IsDig(p[0]) && IsDig(p[1]) && IsDig(p[2]) && IsDig(p[3]) && p[4] == (byte)'-'
            && IsDig(p[5]) && IsDig(p[6]) && p[7] == (byte)'-'
            && IsDig(p[8]) && IsDig(p[9]) && p[10] == (byte)'T'
            && IsDig(p[11]) && IsDig(p[12]) && p[13] == (byte)':'
            && IsDig(p[14]) && IsDig(p[15]) && p[16] == (byte)':'
            && IsDig(p[17]) && IsDig(p[18]) && p[19] == (byte)'.'
            && IsDig(p[20]) && IsDig(p[21]) && IsDig(p[22]) && p[23] == (byte)'Z';
    }

    static ulong HashBytes(byte[] s, int len)
    {
        ulong h = 1469598103934665603UL;
        for (int i = 0; i < len; i++)
        {
            h ^= s[i];
            h *= 1099511628211UL;
        }
        return h;
    }

    static int CmpBytes(byte[] a, byte[] b)
    {
        int n = Math.Min(a.Length, b.Length);
        for (int i = 0; i < n; i++)
        {
            int d = a[i] - b[i];
            if (d != 0) return d;
        }
        return a.Length - b.Length;
    }

    static void Process(byte* lp, byte* lineEnd)
    {
        lines++;
        bool ok = true;
        int statusClass = 0;
        int lat = 0;
        byte* pathStart = null, pathEnd = null;

        byte* q = lp;
        byte* end = lineEnd;

        do
        {
            if (end - q < 25 || !TsOk(q)) { ok = false; break; }
            q += 24;
            if (*q != (byte)' ') { ok = false; break; }
            q++;
            if (q >= end || *q < (byte)'a' || *q > (byte)'z') { ok = false; break; }
            q++;
            while (q < end && *q >= (byte)'a' && *q <= (byte)'z') q++;
            if (q >= end || *q != (byte)'-') { ok = false; break; }
            q++;
            if (q >= end || !IsDig(*q)) { ok = false; break; }
            while (q < end && IsDig(*q)) q++;
            if (q >= end || *q != (byte)' ') { ok = false; break; }
            q++;

            long rem = end - q;
            if (rem >= 4 && q[0] == (byte)'G' && q[1] == (byte)'E' && q[2] == (byte)'T' && q[3] == (byte)' ') q += 4;
            else if (rem >= 5 && q[0] == (byte)'P' && q[1] == (byte)'O' && q[2] == (byte)'S' && q[3] == (byte)'T' && q[4] == (byte)' ') q += 5;
            else if (rem >= 4 && q[0] == (byte)'P' && q[1] == (byte)'U' && q[2] == (byte)'T' && q[3] == (byte)' ') q += 4;
            else if (rem >= 7 && q[0] == (byte)'D' && q[1] == (byte)'E' && q[2] == (byte)'L' && q[3] == (byte)'E' && q[4] == (byte)'T' && q[5] == (byte)'E' && q[6] == (byte)' ') q += 7;
            else if (rem >= 6 && q[0] == (byte)'P' && q[1] == (byte)'A' && q[2] == (byte)'T' && q[3] == (byte)'C' && q[4] == (byte)'H' && q[5] == (byte)' ') q += 6;
            else { ok = false; break; }

            if (q >= end || *q != (byte)'/') { ok = false; break; }
            pathStart = q;
            while (q < end && IsPathCh(*q)) q++;
            pathEnd = q;
            if (q < end && *q == (byte)'?')
            {
                q++;
                while (q < end && *q != (byte)' ') q++;
            }
            if (q >= end || *q != (byte)' ') { ok = false; break; }
            q++;
            if (end - q < 4 || !IsDig(q[0]) || !IsDig(q[1]) || !IsDig(q[2]) || q[3] != (byte)' ') { ok = false; break; }
            statusClass = q[0] - (byte)'0';
            q += 4;
            if (q >= end || !IsDig(*q)) { ok = false; break; }
            while (q < end && IsDig(*q)) q++;
            if (q >= end || *q != (byte)'B') { ok = false; break; }
            q++;
            if (q >= end || *q != (byte)' ') { ok = false; break; }
            q++;
            if (q >= end || !IsDig(*q)) { ok = false; break; }
            int v = 0;
            while (q < end && IsDig(*q)) { v = v * 10 + (*q - (byte)'0'); q++; }
            if (q >= end || *q != (byte)'.') { ok = false; break; }
            q++;
            if (q >= end || !IsDig(*q)) { ok = false; break; }
            v = v * 10 + (*q - (byte)'0');
            q++;
            if (end - q < 3 || q[0] != (byte)'m' || q[1] != (byte)'s' || q[2] != (byte)' ') { ok = false; break; }
            q += 3;
            if (q >= end || *q != (byte)'"') { ok = false; break; }
            q++;
            while (q < end && *q != (byte)'"') q++;
            if (q >= end) { ok = false; break; }
            q++;
            if (q != end) { ok = false; break; }
            lat = v;
        } while (false);

        if (!ok)
        {
            malformed++;
        }
        else
        {
            statusCount[statusClass]++;
            long pathLen = pathEnd - pathStart;
            int need = (int)pathLen * 4 + 4;
            if (need > scratch.Length) scratch = new byte[need];
            int tlen = 0;
            byte* t = pathStart;
            while (t < pathEnd)
            {
                scratch[tlen++] = (byte)'/';
                t++;
                byte* s = t;
                bool digits = true, nonempty = false;
                while (t < pathEnd && *t != (byte)'/')
                {
                    if (!IsDig(*t)) digits = false;
                    nonempty = true;
                    t++;
                }
                if (nonempty && digits)
                {
                    scratch[tlen++] = (byte)'{';
                    scratch[tlen++] = (byte)'i';
                    scratch[tlen++] = (byte)'d';
                    scratch[tlen++] = (byte)'}';
                }
                else
                {
                    while (s < t) scratch[tlen++] = *s++;
                }
            }
            ulong h = HashBytes(scratch, tlen);
            int id = table.Find(scratch, tlen, h);
            if (id < 0)
            {
                id = names.Count;
                byte[] key = new byte[tlen];
                Array.Copy(scratch, key, tlen);
                table.Put(key, tlen, h, id);
                names.Add(key);
                lists.Add(new IntList());
                maxes.Add(0);
            }
            IntList il = lists[id];
            il.Add(lat);
            if (lat > maxes[id]) maxes[id] = lat;
        }
    }

    static int Main(string[] args)
    {
        names = new List<byte[]>();
        lists = new List<IntList>();
        maxes = new List<int>();
        table = new Table(1024);
        scratch = new byte[2048];
        statusCount = new long[10];

        byte[] buf = new byte[1 << 22];
        int len = 0;
        bool eof = false;
        using (var fs = new FileStream(args[0], FileMode.Open, FileAccess.Read, FileShare.Read, 1 << 16, FileOptions.SequentialScan))
        {
            while (!eof)
            {
                if (len == buf.Length) Array.Resize(ref buf, len << 1);
                int r = fs.Read(buf, len, buf.Length - len);
                if (r <= 0)
                {
                    eof = true;
                }
                else
                {
                    len += r;
                }
                int s = 0;
                fixed (byte* bp = buf)
                {
                    while (s < len)
                    {
                        int rel = buf.AsSpan(s, len - s).IndexOf((byte)'\n');
                        if (rel < 0) break;
                        int nl = s + rel;
                        Process(bp + s, bp + nl);
                        s = nl + 1;
                    }
                }
                if (s > 0)
                {
                    Buffer.BlockCopy(buf, s, buf, 0, len - s);
                    len -= s;
                }
            }
        }
        if (len > 0)
        {
            fixed (byte* bp = buf) Process(bp, bp + len);
        }

        var sb = new StringBuilder(512);
        sb.Append("lines ").Append(lines).Append('\n');
        sb.Append("malformed ").Append(malformed).Append('\n');
        for (int d = 0; d < 10; d++)
        {
            if (statusCount[d] != 0)
                sb.Append("status ").Append(d).Append("xx ").Append(statusCount[d]).Append('\n');
        }

        int m = names.Count;
        int[] order = new int[m];
        for (int i = 0; i < m; i++) order[i] = i;
        Array.Sort(order, (a, b) =>
        {
            int ca = lists[a].n, cb = lists[b].n;
            if (ca != cb) return cb - ca;
            return CmpBytes(names[a], names[b]);
        });

        int top = Math.Min(10, m);
        for (int k = 0; k < top; k++)
        {
            int idx = order[k];
            IntList il = lists[idx];
            Array.Sort(il.a, 0, il.n);
            long cnt = il.n;
            int i50 = (int)((50L * cnt + 99) / 100) - 1;
            int i95 = (int)((95L * cnt + 99) / 100) - 1;
            int p50 = il.a[i50], p95 = il.a[i95], mx = il.a[il.n - 1];
            sb.Append("path ").Append(Encoding.Latin1.GetString(names[idx]))
              .Append(' ').Append(cnt)
              .Append(' ').Append(p50 / 10).Append('.').Append(p50 % 10)
              .Append(' ').Append(p95 / 10).Append('.').Append(p95 % 10)
              .Append(' ').Append(mx / 10).Append('.').Append(mx % 10)
              .Append('\n');
        }

        Console.Out.Write(sb.ToString());
        return 0;
    }
}
