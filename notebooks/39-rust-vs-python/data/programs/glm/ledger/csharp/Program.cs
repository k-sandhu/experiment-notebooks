using System;
using System.Buffers.Binary;
using System.Text;

// Ledger: sum JSON-lines transactions with exact integer currency conversion.
// Single pass over the raw bytes; only the needed fields are extracted.
// Keys live in open-addressing tables backed by a private byte pool.
sealed class Table
{
    public int cap = 1024, mask = 1023, size, poolLen;
    public int[] slot = new int[1024];   // entry index + 1, 0 = empty
    public int[] keyOff = new int[1024];
    public int[] keyLen = new int[1024];
    public long[] a = new long[1024];    // count (channels)
    public long[] b = new long[1024];    // net
    public byte[] pool = new byte[1 << 16];

    static long Hash(byte[] d, int off, int len)
    {
        ulong h = 0xcbf29ce484222325UL;
        for (int i = 0; i < len; i++)
        {
            h ^= d[off + i];
            h *= 0x100000001b3UL;
        }
        return (long)h;
    }

    public int Find(byte[] d, int off, int len)
    {
        int h = (int)Hash(d, off, len);
        int i = h & mask;
        int[] slot = this.slot;
        while (slot[i] != 0)
        {
            int e = slot[i] - 1;
            if (keyLen[e] == len)
            {
                var p = pool;
                int po = keyOff[e], k = 0;
                while (k < len && p[po + k] == d[off + k]) k++;
                if (k == len) return e;
            }
            i = (i + 1) & mask;
        }
        return -1;
    }

    public int FindOrInsert(byte[] d, int off, int len)
    {
        if (size * 10 >= cap * 7) Grow();
        int h = (int)Hash(d, off, len);
        int i = h & mask;
        int[] slot = this.slot;
        while (slot[i] != 0)
        {
            int e = slot[i] - 1;
            if (keyLen[e] == len)
            {
                var p = pool;
                int po = keyOff[e], k = 0;
                while (k < len && p[po + k] == d[off + k]) k++;
                if (k == len) return e;
            }
            i = (i + 1) & mask;
        }
        int ne = size++;
        if (poolLen + len > pool.Length)
            Array.Resize(ref pool, Math.Max(pool.Length * 2, poolLen + len));
        Array.Copy(d, off, pool, poolLen, len);
        keyOff[ne] = poolLen;
        keyLen[ne] = len;
        poolLen += len;
        a[ne] = 0;
        b[ne] = 0;
        slot[i] = ne + 1;
        return ne;
    }

    void Grow()
    {
        cap <<= 1;
        mask = cap - 1;
        var nslot = new int[cap];
        var nKeyOff = new int[cap];
        var nKeyLen = new int[cap];
        var na = new long[cap];
        var nb = new long[cap];
        for (int e = 0; e < size; e++)
        {
            int h = (int)Hash(pool, keyOff[e], keyLen[e]);
            int i = h & mask;
            while (nslot[i] != 0) i = (i + 1) & mask;
            nslot[i] = e + 1;
            nKeyOff[e] = keyOff[e];
            nKeyLen[e] = keyLen[e];
            na[e] = a[e];
            nb[e] = b[e];
        }
        slot = nslot;
        keyOff = nKeyOff;
        keyLen = nKeyLen;
        a = na;
        b = nb;
    }
}

static class Program
{
    static byte[] data;
    static byte[] scratch = new byte[256];
    static int scratchLen;

    static bool IsWS(byte c) => c == (byte)' ' || c == (byte)'\t' || c == (byte)'\r' || c == (byte)'\n';

    static int SkipWS(int i)
    {
        while (i < data.Length && IsWS(data[i])) i++;
        return i;
    }

    static int sVal, eVal, sNext;
    static bool escVal;

    static void ParseString(int i)
    {
        i++;
        sVal = i;
        bool esc = false;
        int n = data.Length;
        while (i < n)
        {
            byte c = data[i];
            if (c == (byte)'"') break;
            if (c == (byte)'\\')
            {
                esc = true;
                i++;
                if (i < n && data[i] == (byte)'u') i += 4;
            }
            i++;
        }
        eVal = i;
        escVal = esc;
        sNext = i + 1;
    }

    static int SkipValue(int i)
    {
        int n = data.Length;
        if (i < n && data[i] == (byte)'"')
        {
            ParseString(i);
            return sNext;
        }
        if (i < n && (data[i] == (byte)'{' || data[i] == (byte)'['))
        {
            int depth = 0;
            while (i < n)
            {
                byte c = data[i];
                if (c == (byte)'"')
                {
                    ParseString(i);
                    i = sNext;
                    continue;
                }
                if (c == (byte)'{' || c == (byte)'[') depth++;
                else if (c == (byte)'}' || c == (byte)']')
                {
                    if (--depth == 0) return i + 1;
                }
                i++;
            }
            return i;
        }
        while (i < n)
        {
            byte c = data[i];
            if (c == (byte)',' || c == (byte)'}' || c == (byte)']') break;
            i++;
        }
        return i;
    }

    static bool StrEq(int s, int e, bool esc, string lit)
    {
        if (!esc)
        {
            int len = e - s;
            if (len != lit.Length) return false;
            for (int k = 0; k < len; k++)
                if (data[s + k] != lit[k]) return false;
            return true;
        }
        DecodeString(s, e);
        if (scratchLen != lit.Length) return false;
        for (int k = 0; k < scratchLen; k++)
            if (scratch[k] != lit[k]) return false;
        return true;
    }

    static void DecodeString(int s, int e)
    {
        int need = (e - s) * 4 + 16;
        if (scratch.Length < need) scratch = new byte[need];
        scratchLen = 0;
        for (int i = s; i < e; i++)
        {
            byte c = data[i];
            if (c != (byte)'\\')
            {
                scratch[scratchLen++] = c;
                continue;
            }
            i++;
            byte x = data[i];
            switch (x)
            {
                case (byte)'"': scratch[scratchLen++] = (byte)'"'; break;
                case (byte)'\\': scratch[scratchLen++] = (byte)'\\'; break;
                case (byte)'/': scratch[scratchLen++] = (byte)'/'; break;
                case (byte)'b': scratch[scratchLen++] = (byte)'\b'; break;
                case (byte)'f': scratch[scratchLen++] = (byte)'\f'; break;
                case (byte)'n': scratch[scratchLen++] = (byte)'\n'; break;
                case (byte)'r': scratch[scratchLen++] = (byte)'\r'; break;
                case (byte)'t': scratch[scratchLen++] = (byte)'\t'; break;
                case (byte)'u':
                {
                    int cp = Hex4(i + 1);
                    i += 4;
                    if (cp >= 0xD800 && cp <= 0xDBFF && i + 2 < e &&
                        data[i + 1] == (byte)'\\' && data[i + 2] == (byte)'u')
                    {
                        int lo = Hex4(i + 3);
                        if (lo >= 0xDC00 && lo <= 0xDFFF)
                        {
                            cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
                            i += 6;
                        }
                    }
                    AppendRune(cp);
                    break;
                }
                default: scratch[scratchLen++] = x; break;
            }
        }
    }

    static int Hex4(int i)
    {
        int v = 0;
        for (int k = 0; k < 4; k++)
        {
            byte c = data[i + k];
            v <<= 4;
            if (c >= (byte)'0' && c <= (byte)'9') v |= c - (byte)'0';
            else if (c >= (byte)'a' && c <= (byte)'f') v |= c - (byte)'a' + 10;
            else if (c >= (byte)'A' && c <= (byte)'F') v |= c - (byte)'A' + 10;
        }
        return v;
    }

    static void AppendRune(int cp)
    {
        if (cp < 0x80) scratch[scratchLen++] = (byte)cp;
        else if (cp < 0x800)
        {
            scratch[scratchLen++] = (byte)(0xC0 | cp >> 6);
            scratch[scratchLen++] = (byte)(0x80 | cp & 0x3F);
        }
        else if (cp < 0x10000)
        {
            scratch[scratchLen++] = (byte)(0xE0 | cp >> 12);
            scratch[scratchLen++] = (byte)(0x80 | (cp >> 6) & 0x3F);
            scratch[scratchLen++] = (byte)(0x80 | cp & 0x3F);
        }
        else
        {
            scratch[scratchLen++] = (byte)(0xF0 | cp >> 18);
            scratch[scratchLen++] = (byte)(0x80 | (cp >> 12) & 0x3F);
            scratch[scratchLen++] = (byte)(0x80 | (cp >> 6) & 0x3F);
            scratch[scratchLen++] = (byte)(0x80 | cp & 0x3F);
        }
    }

    // "12", "12.5", "12.05" -> integer hundredths
    static long ParseAmount(int s, int e)
    {
        long whole = 0;
        int i = s;
        while (i < e && data[i] >= (byte)'0' && data[i] <= (byte)'9')
        {
            whole = whole * 10 + (data[i] - (byte)'0');
            i++;
        }
        long frac = 0;
        if (i < e && data[i] == (byte)'.')
        {
            i++;
            frac = (data[i] - (byte)'0') * 10L;
            i++;
            if (i < e) frac += data[i] - (byte)'0';
        }
        return whole * 100 + frac;
    }

    static byte[] keyArr = Array.Empty<byte>();
    static int keyOff, keyLen;

    static void MakeKey(int s, int e, bool esc)
    {
        if (!esc)
        {
            keyArr = data;
            keyOff = s;
            keyLen = e - s;
        }
        else
        {
            DecodeString(s, e);
            keyArr = scratch;
            keyOff = 0;
            keyLen = scratchLen;
        }
    }

    static int IndexOf(int from, byte c)
    {
        for (int i = from; i < data.Length; i++)
            if (data[i] == c) return i;
        return -1;
    }

    static bool AccountBetter(Table t, int x, int y)
    {
        long nx = t.b[x], ny = t.b[y];
        if (nx != ny) return nx > ny;
        int lx = t.keyLen[x], ly = t.keyLen[y];
        int ox = t.keyOff[x], oy = t.keyOff[y];
        int m = Math.Min(lx, ly);
        for (int k = 0; k < m; k++)
        {
            int d = (t.pool[ox + k] & 0xff) - (t.pool[oy + k] & 0xff);
            if (d != 0) return d < 0;
        }
        return lx < ly;
    }

    static void AppendLong(byte[] buf, ref int len, long v)
    {
        if (v == 0) { buf[len++] = (byte)'0'; return; }
        bool neg = v < 0;
        ulong u = neg ? (ulong)(-v) : (ulong)v;
        int start = len;
        while (u > 0)
        {
            buf[len++] = (byte)('0' + (int)(u % 10));
            u /= 10;
        }
        if (neg) buf[len++] = (byte)'-';
        Array.Reverse(buf, start, len - start);
    }

    static void Main(string[] args)
    {
        data = System.IO.File.ReadAllBytes(args[0]);
        int n = data.Length;
        var rates = new Table();
        var channels = new Table();
        var accounts = new Table();

        // First line: rates.
        int i = SkipWS(0);
        int eol = IndexOf(i, (byte)'\n');
        if (eol < 0) eol = n;
        int p = SkipWS(i);
        if (p < n && data[p] == (byte)'{')
        {
            p++;
            while (p < n)
            {
                p = SkipWS(p);
                if (p >= n || data[p] == (byte)'}') break;
                if (data[p] == (byte)',') { p++; continue; }
                ParseString(p);
                int ks = sVal, ke = eVal; bool kesc = escVal;
                p = SkipWS(sNext);
                p++; // ':'
                p = SkipWS(p);
                if (StrEq(ks, ke, kesc, "rates"))
                {
                    p = SkipWS(p);
                    p++; // '{'
                    while (p < n)
                    {
                        p = SkipWS(p);
                        if (p >= n || data[p] == (byte)'}') break;
                        if (data[p] == (byte)',') { p++; continue; }
                        ParseString(p);
                        int cs = sVal, ce = eVal; bool cesc = escVal;
                        p = SkipWS(sNext);
                        p++; // ':'
                        p = SkipWS(p);
                        bool neg = data[p] == (byte)'-';
                        if (neg) p++;
                        long rate = 0;
                        while (p < n && data[p] >= (byte)'0' && data[p] <= (byte)'9')
                        {
                            rate = rate * 10 + (data[p] - (byte)'0');
                            p++;
                        }
                        if (neg) rate = -rate;
                        MakeKey(cs, ce, cesc);
                        rates.b[rates.FindOrInsert(keyArr, keyOff, keyLen)] = rate;
                    }
                    p++; // '}'
                }
                else
                {
                    p = SkipValue(p);
                }
            }
        }
        i = eol < n ? eol + 1 : n;

        long totalCount = 0, totalNet = 0;
        while (i < n)
        {
            int q = SkipWS(i);
            eol = IndexOf(i, (byte)'\n');
            if (eol < 0) eol = n;
            if (q < eol && data[q] == (byte)'{')
            {
                q++;
                long sign = 0, rate = 0, amount = 0;
                bool hasRate = false;
                int accS = -1, accE = 0, chanS = -1, chanE = 0;
                bool accEsc = false, chanEsc = false, isTest = false;
                while (true)
                {
                    q = SkipWS(q);
                    if (q >= n || data[q] == (byte)'}') { q++; break; }
                    if (data[q] == (byte)',') { q++; continue; }
                    ParseString(q);
                    int ks = sVal, ke = eVal; bool kesc = escVal;
                    q = SkipWS(sNext);
                    q++; // ':'
                    q = SkipWS(q);
                    if (!kesc)
                    {
                        int kl = ke - ks;
                        byte k0 = kl > 0 ? data[ks] : (byte)0;
                        if (k0 == (byte)'t' && kl == 4 && data[ks + 1] == (byte)'y'
                            && data[ks + 2] == (byte)'p' && data[ks + 3] == (byte)'e')
                        {
                            ParseString(q);
                            int vs = sVal, ve = eVal; bool vesc = escVal;
                            q = sNext;
                            if (StrEq(vs, ve, vesc, "credit") || StrEq(vs, ve, vesc, "refund")) sign = 1;
                            else if (StrEq(vs, ve, vesc, "debit")) sign = -1;
                            continue;
                        }
                        else if (k0 == (byte)'a' && kl == 6 && data[ks + 1] == (byte)'m'
                            && data[ks + 2] == (byte)'o' && data[ks + 3] == (byte)'u'
                            && data[ks + 4] == (byte)'n' && data[ks + 5] == (byte)'t')
                        {
                            ParseString(q);
                            int vs = sVal, ve = eVal;
                            q = sNext;
                            amount = ParseAmount(vs, ve);
                            continue;
                        }
                        else if (k0 == (byte)'c' && kl == 8 && data[ks + 1] == (byte)'u'
                            && data[ks + 2] == (byte)'r' && data[ks + 3] == (byte)'r'
                            && data[ks + 4] == (byte)'e' && data[ks + 5] == (byte)'n'
                            && data[ks + 6] == (byte)'c' && data[ks + 7] == (byte)'y')
                        {
                            ParseString(q);
                            int vs = sVal, ve = eVal; bool vesc = escVal;
                            q = sNext;
                            MakeKey(vs, ve, vesc);
                            int ri = rates.Find(keyArr, keyOff, keyLen);
                            hasRate = ri >= 0;
                            if (hasRate) rate = rates.b[ri];
                            continue;
                        }
                        else if (k0 == (byte)'a' && kl == 7 && data[ks + 1] == (byte)'c'
                            && data[ks + 2] == (byte)'c' && data[ks + 3] == (byte)'o'
                            && data[ks + 4] == (byte)'u' && data[ks + 5] == (byte)'n'
                            && data[ks + 6] == (byte)'t')
                        {
                            ParseString(q);
                            accS = sVal; accE = eVal; accEsc = escVal;
                            q = sNext;
                            continue;
                        }
                        else if (k0 == (byte)'t' && kl == 4 && data[ks + 1] == (byte)'a'
                            && data[ks + 2] == (byte)'g' && data[ks + 3] == (byte)'s')
                        {
                            q++; // '['
                            while (true)
                            {
                                q = SkipWS(q);
                                if (q >= n || data[q] == (byte)']') { q++; break; }
                                if (data[q] == (byte)',') { q++; continue; }
                                if (data[q] == (byte)'"')
                                {
                                    ParseString(q);
                                    int vs = sVal, ve = eVal; bool vesc = escVal;
                                    q = sNext;
                                    if (!isTest && StrEq(vs, ve, vesc, "test")) isTest = true;
                                }
                                else
                                {
                                    q = SkipValue(q);
                                }
                            }
                            continue;
                        }
                        else if (k0 == (byte)'m' && kl == 4 && data[ks + 1] == (byte)'e'
                            && data[ks + 2] == (byte)'t' && data[ks + 3] == (byte)'a')
                        {
                            q++; // '{'
                            while (true)
                            {
                                q = SkipWS(q);
                                if (q >= n || data[q] == (byte)'}') { q++; break; }
                                if (data[q] == (byte)',') { q++; continue; }
                                ParseString(q);
                                int mks = sVal, mke = eVal; bool mkesc = escVal;
                                q = SkipWS(sNext);
                                q++; // ':'
                                q = SkipWS(q);
                                if (StrEq(mks, mke, mkesc, "channel"))
                                {
                                    ParseString(q);
                                    chanS = sVal; chanE = eVal; chanEsc = escVal;
                                    q = sNext;
                                }
                                else
                                {
                                    q = SkipValue(q);
                                }
                            }
                            continue;
                        }
                    }
                    q = SkipValue(q);
                }
                if (sign != 0 && !isTest && hasRate && accS >= 0 && chanS >= 0)
                {
                    long val = sign * ((amount * rate) / 1_000_000L);
                    totalCount++;
                    totalNet += val;
                    MakeKey(chanS, chanE, chanEsc);
                    int ci = channels.FindOrInsert(keyArr, keyOff, keyLen);
                    channels.a[ci]++;
                    channels.b[ci] += val;
                    MakeKey(accS, accE, accEsc);
                    int ai = accounts.FindOrInsert(keyArr, keyOff, keyLen);
                    accounts.b[ai] += val;
                }
            }
            i = eol < n ? eol + 1 : n;
        }

        // ---- output ----
        byte[] buf = new byte[1 << 16];
        int len = 0;
        void Ensure(int extra)
        {
            if (len + extra > buf.Length) Array.Resize(ref buf, Math.Max(buf.Length * 2, len + extra));
        }
        void Put(string s)
        {
            Ensure(s.Length);
            foreach (char c in s) buf[len++] = (byte)c;
        }
        void PutLong(long v) { Ensure(24); AppendLong(buf, ref len, v); }

        Put("counted "); PutLong(totalCount); Put("\nnet "); PutLong(totalNet); Put("\n");

        // Channel lines sorted by name ascending (byte order).
        int nc = channels.size;
        int[] cIdx = new int[nc];
        for (int e = 0; e < nc; e++) cIdx[e] = e;
        Array.Sort(cIdx, (x, y) =>
        {
            int lx = channels.keyLen[x], ly = channels.keyLen[y];
            int ox = channels.keyOff[x], oy = channels.keyOff[y];
            int m = Math.Min(lx, ly);
            for (int k = 0; k < m; k++)
            {
                int d = channels.pool[ox + k] - channels.pool[oy + k];
                if (d != 0) return d;
            }
            return lx - ly;
        });
        foreach (int e in cIdx)
        {
            Put("channel ");
            Put(Encoding.Latin1.GetString(channels.pool, channels.keyOff[e], channels.keyLen[e]));
            Put(" "); PutLong(channels.a[e]); Put(" "); PutLong(channels.b[e]); Put("\n");
        }

        // Top 10 accounts by net desc, then id asc.
        int na = accounts.size;
        int take = Math.Min(10, na);
        int[] best = new int[take];
        int bestCount = 0;
        for (int e = 0; e < na; e++)
        {
            if (bestCount < take)
            {
                best[bestCount++] = e;
                continue;
            }
            int worst = 0;
            for (int j = 1; j < take; j++)
                if (AccountBetter(accounts, best[worst], best[j])) worst = j;
            if (AccountBetter(accounts, e, best[worst])) best[worst] = e;
        }
        Array.Sort(best, 0, bestCount, Comparer<int>.Create((x, y) =>
            AccountBetter(accounts, x, y) ? -1 : AccountBetter(accounts, y, x) ? 1 : 0));
        for (int k = 0; k < bestCount; k++)
        {
            int e = best[k];
            Put("account ");
            Put(Encoding.Latin1.GetString(accounts.pool, accounts.keyOff[e], accounts.keyLen[e]));
            Put(" "); PutLong(accounts.b[e]); Put("\n");
        }

        using var so = Console.OpenStandardOutput();
        so.Write(buf, 0, len);
    }
}
