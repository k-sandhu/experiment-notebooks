using System;
using System.IO;
using System.Text;

unsafe class Program
{
    struct Cell
    {
        public int Index;
        public int Up;
        public int Down;
        public int Left;
        public int Right;
        public int Position;
    }

    static int ReadInt(byte[] input, ref int pos)
    {
        while (pos < input.Length && input[pos] <= 32) pos++;
        int value = 0;
        while (pos < input.Length && input[pos] >= '0' && input[pos] <= '9')
        {
            value = value * 10 + input[pos] - '0';
            pos++;
        }
        return value;
    }

    static void Main(string[] args)
    {
        byte[] input = File.ReadAllBytes(args[0]);
        int pos = 0;
        int height = ReadInt(input, ref pos);
        int width = ReadInt(input, ref pos);
        int steps = ReadInt(input, ref pos);

        int stride = width + 2;
        int size = (height + 2) * stride;
        byte[] kind = new byte[size];
        int[] first = new int[size];
        int[] second = new int[size];
        int openCount = 0;

        for (int r = 0; r < height; r++)
        {
            while (pos < input.Length && input[pos] <= 32) pos++;
            int start = (r + 1) * stride + 1;
            for (int c = 0; c < width; c++)
            {
                byte ch = input[pos++];
                int index = start + c;
                if (ch == '.')
                {
                    kind[index] = 1;
                    openCount++;
                }
                else if (ch != '#')
                {
                    kind[index] = 2;
                    int value = (ch - '0') * 1000;
                    first[index] = value;
                    second[index] = value;
                }
            }
        }

        Cell[] cells = new Cell[openCount];
        int count = 0;
        for (int r = 0; r < height; r++)
        {
            int start = (r + 1) * stride + 1;
            for (int c = 0; c < width; c++)
            {
                int index = start + c;
                if (kind[index] != 1) continue;

                cells[count++] = new Cell
                {
                    Index = index,
                    Up = kind[index - stride] == 0 ? index : index - stride,
                    Down = kind[index + stride] == 0 ? index : index + stride,
                    Left = kind[index - 1] == 0 ? index : index - 1,
                    Right = kind[index + 1] == 0 ? index : index + 1,
                    Position = r * width + c
                };
            }
        }

        fixed (int* firstPtr = first)
        fixed (int* secondPtr = second)
        fixed (Cell* cellPtr = cells)
        {
            int* current = firstPtr;
            int* next = secondPtr;

            for (int step = 0; step < steps; step++)
            {
                int changed = 0;
                for (int i = 0; i < openCount; i++)
                {
                    Cell* cell = cellPtr + i;
                    int old = current[cell->Index];
                    int value = ((old << 2)
                        + current[cell->Up]
                        + current[cell->Down]
                        + current[cell->Left]
                        + current[cell->Right]) >> 3;
                    next[cell->Index] = value;
                    changed |= old ^ value;
                }

                int* temp = current;
                current = next;
                next = temp;
                if (changed == 0) break;
            }

            long sum = 0;
            long checksum = 0;
            int maximum = -1;
            int maxPosition = 0;

            for (int i = 0; i < openCount; i++)
            {
                Cell* cell = cellPtr + i;
                int value = current[cell->Index];
                sum += value;
                checksum += (long)value * (cell->Position + 1L);
                if (value > maximum)
                {
                    maximum = value;
                    maxPosition = cell->Position;
                }
            }

            var output = new StringBuilder();
            output.Append("sum ").Append(sum).Append('\n');
            output.Append("max ").Append(maximum).Append(' ')
                  .Append(maxPosition / width).Append(' ')
                  .Append(maxPosition % width).Append('\n');
            output.Append("checksum ").Append(checksum).Append('\n');
            Console.Write(output.ToString());
        }
    }
}
