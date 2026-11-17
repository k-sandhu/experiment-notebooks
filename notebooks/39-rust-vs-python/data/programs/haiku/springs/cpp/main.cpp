// Springs on a ring: explicit time stepping of N masses joined by N springs (see SPEC.md).
//
// Each step runs in two passes over flat arrays, so the loops stay simple enough for the
// compiler to vectorize. The arithmetic keeps the spec's operation order, so the results
// match the reference bit for bit, apart from summation order in the final sums.

#include <charconv>
#include <cmath>
#include <cstddef>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iterator>
#include <string>
#include <system_error>
#include <vector>

namespace {

// Reads the next whitespace-separated decimal number, correctly rounded.
template <class T>
T next_number(const char*& p, const char* end) {
    while (p < end && static_cast<unsigned char>(*p) <= ' ') ++p;
    if (p < end && *p == '+') ++p;  // from_chars does not accept a leading '+'
    T value{};
    auto [ptr, ec] = std::from_chars(p, end, value);
    if (ec != std::errc()) {
        std::fputs("malformed number in input\n", stderr);
        std::exit(1);
    }
    p = ptr;
    return value;
}

struct Ring {
    std::size_t n = 0;
    long long steps = 0;
    double dt = 0.0;
    double circumference = 0.0;
    std::vector<double> x, v, m, k, r, c;
    std::vector<double> f;  // spring forces for the current step
};

Ring read_ring(const char* path) {
    std::ifstream in(path, std::ios::binary);
    if (!in) {
        std::fputs("cannot open input file\n", stderr);
        std::exit(1);
    }
    const std::string text((std::istreambuf_iterator<char>(in)), std::istreambuf_iterator<char>());
    const char* p = text.data();
    const char* end = p + text.size();

    Ring ring;
    ring.n = next_number<long long>(p, end);
    ring.steps = next_number<long long>(p, end);
    ring.dt = next_number<double>(p, end);
    ring.circumference = next_number<double>(p, end);

    const std::size_t n = ring.n;
    ring.x.resize(n);
    ring.v.resize(n);
    ring.m.resize(n);
    ring.k.resize(n);
    ring.r.resize(n);
    ring.c.resize(n);
    ring.f.resize(n);
    for (std::size_t i = 0; i < n; ++i) {
        ring.x[i] = next_number<double>(p, end);
        ring.v[i] = next_number<double>(p, end);
        ring.m[i] = next_number<double>(p, end);
        ring.k[i] = next_number<double>(p, end);
        ring.r[i] = next_number<double>(p, end);
        ring.c[i] = next_number<double>(p, end);
    }
    return ring;
}

// One time step (SPEC.md, "One time step").
void step(Ring& ring) {
    const std::size_t n = ring.n;
    const double P = ring.circumference;
    const double dt = ring.dt;
    double* __restrict x = ring.x.data();
    double* __restrict v = ring.v.data();
    const double* __restrict m = ring.m.data();
    const double* __restrict k = ring.k.data();
    const double* __restrict r = ring.r.data();
    const double* __restrict c = ring.c.data();
    double* __restrict f = ring.f.data();

    // Pass 1: spring forces from the old positions. Spring n-1 wraps around to mass 0.
    for (std::size_t i = 0; i + 1 < n; ++i) {
        f[i] = k[i] * ((x[i + 1] - x[i]) - r[i]);
    }
    f[n - 1] = k[n - 1] * (((x[0] + P) - x[n - 1]) - r[n - 1]);

    // Pass 2: velocity from the forces (old velocity), then position from the new velocity.
    // Mass 0 uses the force of spring n-1 as its left neighbour.
    v[0] = v[0] + dt * (((f[0] - f[n - 1]) - (c[0] * v[0])) / m[0]);
    for (std::size_t i = 1; i < n; ++i) {
        v[i] = v[i] + dt * (((f[i] - f[i - 1]) - (c[i] * v[i])) / m[i]);
    }
    for (std::size_t i = 0; i < n; ++i) {
        x[i] = x[i] + dt * v[i];
    }
}

}  // namespace

int main(int argc, char** argv) {
    if (argc < 2) {
        std::fputs("usage: solution INPUT_PATH\n", stderr);
        return 1;
    }
    Ring ring = read_ring(argv[1]);
    const std::size_t n = ring.n;

    for (long long s = 0; s < ring.steps; ++s) {
        step(ring);
    }

    const double P = ring.circumference;
    double kinetic = 0.0;
    for (std::size_t i = 0; i < n; ++i) {
        kinetic += ((0.5 * ring.m[i]) * ring.v[i]) * ring.v[i];
    }

    double potential = 0.0;
    for (std::size_t i = 0; i + 1 < n; ++i) {
        const double s = (ring.x[i + 1] - ring.x[i]) - ring.r[i];
        potential += ((0.5 * ring.k[i]) * s) * s;
    }
    const double s_last = ((ring.x[0] + P) - ring.x[n - 1]) - ring.r[n - 1];
    potential += ((0.5 * ring.k[n - 1]) * s_last) * s_last;

    double position = 0.0;
    for (std::size_t i = 0; i < n; ++i) {
        position += ring.x[i];
    }

    std::size_t fastest = 0;
    for (std::size_t i = 1; i < n; ++i) {
        if (std::fabs(ring.v[i]) > std::fabs(ring.v[fastest])) fastest = i;
    }

    std::printf("kinetic %.16e\n", kinetic);
    std::printf("potential %.16e\n", potential);
    std::printf("position %.16e\n", position);
    std::printf("fastest %zu\n", fastest);
    return 0;
}
