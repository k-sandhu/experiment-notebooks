// Word pairs benchmark - C# 12, .NET 8, unsafe scanning.
// Single pass: lowercase words in place, intern them to ids, emit packed
// (prevId, curId) pairs within sentences, sort the packed pairs, count runs,
// keep the top 20 by (count desc, word1 asc, word2 asc).
using System;
using System.Collections.Generic;
using System.IO;
using System.Text;

class Program
{
    static bool IsLetter(byte c)
    {
        c = (byte)(c | 0x20);
        return c >= (byte)'a' && c <= (byte)'z';
    }

    // Open-addressing map from lowercase word to a dense id.
    // Lookup compares against the input buffer region directly, so only
    // distinct words are turned into string objects.
    sealed class WordMap
    {
        string[] keys;
        int[] hashes;
        int[] ids;
        int mask;
        int occupied;
        int growAt;
        readonly List<string> words; // id -> word

        public WordMap(int cap)
        {
            keys = new string[cap];
            hashes = new int[cap];
            ids = new int[cap];
            mask = cap - 1;
            growAt = (int)(cap * 0.75);
            words = new List<string>(cap);
        }

        public List<string> Words => words;

        void Grow()
        {
            string[] oldKeys = keys;
            int[] oldHashes = hashes;
            int[] oldIds = ids;
            int newCap = oldKeys.Length * 2;
            keys = new string[newCap];
            hashes = new int[newCap];
            ids = new int[newCap];
            mask = newCap - 1;
            growAt = (int)(newCap * 0.75);
            for (int i = 0; i < oldKeys.Length; i++)
            {
                string k = oldKeys[i];
                if (k != null)
                {
                    int h = oldHashes[i] & mask;
                    int pos = h;
                    while (keys[pos] != null) pos = (pos + 1) & mask;
                    keys[pos] = k;
                    hashes[pos] = oldHashes[i];
                    ids[pos] = oldIds[i];
                }
            }
        }

        static int HashBytes(byte[] data, int start, int len)
        {
            int h = unchecked((int)2166136261);
            for (int i = 0; i < len; i++) h = (h * 16777619) ^ data[start + i];
            return h;
        }

        static bool EqualsBytes(string k, byte[] data, int start, int len)
        {
            if (k.Length != len) return false;
            for (int i = 0; i < len; i++)
                if (k[i] != (char)data[start + i]) return false;
            return true;
        }

        public int GetOrPut(byte[] data, int start, int len, int hash)
        {
            int pos = hash & mask;
            while (true)
            {
                string k = keys[pos];
                if (k == null)
                {
                    string s = Encoding.ASCII.GetString(data, start, len);
                    keys[pos] = s;
                    hashes[pos] = hash;
                    ids[pos] = occupied;
                    words.Add(s);
                    int id = occupied++;
                    if (occupied >= growAt) Grow();
                    return id;
                }
                if (hashes[pos] == hash && EqualsBytes(k, data, start, len)) return ids[pos];
                pos = (pos + 1) & mask;
            }
        }
    }

    // Top-20 bookkeeping, ordered best-first.
    static long[] bestCount = new long[20];
    static int[] bestW1 = new int[20];
    static int[] bestW2 = new int[20];
    static int bestn;
    static List<string> words;

    static bool Better(long c1, int a1, int b1, long c2, int a2, int b2)
    {
        if (c1 != c2) return c1 > c2;
        int cmp = words[a1].CompareTo(words[a2]);
        if (cmp != 0) return cmp < 0;
        return words[b1].CompareTo(words[b2]) < 0;
    }

    static void Consider(long count, int w1, int w2)
    {
        if (bestn < 20)
        {
            int pos = bestn;
            while (pos > 0 && Better(count, w1, w2, bestCount[pos - 1], bestW1[pos - 1], bestW2[pos - 1]))
            {
                bestCount[pos] = bestCount[pos - 1];
                bestW1[pos] = bestW1[pos - 1];
                bestW2[pos] = bestW2[pos - 1];
                pos--;
            }
            bestCount[pos] = count;
            bestW1[pos] = w1;
            bestW2[pos] = w2;
            bestn++;
        }
        else if (Better(count, w1, w2, bestCount[19], bestW1[19], bestW2[19]))
        {
            long c = count;
            int a = w1;
            int b = w2;
            int pos = 19;
            while (pos > 0 && Better(c, a, b, bestCount[pos - 1], bestW1[pos - 1], bestW2[pos - 1]))
            {
                bestCount[pos] = bestCount[pos - 1];
                bestW1[pos] = bestW1[pos - 1];
                bestW2[pos] = bestW2[pos - 1];
                pos--;
            }
            bestCount[pos] = c;
            bestW1[pos] = a;
            bestW2[pos] = b;
        }
    }

    static int Main(string[] args)
    {
        if (args.Length < 1) return 1;
        byte[] data = File.ReadAllBytes(args[0]);
        int n = data.Length;
        var map = new WordMap(1 << 14);
        words = map.Words;
        long[] pairs = new long[1 << 20];
        int pairCount = 0;
        int prevId = 0;
        bool havePrev = false;
        long wordTotal = 0, pairTotal = 0;

        int i = 0;
        while (i < n)
        {
            while (i < n)
            {
                byte c = data[i];
                if (IsLetter(c)) break;
                if (c == '.' || c == '!' || c == '?') havePrev = false;
                i++;
            }
            if (i >= n) break;
            int start = i;
            int h = unchecked((int)2166136261);
            while (i < n)
            {
                byte c = data[i];
                if (!IsLetter(c)) break;
                if (c >= (byte)'A' && c <= (byte)'Z') c = (byte)(c + 0x20);
                data[i] = c;
                h = (h * 16777619) ^ c;
                i++;
            }
            int len = i - start;
            int id = map.GetOrPut(data, start, len, h);
            wordTotal++;
            if (havePrev)
            {
                pairTotal++;
                if (pairCount == pairs.Length)
                {
                    long[] nb = new long[pairs.Length * 2];
                    Array.Copy(pairs, 0, nb, 0, pairCount);
                    pairs = nb;
                }
                pairs[pairCount++] = ((long)prevId << 32) | (id & 0xFFFFFFFFL);
            }
            prevId = id;
            havePrev = true;
        }

        Array.Sort(pairs, 0, pairCount);

        int k = 0;
        long distinct = 0;
        while (k < pairCount)
        {
            int j = k + 1;
            while (j < pairCount && pairs[j] == pairs[k]) j++;
            Consider(j - k, (int)(pairs[k] >> 32), (int)(pairs[k] & 0xFFFFFFFFL));
            distinct++;
            k = j;
        }

        var sb = new StringBuilder();
        sb.Append("words ").Append(wordTotal).Append('\n');
        sb.Append("pairs ").Append(pairTotal).Append('\n');
        sb.Append("distinct ").Append(distinct).Append('\n');
        for (int t = 0; t < bestn; t++)
        {
            sb.Append(bestCount[t]).Append(' ').Append(words[bestW1[t]]).Append(' ').Append(words[bestW2[t]]).Append('\n');
        }
        Console.Write(sb.ToString());
        return 0;
    }
}
