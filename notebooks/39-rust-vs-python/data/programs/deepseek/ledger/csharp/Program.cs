using System;
using System.IO;
using System.Text;
using System.Runtime.InteropServices;

unsafe static class Program
{
    static byte* P;
    static byte* E;

    // last scanned string
    static byte* sBeg;
    static int sLen;
    static bool sEsc;

    // resolved string
    static byte* rPtr;
    static int rLen;

    static byte* scratch;
    static int scratchCap;

    static readonly byte[] K_ACCOUNT = Ascii("account");
    static readonly byte[] K_AMOUNT = Ascii("amount");
    static readonly byte[] K_TYPE = Ascii("type");
    static readonly byte[] K_TAGS = Ascii("tags");
    static readonly byte[] K_META = Ascii("meta");
    static readonly byte[] K_CHANNEL = Ascii("channel");
    static readonly byte[] K_CURRENCY = Ascii("currency");
    static readonly byte[] K_RATES = Ascii("rates");
    static readonly byte[] K_TEST = Ascii("test");
    static readonly byte[] K_VOID = Ascii("void");
    static readonly byte[] K_DEBIT = Ascii("debit");

    static byte[] Ascii(string s) => Encoding.ASCII.GetBytes(s);

    static void SkipWs()
    {
        byte* p = P;
        while (p < E)
        {
            byte c = *p;
            if (c == ' ' || c == '\t' || c == '\r' || c == '\n') p++;
            else break;
        }
        P = p;
    }

    static void ScanString()
    {
        byte* p = P + 1;
        byte* st = p;
        bool esc = false;
        while (*p != '"')
        {
            if (*p == '\\')
            {
                esc = true;
                p++;
                if (*p == 'u') p += 5; else p++;
            }
            else p++;
        }
        sBeg = st;
        sLen = (int)(p - st);
        P = p + 1;
        sEsc = esc;
    }

    static void SkipString()
    {
        P++;
        while (*P != '"')
        {
            if (*P == '\\')
            {
                P++;
                if (*P == 'u') P += 5; else P++;
            }
            else P++;
        }
        P++;
    }

    static int Hex4(byte* q)
    {
        int v = 0;
        for (int i = 0; i < 4; i++)
        {
            byte c = q[i];
            int d;
            if (c >= '0' && c <= '9') d = c - '0';
            else if (c >= 'a' && c <= 'f') d = c - 'a' + 10;
            else d = c - 'A' + 10;
            v = (v << 4) | d;
        }
        return v;
    }

    static void EnsureScratch(int need)
    {
        if (need <= scratchCap) return;
        int cap = scratchCap == 0 ? 256 : scratchCap;
        while (cap < need) cap *= 2;
        scratch = (byte*)NativeMemory.Realloc(scratch, (nuint)cap);
        scratchCap = cap;
    }

    static void Unescape()
    {
        EnsureScratch(sLen + 1);
        int n = 0;
        byte* q = sBeg;
        byte* e = sBeg + sLen;
        while (q < e)
        {
            int c = *q++;
            if (c != '\\') { scratch[n++] = (byte)c; continue; }
            int esc = *q++;
            switch (esc)
            {
                case '"': scratch[n++] = (byte)'"'; break;
                case '\\': scratch[n++] = (byte)'\\'; break;
                case '/': scratch[n++] = (byte)'/'; break;
                case 'b': scratch[n++] = (byte)'\b'; break;
                case 'f': scratch[n++] = (byte)'\f'; break;
                case 'n': scratch[n++] = (byte)'\n'; break;
                case 'r': scratch[n++] = (byte)'\r'; break;
                case 't': scratch[n++] = (byte)'\t'; break;
                case 'u':
                {
                    int cp = Hex4(q); q += 4;
                    if (cp >= 0xD800 && cp <= 0xDBFF && q + 6 <= e && q[0] == '\\' && q[1] == 'u')
                    {
                        int lo = Hex4(q + 2);
                        if (lo >= 0xDC00 && lo <= 0xDFFF)
                        {
                            cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
                            q += 6;
                        }
                    }
                    if (cp < 0x80) scratch[n++] = (byte)cp;
                    else if (cp < 0x800)
                    {
                        scratch[n++] = (byte)(0xC0 | (cp >> 6));
                        scratch[n++] = (byte)(0x80 | (cp & 0x3F));
                    }
                    else if (cp < 0x10000)
                    {
                        scratch[n++] = (byte)(0xE0 | (cp >> 12));
                        scratch[n++] = (byte)(0x80 | ((cp >> 6) & 0x3F));
                        scratch[n++] = (byte)(0x80 | (cp & 0x3F));
                    }
                    else
                    {
                        scratch[n++] = (byte)(0xF0 | (cp >> 18));
                        scratch[n++] = (byte)(0x80 | ((cp >> 12) & 0x3F));
                        scratch[n++] = (byte)(0x80 | ((cp >> 6) & 0x3F));
                        scratch[n++] = (byte)(0x80 | (cp & 0x3F));
                    }
                    break;
                }
                default: scratch[n++] = (byte)esc; break;
            }
        }
        rPtr = scratch;
        rLen = n;
    }

    static void Resolve()
    {
        if (sEsc)
        {
            Unescape();
        }
        else
        {
            rPtr = sBeg;
            rLen = sLen;
        }
    }

    static bool Eq(byte[] lit)
    {
        if (rLen != lit.Length) return false;
        byte* p = rPtr;
        int n = lit.Length;
        for (int i = 0; i < n; i++)
            if (p[i] != lit[i]) return false;
        return true;
    }

    static void SkipValue()
    {
        SkipWs();
        byte* p = P;
        byte c = *p;
        if (c == '"')
        {
            p++;
            while (*p != '"')
            {
                if (*p == '\\') { p++; if (*p == 'u') p += 5; else p++; }
                else p++;
            }
            P = p + 1;
            return;
        }
        if (c == '{' || c == '[')
        {
            int depth = 0;
            while (true)
            {
                byte d = *p;
                if (d == '"')
                {
                    p++;
                    while (*p != '"')
                    {
                        if (*p == '\\') { p++; if (*p == 'u') p += 5; else p++; }
                        else p++;
                    }
                    p++;
                }
                else if (d == '{' || d == '[') { depth++; p++; }
                else if (d == '}' || d == ']') { p++; if (--depth == 0) { P = p; return; } }
                else p++;
            }
        }
        while (p < E)
        {
            byte d = *p;
            if (d == ',' || d == '}' || d == ']' || d == ' ' || d == '\t' || d == '\r' || d == '\n') break;
            p++;
        }
        P = p;
    }

    // ---------------- rates
    static byte[][] rateKeys = new byte[16][];
    static long[] rateVals = new long[16];
    static int rateN;

    static long LookupRate()
    {
        for (int i = 0; i < rateN; i++)
        {
            byte[] k = rateKeys[i];
            if (k.Length != rLen) continue;
            byte* p = rPtr;
            bool same = true;
            for (int j = 0; j < rLen; j++)
                if (p[j] != k[j]) { same = false; break; }
            if (same) return rateVals[i];
        }
        return 0;
    }

    // ---------------- accounts
    static int[] accSlots = new int[1 << 14];
    static int[] accStart = new int[1 << 13];
    static int[] accLen = new int[1 << 13];
    static long[] accSum = new long[1 << 13];
    static int[] accCnt = new int[1 << 13];
    static int accN;
    static byte[] arena = new byte[1 << 16];
    static int arenaLen;

    static int Hash(byte* a, int len)
    {
        int h = unchecked((int)0x811c9dc5);
        for (int i = 0; i < len; i++)
        {
            h ^= a[i];
            h *= 0x01000193;
        }
        return h & 0x7fffffff;
    }

    static int HashArray(byte[] a, int off, int len)
    {
        int h = unchecked((int)0x811c9dc5);
        for (int i = 0; i < len; i++)
        {
            h ^= a[off + i];
            h *= 0x01000193;
        }
        return h & 0x7fffffff;
    }

    static void GrowAccounts()
    {
        int cap = accStart.Length * 2;
        Array.Resize(ref accStart, cap);
        Array.Resize(ref accLen, cap);
        Array.Resize(ref accSum, cap);
        Array.Resize(ref accCnt, cap);
    }

    static void Rehash()
    {
        int[] ns = new int[accSlots.Length * 2];
        int mask = ns.Length - 1;
        for (int i = 0; i < accN; i++)
        {
            int slot = HashArray(arena, accStart[i], accLen[i]) & mask;
            while (ns[slot] != 0) slot = (slot + 1) & mask;
            ns[slot] = i + 1;
        }
        accSlots = ns;
    }

    static int InternAccount()
    {
        int mask = accSlots.Length - 1;
        int slot = Hash(rPtr, rLen) & mask;
        while (true)
        {
            int e = accSlots[slot];
            if (e == 0) break;
            int i = e - 1;
            if (accLen[i] == rLen)
            {
                int st = accStart[i];
                byte* p = rPtr;
                bool same = true;
                for (int j = 0; j < rLen; j++)
                    if (arena[st + j] != p[j]) { same = false; break; }
                if (same) return i;
            }
            slot = (slot + 1) & mask;
        }
        if (accN == accStart.Length) GrowAccounts();
        int idx = accN++;
        if (arenaLen + rLen > arena.Length)
        {
            int cap = arena.Length;
            while (cap < arenaLen + rLen) cap *= 2;
            Array.Resize(ref arena, cap);
        }
        int start = arenaLen;
        byte* src = rPtr;
        for (int j = 0; j < rLen; j++) arena[start + j] = src[j];
        accStart[idx] = start;
        accLen[idx] = rLen;
        arenaLen += rLen;
        accSum[idx] = 0;
        accCnt[idx] = 0;
        accSlots[slot] = idx + 1;
        if (accN * 2 > accSlots.Length) Rehash();
        return idx;
    }

    // ---------------- channels
    static byte[][] chName = new byte[64][];
    static long[] chCnt = new long[64];
    static long[] chNet = new long[64];
    static int chN;

    static int InternChannel()
    {
        for (int i = 0; i < chN; i++)
        {
            byte[] n = chName[i];
            if (n.Length != rLen) continue;
            byte* p = rPtr;
            bool same = true;
            for (int j = 0; j < rLen; j++)
                if (n[j] != p[j]) { same = false; break; }
            if (same) return i;
        }
        if (chN == chName.Length)
        {
            int cap = chN * 2;
            Array.Resize(ref chName, cap);
            Array.Resize(ref chCnt, cap);
            Array.Resize(ref chNet, cap);
        }
        byte[] name = new byte[rLen];
        byte* q = rPtr;
        for (int j = 0; j < rLen; j++) name[j] = q[j];
        chName[chN] = name;
        chCnt[chN] = 0;
        chNet[chN] = 0;
        return chN++;
    }

    static long ParseAmount()
    {
        byte* a = rPtr;
        int i = 0;
        long whole = 0;
        while (i < rLen)
        {
            byte c = a[i];
            if (c < '0' || c > '9') break;
            whole = whole * 10 + (c - '0');
            i++;
        }
        int f1 = 0, f2 = 0;
        if (i < rLen && a[i] == '.')
        {
            i++;
            if (i < rLen) { f1 = a[i] - '0'; i++; }
            if (i < rLen) { f2 = a[i] - '0'; }
        }
        return whole * 100 + f1 * 10 + f2;
    }

    // ---------------- transactions
    static long totalCount, totalNet;
    static bool curHasTest;

    static void ParseTags()
    {
        P++; SkipWs();
        if (*P == ']') { P++; return; }
        while (true)
        {
            SkipWs();
            if (*P == '"')
            {
                ScanString();
                if (!curHasTest)
                {
                    Resolve();
                    if (Eq(K_TEST)) curHasTest = true;
                }
            }
            else SkipValue();
            SkipWs();
            if (*P == ',') { P++; continue; }
            P++;
            return;
        }
    }

    static int ParseMeta()
    {
        int chIdx = -1;
        P++; SkipWs();
        if (*P == '}') { P++; return chIdx; }
        while (true)
        {
            SkipWs();
            ScanString();
            Resolve();
            bool isChannel = Eq(K_CHANNEL);
            SkipWs();
            P++;
            SkipWs();
            if (isChannel)
            {
                ScanString();
                Resolve();
                chIdx = InternChannel();
            }
            else SkipValue();
            SkipWs();
            if (*P == ',') { P++; continue; }
            P++;
            return chIdx;
        }
    }

    static void ParseTransaction()
    {
        int acctIdx = -1;
        int chIdx = -1;
        int sign = 1;
        curHasTest = false;
        long hundredths = 0;
        long rate = 0;

        P++;
        SkipWs();
        if (*P == '}') { P++; return; }
        while (true)
        {
            SkipWs();
            ScanString();
            Resolve();
            int first = rLen > 0 ? rPtr[0] : 0;
            SkipWs();
            P++;
            SkipWs();
            switch (first)
            {
                case 'a':
                    if (Eq(K_ACCOUNT)) { ScanString(); Resolve(); acctIdx = InternAccount(); }
                    else if (Eq(K_AMOUNT)) { ScanString(); Resolve(); hundredths = ParseAmount(); }
                    else SkipValue();
                    break;
                case 't':
                    if (Eq(K_TYPE))
                    {
                        ScanString(); Resolve();
                        if (Eq(K_VOID)) sign = 0;
                        else if (Eq(K_DEBIT)) sign = -1;
                        else sign = 1;
                    }
                    else if (Eq(K_TAGS)) ParseTags();
                    else SkipValue();
                    break;
                case 'm':
                    if (Eq(K_META)) chIdx = ParseMeta();
                    else SkipValue();
                    break;
                case 'c':
                    if (Eq(K_CURRENCY)) { ScanString(); Resolve(); rate = LookupRate(); }
                    else SkipValue();
                    break;
                default:
                    SkipValue();
                    break;
            }
            SkipWs();
            if (*P == ',') { P++; continue; }
            P++;
            break;
        }

        if (sign == 0 || curHasTest) return;

        long usd = (hundredths * rate) / 1000000L;
        long val = sign > 0 ? usd : -usd;

        totalCount++;
        totalNet += val;
        if (acctIdx >= 0)
        {
            accSum[acctIdx] += val;
            accCnt[acctIdx]++;
        }
        if (chIdx >= 0)
        {
            chCnt[chIdx]++;
            chNet[chIdx] += val;
        }
    }

    static int CmpBytes(byte[] a, byte[] b)
    {
        int n = Math.Min(a.Length, b.Length);
        for (int i = 0; i < n; i++)
        {
            int x = a[i], y = b[i];
            if (x != y) return x - y;
        }
        return a.Length - b.Length;
    }

    static int CmpArena(int i, int j)
    {
        int ni = accLen[i], nj = accLen[j];
        int si = accStart[i], sj = accStart[j];
        int n = Math.Min(ni, nj);
        for (int k = 0; k < n; k++)
        {
            int x = arena[si + k], y = arena[sj + k];
            if (x != y) return x - y;
        }
        return ni - nj;
    }

    static int Main(string[] args)
    {
        if (args.Length < 1) return 1;

        byte[] data = File.ReadAllBytes(args[0]);

        fixed (byte* basePtr = data)
        {
            P = basePtr;
            E = basePtr + data.Length;

            // {"rates": {...}}
            SkipWs();
            P++;
            SkipWs();
            if (*P != '}')
            {
                while (true)
                {
                    SkipWs();
                    ScanString();
                    Resolve();
                    bool isRates = Eq(K_RATES);
                    SkipWs();
                    P++;
                    SkipWs();
                    if (isRates && *P == '{')
                    {
                        P++;
                        SkipWs();
                        if (*P != '}')
                        {
                            while (true)
                            {
                                SkipWs();
                                ScanString();
                                Resolve();
                                byte[] cur = new byte[rLen];
                                byte* cp = rPtr;
                                for (int j = 0; j < rLen; j++) cur[j] = cp[j];
                                SkipWs();
                                P++;
                                SkipWs();
                                bool neg = false;
                                if (*P == '-') { neg = true; P++; }
                                long v = 0;
                                while (*P >= '0' && *P <= '9')
                                {
                                    v = v * 10 + (*P - '0');
                                    P++;
                                }
                                if (neg) v = -v;
                                if (rateN == rateKeys.Length)
                                {
                                    Array.Resize(ref rateKeys, rateN * 2);
                                    Array.Resize(ref rateVals, rateN * 2);
                                }
                                rateKeys[rateN] = cur;
                                rateVals[rateN] = v;
                                rateN++;
                                SkipWs();
                                if (*P == ',') { P++; continue; }
                                P++;
                                break;
                            }
                        }
                        else P++;
                    }
                    else SkipValue();
                    SkipWs();
                    if (*P == ',') { P++; continue; }
                    P++;
                    break;
                }
            }
            else P++;

            while (true)
            {
                SkipWs();
                if (P >= E) break;
                if (*P != '{') { P++; continue; }
                ParseTransaction();
            }
        }

        // channels sorted by bytes
        int[] ci = new int[chN];
        for (int i = 0; i < chN; i++) ci[i] = i;
        for (int i = 1; i < chN; i++)
        {
            int v = ci[i];
            int j = i - 1;
            while (j >= 0 && CmpBytes(chName[ci[j]], chName[v]) > 0)
            {
                ci[j + 1] = ci[j];
                j--;
            }
            ci[j + 1] = v;
        }

        // top ten accounts
        int[] best = new int[10];
        int bn = 0;
        for (int i = 0; i < accN; i++)
        {
            if (accCnt[i] == 0) continue;
            long s = accSum[i];
            int p = bn;
            while (p > 0)
            {
                int o = best[p - 1];
                bool better;
                if (s != accSum[o]) better = s > accSum[o];
                else better = CmpArena(i, o) < 0;
                if (!better) break;
                p--;
            }
            if (p >= 10) continue;
            if (bn < 10) bn++;
            for (int j = bn - 1; j > p; j--) best[j] = best[j - 1];
            best[p] = i;
        }

        var sb = new StringBuilder(4096);
        sb.Append("counted ").Append(totalCount).Append('\n');
        sb.Append("net ").Append(totalNet).Append('\n');
        for (int i = 0; i < chN; i++)
        {
            int c = ci[i];
            if (chCnt[c] == 0) continue;
            sb.Append("channel ").Append(Encoding.UTF8.GetString(chName[c]))
              .Append(' ').Append(chCnt[c]).Append(' ').Append(chNet[c]).Append('\n');
        }
        for (int i = 0; i < bn; i++)
        {
            int a = best[i];
            sb.Append("account ").Append(Encoding.UTF8.GetString(arena, accStart[a], accLen[a]))
              .Append(' ').Append(accSum[a]).Append('\n');
        }
        byte[] outBytes = Encoding.UTF8.GetBytes(sb.ToString());
        using var stdout = Console.OpenStandardOutput();
        stdout.Write(outBytes, 0, outBytes.Length);
        return 0;
    }
}
