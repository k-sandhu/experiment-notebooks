#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cmath>
#include <vector>

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    FILE* fp = std::fopen(argv[1], "rb");
    if (!fp) return 1;
    std::fseek(fp, 0, SEEK_END);
    long sz = std::ftell(fp);
    std::fseek(fp, 0, SEEK_SET);
    std::vector<char> buf((size_t)sz + 1);
    if (sz > 0) std::fread(buf.data(), 1, (size_t)sz, fp);
    std::fclose(fp);
    buf[(size_t)sz] = '\0';
    char* p = buf.data();
    char* endp = nullptr;
    long Nl = std::strtol(p, &endp, 10); p = endp;
    long Sl = std::strtol(p, &endp, 10); p = endp;
    double dt = std::strtod(p, &endp); p = endp;
    double P = std::strtod(p, &endp); p = endp;
    int N = (int)Nl;
    long S = Sl;
    std::vector<double> x(N), v(N), m(N), k(N), r(N), c(N);
    for (int i = 0; i < N; i++) {
        x[i] = std::strtod(p, &endp); p = endp;
        v[i] = std::strtod(p, &endp); p = endp;
        m[i] = std::strtod(p, &endp); p = endp;
        k[i] = std::strtod(p, &endp); p = endp;
        r[i] = std::strtod(p, &endp); p = endp;
        c[i] = std::strtod(p, &endp); p = endp;
    }
    double* __restrict xp = x.data();
    double* __restrict vp = v.data();
    double* __restrict mp = m.data();
    double* __restrict kp = k.data();
    double* __restrict rp = r.data();
    double* __restrict cp = c.data();
    std::vector<double> dtm(N);
    for (int i = 0; i < N; i++) dtm[i] = dt / m[i];
    double* __restrict dtmp = dtm.data();

    for (long step = 0; step < S; step++) {
        double fLast = kp[N-1] * (((xp[0] + P) - xp[N-1]) - rp[N-1]);
        double prevF = fLast;
        int last = N - 1;
        for (int i = 0; i < last; i++) {
            double fi = kp[i] * ((xp[i+1] - xp[i]) - rp[i]);
            double F = (fi - prevF) - (cp[i] * vp[i]);
            double nv = vp[i] + dtmp[i] * F;
            vp[i] = nv;
            xp[i] = xp[i] + dt * nv;
            prevF = fi;
        }
        {
            int i = last;
            double F = (fLast - prevF) - (cp[i] * vp[i]);
            double nv = vp[i] + dtmp[i] * F;
            vp[i] = nv;
            xp[i] = xp[i] + dt * nv;
        }
    }
    double K = 0, U = 0, X = 0;
    for (int i = 0; i < N; i++) {
        K += ((0.5 * mp[i]) * vp[i]) * vp[i];
        X += xp[i];
    }
    for (int i = 0; i < N-1; i++) {
        double s = (xp[i+1] - xp[i]) - rp[i];
        U += ((0.5 * kp[i]) * s) * s;
    }
    {
        double s = ((xp[0] + P) - xp[N-1]) - rp[N-1];
        U += ((0.5 * kp[N-1]) * s) * s;
    }
    int J = 0;
    double best = std::fabs(vp[0]);
    for (int i = 1; i < N; i++) {
        double a = std::fabs(vp[i]);
        if (a > best) { best = a; J = i; }
    }
    std::printf("kinetic %.17e\npotential %.17e\nposition %.17e\nfastest %d\n", K, U, X, J);
    return 0;
}
