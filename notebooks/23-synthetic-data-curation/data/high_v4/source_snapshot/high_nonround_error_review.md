# Non-round quantity errors in the original collection

This post-hoc review isolates the seven frozen collection responses whose quantity delta is outside the repeated −100/−200-unit offsets. Delta means observed quantity minus the answer independently derived from the literal packet. I reparsed each exact saved document with the independent Fraction reader, checked it against the pre-audited source record, and recomputed open balance from current ordered demand minus the net allocated dispatch ledger.

These are counterfactual arithmetic checks only. An exact numerical match shows that a hypothetical omitted, duplicated or wrongly revised event could produce the same delta. It does not show that the model made that mistake. The report does not describe any counterfactual as the model’s reasoning.

| Case | Family | Expected open units | Model output | Delta |
|---|---|---:|---:|---:|
| `account-56fd10ed56500a83af17` | compound | 91,504 | 91,432 | -72 |
| `account-6096dbb0d4b1dff23766` | effective_authority | 88,232 | 88,160 | -72 |
| `account-81ae28dafc747351824c` | tier_sequential_pricing | 87,801 | 87,729 | -72 |
| `account-9c3fa4f97055b7fb2cb5` | split_allocations | 90,380 | 90,480 | +100 |
| `account-fec037740b6811d6ce5e` | tier_sequential_pricing | 88,026 | 87,482 | -544 |
| `account-ff063de4c5006a400e7d` | shipment_revisions | 88,043 | 87,971 | -72 |
| `account-f3fc844a1c0b64528f2d` | shipment_revisions | 87,400 | 87,256 | -144 |

## What the visible ledger permits us to say

### `account-56fd10ed56500a83af17`: -72 units

The text-derived answer is 91,504 open units: 95,791 ordered minus 4,287 net allocated dispatched. The packet has 86 selected logical events and its accepted returns total -334 net units.
A return counterfactual matches the delta exactly: omit the return `RT-02` (4 units × 24 units per CASE × 3/4 target-line share = -72 net units; references `SH-01`). The factor and allocation come from the selected original shipment and its occurrence date. This is a numerical match, not a claim about the model’s process.
A single-event arithmetic match also exists for SH-04 (72 units). Counting such a valid shipment twice would produce the negative delta; omitting it would produce the positive delta. The cache alone cannot tell whether either happened.


### `account-6096dbb0d4b1dff23766`: -72 units

The text-derived answer is 88,232 open units: 95,845 ordered minus 7,613 net allocated dispatched. The packet has 86 selected logical events and its accepted returns total -520 net units.
A return counterfactual matches the delta exactly: omit the return `RT-01` (4 units × 24 units per CASE × 3/4 target-line share = -72 net units; references `SH-04`), omit the return `RT-02` (4 units × 24 units per CASE × 3/4 target-line share = -72 net units; references `SH-01`), omit the return `RT-03` (4 units × 24 units per CASE × 3/4 target-line share = -72 net units; references `SH-10`). The factor and allocation come from the selected original shipment and its occurrence date. This is a numerical match, not a claim about the model’s process.


### `account-81ae28dafc747351824c`: -72 units

The text-derived answer is 87,801 open units: 95,144 ordered minus 7,343 net allocated dispatched. The packet has 86 selected logical events and its accepted returns total -520 net units.
A return counterfactual matches the delta exactly: omit the return `RT-01` (4 units × 24 units per CASE × 3/4 target-line share = -72 net units; references `SH-04`), omit the return `RT-02` (4 units × 24 units per CASE × 3/4 target-line share = -72 net units; references `SH-01`), omit the return `RT-03` (4 units × 24 units per CASE × 3/4 target-line share = -72 net units; references `SH-10`). The factor and allocation come from the selected original shipment and its occurrence date. This is a numerical match, not a claim about the model’s process.


### `account-9c3fa4f97055b7fb2cb5`: +100 units

The text-derived answer is 90,380 open units: 94,846 ordered minus 4,466 net allocated dispatched. The packet has 86 selected logical events and its accepted returns total -372 net units.
No single accepted return, counted shipment, active-reversed shipment or earlier shipment revision tested here matches +100 units. Ignoring every accepted return would shift this answer by -372 units, which does not by itself reproduce the observed output. I leave the remaining discrepancy unexplained.


### `account-fec037740b6811d6ce5e`: -544 units

The text-derived answer is 88,026 open units: 94,670 ordered minus 6,644 net allocated dispatched. The packet has 86 selected logical events and its accepted returns total -444 net units.
No single accepted return, counted shipment, active-reversed shipment or earlier shipment revision tested here matches -544 units. Ignoring every accepted return would shift this answer by -444 units, which does not by itself reproduce the observed output. I leave the remaining discrepancy unexplained.


### `account-ff063de4c5006a400e7d`: -72 units

The text-derived answer is 88,043 open units: 95,328 ordered minus 7,285 net allocated dispatched. The packet has 86 selected logical events and its accepted returns total -444 net units.
A return counterfactual matches the delta exactly: omit the return `RT-01` (4 units × 24 units per CASE × 3/4 target-line share = -72 net units; references `SH-04`), omit the return `RT-02` (4 units × 24 units per CASE × 3/4 target-line share = -72 net units; references `SH-01`), omit the return `RT-03` (4 units × 24 units per CASE × 3/4 target-line share = -72 net units; references `SH-10`). The factor and allocation come from the selected original shipment and its occurrence date. This is a numerical match, not a claim about the model’s process.
A second exact counterfactual is to count `SH-03` despite its active reversal `RV-01`. The visible row is 12 BOX at allocation `AL-1`; 12 × 12 units per BOX × 1/2 target-line share = 72 units, exactly the magnitude of the error. The packet’s POSTED reversal means the row contributes zero under the stated rule.
A single-event arithmetic match also exists for SH-21 (72 units), SH-24 (72 units), SH-27 (72 units), SH-36 (72 units), SH-51 (72 units), SH-60 (72 units). Counting such a valid shipment twice would produce the negative delta; omitting it would produce the positive delta. The cache alone cannot tell whether either happened.


### `account-f3fc844a1c0b64528f2d`: -144 units

The text-derived answer is 87,400 open units: 94,591 ordered minus 7,191 net allocated dispatched. The packet has 86 selected logical events and its accepted returns total -444 net units.
A second exact counterfactual is to count `SH-13` despite its active reversal `RX-13`. The visible row is 8 CASE at allocation `AL-2`; 8 × 24 units per CASE × 3/4 target-line share = 144 units, exactly the magnitude of the error. The packet’s POSTED reversal means the row contributes zero under the stated rule.
A single-event arithmetic match also exists for SH-27 (144 units), SH-31 (144 units), SH-36 (144 units), SH-60 (144 units). Counting such a valid shipment twice would produce the negative delta; omitting it would produce the positive delta. The cache alone cannot tell whether either happened.


## Reading these examples

Four of the seven deltas are −72 units, one is −144, one is +100, and one is −544. The source audit confirms all seven packets are internally solvable and their stored answers and evidence requirements match the rendered text. The −72 examples have exact single-return omission arithmetic; one also has an exact active-reversal inclusion alternative. The −144 example has a matching active-reversed shipment and valid-shipment amount. These alternatives overlap, so they do not identify which operation, if any, occurred. The +100 and −544 examples have no tested single-event match; for the −544 case, ignoring all returns gives −444, leaving a further −100-unit gap.

The repeated −100 and −200 errors are more common in the full collection, but this small set shows that other ledger-scale discrepancies occur. It does not establish a shared cause. The complete arithmetic trace, response values, row IDs, document hashes, and counterfactual candidate lists are in [high_nonround_error_review.json](high_nonround_error_review.json).
