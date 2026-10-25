# Sol-targeted pilot review

Reviewed all three saved pilot levels without changing any fixture, helper, cache, score, or output. No model call was added.

## Saved-request and score checks

All 24 request hashes match the complete saved requests. All 48 model answers match the parsed raw final responses by case ID, and recomputing `sol_validate_answer` reproduces every saved verification object. Every recorded batch position points to the correct case ID.

The 12 source-batch groups contain one request for Sol and one for Luna. Both models receive identical prompt messages, case-input objects, task instructions, and source documents within each group. Model payloads contain only case ID, task instructions, and documents. No gold answers or evaluator records enter those inputs.

There are no transport failures, parse failures, or invalid answer schemas. All pilot answers are usable replies, so the two Sol errors qualify for the declared value/schema criterion. No missing reply or envelope error is counted as a difficulty signal.

## The declared threshold was not reached

| Pilot level | Sol exact values and accepted | Sol qualifying misses | Luna exact values and accepted |
|---|---:|---:|---:|
| 1 | 7/8 | 1 | 0/8 |
| 2 | 8/8 | 0 | 0/8 |
| 3 | 7/8 | 1 | 0/8 |

The frozen rule requires at least two Sol value/schema misses within one eight-case level. No level meets that threshold. The saved ladder correctly chooses level 3 using the declared highest-level fallback and records `threshold_met=false`. It does not claim a threshold crossing.

Sol has two genuine field-value disagreements across 24 pilot cases. It has no evidence-only or schema failures. These results establish observed quantity mistakes under the low-reasoning, tool-free setting; they do not establish that error rates increase with the numerical difficulty level. Each level also uses different source facts and only eight cases.

## Traceable Sol disagreements

| Level | Case ID | Family | Expected open units | Sol returned | Other fields |
|---|---|---|---:|---:|---|
| 1 | `recon-bb2bfec51726935a1e53` | effective_authority | 15,780 | 15,680 | All six correct |
| 3 | `recon-1be419cf8d966fa3c2e5` | dated_uom_returns | 21,402 | 21,392 | All six correct |

Both failures have the sole verifier reason `Wrong value: quantity_units`; all seven evidence checks pass. The differences of 100 and 10 units are present literally in Sol's raw cached JSON. They are not caused by a citation policy or a parser converting valid values into missing answers. The fixture reviewer independently reconstructed both quantities from the rendered packets:

- Level 1: `16,922 - (1,152 CASE-derived units + 22 EA units + 112 BOX-derived units - 144 returned units) = 15,780`.
- Level 3: `25,176 - (3,528 CASE-derived units + 78 EA units + 384 BOX-derived units - 216 returned units) = 21,402`.

The required sources are present and neither label is ambiguous under the stated rules.

The main experiment should retain the declared fresh seeds, selected level 3, and separate audit. Pilot cases must not become main repair cases. Any paired repair estimate will be conditional on the actual original Sol misses found in the new 48-case collection, which may be fewer than the cap of 24.
