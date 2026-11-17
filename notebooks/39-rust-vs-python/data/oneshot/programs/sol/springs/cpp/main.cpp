#include <charconv>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <fstream>
#include <iterator>
#include <string>
#include <vector>

#pragma float_control(precise, on)
#pragma fp_contract(off)

class Parser {
    const char* current_;
    const char* end_;

public:
    explicit Parser(const std::string& text)
        : current_(text.data()), end_(text.data() + text.size()) {}

    template <typename T>
    T next() {
        while (current_ != end_ &&
               static_cast<unsigned char>(*current_) <= ' ') {
            ++current_;
        }
        T value{};
        const auto result = std::from_chars(current_, end_, value);
        current_ = result.ptr;
        return value;
    }
};

static void simulate(
    std::size_t n,
    std::uint64_t steps,
    double dt,
    double circumference,
    double* __restrict x,
    double* __restrict v,
    const double* __restrict m,
    const double* __restrict k,
    const double* __restrict r,
    const double* __restrict c,
    double* __restrict force)
{
    const std::size_t last = n - 1;

    for (std::uint64_t step = 0; step < steps; ++step) {
        for (std::size_t i = 0; i < last; ++i) {
            const double stretch = (x[i + 1] - x[i]) - r[i];
            force[i + 1] = k[i] * stretch;
        }

        const double stretch =
            ((x[0] + circumference) - x[last]) - r[last];
        force[n] = k[last] * stretch;
        force[0] = force[n];

        for (std::size_t i = 0; i < n; ++i) {
            const double net =
                (force[i + 1] - force[i]) - (c[i] * v[i]);
            const double velocity = v[i] + dt * (net / m[i]);
            v[i] = velocity;
            x[i] = x[i] + dt * velocity;
        }
    }
}

int main(int argc, char* argv[]) {
    if (argc != 2) {
        return 0;
    }

    std::ifstream input(argv[1], std::ios::binary);
    if (!input) {
        return 0;
    }

    const std::string text(
        (std::istreambuf_iterator<char>(input)),
        std::istreambuf_iterator<char>());
    Parser parser(text);

    const std::size_t n = parser.next<std::size_t>();
    const std::uint64_t steps = parser.next<std::uint64_t>();
    const double dt = parser.next<double>();
    const double circumference = parser.next<double>();

    std::vector<double> x(n), v(n), m(n), k(n), r(n), c(n);
    std::vector<double> force(n + 1);

    for (std::size_t i = 0; i < n; ++i) {
        x[i] = parser.next<double>();
        v[i] = parser.next<double>();
        m[i] = parser.next<double>();
        k[i] = parser.next<double>();
        r[i] = parser.next<double>();
        c[i] = parser.next<double>();
    }

    simulate(n, steps, dt, circumference,
             x.data(), v.data(), m.data(), k.data(),
             r.data(), c.data(), force.data());

    double kinetic = 0.0;
    double potential = 0.0;
    double position = 0.0;
    double maximumSpeed = std::fabs(v[0]);
    std::size_t fastest = 0;

    for (std::size_t i = 0; i < n; ++i) {
        kinetic += ((0.5 * m[i]) * v[i]) * v[i];
        position += x[i];

        const double speed = std::fabs(v[i]);
        if (speed > maximumSpeed) {
            maximumSpeed = speed;
            fastest = i;
        }
    }

    for (std::size_t i = 0; i + 1 < n; ++i) {
        const double stretch = (x[i + 1] - x[i]) - r[i];
        potential += ((0.5 * k[i]) * stretch) * stretch;
    }

    const std::size_t last = n - 1;
    const double stretch =
        ((x[0] + circumference) - x[last]) - r[last];
    potential += ((0.5 * k[last]) * stretch) * stretch;

    std::printf("kinetic %.16e\n", kinetic);
    std::printf("potential %.16e\n", potential);
    std::printf("position %.16e\n", position);
    std::printf("fastest %zu\n", fastest);
    return 0;
}
