#include <immintrin.h>
#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <charconv>
#include <string>
#include <vector>

static bool readFile(const char* path, std::string& out) {
    FILE* f = std::fopen(path, "rb");
    if (!f) return false;
    std::fseek(f, 0, SEEK_END);
    long n = std::ftell(f);
    std::fseek(f, 0, SEEK_SET);
    out.resize(n);
    size_t got = n ? std::fread(out.data(), 1, n, f) : 0;
    out.resize(got);
    std::fclose(f);
    return true;
}

struct Parser {
    const char* p;
    const char* e;
    void skip() { while (p < e && (unsigned char)*p <= ' ') ++p; }
    double dbl() {
        skip();
        const char* q = p;
        if (q < e && *q == '+') ++q;
        double v = 0;
        auto r = std::from_chars(q, e, v);
        p = r.ptr;
        return v;
    }
};

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    std::string data;
    if (!readFile(argv[1], data)) return 1;
    Parser ps{data.data(), data.data() + data.size()};
    long long N = (long long)ps.dbl();
    long long S = (long long)ps.dbl();
    double dt = ps.dbl();
    double P = ps.dbl();
    std::vector<double> x(N + 8), v(N + 8), m(N + 8), k(N + 8), r(N + 8), c(N + 8), fa(N + 8);
    for (long long i = 0; i < N; ++i) {
        x[i] = ps.dbl(); v[i] = ps.dbl(); m[i] = ps.dbl();
        k[i] = ps.dbl(); r[i] = ps.dbl(); c[i] = ps.dbl();
    }
    double* X = x.data(); double* V = v.data(); double* M = m.data();
    double* K = k.data(); double* R = r.data(); double* C = c.data(); double* FA = fa.data();
    const __m256d vdt = _mm256_set1_pd(dt);
    const long long n1 = N - 1;
    for (long long s = 0; s < S; ++s) {
        // spring i is stored at FA[i+1]; FA[0] holds spring N-1
        double last = K[n1] * (((X[0] + P) - X[n1]) - R[n1]);
        long long i = 0;
        for (; i + 4 <= n1; i += 4) {
            __m256d a = _mm256_loadu_pd(X + i + 1);
            __m256d b = _mm256_loadu_pd(X + i);
            __m256d st = _mm256_sub_pd(_mm256_sub_pd(a, b), _mm256_loadu_pd(R + i));
            _mm256_storeu_pd(FA + i + 1, _mm256_mul_pd(_mm256_loadu_pd(K + i), st));
        }
        for (; i < n1; ++i) FA[i + 1] = K[i] * ((X[i + 1] - X[i]) - R[i]);
        FA[N] = last;
        FA[0] = last;
        i = 0;
        for (; i + 4 <= N; i += 4) {
            __m256d F = _mm256_sub_pd(_mm256_sub_pd(_mm256_loadu_pd(FA + i + 1), _mm256_loadu_pd(FA + i)),
                                      _mm256_mul_pd(_mm256_loadu_pd(C + i), _mm256_loadu_pd(V + i)));
            __m256d nv = _mm256_add_pd(_mm256_loadu_pd(V + i),
                                       _mm256_mul_pd(vdt, _mm256_div_pd(F, _mm256_loadu_pd(M + i))));
            _mm256_storeu_pd(V + i, nv);
            _mm256_storeu_pd(X + i, _mm256_add_pd(_mm256_loadu_pd(X + i), _mm256_mul_pd(vdt, nv)));
        }
        for (; i < N; ++i) {
            double F = (FA[i + 1] - FA[i]) - (C[i] * V[i]);
            V[i] = V[i] + dt * (F / M[i]);
            X[i] = X[i] + dt * V[i];
        }
    }
    double kin = 0, pot = 0, pos = 0, best = -1;
    long long bi = 0;
    for (long long i = 0; i < N; ++i) {
        kin += ((0.5 * M[i]) * V[i]) * V[i];
        double st = (i < n1) ? ((X[i + 1] - X[i]) - R[i]) : (((X[0] + P) - X[n1]) - R[n1]);
        pot += ((0.5 * K[i]) * st) * st;
        pos += X[i];
        double a = std::fabs(V[i]);
        if (a > best) { best = a; bi = i; }
    }
    std::printf("kinetic %.12e\npotential %.12e\nposition %.12e\nfastest %lld\n", kin, pot, pos, bi);
    return 0;
}
