using System;
using System.Collections.Generic;
using System.IO;
using System.Runtime.CompilerServices;
using System.Text;

internal static class Program
{
    private const uint FnvOffset = 2166136261U;
    private const uint FnvPrime = 16777619U;

    private struct WordEntry
    {
        public uint Hash;
        public int Offset;
        public int Length;
        public int Id;
    }

    private sealed class WordTable
    {
        private WordEntry[] _entries = new WordEntry[4096];
        private int _threshold = 2867;
        private byte[] _arena = new byte[65536];
        private int _used;

        public readonly List<string> Names = new List<string>(4096) { "" };

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        private static int Bucket(uint hash, int mask)
        {
            return (int)((hash ^ (hash >> 16)) & (uint)mask);
        }

        public int GetId(byte[] input, int start, int length, uint hash)
        {
            ReadOnlySpan<byte> word = input.AsSpan(start, length);
            WordEntry[] entries = _entries;
            int mask = entries.Length - 1;
            int index = Bucket(hash, mask);

            while (true)
            {
                ref WordEntry entry = ref entries[index];
                if (entry.Id == 0)
                    break;

                if (entry.Hash == hash &&
                    entry.Length == length &&
                    word.SequenceEqual(_arena.AsSpan(entry.Offset, length)))
                {
                    return entry.Id;
                }

                index = (index + 1) & mask;
            }

            if (Names.Count - 1 >= _threshold)
            {
                Grow();
                entries = _entries;
                mask = entries.Length - 1;
                index = Bucket(hash, mask);
                while (entries[index].Id != 0)
                    index = (index + 1) & mask;
            }

            int required = checked(_used + length);
            if (required > _arena.Length)
            {
                int capacity = (int)Math.Min(
                    Array.MaxLength,
                    Math.Max((long)required, (long)_arena.Length * 2));
                Array.Resize(ref _arena, capacity);
            }

            int id = Names.Count;
            Names.Add(Encoding.ASCII.GetString(word));
            word.CopyTo(_arena.AsSpan(_used, length));

            entries[index] = new WordEntry
            {
                Hash = hash,
                Offset = _used,
                Length = length,
                Id = id
            };

            _used = required;
            return id;
        }

        private void Grow()
        {
            WordEntry[] oldEntries = _entries;
            WordEntry[] newEntries =
                new WordEntry[checked(oldEntries.Length * 2)];
            int mask = newEntries.Length - 1;

            for (int i = 0; i < oldEntries.Length; i++)
            {
                ref WordEntry entry = ref oldEntries[i];
                if (entry.Id == 0)
                    continue;

                int index = Bucket(entry.Hash, mask);
                while (newEntries[index].Id != 0)
                    index = (index + 1) & mask;

                newEntries[index] = entry;
            }

            _entries = newEntries;
            _threshold = (int)(newEntries.Length * 7L / 10);
        }
    }

    private struct PairEntry
    {
        public ulong Key;
        public long Count;
    }

    private sealed class PairTable
    {
        public PairEntry[] Entries = new PairEntry[65536];
        public int Distinct;

        private int _threshold = 45875;

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        private static uint Hash(ulong key)
        {
            unchecked
            {
                key ^= key >> 33;
                key *= 0xff51afd7ed558ccdUL;
                key ^= key >> 33;
                key *= 0xc4ceb9fe1a85ec53UL;
                key ^= key >> 33;
                return (uint)key;
            }
        }

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public void Add(ulong key)
        {
            PairEntry[] entries = Entries;
            int mask = entries.Length - 1;
            uint hash = Hash(key);
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
                    break;

                index = (index + 1) & mask;
            }

            if (Distinct >= _threshold)
            {
                Grow();
                entries = Entries;
                mask = entries.Length - 1;
                index = (int)(hash & (uint)mask);

                while (entries[index].Key != 0)
                    index = (index + 1) & mask;
            }

            entries[index].Key = key;
            entries[index].Count = 1;
            Distinct++;
        }

        private void Grow()
        {
            PairEntry[] oldEntries = Entries;
            PairEntry[] newEntries =
                new PairEntry[checked(oldEntries.Length * 2)];
            int mask = newEntries.Length - 1;

            for (int i = 0; i < oldEntries.Length; i++)
            {
                ref PairEntry entry = ref oldEntries[i];
                if (entry.Key == 0)
                    continue;

                int index = (int)(Hash(entry.Key) & (uint)mask);
                while (newEntries[index].Key != 0)
                    index = (index + 1) & mask;

                newEntries[index] = entry;
            }

            Entries = newEntries;
            _threshold = (int)(newEntries.Length * 7L / 10);
        }
    }

    private sealed class Counter
    {
        public readonly WordTable Vocabulary = new WordTable();
        public readonly PairTable PairCounts = new PairTable();

        public long Words;
        public long Pairs;
        public int Previous;

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public void AcceptWord(byte[] buffer, int start, int length, uint hash)
        {
            int id = Vocabulary.GetId(buffer, start, length, hash);
            Words++;

            if (Previous != 0)
            {
                ulong key = ((ulong)(uint)Previous << 32) | (uint)id;
                PairCounts.Add(key);
                Pairs++;
            }

            Previous = id;
        }
    }

    private struct Result
    {
        public ulong Key;
        public ulong LexicalOrder;
        public long Count;
    }

    public static void Main(string[] args)
    {
        var counter = new Counter();
        ReadInput(args[0], counter);
        WriteOutput(counter);
    }

    private static unsafe void ReadInput(string path, Counter counter)
    {
        using var stream = new FileStream(
            path,
            FileMode.Open,
            FileAccess.Read,
            FileShare.Read,
            bufferSize: 1,
            options: FileOptions.SequentialScan);

        // The extra byte is a non-letter sentinel.
        byte[] buffer = new byte[(1 << 20) + 1];
        int carry = 0;
        uint carryHash = FnvOffset;

        while (true)
        {
            int capacity = buffer.Length - 1;
            if (carry == capacity)
            {
                int newCapacity = (int)Math.Min(
                    Array.MaxLength - 1L, (long)capacity * 2);

                if (newCapacity <= capacity)
                    throw new OutOfMemoryException();

                Array.Resize(ref buffer, newCapacity + 1);
                capacity = newCapacity;
            }

            int read = stream.Read(buffer, carry, capacity - carry);
            if (read == 0)
            {
                if (carry != 0)
                    counter.AcceptWord(buffer, 0, carry, carryHash);
                break;
            }

            int end = carry + read;
            buffer[end] = 0;

            fixed (byte* data = buffer)
            {
                byte* p = data + carry;
                byte* endPointer = data + end;
                byte* wordStart = data;
                uint hash = carryHash;
                bool continuing = carry != 0;
                carry = 0;

                while (p < endPointer)
                {
                    if (!continuing)
                    {
                        while (p < endPointer)
                        {
                            uint c = (uint)(*p | 32);
                            if (c - (uint)'a' <= 25U)
                                break;

                            if (c == '.' || c == '!' || c == '?')
                                counter.Previous = 0;

                            p++;
                        }

                        if (p == endPointer)
                            break;

                        wordStart = p;
                        hash = FnvOffset;
                    }

                    continuing = false;

                    while (true)
                    {
                        uint c = (uint)(*p | 32);
                        if (c - (uint)'a' > 25U)
                            break;

                        *p = (byte)c;
                        hash = unchecked((hash ^ c) * FnvPrime);
                        p++;
                    }

                    if (p == endPointer)
                    {
                        carry = (int)(p - wordStart);
                        carryHash = hash;

                        if (wordStart != data)
                        {
                            buffer.AsSpan((int)(wordStart - data), carry)
                                  .CopyTo(buffer.AsSpan(0, carry));
                        }

                        break;
                    }

                    counter.AcceptWord(
                        buffer,
                        (int)(wordStart - data),
                        (int)(p - wordStart),
                        hash);
                }
            }
        }
    }

    private static void WriteOutput(Counter counter)
    {
        var output = new StringBuilder();
        output.Append("words ").Append(counter.Words).Append('\n');
        output.Append("pairs ").Append(counter.Pairs).Append('\n');
        output.Append("distinct ").Append(counter.PairCounts.Distinct).Append('\n');

        if (counter.PairCounts.Distinct == 0)
        {
            Console.Write(output.ToString());
            return;
        }

        List<string> names = counter.Vocabulary.Names;
        int vocabularySize = names.Count - 1;
        int[] sortedIds = new int[vocabularySize];

        for (int i = 0; i < sortedIds.Length; i++)
            sortedIds[i] = i + 1;

        Array.Sort(
            sortedIds,
            (a, b) => string.CompareOrdinal(names[a], names[b]));

        int[] ranks = new int[names.Count];
        for (int i = 0; i < sortedIds.Length; i++)
            ranks[sortedIds[i]] = i;

        Result[] best = new Result[20];
        int size = 0;
        PairEntry[] entries = counter.PairCounts.Entries;

        for (int i = 0; i < entries.Length; i++)
        {
            ref PairEntry entry = ref entries[i];
            if (entry.Key == 0)
                continue;

            long count = entry.Count;
            if (size == 20 && count < best[19].Count)
                continue;

            int first = (int)(entry.Key >> 32);
            int second = (int)(uint)entry.Key;
            ulong lexicalOrder =
                ((ulong)(uint)ranks[first] << 32) | (uint)ranks[second];

            if (size == 20 &&
                count == best[19].Count &&
                lexicalOrder >= best[19].LexicalOrder)
            {
                continue;
            }

            int position = size < 20 ? size : 19;
            while (position > 0)
            {
                ref Result previous = ref best[position - 1];

                if (count < previous.Count ||
                    (count == previous.Count &&
                     lexicalOrder >= previous.LexicalOrder))
                {
                    break;
                }

                best[position] = previous;
                position--;
            }

            best[position] = new Result
            {
                Key = entry.Key,
                Count = count,
                LexicalOrder = lexicalOrder
            };

            if (size < 20)
                size++;
        }

        for (int i = 0; i < size; i++)
        {
            Result result = best[i];
            int first = (int)(result.Key >> 32);
            int second = (int)(uint)result.Key;

            output.Append(result.Count).Append(' ')
                  .Append(names[first]).Append(' ')
                  .Append(names[second]).Append('\n');
        }

        Console.Write(output.ToString());
    }
}
