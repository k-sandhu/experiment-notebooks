using System;
using System.IO;
using System.Text;

internal static class Program
{
    // Open-addressing map from lowercased word bytes to id.
    static int[] wordSlots; // id + 1, 0 means empty
    static int wordMask;
    static int wordCount;
    static List<byte[]> words; // id -> lowercase word bytes

    static int WordHash(byte[] buf, int len)
    {
        uint h = 2166136261u;
        for (int i = 0; i < len; ++i)
        {
            h ^= buf[i];
            h *= 16777619u;
        }
        return (int)h;
    }

    static void GrowWords()
    {
        int[] old = wordSlots;
        int n = old.Length * 2;
        wordSlots = new int[n];
        wordMask = n - 1;
        wordCount = 0;
        foreach (int v in old)
        {
            if (v == 0) continue;
            byte[] w = words[v - 1];
            int h = WordHash(w, w.Length) & wordMask;
            while (wordSlots[h] != 0) h = (h + 1) & wordMask;
            wordSlots[h] = v;
            ++wordCount;
        }
    }

    static int Intern(byte[] buf, int len)
    {
        if (wordCount * 4 >= wordSlots.Length * 3) GrowWords();
        int h = WordHash(buf, len) & wordMask;
        while (true)
        {
            int v = wordSlots[h];
            if (v == 0)
            {
                int id = wordCount++;
                byte[] copy = new byte[len];
                Array.Copy(buf, copy, len);
                words.Add(copy);
                wordSlots[h] = id + 1;
                return id;
            }
            int wid = v - 1;
            byte[] w = words[wid];
            if (w.Length == len)
            {
                bool eq = true;
                for (int i = 0; i < len; ++i)
                {
                    if (w[i] != buf[i]) { eq = false; break; }
                }
                if (eq) return wid;
            }
            h = (h + 1) & wordMask;
        }
    }

    // Open-addressing map from packed (id1, id2) pair key to count.
    static long[] pairKeys; // -1L means empty (keys are always >= 0)
    static int[] pairCounts;
    static int pairMask;
    static int pairCount;

    static int PairHash(long k)
    {
        k ^= k >> 33;
        k *= unchecked((long)0xff51afd7ed558ccdL);
        k ^= k >> 33;
        k ^= k >> 32;
        return (int)k;
    }

    static void GrowPairs()
    {
        long[] oldK = pairKeys;
        int[] oldC = pairCounts;
        int n = oldK.Length * 2;
        pairKeys = new long[n];
        pairCounts = new int[n];
        pairMask = n - 1;
        Array.Fill(pairKeys, -1L);
        pairCount = 0;
        for (int i = 0; i < oldK.Length; ++i)
        {
            long k = oldK[i];
            if (k == -1L) continue;
            int h = PairHash(k) & pairMask;
            while (pairKeys[h] != -1L) h = (h + 1) & pairMask;
            pairKeys[h] = k;
            pairCounts[h] = oldC[i];
            ++pairCount;
        }
    }

    static int PairInsert(long key)
    {
        if ((pairCount + 1) * 4 >= pairKeys.Length * 3) GrowPairs();
        int h = PairHash(key) & pairMask;
        while (pairKeys[h] != -1L)
        {
            if (pairKeys[h] == key) return h;
            h = (h + 1) & pairMask;
        }
        pairKeys[h] = key;
        pairCounts[h] = 0;
        ++pairCount;
        return h;
    }

    static int WordCmp(byte[] x, byte[] y)
    {
        int n = x.Length < y.Length ? x.Length : y.Length;
        for (int i = 0; i < n; ++i)
        {
            if (x[i] != y[i]) return x[i] - y[i];
        }
        return x.Length - y.Length;
    }

    static int CompareEntries(Entry x, Entry y)
    {
        if (x.c != y.c) return y.c - x.c;
        int cmp = WordCmp(words[x.a], words[y.a]);
        if (cmp != 0) return cmp;
        return WordCmp(words[x.b], words[y.b]);
    }

    static long wordsCount;
    static long pairsCount;
    static int prevId = -1;

    static void NoteWord(int id)
    {
        ++wordsCount;
        if (prevId >= 0)
        {
            ++pairsCount;
            long key = ((long)prevId << 32) | (uint)id;
            int idx = PairInsert(key);
            pairCounts[idx]++;
        }
        prevId = id;
    }

    static int Main(string[] args)
    {
        byte[] data = File.ReadAllBytes(args[0]);

        wordSlots = new int[1 << 14];
        wordMask = wordSlots.Length - 1;
        wordCount = 0;
        words = new List<byte[]>();
        pairKeys = new long[1 << 16];
        pairCounts = new int[1 << 16];
        pairMask = pairKeys.Length - 1;
        pairCount = 0;
        Array.Fill(pairKeys, -1L);
        wordsCount = 0;
        pairsCount = 0;
        prevId = -1;

        byte[] buf = new byte[64];
        int blen = 0;
        for (int i = 0; i < data.Length; ++i)
        {
            int c = data[i];
            if ((c >= 65 && c <= 90) || (c >= 97 && c <= 122))
            {
                if (blen == buf.Length)
                {
                    byte[] nb = new byte[buf.Length * 2];
                    Array.Copy(buf, nb, blen);
                    buf = nb;
                }
                buf[blen++] = (byte)(c | 0x20);
            }
            else
            {
                if (blen > 0) { NoteWord(Intern(buf, blen)); blen = 0; }
                if (c == 46 || c == 33 || c == 63) prevId = -1;
            }
        }
        if (blen > 0) NoteWord(Intern(buf, blen));

        int distinct = pairCount;
        Entry[] ents = new Entry[distinct];
        int t = 0;
        for (int i = 0; i < pairKeys.Length; ++i)
        {
            long k = pairKeys[i];
            if (k != -1L)
            {
                ents[t] = new Entry { c = pairCounts[i], a = (int)(k >> 32), b = (int)k };
                ++t;
            }
        }
        Array.Sort(ents, CompareEntries);

        var sb = new StringBuilder();
        sb.Append("words ").Append(wordsCount).Append('\n');
        sb.Append("pairs ").Append(pairsCount).Append('\n');
        sb.Append("distinct ").Append(distinct).Append('\n');
        int limit = distinct < 20 ? distinct : 20;
        for (int i = 0; i < limit; ++i)
        {
            sb.Append(ents[i].c).Append(' ');
            sb.Append(Encoding.ASCII.GetString(words[ents[i].a])).Append(' ');
            sb.Append(Encoding.ASCII.GetString(words[ents[i].b])).Append('\n');
        }
        Console.Write(sb);
        return 0;
    }

    private struct Entry
    {
        public int c, a, b;
    }
}
