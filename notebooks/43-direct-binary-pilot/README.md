# Can a model write executable bytes directly?

A processor follows small instructions: fetch a number, add another number, jump to a different instruction, or return an answer. Software developers usually describe the work in a programming language. A compiler translates that description into the instruction bytes the processor can run. Testing whether a language model can supply those bytes itself asks how much of that translation it can carry out without the usual software tools.

Someone building a tiny calculation may want to know whether a model understands a processor's instructions well enough to produce a working function. Someone asking for a program they can launch needs more: an operating system must recognise the file and know where its instructions begin. A useful result must identify which of these capabilities was demonstrated and what kind of work the program performs.

Consider this **illustrative example**, separate from the measured tests. A calculation takes two whole numbers, multiplies the first by 37 and the second by 11, and adds 23. With inputs 2 and 3, the answer is 74 + 33 + 23 = 130. A programmer could write that calculation in a familiar language and ask a compiler to translate it.

The complication is that a processor stores a fixed amount of information in each number. With unsigned 64-bit numbers, adding one to 18,446,744,073,709,551,615 wraps back to zero. That wrap can be part of the requested calculation. A program that works for 2 and 3 has not yet shown that it handles the whole numerical interface correctly.

A file-processing tool adds another kind of work. An integer sorter might receive `3 -1 3 0`, recognise four numbers, keep the duplicate 3, and write `-1`, `0`, `3`, `3` in order. It must find where each number begins and ends, store an unknown number of values within its limit, and write digits back out. Someone using that tool needs the complete file handled correctly, including a clear error if a token is invalid.

There are three practical routes to an executable. The model can write C source and let a compiler translate it. It can choose processor instructions using readable names and let an assembler encode those instructions, then let a linker construct the file. Or it can return every executable byte directly. The last route carries the work of encoding instructions and arranging the file itself. Assembly is the name for the readable instruction language.

An executable also contains information for the operating system: where to load the program and which instruction to start with. ELF is the executable file format used here. The model's direct response must include that information as well as the program logic. Converting its hexadecimal text into bytes is the only preparation allowed on that route; no missing header or instruction is added.

The question is how far this works on five small but different tasks: two numerical calculations and three tools with variable-length input. The file tools are an integer sorter, a binary run-length compressor and an account-total summariser. Within each file task, all three routes must satisfy the same input, output and error contract. Hidden inputs check the result; saved usage records show what generation actually cost.
## Study summary

GPT-6.1 Sol produced 9 fully correct first attempts out of nine complete file-processing programs. Each was checked on 128 hidden files with exact expected output bytes and exit status. There were 0 unreadable or unbuildable/unloadable artifacts. Across all five tasks, 15 of fifteen first attempts passed their whole test set, including the six original numerical artifacts. Those original artifacts include four callable functions and two complete executables, so their interfaces are shown separately in the results.

Direct ELF passed 3/3 programs across the three file tasks; among readable artifacts it passed 3/3. NASM + linker passed 3/3 programs across the three file tasks; among readable artifacts it passed 3/3. C + compiler passed 3/3 programs across the three file tasks; among readable artifacts it passed 3/3.

The 1,920 comparisons evaluate fifteen generated programs, with one generation per slot. The numerical artifacts and all three file tasks are at a correctness ceiling: no case separates the routes. One candidate per slot cannot establish a model's general reliability or a stable ranking of workflows. C and assembly use different external assistance from direct bytes, and C may use a runtime library. No execution-speed or compiler-efficiency claim is tested.

The fifteen calls report 109,522 input tokens and 50,189 output tokens, including 38,965 reasoning tokens. Their recorded standard API equivalent is US$0.698073; actual subscription charges are unavailable. All calls have saved usage records. The result supports the task-specific conclusions below, with exact returned artifacts available for inspection.

Excluding unreadable artifacts does not change the observed ordering of the three file-program routes. This is an ordering of these candidates only, with three tasks per route.

## Contents

- [1. Setup and scope](#1-setup-and-scope)
- [2. Data and exact answers](#2-data-and-exact-answers)
- [3. Three ways to supply a program](#3-three-ways-to-supply-a-program)
- [4. From a response to a checked answer](#4-from-a-response-to-a-checked-answer)
- [5. Correctness across tasks](#5-correctness-across-tasks)
- [6. Token usage and cost](#6-token-usage-and-cost)
- [7. Boundary cases and errors](#7-boundary-cases-and-errors)
- [8. What this result supports](#8-what-this-result-supports)
- [9. Reproduction and saved evidence](#9-reproduction-and-saved-evidence)
- [10. Future work and further reading](#10-future-work-and-further-reading)

```mermaid
flowchart TD
    specs["5 task specifications"] --> requests["15 frozen requests<br/>one first attempt per slot"]
    inputs["640 labelled hidden cases<br/>128 per task"] --> gold["Exact Python answers<br/>integers or output bytes + exit"]
    requests --> model["GPT-6.1 Sol via codex exec<br/>high effort, no observed tools"]
    model --> cache["15 cached responses<br/>raw events and usage"]
    cache --> direct["5 whole ELF byte responses<br/>hex decoding only"]
    cache --> fn["4 numerical functions<br/>2 raw + 2 assembled"]
    cache --> nasm["3 complete NASM programs<br/>assemble + link"]
    cache --> c["3 complete C programs<br/>compile + link"]
    direct --> native["11 executable attempts<br/>Linux loader in Docker"]
    nasm --> native
    c --> native
    fn --> emu["4 functions<br/>CPU emulator"]
    native --> score["1920 planned case comparisons<br/>format, build, load and task checks"]
    emu --> score
    gold --> score
    score --> report["Scores, boundary examples<br/>usage, cost and limitations"]
```

For `sorter-002`, the evaluator keeps the input `3 -1 3 0` out of the model request. Each generated program receives that file only when it runs. The evaluator expects four output lines, `-1`, `0`, `3`, `3`, and exit zero. Assembly and C go through their declared build tools; direct bytes receive no added code. This gives three observations of the same file-processing contract. An artifact rejected before execution still fails its 128 planned comparisons and is reported in its own failure category.

<a id="1-setup-and-scope"></a>

## 1. Setup and scope

This experiment tests one model on five tasks and distinguishes callable functions from complete executable programs. Choosing one model keeps the initial collection small enough to measure usage before designing a broader study. It also means there is no evidence here about which provider or model is better at this task. High reasoning effort is fixed across all fifteen requests; there is no effort sweep or instruction tuning.

| Model | Pinned identifier and revision visibility | Provider and call route | Published size and precision | Output settings | Why included |
|---|---|---|---|---|---|
| GPT-6.1 Sol | `gpt-6.1-sol`; CLI 0.160.1; an immutable dated weight snapshot is not exposed by this route | OpenAI, `codex exec`, fresh ephemeral session per request | Not published | High reasoning effort; explicit default service tier; supported default sampling; neutral base instruction; tools disabled and observed events audited | One current coding model for an existence, complexity and usage test |

The model identifier is fixed, but that is weaker than pinning an immutable weight revision. A future fresh run could receive different model weights under the same identifier. Saved responses preserve the actual evidence for this run. The official model page gives a knowledge cutoff of April 30, 2026; the evaluation inputs were generated on November 3, 2026. [Model documentation](https://developers.openai.com/api/docs/models/gpt-6.1-sol).

Each task group had its requests, input cases, primary score and parsing policy fixed before its calls. The three file tasks were selected after the numerical tasks reached a ceiling; [the protocol history](data/PROTOCOL.md) records that decision. One first attempt occupies each slot. There is no feedback, correction conversation or selection of the best of several candidates. A fresh session does not see another artifact, the hidden cases, the expected answers or a test result. The following setup defines every helper inside the notebook and defaults to replay without model calls.

<a id="2-data-and-exact-answers"></a>

## 2. Data and exact answers

The tasks have exact answers, so no language-model judge grades their behaviour. Python computes the requested numerical results or exact expected stdout bytes and exit status. The model receives a mathematical or file-format specification and a small example, never the hidden case list or reference implementation. All evaluation instances were generated in Python after the documented model cutoff. Familiar algorithms and file-processing patterns may still have appeared in training.

| Task | Contract | Hidden cases |
|---|---|---|
| Affine arithmetic | Return `(37*x + 11*y + 23) mod 2^64` for two unsigned integers | 128 |
| Greatest common divisor | Return the largest common divisor, with `gcd(0,0)=0` | 128 |
| Integer sorter | Read up to 128 signed 32-bit decimal numbers; print ascending canonical values | 128 |
| Run-length compressor | Read up to 4096 arbitrary bytes; emit binary count/value pairs | 128 |
| Transaction totals | Read restricted integer CSV; print account totals in numeric ID order | 128 |


The numerical tasks use 16 boundary pairs, 96 random pairs and 16 pairs with constructed common factors. Greatest common divisor, shortened to GCD, means the largest positive integer dividing both inputs without a remainder. For 48 and 18 it is 6. Unsigned 64-bit values include numbers larger than the largest positive signed value, so the cases also check full-width handling and explicit zero conventions. These two tasks share input pairs but have different expected answers.

The sorter accepts only space, tab and LF as separators. Tokens can have a minus sign and leading zeroes, but cannot have a plus sign or stray characters. Every value must fit a signed 32-bit integer. Empty or whitespace-only input produces empty output. Valid output has one canonical decimal value per line, with duplicates retained. Invalid input must produce exactly `ERR` followed by LF and exit 2, with no partial sorted output. This makes parsing and error handling part of correctness alongside the ordering algorithm.

The compressor uses run-length encoding. It replaces consecutive equal bytes with a count and that byte. For ASCII `AAAABB`, the exact output is hex `04 41 02 42`: four A bytes and two B bytes. Counts occupy one byte and run from 1 to 255. A run of 256 A bytes therefore becomes `ff 41 01 41`, not a zero count or a truncated 255. Input is binary, so zero, 255 and LF are ordinary byte values. Empty input produces empty output. No decoder, file header or output length prefix is requested.

Transaction input begins with exactly `account,amount_cents` followed by LF. Each subsequent row contains an account from 0 through 63 and an integer amount between minus and plus one billion cents. There are at most 128 rows. The last row's LF is optional. Amounts are added per account and output is sorted by account ID, with one line for each account that appeared, including a total of zero. This is a restricted integer CSV task: quotes, blank records, CR and extra fields are invalid. It does not claim support for general CSV dialects or floating-point money.

| File task | Valid files | Malformed files | Boundary coverage |
|---|---|---|---|
| Sorter | 112 | 16 | Signed limits, duplicate values, leading zeroes, empty input, excess count |
| Compressor | 128 | 0 | Binary byte values, 254/255/256 and 510/511 runs, 4096-byte inputs |
| Transactions | 112 | 16 | Header-only input, repeated IDs, zero totals, 128 rows, malformed fields |


There are 16 planned boundary inputs per file task. The sorter and transactions then have 16 malformed inputs and 96 generated valid files; the compressor has 112 further generated binary inputs. These groups deliberately probe specific contracts rather than approximate the distribution of production files. The compressor has no malformed cases because every byte string within the length bound is valid. The exact inputs, expected outputs, exit statuses, group labels and stable IDs are saved in [numerical tasks](data/tasks.json) and [file cases](data/streams_v2/cases.json).

The byte oracles validate entire output streams. Correct numbers with extra spaces, missing newlines, wrong record order, a missing zero-total account, unexpected stderr or the wrong exit status fail the contract. This prevents an evaluator from silently rescuing a near match using a permissive parser. It also means the study can identify formatting mistakes without calling them failures of the underlying sorting or summation algorithm.

<a id="3-three-ways-to-supply-a-program"></a>

## 3. Three ways to supply a program

All three file-processing routes receive the same task contract and must produce a complete executable with the same observable behaviour. Their external assistance differs explicitly. The model does not run tools while generating any response; the evaluator runs build tools only after the assembly and C responses have been saved.

| Route | Model supplies | Evaluator supplies | Interface |
|---|---|---|---|
| Direct ELF | Every file byte as hexadecimal | Whitespace-only hex decoding and executable permission | Whole program |
| NASM + linker | Instructions, labels, sections and startup source | NASM encodes instructions; GNU ld builds ELF | Whole program |
| C + compiler | Complete C11 source with main | GCC at -O2 and normal linking; libc available | Whole program |
| Raw numerical function | Actual instruction bytes as hexadecimal | Argument registers, stack and return address | Callable function |
| Assembly numerical function | Instruction names and labels | Keystone encoding plus the same function harness | Callable function |


Hexadecimal is a transport encoding: two digits specify a byte. Converting `c3` into a byte does not select an instruction, calculate a branch target or fill in a missing header. Direct file responses must contain the whole ELF header, program headers, machine code and any initialised data. Linux uses those headers to locate loadable regions and an entry point. [ELF program-loading specification](https://gabi.xinuos.com/elf/07-pheader.html).

The assembly-file route uses `nasm -f elf64`, then `ld -m elf_x86_64 -e _start`. The model supplies `_start` and its input/output code. NASM resolves instruction encodings and labels, and the linker constructs the executable. The C route uses `gcc -std=c11 -O2 -fno-pie -no-pie`. C may use libc, while direct and NASM programs use read, write and exit system calls. The saved C sorter calls qsort, so its workflow delegates sorting to a library as well as delegating compilation. Both differences are part of the practical workflows being compared. [NASM output formats](https://www.nasm.us/doc/nasm09.html), [GCC optimisation options](https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html).

```mermaid
flowchart LR
    request["One task + output route"] --> call["GPT-6.1 Sol<br/>codex exec, high effort<br/>returns artifact + usage"]
    call --> cache["Save original response<br/>no feedback or repair"]
    cache --> wait["Wait for completion<br/>next independent request"]
    cache --> evaluate["After collection<br/>decode/build and execute"]
```

Fresh sessions run sequentially. No later request sees a previous answer or score. Supported switches disable optional tools; preflight excludes repository instructions, while mandatory CLI context remains. The event audit checks actual tool use rather than claiming a provably empty advertised catalogue. Exact requests and raw events are retained in the numerical and file-task cache directories.

### How the study got here

The numerical tasks produced six correct artifacts and a ceiling, motivating three file tools with parsing, buffers and state. The file routes use matching executable contracts. Each group was fixed before its calls; the complexity progression was chosen after the numerical results. [Dated protocol history](data/PROTOCOL.md).


### An exact file-program request and raw response

This is the complete task request for the direct compressor. It contains the same example and route constraints the model received; none of the 128 hidden files is included.

<details>
<summary>Exact compressor request</summary>

```text
Implement this complete Linux x86-64 command-line program.
Read stdin as arbitrary binary bytes, length 0 through 4096 inclusive. Run-length encode it as binary pairs [count,value]. Count is one unsigned byte 1 through 255. Each maximal run of equal bytes must be emitted as zero or more [255,value] pairs followed by one [remaining,value] pair if a remainder exists. Do not emit zero-count pairs. Empty input produces empty output. Write ONLY these pairs, no header or length prefix, and exit 0. All byte values 0 through 255 are ordinary input data. Example ASCII 'AAAABB' produces hex 04 41 02 42. A run of 256 'A' bytes produces ff 41 01 41. The maximum possible output length is 8192 bytes. All inputs in the stated length range are valid.
The test uses a regular stdin file and EOF; each process handles one file. Stderr must always be empty. No files, network, external commands, testing, compiler, assembler or other tool use during generation. One final artifact only; no Markdown fences, explanations or placeholders.
Return the ENTIRE executable file as a plain hexadecimal string, whitespace allowed, at most 8192 bytes after decoding. Supply every ELF64 header, program header, instruction and any initialised data byte yourself. No wrapper, linker, assembler, fixup or added header will be provided. Use ET_EXEC, baseline integer x86-64, no interpreter or dynamic libraries. Linux read=0, write=1, exit=60; use only these syscalls. Use the stack or your own loadable writable segment for working buffers. A normal base such as 0x400000 and omitted section headers are allowed. All process-entry registers except RSP are unspecified. Return actual hex bytes only, including all zeroes.
```

</details>

The response excerpt below is copied from the saved final response. It shows the beginning of the returned file; the complete unchanged text is in its request-hash cache row under `data/streams_v2/cache/`.

```text
7f454c46020101000000000000000000
02003e00010000007800400000000000
40000000000000000000000000000000
00000000400038000100000000000000
01000000050000000000000000000000
00004000000000000000400000000000
28010000000000002801000000000000
001000000
```

Whitespace-only decoding produces 296 bytes. The first four bytes are `7f 45 4c 46`; the ELF identification and header fields can be inspected before execution. The Linux loader and hidden-output checks below determine whether those bytes form a usable program. The excerpt is an input to validation, while the measured case scores supply its behavioural evidence.

<a id="4-from-a-response-to-a-checked-answer"></a>

## 4. From a response to a checked answer

The scorer first checks delivery: plain hex with an even digit count and the permitted length, or source accepted by the designated build tools. Fenced explanations or malformed artifacts are unreadable. Builds and loader failures remain separate from programs that run incorrectly. The original parser is used throughout; response bytes and source are never repaired.

For a raw function, the evaluator maps its unchanged bytes and a stack in Unicorn, sets the two argument registers, and supplies a return address leading to a stopping point. A finite instruction allowance and timeout stop loops that do not finish. Replay also checks that the stack and required preserved registers are restored, and starts other scratch registers with nonzero values. This helps expose a program that accidentally assumes unrelated registers contain zero. Unicorn emulates CPU instructions; it does not supply a compiler or a Linux process to the function. [Unicorn tutorial](https://www.unicorn-engine.org/docs/tutorial.html).

For a complete executable, the evaluator launches it through Linux in a local restricted container. The numerical programs read 16 bytes and return eight, while file programs receive their complete bounded stdin file and EOF. Expected stdout, exit status and empty stderr must all match. The file-task container mounts only the runner and a job with input cases and source/bytes; it never mounts expected answers or the repository. It has no network and uses an unprivileged account, a read-only root and explicit process, memory, output and time limits. Regular-file input does not establish correct handling of slow pipes or operating-system errors.

### A measured case from request to score

Item `affine-004` uses `x=6` and `y=9`. Its expected value is `37*6 + 11*9 + 23 = 344`. Neither 6 nor 9 appears as that pair in the request example; the only illustrated prompt input was 2 and 3. The raw response was exactly:

```text
48 6b c7 25 48 6b d6 0b 48 8d 44 10 17 c3
```

Decoding the hex yields 14 bytes. A disassembler reads bytes back into instruction names so we can inspect what was generated; it does not change them or help generate them. The observed decoding is:

| Returned bytes | Decoded instruction | Meaning for this case |
|---|---|---|
| `48 6b c7 25` | `imul rax, rdi, 0x25` | Multiply 6 by hexadecimal 25, which is decimal 37: RAX becomes 222 |
| `48 6b d6 0b` | `imul rdx, rsi, 0xb` | Multiply 9 by decimal 11: RDX becomes 99 |
| `48 8d 44 10 17` | `lea rax, [rax + rdx + 0x17]` | Add 222, 99 and decimal 23: RAX becomes 344 |
| `c3` | `ret` | Return to the evaluator with 344 in RAX |

Here the address-calculation instruction `lea` is being used for arithmetic. It computes the sum inside the brackets rather than reading a value from that location. This is a concrete reason to inspect the generated instructions: their familiar names alone can hide what they do in context. The measured output is 344, so this input contributes one correct comparison. Capstone produced the displayed disassembly after generation. [Disassembly documentation](https://www.capstone-engine.org/lang_python.html).

If a program passed 127 of 128 inputs, its input accuracy would be about 99.2%, but its program-pass score would still be a failure. A launchable executable must satisfy the whole tested contract, not just usually return a plausible number. The primary score is the number of programs passing every input. The input counts are supporting evidence about coverage and failures, not independent samples of code generation.

The file-task evaluator first checks response syntax, then assembly/compilation or direct hex decoding, then actual loading and execution. An artifact rejected at one of these pre-execution stages is unreadable for the readable-only score. A loaded program that crashes, times out or emits the wrong stdout, stderr or exit code fails its cases. Valid-case and malformed-case counts are retained separately so ordinary input handling cannot conceal a missing error path. Evaluator-container failures raise an exception instead of counting against the model.

The file harness was checked before generation using binary echo programs through GCC and NASM/ld, exact oracle examples and an invalid ELF file. These controls are evaluator code, excluded from model scores and never sent to the model. The fixed toolchain image, package versions, source commands and resource settings are in [toolchain.json](data/streams_v2/toolchain.json) and [the file-task protocol](data/streams_v2/PROTOCOL.md).

The emulator keeps its 10,000-instruction limit and uses a 0.5-second wall allowance. Cache replay exposed a cold-start false timeout under the original 20 ms allowance; the wider timing margin changes no response or task rule. The native file tests use their separately fixed limits. [Timing amendment](data/PROTOCOL.md).

<a id="5-correctness-across-tasks"></a>

## 5. Correctness across tasks

Read the heatmap by row. Every filled cell represents one generated program tested on 128 cases, and its annotation gives the number of correct cases. Grey cells marked “not run” are deliberately absent conditions. Numerical functions and full programs have different columns, so the small function results cannot be mistaken for complete-file controls. Colour encodes the fraction correct; labels give the exact counts without relying on colour.

![Exact hidden-case scores for fifteen programs across five tasks, with callable functions separated from complete executables.](figures/task_correctness.png)

| Task | Route | Bytes | Cases correct | Artifact stage | Execution failures | Wrong outputs |
|---|---|---|---|---|---|---|
| Affine arithmetic | Raw function | 14 | 128/128 | readable | 0 | 0 |
| Affine arithmetic | Direct ELF | 192 | 128/128 | readable | 0 | 0 |
| Affine arithmetic | Assembly function | 14 | 128/128 | readable | 0 | 0 |
| GCD | Raw function | 28 | 128/128 | readable | 0 | 0 |
| GCD | Direct ELF | 224 | 128/128 | readable | 0 | 0 |
| GCD | Assembly function | 25 | 128/128 | readable | 0 | 0 |
| Integer sorter | Direct ELF | 1348 | 128/128 | readable | 0 | 0 |
| Integer sorter | NASM + linker | 9920 | 128/128 | readable | 0 | 0 |
| Integer sorter | C + compiler | 16016 | 128/128 | readable | 0 | 0 |
| Run-length compressor | Direct ELF | 296 | 128/128 | readable | 0 | 0 |
| Run-length compressor | NASM + linker | 5232 | 128/128 | readable | 0 | 0 |
| Run-length compressor | C + compiler | 15888 | 128/128 | readable | 0 | 0 |
| Transaction totals | Direct ELF | 1152 | 128/128 | readable | 0 | 0 |
| Transaction totals | NASM + linker | 10144 | 128/128 | readable | 0 | 0 |
| Transaction totals | C + compiler | 16048 | 128/128 | readable | 0 | 0 |


Across all tasks, 15/15 programs passed all 128 cases. The matched file-processing comparison gives 9/9 passing programs. The original numerical conditions remain six of six, a ceiling on which no case separates the routes. A program that passes most files still fails the primary all-case score. This strict rule matters for a tool that could silently mishandle a malformed record or corrupt one unusually long run.

Integer sorter: Direct ELF answers 128/128 correctly and passes the whole task; NASM + linker answers 128/128 correctly and passes the whole task; C + compiler answers 128/128 correctly and passes the whole task.

Run-length compressor: Direct ELF answers 128/128 correctly and passes the whole task; NASM + linker answers 128/128 correctly and passes the whole task; C + compiler answers 128/128 correctly and passes the whole task.

Transaction totals: Direct ELF answers 128/128 correctly and passes the whole task; NASM + linker answers 128/128 correctly and passes the whole task; C + compiler answers 128/128 correctly and passes the whole task.

Artifact stage distinguishes response, build and loader failures. Execution failures are crashes or timeouts. Wrong outputs include stdout, stderr or exit-status mismatches after a completed run. None occurred here; the categories remain in the saved scores so future failures can be interpreted correctly.

The valid/malformed table makes a second distinction. Ordinary successful inputs and requested error handling both count in the complete program contract. RLE has no malformed inputs within the permitted size range; every byte value is allowed.

| Task | Route | Valid files correct | Malformed files correct |
|---|---|---|---|
| Integer sorter | Direct ELF | 112/112 | 16/16 |
| Integer sorter | NASM + linker | 112/112 | 16/16 |
| Integer sorter | C + compiler | 112/112 | 16/16 |
| Run-length compressor | Direct ELF | 128/128 | not applicable |
| Run-length compressor | NASM + linker | 128/128 | not applicable |
| Run-length compressor | C + compiler | 128/128 | not applicable |
| Transaction totals | Direct ELF | 112/112 | 16/16 |
| Transaction totals | NASM + linker | 112/112 | 16/16 |
| Transaction totals | C + compiler | 112/112 | 16/16 |


The table prevents a high aggregate score from hiding an error path. Each text program has 112 valid files and 16 malformed files, so a program that ignores every invalid case can still answer 87.5% of its files correctly. That would be inadequate for the specified tool. Conversely, a program that returns `ERR` for every input would pass those 16 error cases without doing the main task at all. The full-case score rejects both behaviours.

File sizes are descriptive. C can include runtime startup and dynamic-library references that handwritten ELF files do not. NASM/ld chooses a normal linked layout rather than the compact single-segment layout used by a direct response. Neither smaller files nor lower generation time establishes faster execution. This study measures generation usage and correctness, with no benchmark of the programs' speed.

<a id="6-token-usage-and-cost"></a>

## 6. Token usage and cost

Output usage has two parts: the returned artifact text and reported reasoning. The CLI exposes total output tokens and a reasoning subset. Subtracting that subset gives final-artifact tokens; adding it to output again would double-count it. The chart stacks these two parts for each response. Labels name the task and route, and the horizontal axis counts output tokens. A missing usage record is marked as unknown rather than treated as zero generated work.

![Reported output tokens separated into reasoning and final-artifact tokens for each generated program.](figures/generation_usage.png)

| Task | Route | Input | Cached input | Output | Reasoning subset | Seconds | API equivalent USD |
|---|---|---|---|---|---|---|---|
| Affine arithmetic | Raw function | 7177 | 0 | 254 | 217 | 9.3 | 0.016894 |
| Affine arithmetic | Direct ELF | 7277 | 0 | 1112 | 935 | 26.1 | 0.025674 |
| Affine arithmetic | Assembly function | 7184 | 0 | 168 | 128 | 8.7 | 0.016048 |
| GCD | Raw function | 7194 | 0 | 496 | 435 | 14.4 | 0.019348 |
| GCD | Direct ELF | 7294 | 6016 | 2639 | 2430 | 56.3 | 0.029548 |
| GCD | Assembly function | 7201 | 0 | 234 | 166 | 7.8 | 0.016742 |
| Integer sorter | Direct ELF | 7394 | 0 | 16408 | 13704 | 333.9 | 0.178868 |
| Integer sorter | NASM + linker | 7350 | 0 | 2829 | 1552 | 70.9 | 0.042990 |
| Integer sorter | C + compiler | 7313 | 0 | 1613 | 700 | 36.0 | 0.030756 |
| Run-length compressor | Direct ELF | 7355 | 0 | 3557 | 3218 | 79.7 | 0.050280 |
| Run-length compressor | NASM + linker | 7311 | 0 | 903 | 456 | 25.3 | 0.023652 |
| Run-length compressor | C + compiler | 7274 | 6016 | 520 | 194 | 14.2 | 0.008318 |
| Transaction totals | Direct ELF | 7441 | 0 | 14592 | 12275 | 295.7 | 0.160802 |
| Transaction totals | NASM + linker | 7397 | 0 | 3382 | 2039 | 71.2 | 0.048614 |
| Transaction totals | C + compiler | 7360 | 0 | 1482 | 516 | 35.4 | 0.029540 |


The saved calls report 109,522 input tokens and 50,189 output tokens, of which 38,965 are reasoning. The standard API equivalent for reported usage is US$0.698073. Usage is available for every call. The API equivalent is calculated at US$2 per million uncached input tokens, US$0.10 per million cached input tokens and US$10 per million output tokens. It is not a subscription invoice. [Published model rates](https://developers.openai.com/api/docs/models/gpt-6.1-sol).

The direct sorter alone used 16,408 output tokens, including 13,704 reasoning tokens, and took 333.9 seconds. Its NASM counterpart used 2,829 tokens and its C counterpart 1,613. Thus the tiny numerical programs did not forecast the encoding work of a parser and sorter. This is one observed generation per route, with the same sorter contract; it does not establish a fixed ratio or a per-byte cost law. Generation time includes service and CLI overhead and is unrelated to native execution speed.

The first numerical artifacts had only 4,903 total output tokens across six calls. Larger program layout can require more reasoning as well as more artifact text, so scaling a budget from returned byte count alone is unreliable. The larger-task measurements are useful evidence for planning another sample at similar complexity, while their one-attempt design cannot estimate a distribution of usage or a worst-case budget.

Input usage includes mandatory CLI context beyond the short task specification. Supported feature disables reduce optional context and prevent tool use, but do not remove all platform instructions. Provider cache reads are reported separately and priced accordingly. Actual subscription quota conversion, electricity and local computing cost were not measured. Replay uses the saved responses and incurs no fresh model spend.

<a id="7-boundary-cases-and-errors"></a>

## 7. Boundary cases and errors

No failure or disagreement was observed on the 1,920 comparisons. Five named file cases below show planned contract boundaries rather than invented errors. Stable IDs connect them to the saved bytes. Each input and expected answer is shared across routes, observed outputs remain unedited, and excerpts are labelled.

### Sorting and duplicate retention

Measured case `sorter-002` is in the `boundary` group. The input has a negative value, a zero and a repeated value. The correct output retains both copies of 3. This checks the actual ordering and file formatting together.

Input:

```text
3 -1 3 0

```

Expected output (9 bytes), with exit 0 and empty stderr:

```text
-1
0
3
3

```

| Route | Observed stdout | Exit | Outcome |
|---|---|---|---|
| Direct ELF | -1\n0\n3\n3\n | 0 | correct |
| NASM + linker | -1\n0\n3\n3\n | 0 | correct |
| C + compiler | -1\n0\n3\n3\n | 0 | correct |

This case passed in 3/3 routes.

Within this planned input group, the correct-file counts are Direct ELF 16/16, NASM + linker 16/16, C + compiler 16/16.

### Signed integer limits

Measured case `sorter-003` is in the `boundary` group. The smallest and largest signed 32-bit integers exercise both comparison and decimal output at the domain limits. The parser must accept these endpoints and reject values just outside them.

Input:

```text
-2147483648 2147483647 0

```

Expected output (25 bytes), with exit 0 and empty stderr:

```text
-2147483648
0
2147483647

```

| Route | Observed stdout | Exit | Outcome |
|---|---|---|---|
| Direct ELF | -2147483648\n0\n2147483647\n | 0 | correct |
| NASM + linker | -2147483648\n0\n2147483647\n | 0 | correct |
| C + compiler | -2147483648\n0\n2147483647\n | 0 | correct |

This case passed in 3/3 routes.

Within this planned input group, the correct-file counts are Direct ELF 16/16, NASM + linker 16/16, C + compiler 16/16.

### A run crossing the count-byte limit

Measured case `rle-007` is in the `boundary` group. A single count byte holds at most 255, so a run of 256 A bytes must become two pairs, ff 41 and 01 41. A wrapped count of zero or a missing final byte would fail exact output and decompression.

Input:

```text
256 copies of byte 41
```

Expected output (4 bytes), with exit 0 and empty stderr:

```text
ff 41 01 41
```

| Route | Observed stdout | Exit | Outcome |
|---|---|---|---|
| Direct ELF | ff 41 01 41 | 0 | correct |
| NASM + linker | ff 41 01 41 | 0 | correct |
| C + compiler | ff 41 01 41 | 0 | correct |

This case passed in 3/3 routes.

Within this planned input group, the correct-file counts are Direct ELF 16/16, NASM + linker 16/16, C + compiler 16/16.

### Combining repeated accounts

Measured case `transactions-001` is in the `boundary` group. Account 17 occurs twice and must total 1525 cents. Account 42 must still appear with minus 300 cents. The output is sorted by account ID, not by input order or amount.

Input:

```text
account,amount_cents
17,1250
42,-300
17,275

```

Expected output (16 bytes), with exit 0 and empty stderr:

```text
17,1525
42,-300

```

| Route | Observed stdout | Exit | Outcome |
|---|---|---|---|
| Direct ELF | 17,1525\n42,-300\n | 0 | correct |
| NASM + linker | 17,1525\n42,-300\n | 0 | correct |
| C + compiler | 17,1525\n42,-300\n | 0 | correct |

This case passed in 3/3 routes.

Within this planned input group, the correct-file counts are Direct ELF 16/16, NASM + linker 16/16, C + compiler 16/16.

### A valid row followed by a malformed row

Measured case `transactions-031` is in the `malformed` group. The first record is valid, but a later amount is not an integer. The whole file must return ERR and exit 2 without leaking partial totals. This checks when the program commits output, not just whether it can add numbers.

Input:

```text
account,amount_cents
1,2
2,bad

```

Expected output (4 bytes), with exit 2 and empty stderr:

```text
ERR

```

| Route | Observed stdout | Exit | Outcome |
|---|---|---|---|
| Direct ELF | ERR\n | 2 | correct |
| NASM + linker | ERR\n | 2 | correct |
| C + compiler | ERR\n | 2 | correct |

This case passed in 3/3 routes.

Within this planned input group, the correct-file counts are Direct ELF 16/16, NASM + linker 16/16, C + compiler 16/16.

![Three direct executable successes showing the input, expected output and matching returned result.](figures/case_panels.png)

The panels show three planned boundary cases because no failures occurred: duplicate retention in sorting, a run crossing 255 bytes, and repeated accounts in a totals file. Each gives the measured ID, direct-byte route, expected and observed outputs. The tables above give the corresponding controls and group counts.

The numerical function example in section 4 remains an end-to-end success: `affine-004` returns 344 from inputs 6 and 9, with all 14 returned bytes shown beside their decoded instructions. The numerical GCD tests also include zero and full-width unsigned values. Those successes locate the simpler end of the tested capability. They do not explain a file-processing failure by themselves; any claim about a broken branch, parser state or address requires inspection of that particular artifact.

<a id="8-what-this-result-supports"></a>

## 8. What this result supports

The evidence now covers five tasks with different demands. The numerical artifacts establish correct small instruction sequences and loadable complete files. The three file tools test parsing, arrays, variable output length and state across records under a matched external contract. The observed answer is 9/9 fully correct file-program candidates and 15/15 fully correct artifacts overall. These are claims about the saved programs, whose exact outputs can be reproduced from the caches.

One first attempt per slot does not measure how often a route will work. There are only three selected file-processing tasks, and a model can vary between generations. Running 128 cases checks an individual candidate more thoroughly, but does not create 128 independent generation trials. The task set was chosen to add difficulties after the numerical ceiling, so it is exploratory evidence about those difficulties, not a random benchmark of software engineering.

The three whole-program routes have the same permitted input and required output, but different assistance. C can call libc; assembly receives an encoder and linker; direct bytes receive neither. That comparison is relevant to someone choosing a workflow, while it does not isolate a single cognitive burden. A failure in direct output may concern algorithm choice, parsing, register use, instruction encoding or executable layout. Aggregate scores alone do not identify which one caused it.

Every task is bounded. Inputs fit within 4096 bytes, arrays have at most 128 items, and account IDs fit a 64-entry table. The tools do not implement general CSV quoting, arbitrary-size files, streaming pipes, a persistent database, concurrency, a user interface or recovery from operating-system failures. Their contracts are useful probes, but these omissions limit how far any success can be carried into a production application.

Direct requests provide an architecture, syscall identifiers and practical ELF guidance. They contain no completed header bytes, source implementation or hidden expected answers. The test therefore concerns implementing a precisely specified program with a known interface. It cannot determine whether the model internally imagined source or assembly before returning bytes; only external tool use and returned artifacts are observed.

The fixed model ID does not expose an immutable weight revision, so fresh generations may change; cached replay preserves the evidence. New input instances prevent lookup of this test set, while the familiar algorithms may occur in training.

There is no compiler-efficiency finding. Native running time, throughput and energy were not benchmarked. Complete-file byte counts include different startup, linking and runtime choices. A compact handwritten ELF and a dynamically linked C program do not have equivalent file-layout overhead. The study reports generation cost and correctness rather than interpreting smaller binaries as faster or better software.

The numerical scorer gained register and loader controls after its initial results; all six scores stayed unchanged. File contracts and controls were fixed before generation, and no response received repair feedback. [Protocol history](data/PROTOCOL.md), [file-task protocol](data/streams_v2/PROTOCOL.md).

<a id="9-reproduction-and-saved-evidence"></a>

## 9. Reproduction and saved evidence

The [executed notebook](43_direct_binary_pilot.ipynb) contains all task generators, request builders, CLI isolation settings, parsers, native runners, CPU-emulation code, scoring and chart helpers. It imports no helper code from the repository. Every model response is saved with its full request, settings, raw CLI events, timestamps and usage. Default execution replays those responses without any fresh model calls.

Install [requirements.txt](requirements.txt) and have a local Linux Docker engine. The numerical executables use the original pinned Python image. The file tools use the compiler image recorded in [toolchain.json](data/streams_v2/toolchain.json), which contains GCC 14.2.0, NASM 2.16.03 and GNU ld 2.44. The recorded image ID pins the environment actually used. Its Dockerfile pins the base digest but does not use a historical package repository, so a later rebuild may differ and must be recorded explicitly.

```powershell
cd notebooks/43-direct-binary-pilot
python -m pip install -r requirements.txt
docker build -t experiment43-toolchain:streams-v2 data/streams_v2/toolchain
python -m nbconvert --to notebook --execute --inplace 43_direct_binary_pilot.ipynb
```

The notebook checks that the recorded toolchain image is available. If a rebuild gives another image ID, an explicit environment override may be used for an execution-environment replication, with that change recorded in the protocol. Replaying the same response bytes on a different compiler, libc or kernel is a different environment check; it does not add a model generation.

Fresh generation requires setting `DIRECT_BINARY_FRESH=1` and having missing request-cache slots. The size knobs are the numerical task count, file task count, model list, output-route list and maximum fresh calls per group. The original groups contain six and nine fixed requests respectively. Frozen request identity is checked, cache entries are reused, and no automatic retry or candidate selection occurs. Changing task prompts or models requires a new protocol entry and distinct frozen requests rather than editing an old result.

The current evidence tables are [results.json](data/results.json), [results.csv](data/results.csv), [case_results.json](data/case_results.json) and [usage_summary.json](data/usage_summary.json). Numerical requests and original artifacts remain in `data/requests.json`, `data/cache/` and `data/artifacts.json`. File inputs, requests, caches, build logs, output streams and compiled/direct hex artifacts are under [data/streams_v2](data/streams_v2/). `engine.py` is a readable snapshot of that run's evaluator; the notebook defines the same helpers internally and does not import the snapshot.

Every fresh call is sent to local Langfuse after caching when its health check and environment credentials permit it. Replay sends nothing. Trace IDs are derived from notebook identity and request hashes to permit deduplication. The original six traces recorded inclusive output usage; the current helper reports the reasoning subset separately. The immutable CLI usage fields are the source for all accounting here, with no double-counting of reasoning.

The combined collection contains fifteen unique request slots and no repair candidates. The recorded API equivalent is US$0.698073 for available usage. All fifteen calls have reported usage. Actual subscription billing is unavailable. Hash manifests normalise Windows CRLF to LF so frozen inputs and response records can be checked across Git platforms. Scratch native jobs and HTML reading copies are ignored. No generated executable is launched directly on the Windows host.

<a id="10-future-work-and-further-reading"></a>

## 10. Future work and further reading

The links below were opened and checked on November 3, 2026 (America/Toronto). They document the interfaces and tools; measured correctness, bytes and token counts come from this study's saved responses.

### Future work

- Generate at least ten fresh candidates for every file-task route using the same fixed contracts. Measure whole-program success and the distribution of token usage. The current one-attempt design and its 9/9 passing file programs cannot estimate repeatability.
- Add a key-value command processor or a small expression evaluator with parentheses. Measure state transitions, parsing failures and exact error handling. The current bounded sorter, compressor and totals table cover only a few interacting components, while the numerical tasks already sit at a ceiling.
- Compare untouched first attempts with a fixed one-diagnostic repair allowance, retaining both results and all costs. Measure how many build, loader and execution failures can be recovered. No present artifact received feedback, so this study cannot tell whether observed problems are cheap to repair.
- Match runtime and linking choices across source and direct-byte routes, then benchmark only candidates proven correct. Measure code size and native throughput on a fixed platform. Current file lengths include different library and linker overhead and cannot answer compiler-efficiency claims.
- Repeat selected tasks on another architecture and at another reasoning effort. Measure instruction/layout failures and complete-contract success per token. The direct sorter's 16,408 output tokens and the smaller compressor request show that one tiny arithmetic sample cannot forecast generation usage at another complexity.

### Further reading

- [ELF program loading](https://gabi.xinuos.com/elf/07-pheader.html) (Xinuos, ELF Object File Format 4.3 draft, accessed 2026). Explains the segment and entry information a complete executable must supply.
- [NASM output formats](https://www.nasm.us/doc/nasm09.html) (NASM contributors, accessed 2026). Describes assembler output formats used to turn the source control into ELF object code.
- [GCC optimisation options](https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html) (GNU Project, accessed 2026). Documents the compiler optimisation setting used for the C workflow.
- [GNU linker command-line options](https://sourceware.org/binutils/docs/ld/Options.html) (GNU Project, accessed 2026). Gives the linker interface used to construct the assembly executables.
- [How SQLite is tested](https://sqlite.org/testing.html) (SQLite contributors, accessed 2026). Shows why boundary inputs, malformed data and independent test machinery matter beyond a few successful examples.
