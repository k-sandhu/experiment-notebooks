You are writing five versions of the same program, in C++, Java, C#, Go and JavaScript, for a comparison of
how fast and how memory-hungry each version is.

The task is described in SPEC.md in this folder. The folder samples/ holds example inputs (`*.in`), each with
the exact expected output (`*.out`).

Each language has its own folder with a starting file and a `build.cmd`. The benchmark builds every program with
these same build scripts and flags, whatever you change in them. Write these programs:

1. `cpp/main.cpp` (more `.cpp` and header files in `cpp/` are fine): C++20, built by `cpp\build.cmd` with
   Microsoft Visual C++ 19.40 (Visual Studio 2022) and `/O2 /GL /EHsc /std:c++20`. Standard library only, plus
   nlohmann/json 3.12 (`#include <nlohmann/json.hpp>`, already in `cpp/include/`). Run as
   `cpp\solution.exe INPUT_PATH`.
2. `java/src/Main.java` (more `.java` files in `java/src/` are fine): Java 23, built by `java\build.cmd` with
   `javac`. Java SE only, plus Jackson 2.22 (core, databind and annotations, already in `java/lib/`). Run as
   `java\run.cmd INPUT_PATH`, which runs `java -cp "out;lib\*" Main` with the default JVM settings.
3. `csharp/Program.cs` (more `.cs` files in `csharp/` are fine): C# 12 on .NET 8, built in Release by
   `csharp\build.cmd`. Base class library only. You may change properties in `csharp/solution.csproj`, but do not
   add package references. Run as `csharp\out\solution.exe INPUT_PATH`.
4. `go/main.go` (more `.go` files in `go/` are fine): Go 1.27, built by `go\build.cmd`. Standard library only.
   Run as `go\solution.exe INPUT_PATH`.
5. `js/main.js`: JavaScript on Node.js 22, with no build step. Built-in Node modules only; no npm packages. Run as
   `node js\main.js INPUT_PATH`.

Each program reads the input file whose path is its first argument (SPEC.md says if a task takes more
arguments) and writes the answer to standard output exactly as SPEC.md describes.

Your goals, in order:

1. Every version must print the correct output for any valid input as SPEC.md defines it, not only for the
   samples.
2. Make each version as fast as you can. Write each one the way a skilled developer in that language would
   write fast code, using that language's own strengths.

Use a single thread and a single process unless SPEC.md says otherwise. Do not precompute or embed answers,
start other programs, or read any file other than the input. Python 3.13 (`C:\Python313\python.exe`) is
available if you want it for testing, but not as part of any program.

The programs will be run on Windows 11 on a 16-core laptop, on larger inputs of the same kind; SPEC.md gives
the benchmark size. Build and test all five versions against every sample before you finish. Work only inside
this folder, and take at most about 60 minutes. Other programs run on this machine at the same time: never stop
a process you did not start yourself, so do not kill processes by name (for example `taskkill /IM java.exe` or
`Stop-Process -Name node`); stop only your own processes, by process ID.

When you are done, reply with a short summary: the algorithm, the main choices you made for speed in each
version, and which samples each version passes.
