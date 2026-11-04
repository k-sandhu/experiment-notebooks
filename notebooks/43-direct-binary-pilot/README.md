# Can a model write executable bytes directly?

A processor follows small instructions: fetch a number, add another number, jump to a different instruction, or return an answer. Software developers usually describe the work in a programming language. A compiler translates that description into the instruction bytes the processor can run. Testing whether a language model can supply those bytes itself asks how much of that translation it can carry out without the usual software tools.

That question matters in two different situations. Someone building a tiny calculation may want to know whether a model understands the processor's instructions well enough to produce a working function. Someone asking for a program they can launch needs more: an operating system must recognise the file and know where its instructions begin. A useful result must identify which of these capabilities was demonstrated.

Consider this **illustrative example**, separate from the measured tests. A calculation takes two whole numbers, multiplies the first by 37 and the second by 11, and adds 23. With inputs 2 and 3, the answer is 74 + 33 + 23 = 130. A programmer could write that calculation in a familiar language and ask a compiler to translate it.

The complication is that a processor stores a fixed amount of information in each number. This study uses unsigned 64-bit numbers, which run from zero to 18,446,744,073,709,551,615. Adding one to the largest value wraps back to zero. That wrap is part of the requested calculation, so a program that merely works for 2 and 3 has not yet shown that it handles the whole interface correctly.

One approach lets the model describe the processor instructions using names such as “multiply” and “return.” An assembler turns those instruction names into bytes and calculates their encodings. This removes a clerical burden while leaving the algorithm to the model. Assembly is the name for that readable instruction language.

A second approach asks the model for the bytes themselves. We write them to memory unchanged and check the answer when a processor emulator runs them. There is no assembler in that path. A third approach asks for an entire executable file, including the information Linux needs to load it and the instructions for reading inputs and writing the answer. ELF is the executable file format used for this test.

These are different amounts of work. A working function proves that generated instruction bytes can calculate an answer under a supplied calling convention. A working ELF file also proves that the model can put instructions into a file the Linux loader accepts. Neither result establishes that the model can produce a large application, make it portable, or improve on an optimising compiler.

The question is therefore narrow: can one current coding model produce correct raw functions and complete executable files for two small tasks, on its first attempt, without using generation tools? The assembly version supplies a control for the same calculations, and the saved usage answers a second practical question: how many tokens did those attempts actually take?

## Study summary

GPT-6.1 Sol produced all six requested programs correctly: two raw functions, two complete ELF files, and two assembly controls. Each program passed all 128 hidden input pairs. The complete executable files were 192 and 224 bytes and ran through the actual Linux loader in a local container, with every byte supplied by the model. No compiler, assembler, generated header or wrapper was added to either ELF response.

There were zero unreadable replies, zero execution failures and zero wrong answers. Correctness means the exact requested integer result on all hidden inputs, plus a successful return for functions or exactly eight output bytes and exit status zero for executables. The all-attempt and readable-only scores are both six of six. This is a ceiling: no task separates the formats, and these two familiar algorithms cannot rank methods or establish reliability on larger software.

The six calls used 43,327 input tokens and 4,903 output tokens. The CLI identifies 4,311 of those output tokens as reasoning and 592 as final artifacts. Their standard API equivalent is US$0.124254, including reported input-cache reads. This is a conversion from measured tokens, not an observed subscription invoice. The evidence supports a small existence claim: direct executable generation already works for these cases. It does not test the stronger claim that direct binaries will replace normal software development or outperform compilers.

## Contents

- [1. Setup and scope](#1-setup-and-scope)
- [2. Data and exact answers](#2-data-and-exact-answers)
- [3. Three ways to supply a program](#3-three-ways-to-supply-a-program)
- [4. From a response to a checked answer](#4-from-a-response-to-a-checked-answer)
- [5. Correctness and executable files](#5-correctness-and-executable-files)
- [6. Token usage and cost](#6-token-usage-and-cost)
- [7. Error analysis and boundary cases](#7-error-analysis-and-boundary-cases)
- [8. What this result supports](#8-what-this-result-supports)
- [9. Reproduction and saved evidence](#9-reproduction-and-saved-evidence)
- [10. Future work and further reading](#10-future-work-and-further-reading)

```mermaid
flowchart TD
    spec["2 task specifications<br/>affine arithmetic and GCD"] --> prompts["6 frozen requests<br/>2 tasks x 3 formats"]
    inputs["128 hidden input pairs per task<br/>256 labelled task cases"] --> gold["Exact Python answers<br/>256 expected integers"]
    prompts --> calls["GPT-6.1 Sol via codex exec<br/>6 independent first attempts"]
    calls --> cache["6 immutable cached responses<br/>raw events and usage"]
    cache --> raw["2 raw hex responses<br/>decode bytes only"]
    cache --> elf["2 complete ELF hex responses<br/>decode bytes only"]
    cache --> asm["2 assembly responses<br/>Keystone encodes instructions"]
    raw --> emu["Unicorn CPU emulator<br/>4 functions x 128 inputs"]
    asm --> emu
    elf --> linux["Linux loader in Docker<br/>2 executables x 128 inputs"]
    emu --> score["768 exact comparisons<br/>plus format and execution checks"]
    linux --> score
    gold --> score
    score --> report["6 program scores<br/>token and cost tables, figures"]
```

One measured example is `affine-004`, with inputs 6 and 9. Its specification goes to the model, but its input values stay with the evaluator. The returned raw bytes execute with those numbers in the specified registers. The evaluator compares the resulting 344 with its independently computed 344. The same pair is also tested through the complete file's standard input and the assembled control, so those three observations concern the same calculation. The 768 comparisons are repeated tests of six programs, not 768 independently generated programs.

<a id="1-setup-and-scope"></a>

## 1. Setup and scope

This experiment tests one model in three output formats. Choosing one model keeps the initial collection small enough to measure usage before designing a broader study. It also means there is no evidence here about which provider or model is better at this task. High reasoning effort is fixed across all six requests; there is no effort sweep or instruction tuning.

| Model | Pinned identifier and revision visibility | Provider and call route | Published size and precision | Output settings | Why included |
|---|---|---|---|---|---|
| GPT-6.1 Sol | `gpt-6.1-sol`; CLI 0.160.1; an immutable dated weight snapshot is not exposed by this route | OpenAI, `codex exec`, fresh ephemeral session per request | Not published | High reasoning effort; explicit default service tier; supported default sampling; neutral base instruction; tools disabled and observed events audited | One current coding model for an initial existence and usage test |

The model identifier is fixed, but that is weaker than pinning an immutable weight revision. A future fresh run could receive different model weights under the same identifier. Saved responses preserve the actual evidence for this run. The official model page gives a knowledge cutoff of April 30, 2026; the evaluation inputs were generated on November 3, 2026. [Model documentation](https://developers.openai.com/api/docs/models/gpt-6.1-sol).

The simpler alternative would ask for a familiar source language and run its compiler. That would test source generation and the compiler together. Assembly is a closer control because the model already chooses processor instructions while the assembler handles encodings and label offsets. It is still a different workflow from a model writing all file bytes itself. This pilot measures whether each workflow can succeed, rather than claiming that the three require the same work.

Before collection, the request list, task rules, inputs, primary score and parsing policy were fixed in [the protocol](data/PROTOCOL.md). One first attempt occupies each slot. There is no feedback, correction conversation or selection of the best of several candidates. A fresh session does not see another artifact, the hidden cases, the expected answers or a test result. The following setup defines every helper inside the notebook and defaults to replay without model calls.

<a id="2-data-and-exact-answers"></a>

## 2. Data and exact answers

The tasks use integers so correctness has an exact meaning. There is no model judge and no subjective assessment of style. For affine arithmetic, Python computes `37*x + 11*y + 23` and keeps the low 64 bits. For greatest common divisor, Python's `math.gcd` supplies the expected answer, including the explicitly stated zero cases. The model receives the same mathematical rule and one small example, rather than implementation source or answers for the hidden inputs.

Greatest common divisor, shortened to GCD below, means the largest positive integer that divides both inputs without a remainder. For 48 and 18, both are divisible by 6 and no larger integer divides both, so the answer is 6. A useful program must also cope with one input being zero and with numbers above the largest signed 64-bit value. Unsigned means that every bit contributes to a non-negative value; treating its top bit as a minus sign changes the task.

| Task | Input domain | Requested result | Hidden cases |
|---|---|---|---:|
| Affine arithmetic | Two unsigned 64-bit integers | `(37*x + 11*y + 23) mod 2^64` | 128 |
| GCD | Two unsigned 64-bit integers | Greatest common divisor, with `gcd(0,0)=0` | 128 |

The two tasks deliberately cover different instruction patterns. Affine arithmetic can be a short straight sequence. GCD normally includes a repeated remainder operation, a conditional branch and an exit case. Passing both is more informative than returning a constant or printing a fixed greeting, because the answer changes with hidden input. It remains a tiny sample of software: neither task allocates objects, parses variable-length text, uses a library or maintains state between invocations.

Each task receives the same 128 input pairs. Sixteen explicit boundary pairs include zero, equal values, the largest unsigned number, powers of two, ordinary examples and values on opposite sides of the signed boundary. Ninety-six pairs are generated across the unsigned 64-bit range with a fixed Python seed. Sixteen further pairs share a generated factor. These last pairs help prevent a GCD test consisting almost entirely of random coprime inputs whose expected answer is one.

| Input group | Pairs per task | Why it is present |
|---|---:|---|
| Explicit boundaries | 16 | Exercise zero, overflow, full-width values and ordinary arithmetic |
| Uniform random bit patterns | 96 | Check different unseen numerical inputs without hand-selecting outcomes |
| Constructed common factors | 16 | Make the GCD return values larger than one on a planned group |

These counts describe test coverage, not a representative probability distribution of real programs. The common-factor group is also used for affine arithmetic to keep pairing simple, although its special mathematical structure is relevant mainly to GCD. The exact pairs, group labels, item IDs, creation date, generator seed, ground truth and provenance are in [tasks.json](data/tasks.json). The next step loads that frozen file and verifies its counts; it does not ask another model to create evaluation data.

The inputs are fresh code-generated instances, but multiplication, wraparound and the Euclidean algorithm are familiar concepts that may have appeared in training. Fresh vectors prevent a literal lookup of this saved test set. They do not prove that the model invented an algorithm or can solve an unfamiliar programming problem.

<a id="3-three-ways-to-supply-a-program"></a>

## 3. Three ways to supply a program

The raw-function condition asks for hexadecimal characters representing machine-code bytes. Two hex digits specify one byte: `c3`, for example, is the return instruction used at the end of the saved raw functions. Hexadecimal is a readable transport encoding; converting two digits to a byte performs no instruction selection, compilation, linking or offset repair. Spaces and newlines can be discarded without changing the bytes.

The function interface tells the model where the two inputs arrive and where to leave the answer. RDI and RSI are processor registers, small named storage locations inside the processor. RAX is the return-value register. A calling convention is the agreement about those locations and which other registers a function must preserve. This study supplies the System V AMD64 convention and a fixed function start address. It is not asking the model to infer an unspecified interface. [ABI project](https://gitlab.com/x86-psABIs/x86-64-ABI).

The assembly control has the same interface and byte-size limit, but asks for instruction names and labels. Keystone encodes those instructions after the model finishes. This is the only condition that uses an assembler. It tells us whether the model can select a correct processor-level algorithm when it can delegate the byte encodings. It is not a high-level language or an optimising C compiler baseline. [Keystone's Python example](https://github.com/keystone-engine/keystone/blob/master/bindings/python/sample.py).

The complete-file condition adds startup and input/output work. The model must supply an ELF header identifying the executable, a program header telling Linux what to load, instructions for obtaining two inputs, the calculation, output instructions and an exit. The evaluator converts hex to bytes, marks the file executable inside the test container and launches it. No ELF bytes are generated by the evaluator for this condition. The ELF specifications explain how file headers and loadable segments tell a loader where program content belongs. [ELF headers](https://gabi.xinuos.com/elf/02-eheader.html), [program loading](https://gabi.xinuos.com/elf/07-pheader.html).

| Condition | Model supplies | Evaluator supplies before execution | Where correctness is checked |
|---|---|---|---|
| Raw bytes | Entire function as hex | Hex decoding, registers, stack and a return address | x86-64 CPU emulator |
| Complete ELF | Entire executable as hex | Hex decoding, executable permission and input bytes | Actual Linux loader and process |
| Assembly control | Function instructions and labels | Keystone assembly, registers, stack and a return address | Same x86-64 CPU emulator |

The complete-file requests therefore face a larger interface. Their token counts cannot be interpreted as the isolated cost of “writing binary rather than assembly.” They include headers and file input/output that function requests do not perform. Keeping that distinction visible is essential to understanding both the success and the generation-cost comparison.

The full model-call graph has no chained reasoning agent, retry or hidden repair stage. Every request is an independent terminal call. Calls run sequentially, and the evaluator waits for one response before starting the next; later prompts do not change when earlier responses arrive.

```mermaid
flowchart LR
    req["One frozen task + format request"] --> call["GPT-6.1 Sol<br/>codex exec, high effort<br/>returns artifact text and usage"]
    call --> cache["Save one response<br/>no feedback or retry"]
    cache --> next["Wait complete<br/>start next independent request"]
    cache --> test["After collection<br/>decode or assemble, then test"]
```

The exact raw-function affine request is reproduced below. The other five full requests, including all ELF interface requirements, are in [requests.json](data/requests.json). This excerpt is the actual task text, not a rewritten explanation.

```text
Produce a correct x86-64 implementation of this task.
Given unsigned 64-bit integers x and y, return (37*x + 11*y + 23) modulo 2^64. Overflow wraps. Example: x=2, y=3 returns 130.
No tools, execution, compiler, assembler, external lookup, or testing. Work out the answer yourself. One final artifact only.
Interface: System V AMD64 leaf function. x is in RDI, y in RSI; return the unsigned 64-bit answer in RAX using RET. Preserve RBX, RBP and R12-R15 if used. Function starts at address 0x100000. No syscalls, external calls, absolute addresses, or data outside its code and ordinary stack. Use baseline integer x86-64 instructions.
Return only a hexadecimal string encoding the actual function machine-code bytes, at most 512 bytes. Whitespace is allowed. No prefixes, fences, assembly, comments, explanations or placeholders.
```

The model also receives the neutral instruction “Solve the supplied programming task. Return only the requested artifact. Do not call tools.” Supported CLI feature switches disable shell execution, search, agents, plugins and other optional facilities. A no-generation preflight confirms that repository instructions do not enter the isolated working directory. The CLI still injects mandatory runtime context, and its JSON event stream does not prove an empty advertised tool catalogue. The defensible observation is narrower: all six saved responses contain zero observed tool calls, and none of the returned artifacts was repaired after generation.

<a id="4-from-a-response-to-a-checked-answer"></a>

## 4. From a response to a checked answer

The scorer separates the ability to deliver a readable artifact from the ability to compute the answer. A hex response is readable only if it contains hex digits and whitespace, has an even number of digits, and fits the byte limit. Assembly must be accepted by the designated assembler without explanations or fenced code. A failed parser would be reported as unreadable. All six replies passed their original parser, so no parser change or response repair was needed.

A readable artifact can still be wrong. The operating system may reject a malformed executable, a function may never return, or an apparently valid program may compute the wrong integer. The saved results distinguish execution failures from numerical mismatches. This avoids interpreting a header mistake as evidence of weak arithmetic, while still counting that executable as a failed program.

For a raw function, the evaluator maps its unchanged bytes and a stack in Unicorn, sets the two argument registers, and supplies a return address leading to a stopping point. A finite instruction allowance and timeout stop loops that do not finish. Replay also checks that the stack and required preserved registers are restored, and starts other scratch registers with nonzero values. This helps expose a program that accidentally assumes unrelated registers contain zero. Unicorn emulates CPU instructions; it does not supply a compiler or a Linux process to the function. [Unicorn tutorial](https://www.unicorn-engine.org/docs/tutorial.html).

For a complete ELF, the evaluator writes the exact returned bytes inside an isolated Linux container and launches the file through Linux. The 16-byte input file contains two little-endian unsigned integers: the least significant byte comes first. Output must be exactly eight bytes in the same representation, and the process must exit successfully. Using a regular input file fixes the input delivery assumption stated in the prompt. This study does not test slow streaming input or general handling of operating-system errors.

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

Trusted harness checks exercise an addition function, a deliberately wrong return, an infinite loop, a preserved-register violation, a hand-built valid addition ELF and a non-ELF file. These controls check that the evaluator can see correct execution and reject specific invalid behaviour. They are created by the evaluator, never sent to the model and never counted as model successes. The exact controls and their results are retained in the notebook and [harness_checks.json](data/harness_checks.json).

<a id="5-correctness-and-executable-files"></a>

## 5. Correctness and executable files

Compare the three formats within each task before comparing the tasks. Every bar in the correctness panel counts hidden inputs answered exactly, out of 128. The six bars represent six generated programs. The adjacent panel shows reported output tokens for the same artifacts. Colours identify the formats, and the labels identify both task and format so the comparison does not depend on colour alone. There are no confidence intervals because these are the complete observed results of two selected task specifications, not a random sample of programming tasks.

![All six programs answered 128 of 128 hidden inputs correctly; complete ELF generation used more output tokens than either function format.](figures/pilot_results.png)

All six programs passed all 128 inputs, so all six correctness bars reach 128. The two complete ELF files passed 256 native process invocations combined. The four raw or assembled functions passed 512 emulator invocations. These are 768 exact comparisons of six generated programs. They establish correctness on this frozen suite, not a 768-program success rate.

| Task | Format | Bytes | Hidden inputs correct | Unreadable replies | Execution failures | Numerical errors |
|---|---|---:|---:|---:|---:|---:|
| affine | Raw bytes | 14 | 128/128 | 0 | 0 | 0 |
| affine | Complete ELF | 192 | 128/128 | 0 | 0 | 0 |
| affine | Assembly control | 14 | 128/128 | 0 | 0 | 0 |
| gcd | Raw bytes | 28 | 128/128 | 0 | 0 | 0 |
| gcd | Complete ELF | 224 | 128/128 | 0 | 0 | 0 |
| gcd | Assembly control | 25 | 128/128 | 0 | 0 | 0 |

The all-attempt score is six passing programs out of six. Among readable replies it is also six out of six, because there were no unreadable replies. No item separates the formats: all three methods pass every one of the same 256 labelled task cases. The experiment is at a correctness ceiling and cannot distinguish their reliability. The byte lengths describe artifact size; they do not measure execution speed or prove that one instruction sequence is better.

The strongest evidence for direct binary generation is the complete-file condition. The arithmetic response is a 192-byte ELF and the GCD response is a 224-byte ELF. Both identify machine type 62, Linux's x86-64 ELF machine identifier, use one 56-byte program-header record after the 64-byte ELF header, and begin execution at `0x400078`. That address is 120 bytes after a load base of `0x400000`. Their returned file content, decoded from hex without any added bytes, is in [artifacts.json](data/artifacts.json).

Those first 120 bytes are file and segment metadata. The rest includes program startup, input, calculation, output and exit. This explains why comparing a 192-byte complete file with a 14-byte raw function does not measure waste introduced by the model. They implement different interfaces. A raw function has an evaluator provide inputs and collect a return value. The ELF must arrange the equivalent work itself before Linux can observe an answer.

The assembly control for arithmetic encodes to 14 bytes, the same length as the raw answer, but uses a different temporary register. The GCD control encodes to 25 bytes, compared with the 28-byte raw answer. The raw GCD copies its second argument into another register before looping; the control can loop using the argument register. This is an observed code-size difference on one pair, not an optimisation finding. The complete files also differ in input/output handling, so their lengths include more than the arithmetic algorithm.

<a id="6-token-usage-and-cost"></a>

## 6. Token usage and cost

The original reason to keep the study this small was uncertainty about how much work direct encoding would require. The useful distinction is between the final artifact and the computation used to produce it. The CLI reports total output tokens and a reasoning subset. Subtracting that subset gives the final-artifact token count; adding it to total output again would double-count reasoning.

Before reading the chart, compare the total height with the smaller final-artifact segment. Each bar is one call, with output tokens on the vertical axis. Blue counts reported reasoning and gold counts the remaining output. These are usage records, not a transcript of hidden reasoning or a timing profile of the generated program.

![Reasoning accounts for 4,311 of the pilot's 4,903 output tokens; full ELF GCD is the largest call at 2,639 tokens.](figures/reasoning_usage.png)

Reasoning accounts for 4,311 of 4,903 output tokens, or 87.9%. The final artifacts account for 592. The complete GCD file uses the most output: 2,639 tokens, including 2,430 reasoning tokens and 209 artifact tokens. The arithmetic assembly control uses the least: 168 total output tokens. These observed values replace the unmeasured assumption that a small request would necessarily need several thousand reasoning tokens.

| Task | Format | Input tokens | Cached input | Output tokens | Reasoning subset | Final artifact tokens | Seconds | API equivalent, USD |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| affine | Raw bytes | 7,177 | 0 | 254 | 217 | 37 | 9.3 | 0.016894 |
| affine | Complete ELF | 7,277 | 0 | 1,112 | 935 | 177 | 26.1 | 0.025674 |
| affine | Assembly control | 7,184 | 0 | 168 | 128 | 40 | 8.7 | 0.016048 |
| gcd | Raw bytes | 7,194 | 0 | 496 | 435 | 61 | 14.4 | 0.019348 |
| gcd | Complete ELF | 7,294 | 6,016 | 2,639 | 2,430 | 209 | 56.3 | 0.029548 |
| gcd | Assembly control | 7,201 | 0 | 234 | 166 | 68 | 7.8 | 0.016742 |

The six calls together used 43,327 input tokens, including 6,016 cached tokens, and 4,903 output tokens. Total generation wall time, summed across sequential calls, was 122.7 seconds. It includes service and CLI overhead; it is not the execution time of the generated binaries. There was one cache-reading request and no input cache-write tokens reported. The observations come from one request per slot, so neither a typical latency nor a stable token distribution can be estimated from them.

The two complete-file requests together use 3,751 output tokens. The two raw functions use 750, and the two assembly controls use 402. In this sample, producing the complete file is the largest generation burden. That comparison bundles the ELF headers, file input/output and direct byte encoding, while the assembly conditions return functions. It cannot identify how much of the difference comes from any one of those additions or predict how that difference scales with file size.

The input chart separates uncached and cached input for the same six calls. The horizontal axis counts tokens reported by the CLI, not the number of characters in the visible user prompt. A light segment shows the cached portion of the complete GCD request. No claim about why that single cache hit occurred is needed to compute its price.

![Each call reports about 7,200 input tokens; 6,016 cached tokens occur in the complete GCD request.](figures/input_usage.png)

Input usage runs from 7,177 to 7,294 tokens per call even though each task request is short. The no-generation preflight reports mandatory runtime context beyond the supplied task text. This supports treating CLI input overhead as part of a cost forecast, rather than estimating from the visible specification alone. The preflight counts characters by context block, not tokens, so it does not provide an exact token allocation to each source of that overhead.

At the documented standard rates of US$2 per million uncached input tokens, US$0.10 per million cached input tokens and US$10 per million output tokens, the calculation is `(37,311*2 + 6,016*0.10 + 4,903*10) / 1,000,000 = US$0.1242536`. Without the observed input cache read, the same counts would give US$0.135684. The rounded headline is about 12 US cents, and the saved unrounded figures remain in the results. [Published rates](https://developers.openai.com/api/docs/models/gpt-6.1-sol).

These are standard API equivalents for calls made through the CLI. No API billing route was used to generate the answers. The actual subscription invoice or quota conversion is not exposed, so a measured cash charge is unknown. A cached notebook replay makes zero fresh model calls and has zero additional model spend. Local compute time and electricity were not priced.

<a id="7-error-analysis-and-boundary-cases"></a>

## 7. Error analysis and boundary cases

No model failure or disagreement occurred on the frozen test set. An error section cannot manufacture one to illustrate a category. Instead, the cases below show boundaries a plausible but incorrect implementation could have missed, together with what all three saved artifacts actually returned. The ordinary case in section 4 and these boundary cases supply measured examples with stable IDs. They were selected for their mathematical role from the explicit boundary group; the complete per-input table remains available so these examples do not substitute for aggregate coverage.

### Overflow in the affine calculation

Item `affine-008` has both inputs equal to the largest unsigned 64-bit value, 18,446,744,073,709,551,615. Before reducing to 64 bits, multiplying by 37 and 11 adds up to 48 times that value, then adds 23. Since `48*(2^64-1)+23 = 48*2^64-25`, the requested wrapped answer is `2^64-25`, or 18,446,744,073,709,551,591.

| Case | Expected | Raw bytes observed | Complete ELF observed | Assembly control observed |
|---|---:|---:|---:|---:|
| `affine-008` | 18,446,744,073,709,551,591 | 18,446,744,073,709,551,591 | 18,446,744,073,709,551,591 | 18,446,744,073,709,551,591 |

All three return the required wrapped integer. An implementation that uses only 32-bit intermediate arithmetic could still pass the small request example but fail this case. The observed raw instructions use 64-bit destinations and keep the low 64 bits, which is consistent with the requested wrap. The example supports that particular implementation boundary; the full 128 cases provide broader numerical checks without proving equivalence for all possible pairs.

### A GCD loop with more than one remainder

Item `gcd-005` uses 48 and 18. Replacing a pair with the second number and the remainder leaves its common divisors unchanged: `(48,18)` becomes `(18,12)`, then `(12,6)`, then `(6,0)`. When the second number reaches zero, the first number is the answer, 6.

| Case | Expected | Raw bytes observed | Complete ELF observed | Assembly control observed |
|---|---:|---:|---:|---:|
| `gcd-005` | 6 | 6 | 6 | 6 |

The raw answer contains a conditional jump around the loop for an initial zero and a backward conditional jump after each remainder. Its instruction bytes decode to unsigned division, followed by moving the divisor and remainder into the next pair. A wrong jump displacement could send execution into another instruction or a data region, even if every instruction encoding looked individually familiar. Actual execution succeeds for this case and all 127 other GCD pairs in each format, which tests the assembled branch layout as well as the chosen algorithm.

### Both inputs zero

Item `gcd-000` uses `(0,0)` and has a stipulated answer of zero. The usual remainder operation must not divide by zero. The raw artifact first moves the initial values into working registers, tests the second value, and branches straight to its return when that value is zero.

| Case | Expected | Raw bytes observed | Complete ELF observed | Assembly control observed |
|---|---:|---:|---:|---:|
| `gcd-000` | 0 | 0 | 0 | 0 |

All three produce zero without an execution error. This illustrates why successful numeric output and successful execution are recorded separately. A division exception would fail the program even if a loose scorer happened to fill in a default numeric value of zero. The evaluator never converts an exception or missing output into a correct integer.

### A full-width value returned unchanged

Item `gcd-015` uses the largest unsigned 64-bit value as its first input and zero as its second. Its expected answer is that same largest value. A function that truncates the return to 32 bits or treats it as a negative signed integer would violate the specified result.

| Case | Expected | Raw bytes observed | Complete ELF observed | Assembly control observed |
|---|---:|---:|---:|---:|
| `gcd-015` | 18,446,744,073,709,551,615 | 18,446,744,073,709,551,615 | 18,446,744,073,709,551,615 | 18,446,744,073,709,551,615 |

The complete executable writes eight `ff` bytes for this input, which the evaluator reads as the requested unsigned value. The raw function returns the same bit pattern in its 64-bit return register. This joins the arithmetic contract to the file interface: checking a printed decimal string alone would have tested a different output format from the one requested.

### Opposite sides of the signed boundary

Item `gcd-010` uses 9,223,372,036,854,775,807 and 9,223,372,036,854,775,809. Both numbers are odd and differ by two, so their greatest common divisor is one. The upper input exceeds the largest positive signed 64-bit number. The raw bytes use unsigned division, as the task requires.

| Case | Expected | Raw bytes observed | Complete ELF observed | Assembly control observed |
|---|---:|---:|---:|---:|
| `gcd-010` | 1 | 1 | 1 | 1 |

This case passes in all formats. It was present in the 16-case boundary group before collection, rather than added after noticing which instructions the model chose. It is evidence for full-width handling within the specified domain. It does not test negative numbers, whose meaning is deliberately outside that domain.

The useful missing failure is therefore itself a limitation: these tasks are too easy to expose the boundaries of direct byte generation. There is no basis for claiming that format errors are rare in general. The next experiment should add tasks with more branches, address calculations and data layouts before treating a six-of-six result as a dependable workflow.

<a id="8-what-this-result-supports"></a>

## 8. What this result supports

The complete ELF artifacts establish that a model can already emit bytes that Linux loads and runs correctly for these two tasks. The raw functions separately establish working processor instruction encodings under a supplied interface. The successful control shows that the same model can also express the algorithms in assembly. Those are concrete capability observations, and the saved bytes make them inspectable without relying on an answer that merely claims to be executable.

The result does not test production software. A 192-byte arithmetic program or a 224-byte number-theory program has no graphical interface, authentication system, dependency graph, persistent database or cross-platform build. There are no variable-length structures, heap allocations, floating-point operations or multi-threaded interactions. These omitted requirements are reasons to enlarge the task design, not evidence that the model would either pass or fail them.

The study is an existence test rather than a reliability estimate. There are two chosen algorithms and one attempt per format. Running 128 inputs checks an individual program more thoroughly, but does not create 128 independent opportunities for the model to generate a new program. Repeated fresh generations are needed to measure how often a method succeeds. There is no statistically defensible way to extrapolate this task set into a general binary-writing success percentage.

The direct-format prompts provide architecture, interface, syscall numbers and practical file-format guidance. That is an intentional definition of the task. They contain no reference implementation, header hex template or hidden answers. The experiment therefore asks whether a model can implement a precisely stated small program, not whether it can discover a processor or file format unaided. It also cannot determine whether the model internally pictured assembly or higher-level code before returning bytes; only external tool use and returned artifacts are observed.

Generation was fixed before the answers arrived, and no model was asked to repair an output. Replay added checks for preserved registers and trusted native-loader controls after the initial successful scores were visible; these checks use exactly the same cached responses and leave all six program scores unchanged. The original parser and the numerical task definitions did not change. The dated record and exact scope are in [PROTOCOL.md](data/PROTOCOL.md).

There is also no compiler performance finding. The control is an assembler, which translates chosen instructions. No optimising compiler is given an equivalent high-level source program, and the study does not benchmark native execution speed, memory use or instruction throughput. The slightly shorter assembly GCD function does not establish superiority of either generation path. Claims that AI-generated binaries are more efficient than compiler output remain untested here.

Token usage is useful for planning more pilots of similar size, with the same CLI and effort setting. It is not a per-byte pricing law. The smallest and largest calls differ in task and interface, their inputs include CLI context, and provider caching appears in only one slot. A bigger program could require much more reasoning or fail before it emits any useful bytes. Any larger budget should be based on measured samples at its own complexity level.

For someone deciding what to try next, this evidence supports keeping direct executable generation as a testable approach for small, precisely specified programs. The uncertainty now concerns the point where reliable encoding, file layout and program logic stop fitting into one correct first attempt. More elaborate tasks and repeated generations can locate that boundary; this ceiling cannot.

<a id="9-reproduction-and-saved-evidence"></a>

## 9. Reproduction and saved evidence

Open [the executed notebook](43_direct_binary_pilot.ipynb) to see the complete narrative, exact requests, saved outputs, scorer and chart code. The notebook imports no code from another repository file. All helpers, including the native-runner source, model-call wrapper, parser, emulator and trace helper, are defined in its cells. A normal replay loads the six cached responses, reruns execution checks and redraws figures without any model calls.

Install [requirements.txt](requirements.txt), and have a local Linux Docker engine with the recorded amd64 Python image available. The immutable local image ID is recorded in the notebook and protocol. If that exact image is unavailable on another computer, explicitly record the replacement image and platform before replaying; the original native environment is not promised by a moving image tag. CPU emulation does not require Docker, but complete executable verification does.

```powershell
cd notebooks/43-direct-binary-pilot
python -m pip install -r requirements.txt
python -m nbconvert --to notebook --execute --inplace 43_direct_binary_pilot.ipynb
```

Fresh generation is disabled by default. The size knobs at the top are `N_TASKS`, `MODELS`, `FORMATS` and `MAX_NEW_CALLS`. Setting `DIRECT_BINARY_FRESH=1` explicitly permits missing-cache requests, still capped at six new calls. An existing cache is always loaded rather than overwritten. Changing a prompt or model requires updating the frozen-request record and protocol for a distinct run; replay checks request identity. There is no automatic retry or expansion after a failure.

The primary saved files are [results.csv](data/results.csv), [results.json](data/results.json), [case_results.json](data/case_results.json), [artifacts.json](data/artifacts.json), [tasks.json](data/tasks.json), [requests.json](data/requests.json), [usage_summary.json](data/usage_summary.json) and [preflight.json](data/preflight.json). Individual cache filenames are the full-request hashes and contain request text, command settings, raw CLI events, final response, timing and the provider usage fields. Hex artifacts are also saved separately under `data/artifacts/`. None of those files contains API credentials.

Each fresh request was sent to the local Langfuse instance after the response was cached; all six trace submissions returned HTTP 200. Replay sends no new traces. The original trace helper recorded inclusive output usage as one total; the final helper separates the reported reasoning subset for future calls. The immutable raw cache is the accounting source for the split reported here. A dry-run inspection of the repository backfill path was performed without resending existing pilot traces.

The run contains six completed requests, zero blocked or timed-out requests, zero observed tool calls and zero repair requests. It used 43,327 input tokens, 6,016 of them cached, and 4,903 output tokens. The recorded standard API equivalent is US$0.1242536. Actual subscription charges are unknown. The notebook prints spend at the end and makes fresh replay spend explicit.

<a id="10-future-work-and-further-reading"></a>

## 10. Future work and further reading

The documentation links below were opened and checked on November 3, 2026 (America/Toronto). Sources identify the interfaces and tools; all measured program, byte and usage claims come from this pilot's saved artifacts.

### Future work

- Add a planned complexity ladder: array sums, variable-length text parsing, a small checksum and a stateful parser. Keep the same input contract within each format and measure first-attempt program passes, parse failures and execution failures. The six-of-six ceiling motivates seeking the first complexity level that separates the methods.
- Repeat each task-format pair at least ten times with fresh sessions and fixed settings. Measure the distribution of output tokens, launch success and full-input correctness. One candidate per slot cannot tell whether the observed success or the low output usage is repeatable.
- Add a high-level source condition compiled with a pinned optimising compiler, with an identical program interface and equivalent validation. Only then measure code size and native runtime. The present assembler control and unequal function/file interfaces leave the compiler-efficiency claim unanswered.
- Add an explicitly bounded repair condition that receives one execution diagnostic, alongside untouched first attempts. Measure extra tokens and recovered programs. This pilot used no feedback and observed no failures, so repair value requires harder cases where failures actually occur.
- Run the same specifications on a second processor architecture and at a second reasoning effort. Measure correct encoding, platform-specific failures and usage. The present evidence concerns only x86-64 and one high-effort model configuration.

### Further reading

- [ELF header](https://gabi.xinuos.com/elf/02-eheader.html) (Xinuos, ELF Object File Format 4.3 draft, accessed 2026). Describes the file identification and entry-point fields the complete executable must supply.
- [Program loading](https://gabi.xinuos.com/elf/07-pheader.html) (Xinuos, ELF Object File Format 4.3 draft, accessed 2026). Explains how segment records tell the loader which bytes become a process image.
- [x86-64 psABI project](https://gitlab.com/x86-psABIs/x86-64-ABI) (x86 psABIs contributors, accessed 2026). Maintains the calling-convention specification behind the function interface used here.
- [Unicorn programming tutorial](https://www.unicorn-engine.org/docs/tutorial.html) (Unicorn contributors, accessed 2026). Shows how raw instruction bytes can be mapped and executed independently of a native executable file.
- [Linux x86-64 syscall table](https://github.com/torvalds/linux/blob/master/arch/x86/entry/syscalls/syscall_64.tbl) (Linux contributors, accessed 2026). Gives the operating-system call identifiers used for the complete files' input, output and exit.
