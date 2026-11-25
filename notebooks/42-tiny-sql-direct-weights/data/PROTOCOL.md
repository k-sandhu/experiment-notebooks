# Protocol history

## 2026-11-02 to 2026-11-03: original conversation experiments

This is a retrospective archive, not a preregistered trial. Claim https://github.com/k-sandhu/experiment-notebooks/issues/111; branch `add-41-42-direct-weights`. Original artefacts are copied losslessly with hashes in `archive_manifest.json`.

The original task initialized tiny text models, then adopted 50-dimensional frozen GloVe vectors, a shared 50×8 projection, an eight-wide one-block GPT2-style causal transformer, 1,110 vocabulary entries and 2,208 editable values. Teachers alone chose all candidate values. The owner required teacher outputs through tool-free CLI text and tester-only saving/testing, and subsequently required no SQL table creation or execution. The notebook implements only the later parse-only protocol. Obsolete early scaffold functions are archived source, never imported.

Sol's initial and revised outputs, feedback and raw generation records are retained in `history/` and `history/round-02/attempt-02/`. They used different case counts and are not a matched model comparison. An original Astra maximum-effort run was cancelled by the assistant after about 38 minutes before producing a complete vector. That cancellation was a tester mistake, not evidence of a bad network; the record and recovery audit are retained. The restarted Astra xhigh run completed, produced all 2,208 values and was tested unchanged on sixteen cases. Its frozen embeddings matched the original exactly.

Free Nemotron Ultra and Super trials are retained, including an overlong incomplete numerical response and a valid but nearly all-zero candidate. Empty or malformed replies are separate from wrong SQL outputs. No attempt was silently substituted for a successful one.

## 2026-11-03: exploratory diagnostic study

The 388-value MLP and 2,208-value SQL checkpoint were compared descriptively with a pinned Pythia-14m reference. Reference repository `EleutherAI/pythia-14m`, revision `cf967c0a9a04383db6f7b1108d86b2962634b4ac`, Apache 2.0. Checkpoint SHA-256 `116a02532db461f91386a5b20f942ff2c8d4de7341e21b55caafc3d7b25f49a1`. Only reference weights were inspected; no reference generation benchmark was run.

After inspecting raw SQL behaviour, eleven fixed decoding conditions were applied to all 123 schemas. Sampling used three seeds reused across schemas; other conditions used one output per schema. Total 1,845 outputs, float64, maximum thirty-two new tokens, context sixty-four. No grammar, template, name repair or weight modification. Scores use SQLGlot 30.11.0, SQLite dialect, raised parsing errors and conservative SELECT AST schema comparison. No SQL execution. The inverse-standard-deviation gain conditions are diagnostic, not calibrated probabilities. All conditions have zero schema matches. Full generations and requests are cached.

## 2026-11-03: bounded numerical priors

The owner requested numerical ranges, means and additional priors to avoid predominantly zero weights mixed with extreme magnitudes. The prepared `bounded-sql-v1` prompt adds role-specific group means/scales, per-scalar limits, matrix density, layer-normalization gains near one, projection rank/conditioning and softer functional guidance. These are experiment-chosen restrictions informed by initialization and numerical stability, not universal trained-model laws. Previous submission violations are measured under the same validator. Four exact feedback cases are supplied. Teacher xhigh effort, no tools, preserved CLI history and direct last-message capture. All original numbers are saved unchanged; compliance failure would be reported rather than repaired.

The run completed in 964.154 seconds, with 312,108 input tokens, 31,903 output tokens including 22,379 reasoning tokens. All 2,208 values are present, 2,112 changed relative to the previous Astra checkpoint, and frozen embeddings are identical. All hard priors pass. Sixteen raw generations, including twelve cases not in the four-case feedback, yield zero parseable SELECT outputs, zero schema matches and no EOS. The numerical profile improves under its own constraints while the task remains at a floor. This is not a controlled causal ablation of one numerical property.

## 2026-11-03: notebook compilation

Zero fresh teacher calls. Original response/embedding values copied unchanged; the large full GloVe archive and reference Pythia weight file are omitted, with exact frozen subset and pinned reference metadata retained. A self-contained NumPy forward implementation reproduces all sixteen raw strings from each Astra checkpoint exactly. This replay creates no database, imports no historical helper and does not optimize candidate values. Original study source and obsolete early helper code remain evidence only. The MLP analysis and new digits comparison are compiled separately in Notebook 41.
