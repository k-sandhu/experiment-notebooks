# Procurement reconciliation fixture contract

Version `23-procurement-v3`, created 2026-10-24. This module is independent of
frozen v1/v2 modules and uses only the Python standard library. It makes no model
calls. Its generated records and document prose come from seeded program logic,
not sampled model answers or copied customer records.

## Interface

`SOL_TASK_INSTRUCTIONS`, `SOL_FIELDS` and `SOL_FAMILIES` are the public constants.
There is deliberately no unprefixed `FAMILIES` alias because the notebook's v1
functions use that global name. Public functions are:

- `sol_make_cases(n, seed, level=1, split='pilot', start_index=0)`.
- `sol_validate_answer(case, response)`.
- `sol_audit_fixtures(cases)`.
- `sol_correct_response(case)`.
- `sol_independent_reference(case)`.
- `sol_make_verifier_controls(cases)`.

Levels are 1, 2 or 3; splits are `pilot`, `collection` or `audit`. Zero cases are
supported. Cases have the existing metadata names, plus `level`: `case_id`,
`family`, `round`, `arm`, `split`, `created_at`, `document`, `gold`,
`evidence_gold`, `source_record`, `template_group`, `content_hash`, `semantic_hash`.
Case IDs are opaque hashes including seed, source facts and collection identity.
Neither level nor family is printed in the model's document. The model receives
only shared instructions, case identity and rendered sources. Source records,
gold, family, level and provenance metadata remain evaluator-only.

The seven answer fields and parsed response shape match the prior rounds.
`evidence_gold` maps each field to a list of required document IDs. The validator
returns `valid_schema`, seven-field `field_correct` and `evidence_correct`
mappings, `exact_fields`, `accepted`, `reasons`, `reason_categories`,
`has_value_error`, and `evidence_only_failure`. Wrong integer values and missing
citations remain separate categories; Boolean and float values cannot pass an
integer field. Additional object keys are rejected.

## Business semantics

Seven document groups form one procurement handoff packet. P01 is a signed order
with eight lines, including two lines ordering the same SKU. P02 is an approval
register. P03 is an effective-dated UOM master. P04 allocates physical movements
between lines. P05 contains tiered price plans. P06 is a physical movement
revision export. P07 is a separate purchase account that shares a SKU but cannot
supply the target order's commercial state.

Commercial fields resolve separately. Eligibility requires both recorded and
effective timestamps at or before the cutoff, 2026-10-24T12:00:00Z, with approval
present. A line value overrides an order default. Within the same scope, higher
approval authority wins, then later effective timestamp, then higher revision.
Recorded timestamp only controls availability. Blank or omitted fields leave
older terms intact. There are no conflicting equal-priority approvals.

Physical movements first resolve logical event identity and row revision.
Identical overlapping copies count once. A corrected row replaces its older
revision. A selected VOID row contributes nothing. A current posted reversal
removes the referenced shipment once, including its selected correction. A
voided reversal has no effect. Movements occurring after cutoff, or recorded
after cutoff, cannot affect this extract. Other purchase accounts are excluded.

Each remaining shipment converts its UOM using the master effective on its
occurred date, then applies its allocation key's share for the target line.
Accepted returns inherit their original shipment's UOM, occurred date, SKU and
allocation key. A return date cannot select a newer carton factor. Returns
against removed shipments contribute nothing. Every generated fractional share
produces an exact integer number of individual units. Open units are current
ordered units minus net allocated dispatch after returns.

Price tiers use current approved ordered units before shipments, not the open
balance. The chosen plan's gross individual-unit price receives rebate A, then
rebate B on the remainder, then its per-unit fee minus its per-unit credit.
Only the final cent result is rounded, nearest with exact half-cents up. Source
amounts are currency units per individual unit, with fractional-cent fee/credit
values explicitly represented. No freight/tax invoice total is inferred.

Purchase-order status is active in this fixture set. Shipment void/reversal is
not purchase-order cancellation. This round tests accounting reconciliation and
scoped terms, not unresolved commercial ambiguity or order cancellation.

## Scenario labels and difficulty

The six labels are `shipment_revisions`, `dated_uom_returns`, `split_allocations`,
`tier_sequential_pricing`, `effective_authority`, and `compound`. All cases share
the core reconciliation workflow. Some variants add a third shipment correction,
a voided reversal, alternative allocations, or additional commercial precedence
dependencies. The labels describe scenario variants, not isolated causal
ablations of six independent mechanisms. A per-family result cannot establish
which individual mechanism caused an error.

Level 1 has 12 base shipment identities, level 2 has 20, and level 3 has 32,
before corrections, returns, reversals and distractor rows. Higher levels also
include additional approval/return dependencies. The initial six-case prototype
measures 2,144–2,281 whitespace-delimited words at level 1 and 2,749–2,810 at level
3. Records are ordinary tables plus policy/approval notes; no source document
contains the precomputed open balance or net unit price. Audit uses archive
headers on the same semantic task families. It is a rendering holdout, not
unseen-business-rule validation.

## Verification and reproducibility

The constructor's gold implementation uses procedural term updates and a latest-
row map, with Decimal price arithmetic. The independent reference groups event
revisions, resolves fields separately and uses Fraction arithmetic. It does not
read stored gold. Audit compares both implementations and checks rendered source
reconstruction, content/semantic hashes, LF line endings, nonnegative balances,
allocation totals, and acceptance of gold responses. This does not replace
manual inspection of whether the rendered text expresses the intended rules.

Semantic hashes normalize table/event order and identical overlapping rows but
retain actual source facts, logical event identities, timestamps and commercial
values. The exact document has a separate content hash. Sorted-key JSON
serialization preserves the reconstructed document, truth and hashes.

The evidence policy accepts any additional relevant P01–P06 context once the
necessary current sources are present. It does not demand one exact citation
order and rejects P07 as target support. Context alone does not establish a
value. Order ID has several sufficient literal approved sources. All accepted
examples require correct values as well as adequate source coverage.

Run `python -m unittest test_sol_fixtures -v`. Sixteen tests pass. They include a
hand-calculated 60-open-unit, 140-cent example; corrected and overlapping rows;
reversal and voided-reversal behavior; historical UOM returns; scope, authority,
effective and revision precedence; inclusive cutoff; tier boundaries; sequential
discounts and half-cent rounding; all-level sorted-JSON round trips; schema and
evidence boundaries; and corrupted-gold detection. Verifier controls are
explicitly labelled `is_model_result=False` and must never be counted as model
failures.

### Citation policy question recorded before inspecting pilot responses

The frozen quantity support set always includes P01 for purchase-line/SKU
identification. An alternative sufficient derivation may use P02's current
ordered quantity, P04's target-line allocation, P06's explicit shipment SKU and
P03's conversion master, without P01. That alternative appears defensible because
each physical movement carries its own SKU and the query already identifies the
line. The concern was reported after live pilot launch, so the frozen helper and
raw scoring policy are unchanged. It does not affect any reference value or the
primary field-value outcome. If such a citation-only rejection is observed, it
should be disclosed and assessed in a separately labelled reviewed policy view,
without rewriting raw scores, source packs or pilot selection history. No pilot
responses were inspected when this question was recorded.

The prototype still uses authored accounting rules, exact references and clean
table exports. It is more involved than the earlier packs but does not establish
production reliability, naturalness of real correspondence or downstream
training value. Larger context, batching and model effort must be measured by
separate comparisons rather than inferred from one error rate.
