# Hard v2 pipeline review

Reviewed the frozen main artifacts after collection. No request, fixture, score, cache, or export was changed. No model call was added.

## Request and score checks

All 78 cache request hashes match the complete saved requests. All 312 answer records (288 original answers and 24 repairs) match the corresponding parsed raw final response by case ID. Recomputing `hard_validate_answer` reproduces every saved verification object.

The 72 original requests form 20 case-batch groups: 16 collection groups with two draws from each model, and four audit groups with one draw from each model. Within every group, both models receive identical `case_inputs`, prompt messages, source documents, task instructions, and CLI options. Only the requested model and draw metadata differ. Source payloads contain exactly `case_id`, `task_instructions`, and `documents`; evaluator records and gold answers are absent.

All requests finish without a transport or parse error. Every original answer has a valid typed schema. The near-total Luna failure is present in the raw generated values and is not caused by batch-envelope parsing, positional reassignment, a missing source pack, or a stricter citation-only score. The CLI does not return a resolved backend snapshot ID, so the model identity remains the explicitly requested CLI model ID rather than an independently attested immutable snapshot.

All 24 repairs use the other model, preserve the original response, and supply only failed field names, verifier error strings, and the failure category as feedback. No expected field values are supplied. Failed-field lists retain their original field order; saved JSON objects sort dictionary keys, so set equality is the appropriate provenance check when reconstructing those lists from saved verification dictionaries.

## Measured output differences

| Main collection measure | GPT-6 Luna | GPT-6.1 Sol |
|---|---:|---:|
| Original answers | 128 | 128 |
| Valid schemas | 128 | 128 |
| Seven exact field values | 1 | 128 |
| Correct fields and sufficient evidence | 0 | 128 |
| Field-value failure category | 127 | 0 |
| Evidence-only failure category | 1 | 0 |

Luna's wrong fields are quantity in 122/128 answers, price in 94/128, currency in 33/128, shipping date in 33/128, and status in 24/128. An answer can have several wrong fields, so these counts should not be added as independent failed answers. Order ID and SKU are correct in all Luna collection answers.

Luna returns null for all four commercial fields in 33/128 answers. Twenty of those answers still say the order is active. These nulls are literal model outputs even when the source contains known commercial terms. They explain some failures, but they do not establish why the model produced them. A batch-context effect is one possible explanation; there was no single-case control or randomized batch-composition comparison to test it.

For `hard-790f43d1c3111dd59a73`, the target is PO-894574 line L05. Revision 4 sets 11 cartons, the master says 16 units/carton, and the purchase order retains one loose unit. Eligible signed ledger movements total `45 + 19 - 4 = 60`, so the open balance is `11 * 16 + 1 - 60 = 117`. The net price is `275.21 * 0.95 / 16 = 16.34059375` currency units, rounded once to 1,634 cents. Luna's first draw returns 92 units and 1,632 cents. Sol returns 117 and 1,634. This is a field-value disagreement supported by explicit source arithmetic.

The only exact Luna collection answer is `hard-b0b4a037d9e6d95598af:gpt-6-luna:generate:1`. It has the correct quantity 58, but its quantity citations omit the current revision-4 amendment D04 and include older D05. It therefore fails evidence while all seven values pass. This distinct case should not be described as a wrong-value answer.

The audit has 16 different source packs in a different document layout. Sol passes 16/16; Luna passes 1/16. The audit was not used for selection or repairs.

## The adaptive arm has no ranking signal

Every one of the 32 shared cases has at least one Luna value failure. Each of the eight families therefore has four error cases out of four observed cases. With one prior error and four prior cases, every smoothed score is `(4 + 1) / (4 + 4) = 0.625`. The normalized weights are exactly 0.125 for every family, and both the requested quotas and actual adaptive allocation are two cases per family.

The fixed arm also has two cases per family. The adaptive arm did not emphasize harder families. This is not the declared no-error fallback: errors were present, but the coarse family-level signal was equally saturated everywhere. Fixed has 32/64 exact original answers; adaptive has 33/64, with both having 32/64 accepted answers. Those draws are dependent and the source values differ, so the one-answer difference does not establish an adaptive benefit.

## Frontier headroom and repair marginal value

Sol's first draw already supplies exact values for all 64 collection cases. A hypothetical oracle selecting either Sol draw still covers 64/64. Selecting from either model's four original draws covers 64/64. Adding the 24 verified Sol repairs also leaves 64/64. These are oracle upper bounds based on known generated answers, not deployable selectors or evidence of training.

All 24 selected Luna-to-Sol repairs pass, and all started from field-value failures. They correct individual weaker-model answers. They add zero distinct accepted semantic cases because Sol's original answers already cover every collection case. No Sol-to-Luna repair was attempted because no Sol original failed. Zero attempts is not a 0% repair success rate.

The 64 natural preference pairs all reject a field-value-failing original answer. None is merely an evidence-only pair. The accepted export has 64 distinct semantic cases, all already covered by original Sol outputs. This is usable curation evidence for correcting Luna-like outputs, but there is no measured remaining Sol error on which to demonstrate a frontier-model improvement. Sixteen audit cases and eight generated template families do not establish a universal performance ceiling.
