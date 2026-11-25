# Interruption review: scale interventions

## Scope and evidence

This is a read-only methodological review. I read the preregistration, source freeze, intervention start declaration, and amendment 001. I did not inspect model responses or calculate intervention effects. The supplied operational record says the client runner stopped during `clientrefresh`, leaving 116 terminal intervention calls and four pending records (two calls in each arm, spanning two source pairs); the remaining 1,080 calls had not been sent. Each pending record contains only a pending marker, start time, and 900-second timeout. The runner session is gone. The four physical requests therefore have unknown outcomes; the records do not establish whether the CLI or service completed them after the runner stopped.

Review integrity note: a batched read command successfully printed `data/scale_v5/main/infrastructure_stop.json`, which contains original-collection `wave_results`. A later command intended to read the intervention interruption inventory failed because incompatible PowerShell parameters were supplied; the intervention inventory was not read. The displayed records were from the pre-intervention original stage, not intervention responses or scores. I did not inspect or use them for this intervention review, and I notified the coordinating agent immediately. No intervention outcome or efficacy result was disclosed to me, and no efficacy-dependent recommendation was made.

## Recommendation

Before sending any continuation calls, register a timestamped amendment 002 that explicitly closes only the four exact pending request identities as **controller-interrupted; outcome unavailable**. Preserve the four original pending raw-cache byte streams immutably and record their hashes and request identities. Do not invent response bytes, timestamps, elapsed durations, CLI events, return codes, or a provider/model failure. Do not reissue these four requests. Keep the already terminal calls and all frozen source, scoring, selection, allocation, caps, feedback, and old response bytes unchanged. Continue only the 1,080 unsent requests, in the frozen order/waves; any new error stops the run under the existing stop-on-new-infrastructure-failure rule.

Treat the two affected sources as two randomized pairs with both outcomes unavailable. Do not call either missing response wrong, a failed extraction, or a provider failure. Preserve the 600-pair target in the report, with 598 fully observed pairs and two pairs unavailable. Report the preregistered paired analysis on the 598 complete pairs as an available-case estimate, clearly labeled as such. Also run a predeclared all-600-pair sensitivity analysis over all 16 possible assignments of binary recovery outcomes to the four missing arm responses. The original primary claim (positive repair-minus-fresh difference and exact two-sided conditional McNemar p < 0.05) should be considered robust only if it holds under every completion; otherwise report the result as inconclusive for the 600-pair target. Report the full range of effect estimates, p-values, and bootstrap interval endpoints across completions. Do not choose a completion based on which arm it favors.

For the 600-pair recovery-rate difference, let `S` be the sum of repair-minus-fresh differences over the 598 complete pairs. The two unavailable pair differences can each be -1, 0, or +1, so the all-pair mean difference is bounded by `(S - 2)/600` and `(S + 2)/600`. This is a transparent worst-case bound; it does not assume missingness is unrelated to outcomes. Keep failure classification and service reliability separate from recovery correctness: the known client interruption is an execution/observation gap, not evidence that the model returned an incorrect answer or that the provider failed.

## Checks and risks

- The preregistration fixes paired assignment, the 600-source target, the binary all-seven-value recovery endpoint, exact two-sided conditional McNemar test, and 20,000-resample paired bootstrap. It also forbids efficacy-based stopping and orchestration retries.
- The original stop and amendment 001 concern a separate original-collection capacity failure. Amendment 002 should reference, not replace or rewrite, those records.
- The continuation must bypass only the four specifically identified pending rows, while retaining the previously reviewed original capacity-failure handling. Any new error must stop immediately after the current bounded wave drains.
- Two unavailable pairs are few, but interruption at a boundary after runner loss may be related to task runtime or request order. Complete-case analysis alone cannot rule out informative missingness; hence the all-completion sensitivity analysis.
- Four retained raw pending files should remain byte-for-byte unchanged. If the finalizer requires terminal rows, use a separate immutable overlay keyed to those exact request hashes, or retain an archived pending record plus a final-analysis availability table. Do not overwrite raw evidence to make the cache appear terminal.
- Before resume, independently verify exact identity and arm/pair mapping for the four allowed exceptions, all 1,080 unsent keys, and that no existing terminal or pending request can be selected for dispatch.
- No efficacy outputs or partial arm answers were used to formulate this recommendation. A separate reviewer should verify implementation, audit linkage, and output accounting.

## Conclusion

A narrowly scoped, pre-outcome amendment and explicit missing-outcome sensitivity analysis allow the remaining frozen work to proceed without guessing what the four calls returned. The study must distinguish unavailable observations from model errors and must not claim the original 600-pair primary result unless it survives all valid completions.

