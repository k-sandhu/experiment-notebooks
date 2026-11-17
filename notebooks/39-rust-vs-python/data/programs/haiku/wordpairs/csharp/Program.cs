using System;
using System.IO;
using System.Text;

// Counts adjacent word pairs within sentences and prints the 20 most frequent ones (see SPEC.md).
//
// One pass over the whole input: letters form words, which are looked up in an open-addressing
// vocabulary table; each pair of neighbouring words is counted in an open-addressing table of
// struct slots. The scan uses pointers to avoid bounds checks.
internal static unsafe class Program
{
    // Byte classes.
    private const byte Separator = 0;
    private const byte Letter = 1;
    private const byte SentenceEnd = 2;

    private const uint FnvOffset = 0x811C9DC5u;
    private const uint FnvPrime = 0x01000193u;
    private const int NoWord = -1;
    private const int Top = 20;

    private static readonly byte[] ClassTable = BuildClassTable();

    private static byte[] BuildClassTable()
    {
        var table = new byte[256];
        for (int c = 'A'; c <= 'Z'; c++)
        {
            table[c] = Letter;
            table[c + 32] = Letter;
        }
        table['.'] = SentenceEnd;
        table['!'] = SentenceEnd;
        table['?'] = SentenceEnd;
        return table;
    }

    internal static int MixPair(int a, int b)
    {
        uint h = ((uint)a * 0x9E3779B1u) ^ (uint)b;
        h ^= h >> 16;
        h *= 0x85EBCA6Bu;
        h ^= h >> 13;
        return (int)h;
    }

    // One pair-table slot; C == 0 marks an empty slot.
    internal struct Slot
    {
        public int A;
        public int B;
        public int C;
    }

    // Counts ordered pairs of word ids.
    internal sealed class PairCounter
    {
        private const int InitialSlots = 1 << 20;

        private Slot[] _slots = new Slot[InitialSlots];
        private int _mask = InitialSlots - 1;
        private long _distinct;

        public long Distinct => _distinct;

        public Slot[] Slots => _slots;

        public void Add(int a, int b)
        {
            int idx = MixPair(a, b) & _mask;
            while (true)
            {
                ref Slot s = ref _slots[idx];
                if (s.C == 0)
                {
                    s.A = a;
                    s.B = b;
                    s.C = 1;
                    if (++_distinct * 4 > (_mask + 1L) * 3)
                    {
                        Grow();
                    }
                    return;
                }
                if (s.A == a && s.B == b)
                {
                    s.C++;
                    return;
                }
                idx = (idx + 1) & _mask;
            }
        }

        private void Grow()
        {
            var bigger = new Slot[_slots.Length * 2];
            int m = bigger.Length - 1;
            foreach (Slot s in _slots)
            {
                if (s.C == 0)
                {
                    continue;
                }
                int idx = MixPair(s.A, s.B) & m;
                while (bigger[idx].C != 0)
                {
                    idx = (idx + 1) & m;
                }
                bigger[idx] = s;
            }
            _slots = bigger;
            _mask = m;
        }
    }

    // Maps lower-cased words to dense ids in first-seen order.
    internal sealed class Vocab
    {
        private int[] _table = new int[1 << 16]; // id + 1, 0 = empty
        private uint[] _hashes = new uint[1024];
        private string[] _words = new string[1024];
        private int _count;

        public int Count => _count;

        public string Word(int id) => _words[id];

        // p[0..len) holds letters in either case; h is the FNV-1a hash of their lower-case form.
        public int Find(byte* p, int len, uint h)
        {
            int mask = _table.Length - 1;
            int idx = (int)(h & (uint)mask);
            int v;
            while ((v = _table[idx]) != 0)
            {
                int id = v - 1;
                if (_hashes[id] == h && SameFolded(_words[id], p, len))
                {
                    return id;
                }
                idx = (idx + 1) & mask;
            }

            int newId = _count;
            var chars = new char[len];
            for (int j = 0; j < len; j++)
            {
                chars[j] = (char)(p[j] | 0x20);
            }
            if (newId == _words.Length)
            {
                Array.Resize(ref _words, newId * 2);
                Array.Resize(ref _hashes, newId * 2);
            }
            _words[newId] = new string(chars);
            _hashes[newId] = h;
            _table[idx] = newId + 1;
            _count = newId + 1;
            if (_count * 2L > _table.Length)
            {
                Rehash();
            }
            return newId;
        }

        private static bool SameFolded(string w, byte* p, int len)
        {
            if (w.Length != len)
            {
                return false;
            }
            for (int j = 0; j < len; j++)
            {
                if (w[j] != (p[j] | 0x20))
                {
                    return false;
                }
            }
            return true;
        }

        private void Rehash()
        {
            var bigger = new int[_table.Length * 2];
            int mask = bigger.Length - 1;
            for (int id = 0; id < _count; id++)
            {
                int idx = (int)(_hashes[id] & (uint)mask);
                while (bigger[idx] != 0)
                {
                    idx = (idx + 1) & mask;
                }
                bigger[idx] = id + 1;
            }
            _table = bigger;
        }
    }

    // Entry k of a top list: count, first id, second id (stored in a Slot).
    private static bool Better(Slot[] top, int x, int y, int[] rank)
    {
        if (top[x].C != top[y].C)
        {
            return top[x].C > top[y].C;
        }
        int ax = rank[top[x].A];
        int ay = rank[top[y].A];
        if (ax != ay)
        {
            return ax < ay;
        }
        return rank[top[x].B] < rank[top[y].B];
    }

    private static int Main(string[] args)
    {
        if (args.Length < 1)
        {
            Console.Error.WriteLine("usage: solution INPUT_PATH");
            return 2;
        }
        byte[] buf = File.ReadAllBytes(args[0]);
        var vocab = new Vocab();
        var pairs = new PairCounter();
        long words = 0;
        long total = 0;
        int prev = NoWord;
        int n = buf.Length;

        fixed (byte* p = buf)
        fixed (byte* cls = ClassTable)
        {
            int i = 0;
            while (i < n)
            {
                byte c = cls[p[i]];
                if (c == Letter)
                {
                    int start = i;
                    uint h = FnvOffset;
                    do
                    {
                        h = (h ^ (uint)(p[i] | 0x20)) * FnvPrime;
                        i++;
                    }
                    while (i < n && cls[p[i]] == Letter);
                    int id = vocab.Find(p + start, i - start, h);
                    words++;
                    if (prev != NoWord)
                    {
                        pairs.Add(prev, id);
                        total++;
                    }
                    prev = id;
                }
                else
                {
                    if (c == SentenceEnd)
                    {
                        prev = NoWord;
                    }
                    i++;
                }
            }
        }

        // Rank words by byte order so ties can be broken with integer comparisons.
        int vocabSize = vocab.Count;
        var order = new int[vocabSize];
        for (int k = 0; k < vocabSize; k++)
        {
            order[k] = k;
        }
        Array.Sort(order, (x, y) => string.CompareOrdinal(vocab.Word(x), vocab.Word(y)));
        var rank = new int[vocabSize];
        for (int r = 0; r < vocabSize; r++)
        {
            rank[order[r]] = r;
        }

        var top = new Slot[Top + 1];
        int size = 0;
        foreach (Slot s in pairs.Slots)
        {
            if (s.C == 0)
            {
                continue;
            }
            int j = size;
            top[j] = s;
            if (size == Top && !Better(top, Top, Top - 1, rank))
            {
                continue;
            }
            if (size < Top)
            {
                size++;
            }
            while (j > 0 && Better(top, j, j - 1, rank))
            {
                (top[j], top[j - 1]) = (top[j - 1], top[j]);
                j--;
            }
        }

        var sb = new StringBuilder();
        sb.Append("words ").Append(words).Append('\n');
        sb.Append("pairs ").Append(total).Append('\n');
        sb.Append("distinct ").Append(pairs.Distinct).Append('\n');
        for (int r = 0; r < size; r++)
        {
            sb.Append(top[r].C).Append(' ')
              .Append(vocab.Word(top[r].A)).Append(' ')
              .Append(vocab.Word(top[r].B)).Append('\n');
        }
        Console.Out.Write(sb.ToString());
        Console.Out.Flush();
        return 0;
    }
}
