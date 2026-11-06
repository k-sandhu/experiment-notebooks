using System;
using System.IO;
using System.Text;

class Program
{
    static byte[] data;
    static int n;

    static byte[] scratch = new byte[1024];

    static byte[][] tmpl = new byte[1024][];
    static int[] tmplLen = new int[1024];
    static int[] count = new int[1024];
    static long[][] lat = new long[1024][];
    static int[] latN = new int[1024];
    static int nEntries;

    static int[] table = new int[2048];

    static int stStatus, stTlen;
    static long stLat;

    static bool IsDig(byte c) => (uint)(c - '0') < 10u;

    static void EnsureScratch(int need)
    {
        if (need > scratch.Length) scratch = new byte[need];
    }

    static int Hash(byte[] b, int len)
    {
        unchecked
        {
            int h = (int)0x811c9dc5;
            for (int i = 0; i < len; i++) h = (h ^ b[i]) * 16777619;
            h ^= (int)((uint)h >> 16);
            return h;
        }
    }

    static int FindEntry(int len)
    {
        int mask = table.Length - 1;
        int idx = Hash(scratch, len) & mask;
        while (true)
        {
            int s = table[idx];
            if (s == 0) return -1;
            int e = s - 1;
            if (tmplLen[e] == len && tmpl[e].AsSpan().SequenceEqual(scratch.AsSpan(0, len)))
                return e;
            idx = (idx + 1) & mask;
        }
    }

    static void AddEntry(int len)
    {
        if (nEntries == tmpl.Length)
        {
            int cap = nEntries * 2;
            Array.Resize(ref tmpl, cap);
            Array.Resize(ref tmplLen, cap);
            Array.Resize(ref count, cap);
            Array.Resize(ref lat, cap);
            Array.Resize(ref latN, cap);
        }
        int e = nEntries++;
        tmpl[e] = scratch.AsSpan(0, len).ToArray();
        tmplLen[e] = len;
        lat[e] = new long[16];
        if ((long)nEntries * 2 >= table.Length)
        {
            int[] t = new int[table.Length * 2];
            int mask = t.Length - 1;
            for (int i = 0; i < nEntries; i++)
            {
                int idx = Hash(tmpl[i], tmplLen[i]) & mask;
                while (t[idx] != 0) idx = (idx + 1) & mask;
                t[idx] = i + 1;
            }
            table = t;
        }
        else
        {
            int mask = table.Length - 1;
            int idx = Hash(tmpl[e], len) & mask;
            while (table[idx] != 0) idx = (idx + 1) & mask;
            table[idx] = e + 1;
        }
    }

    static bool ParseLine(int p, int le)
    {
        byte[] d = data;
        if (le - p < 25) return false;
        if (!(IsDig(d[p]) && IsDig(d[p + 1]) && IsDig(d[p + 2]) && IsDig(d[p + 3]) && d[p + 4] == '-'
              && IsDig(d[p + 5]) && IsDig(d[p + 6]) && d[p + 7] == '-' && IsDig(d[p + 8])
              && IsDig(d[p + 9]) && d[p + 10] == 'T' && IsDig(d[p + 11]) && IsDig(d[p + 12])
              && d[p + 13] == ':' && IsDig(d[p + 14]) && IsDig(d[p + 15]) && d[p + 16] == ':'
              && IsDig(d[p + 17]) && IsDig(d[p + 18]) && d[p + 19] == '.' && IsDig(d[p + 20])
              && IsDig(d[p + 21]) && IsDig(d[p + 22]) && d[p + 23] == 'Z' && d[p + 24] == ' '))
            return false;

        int i = p + 25;
        int j = i;
        while (j < le && d[j] >= 'a' && d[j] <= 'z') j++;
        if (j == i || j >= le || d[j] != '-') return false;
        j++;
        int ds = j;
        while (j < le && IsDig(d[j])) j++;
        if (j == ds || j >= le || d[j] != ' ') return false;
        j++;

        if (j + 4 <= le && d[j] == 'G' && d[j + 1] == 'E' && d[j + 2] == 'T' && d[j + 3] == ' ') j += 4;
        else if (j + 5 <= le && d[j] == 'P' && d[j + 1] == 'O' && d[j + 2] == 'S' && d[j + 3] == 'T' && d[j + 4] == ' ') j += 5;
        else if (j + 4 <= le && d[j] == 'P' && d[j + 1] == 'U' && d[j + 2] == 'T' && d[j + 3] == ' ') j += 4;
        else if (j + 7 <= le && d[j] == 'D' && d[j + 1] == 'E' && d[j + 2] == 'L' && d[j + 3] == 'E' && d[j + 4] == 'T' && d[j + 5] == 'E' && d[j + 6] == ' ') j += 7;
        else if (j + 6 <= le && d[j] == 'P' && d[j + 1] == 'A' && d[j + 2] == 'T' && d[j + 3] == 'C' && d[j + 4] == 'H' && d[j + 5] == ' ') j += 6;
        else return false;

        if (j >= le || d[j] != '/') return false;
        int q = j + 1;
        while (q < le)
        {
            int c = d[q];
            if ((c >= '0' && c <= '9') || (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z')
                || c == '_' || c == '/' || c == '-')
                q++;
            else break;
        }

        int fieldEnd;
        if (q < le && d[q] == '?')
        {
            int r = q + 1;
            while (r < le && d[r] != ' ') r++;
            if (r >= le) return false;
            fieldEnd = r;
        }
        else if (q < le && d[q] == ' ')
        {
            fieldEnd = q;
        }
        else return false;

        EnsureScratch((q - j) * 4 + 16);
        byte[] sc = scratch;
        int t = 0;
        int s = j;
        while (s < q)
        {
            if (d[s] == '/')
            {
                sc[t++] = (byte)'/';
                s++;
                continue;
            }
            int e = s;
            bool allDig = true;
            while (e < q && d[e] != '/')
            {
                if (!IsDig(d[e])) allDig = false;
                e++;
            }
            if (allDig)
            {
                sc[t] = (byte)'{'; sc[t + 1] = (byte)'i'; sc[t + 2] = (byte)'d'; sc[t + 3] = (byte)'}';
                t += 4;
            }
            else
            {
                for (int k = s; k < e; k++) sc[t++] = d[k];
            }
            s = e;
        }

        int kk = fieldEnd;
        if (kk + 4 >= le) return false;
        if (!IsDig(d[kk + 1]) || !IsDig(d[kk + 2]) || !IsDig(d[kk + 3]) || d[kk + 4] != ' ') return false;
        stStatus = d[kk + 1] - '0';
        kk += 5;

        int e2 = kk;
        while (e2 < le && IsDig(d[e2])) e2++;
        if (e2 == kk) return false;
        if (e2 >= le || d[e2] != 'B') return false;
        e2++;
        if (e2 >= le || d[e2] != ' ') return false;
        e2++;

        int ls = e2;
        long v = 0;
        while (e2 < le && IsDig(d[e2]))
        {
            v = v * 10 + (d[e2] - '0');
            e2++;
        }
        if (e2 == ls) return false;
        if (e2 >= le || d[e2] != '.') return false;
        e2++;
        if (e2 >= le || !IsDig(d[e2])) return false;
        v = v * 10 + (d[e2] - '0');
        e2++;
        if (e2 + 3 >= le) return false;
        if (d[e2] != 'm' || d[e2 + 1] != 's' || d[e2 + 2] != ' ') return false;
        e2 += 3;
        if (d[e2] != '"') return false;
        e2++;
        int r2 = e2;
        while (r2 < le && d[r2] != '"') r2++;
        if (r2 != le - 1) return false;

        stLat = v;
        stTlen = t;
        return true;
    }

    static int CmpBytes(byte[] a, byte[] b)
    {
        int m = Math.Min(a.Length, b.Length);
        for (int i = 0; i < m; i++)
        {
            int x = a[i], y = b[i];
            if (x != y) return x - y;
        }
        return a.Length - b.Length;
    }

    static bool Better(int a, int b)
    {
        if (count[a] != count[b]) return count[a] > count[b];
        return CmpBytes(tmpl[a], tmpl[b]) < 0;
    }

    static void AppendTenths(StringBuilder sb, long v)
    {
        sb.Append(v / 10).Append('.').Append(v % 10);
    }

    static void Main(string[] args)
    {
        data = File.ReadAllBytes(args[0]);
        n = data.Length;

        long lines = 0, malformed = 0;
        long[] statusCount = new long[10];

        int p = 0;
        while (p < n)
        {
            int rel = data.AsSpan(p).IndexOf((byte)'\n');
            int le = rel < 0 ? n : p + rel;
            lines++;
            if (ParseLine(p, le))
            {
                statusCount[stStatus]++;
                int len = stTlen;
                int e = FindEntry(len);
                if (e < 0)
                {
                    AddEntry(len);
                    e = nEntries - 1;
                }
                count[e]++;
                long[] a = lat[e];
                int k = latN[e];
                if (k == a.Length)
                {
                    Array.Resize(ref a, k * 2);
                    lat[e] = a;
                }
                a[k] = stLat;
                latN[e] = k + 1;
            }
            else
            {
                malformed++;
            }
            p = rel < 0 ? n : le + 1;
        }

        int[] best = new int[10];
        int bestN = 0;
        for (int e = 0; e < nEntries; e++)
        {
            int pos = 0;
            while (pos < bestN && Better(best[pos], e)) pos++;
            if (pos < 10)
            {
                int lim = Math.Min(bestN, 9);
                for (int k = lim; k > pos; k--) best[k] = best[k - 1];
                best[pos] = e;
                if (bestN < 10) bestN++;
            }
        }

        var sb = new StringBuilder(8192);
        sb.Append("lines ").Append(lines).Append('\n');
        sb.Append("malformed ").Append(malformed).Append('\n');
        for (int c = 0; c < 10; c++)
        {
            if (statusCount[c] != 0)
                sb.Append("status ").Append((char)('0' + c)).Append("xx ").Append(statusCount[c]).Append('\n');
        }
        for (int bi = 0; bi < bestN; bi++)
        {
            int e = best[bi];
            int len = latN[e];
            Array.Sort(lat[e], 0, len);
            int i50 = (50 * len + 99) / 100 - 1;
            int i95 = (95 * len + 99) / 100 - 1;
            sb.Append("path ").Append(Encoding.ASCII.GetString(tmpl[e])).Append(' ').Append(count[e]).Append(' ');
            AppendTenths(sb, lat[e][i50]);
            sb.Append(' ');
            AppendTenths(sb, lat[e][i95]);
            sb.Append(' ');
            AppendTenths(sb, lat[e][len - 1]);
            sb.Append('\n');
        }

        using Stream stdout = Console.OpenStandardOutput();
        byte[] outb = Encoding.UTF8.GetBytes(sb.ToString());
        stdout.Write(outb, 0, outb.Length);
    }
}
