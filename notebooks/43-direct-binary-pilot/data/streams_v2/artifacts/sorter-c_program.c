#include <errno.h>
#include <stdint.h>
#include <stdlib.h>
#include <unistd.h>

static int write_all(const char *data, size_t length)
{
    while (length != 0) {
        ssize_t written = write(STDOUT_FILENO, data, length);
        if (written < 0) {
            if (errno == EINTR)
                continue;
            return -1;
        }
        if (written == 0)
            return -1;
        data += (size_t)written;
        length -= (size_t)written;
    }
    return 0;
}

static int error_result(void)
{
    (void)write_all("ERR\n", 4);
    return 2;
}

static int append_value(int32_t *values, size_t *count,
                        int has_digits, int negative, uint32_t magnitude)
{
    if (!has_digits || *count >= 128)
        return -1;

    values[*count] = negative
        ? (int32_t)(-(int64_t)magnitude)
        : (int32_t)magnitude;
    ++*count;
    return 0;
}

static int compare_values(const void *left, const void *right)
{
    int32_t a = *(const int32_t *)left;
    int32_t b = *(const int32_t *)right;
    return (a > b) - (a < b);
}

int main(void)
{
    unsigned char input[4096];
    int32_t values[128];
    size_t count = 0;
    int active = 0;
    int negative = 0;
    int has_digits = 0;
    uint32_t magnitude = 0;

    for (;;) {
        ssize_t received = read(STDIN_FILENO, input, sizeof input);
        if (received < 0) {
            if (errno == EINTR)
                continue;
            return error_result();
        }
        if (received == 0)
            break;

        for (size_t i = 0; i < (size_t)received; ++i) {
            unsigned char c = input[i];

            if (c == 0x20 || c == 0x09 || c == 0x0a) {
                if (active) {
                    if (append_value(values, &count, has_digits,
                                     negative, magnitude) != 0)
                        return error_result();
                    active = 0;
                }
                continue;
            }

            if (!active) {
                active = 1;
                negative = 0;
                has_digits = 0;
                magnitude = 0;
                if (c == '-') {
                    negative = 1;
                    continue;
                }
            }

            if (c < '0' || c > '9')
                return error_result();

            uint32_t digit = (uint32_t)(c - '0');
            uint32_t limit = negative
                ? UINT32_C(2147483648)
                : UINT32_C(2147483647);

            if (magnitude > limit / 10 ||
                (magnitude == limit / 10 && digit > limit % 10))
                return error_result();

            magnitude = magnitude * 10 + digit;
            has_digits = 1;
        }
    }

    if (active &&
        append_value(values, &count, has_digits, negative, magnitude) != 0)
        return error_result();

    qsort(values, count, sizeof values[0], compare_values);

    char output[128 * 12];
    size_t output_length = 0;

    for (size_t i = 0; i < count; ++i) {
        int64_t value = values[i];
        if (value < 0) {
            output[output_length++] = '-';
            value = -value;
        }

        char digits[10];
        size_t digit_count = 0;
        do {
            digits[digit_count++] = (char)('0' + value % 10);
            value /= 10;
        } while (value != 0);

        while (digit_count != 0)
            output[output_length++] = digits[--digit_count];

        output[output_length++] = '\n';
    }

    return write_all(output, output_length) == 0 ? 0 : 1;
}
