#include <cstdio>
#include <cstdlib>
#include <charconv>
#include <vector>

int main(int argc, char** argv) {
    if (argc < 2) return 1;

    FILE* fp = std::fopen(argv[1], "rb");
    if (!fp) return 1;
    std::fseek(fp, 0, SEEK_END);
    long size = std::ftell(fp);
    std::fseek(fp, 0, SEEK_SET);
    std::vector<char> data((size_t)size + 32);
    size_t got = std::fread(data.data(), 1, (size_t)size, fp);
    std::fclose(fp);
    for (size_t i = got; i < data.size(); ++i) data[i] = 0;

    char* p = data.data();
    char* end = p + got;

    auto skipWs = [&]() {
        while (p < end && (*p == ' ' || *p == '\n' || *p == '\r' || *p == '\t')) ++p;
    };
    auto readDouble = [&]() -> double {
        skipWs();
        double v = 0.0;
        auto r = std::from_chars(p, end, v);
        p = const_cast<char*>(r.ptr);
        return v;
    };
    auto readInt = [&]() -> long long {
        skipWs();
        long long v = 0;
        auto r = std::from_chars(p, end, v);
        p = const_cast<char*>(r.ptr);
        return v;
    };

    const long long n = readInt();
    const long long steps = readInt();
    const double dt = readDouble();
    const double P = readDouble();

    std::vector<double> x(n), v(n), m(n), k(n), r(n), c(n);
    for (long long i = 0; i < n; ++i) {
        x[i] = readDouble();
        v[i] = readDouble();
        m[i] = readDouble();
        k[i] = readDouble();
        r[i] = readDouble();
        c[i] = readDouble();
    }

    for (long long t = 0; t < steps; ++t) {
        const double x0 = x[0];
        const double xl = x[n - 1];
        const double sLast = ((x0 + P) - xl) - r[n - 1];
        const double fLast = k[n - 1] * sLast;
        double fprev = fLast;

        for (long long i = 0; i < n - 1; ++i) {
            const double s = (x[i + 1] - x[i]) - r[i];
            const double f = k[i] * s;
            const double F = (f - fprev) - c[i] * v[i];
            const double nv = v[i] + dt * (F / m[i]);
            v[i] = nv;
            x[i] = x[i] + dt * nv;
            fprev = f;
        }

        const long long i = n - 1;
        const double F = (fLast - fprev) - c[i] * v[i];
        const double nv = v[i] + dt * (F / m[i]);
        v[i] = nv;
        x[i] = x[i] + dt * nv;
    }

    double K = 0.0, U = 0.0, X = 0.0;
    for (long long i = 0; i < n; ++i) {
        K += ((0.5 * m[i]) * v[i]) * v[i];
        X += x[i];
    }
    for (long long i = 0; i < n - 1; ++i) {
        const double s = (x[i + 1] - x[i]) - r[i];
        U += ((0.5 * k[i]) * s) * s;
    }
    {
        const double s = ((x[0] + P) - x[n - 1]) - r[n - 1];
        U += ((0.5 * k[n - 1]) * s) * s;
    }

    long long fastest = 0;
    double best = -1.0;
    for (long long i = 0; i < n; ++i) {
        double a = v[i] < 0 ? -v[i] : v[i];
        if (a > best) { best = a; fastest = i; }
    }

    std::printf("kinetic %.12e\npotential %.12e\nposition %.12e\nfastest %lld\n",
                K, U, X, fastest);
    return 0;
}
