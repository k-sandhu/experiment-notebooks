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

## Extension to five more languages (2026-11-03)

- Requested after notebook 39 (Rust and Python) merged in PR #108: the same tasks in other widely used languages,
  on branch `extend-39-languages`. The owner chose C++, Java, JavaScript, C# and Go, vendored JSON libraries for
  C++ and Java (the standard libraries have none), and extending this notebook rather than starting a new one.
- Toolchains: MSVC 19.40 from the installed Visual Studio 2022; Oracle JDK 23 and Node.js 22.17.0 already
  installed; .NET SDK 8.0.427 (runtime 8.0.33) installed without admin rights to `D:\projects\toolchains\dotnet8`
  with Microsoft's signed `dotnet-install.ps1`; Go 1.27.3 unpacked to `D:\projects\toolchains\go1.27.3` from the
  official zip (SHA-256 checked against go.dev). nlohmann/json 3.12.0 (identical SHA-256 from the release asset and
  the tagged source) and Jackson 2.22.4 core and databind with annotations 2.22 (SHA-1 checked against Maven
  Central); hashes in `bench/template/vendor_langs.json`. Maven's "latest" annotations entry pointed to a 3.0
  release candidate; the 2.22 line that databind 2.22.4 declares was used instead.
- Inside the Codex sandbox, `javac` could not read jars through a path under the user profile; language sessions
  therefore run under the resolved D: path of the work folder. A `java\run.cmd` wrapper was added after the Java
  classpath command was mangled when typed in Git Bash during a smoke test.
- Harness extension written by GPT-6.1 Terra at high effort (commit `8b4e5d02`): templates, build scripts with
  fixed flags, builds, runs, line counts, start-up baselines, and a stored `request` object (CLI, model, flags,
  prompt, file hashes) in every session's metadata. The 18 earlier sessions were given their `request` after the
  fact; each reproduces its recorded request hash. The main-session hashes were unchanged by the extension.
- Language sessions: heat with both models first (both passed every input), then the other 14, three per model at
  a time; all 16 exited normally with every file present. Claude Sonnet 5.5: 34.2 minutes, USD 3.77. GPT-6.1 Terra:
  27.6 minutes on the Codex subscription.
- Langfuse tracing: the backfill script in `D:\projects\langfuse` was changed to read the prompt from session
  metadata (the CLI receives it on stdin, so it is not in the event stream). The 18 earlier sessions had already
  been sent by an earlier backfill without their prompts; they were not deleted and resent. The two language heat
  sessions finished at the same moment and both trace uploads ran, storing each trace twice; trace uploads now take
  a lock. The other 14 language sessions were traced once each, with their prompts.
- Line endings: Terra's language files were written with CRLF; the working copies were normalised to LF (what git
  stores) and builds, line counts and correctness were run again so recorded source hashes match a checkout.
- Measurement (2026-11-03): the October results moved to `data/results_2026-10-30/`. Builds, line counts and
  correctness 18:35-19:18 EST; a queued timing script started early in a gap between two correctness steps and
  measured start-up times for about a minute while builds ran; it was stopped and its `baseline.csv` deleted.
  Timing from 19:18 to 20:13 EST: start-up baselines, timed runs, size sweep and scaling, all programs of every
  version interleaved per task. Other programs kept a median of 4.4 of 22 logical processors busy. Every run was
  correct.
- Analysis choices made after the results were seen: relative time (to each model's fastest version per task) as
  the main speed summary; memory as peak working set for every task including walkers (at one worker every
  walkers program ran as one process; job commit had counted the Java heap reservation, 645 MB against a 49 MB
  working set); code size in bytes rather than lines, because Terra often wrote several statements per line.

## Seven more models (2026-11-05)

- Requested after the seven-language extension (PR #115, not yet merged): the same programs in every language by Claude
  Opus 5.5, Claude Haiku 5.5, DeepSeek V4.1 Flash (`deepseek/deepseek-v4.1-flash-1017`), GLM 5.3 Flash
  (`z-ai/glm-5.3-flash`), Nemotron 3.5 Super VL (`nvidia/nemotron-3.5-super-vl:free`), Muse Wonder and Muse Wonder
  Full. Branch `extend-39-models`, built on `extend-39-languages`. Both prompts, all templates and the existing
  sessions are unchanged; the 32 Sonnet and Terra request hashes were checked to be identical after the change.
- Harnesses. Opus and Haiku run through `claude -p` exactly as Sonnet does, with the model swapped. Muse models run
  through `muse exec` (Muse Code 1.4.14) with `--reasoning-effort high --yolo --disable-web-tools
  --no-foreign-personal-context` (`--yolo` turns off approvals and the sandbox, as `bypassPermissions` does for
  Claude; no author has web tools). The three open-weight models run inside Claude Code (`claude -p`, same flags as
  Sonnet) pointed at OpenRouter's Anthropic-compatible endpoint through a local proxy (`bench/openrouter_proxy.py`).
  The proxy pins each model to its own lab's endpoint (DeepSeek, Z.AI, and Nvidia, the only free host), removes
  Claude Code's `thinking` field (it turned GLM's reasoning off in a probe) and asks for `reasoning: {effort: high}`;
  every request's provider, token use, reasoning tokens and cost is logged. How much each model reasons per request
  is the model's choice. Background calls naming a Claude model would be rejected by the proxy; none occurred in the
  canaries. The session environment gets a dummy token; the proxy holds the OpenRouter key. The key is still in the
  Windows user environment, which a session with shell access could in principle read.
- Probes before the runs (2026-11-05, scratch, not used in results): a direct `/v1/messages` call per model with and
  without the reasoning fields, and short Claude Code tasks (write and run a small Python script) through a logging
  proxy. All three models used tools correctly and reasoned when asked.
- Implementation. GPT-6.1 Terra was given the change specification but stopped at once on the Codex usage limit
  (reset 2026-11-06 07:24); Claude Sonnet 5.5 (`claude -p`, effort high) wrote the proxy, the runner changes and their
  offline tests instead. Muse transcripts are exported after each session with `muse export` and kept as
  `data/sessions/<model>/<task>[.langs].muse-export.json.gz`, because Muse's `--json` event stream omits tool inputs.
- Canaries: heat, both session kinds, all seven models (14 sessions), then a build and correctness check: every
  program built and was correct on all five heat inputs. At the first launch the proxy's port was still held by a
  scratch probe proxy, so the six OpenRouter canaries stopped before any model call and were launched again.
- Sessions that ended in a harness failure before the model finished were run again once, with the failed run's
  records kept in `data/failed_sessions/`:
  - GLM, heat main: Claude Code exited with Windows status 0xC0000409 after 3 requests, while GLM was streaming a long
    reasoning block (about 8,000 tokens); no program had been written. The rerun completed (37 requests).
  - Muse Wonder, ledger main: the Muse launcher script failed after 1.8 s with "Cannot create a file when that file
    already exists" while updating its update-check file, because two Muse sessions started at the same moment; the
    model was never called. The rerun completed.
- Interruption: the Claude desktop app restarted at 14:38 EST, which ended the session runner, the proxy and the
  sessions in progress. 38 sessions had finished. The others were started again from scratch at 14:43 (a session
  only counts once its metadata is written).
- Langfuse was not reachable during the runs (`localhost:3300` refused connections), so no traces were sent; they are
  to be sent with the backfill script afterwards.
- Nemotron's free tier allows 1,000 requests a day for the account (`free-models-per-day-high-balance`, resetting at
  00:00 UTC). It was used up at 21:54 UTC on 2026-11-05, after about 915 requests from ten Nemotron sessions. From
  then on every Nemotron request got HTTP 429; the proxy retried each for about 20 minutes, and Claude Code ended the
  logscan language session with "Request timed out". Every Nemotron session whose proxy log contains this daily-limit
  429 is run again from scratch after the reset; the failed runs are kept in `data/failed_sessions/nemotron/`.
- GLM, ledger main, reached the 75-minute limit with all three files written. A time-out is the model's outcome under
  the same limit as every other session, so it was not run again; its files are measured as written.
- OpenRouter credits ran out at about 23:00 UTC (balance USD 0.03 of 320; this study had used about USD 7 of the
  key's USD 15.70 that day). From then on DeepSeek and GLM requests got HTTP 402 ("would exceed your available
  credits"); their align and walkers sessions failed and are run again once credits are added.
- Long PATH after the app restart. The restarted desktop app passed a PATH of 7,921 characters to the runner.
  Visual Studio's `vcvars64.bat`, which every C++ build script calls, then fails with "The input line is too long",
  so in the 38 language sessions started after 19:38 UTC the models could not build C++ (the logs show the error 0
  to 58 times per session). Sessions before the restart, and all main sessions (Rust builds do not use vcvars), were
  unaffected. The runner and the measurement now set a short fixed PATH (`config.BASE_PATH`: Windows folders,
  Python, Cargo, Git, Node, Java, the Visual Studio installer folder and the two CLIs; language sessions and builds
  add their toolchains in front). All 38 sessions are run again with it; the affected runs are kept in
  `data/failed_sessions/` (a second failed run of the same session gets a `.2` suffix). The first build and
  correctness pass of the measurement hit the same error on every C++ build; those rows were deleted and rebuilt.
- Transient provider errors that Claude Code retried within a session: two HTTP 520s from DeepSeek and two 404s from
  Nvidia; those sessions finished normally.
- A stale correctness row (2026-11-06): the build and correctness pass was running while Muse Wonder Full's ledger
  language session was rerun. The C# check on the benchmark input started 8 seconds after the new source was written,
  before it was built, and was stored as `build_failed` under the new source hash. That one row was deleted and the
  check rerun (correct). For C# the executable hash in the cache key is that of .NET's launcher stub, identical for
  every C# program, so for C# the key depends on the source hash alone; every run also requires a successful build of
  the current source, so no result was affected.
- Timing on battery (2026-11-06). Springs and heat, whose programs were all final, were timed from 09:22 to 13:30 EST
  while the other sessions waited. The Windows event log shows the laptop had been unplugged at 23:14 the evening
  before, slept with its lid closed from 09:34 to 12:55, and went back on mains power at 13:29. Every program ran 1.6
  to 2.5 times slower than on 2026-11-03 (power plan "Balanced" on battery against "Silent" on mains), and one
  simple-Python springs run spanned the sleep and was recorded as 12,092 s. Rerun on mains power at 13:40, three heat
  programs matched their 2026-11-03 times within 15%. These timings are not used; the files are kept in
  `data/results_battery_2026-11-06/`, and all eight tasks are timed again in one sitting on mains power.
- Power guard. Before the new timing, `bench/measure.py` gained a guard (written by Claude Sonnet 5.5): timed runs wait
  for mains power, and a run is discarded and repeated if the computer slept during it (tick count against unbiased
  interrupt time), if a heartbeat thread in the harness saw a gap of more than 5 s (the process was suspended, as in
  Modern Standby), or, for timed runs, if mains power was lost. Every wait and discarded run is logged in
  `data/results/power_events.csv`. The guard keeps no row it would otherwise have changed, so `HARNESS_VERSION` and the
  cache keys are unchanged.
- Session token counts. A Claude Code session can end with more than one `result` event when the model continues
  briefly after its answer (for example when a background command it started finishes). Each later event reports
  turns and tokens for its own continuation only, while the cost is cumulative, and the runner kept only the last
  event. Six session records undercounted: Opus align (main) and heat (languages), Haiku springs (languages), Nemotron
  walkers (both), and a failed Haiku routes language run (for example Opus heat, languages: 2 turns and 385 output
  tokens recorded, 69 and 69,191 in fact). `bench/sessions.py` now sums turns and tokens over all result events, and
  `python -m bench.sessions refresh-metadata` rewrote those fields from the saved logs (other records gained only a
  `result_events` count). Costs were already right. Fix by Claude Sonnet 5.5, 2026-11-06.
- Nemotron reruns (2026-11-07). The six Nemotron language sessions that had hit the daily limit were run again from
  00:02 UTC, after the reset, two at a time. Five completed (88 to 183 requests each, 611 in all). Logscan's rerun
  stopped before any model call: its work folder held a file named `nul` (written by the earlier session's redirect to
  Windows' null device), which Python's `shutil.rmtree` cannot delete. The file was removed and logscan was run again
  at 01:24 UTC (110 requests). No request in the six reruns got a 429; Nvidia returned 11 transient 404s, which Claude
  Code retried.
- DeepSeek and GLM after credits were added (2026-11-07). The 15 remaining DeepSeek and GLM sessions (the four failed
  main sessions and the eleven language sessions affected by the 402s or the long PATH) were run from 18:00 UTC, six at
  a time. The laptop slept from 18:51 to 03:23 UTC (Windows event log: Kernel-Power 42 at 13:51 EST, then a power
  source change and wake at 22:23 EST; the proxy logs show no request in between). `SetThreadExecutionState` prevents
  only idle sleep. Four sessions were in progress and recorded 523 to 549 minutes of wall time: DeepSeek logscan and
  walkers, GLM wordpairs and logscan (all language sessions). Every request returned 200 after the wake, but in GLM
  wordpairs a test command running across the sleep reached its 300-second tool limit at the wake and was moved to the
  background. The four were run again from scratch on mains power; the runs that spanned the sleep are kept in
  `data/failed_sessions/` with a `.2` suffix. The other eleven finished normally (9 to 49 minutes).
- Line endings (2026-11-08). Six saved source files had Windows line endings (GLM walkers `fast.py`, `plain.py`,
  `go/main.go` and `js/main.js`; DeepSeek logscan `csharp/solution.csproj` and ledger `go/main.go`). The repository
  stores text with LF (`.gitattributes`), so a checkout would not match their recorded source hashes. They were
  converted to LF, rebuilt and checked again (all correct) before the final timing.
- Builds moved aside. `data/results/builds.csv` held build times recorded on battery power or while sessions were
  running; it was moved to `data/results_battery_2026-11-06/` with the battery timings, and every program was built
  again in the final sitting.
- Final timing (2026-11-08). `python -m bench.measure all` ran from 05:40:35 to 10:36:37 UTC on mains power ("Silent"
  power plan, lid open; `data/machine.json` recorded at 05:40:44 UTC). No `power_events.csv` was written: the guard
  never waited for power or discarded a run. Rows: 434 builds, 2,950 timed runs, 2,700 size-sweep runs, 1,095
  scaling runs and 160 start-up runs, all correct; correctness rows from earlier passes were reused where a
  program's source and executable hashes were unchanged. Other programs kept a median of 9.7 of 22 logical
  processors busy during the timed runs (4.4 on 2026-11-03); a sample taken right after the run showed OneDrive's
  sync service using about 4.5 cores. The median coefficient of variation of a program's five repeats was 9 to 14%
  per version (3 to 6% on 2026-11-03).
- Analysis changes after the final results were seen (2026-11-08), all by GPT-6.1 Terra in the notebook code:
  - Stale correctness rows. On 2026-11-06 at 02:47 UTC the harness stored `build_failed` for Muse Wonder Full's ledger
    C++, Java, Go and JavaScript on the benchmark input, before those programs had been rebuilt; the same sources
    were checked again at 05:33 UTC and were correct (only the C# row had been deleted, see above). The notebook took
    the first failing row and dropped those four programs from every analysis. It now keeps the latest correctness
    row for each program, input and worker count (824 older rows set aside, none of them a failure of a current
    program); Wonder Full is 64 of 64 correct and its speed index uses all 64 cells.
  - Stale code-size rows. `loc.csv` keeps one row per version of each source file, so rerun sessions left older rows
    behind and the notebook counted them (GLM showed 667 kB of source instead of 342 kB). It now keeps only rows whose
    key matches the current file (143 older rows set aside).
  - Pooled language-and-model split. The first version fitted one model over all tasks with task, language and model
    terms, which put task-specific language and model differences into the remainder (six languages: 37% language,
    26% model, 36% remainder). It was replaced by adding each part's sum of squares over the eight tasks (46%, 40%,
    14%), which matches the per-task split. The unweighted mean of the per-task shares (46%, 40%) is stored as a
    check in `data/results/derived/language_vs_model.csv`.
  - Figure fixes only: plain tick labels on every log axis, full model names, legend and title wording, compact
    tables.
- Leftover files. Nemotron's walkers JavaScript folder holds five debug scripts it wrote and left (`dbg.js` to
  `dbg5.js`, 9.8 kB). They are part of the saved program, its source hash and its code size; `main.js` does not load
  them. The rerun of that session no longer has the `worker.js` of the failed run, so the file is removed.

## GPT-6.1 Sol and one-reply programs (2026-11-09 to 2026-11-12, UTC)

- Requested by the repo owner after the nine-model timing: GPT-6.1 Sol's sessions for every task, so OpenAI's larger
  model is measured like Terra; then programs from the remaining top models written in single calls without tools,
  to keep their cost down.
- Sol sessions (2026-11-09, 19:58 to 21:32). Author `sol61` (the name `sol` belongs to the heat pilot), `codex exec`
  with codex-cli 0.160.1, `gpt-6.1-sol`, reasoning effort high, the same prompts, templates and runner as Terra.
  16 sessions, none ended by a harness failure. 37.7 M input tokens (36.7 M cached) and 0.56 M output tokens, on the
  Codex subscription; at API list prices (USD 2.00, 0.10 and 10.00 per million input, cached and output tokens) about
  USD 11.2. Build and correctness checks of its 64 programs started at 21:47; all correct.
- One-reply test (2026-11-09, 21:05 to 21:26). `bench/oneshot.py` with `bench/ONESHOT_PROMPT.md`: heat and ledger in
  all eight versions by Claude Haiku 5.5, Claude Sonnet 5.5, GPT-6.1 Sol and GPT-6.1 Terra, 64 calls, tools off and a
  one-line system prompt ("You are a programmer. Answer each request in a single reply. You cannot run code or use
  tools."). 8 of 64 programs failed the samples or the build: Haiku heat C++, NumPy and Java (wrong on the samples) and
  C# (did not compile); Sonnet heat Go and plain Python (wrong) and ledger C# (did not compile); Terra ledger Go (2 of
  3 samples). Sol passed 16 of 16. Spend at list prices about USD 3.5 (Haiku 0.19, Sonnet 1.50, Sol 1.51, Terra 0.34).
  Used only to design the next prompt; not in the results (`data/oneshot_test/`).
- One-reply prompt (`bench/ONESHOT_PROMPT_V2.md`). One prompt per program, with the language's toolchain and build
  settings (`bench/oneshot_languages_v2.json`), the exact run command and argument list, output rules, the task
  spec, an exact input and output contract per task written for this design (`bench/oneshot_contracts/`), and every
  sample of at most 2,000 bytes with its expected output (all four walkers samples). The reply must be one fenced code
  block holding the whole file. Claude: `claude -p --safe-mode --tools "" --system-prompt <one line>
  --no-session-persistence`; Codex: `codex exec --ignore-user-config --ephemeral --sandbox read-only` with
  `model_instructions_file` replacing Codex's own agent instructions. Codex still adds about 12,000 input tokens of
  its own per call. Every call recorded 0 tool calls.
- Gemini 4 Carbon and Argon. Both were to run through OpenRouter's Batch API; the batches were refused with HTTP 402
  (account balance USD 0.46) and Gemini was then left out at the owner's request. No Gemini output exists.
- One-reply run (2026-11-12, 03:49 to 05:52). `python -m bench.oneshot run --protocol v2`, GPT-6.1 Sol and GPT-6 Astra
  through `codex exec`, Claude Fable 5.2 through `claude -p` (Claude Code 2.1.296), effort high, 64 calls each. Every
  reply held one code block; every program built and passed its samples (`data/oneshot/checks.csv`), and the 432
  hidden-input runs of `python -m bench.oneshot hidden` (t1 and full, walkers also at 1 and 16 workers) all passed
  (`data/oneshot/checks_hidden.csv`). Tokens and list-price cost: Sol 0.97 M input (0.42 M cached), 0.34 M output
  (0.24 M reasoning), USD 4.55; Astra 0.96 M input (0.39 M cached), 0.25 M output (0.15 M reasoning), USD 18.41;
  Fable 0.21 M input, 1.39 M output (1.16 M thinking), USD 58.93 at USD 8 and 40 per million input and output tokens.
  Claude Code reported USD 36.83 for Fable, priced at older rates of USD 5 and 25. One Fable reply reached 69,339
  output tokens, past `CLAUDE_CODE_MAX_OUTPUT_TOKENS=64000`, because Claude Code continued it in a second message;
  the harness joins the text of every assistant message, and the program was complete.
- Export. `python -m bench.oneshot export` (written by GPT-6.1 Terra) copied each one-reply program with the files an
  agent session leaves (`Cargo.toml`, `go.mod`, `solution.csproj`) into `data/programs/` as authors `sol61-oneshot`,
  `astra-oneshot` and `fable-oneshot`, with a `meta.json` naming each program's request hash. A second export
  changed nothing.
- Timing (2026-11-12). `bench.measure` build, loc, correct and bench for the four new authors from 15:15:47 to
  16:31:47, then `anchor` (Opus 5.5's 64 programs re-timed on the full inputs, 1 worker, 5 repeats, into
  `data/results/anchor_20261112.csv`) to 16:40:25, then sweep and scaling to 16:55:03. Mains power, lid open, the
  desktop app's keep-awake on and a helper holding `ES_SYSTEM_REQUIRED`; no `power_events.csv` was written. Rows:
  192 builds, 1,440 correctness runs (from 2026-11-09 on), 1,280 timed runs, 320 anchor runs, 1,152 size-sweep runs
  and 480 scaling runs, all correct. Every timed program got 5 repeats.
- Drift between the two timing days. Opus 5.5's re-timed programs took 0.938 times their 2026-11-08 medians
  (geometric mean of 64 per-program ratios; range 0.78 to 1.10; 19 more than 10% from 1.0, none more than 25%). Other
  programs kept a median of 6.4 logical processors busy during the 2026-11-12 runs against 9.7 on 2026-11-08. The
  notebook divides every 2026-11-12 run time by the measured factor before comparing it with the first day.
  The correction was chosen after the anchor and the new authors' times had been seen. A per-program correction
  (each new program divided by the ratio of Opus's program for the same task and language) gives exactly the same
  overall speed indices, because the geometric mean of the 64 per-program factors is the global factor; only the
  breakdowns by task and version differ. Both are in `data/results/derived/model_speed_drift_variants.csv`.
- Analysis changes (2026-11-12). The notebook code was written by Claude Sonnet 5.5, because GPT-6.1 Terra's Codex
  sandbox could not write to the notebook file: Sol joins the agent-session models, so the speed index's
  reference is the geometric mean of ten models instead of nine, which moves every model's index slightly; the
  language-and-model split now uses ten models. The one-reply authors are scored on the same scale but kept out of
  the split and the run-time and language summaries.
