# V4 design review: high-reasoning Sol recovery

## Decision question

The useful comparison is conditional and paired: among source cases where a high-reasoning GPT-6.1 Sol original answer has a valid parsed answer/schema but at least one wrong field value, does one verifier-guided repair recover all values more often than one fresh Sol retry on the same case? The primary outcome should be a schema-valid answer with all seven target values exact, because this is the extraction recovery the follow-up is meant to test. Evidence support and strict acceptance should be reported separately. Schema-only, evidence-only, transport, or parse failures do not qualify as usable extraction misses. A case counts once in the primary analysis, even if several fields are wrong.

This is a response intervention study, not a model-training experiment. Use the same pinned-by-alias model, high reasoning setting, one-case request shape, answer schema, system/task instructions, timeout, and output limit for both arms. Each selected case gets exactly one fresh retry and one repair. The retry receives only the original task and source packet. The repair receives the same packet plus the original Sol answer and a frozen field-level diagnosis. Run each call in a fresh process/thread so neither arm can see the other arm’s answer. Randomize call order within each pair or counterbalance order across case IDs. Report input/output tokens per arm; matching call counts does not match compute.

The repair diagnosis contains only wrong-field, schema, or evidence flags, plus the original answer; it does not return correct values or gold evidence IDs. This is a combined repair-package comparison because repair sees the original answer and flags while the fresh retry sees neither. It does not isolate the causal effect of feedback alone. Save the exact feedback and label its source clearly. The synthetic verifier’s access to a complete answer key to produce those flags is itself a study limitation.

## Cohorts and stopping rules

Keep the pilot separate from the main cache, cases, metrics, and exports. A pilot of eight cases at each predeclared difficulty level is small. The threshold means three cases with a parsed, schema-valid answer containing at least one wrong value, not three wrong fields within one case. Use the first level meeting the threshold. If no level meets it, use the declared highest-level fallback and report the miss. The pilot is a design screen and must not be presented as a failure-rate estimate.

For the main study, preserve 160 collection cases and 24 separate audit cases. Validate the complete potential set of 240 collection plus 24 audit cases before any main model call. If fewer than 40 of the first 160 original responses have a valid parsed schema and at least one wrong field value, expand once to 240 collection cases using the frozen extension seed and the same source-generation distribution; call only the additional 80, and exclude unused cases from the analysis. If more than 80 cases qualify, select at most 80 by a seeded random priority independent of outcome and error severity. Freeze that selection seed before the first call. If fewer than 40 remain eligible after expansion, run all eligible pairs and treat the resulting comparison as underpowered/descriptive. Never manufacture harder cases or change the threshold after inspecting responses. Evidence-only, schema-only, transport, and parse failures remain in baseline reporting but never trigger expansion or repair selection.

The 24 audit cases must be generated independently of the pilot and collection feedback, excluded from eligibility selection and interventions, and reported separately. They can show whether the high-reasoning baseline transfers to the declared layout/source variation; they cannot establish broad external generalization.

At the planned maximum, 240 collection originals plus 24 audit originals require 264 calls. Up to 80 selected misses add 160 paired intervention calls, for a maximum of 424 model requests. If the run has a hard-stop guard, set it above the predeclared maximum only for logging/repair accounting; do not permit unbounded retries. Report the pilot request count separately. Token use and elapsed time are the relevant available costs if Codex subscription billing does not expose USD charges.

## Analysis plan

For each selected case, record the original miss, fresh-retry outcome, repair-package outcome, and pair type: both recover, retry only, repair package only, or neither. The primary contrast is the paired difference in schema-valid, all-seven-value recovery, with its numerator, denominator, an exact McNemar result, and a paired bootstrap confidence interval. Treat inference as descriptive because cases are difficulty-enriched and may share generation templates. Keep field-level accuracy, schema, evidence, strict acceptance, introduced wrong fields, and repair prompt tokens as secondary measures. Do not count two corrected fields as two recovered cases. Show the full paired contingency table; with at most 80 pairs, a few discordant cases can dominate the percentage.

Selection is conditional on an original Sol value error, so the repair comparison says nothing about all incoming cases. Report baseline accuracy on the full collection before describing the selected cohort. The main cohort size expansion is triggered by usable value misses, so mark it as a predeclared sample-size rule and disclose whether it fired. Keep per-case original, retry, repair, request key, and error fields linked by stable IDs.

## Solvability and source validation before calls

The strongest risk is not model difficulty; it is a synthetic answer key that is accidentally inconsistent with the text. Before any pilot or main calls, independently parse only the rendered model-visible packets and reconstruct every target answer without consulting constructor records, hidden fields, fixture gold, or the primary reducer. The parsed-text implementation should be meaningfully independent: use a different structure and arithmetic path (for example, `Fraction` or integer rational arithmetic for rates versus the generator’s `Decimal` path), not a wrapper around the same helpers.

For every case, save a pre-call audit with the rendered text hash, parsed source facts, selected governing records, exclusions, intermediate unit and price calculations, expected seven-field output, and cited source IDs. Validate that all referenced records and return links actually render, the required evidence is present, and the task instructions tell the model how to resolve each conflict. Run this audit across the complete planned main and audit set before calls. If any case fails, fix the generator and regenerate the entire frozen cohort before collecting responses; do not patch a gold answer after seeing a model response.

The audit should explicitly check:

- recorded-time cutoff and timezone conversion, including events on either side of the cutoff;
- scope, authority, effective time, revision order, and ties for every field;
- movement deduplication, void/reversal behavior, returns, and the original shipment’s unit and allocation basis;
- unit conversions and allocation percentages, including fractional outcomes;
- price tier selection, sequential rebates, fee/credit order, currency, and one declared final rounding rule;
- cancellations, reinstatements, partially amended orders, and whether status is independent of quantity and price;
- all target fields’ required citations and the distinction between value errors and citation errors.

Choose a public, deterministic rounding contract (such as integer half-up at final cents) and use it consistently in instructions, independent audit, verifier, and expected answer. Do not allow Python’s implicit banker’s rounding to decide cases unless that is the explicitly stated business rule. Include boundary cases, but make them calculable from the rendered source alone. If the model is expected to abstain on ambiguity, state that behavior and ensure the gold agrees.

## Protocol decisions and remaining limitations

The study’s target is a narrow paired question on audited synthetic cases. The pilot threshold is the first level with at least three cases that have a schema-valid response and one or more wrong values; if no level reaches it, the protocol uses the predeclared highest-level fallback and reports that the threshold was missed. The main cohort expands from 160 to 240 only when fewer than 40 eligible original misses appear. A seeded random ranking caps interventions at 80 cases, without looking at miss severity. Eligible misses are the unit for selection and analysis, not individual wrong fields.

The repair arm receives both the prior answer and verifier flags. A difference can reflect the answer context, flags, or their combination; the design cannot separate these effects. The synthetic verifier can create accurate field flags from hidden gold, which gives the repair arm information unavailable in an ordinary live workflow. Even a repair win would establish neither training benefit nor deployment performance. A small number of qualifying misses can leave the paired comparison descriptive, and related templates weaken broad statistical generalization.

“High reasoning” is one Codex CLI setting, not a model capability ceiling. The result also depends on the one-case prompt, source renderer, timeout, output limit, and disabled tools. Record the exact invocation and resolved model metadata. A later matched-effort experiment could test other settings, but this design cannot say whether they would change the result.

The independent rendered-text audit is the key solvability check. It should cover every official pilot case before calls and the complete potential collection and audit cohorts before any main call. Agreement between distinct parsers is strong evidence against a label-generation bug, but it does not establish that fictional business rules represent every purchasing organization. Include traceable packet-derived calculations and state that limitation in the final report.
