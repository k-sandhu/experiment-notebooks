using System;
using System.IO;
using System.Runtime.Intrinsics;
using System.Runtime.Intrinsics.X86;

internal static class Program
{
    private static int ReadInt(byte[] input, ref int position)
    {
        while (input[position] <= 32)
            position++;

        int value = 0;
        while (position < input.Length)
        {
            int digit = input[position] - (byte)'0';
            if ((uint)digit > 9)
                break;

            value = value * 10 + digit;
            position++;
        }

        return value;
    }

    private static unsafe int[] Simulate(
        int[] a, int[] b, int[] coefficients, int[] masks,
        int[] openCells, int openCount, int[] blocks, int blockCount,
        int stride, int steps)
    {
        fixed (int* pa = a)
        fixed (int* pb = b)
        fixed (int* pc = coefficients)
        fixed (int* pm = masks)
        fixed (int* po = openCells)
        fixed (int* pblocks = blocks)
        {
            int* current = pa;
            int* next = pb;

            if (Avx2.IsSupported && (long)openCount >= (long)blockCount * 3)
            {
                for (int step = 0; step < steps; step++)
                {
                    for (int j = 0; j < blockCount; j++)
                    {
                        int index = pblocks[j];
                        Vector256<int> center = Avx.LoadVector256(current + index);

                        Vector256<int> value = Avx2.MultiplyLow(
                            center, Avx.LoadVector256(pc + index));

                        value = Avx2.Add(value, Avx.LoadVector256(current + index - stride));
                        value = Avx2.Add(value, Avx.LoadVector256(current + index + stride));
                        value = Avx2.Add(value, Avx.LoadVector256(current + index - 1));
                        value = Avx2.Add(value, Avx.LoadVector256(current + index + 1));
                        value = Avx2.ShiftRightArithmetic(value, 3);

                        value = Avx2.BlendVariable(
                            center, value, Avx.LoadVector256(pm + index));

                        Avx.Store(next + index, value);
                    }

                    int* temporary = current;
                    current = next;
                    next = temporary;
                }
            }
            else
            {
                for (int step = 0; step < steps; step++)
                {
                    for (int j = 0; j < openCount; j++)
                    {
                        int index = po[j];
                        next[index] = (
                            pc[index] * current[index]
                            + current[index - stride]
                            + current[index + stride]
                            + current[index - 1]
                            + current[index + 1]) >> 3;
                    }

                    int* temporary = current;
                    current = next;
                    next = temporary;
                }
            }
        }

        return (steps & 1) == 0 ? a : b;
    }

    private static void Main(string[] args)
    {
        byte[] input = File.ReadAllBytes(args[0]);
        int position = 0;

        int height = ReadInt(input, ref position);
        int width = ReadInt(input, ref position);
        int steps = ReadInt(input, ref position);

        while (position < input.Length && input[position] <= 32)
            position++;

        int stride = width + 2;
        int length = (height + 2) * stride + 8;

        int[] a = new int[length];
        int[] b = new int[length];
        int[] masks = new int[length];
        int[] coefficients = new int[length];
        byte[] passable = new byte[length];
        int[] openCells = new int[height * width];

        int openCount = 0;
        bool hasSource = false;

        for (int row = 0; row < height; row++)
        {
            int rowStart = (row + 1) * stride + 1;

            for (int column = 0; column < width; column++)
            {
                byte cell = input[position++];
                int index = rowStart + column;

                if (cell == (byte)'.')
                {
                    passable[index] = 1;
                    masks[index] = -1;
                    openCells[openCount++] = index;
                }
                else if (cell != (byte)'#')
                {
                    passable[index] = 1;
                    int value = (cell - (byte)'0') * 1000;
                    a[index] = value;
                    b[index] = value;
                    hasSource = true;
                }
            }

            if (position < input.Length && input[position] == (byte)'\r')
                position++;
            if (position < input.Length && input[position] == (byte)'\n')
                position++;
        }

        int[] result = a;

        if (steps > 0 && hasSource)
        {
            for (int j = 0; j < openCount; j++)
            {
                int index = openCells[j];
                coefficients[index] = 8
                    - passable[index - stride]
                    - passable[index + stride]
                    - passable[index - 1]
                    - passable[index + 1];
            }

            int first = stride + 1;
            int last = height * stride + width;
            int[] blocks = new int[(last - first + 8) >> 3];

            int blockCount = 0;
            int previousBlock = -1;

            for (int j = 0; j < openCount; j++)
            {
                int block = (openCells[j] - first) >> 3;
                if (block != previousBlock)
                {
                    blocks[blockCount++] = first + (block << 3);
                    previousBlock = block;
                }
            }

            result = Simulate(
                a, b, coefficients, masks, openCells, openCount,
                blocks, blockCount, stride, steps);
        }

        long sum = 0;
        long checksum = 0;
        int maximum = -1;
        int maximumIndex = openCells[0];

        for (int j = 0; j < openCount; j++)
        {
            int index = openCells[j];
            int value = result[index];

            sum += value;

            int row = index / stride - 1;
            int column = index % stride - 1;
            checksum += (long)value * ((long)row * width + column + 1);

            if (value > maximum)
            {
                maximum = value;
                maximumIndex = index;
            }
        }

        int maximumRow = maximumIndex / stride - 1;
        int maximumColumn = maximumIndex % stride - 1;

        Console.WriteLine($"sum {sum}");
        Console.WriteLine($"max {maximum} {maximumRow} {maximumColumn}");
        Console.WriteLine($"checksum {checksum}");
    }
}
