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
