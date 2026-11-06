// Springs on a ring: explicit integration of a ring of masses joined by springs.
#include <charconv>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <immintrin.h>
#include <intrin.h>
#include <vector>

namespace {

struct Reader {
    const char* p;
    const char* end;

    void skip() {
        while (p < end && (*p == ' ' || *p == '\n' || *p == '\r' || *p == '\t')) ++p;
        if (p < end && *p == '+') ++p;
    }
    double num() {
        skip();
        double v = 0.0;
        auto res = std::from_chars(p, end, v);
        p = res.ptr;
        return v;
    }
    long long integer() {
        skip();
        long long v = 0;
        auto res = std::from_chars(p, end, v);
        p = res.ptr;
        return v;
    }
};

// 32-byte aligned double buffer with room for padding lanes.
struct Buf {
    double* d;
    explicit Buf(size_t n) {
        d = static_cast<double*>(_aligned_malloc(n * sizeof(double), 32));
        std::memset(d, 0, n * sizeof(double));
    }
    ~Buf() { _aligned_free(d); }
    double& operator[](size_t i) { return d[i]; }
};

bool has_avx() {
    int info[4];
    __cpuid(info, 1);
    bool osxsave = (info[2] & (1 << 27)) != 0;
    bool avx = (info[2] & (1 << 28)) != 0;
    if (!osxsave || !avx) return false;
    unsigned long long xcr0 = _xgetbv(0);
    return (xcr0 & 6) == 6;
}

// Portable fallback: two plain loops per step (MSVC vectorises them with SSE2).
void simulate_scalar(int n, long long steps, double dt, double P, double* x, double* v, const double* m,
                     const double* k, const double* r, const double* c, double* fa) {
    // fa[0] holds f[n-1] (the f[-1] wrap-around), fa[i+1] holds f[i].
    for (long long s = 0; s < steps; ++s) {
        x[n] = x[0] + P;
        for (int i = 0; i < n; ++i) fa[i + 1] = k[i] * ((x[i + 1] - x[i]) - r[i]);
        fa[0] = fa[n];
        for (int i = 0; i < n; ++i) {
            double F = (fa[i + 1] - fa[i]) - (c[i] * v[i]);
            double nv = v[i] + dt * (F / m[i]);
            v[i] = nv;
            x[i] = x[i] + dt * nv;
        }
    }
}

// AVX path: one fused pass per step. Lanes past n are padding (k = r = c = 0, m = 1) and never feed real lanes.
void simulate_avx(int n, long long steps, double dt, double P, double* x, double* v, const double* m, const double* k,
                  const double* r, const double* c) {
    const int blocks = (n + 3) / 4;
    const __m256d vdt = _mm256_set1_pd(dt);
    for (long long s = 0; s < steps; ++s) {
        x[n] = x[0] + P;  // ghost position closing the ring
        double flast = k[n - 1] * ((x[n] - x[n - 1]) - r[n - 1]);
        __m256d prev = _mm256_set1_pd(flast);
        for (int b = 0; b < blocks; ++b) {
            const int i = b * 4;
            __m256d xi = _mm256_load_pd(x + i);
            __m256d xn = _mm256_loadu_pd(x + i + 1);
            __m256d f = _mm256_mul_pd(_mm256_load_pd(k + i), _mm256_sub_pd(_mm256_sub_pd(xn, xi), _mm256_load_pd(r + i)));
            // fs = [prev3, f0, f1, f2]
            __m256d t = _mm256_permute2f128_pd(prev, f, 0x21);
            __m256d fs = _mm256_shuffle_pd(t, f, 5);
            __m256d vi = _mm256_load_pd(v + i);
            __m256d F = _mm256_sub_pd(_mm256_sub_pd(f, fs), _mm256_mul_pd(_mm256_load_pd(c + i), vi));
            vi = _mm256_add_pd(vi, _mm256_mul_pd(vdt, _mm256_div_pd(F, _mm256_load_pd(m + i))));
            _mm256_store_pd(v + i, vi);
            _mm256_store_pd(x + i, _mm256_add_pd(xi, _mm256_mul_pd(vdt, vi)));
            prev = f;
        }
    }
    _mm256_zeroupper();
}

}  // namespace

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    FILE* fp = std::fopen(argv[1], "rb");
    if (!fp) return 1;
    std::fseek(fp, 0, SEEK_END);
    long sz = std::ftell(fp);
    std::fseek(fp, 0, SEEK_SET);
    std::vector<char> data(static_cast<size_t>(sz) + 1);
    size_t got = std::fread(data.data(), 1, static_cast<size_t>(sz), fp);
    std::fclose(fp);
    data[got] = '\0';

    Reader rd{data.data(), data.data() + got};
    const int n = static_cast<int>(rd.integer());
    const long long steps = rd.integer();
    const double dt = rd.num();
    const double P = rd.num();

    const size_t cap = static_cast<size_t>(n) + 8;
    Buf x(cap), v(cap), m(cap), k(cap), r(cap), c(cap), fa(cap);
    for (size_t i = n; i < cap; ++i) m[i] = 1.0;
    for (int i = 0; i < n; ++i) {
        x[i] = rd.num();
        v[i] = rd.num();
        m[i] = rd.num();
        k[i] = rd.num();
        r[i] = rd.num();
        c[i] = rd.num();
    }

    if (has_avx())
        simulate_avx(n, steps, dt, P, x.d, v.d, m.d, k.d, r.d, c.d);
    else
        simulate_scalar(n, steps, dt, P, x.d, v.d, m.d, k.d, r.d, c.d, fa.d);

    double K = 0.0, U = 0.0, X = 0.0;
    int J = 0;
    double best = -1.0;
    for (int i = 0; i < n; ++i) {
        K += ((0.5 * m[i]) * v[i]) * v[i];
        double nx = (i + 1 < n) ? x[i + 1] : x[0] + P;
        double st = (nx - x[i]) - r[i];
        U += ((0.5 * k[i]) * st) * st;
        X += x[i];
        double a = std::fabs(v[i]);
        if (a > best) {
            best = a;
            J = i;
        }
    }
    std::printf("kinetic %.17e\npotential %.17e\nposition %.17e\nfastest %d\n", K, U, X, J);
    return 0;
}
