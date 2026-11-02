# Notebook 39 protocol and run history

Records for someone checking the work. The README and notebook summarise the parts that change how far to
trust the result. All times are local (EDT, UTC-4) on 2026-10-30 unless marked UTC.

## Design fixed before any author session

- Question, task list, measures and author prompt: claim issue
  [#103](https://github.com/k-sandhu/experiment-notebooks/issues/103), opened before any file was written.
- Eight task specs (`bench/tasks/*/SPEC.md`) and the author prompt (`bench/AUTHOR_PROMPT.md`) were written by
  Claude Opus 5.5 and committed in `74d7ed61` (12:07).
- The harness (generators, reference solutions, independent second implementations, comparators, session
  runner, Windows job-object measurement) was written by GPT-6.1 Sol at high effort (`codex exec`) and reviewed
  before commit `3685b2eb` (13:21). The reference solutions agree with the second implementations on all 55
  inputs (`data/reference_agreements.csv`).
- Changes made after Sol's review and before any session, all in `3685b2eb`:
  - springs benchmark size raised from S = 5,000 to S = 15,000 steps, because the reference finished in 5.6 s
    and a Rust version would have been too fast to time well;
  - ledger and logscan file sizes in the specs corrected to what the generator writes (about 380 MB and
    230 MB);
  - heat spec: "The grid contains at least one open cell"; align spec: use the substitution costs as given;
  - small alignment inputs given at least six string pairs (linear scaling had left one pair);
  - comparator: a well-formed output with missing or extra rows is `wrong`, not `unreadable`;
  - author sessions run with an environment stripped of the launching agent's `CLAUDE*`, `ANTHROPIC_*`,
    `OPENAI_*` and `CODEX_*` variables (the launching session had `CLAUDE_EFFORT=xhigh`, which could have
    overridden `--effort high`);
  - `codex exec --ignore-user-config` needs `-c approval_policy="never" -c windows.sandbox="elevated"`, found in
    a smoke test where every command was blocked without them.
- Large `s3` sample inputs are git-ignored; they regenerate byte-identically from the generator and are pinned
  by SHA-256 in `inputs_manifest.json`.

## Author sessions

1. Pilot (13:10-13:34): heat only, Claude Opus 5.5 (`claude -p`, effort high) and GPT-6.1 Sol (`codex exec`,
   effort high), to test the pipeline end to end. Both passed every sample. Kept as `data/programs/opus/heat`
   and `data/programs/sol/heat` with their logs; measured alongside the main heat programs as a side
   comparison.
2. First parallel run (13:34-13:38), Opus 5.5 and Sol, six sessions at once: lost. About four minutes in, the
   Opus wordpairs session ran `taskkill //F //IM python.exe` to clean up its own benchmark processes. That
   killed every Python process on the machine, including the session runner; the runner's job objects
   (kill-on-close) then ended all six sessions. Partial logs are kept outside the repository; no program from
   this run is used.
3. Model change (13:40): the user was running short on Opus and Sol quota and asked to move to Claude Sonnet 5.5
   and GPT-6.1 Terra, for all 16 sessions including heat, so that one model pair wrote everything. At the same
   time one sentence was added to the author prompt: never stop a process you did not start, and never kill
   processes by name. Commit `1accd719`.
4. Main run (13:43-14:17): 16 sessions, three per model at a time, all exited normally, none timed out, no
   program file missing. Claude Sonnet 5.5: 80.4 session-minutes, USD 4.18. GPT-6.1 Terra: 24.7
   session-minutes, 2.2 M input tokens (mostly cached) and 43 k output tokens on the Codex subscription.
   Commit `47f6cbe4`.

## Measurement

- Machine: Intel Core Ultra 9 185H (6 performance cores with two threads each, 8 efficiency cores, 2 low-power
  cores; 22 logical processors), 31.4 GB RAM, Windows 11 build 26300, power plan "Turbo", on AC power.
  Python 3.13.5, NumPy 2.2.6, rustc and cargo 1.99.0. See `machine.json`.
- Single-threaded runs were limited to the 12 performance-core logical processors through a job-object
  affinity; walkers runs could use all 22.
- Order (all UTC): correctness 18:28-18:34, timed runs 18:35-19:07, size sweep 19:07-19:10, scaling
  19:12-19:17. Timed runs: one warm-up and five interleaved repeats per program, in an order shuffled with a
  fixed seed. Sweep and scaling: one warm-up and three repeats.
- The machine was not idle. Other agent sessions, a browser, the ChatGPT app, WSL and antivirus scanning were
  running. During the timed runs the rest of the machine kept a median of 7.8 logical processors busy
  (maximum 20.6; column `other_busy_cores`), and only about 3.8 GB of RAM was free at one check. The median
  coefficient of variation over the five repeats is 8.5%; sub-second heat runs vary by 20-30%, and one springs
  Rust program had one repeat five times its fastest. Reported numbers are medians with min-max ranges.
- Peak memory is the main process's peak working set (Windows' equivalent of peak resident memory), except
  for walkers, where the job's peak commit is used because the Python versions start worker processes. A
  Windows console host joins each job and adds about 1 MB of commit; working set excludes it.
- After the measurements, the notebook's work folder (3.8 GB of inputs, builds and session folders) and its
  worktree were moved from C: to D: at the user's request (C: was 98% full). A directory junction at the old
  path `C:\Users\sandh\nb-work\39-rust-vs-python` keeps recorded paths and cache keys valid.

## Analysis

- The notebook code (tables and figures) was written by GPT-6.1 Terra at high effort from a written
  specification. Claude Sonnet 5.5 then changed six figure cells (start-up floor legends, data-driven titles, the
  "faster Python version" comparison, pilot authors removed from the size sweep, the multi-task reference file
  removed from the code-size panel) and fixed a pandas deprecation in the correctness cell. The narrative was
  written by Claude Opus 5.5.
- One number in the error analysis comes from a separate check, not from the saved tables: on 2026-10-30, after
  the measurements, `np.fromstring(text, dtype=np.int64, sep=" ")` took 2.43 s on the routes benchmark input
  (2,700,006 numbers) and `list(map(int, text.split()))` took 0.32 s, run once each with Python 3.13.5 and
  NumPy 2.2.6.
- Memory in the notebook and README is in decimal megabytes (10^6 bytes).
- No analysis choice was preregistered beyond the measures listed in the claim issue. The headline statistic
  (geometric mean over tasks of Rust's speed-up over the faster of each model's two Python versions) was chosen
  after the timing results were seen, because every program was correct and the "faster of the two Python
  versions" is the comparison a developer choosing between them would make. The notebook also reports the
  speed-up over each Python version separately.
