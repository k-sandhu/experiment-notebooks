using System;
using System.IO;
using System.Numerics;
using System.Runtime.CompilerServices;

internal static class Program
{
    private static long ReadNumber(byte[] input, ref int position)
    {
        while (input[position] <= 32)
            position++;

        long value = 0;
        while (position < input.Length)
        {
            uint digit = (uint)(input[position] - (byte)'0');
            if (digit > 9)
                break;

            value = value * 10 + digit;
            position++;
        }

        return value;
    }

    private static unsafe void Main(string[] args)
    {
        byte[] input = File.ReadAllBytes(args[0]);
        int position = 0;
        int height = (int)ReadNumber(input, ref position);
        int width = (int)ReadNumber(input, ref position);
        long steps = ReadNumber(input, ref position);

        int stride = width + 2;
        int length = (height + 2) * stride;

        byte[] kinds = new byte[length];
        int[] first = new int[length];
        int[] second = new int[length];
        int[] coefficients = new int[length];
        int[] masks = new int[length];

        bool hasSource = false;

        for (int row = 0; row < height; row++)
        {
            while (input[position] <= 32)
                position++;

            int index = (row + 1) * stride + 1;
            for (int column = 0; column < width; column++, index++)
            {
                byte cell = input[position++];

                if (cell == (byte)'.')
                {
                    kinds[index] = 1;
                    masks[index] = -1;
                }
                else if (cell != (byte)'#')
                {
                    kinds[index] = 2;
                    int value = (cell - (byte)'0') * 1000;
                    first[index] = value;
                    second[index] = value;
                    hasSource = true;
                }
            }
        }

        int start = stride + 1;
        int end = (height + 1) * stride - 1;

        for (int index = start; index < end; index++)
        {
            if (masks[index] == 0)
                continue;

            coefficients[index] =
                4 +
                (kinds[index - stride] == 0 ? 1 : 0) +
                (kinds[index + stride] == 0 ? 1 : 0) +
                (kinds[index - 1] == 0 ? 1 : 0) +
                (kinds[index + 1] == 0 ? 1 : 0);
        }

        if (!hasSource)
            steps = 0;

        long sum = 0;
        long checksum = 0;
        int maximum = -1;
        int maximumRow = 0;
        int maximumColumn = 0;

        fixed (int* firstPointer = first)
        fixed (int* secondPointer = second)
        fixed (int* coefficientPointer = coefficients)
        fixed (int* maskPointer = masks)
        {
            int* current = firstPointer;
            int* next = secondPointer;

            int vectorWidth = Vector<int>.Count;
            int vectorEnd = Vector.IsHardwareAccelerated
                ? end - vectorWidth + 1
                : start;

            for (long step = 0; step < steps; step++)
            {
                int index = start;

                for (; index < vectorEnd; index += vectorWidth)
                {
                    Vector<int> center =
                        Unsafe.ReadUnaligned<Vector<int>>(current + index);

                    Vector<int> total =
                        center * Unsafe.ReadUnaligned<Vector<int>>(
                            coefficientPointer + index);

                    total += Unsafe.ReadUnaligned<Vector<int>>(
                        current + index - stride);
                    total += Unsafe.ReadUnaligned<Vector<int>>(
                        current + index + stride);
                    total += Unsafe.ReadUnaligned<Vector<int>>(
                        current + index - 1);
                    total += Unsafe.ReadUnaligned<Vector<int>>(
                        current + index + 1);

                    Vector<int> updated = Vector.ShiftRightLogical(total, 3);
                    Vector<int> mask =
                        Unsafe.ReadUnaligned<Vector<int>>(maskPointer + index);

                    updated = Vector.ConditionalSelect(mask, updated, center);
                    Unsafe.WriteUnaligned(next + index, updated);
                }

                for (; index < end; index++)
                {
                    if (maskPointer[index] != 0)
                    {
                        next[index] =
                            (coefficientPointer[index] * current[index] +
                             current[index - stride] +
                             current[index + stride] +
                             current[index - 1] +
                             current[index + 1]) >> 3;
                    }
                }

                int* temporary = current;
                current = next;
                next = temporary;
            }

            for (int row = 0; row < height; row++)
            {
                int index = (row + 1) * stride + 1;
                long weight = (long)row * width + 1;

                for (int column = 0; column < width; column++, index++, weight++)
                {
                    if (maskPointer[index] == 0)
                        continue;

                    int value = current[index];
                    sum += value;
                    checksum += value * weight;

                    if (value > maximum)
                    {
                        maximum = value;
                        maximumRow = row;
                        maximumColumn = column;
                    }
                }
            }
        }

        Console.Write(
            $"sum {sum}\nmax {maximum} {maximumRow} {maximumColumn}\nchecksum {checksum}\n");
    }
}
