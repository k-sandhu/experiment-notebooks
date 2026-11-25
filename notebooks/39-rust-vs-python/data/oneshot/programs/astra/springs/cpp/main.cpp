#include <charconv>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iterator>
#include <string>
#include <system_error>
#include <vector>

#pragma float_control(precise, on)
#pragma fp_contract(off)

class Parser {
    const char* current;
    const char* end;

    void skipWhitespace() {
        while (current != end &&
               static_cast<unsigned char>(*current) <= ' ') {
            ++current;
        }
    }

public:
    explicit Parser(const std::string& text)
        : current(text.data()), end(text.data() + text.size()) {}

    template <class T>
    T integer() {
        skipWhitespace();
        T value{};
        const auto result = std::from_chars(current, end, value);
        current = result.ptr;
        return value;
    }

    double number() {
        skipWhitespace();
        const char* start = current;
        double value = 0.0;
        const auto result =
            std::from_chars(current, end, value, std::chars_format::general);
        current = result.ptr;
        if (result.ec == std::errc::result_out_of_range) {
            value = std::strtod(start, nullptr);
        }
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
        const double wrapForce = k[last] * stretch;
        force[n] = wrapForce;
        force[0] = wrapForce;

        for (std::size_t i = 0; i < n; ++i) {
            const double netForce =
                (force[i + 1] - force[i]) - (c[i] * v[i]);
            const double newVelocity = v[i] + dt * (netForce / m[i]);
            v[i] = newVelocity;
            x[i] = x[i] + dt * newVelocity;
        }
    }
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
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

    const std::size_t n = parser.integer<std::size_t>();
    const std::uint64_t steps = parser.integer<std::uint64_t>();
    const double dt = parser.number();
    const double circumference = parser.number();

    if (n == 0) {
        return 0;
    }

    std::vector<double> x(n), v(n), m(n), k(n), r(n), c(n);
    std::vector<double> force(n + 1);

    for (std::size_t i = 0; i < n; ++i) {
        x[i] = parser.number();
        v[i] = parser.number();
        m[i] = parser.number();
        k[i] = parser.number();
        r[i] = parser.number();
        c[i] = parser.number();
    }

    simulate(n, steps, dt, circumference,
             x.data(), v.data(), m.data(), k.data(),
             r.data(), c.data(), force.data());

    double kinetic = 0.0;
    double potential = 0.0;
    double position = 0.0;
    std::size_t fastest = 0;
    double greatestSpeed = std::fabs(v[0]);

    for (std::size_t i = 0; i < n; ++i) {
        kinetic += ((0.5 * m[i]) * v[i]) * v[i];
        position += x[i];

        const double speed = std::fabs(v[i]);
        if (speed > greatestSpeed) {
            greatestSpeed = speed;
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

    std::printf(
        "kinetic %.17e\n"
        "potential %.17e\n"
        "position %.17e\n"
        "fastest %zu\n",
        kinetic, potential, position, fastest);

    return 0;
}
