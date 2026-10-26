# Hard main run review

Reviewed 2026-10-24. Read-only inspection of `data/hard_v2/` source packs,
original answers and verification records. No frozen fixture, scoring rule,
pipeline, cache or output was changed. The reviewer authored the fixtures; this
is a source and arithmetic audit, not independent human annotation.

No label bug was found. All 80 saved source packs pass the complete fixture audit
after JSON serialization: gold agrees with the independent event reducer,
documents reconstruct exactly, hashes match and gold responses are accepted.
Eight representative cases below cover all eight families, the only Luna
collection answer with correct values, and the main error boundaries.

## Counts and what fails

Sol has 128/128 collection answers with correct values and accepted evidence.
Luna has one of 128 with correct values, and that answer has genuinely incomplete
current quantity evidence. The other 127 Luna collection answers have value
errors. Its 306 wrong-field occurrences are 122 quantities, 94 prices, 33
currencies, 33 dates and 24 statuses. Order IDs and SKUs are correct throughout.

All 288 original collection/audit answers are present and schema-valid. There
are no transport failures. The collection gap therefore cannot be attributed to
missing replies, malformed JSON or the v1 harmless-context citation problem.
On the 16-case audit, Sol has 16/16 exact and accepted; Luna has one accepted and
15 with value errors.

Every wrong Luna collection currency and date is null rather than an incorrect
non-null code or date. Status mismatches are active reported as ambiguous (13),
ambiguous reported as active (7), and active reported as cancelled (4). These
are incorrect extraction values under the explicit rules. A permitted nullable
schema type does not make an unsupported null correct.

## Eight checked cases

Each quantity calculation excludes MEMO postings, movements after the noon UTC
cutoff, other purchase orders and other lines. Accepted returns have negative
signed units and reopen demand. Price calculations are in cents and round only
the final per-unit result, half up. Sol returns the stated reference values for
all eight cases; the table compares the specified Luna row.

| Case and Luna sample | Source calculation and correct result | Observed Luna result and interpretation |
| --- | --- | --- |
| Scoped revisions, `hard-b0b4a037d9e6d95598af`, sample 1 | D04 revision 4 gives 10 cartons; D01 retains four loose units. Pack size is eight. `10*8+4-(15+15-4)=58`. `16233*0.75/8=1521.84375`, rounds to 1522. | All values, including 58 and 1522, are correct. Quantity citations are D01, D05, D02 and D07. D05 is revision 3 and says nine cartons; D04, which establishes ten, is missing. This is a real evidence-only failure, not rejection of harmless extra context. |
| Same SKU on another order, `hard-2d6075a5ca315345ada4`, sample 0 | Target terms remain six cartons, three loose units and eight units/carton. `6*8+3-(9+2-4)=44`. `22231*0.80/8=2223.1`, rounds to 2223. The other order's amendments cannot change this target. | Returns 42 units and 2223 cents. Quantity is wrong even though the required document groups are cited. The source fixes a unique 44-unit balance. |
| Conditional release, `hard-97be546eaa2e95b6c802`, sample 0 | D05 RELEASED activates D04: eight cartons, three loose units, rebate C12 and date 2026-11-23. `8*6+3-(7+2-6)=48`. `7732*0.875/6=1127.583...`, rounds to 1128. | Returns 40 units and 1072 cents. Status, currency and date are right; both computed values are wrong. No unresolved gate or tie permits an alternative answer. |
| Reinstatement, `hard-776a59cca403be0e648b`, sample 0 | Approved D05 revision 7 says active and overrides D04 revision 3 cancellation. Latest commercial terms and ledger remain: `5*24+3-(38+5-2)=82`; `16515/24=688.125`, rounds to 688. Currency CAD and date 2026-11-10 are known. | Reports cancelled and clears all commercial fields. Both status documents are cited, but the chosen state uses the superseded cancellation. The higher revision unambiguously reinstates the line. |
| Signed shipments, `hard-688b4d82e73e22e16cc9`, sample 0 | `5*16+5-(5+19-4-1)=66`; `33188*0.75/16=1555.6875`, rounds to 1556. No current cancellation or field conflict exists. | Reports active while all four commercial fields are null. Its citations cover the required sources. These are four wrong values, not a citation-only failure or an acceptable abstention. |
| Pack discount, `hard-9c26e2b72dabccd69a0e`, sample 0 | D04 changes list price to 17340 and rebate to E25. `10*16+1-(52+12-6)=103`; `17340*0.75/16=812.8125`, rounds to 813. Currency CAD and date 2026-11-12 remain known. | Reports ambiguous and clears quantity, price, currency and date. An approved partial update replaces the older price/code; it does not create a same-revision conflict. The source is resolved. |
| Equal-revision conflict, `hard-79914b03ce606988d422`, sample 0 | D04 and D05 are both revision 5 but give 12 versus 15 cartons. Quantity is null and status ambiguous. Unchanged price is `15462*0.75/16=724.78125`, rounds to 725. Currency EUR and date 2026-11-02 remain known. | Returns 82 units, active status and 724 cents. It incorrectly resolves the explicit quantity tie and also returns the wrong rounded price. Citing both conflicting messages does not make a non-null quantity valid. |
| Compound reconciliation, `hard-5ea1fe63f453baaa146b`, sample 0 | D09 HOLD keeps D08's conditional terms inactive. D04 revision 4 supplies seven cartons; D01 supplies two loose units; D07 supplies the new carton price and rebate D20. `7*9+2-(3+9-1-5)=59`; `14459*0.80/9=1285.244...`, rounds to 1285. | Returns 43 units and the correct 1285 cents/date/status. Quantity evidence cites older D05 instead of D04. The wrong quantity is independently sufficient for rejection; the missing current source is an additional evidence problem. |

These cases cover ordinary numeric disagreement, unsupported nulls, an invented
conflict, failure to retain reinstated terms, failure to report a genuine
conflict, incorrect final rounding and correct values with a stale citation.
No new failure category suggests an evaluator ambiguity. For example, a real
conflict makes only the affected field null, while a real cancellation clears
the four commercial output fields. The sources distinguish those states.

## Limits on interpreting the large gap

The main collection contains 56 active and eight ambiguous source cases. All
eight `cancel_reinstate` collection cases happen to be reinstated active; none
is finally cancelled. The pilot's only two exact Luna answers were its cancelled
case, and the audit's sole exact Luna answer is also cancelled. That easy null
category is absent from collection, which is a relevant composition difference
when comparing the pilot rate with the main rate. It does not explain away the
observed arithmetic and state errors.

Four cases share each original CLI request, and these models use the same
low-effort setting. Batching, prompt length, output interactions, alias behavior
or the effort setting might affect performance. This run has no matched
single-case/high-effort ablation, so it cannot establish which factor caused
the gap or why Luna returned a particular wrong number. The recorded outputs
support the narrow conclusion: under this fixed protocol and these generated
packs, most Luna answers have wrong commercial values while Sol's answers match
the reference. They do not establish a general model ranking or production
reliability. Sources remain explicit-rule fictional packs rather than real
business correspondence, and no training result is measured.
