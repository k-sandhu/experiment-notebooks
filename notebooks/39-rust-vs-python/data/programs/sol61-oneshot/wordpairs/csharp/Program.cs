using System;
using System.IO;
using System.Text;
using System.Runtime.CompilerServices;

internal static class Program
{
    private struct Word
    {
        public uint Hash;
        public int Start;
        public int Length;
    }

    private sealed class WordTable
    {
        private readonly byte[] text;
        private int[] buckets = new int[8192];
        private Word[] words = new Word[4096];
        private int threshold = 6144;

        public int Count { get; private set; }

        public WordTable(byte[] text)
        {
            this.text = text;
        }

        public int Intern(int start, int length, uint hash)
        {
            int mask = buckets.Length - 1;
            int index = (int)(hash & (uint)mask);

            while (true)
            {
                int id = buckets[index];
                if (id == 0)
                {
                    if (Count >= threshold)
                    {
                        Grow();
                        mask = buckets.Length - 1;
                        index = (int)(hash & (uint)mask);
                        while (buckets[index] != 0)
                            index = (index + 1) & mask;
                    }

                    id = ++Count;
                    if (id == words.Length)
                        Array.Resize(ref words, words.Length * 2);

                    words[id] = new Word
                    {
                        Hash = hash,
                        Start = start,
                        Length = length
                    };
                    buckets[index] = id;
                    return id;
                }

                ref Word word = ref words[id];
                if (word.Hash == hash &&
                    word.Length == length &&
                    text.AsSpan(start, length).SequenceEqual(
                        text.AsSpan(word.Start, length)))
                {
                    return id;
                }

                index = (index + 1) & mask;
            }
        }

        private void Grow()
        {
            int[] next = new int[buckets.Length * 2];
            int mask = next.Length - 1;

            for (int id = 1; id <= Count; id++)
            {
                int index = (int)(words[id].Hash & (uint)mask);
                while (next[index] != 0)
                    index = (index + 1) & mask;
                next[index] = id;
            }

            buckets = next;
            threshold = next.Length - next.Length / 4;
        }

        public int Compare(int first, int second)
        {
            Word a = words[first];
            Word b = words[second];
            return text.AsSpan(a.Start, a.Length).SequenceCompareTo(
                text.AsSpan(b.Start, b.Length));
        }

        public void Append(StringBuilder output, int id)
        {
            Word word = words[id];
            output.Append(Encoding.ASCII.GetString(text, word.Start, word.Length));
        }
    }

    private struct PairEntry
    {
        public ulong Key;
        public long Count;
    }

    private sealed class PairTable
    {
        private PairEntry[] entries = new PairEntry[65536];
        private int threshold = 49152;

        public int Count { get; private set; }
        public PairEntry[] Entries => entries;

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        private static uint Hash(ulong key)
        {
            key ^= key >> 33;
            key *= 0xff51afd7ed558ccdUL;
            key ^= key >> 33;
            key *= 0xc4ceb9fe1a85ec53UL;
            key ^= key >> 33;
            return (uint)key;
        }

        public void Add(ulong key)
        {
            uint hash = Hash(key);
            int mask = entries.Length - 1;
            int index = (int)(hash & (uint)mask);

            while (true)
            {
                ref PairEntry entry = ref entries[index];

                if (entry.Key == key)
                {
                    entry.Count++;
                    return;
                }

                if (entry.Key == 0)
                {
                    if (Count >= threshold)
                    {
                        Grow();
                        mask = entries.Length - 1;
                        index = (int)(hash & (uint)mask);
                        while (entries[index].Key != 0)
                            index = (index + 1) & mask;
                    }

                    entries[index].Key = key;
                    entries[index].Count = 1;
                    Count++;
                    return;
                }

                index = (index + 1) & mask;
            }
        }

        private void Grow()
        {
            PairEntry[] old = entries;
            PairEntry[] next = new PairEntry[old.Length * 2];
            int mask = next.Length - 1;

            for (int i = 0; i < old.Length; i++)
            {
                ulong key = old[i].Key;
                if (key == 0)
                    continue;

                int index = (int)(Hash(key) & (uint)mask);
                while (next[index].Key != 0)
                    index = (index + 1) & mask;

                next[index] = old[i];
            }

            entries = next;
            threshold = next.Length - next.Length / 4;
        }
    }

    private static void Main(string[] args)
    {
        byte[] text = File.ReadAllBytes(args[0]);
        var words = new WordTable(text);
        var pairs = new PairTable();

        long wordCount = 0;
        long pairCount = 0;
        int previous = 0;
        int position = 0;

        while (position < text.Length)
        {
            uint letter = (uint)((text[position] | 32) - 'a');

            if (letter <= 25)
            {
                int start = position;
                uint hash = 2166136261U;

                do
                {
                    byte lower = (byte)(letter + 'a');
                    text[position++] = lower;
                    hash = (hash ^ lower) * 16777619U;

                    if (position == text.Length)
                        break;

                    letter = (uint)((text[position] | 32) - 'a');
                }
                while (letter <= 25);

                hash ^= hash >> 16;
                int current = words.Intern(start, position - start, hash);
                wordCount++;

                if (previous != 0)
                {
                    pairs.Add(((ulong)(uint)previous << 32) | (uint)current);
                    pairCount++;
                }

                previous = current;
            }
            else
            {
                byte separator = text[position++];
                if (separator == '.' || separator == '!' || separator == '?')
                    previous = 0;
            }
        }

        var output = new StringBuilder(2048);
        output.Append("words ").Append(wordCount).Append('\n');
        output.Append("pairs ").Append(pairCount).Append('\n');
        output.Append("distinct ").Append(pairs.Count).Append('\n');

        if (pairs.Count == 0)
        {
            Console.Write(output.ToString());
            return;
        }

        int[] order = new int[words.Count];
        for (int i = 0; i < order.Length; i++)
            order[i] = i + 1;

        Array.Sort(order, words.Compare);

        int[] ranks = new int[words.Count + 1];
        for (int i = 0; i < order.Length; i++)
            ranks[order[i]] = i;

        ulong[] topKeys = new ulong[20];
        ulong[] topLex = new ulong[20];
        long[] topCounts = new long[20];
        int used = 0;

        PairEntry[] entries = pairs.Entries;
        for (int i = 0; i < entries.Length; i++)
        {
            ulong key = entries[i].Key;
            if (key == 0)
                continue;

            long count = entries[i].Count;
            if (used == 20 && count < topCounts[19])
                continue;

            int first = (int)(key >> 32);
            int second = (int)(uint)key;
            ulong lex = ((ulong)(uint)ranks[first] << 32) | (uint)ranks[second];

            if (used == 20 &&
                count == topCounts[19] &&
                lex >= topLex[19])
            {
                continue;
            }

            int at;
            if (used < 20)
                at = used++;
            else
                at = 19;

            while (at > 0 &&
                   (count > topCounts[at - 1] ||
                    (count == topCounts[at - 1] && lex < topLex[at - 1])))
            {
                topCounts[at] = topCounts[at - 1];
                topKeys[at] = topKeys[at - 1];
                topLex[at] = topLex[at - 1];
                at--;
            }

            topCounts[at] = count;
            topKeys[at] = key;
            topLex[at] = lex;
        }

        for (int i = 0; i < used; i++)
        {
            output.Append(topCounts[i]).Append(' ');
            words.Append(output, (int)(topKeys[i] >> 32));
            output.Append(' ');
            words.Append(output, (int)(uint)topKeys[i]);
            output.Append('\n');
        }

        Console.Write(output.ToString());
    }
}
