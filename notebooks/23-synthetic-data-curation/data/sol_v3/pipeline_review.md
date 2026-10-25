# Sol-targeted main pipeline review

Reviewed saved main artifacts after collection without changing any generating helper, fixture, cache, label, score, or export. No model call was added.

## Lineage and treatment checks

All 66 complete request hashes match their cached requests. All 129 response rows, comprising 120 original replies and nine intervention replies, match the raw parsed final JSON by case ID. Recomputing the frozen verifier reproduces every saved verification object, and recorded batch positions match case IDs.

The 60 original requests form 30 Sol/Luna source-batch pairs. Within every pair, case-input objects, source text, task instructions, prompt messages, and CLI options are identical. Each input object contains exactly case ID, task instructions, and documents. No evaluator metadata or gold answer is in the model payload. All requests complete without transport or parse failure, and all replies have valid typed schemas.

The selected set is exactly the three usable original Sol collection replies with a field-value failure. It matches stable case-ID ordering and includes all eligible misses because three is below the cap of 24. Luna-only, evidence-only, audit, transport, and missing-response errors do not enter selection.

All intervention arms cover the same three source cases in the same ordered batches, of sizes two and one. Their source hashes match the originals. Fresh retry uses Sol generation with a new draw identity and no prior answer or feedback. Self-repair and cross-repair receive identical prompt messages, original Sol responses, and generic field/category feedback; the requested model differs. Feedback contains failed field names and fixed category flags, with no expected numeric or string values. Each arm has two requests and three item attempts.

## Baseline and paired result

| Original split | Sol exact values and accepted | Luna exact values and accepted |
|---|---:|---:|
| Collection | 45/48 | 0/48 |
| Audit | 12/12 | 0/12 |

The three original Sol misses contain four incorrect field values: quantity on all three cases and price on one. Every other original Sol field is correct. There are no Sol evidence-only or schema failures in this run.

| Intervention on the same three Sol misses | Exact values | Values and evidence accepted | Original wrong fields fixed | New wrong fields introduced |
|---|---:|---:|---:|---:|
| Fresh Sol retry | 3/3 | 3/3 | 4/4 | 0 |
| Sol self-repair | 3/3 | 3/3 | 4/4 | 0 |
| Luna cross-repair | 0/3 | 0/3 | 0/4 | 0 |

The self-repair versus fresh-retry paired table has three joint successes and no discordant cases. There is no observed self-repair advantage over a fresh Sol attempt on these three items. Each Sol arm adds three distinct accepted cases beyond the two models' original answers, raising collection coverage from 45 to 48 cases. Luna adds none. No model weights are updated, and the audit is not rerun after intervention.

The control uses the same selected-case batches as the feedback arms. Original baseline batches may have different neighboring cases, so the result controls for a fresh attempt and the intervention batch context together; it does not isolate sampling randomness from every batch-context effect. Three selected cases are too few to establish that the strategies are equivalent in general.

## Luna changes the answers but increases existing errors

All three cross-repair answer objects differ from their original Sol answer objects. None is an unchanged copy. Luna changes the already incorrect quantities, and also the already incorrect price in the third case, while retaining originally correct fields.

| Case ID | Family | Correct quantity | Original Sol quantity | Luna cross-repair quantity | Absolute quantity error, before to after |
|---|---|---:|---:|---:|---:|
| `recon-04f699622fa7f55b9095` | shipment_revisions | 21,547 | 21,537 | 21,513 | 10 to 34 |
| `recon-80db4a9463ee61051565` | effective_authority | 21,812 | 21,752 | 21,716 | 60 to 96 |
| `recon-846f392a960804bf5282` | dated_uom_returns | 21,788 | 21,778 | 21,465 | 10 to 323 |

The third case also has a correct unit price of 909 cents. Original Sol returns 908 cents; Luna returns 482 cents, increasing absolute price error from one cent to 427 cents. The saved `new_wrong_fields=0` statistic is accurate but incomplete as a description of quality: it counts formerly correct fields that become wrong, not worsening magnitude on a field that was already wrong. These absolute-error comparisons are post-collection diagnostics and do not replace the frozen primary metric.

## Citation sensitivity check

For each of the 129 replies, I considered an in-memory response that adds P01 only to a failing quantity citation list when P01 is absent. Zero quantity-evidence failures become valid by that addition alone. Zero otherwise correct, rejected replies become accepted by that addition alone. The observed P01-only affected count is therefore zero; no score or source artifact was changed.

This check does not prove that the evidence policy is correct for every possible response. It establishes that the measured Sol value misses and the three-arm result are not a P01-only citation artifact in these saved replies.

## Calls, usage, and curated examples

| Intervention | Requests | Item attempts | Input tokens | Output tokens | Summed subprocess seconds |
|---|---:|---:|---:|---:|---:|
| Fresh Sol retry | 2 | 3 | 51,057 | 1,238 | 20.00 |
| Sol self-repair | 2 | 3 | 51,606 | 1,349 | 26.48 |
| Luna cross-repair | 2 | 3 | 50,220 | 416 | 10.00 |

Item and request budgets match. Token budgets do not. Token accounting can differ across model backends even when their source prompts or repair prompts match. Summed subprocess time is not orchestration wall time because calls run concurrently, and two requests per arm are not a latency benchmark. Dollar spend is unavailable from this CLI and must not be reported as zero.

The original export contains 45 distinct accepted collection cases and no value-preference pairs correcting an original Sol miss. Fresh retry and self-repair each contain three accepted records and three preference pairs oriented from the actual wrong original Sol answer to a verified corrected answer. Cross-repair has zero accepted records, three rejected records, and zero preference pairs. The three cases are shared between the two successful arms; those six pairs are not six distinct corrected source cases. Audit examples do not appear in any training-style export.

The experiment finds real Sol errors under the declared low-reasoning, tool-free setting. It also shows why reporting only self-repair success would overstate the evidence: a fresh attempt recovers the same three errors. The bounded pilot did not meet its declared two-errors-in-eight threshold, so level 3 remains the honestly reported fallback choice.
