# Hard pilot review

Reviewed 2026-10-24. Read-only inspection of the eight frozen cases and 32 original
answers in `data/hard_v2/pilot/`. No fixture, pipeline, response, cache or scoring
rule was changed. This reviewer authored the fixtures; the check below reads the
saved source text and independently calculates examples, but is not independent
human annotation.

The pilot is clear to proceed to the main run under the frozen protocol. All
eight saved cases pass the complete fixture audit after JSON serialization,
including exact document reconstruction, independent event reduction, hashes and
gold-response acceptance. Manual checks of the rendered target rows, amendments,
carton master, rebate schedule and ledger agree with gold. No incorrect or
ambiguous label was found among the rejected answers.

Sol has 16/16 exact and accepted answers. Luna has 2/16 exact and accepted answers.
All 14 rejected Luna responses have genuine field-value errors, and none is an
evidence-only failure. All 32 responses have valid schemas. Luna's 14 rejected
responses contain 32 wrong-field occurrences: 12 quantities, nine prices, five
currencies, five dates and one status. These are response/field counts, not 14
independent cases.

## Source calculations

The following arithmetic uses the rendered current terms and only POSTED target
order/line movements through 12:00 UTC. Negative movements reopen demand. Prices
are cents after one final half-up rounding step.

| Family and case suffix | Text-based balance or state | Net unit price calculation |
| --- | --- | --- |
| Scoped revisions, `9ab6f7175ba05de15c1e` | Revision 4 replaces cartons with 11. `11*24+4-(72+40-1)=157`. Its date is 2026-11-14. Revision 3 has a later timestamp but less authority. | `66168*0.75/24=2067.75`, rounds to 2068. |
| Same SKU on another order, `fb69f8c289f4dceec765` | Target remains six cartons and one loose unit. `6*12+1-(15+11-6)=53`. The other order's revision 18 cannot amend it. | `28105*0.95/12=2224.979...`, rounds to 2225. |
| Conditional release, `b9e4230983309a1a8ff6` | D05 releases D04. `13*8+5-(23+12-6)=80`. The released date is 2026-11-21. | Code C12 is 12.5%: `18990*0.875/8=2077.03125`, rounds to 2077. |
| Signed shipments, `93950ba5f4c2563b5763` | `9*24+4-(39+48-1-3)=137`. MEMO, another line/order, and the 12:15 posting are excluded. | Code A0 is zero rebate: `30388/24=1266.166...`, rounds to 1266. |
| Cancelled, `8890f011be88eaa74141` | Approved D04 cancels the line. The apparent reinstatement is only a draft; all four commercial fields are null. | Null under the cancellation rule. |
| Pack discount, `b7d7085df04f1abf4289` | `7*8+3-(7+8-1)=45`. Current date remains 2026-11-08. | D04 replaces carton price with 16403 and code B5: `16403*0.95/8=1947.85625`, rounds to 1948. |
| Equal-revision conflict, `0b16a070c8d1db1f8628` | D04 and D05 both have revision 5 but give 11 versus 14 cartons. Only quantity is unresolved; status is ambiguous. Currency CAD and date 2026-11-10 remain known. | Unchanged price: `41839/24=1743.291...`, rounds to 1743. |
| Compound reconciliation, `e9e299162f8aa9d7358e` | D09 releases D08. `14*12+4-(30+8-3-2)=139`. Its date is 2026-11-14. No applicable equal-revision conflict exists. | D07's list price survives; D08 replaces its rebate: `8732*0.875/12=636.708...`, rounds to 637. |

## Nulls and observed error boundaries

Luna sample 0 returns all four commercial fields as null while reporting active
status on the signed-shipment and pack-discount cases. Neither source has an
approved cancellation, withdrawn date or applicable conflict. Both contain known
currency, date, quantity inputs and price inputs. The nulls are incorrect values,
not justified abstentions or a checker type problem. Null is schema-valid for
those fields but must still match the source.

Both Luna answers on the equal-revision case correctly mark quantity null and
status ambiguous, then incorrectly clear price, currency and date too. The
instructions limit a conflict to its affected output; no source changes the
other three values. Luna sample 0 also marks the compound case ambiguous, although
its approved revisions and release decision resolve each field. That rejection
is supported by the source.

Two responses provide useful possible error explanations without proving the
model's internal process. Scoped-revision sample 0 returns 119, exactly 157 minus
the excluded other-order 19, other-line 11 and MEMO 8 movements. Pack-discount
sample 1 returns 1941 cents, the rounded result using the obsolete 16345-cent
carton price with the new rebate, rather than the current 16403-cent price. These
numerical matches are consistent with scope contamination and incomplete partial
revision handling. The raw answers do not show intermediate arithmetic, so those
causes should remain interpretations.

Some wrong-value answers also omit required evidence: a released conditional
field needs its gate, a unit price needs its carton definition, and a quantity
needs the current loose-unit source. No observed rejection rests only on those
citation requirements. Relevant extra target-line context is accepted by design,
and no analogue of the v1 harmless-context false rejection was found.

The pilot has only one source pack per family and two draws per model. It tests
the interface and exposes real mistakes on these eight packs; it cannot estimate
general production accuracy or demonstrate model learning. Its caches and results
must remain separate from the main run, including if later reporting changes.
