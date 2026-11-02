# Source rules and study design

### Source rules and material checks

P01 is the signed order; P02 is partial approvals; P03/P04 are dated handling factors and line allocations; P05 is pricing; P06 is the revision register. Line scope outranks order defaults, then authority, effective timestamp and revision resolve each commercial field independently. Both recorded and effective timestamps must be available by the inclusive October 26 noon cutoff. Movement identity is logical Event ID: choose the highest recorded-by-cutoff revision before applying occurrence/state tests. A selected VOID does not restore the older row. Timely active reversals remove their referenced selected shipment once. Returns use the selected original shipment's date, SKU, handling unit and allocation version. Open quantity is approved demand minus allocated shipments plus accepted returns.

Price tiers use approved demand before movements. Divide gross pack cents by pricing pack units, apply two rebates sequentially, add unit fee and converted pack fee, subtract unit credit, then round once half-up to integer cents. All answer-relevant facts and joins are visible. All 32 potential pilot sources and every 2,144 potential selected-tier main source were checked before their corresponding calls using full text reconstruction, constructor Decimal, independent Fraction, separately parsed text/SQL/Decimal and separate text/Fraction checks. Full traces record chosen revisions, exclusions, historical rates/shares and exact price arithmetic. Source IDs and normalized-fact hashes were checked against prior corpora/pilots. This prevents exact recorded overlap, not broad task-program novelty.

The scope remains clean, active-only high-volume procurement: roughly 110,000–128,000 ordered units and 128/192 logical shipments concentrated on October 18/22/23, with return/correction controls through October 26. Tools are disabled by the CLI profile. It tests text-only reconciliation rather than an accountant using a calculator/database. Regular control patterns and complete rules are deliberate; OCR, missing contracts, hidden policy, tax, currency conversion and unresolved approval conflicts are outside scope. Longer histories do not guarantee failures. [EvoEnv](https://arxiv.org/abs/2605.14392) (Shi et al., 2026) motivates executable generators, staged semantic validation and solver-relative calibration; this illustrates data-workflow steps without reproducing its reinforcement-learning training or downstream evaluation.



### Difficulty calibration

A genuine pilot failure requires a usable, schema-valid answer with at least one wrong typed value. Service, schema and citation-only failures do not qualify.

| Base shipments | Called | Seven values right | Genuine value failures | Fully accepted | At least six failures |
| --- | --- | --- | --- | --- | --- |
| 128 | 16 | 13 | 3 | 13 | False |
| 192 | 16 | 5 | 11 | 5 | True |

The completed pilot made 32 CLI requests and selected 192 shipments per packet: First predeclared threshold crossing. The threshold was met. Uncalled tiers: []. This is solver-relative calibration on fresh seeds, not a causal comparison of length. The pilot answers do not enter the paired main inference.



### Planned precision and the five-point limit

Power is the chance that the predeclared test detects a repair-favoring difference when a specified true difference exists. A five-percentage-point effect means five extra corrected orders per 100 original failures. Discordance is the fraction of cases where exactly one arm succeeds; those cases drive the paired test. The saved exact-enumeration plan uses a positive recovery difference and a two-sided exact McNemar p-value below 0.05. These are planning scenarios, not observed effects.

| Assumed true gain | Assumed discordance | Power at 200 pairs | At 400 | At 600 |
| --- | --- | --- | --- | --- |
| 5 pp | 25% | 24.95% | 47.89% | 66.27% |
| 5 pp | 35% | 18.91% | 36.34% | 51.78% |
| 5 pp | 50% | 14.45% | 26.91% | 38.84% |
| 10 pp | 25% | 78.68% | 97.91% | 99.86% |
| 10 pp | 35% | 63.20% | 91.59% | 98.47% |
| 10 pp | 50% | 47.93% | 79.22% | 92.90% |

At 600 pairs, nominal power for a true five-point gain is only 38.84–66.27%, compared with 92.90–99.86% for ten points. Thus 600 pairs do not guarantee a decisive answer about a small gain; a shortfall weakens the original plan further. The calculation assumes independent case pairs conditional on one fixed generator. Shared source programs/templates can violate that assumption. The actual comparison has 595 complete pairs and checks all 512 possible completions of its unknown outcomes. The table describes the original fully observed design, not the power of that amended decision rule. Earlier v4 outcomes informed planning only and are not pooled into the new estimate. The full frozen grid is in [the saved power plan](../source_snapshot/scale_power_plan.json).



### How original failures were accrued

The frozen plan began with 512 originals and added fixed 256-source tranches only while eligible original failures remained below 600, capped at 2048. Actual called count was 1024; eligible failures 732; selected pairs 600; observed complete pairs 595. There are 1024 uncalled potential collection sources. They are absent from response denominators. No repair outcome affected continuation, stopping or ranking. Audit calls started after selection froze; intervention calls waited for all originals/audit and source review. Each four-request wave contains both arms for two sources with randomized within-wave order and no result sharing.


