#include <errno.h>
#include <stddef.h>
#include <unistd.h>

int main(void)
{
    unsigned char input[4096];
    unsigned char output[8192];
    size_t input_length = 0;
    size_t output_length = 0;

    while (input_length < sizeof input) {
        ssize_t n = read(STDIN_FILENO, input + input_length,
                         sizeof input - input_length);
        if (n > 0) {
            input_length += (size_t)n;
        } else if (n == 0) {
            break;
        } else if (errno != EINTR) {
            return 0;
        }
    }

    size_t i = 0;
    while (i < input_length) {
        unsigned char value = input[i++];
        unsigned int count = 1;

        while (i < input_length && input[i] == value && count < 255) {
            ++i;
            ++count;
        }

        output[output_length++] = (unsigned char)count;
        output[output_length++] = value;
    }

    size_t written = 0;
    while (written < output_length) {
        ssize_t n = write(STDOUT_FILENO, output + written,
                          output_length - written);
        if (n > 0) {
            written += (size_t)n;
        } else if (n < 0 && errno == EINTR) {
            continue;
        } else {
            return 0;
        }
    }

    return 0;
}
