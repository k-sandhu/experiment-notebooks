#include <charconv>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstdint>
#include <fstream>
#include <iterator>
#include <string>
#include <vector>

class Input {
    std::string data;
    const char* p;
    const char* end;
    void skip() { while (p != end && *p <= ' ') ++p; }
public:
    explicit Input(const char* path) {
        std::ifstream file(path, std::ios::binary | std::ios::ate);
        data.resize(static_cast<std::size_t>(file.tellg()));
        file.seekg(0);
        file.read(data.data(), static_cast<std::streamsize>(data.size()));
        p = data.data();
        end = p + data.size();
    }
    std::uint64_t integer() {
        skip();
        if (*p == '+') ++p;
        std::uint64_t value = 0;
        const auto result = std::from_chars(p, end, value);
        p = result.ptr;
        return value;
    }
    double number() {
        skip();
        if (*p == '+') ++p;
        double value = 0;
        const auto result = std::from_chars(p, end, value);
        // from_chars reports underflow/overflow instead of returning 0/infinity.
        if (result.ec == std::errc::result_out_of_range)
            value = std::strtod(p, nullptr);
        p = result.ptr;
        return value;
    }
};

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    Input input(argv[1]);
    const std::size_t n = static_cast<std::size_t>(input.integer());
    const std::uint64_t steps = input.integer();
    const double dt = input.number(), circumference = input.number();
    // Contiguous arrays and one extra position/force eliminate wraparound in
    // the inner loops and allow the compiler to vectorize independent updates.
    std::vector<double> storage(7 * n + 2);
    double* x = storage.data();
    double* v = x + n + 1;
    double* m = v + n;
    double* k = m + n;
    double* r = k + n;
    double* c = r + n;
    double* f = c + n;
    for (std::size_t i = 0; i < n; ++i) {
        x[i] = input.number(); v[i] = input.number(); m[i] = input.number();
        k[i] = input.number(); r[i] = input.number(); c[i] = input.number();
    }
    for (std::uint64_t step = 0; step < steps; ++step) {
        x[n] = x[0] + circumference;
        for (std::size_t i = 0; i < n; ++i)
            f[i + 1] = k[i] * ((x[i + 1] - x[i]) - r[i]);
        f[0] = f[n];
        for (std::size_t i = 0; i < n; ++i) {
            const double force = (f[i + 1] - f[i]) - c[i] * v[i];
            const double velocity = v[i] + dt * (force / m[i]);
            v[i] = velocity;
            x[i] = x[i] + dt * velocity;
        }
    }
    x[n] = x[0] + circumference;
    double kinetic = 0, potential = 0, position = 0;
    std::size_t fastest = 0;
    double speed = std::abs(v[0]);
    for (std::size_t i = 0; i < n; ++i) {
        kinetic += ((0.5 * m[i]) * v[i]) * v[i];
        const double stretch = (x[i + 1] - x[i]) - r[i];
        potential += ((0.5 * k[i]) * stretch) * stretch;
        position += x[i];
        if (std::abs(v[i]) > speed) { speed = std::abs(v[i]); fastest = i; }
    }
    std::printf("kinetic %.17g\npotential %.17g\nposition %.17g\nfastest %zu\n",
                kinetic, potential, position, fastest);
}
