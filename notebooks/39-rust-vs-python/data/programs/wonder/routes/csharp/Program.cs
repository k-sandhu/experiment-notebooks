using System;
using System.IO;
using System.Numerics;
using System.Text;

byte[] buf = File.ReadAllBytes(args[0]);
int pos = 0;
int ParseInt()
{
    int n = buf.Length;
    while (pos < n && (buf[pos] < (byte)'0' || buf[pos] > (byte)'9')) pos++;
    int v = 0;
    while (pos < n && buf[pos] >= (byte)'0' && buf[pos] <= (byte)'9') { v = v * 10 + (buf[pos] - (byte)'0'); pos++; }
    return v;
}
if (buf.Length == 0) return;
int N = ParseInt(), M = ParseInt(), Q = ParseInt();
int[] eu = new int[M], ev = new int[M], ew = new int[M];
int[] deg = new int[N];
int ecnt = 0;
for (int i = 0; i < M; i++)
{
    int u = ParseInt(), v = ParseInt(), w = ParseInt();
    if (u == v) continue;
    eu[ecnt] = u; ev[ecnt] = v; ew[ecnt] = w; ecnt++;
    deg[u]++; deg[v]++;
}
int[] sources = new int[Q];
for (int i = 0; i < Q; i++) sources[i] = ParseInt();
buf = null;
int[] off = new int[N + 1];
for (int i = 0; i < N; i++) off[i + 1] = off[i] + deg[i];
int[] adj = new int[off[N]];
int[] curArr = new int[N];
Array.Copy(off, curArr, N);
for (int i = 0; i < ecnt; i++)
{
    int u = eu[i], v = ev[i], w = ew[i];
    adj[curArr[u]++] = (v << 10) | w;
    adj[curArr[v]++] = (u << 10) | w;
}
eu = null; ev = null; ew = null; deg = null; curArr = null;

const int INF = 0x3f3f3f3f;
int[] dist = new int[N];
int[] nxt = new int[N], prv = new int[N];
byte[] done = new byte[N];
int[] head = new int[1024];
ulong[] words = new ulong[16];
var sb = new StringBuilder(Q * 40);
int[] cs = new int[64]; long[] cR = new long[64], cTot = new long[64], cFar = new long[64]; int[] cNode = new int[64]; int cacheN = 0;

for (int qi = 0; qi < Q; qi++)
{
    int s = sources[qi];
    long R, tot, far; int farNode;
    int ci = -1;
    for (int i = 0; i < cacheN; i++) if (cs[i] == s) { ci = i; break; }
    if (ci >= 0) { R = cR[ci]; tot = cTot[ci]; far = cFar[ci]; farNode = cNode[ci]; }
    else
    {
        Array.Fill(dist, INF);
        Array.Fill(done, (byte)0);
        Array.Fill(head, -1);
        Array.Fill(words, 0UL);
        dist[s] = 0; head[0] = s; nxt[s] = -1; prv[s] = -1; words[0] = 1UL;
        long inq = 1;
        int curDist = 0, curB = 0;
        R = 0; tot = 0; far = 0; farNode = s;
        while (inq > 0)
        {
            int node = head[curB];
            head[curB] = -1;
            words[curB >> 6] &= ~(1UL << (curB & 63));
            while (node != -1)
            {
                int nn = nxt[node];
                done[node] = 1; inq--;
                R++; tot += curDist;
                if (curDist > far) { far = curDist; farNode = node; }
                else if (curDist == far && node < farNode) farNode = node;
                int a0 = off[node], a1 = off[node + 1];
                for (int ai = a0; ai < a1; ai++)
                {
                    int pk = adj[ai];
                    int v = pk >> 10;
                    if (done[v] != 0) continue;
                    int nd = curDist + (pk & 1023);
                    if (nd < dist[v])
                    {
                        if (dist[v] != INF)
                        {
                            int ob = dist[v] & 1023;
                            int pv = prv[v], nv = nxt[v];
                            if (pv != -1) nxt[pv] = nv; else head[ob] = nv;
                            if (nv != -1) prv[nv] = pv;
                            if (head[ob] == -1) words[ob >> 6] &= ~(1UL << (ob & 63));
                        }
                        else inq++;
                        dist[v] = nd;
                        int nb = nd & 1023;
                        int oh = head[nb];
                        nxt[v] = oh; prv[v] = -1;
                        if (oh != -1) prv[oh] = v;
                        else words[nb >> 6] |= (1UL << (nb & 63));
                        head[nb] = v;
                    }
                }
                node = nn;
            }
            if (inq == 0) break;
            int wi = curB >> 6, bi = curB & 63;
            int nb2 = -1;
            ulong w0 = (bi == 63) ? 0UL : (words[wi] & (~0UL << (bi + 1)));
            if (w0 != 0) nb2 = (wi << 6) + BitOperations.TrailingZeroCount(w0);
            else
            {
                for (int k = 1; k < 16; k++)
                {
                    int idx = (wi + k) & 15;
                    ulong w = words[idx];
                    if (w != 0) { nb2 = (idx << 6) + BitOperations.TrailingZeroCount(w); break; }
                }
                if (nb2 == -1)
                {
                    ulong low = (bi == 63) ? ~0UL : ((1UL << (bi + 1)) - 1UL);
                    ulong w = words[wi] & low;
                    if (w != 0) nb2 = (wi << 6) + BitOperations.TrailingZeroCount(w);
                }
            }
            int offd = nb2 - curB; if (offd <= 0) offd += 1024;
            curDist += offd; curB = nb2;
        }
        if (cacheN < 64) { cs[cacheN] = s; cR[cacheN] = R; cTot[cacheN] = tot; cFar[cacheN] = far; cNode[cacheN] = farNode; cacheN++; }
    }
    sb.Append(s).Append(' ').Append(R).Append(' ').Append(tot).Append(' ').Append(far).Append(' ').Append(farNode).Append('\n');
}
Console.Out.Write(sb.ToString());
