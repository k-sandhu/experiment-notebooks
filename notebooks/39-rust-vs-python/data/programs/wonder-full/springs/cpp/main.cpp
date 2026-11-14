#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cmath>
#include <new>

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    FILE* fp = std::fopen(argv[1], "rb");
    if (!fp) return 1;
    std::fseek(fp, 0, SEEK_END);
    long sz = std::ftell(fp);
    std::fseek(fp, 0, SEEK_SET);
    if (sz < 0) sz = 0;
    char* buf = new char[(size_t)sz + 1];
    size_t got = sz ? std::fread(buf, 1, (size_t)sz, fp) : 0;
    std::fclose(fp);
    buf[got] = '\0';

    char* p = buf;
    char* end = nullptr;
    long Nlong = std::strtol(p, &end, 10); p = end;
    long Slong = std::strtol(p, &end, 10); p = end;
    int N = (int)Nlong;
    long S = Slong;
    double dt = std::strtod(p, &end); p = end;
    double P = std::strtod(p, &end); p = end;

    if (N <= 0) {
        std::printf("kinetic %.12e\npotential %.12e\nposition %.12e\nfastest 0\n", 0.0, 0.0, 0.0);
        return 0;
    }

    double* __restrict x = new double[N + 1];
    double* __restrict v = new double[N + 1];
    double* __restrict m = new double[N + 1];
    double* __restrict k = new double[N + 1];
    double* __restrict r = new double[N + 1];
    double* __restrict c = new double[N + 1];
    double* __restrict a = new double[N + 1]; // dt / m

    for (int i = 0; i < N; ++i) {
        x[i] = std::strtod(p, &end); p = end;
        v[i] = std::strtod(p, &end); p = end;
        m[i] = std::strtod(p, &end); p = end;
        k[i] = std::strtod(p, &end); p = end;
        r[i] = std::strtod(p, &end); p = end;
        c[i] = std::strtod(p, &end); p = end;
        a[i] = dt / m[i];
    }
    x[N] = 0;

    const int nm1 = N - 1;
    for (long step = 0; step < S; ++step) {
        // Fused pass: x[i] is only needed for f[i] and f[i-1], both computed
        // before x[i] is updated, so one in-place sweep suffices.
        double fLast = k[nm1] * (((x[0] + P) - x[nm1]) - r[nm1]);
        double fPrev = fLast;
        double xcur = x[0];
        for (int i = 0; i < nm1; ++i) {
            double xnext = x[i + 1];
            double fi = k[i] * ((xnext - xcur) - r[i]);
            double vi = v[i];
            double nv = vi + a[i] * ((fi - fPrev) - c[i] * vi);
            v[i] = nv;
            x[i] = xcur + dt * nv;
            fPrev = fi;
            xcur = xnext;
        }
        {
            double F = (fLast - fPrev) - c[nm1] * v[nm1];
            double nv = v[nm1] + a[nm1] * F;
            v[nm1] = nv;
            x[nm1] = x[nm1] + dt * nv;
        }
    }

    double K = 0.0, U = 0.0, X = 0.0;
    int J = 0;
    double best = std::fabs(v[0]);
    for (int i = 0; i < N; ++i) {
        K += ((0.5 * m[i]) * v[i]) * v[i];
        X += x[i];
        double av = std::fabs(v[i]);
        if (av > best) { best = av; J = i; }
    }
    for (int i = 0; i < nm1; ++i) {
        double s = (x[i + 1] - x[i]) - r[i];
        U += ((0.5 * k[i]) * s) * s;
    }
    {
        double s = ((x[0] + P) - x[nm1]) - r[nm1];
        U += ((0.5 * k[nm1]) * s) * s;
    }

    char out[256];
    int len = std::snprintf(out, sizeof(out),
        "kinetic %.12e\npotential %.12e\nposition %.12e\nfastest %d\n", K, U, X, J);
    std::fwrite(out, 1, (size_t)len, stdout);
    return 0;
}
