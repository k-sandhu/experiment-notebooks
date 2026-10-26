# Sol-targeted pilot source review

Read-only review before the main run. Both reported Sol quantity misses are real
value errors. The saved rendered source packs establish the gold balances below
without an ambiguity or citation-policy change. No frozen helper, source,
response, cache or score was modified. The reviewer authored the fixtures; this
is an explicit source arithmetic check rather than independent human annotation.

## Level 1: 15,780 open units

Case `recon-bb2bfec51726935a1e53`, order PO-219236, line L02, SKU GSK-958.
Sol returned 15,680; the source establishes 15,780.

P02 AP-09 supplies 16,922 current ordered units. AP-09 and AP-03 have the same
Buyer authority and effective timestamp; revision 5 beats revision 4. AP-04's
Planner authority is lower. AP-05 was recorded after cutoff, AP-06 is effective
after cutoff, and AP-07 belongs to L07. None replaces AP-09 for L02.

P03 and P04 give these conversions: CASE movements occurred on October 18, so
use 24 units per CASE and AL-2's 75% L02 share. EA movements use one unit and
AL-3's 50% share. BOX movements occurred on October 23, so use the new 16-unit
factor and AL-1's 25% share.

| Eligible selected event | Quantity and unit calculation | Allocated units |
| --- | --- | ---: |
| SH-01 revision 2 | `16 CASE * 24 * 75%` | 288 |
| SH-02, one copy | `8 EA * 1 * 50%` | 4 |
| SH-04 | `16 CASE * 24 * 75%` | 288 |
| SH-05 | `12 EA * 1 * 50%` | 6 |
| SH-07 revision 1 | `24 CASE * 24 * 75%` | 432 |
| SH-09 | `20 BOX * 16 * 25%` | 80 |
| SH-10 | `8 CASE * 24 * 75%` | 144 |
| SH-11 | `24 EA * 1 * 50%` | 12 |
| SH-12 | `8 BOX * 16 * 25%` | 32 |
| RT-01 against SH-04 | `4 CASE * 24 * 75%`, returned | -72 |
| RT-02 against SH-01 | `4 CASE * 24 * 75%`, returned | -72 |

CASE dispatch is 1,152 units, EA dispatch 22 and BOX dispatch 112. Gross
dispatch is 1,286; accepted returns reopen 144. Net dispatch is therefore 1,142,
and **16,922 - 1,142 = 15,780** open units.

The repeated SH-02 row is one logical event. SH-01 revision 2 replaces revision
1. RV-01 removes SH-03. The selected SH-06 is VOID. SH-08's selected revision 2
occurs after cutoff, so its older revision cannot be restored. SH-07 revision 3
was recorded after cutoff, leaving revision 1 current. Other-order rows are
excluded; target-order OT rows allocate 100% to L07 and contribute zero to L02.

Sol's 15,680 implies net dispatch of 1,242, which is 100 too large. The saved
answer does not expose intermediate arithmetic, so the source cannot identify
one particular internal mistake. The mismatch could be a summation or
reconciliation error; it is not supported by the eligible-event total. All other
answer fields and all frozen evidence checks passed.

## Level 3: 21,402 open units

Case `recon-1be419cf8d966fa3c2e5`, order PO-458839, line L04, SKU VAL-302.
Sol returned 21,392; the source establishes 21,402.

P02 AP-09 supplies 25,176 ordered units by the same explicit scope, authority,
effective-date and revision precedence. CASE factors remain 24 for the original
October 18 movements. BOX shipments use the October 20 factor of 12. Allocation
shares are again 75% for CASE, 50% for EA and 25% for BOX on this target line.

| Movement group | Selected event contributions in individual units | Total |
| --- | --- | ---: |
| CASE dispatch | SH-01=360, SH-04=360, SH-07=432, SH-10=360, SH-13=288, SH-16=288, SH-19=216, SH-22=360, SH-25=432, SH-28=216, SH-31=216 | 3,528 |
| EA dispatch | SH-02=8, SH-05=6, SH-11=12, SH-14=10, SH-17=10, SH-20=12, SH-23=6, SH-26=6, SH-29=4, SH-32=4 | 78 |
| BOX dispatch | SH-09=60, SH-12=48, SH-15=72, SH-18=24, SH-21=60, SH-24=24, SH-27=24, SH-30=72 | 384 |
| Accepted returns | RT-01 against SH-04=-72; RT-02 against SH-01=-72; RT-03 against SH-10=-72 | -216 |

Gross dispatch is 3,990 units. Returns reduce it to 3,774, giving
**25,176 - 3,774 = 21,402** open units. For example, SH-01's selected correction
is `20 CASE * 24 * 75% = 360`, and each four-CASE return is
`4 * 24 * 75% = 72`. The return date does not replace the original shipment's
24-unit CASE factor with the newer 30-unit factor.

The exclusion rules are the same as level 1. Additionally, RV-02's selected
revision 2 is VOID, so SH-05 remains in dispatch. The older posted RV-02 cannot
remove it. Other-order rows and AL-4's L07-only rows contribute zero to L04.

Sol's 21,392 implies net dispatch of 3,784, ten too large. Ten happens to be the
allocated contribution of either SH-14 or SH-17. Double-counting such a row is
one possible explanation, but the final response cannot establish that cause;
an unrelated arithmetic slip could produce the same difference. All other
answer fields and all evidence checks passed.

## Interpretation for level selection

The pilot observed Sol value failures of 1/8, 0/8 and 1/8 at levels 1, 2 and 3.
That is not a monotonic difficulty result, and it does not cross a threshold of
two errors in any level. A level 3 main run is the stated maximum-level fallback,
not evidence that the pilot found or calibrated a failure threshold. These two
misses establish that the source task can produce actual Sol value mistakes.
They do not establish a stable error rate or identify the models' reasoning
process. Pilot caches and results must remain separate from the fresh main run.
