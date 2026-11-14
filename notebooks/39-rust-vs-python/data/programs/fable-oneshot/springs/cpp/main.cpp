#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cmath>
#include <charconv>
#include <system_error>
#include <intrin.h>
#include <immintrin.h>
#include <malloc.h>

static bool hasAvx2() {
    int info[4];
    __cpuid(info, 0);
    if (info[0] < 7) return false;
    __cpuid(info, 1);
    const bool osxsave = (info[2] & (1 << 27)) != 0;
    const bool avx = (info[2] & (1 << 28)) != 0;
    if (!osxsave || !avx) return false;
    if ((_xgetbv(0) & 6) != 6) return false;
    __cpuidex(info, 7, 0);
    return (info[1] & (1 << 5)) != 0;
}

// One time step, AVX2 path. Performs exactly the same IEEE operations as the scalar path.
static __declspec(noinline) void stepAvx2(double* __restrict x, double* __restrict v,
                                          const double* __restrict m, const double* __restrict k,
                                          const double* __restrict r, const double* __restrict c,
                                          size_t n, double dt, double P) {
    x[n] = x[0] + P;
    double carry = k[n - 1] * ((x[n] - x[n - 1]) - r[n - 1]);
    size_t i = 0;
    const size_t nv = n & ~static_cast<size_t>(3);
    if (nv != 0) {
        const __m256d vdt = _mm256_set1_pd(dt);
        __m256d rot = _mm256_set1_pd(carry); // element 0 holds f[i-1]
        for (; i < nv; i += 4) {
            const __m256d xi = _mm256_loadu_pd(x + i);
            const __m256d xn = _mm256_loadu_pd(x + i + 1);
            const __m256d s = _mm256_sub_pd(_mm256_sub_pd(xn, xi), _mm256_loadu_pd(r + i));
            const __m256d f = _mm256_mul_pd(_mm256_loadu_pd(k + i), s);
            const __m256d rotc = _mm256_permute4x64_pd(f, 0x93); // [f3, f0, f1, f2]
            const __m256d fprev = _mm256_blend_pd(rotc, rot, 1);  // [prev f3, f0, f1, f2]
            rot = rotc;
            const __m256d vi = _mm256_loadu_pd(v + i);
            const __m256d F = _mm256_sub_pd(_mm256_sub_pd(f, fprev),
                                            _mm256_mul_pd(_mm256_loadu_pd(c + i), vi));
            const __m256d q = _mm256_div_pd(F, _mm256_loadu_pd(m + i));
            const __m256d vnew = _mm256_add_pd(vi, _mm256_mul_pd(vdt, q));
            _mm256_storeu_pd(v + i, vnew);
            const __m256d xnew = _mm256_add_pd(xi, _mm256_mul_pd(vdt, vnew));
            _mm256_storeu_pd(x + i, xnew);
        }
        carry = _mm_cvtsd_f64(_mm256_castpd256_pd128(rot));
        _mm256_zeroupper();
    }
    for (; i < n; ++i) {
        const double s = (x[i + 1] - x[i]) - r[i];
        const double f = k[i] * s;
        const double F = (f - carry) - (c[i] * v[i]);
        carry = f;
        const double vn = v[i] + dt * (F / m[i]);
        v[i] = vn;
        x[i] = x[i] + dt * vn;
    }
}

static __declspec(noinline) void stepScalar(double* __restrict x, double* __restrict v,
                                            const double* __restrict m, const double* __restrict k,
                                            const double* __restrict r, const double* __restrict c,
                                            size_t n, double dt, double P) {
    x[n] = x[0] + P;
    double carry = k[n - 1] * ((x[n] - x[n - 1]) - r[n - 1]);
    for (size_t i = 0; i < n; ++i) {
        const double s = (x[i + 1] - x[i]) - r[i];
        const double f = k[i] * s;
        const double F = (f - carry) - (c[i] * v[i]);
        carry = f;
        const double vn = v[i] + dt * (F / m[i]);
        v[i] = vn;
        x[i] = x[i] + dt * vn;
    }
}

struct Parser {
    const char* p;
    const char* end;

    void skip() {
        while (p < end && (*p == ' ' || *p == '\n' || *p == '\r' || *p == '\t')) ++p;
    }
    void skipToken() {
        while (p < end && !(*p == ' ' || *p == '\n' || *p == '\r' || *p == '\t')) ++p;
    }
    double num() {
        skip();
        if (p >= end) return 0.0;
        const char* q = p;
        if (*q == '+') ++q;
        double val = 0.0;
        auto res = std::from_chars(q, end, val);
        if (res.ec == std::errc()) {
            p = res.ptr;
            return val;
        }
        // Fallback (e.g. out-of-range values): buffer is null-terminated.
        char* e = nullptr;
        val = std::strtod(p, &e);
        if (e == p) {
            skipToken();
            return 0.0;
        }
        p = e;
        return val;
    }
    long long integer() {
        skip();
        if (p >= end) return 0;
        const char* q = p;
        if (*q == '+') ++q;
        long long val = 0;
        auto res = std::from_chars(q, end, val);
        if (res.ec == std::errc() &&
            (res.ptr >= end || *res.ptr == ' ' || *res.ptr == '\n' || *res.ptr == '\r' || *res.ptr == '\t')) {
            p = res.ptr;
            return val;
        }
        return static_cast<long long>(num());
    }
};

static double* allocArr(size_t count) {
    void* mem = _aligned_malloc(count * sizeof(double), 64);
    if (!mem) std::exit(1);
    std::memset(mem, 0, count * sizeof(double));
    return static_cast<double*>(mem);
}

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    FILE* fp = std::fopen(argv[1], "rb");
    if (!fp) return 1;
    _fseeki64(fp, 0, SEEK_END);
    const long long fsize = _ftelli64(fp);
    _fseeki64(fp, 0, SEEK_SET);
    if (fsize < 0) return 1;
    char* buf = static_cast<char*>(std::malloc(static_cast<size_t>(fsize) + 1));
    if (!buf) return 1;
    const size_t got = std::fread(buf, 1, static_cast<size_t>(fsize), fp);
    std::fclose(fp);
    buf[got] = '\0';

    Parser ps{buf, buf + got};
    const long long Nll = ps.integer();
    const long long S = ps.integer();
    const double dt = ps.num();
    const double P = ps.num();
    if (Nll < 1) return 1;
    const size_t n = static_cast<size_t>(Nll);

    const size_t cap = n + 8;
    double* x = allocArr(cap);
    double* v = allocArr(cap);
    double* m = allocArr(cap);
    double* k = allocArr(cap);
    double* r = allocArr(cap);
    double* c = allocArr(cap);

    for (size_t i = 0; i < n; ++i) {
        x[i] = ps.num();
        v[i] = ps.num();
        m[i] = ps.num();
        k[i] = ps.num();
        r[i] = ps.num();
        c[i] = ps.num();
    }
    std::free(buf);

    if (n >= 4 && hasAvx2()) {
        for (long long s = 0; s < S; ++s) stepAvx2(x, v, m, k, r, c, n, dt, P);
    } else {
        for (long long s = 0; s < S; ++s) stepScalar(x, v, m, k, r, c, n, dt, P);
    }

    double K = 0.0, U = 0.0, X = 0.0;
    size_t J = 0;
    double best = std::fabs(v[0]);
    x[n] = x[0] + P;
    for (size_t i = 0; i < n; ++i) {
        K += ((0.5 * m[i]) * v[i]) * v[i];
        const double s = (x[i + 1] - x[i]) - r[i];
        U += ((0.5 * k[i]) * s) * s;
        const double a = std::fabs(v[i]);
        if (a > best) {
            best = a;
            J = i;
        }
    }
    for (size_t i = 0; i < n; ++i) X += x[i];

    std::printf("kinetic %.16e\n", K);
    std::printf("potential %.16e\n", U);
    std::printf("position %.16e\n", X);
    std::printf("fastest %llu\n", static_cast<unsigned long long>(J));
    std::fflush(stdout);

    _aligned_free(x);
    _aligned_free(v);
    _aligned_free(m);
    _aligned_free(k);
    _aligned_free(r);
    _aligned_free(c);
    return 0;
}
