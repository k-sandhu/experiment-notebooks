#include <unistd.h>
#include <errno.h>
#include <stdint.h>
#include <stddef.h>
#include <string.h>

static void write_all(const char *data, size_t length)
{
    while (length > 0) {
        ssize_t n = write(STDOUT_FILENO, data, length);
        if (n > 0) {
            data += (size_t)n;
            length -= (size_t)n;
        } else if (n < 0 && errno == EINTR) {
            continue;
        } else {
            return;
        }
    }
}

static int fail(void)
{
    write_all("ERR\n", 4);
    return 2;
}

static int is_digit(unsigned char c)
{
    return c >= '0' && c <= '9';
}

static size_t append_decimal(char *out, size_t pos, uint64_t value)
{
    char reversed[20];
    size_t count = 0;

    do {
        reversed[count++] = (char)('0' + value % 10);
        value /= 10;
    } while (value != 0);

    while (count > 0)
        out[pos++] = reversed[--count];

    return pos;
}

int main(void)
{
    static const char header[] = "account,amount_cents\n";
    unsigned char input[4097];
    int64_t totals[64] = {0};
    unsigned char seen[64] = {0};
    size_t length = 0;
    size_t pos;
    unsigned int records = 0;
    char output[2048];
    size_t output_length = 0;

    for (;;) {
        ssize_t n = read(STDIN_FILENO, input + length,
                         sizeof(input) - length);
        if (n > 0) {
            length += (size_t)n;
            if (length > 4096)
                return fail();
        } else if (n == 0) {
            break;
        } else if (errno != EINTR) {
            return fail();
        }
    }

    if (length < sizeof(header) - 1 ||
        memcmp(input, header, sizeof(header) - 1) != 0)
        return fail();

    pos = sizeof(header) - 1;

    while (pos < length) {
        unsigned int account = 0;
        uint64_t amount = 0;
        int negative = 0;

        if (records == 128)
            return fail();

        if (!is_digit(input[pos]))
            return fail();

        do {
            unsigned int digit = (unsigned int)(input[pos] - '0');
            if (account > 6 || (account == 6 && digit > 3))
                return fail();
            account = account * 10 + digit;
            ++pos;
        } while (pos < length && is_digit(input[pos]));

        if (pos == length || input[pos] != ',')
            return fail();
        ++pos;

        if (pos < length && input[pos] == '-') {
            negative = 1;
            ++pos;
        }

        if (pos == length || !is_digit(input[pos]))
            return fail();

        do {
            unsigned int digit = (unsigned int)(input[pos] - '0');
            if (amount > 100000000ULL ||
                (amount == 100000000ULL && digit != 0))
                return fail();
            amount = amount * 10 + digit;
            ++pos;
        } while (pos < length && is_digit(input[pos]));

        if (pos < length) {
            if (input[pos] != '\n')
                return fail();
            ++pos;
        }

        totals[account] += negative ? -(int64_t)amount : (int64_t)amount;
        seen[account] = 1;
        ++records;
    }

    for (unsigned int account = 0; account < 64; ++account) {
        int64_t total;
        uint64_t magnitude;

        if (!seen[account])
            continue;

        output_length = append_decimal(output, output_length, account);
        output[output_length++] = ',';

        total = totals[account];
        if (total < 0) {
            output[output_length++] = '-';
            magnitude = (uint64_t)(-total);
        } else {
            magnitude = (uint64_t)total;
        }

        output_length = append_decimal(output, output_length, magnitude);
        output[output_length++] = '\n';
    }

    write_all(output, output_length);
    return 0;
}
