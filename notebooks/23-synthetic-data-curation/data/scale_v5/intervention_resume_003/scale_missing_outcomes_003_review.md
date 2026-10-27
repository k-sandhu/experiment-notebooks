# Missing-outcome analysis 003 review

## Result

**Passed.** I reviewed the pure analysis helper, its mock-only tests, and the supplied unit-test log. I did not read intervention responses, arm caches, result tables, or efficacy summaries, and made no model calls. I did not rerun tests; the supplied log records eight passing tests.

The analysis gate checks `interventions_complete` before iterating selection, intervention, or unavailable inputs. It verifies every scheduled arm row and binds each unavailable cell to its request key, case, and arm. Unavailable rows must have a null response, an explicit marker, and an error/status field; the allowlist must match all marked rows. Duplicate and mismatched identities and imputed responses are rejected.

The helper separates fully observed pairs from incomplete pairs. It calculates the paired analysis on fully observed pairs only. For the scheduled-cohort sensitivity analysis, it preserves the known arm in a partial pair, enumerates every binary assignment for every unknown response cell, and labels those values as hypothetical. The effect bounds correctly add the known cell contributions and allow each unknown fresh cell to contribute from zero to minus one and each unknown repair cell from zero to plus one.

The bootstrap implementation keeps the frozen selected-case order, seed, and draw count. It applies the same sampled pair multiplicities to every completion and shares computed intervals only when the completion's missing-pair delta vector is identical. The tests compare the intervals for every whole-pair and partial-pair completion with the frozen paired-statistics helper, including a reordered sample. The primary decision remains positive repair-minus-fresh difference and exact two-sided McNemar p below 0.05 in every completion.

## Test evidence

The supplied log records eight passing mock tests. Coverage includes the phase gate, deterministic output and no mutation, identity validation, no imputation, partial-pair fixed counterparts and bounds, whole and partial pair bootstrap equivalence, effect-boundary examples, and a 600-pair mock with 596 complete pairs, eight unknown response cells, 256 completions, and 20,000 bootstrap draws at seed 246600.

## Limits

This review covers the generic analysis helper and mocks only. It does not verify amendment 003's actual request identities, its cache inventory, runtime overlay, or the final report wiring. Those require separate metadata-only checks. The all-completions rule is conservative for the declared binary endpoint; complete-pair results remain available-case estimates and may be affected if interruption is related to request order or runtime.
