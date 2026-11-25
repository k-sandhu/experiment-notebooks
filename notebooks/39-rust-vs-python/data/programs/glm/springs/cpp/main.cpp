#include <cstdio>
#include <charconv>
#include <vector>

static inline double nextd(const char*& p, const char* end) {
    while (p < end && (*p == ' ' || *p == '\n' || *p == '\r' || *p == '\t')) ++p;
    bool neg = false;
    if (p < end && *p == '+') { neg = true; ++p; }  // from_chars rejects a leading '+'
    double v = 0.0;
    auto res = std::from_chars(p, end, v);
    p = res.ptr;
    return neg ? -v : v;
}

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    FILE* fp = fopen(argv[1], "rb");
    if (!fp) return 1;
    fseek(fp, 0, SEEK_END);
    long size = ftell(fp);
    fseek(fp, 0, SEEK_SET);
    std::vector<char> buf((size_t)size + 1);
    size_t got = fread(buf.data(), 1, (size_t)size, fp);
    fclose(fp);
    const char* p = buf.data();
    const char* end = buf.data() + got;

    long N = (long)nextd(p, end);
    long S = (long)nextd(p, end);
    double dt = nextd(p, end);
    double P = nextd(p, end);

    std::vector<double> x(N), v(N), m(N), k(N), r(N), c(N), f(N);
    double* __restrict xp = x.data();
    double* __restrict vp = v.data();
    double* __restrict mp = m.data();
    double* __restrict kp = k.data();
    double* __restrict rp = r.data();
    double* __restrict cp = c.data();
    double* __restrict fp_ = f.data();

    for (long i = 0; i < N; ++i) {
        xp[i] = nextd(p, end);
        vp[i] = nextd(p, end);
        mp[i] = nextd(p, end);
        kp[i] = nextd(p, end);
        rp[i] = nextd(p, end);
        cp[i] = nextd(p, end);
    }

    for (long step = 0; step < S; ++step) {
        for (long i = 0; i < N - 1; ++i)
            fp_[i] = kp[i] * ((xp[i + 1] - xp[i]) - rp[i]);
        fp_[N - 1] = kp[N - 1] * (((xp[0] + P) - xp[N - 1]) - rp[N - 1]);

        {
            double F = (fp_[0] - fp_[N - 1]) - (cp[0] * vp[0]);
            double nv = vp[0] + dt * (F / mp[0]);
            xp[0] = xp[0] + dt * nv;
            vp[0] = nv;
        }
        for (long i = 1; i < N; ++i) {
            double F = (fp_[i] - fp_[i - 1]) - (cp[i] * vp[i]);
            double nv = vp[i] + dt * (F / mp[i]);
            xp[i] = xp[i] + dt * nv;
            vp[i] = nv;
        }
    }

    double K = 0.0, U = 0.0, X = 0.0;
    long J = 0;
    double best = 0.0;
    for (long i = 0; i < N; ++i) {
        K += ((0.5 * mp[i]) * vp[i]) * vp[i];
        X += xp[i];
        double av = vp[i] < 0 ? -vp[i] : vp[i];
        if (av > best) { best = av; J = i; }
    }
    for (long i = 0; i < N - 1; ++i) {
        double s = (xp[i + 1] - xp[i]) - rp[i];
        U += ((0.5 * kp[i]) * s) * s;
    }
    {
        double s = ((xp[0] + P) - xp[N - 1]) - rp[N - 1];
        U += ((0.5 * kp[N - 1]) * s) * s;
    }

    std::printf("kinetic %.17e\npotential %.17e\nposition %.17e\nfastest %ld\n", K, U, X, J);
    return 0;
}
