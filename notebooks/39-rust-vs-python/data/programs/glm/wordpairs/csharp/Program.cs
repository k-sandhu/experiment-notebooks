using System;
using System.IO;
using System.Text;

// Word pairs: count adjacent word pairs within sentences, report totals and top 20.
internal static class Program
{
    private static byte[] _buf;
    private static long[] _pKeys;          // pair table: key -> count, cnt 0 = empty slot
    private static int[] _pCnt;
    private static long _pMask;
    private static long _pFilled;

    private static int[] _wTab;            // word table: slot -> id + 1
    private static int[] _wOff, _wLen, _wHsh;
    private static long _wMask;
    private static int _wCount;

    private static long _words, _pairs;

    private static int Main(string[] args)
    {
        if (args.Length < 1) { Console.Error.WriteLine("usage: solution INPUT_PATH"); return 1; }
        _buf = File.ReadAllBytes(args[0]);
        int n = _buf.Length;
        for (int i = 0; i < n; i++)
        {
            int c = _buf[i];
            if (c >= 'A' && c <= 'Z') _buf[i] = (byte)(c + 32);
        }

        int ps = 1 << 20;
        while (ps < n / 8) ps <<= 1; // distinct pairs scale with input size; avoid rehashing
        _pKeys = new long[ps];
        _pCnt = new int[ps];
        _pMask = ps - 1;

        _wTab = new int[1 << 16];
        _wMask = (1 << 16) - 1;
        _wOff = new int[1 << 16];
        _wLen = new int[1 << 16];
        _wHsh = new int[1 << 16];

        unsafe
        {
            fixed (byte* p = _buf)
            {
                long prev = -1; // no previous word in current sentence
                byte* end = p + n;
                byte* q = p;
                while (q < end)
                {
                    int c = *q;
                    if (IsLetter(c))
                    {
                        byte* start = q;
                        int h = unchecked((int)0x811C9DC5);
                        do
                        {
                            h = (h ^ c) * unchecked((int)0x01000193);
                            q++;
                            c = q < end ? *q : 0;
                        } while (q < end && IsLetter(c));
                        int id = Intern((int)(start - p), (int)(q - start), h);
                        _words++;
                        if (prev >= 0)
                        {
                            AddPair((prev << 32) | (uint)id);
                            _pairs++;
                        }
                        prev = id;
                    }
                    else
                    {
                        if (c == '.' || c == '!' || c == '?') prev = -1;
                        q++;
                    }
                }
            }
        }

        // Keep the 20 best pairs in a min-heap while scanning the pair table.
        long[] hKey = new long[20];
        int[] hCnt = new int[20];
        int hn = 0;
        for (long j = 0; j <= _pMask; j++)
        {
            int cnt = _pCnt[j];
            if (cnt == 0) continue;
            long key = _pKeys[j];
            if (hn < 20)
            {
                int k = hn++;
                hKey[k] = key; hCnt[k] = cnt;
                while (k > 0)
                {
                    int pp = (k - 1) / 2;
                    if (Worse(key, cnt, hKey[pp], hCnt[pp]))
                    {
                        (hKey[pp], hKey[k]) = (hKey[k], hKey[pp]);
                        (hCnt[pp], hCnt[k]) = (hCnt[k], hCnt[pp]);
                        k = pp;
                    }
                    else break;
                }
            }
            else if (Worse(hKey[0], hCnt[0], key, cnt))
            {
                hKey[0] = key; hCnt[0] = cnt;
                int k = 0;
                while (true)
                {
                    int l = 2 * k + 1, r = l + 1, m = k;
                    if (l < hn && Worse(hKey[l], hCnt[l], hKey[m], hCnt[m])) m = l;
                    if (r < hn && Worse(hKey[r], hCnt[r], hKey[m], hCnt[m])) m = r;
                    if (m == k) break;
                    (hKey[m], hKey[k]) = (hKey[k], hKey[m]);
                    (hCnt[m], hCnt[k]) = (hCnt[k], hCnt[m]);
                    k = m;
                }
            }
        }
        for (int a = 0; a < hn; a++)
        {
            int best = a;
            for (int b = a + 1; b < hn; b++)
            {
                if (hCnt[b] > hCnt[best] ||
                    (hCnt[b] == hCnt[best] && CmpWords(hKey[b], hKey[best]) < 0)) best = b;
            }
            if (best != a)
            {
                (hKey[a], hKey[best]) = (hKey[best], hKey[a]);
                (hCnt[a], hCnt[best]) = (hCnt[best], hCnt[a]);
            }
        }

        var sb = new StringBuilder(64 + hn * 48);
        sb.Append("words ").Append(_words).Append('\n');
        sb.Append("pairs ").Append(_pairs).Append('\n');
        sb.Append("distinct ").Append(_pFilled).Append('\n');
        for (int k = 0; k < hn; k++)
        {
            long key = hKey[k];
            int w1 = (int)(key >> 32), w2 = (int)key;
            sb.Append(hCnt[k]).Append(' ');
            sb.Append(Encoding.Latin1.GetString(_buf, _wOff[w1], _wLen[w1]));
            sb.Append(' ');
            sb.Append(Encoding.Latin1.GetString(_buf, _wOff[w2], _wLen[w2]));
            sb.Append('\n');
        }
        using var stdout = Console.OpenStandardOutput();
        stdout.Write(Encoding.Latin1.GetBytes(sb.ToString()));
        return 0;
    }

    private static bool IsLetter(int c) => (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z');

    private static bool Worse(long ka, int ca, long kb, int cb)
    {
        if (ca != cb) return ca < cb;
        return CmpWords(ka, kb) > 0;
    }

    private static int CmpWords(long a, long b)
    {
        int c = CmpWord((int)(a >> 32), (int)(b >> 32));
        if (c != 0) return c;
        return CmpWord((int)a, (int)b);
    }

    private static int CmpWord(int a, int b)
    {
        int o1 = _wOff[a], l1 = _wLen[a], o2 = _wOff[b], l2 = _wLen[b];
        int m = l1 < l2 ? l1 : l2;
        for (int k = 0; k < m; k++)
        {
            int d = _buf[o1 + k] - _buf[o2 + k];
            if (d != 0) return d;
        }
        return l1 - l2;
    }

    private static void AddPair(long key)
    {
        if ((_pFilled + 1) * 4 > (_pMask + 1) * 3) GrowPairs();
        int i = Mix(key) & (int)_pMask;
        while (true)
        {
            if (_pCnt[i] == 0)
            {
                _pKeys[i] = key;
                _pCnt[i] = 1;
                _pFilled++;
                return;
            }
            if (_pKeys[i] == key)
            {
                _pCnt[i]++;
                return;
            }
            i = (i + 1) & (int)_pMask;
        }
    }

    private static void GrowPairs()
    {
        long[] ok = _pKeys;
        int[] oc = _pCnt;
        int ns = ok.Length * 2;
        _pKeys = new long[ns];
        _pCnt = new int[ns];
        _pMask = ns - 1;
        for (int j = 0; j < ok.Length; j++)
        {
            int c = oc[j];
            if (c != 0)
            {
                long key = ok[j];
                int i = Mix(key) & (int)_pMask;
                while (_pCnt[i] != 0) i = (i + 1) & (int)_pMask;
                _pKeys[i] = key;
                _pCnt[i] = c;
            }
        }
    }

    private static int Mix(long x)
    {
        ulong u = (ulong)x;
        u += 0x9E3779B97F4A7C15UL;
        u = (u ^ (u >> 30)) * 0xBF58476D1CE4E5B9UL;
        u = (u ^ (u >> 27)) * 0x94D049BB133111EBUL;
        return (int)(u ^ (u >> 31));
    }

    private static unsafe int Intern(int o, int l, int h)
    {
        if ((_wCount + 1) * 2 > _wMask + 1) GrowWords();
        int i = h & (int)_wMask;
        while (true)
        {
            int slot = _wTab[i];
            if (slot == 0)
            {
                int nid = _wCount++;
                _wOff[nid] = o; _wLen[nid] = l; _wHsh[nid] = h;
                _wTab[i] = nid + 1;
                return nid;
            }
            int id = slot - 1;
            if (_wHsh[id] == h && _wLen[id] == l && EqBytes(_wOff[id], o, l)) return id;
            i = (i + 1) & (int)_wMask;
        }
    }

    private static bool EqBytes(int a, int b, int l)
    {
        for (int k = 0; k < l; k++) if (_buf[a + k] != _buf[b + k]) return false;
        return true;
    }

    private static void GrowWords()
    {
        int[] ot = _wTab;
        int ns = ot.Length * 2;
        _wTab = new int[ns];
        _wMask = ns - 1;
        for (int j = 0; j < ot.Length; j++)
        {
            int slot = ot[j];
            if (slot != 0)
            {
                int id = slot - 1;
                int i = _wHsh[id] & (int)_wMask;
                while (_wTab[i] != 0) i = (i + 1) & (int)_wMask;
                _wTab[i] = id + 1;
            }
        }
    }
}
