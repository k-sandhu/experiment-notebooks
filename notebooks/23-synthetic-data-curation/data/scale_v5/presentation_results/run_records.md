# Detailed collection record

### Infrastructure stop and declared continuation

A [timestamped infrastructure-only amendment](../infrastructure_resume/amendment_001.json) was recorded at 2026-10-27T07:58:56.553988+00:00, before intervention outcomes were available. The run encountered a provider capacity error with no answer. The amendment preserves that terminal failed attempt as a transport failure; it is not resubmitted or relabelled as an extraction error. It remains in attempt and service-failure counts and is ineligible for genuine value-failure accrual or paired selection.

The declared continuation may send only previously unsent originals from the already frozen source/request plan. It does not alter sources, instructions, request identities, the requested model/profile, scoring or selection. The 600-failure target and 2,048-original cap remain unchanged. This is an explicit change to infrastructure handling of the stop, recorded before any intervention comparison. The original execution includes the retained service failure. The [archived continuation companion](../infrastructure_resume/source_snapshot/scale_resume.py) records the implementation separately from the original frozen runtime. This note reports the declared handling policy; it does not inspect partial intervention results or supply missing answers.



### Known follow-up transport stop and unchanged scoring

The [fifth amendment](../intervention_resume_005/amendment_005.json) retains 2 terminal follow-up transport failures without resubmission. The frozen 900-second timeout policy remains in force. The frozen policy scores non-recovery for a timeout even when a raw cache retains a parsed answer, usage or return code zero. The diagnostic label for either terminal service error is Transport failure; not field-scored. Elapsed wall-clock time can include host sleep and is not a measure of active inference compute. The linked amendment preserves the process and sleep evidence.

| Arm | Request key | Terminal error | Timed out | Return code | Elapsed seconds |
| --- | --- | --- | --- | --- | --- |
| feedback_repair | 64a7643d257313d72af7aaf9ce1740f3399778233508012e65524da897385129 | Codex CLI exceeded timeout of 900 seconds | True | 0 | 4534.953589299985 |
| feedback_repair | 689a4570fb27f13b915a1ac531cf677920b9679f8047242027c5fef75156b6a7 | Codex reported turn.failed: {'type': 'turn.failed', 'error': {'message': 'Selected model is at capacity. Please try a different model.'}} | False | 1 | 88.90661780000664 |

Each known failure stays in its observed pair and in operational request and usage totals. Neither a timeout nor a nonzero CLI exit is a measured extraction mistake. No known transport failure adds an unknown outcome: the 8 unavailable outcomes in 4 sources still use the unchanged amendment-003 sensitivity plan. A failure flag from validating no scored answer does not establish that the model returned seven wrong fields. Its retained parsed values are excluded from field-error, newly wrong-field and numeric-regression claims.



### Reviewer identity

The requested authoring reviewer was gpt-6.1-luna; the available reviewer ID was gpt-6-luna at high reasoning effort. Reviewer work is outside measured solver requests and tokens.


### Frozen operational fields and scientific inference

The frozen operational metrics retain every scheduled slot, with unavailable success absent for execution accounting. Their nominal primary_decision field is preserved for replay compatibility. The report uses the separately declared all-completion amended scientific decision, not that nominal field. Per-answer curation retains observed partners of incomplete pairs; only complete-pair inference omits their source. Scoring and parsing are unchanged.


### Calls, tokens and reproducible evidence

| Main request group | Request slots | Input tokens | Output tokens | Median seconds/request | Observed reconnects |
| --- | --- | --- | --- | --- | --- |
| audit | 96 | 6810409 | 640294 | 136.65 | 0 |
| feedback_repair | 600 | 38952474 | 4116351 | 125.37 | 5 |
| fresh_retry | 600 | 39995645 | 3956451 | 118.66 | 4 |
| original | 1024 | 69222792 | 6721158 | 123.64 | 0 |

The complete main has 2320 distinct request slots and 2352 pilot-plus-main scheduled slots. Usage is present for 2309 main requests and missing for 11. Dollar spend is unavailable, not zero. Input/output components are kept separate; cached-input and reasoning components must not be added again to totals that already include them. Equal arm request counts do not imply equal tokens or elapsed compute. These totals cover v5 only, not historical v1–v4. Source gzip files are saved once, while compressed full-request caches retain the observed stdin, replies, timestamps, CLI version/events and usage. Read a gzip JSON cache with gzip.open(path,'rt', encoding='utf-8') and json.load, or download/decompress the linked file. The normal report reads these files and makes no model calls. The frozen [preregistration](../preregistration.json), [source locks](../source_freeze.json) and [completed metrics](../main/metrics.json) link the design to the evidence. Fresh retry reports 39995645 input and 3956451 output tokens across 600 slots; repair reports 38952474 input and 4116351 output tokens across 600 slots. These are reported token components, not a dollar invoice or a guarantee of equal compute.

The 9 interrupted slots were saved as pending before process launch. Their actual launch status is unknown. There are 2343 terminal CLI records including pilot and 9 unavailable attempt slots; actual physical starts are between 2343 and 2352. All scheduled slots count conservatively against the request budget. The frozen fields named physical_cli_requests retain slot counts for replay compatibility; they do not prove that every unavailable slot started. No finish time, return code, elapsed time, usage or CLI events are invented for those slots.
