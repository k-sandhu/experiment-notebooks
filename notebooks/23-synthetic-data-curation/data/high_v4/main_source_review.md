# V4 selected main-cohort source gate

Reviewed 2026-10-26 before main model calls. The prepared level-2 cohort contains 264 unique cases. I compared each case against the independently text-audited level-2 manifest, checking exact case IDs, SHA-256 of the rendered document, content and semantic hashes, stored seven-field answer, and required-evidence IDs. All 264 matched the pre-audited records exactly. The instruction text hash is `0d74782473e7b1b8079f76f004aa87d0d2341bb8c37e4210b5b85acf3d7567b8`, the same frozen protocol reviewed previously.

I also reran the independent rendered-text Fraction audit against the exact saved 264 documents. It found zero answer-key or evidence-key disagreements. Counts match the plan: 160 initial collection cases, 80 extension collection cases, and 24 audit cases. The scored split is 240 collection and 24 audit. The extension is part of the collection set, not an additional audit set.

The main cohort has zero case-ID overlap and zero semantic-hash overlap with the 32 pilot packets across all four levels. All cases are level 2. No regeneration, rescoring, or model call was needed for this gate.

## Source-trace spot check

Case `account-601c5eb617997b88b3cb` remained byte-for-byte identical to its pre-audited packet. Its visible approval rows resolve the target-line ordered balance to 94,882 units and PLAN-C. The independently parsed P06 ledger resolves to 86 selected logical events and 7,037 net target dispatch units, leaving 87,845 units open. The visible PLAN-C row and its 94,000-unit tier yield 275 cents per unit after the two sequential rebates, fees, credit, and final half-up rounding. The expected answer in the saved cohort matches this trace, and the evidence requirements match the rendered-source audit.

Machine-readable per-case hashes and independent derivations are in [high_main_source_review.json](high_main_source_review.json). It records all 264 cases, not just the spot check.

## Gate result

**Source gate clear for main calls.** This clears only the packet identity, rendered-text solvability, gold/evidence consistency, split, and pilot-disjointness checks. It does not certify model outputs or establish generalization beyond these synthetic records.
