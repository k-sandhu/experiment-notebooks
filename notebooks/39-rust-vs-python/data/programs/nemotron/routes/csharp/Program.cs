// Routes: shortest road distances from several sources.
// Multi-source Dijkstra (one run per source) over an undirected graph.
// C# 12, .NET 8, BCL only.
//
// Graph is stored in CSR form: start[node..node+1) indexes into gto/gw.
// Distances are int: any simple path has at most N-1 edges of weight <= 1000,
// so a distance never exceeds (N-1)*1000 < 2^31. Totals need long.

using System;
using System.IO;
using System.Text;

internal static class Program
{
    private static byte[] buf;
    private static int pos;

    private const int INF = int.MaxValue;

    private static int NextInt()
    {
        while (pos < buf.Length && buf[pos] <= 32) pos++;
        bool neg = false;
        if (pos < buf.Length && buf[pos] == 45) { neg = true; pos++; }
        int v = 0;
        while (pos < buf.Length && buf[pos] >= 48 && buf[pos] <= 57) {
            v = v * 10 + (buf[pos] - 48);
            pos++;
        }
        return neg ? -v : v;
    }

    private static void Main(string[] args)
    {
        buf = File.ReadAllBytes(args[0]);
        pos = 0;

        int N = NextInt();
        int M = NextInt();
        int Q = NextInt();

        int[] deg = new int[N + 1];
        int[] eu = new int[M];
        int[] ev = new int[M];
        int[] ew = new int[M];
        for (int i = 0; i < M; i++) {
            int u = NextInt();
            int v = NextInt();
            int w = NextInt();
            eu[i] = u;
            ev[i] = v;
            ew[i] = w;
            deg[u]++;
            deg[v]++;
        }

        int[] start = new int[N + 1];
        for (int i = 0; i < N; i++) start[i + 1] = start[i] + deg[i];

        int totalEdges = 2 * M;
        int[] gto = new int[totalEdges];
        int[] gw = new int[totalEdges];
        int[] cur = new int[N];
        Array.Copy(start, cur, N);
        for (int i = 0; i < M; i++) {
            int u = eu[i];
            int v = ev[i];
            int w = ew[i];
            int p = cur[u]++;
            gto[p] = v;
            gw[p] = w;
            p = cur[v]++;
            gto[p] = u;
            gw[p] = w;
        }

        int[] dist = new int[N];
        int[] hd = new int[Math.Max(16, M)];
        int[] hn = new int[Math.Max(16, M)];
        int hsize = 0;

        void Push(int d, int n)
        {
            int i = hsize++;
            hd[i] = d;
            hn[i] = n;
            while (i > 0) {
                int p = (i - 1) / 2;
                if (hd[p] <= d) break;
                hd[i] = hd[p];
                hn[i] = hn[p];
                i = p;
            }
            hd[i] = d;
            hn[i] = n;
        }

        var sb = new StringBuilder();
        for (int q = 0; q < Q; q++) {
            int s = NextInt();
            Array.Fill(dist, INF);
            dist[s] = 0;
            hsize = 0;
            Push(0, s);
            while (hsize > 0) {
                int d = hd[0];
                int u = hn[0];
                --hsize;
                if (hsize > 0) {
                    int lastD = hd[hsize];
                    int lastN = hn[hsize];
                    int i = 0;
                    for (;;) {
                        int l = 2 * i + 1;
                        int r = l + 1;
                        if (l >= hsize) break;
                        int child = l;
                        if (r < hsize && hd[r] < hd[l]) child = r;
                        if (hd[child] >= lastD) break;
                        hd[i] = hd[child];
                        hn[i] = hn[child];
                        i = child;
                    }
                    hd[i] = lastD;
                    hn[i] = lastN;
                }
                if (d > dist[u]) continue;
                for (int e = start[u]; e < start[u + 1]; e++) {
                    int v = gto[e];
                    int nd = d + gw[e];
                    if (nd < dist[v]) {
                        dist[v] = nd;
                        Push(nd, v);
                    }
                }
            }

            int R = 0;
            long total = 0;
            int far = -1;
            int node = -1;
            for (int i = 0; i < N; i++) {
                int d = dist[i];
                if (d != INF) {
                    R++;
                    total += d;
                    if (d > far) {
                        far = d;
                        node = i;
                    }
                }
            }
            sb.Append(s).Append(' ').Append(R).Append(' ').Append(total)
              .Append(' ').Append(far).Append(' ').Append(node).Append('\n');
        }

        Console.Write(sb.ToString());
    }
}
