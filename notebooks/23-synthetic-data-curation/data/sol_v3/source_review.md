# Sol-targeted main source and intervention review

Read-only review of `data/sol_v3/`. All three original Sol misses are confirmed
field-value errors. No source or reference-label bug was found. No frozen helper,
source, response, cache, score or policy was changed. The reviewer authored the
fixtures; the arithmetic below is a source audit, not independent human
annotation. A second reviewer independently obtained the same five source
balances and prices.

All 60 saved cases pass the complete fixture audit after JSON serialization.
The procedural Decimal gold and separate grouped/Fraction reference agree,
documents reconstruct exactly, and content/semantic hashes match. Sol's original
collection answers are 45/48 exact and accepted; the other three contain three
quantity errors and one price error. Its 12 audit answers are all exact and
accepted. Luna's original collection and audit answers are 0/48 and 0/12 exact.
All 120 original replies and nine interventions have valid schemas; no main
request has a transport or batch-parse failure.

## Paired outcomes on every original Sol miss

Each of the three missed source cases received one fresh Sol retry, one Sol
self-repair and one Luna cross-repair. Self/cross repair received the same
original Sol output and generic failed-field/category flags, without expected
values. Fresh retry received the source task without that output or feedback.

| Case suffix | Gold quantity / price cents | Original Sol | Fresh retry | Self-repair | Cross-repair |
| --- | --- | --- | --- | --- | --- |
| `04f699622fa7f55b9095` | 21,547 / 971 | 21,537 / 971 | 21,547 / 971 | 21,547 / 971 | 21,513 / 971 |
| `80db4a9463ee61051565` | 21,812 / 1296 | 21,752 / 1296 | 21,812 / 1296 | 21,812 / 1296 | 21,716 / 1296 |
| `846f392a960804bf5282` | 21,788 / 909 | 21,778 / 908 | 21,788 / 909 | 21,788 / 909 | 21,465 / 482 |

All six fresh/self answers pass both values and citations. All three cross
answers still fail values. Cross-repair did not simply copy the original wrong
answer: its incorrect quantities change in every case, and its third price
changes from 908 to 482. Absolute quantity errors increase from 10, 60 and 10 to
34, 96 and 323. The third price error increases from one cent to 427 cents.

The recorded `new_wrong_fields` count is zero for cross-repair because none of
the previously correct *fields* became incorrect. That does not mean its numeric
errors stayed unchanged or did no additional harm: the already-wrong fields
became farther from the reference. It corrects zero of the original four wrong
field values. Fresh retry and self-repair each correct all four.

## Shared source rules used in the five worked examples

P01 identifies the target order/line and SKU. P02 AP-09 gives current ordered
units: it is the higher revision among eligible Buyer approvals at the same
effective timestamp. Planner AP-04 has lower authority. Controller AP-05 was
recorded after cutoff; AP-06 is effective after cutoff; AP-08 is unapproved;
AP-07 is another line. Line-specific PLAN-C overrides the order-level PLAN-B
default. AP-10 supplies requested date 2026-11-13. Currency remains P01's default.

P06 is reduced before summation. The latest eligible SH-01 correction replaces
its predecessors, SH-02's overlap copy counts once, RV-01 removes SH-03, the
current SH-06 is VOID, and selected SH-08 occurs after cutoff. SH-07's late-recorded
revision is unavailable. RV-02 is VOID at its selected revision, so SH-05 remains.
Other orders are excluded and AL-4 allocates entirely to L07, not the target.

The CASE shipments in these examples occurred on October 18, giving 24 units per
CASE and a 75% target-line share. EA uses one unit and 50%. BOX uses its current
dated factor and 25%. Each of three four-CASE returns inherits its original
October 18 conversion and reopens `4*24*75%=72` units, for 216 returned units.
Do not use the newer 30-unit CASE factor on the return date.

## Example 1: a ten-unit original miss, both Sol interventions recover

`recon-04f699622fa7f55b9095`, shipment-revision variant, order PO-719901,
SKU CLP-811, currency CAD.

Current ordered units are 24,569. Eligible CASE dispatch totals 2,808; EA totals
70; BOX totals 360. Thus gross dispatch is 3,238 and net dispatch after returns
is `3238-216=3022`. Open quantity is **24,569 - 3,022 = 21,547**.

The selected SH-01 revision 3 contributes `24 CASE*24*75%=432`, rather than
adding its revisions 1 and 2. For example, SH-17 contributes `20 EA*50%=10`.
The original quantity is ten low, but a ten-unit event match does not establish
that the model double-counted that event; the final response exposes no arithmetic.

Current ordered units meet PLAN-C's 24,000-unit tier. P05 gives a gross price of
1074 cents, two 5% rebates, a 3.25-cent fee and a 1.25-cent credit:
`1074*0.95*0.95+3.25-1.25=971.285`, rounded once to **971 cents**. Price and the
other five fields were already correct. Fresh retry and self-repair both return
21,547 with valid evidence. Cross-repair returns 21,513, farther from the source.

## Example 2: a sixty-unit miss remains wrong after cross-repair

`recon-80db4a9463ee61051565`, effective-authority variant, order PO-477983,
SKU CLP-525, currency USD.

P02 gives 25,046 ordered units. CASE contributes 2,952, EA 88 and BOX 410, so
gross dispatch is 3,450. Returns leave 3,234 net dispatched, and
**25,046 - 3,234 = 21,812** open units. A BOX row of 24 units contributes
`24*10*25%=60`; several such rows exist. An extra sixty could arise through an
event-count or arithmetic mistake, but the answer does not identify its cause.

PLAN-C's 24,000 tier gives 1557 gross cents, rebate A 5%, rebate B 12.5%, fee
4.50 cents and credit 2.50 cents:
`1557*0.95*0.875+4.50-2.50=1296.25625`, rounded to **1296 cents**. The original
21,752 quantity is wrong while its price is right. Both Sol interventions return
21,812; Luna cross-repair returns 21,716. All other fields remain correct.

## Example 3: quantity and an exact half-cent price boundary

`recon-846f392a960804bf5282`, dated-UOM-return variant, order PO-298362,
SKU CLP-305, currency CAD.

Current ordered units are 25,050. CASE dispatch totals 3,096, EA 82 and BOX 300.
Gross dispatch is 3,478, net dispatch is `3478-216=3262`, and open quantity is
**25,050 - 3,262 = 21,788**. Sol originally returns 21,778.

P05 PLAN-C at 24,000 units gives 1184 gross cents, two sequential 12.5% rebates,
fee 4.50 cents and credit 2.50 cents:
`1184*0.875*0.875+4.50-2.50=908.5` cents. The declared exact-half-up rule requires
**909 cents**. The original 908 is the result ties-to-even rounding would give,
but the saved final response cannot prove which internal method produced it.
The source and rule nevertheless make 909 unambiguous; this is not a binary
floating-point disagreement.

Fresh retry and self-repair both return 21,788 and 909. Cross-repair returns
21,465 and 482. Its two already-wrong fields become more inaccurate, while its
five originally correct fields stay correct. This is a failed repair, not an
example of a newly wrong previously correct field.

## Example 4: an ordinary original success needs no intervention

`recon-0766b619f8765b016872`, tier/sequential-price variant, order PO-276360,
SKU RIV-404, currency EUR.

P02 gives 25,208 ordered units. CASE 3,600 plus EA 88 plus BOX 464 gives 4,152
gross dispatched. Subtract the 216 returns to get 3,936 net dispatched, then
**25,208 - 3,936 = 21,272** open units. Here BOX uses 16 units per BOX; for example,
`16 BOX*16*25%=64` on SH-09. The factor is SKU/date-specific rather than copied
from one of the failure cases' ten-unit BOX definitions.

PLAN-C's selected gross tier is 684 cents. Its 7.5% then 12.5% rebates and net
1.50-cent fee/credit adjustment give `684*0.925*0.875+2.75-1.25=555.1125`, rounded
to **555 cents**. The original Sol answer matches all seven values and its required
sources. It was correctly excluded from the intervention set. Its absence from
repair/retry is a selection rule, not a missing measurement.

## Example 5: correct historical-UOM reconciliation on the first draw

`recon-08e5076fb7fde1e5ed19`, dated-UOM-return variant, order PO-747377,
SKU VAL-216, currency CAD.

Current demand is 25,170 units. Eligible CASE dispatch is 3,024, EA 68 and BOX
270. Gross is 3,362; net after returns is 3,146; open balance is
**25,170 - 3,146 = 22,024**. The selected SH-01 correction is 32 CASE at the
original factor and allocation: `32*24*75%=576`. RT-02 returns only
`4*24*75%=72`, rather than using the newer CASE size or reversing that whole
shipment. These relationships illustrate why event identity and return UOM both
matter even in a successful answer.

The PLAN-C gross tier is 547 cents, with 12.5% then 2.5% rebates, fee 3.25 cents
and credit 2.50 cents: `547*0.875*0.975+3.25-2.50=467.409375`, rounded to
**467 cents**. Original Sol gets all seven values and citations right. This
ordinary success also receives no intervention.

## Citation-policy question and interpretation

The pre-recorded question about always requiring P01 for quantity has zero
applicable rows in the 120 originals plus nine interventions: no failed quantity
citation set has P02/P03/P04/P06 complete with only P01 absent. It does not alter
any observed acceptance result here. No reviewed-label variant is needed for
these artifacts. In particular, every selected original Sol miss has complete
frozen evidence and fails on its actual numeric value.

There are only three intervention source cases. Fresh retry and self-repair each
recover the same three, so this run shows no added recovery from checker feedback
over another Sol draw. Each arm uses three items and two CLI requests; feedback
arms have longer prompts, so equal requests/items are not equal token budgets.
Cross-repair's zero recoveries are descriptive of these three cases and this
low-effort, batch-of-two protocol, not proof that Luna can never repair Sol.

Each successful Sol arm adds the same three accepted source cases beyond the
45 accepted original source cases. Combining the two arms does not yield six new
distinct cases. The two ordinary successes above must not be described as repaired
or retried. Pilot fallback level selection and the 12-case audit remain separate
from main failure selection. No model weights changed, and no downstream training
benefit is measured.
