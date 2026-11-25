#include <cstdio>
#include <vector>

int main(int argc, char** argv) {
    std::FILE* fp = std::fopen(argv[1], "r");
    if (!fp) {
        return 1;
    }
    int N = 0;
    int S = 0;
    double dt = 0.0;
    double P = 0.0;
    if (std::fscanf(fp, "%d %d %lf %lf", &N, &S, &dt, &P) != 4) {
        std::fclose(fp);
        return 1;
    }
    std::vector<double> x(N), v(N), m(N), k(N), r(N), c(N), f(N);
    for (int i = 0; i < N; ++i) {
        if (std::fscanf(fp, "%lf %lf %lf %lf %lf %lf", &x[i], &v[i], &m[i], &k[i], &r[i], &c[i]) != 6) {
            std::fclose(fp);
            return 1;
        }
    }
    std::fclose(fp);

    const int nm1 = N - 1;
    for (int step = 0; step < S; ++step) {
        // Stretches and spring forces from the old positions (read-only).
        for (int i = 0; i < nm1; ++i) {
            f[i] = k[i] * ((x[i + 1] - x[i]) - r[i]);
        }
        f[nm1] = k[nm1] * (((x[0] + P) - x[nm1]) - r[nm1]);

        // Forces, then velocities, then positions. f is read-only here, so
        // updating x[i] in place cannot corrupt any later force computation.
        double F = (f[0] - f[nm1]) - (c[0] * v[0]);
        v[0] = v[0] + dt * (F / m[0]);
        x[0] = x[0] + dt * v[0];
        for (int i = 1; i < N; ++i) {
            F = (f[i] - f[i - 1]) - (c[i] * v[i]);
            v[i] = v[i] + dt * (F / m[i]);
            x[i] = x[i] + dt * v[i];
        }
    }

    double K = 0.0;
    double U = 0.0;
    double X = 0.0;
    int J = 0;
    double best = -1.0;
    for (int i = 0; i < N; ++i) {
        double xnext = (i + 1 < N) ? x[i + 1] : x[0] + P;
        double s = (xnext - x[i]) - r[i];
        U += ((0.5 * k[i]) * s) * s;
        K += ((0.5 * m[i]) * v[i]) * v[i];
        X += x[i];
        double av = v[i] < 0.0 ? -v[i] : v[i];
        if (av > best) {  // strict: on a tie the smallest index wins
            best = av;
            J = i;
        }
    }

    std::printf("kinetic %.12e\npotential %.12e\nposition %.12e\nfastest %d\n",
                K, U, X, J);
    return 0;
}
