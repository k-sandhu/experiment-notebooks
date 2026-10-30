The numerical records, fictional organizations, appointment schedules and quote
workbooks were generated for this experiment on 24 October 2026. They are offered
under CC0-1.0. No customer or client records are included.

The final wording of the three initial task templates and the harder planning
template was authored through the Anthropic
Claude CLI, using Claude Opus 5.5, from explicit business rules. That vendor is
different from both tested OpenAI policies. All numerical ground truth comes from
deterministic code. The full authoring request and response are retained in
`authoring/`, with an index identifying the request hash and actual call count.

OpenEnv is used under its BSD-3-Clause licence, at revision
`21fbb0ecb2a3e74110b59cf38a1b195decc75c88` (v0.10.0). The environment code is
installed separately and is not vendored here. The original FinQA benchmark
questions are not used. These files contain newly authored fictional tasks.

Model responses are included as experimental evidence. CLI billing for the two
tested policies is not reported by the interface. Authoring metadata reports a
combined list-rate cost of $0.085094 for two authoring calls; that is not an
attestation of subscription billing.

The frontier_v4 follow-up adds 12 newly generated Calendar fixtures, eight prepared
calibration cases and four fresh comparison cases, under the same CC0-1.0 terms.
Only two of the calibration cases were used for policy rollouts. Its additional
Claude Opus 5.5 wording call reports $0.0201788 at list rates. Across all three
authoring calls the reported list metadata is $0.1052728. Tested-policy billing
and actual subscription billing remain unavailable. The full-request cache and
creation dates for this follow-up are indexed in frontier_v4/provenance.json.

The frontier_v5 follow-up adds the prepared difficulty ladder, broader planning
fixtures and conditional-handoff-cost fixtures under CC0-1.0. Numerical inputs
and certificates are code-generated. One new Claude Opus 5.5 wording call costs $0.0364510 at reported list rates.
The reported list cost across all authoring calls is $0.1417238.
Policy CLI and actual subscription billing remain unavailable. The source index
and task creation dates are in frontier_v5/provenance.json. No weights are updated.

## Token-budget follow-up, 26 October 2026

The two 16-case banks in `frontier_v6/` were generated from new seeded code on 26 October 2026. The initial bank belongs to an interrupted launch; the unchanged replacement bank supplies the token comparison. Fictional calendars, numeric records and authored fixture code use CC0-1.0. The OpenEnv revision and BSD-3-Clause environment licence remain pinned in the data provenance.

No new authoring model call was made. Claude Opus 5.5 wording from `frontier_v5/authoring_fees.json` was reused. All four historical authoring responses together report USD 0.1417238 in list metadata. Tested-policy billing is unavailable. No model weights were loaded locally or updated.

## Capacity recovery, 27 October 2026

The provider reported that the selected Sol model was at capacity after twelve whole arms reached their token cutoffs. The recovery protocol retains those twelve and repeats every incomplete or unstarted arm from a fresh environment, using the same numeric case bank, requested models, medium reasoning and controller. All original partial outcomes, the failed request without usage and availability probes remain archived outside the matched comparison. Selection uses completion status rather than rewards. The procedure was recorded after the outage and frozen before restarted trajectories.

`comparison_complete/` contains unchanged copies of the selected source records from `comparison_final/`, `comparison_capacity/` and `comparison_session/`. Its manifest links every file to its origin and hash. Duplicate copies are counted once for physical invocation totals. Incomplete groups with known success/failure contrast are reported as a post hoc diagnostic, while complete groups of four remain the primary metric. Unknown rewards are never relabeled as failures.

## Local session recovery, 27 October 2026

After a tool-session refresh, the last collector and its child were no longer present. Fifteen entire arms had finished. The one unfinished Sol adaptive arm remains archived with 100 completed requests, 3,576,478 reported tokens, four known failures and one abandoned pending request whose usage and outcome are unknown. The pending raw file is never rewritten or resubmitted. Selection used completion status, not rewards.

A new frozen protocol repeats only that arm from a fresh calendar and the full 6M-token allowance. The same requested model, medium reasoning, cases, tool workflow and controller are retained. No availability probe was added. The composite takes twelve whole arms from the original collection, three from capacity recovery and one from local session recovery. All source bytes are unchanged and included copies are counted once. Both recoveries are additional timing limitations; no model weights were updated.
