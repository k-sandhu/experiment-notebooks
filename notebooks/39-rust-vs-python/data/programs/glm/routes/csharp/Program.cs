using System;
using System.IO;

internal static class Program
{
    private static byte[] _buf;
    private static int _pos;

    private static int ReadInt()
    {
        while (_buf[_pos] < (byte)'0' || _buf[_pos] > (byte)'9') _pos++;
        int x = 0;
        while (_buf[_pos] >= (byte)'0' && _buf[_pos] <= (byte)'9') x = x * 10 + (_buf[_pos++] - '0');
        return x;
    }

    private static int Main(string[] args)
    {
        _buf = File.ReadAllBytes(args[0]);
        int n = ReadInt(), m = ReadInt(), q = ReadInt();

        var eu = new int[m]; var ev = new int[m]; var ew = new int[m];
        var start = new int[n + 1];
        for (int i = 0; i < m; i++)
        {
            int u = ReadInt(), v = ReadInt(), w = ReadInt();
            eu[i] = u; ev[i] = v; ew[i] = w;
            start[u + 1]++; start[v + 1]++;
        }
        for (int i = 0; i < n; i++) start[i + 1] += start[i];
        int e2 = start[n];
        var adjV = new int[e2]; var adjW = new int[e2];
        var posArr = new int[n];
        Array.Copy(start, posArr, n);
        for (int i = 0; i < m; i++)
        {
            adjV[posArr[eu[i]]] = ev[i]; adjW[posArr[eu[i]]] = ew[i]; posArr[eu[i]]++;
            adjV[posArr[ev[i]]] = eu[i]; adjW[posArr[ev[i]]] = ew[i]; posArr[ev[i]]++;
        }

        // Dial's bucket queue: weights are 1..1000, so a circular array of 1001
        // buckets (singly linked lists through the arena array) holds all
        // pending distances. Stale entries are skipped via the dist check.
        const int nb = 1001;
        var arena = new int[2 * m + 2];
        var nextIn = new int[2 * m + 2];
        var head = new int[nb];

        var dist = new int[n];
        var settled = new byte[n];
        var ob = new byte[q * 80 + 16];
        int op = 0;

        for (int qi = 0; qi < q; qi++)
        {
            int s = ReadInt();
            Array.Fill(dist, -1);
            Array.Clear(settled);
            Array.Fill(head, -1);
            int cnt = 0;
            dist[s] = 0;
            arena[cnt] = s; nextIn[cnt] = -1; head[0] = cnt; cnt++;
            int remaining = 1;
            int idx = 0;
            int d = 0;
            while (remaining > 0)
            {
                int e = head[idx];
                if (e < 0) { idx = idx + 1 == nb ? 0 : idx + 1; d++; continue; }
                head[idx] = nextIn[e];
                remaining--;
                int v = arena[e];
                if (settled[v] != 0 || dist[v] != d) continue;
                settled[v] = 1;
                int end = start[v + 1];
                for (int i = start[v]; i < end; i++)
                {
                    int u = adjV[i];
                    if (settled[u] != 0) continue;
                    int nd = d + adjW[i];
                    int du = dist[u];
                    if (du < 0 || nd < du)
                    {
                        dist[u] = nd;
                        int b = nd % nb;
                        arena[cnt] = u; nextIn[cnt] = head[b]; head[b] = cnt; cnt++;
                        remaining++;
                    }
                }
            }
            long total = 0;
            int far = 0;
            int farNode = s;
            int r = 0;
            for (int v = 0; v < n; v++)
            {
                int dd = dist[v];
                if (dd >= 0)
                {
                    r++;
                    total += dd;
                    if (dd > far || (dd == far && v < farNode)) { far = dd; farNode = v; }
                }
            }
            op = PutLong(ob, op, s); ob[op++] = (byte)' ';
            op = PutLong(ob, op, r); ob[op++] = (byte)' ';
            op = PutLong(ob, op, total); ob[op++] = (byte)' ';
            op = PutLong(ob, op, far); ob[op++] = (byte)' ';
            op = PutLong(ob, op, farNode); ob[op++] = (byte)'\n';
        }
        using Stream so = Console.OpenStandardOutput();
        so.Write(ob, 0, op);
        return 0;
    }

    private static int PutLong(byte[] ob, int op, long x)
    {
        if (x == 0) { ob[op++] = (byte)'0'; return op; }
        int t = op;
        while (x > 0) { ob[op++] = (byte)('0' + (int)(x % 10)); x /= 10; }
        for (int a = t, b = op - 1; a < b; a++, b--)
            (ob[a], ob[b]) = (ob[b], ob[a]);
        return op;
    }
}
