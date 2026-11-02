# V4 pipeline review

Read-only review by the fixture agent, 2026-10-26. This report is the only review file owned here. No pipeline, fixture, cache or prior-round file was edited during this review. No model calls were made.

## Fixture readiness

The final fixture module passes 17 substantive tests across all levels, including complete rendered-text reconstruction, independent Decimal/Fraction agreement, hand equations, price-unit instruction agreement, reference bounds and schema/value/evidence separation. Parent reports a third independent text/SQL/Decimal audit of all 32 official pilot fixtures, using seeds 244101, 244202, 244303 and 244404 with eight cases at each respective level. Separate reader review found the current instructions and source units coherent. Sources remain frozen.

Readiness SHA256:

| File | SHA256 |
| --- | --- |
| high_fixtures.py | FF9479D80C93327D3CF0F4F854B1DA89E5BD8D8B0DB48707509F9CFE77E15547 |
| test_high_fixtures.py | A56A449CD785AD4C29FE06611318EE034472CE2C9C324FF8E1B3BFB51D8909F2 |
| high_fixture_contract.md | E538D1EA429665CE815A72209B7493A50509653890A8F095CAB63925D5715B08 |

## Transport review

The current high_transport.py constructs exactly one case per request. The allowed model is gpt-6.1-sol. Both hashed request metadata and actual CLI options explicitly set reasoning effort high. high_call_model rejects a changed effort, CLI profile, maximum-case count or timeout inconsistent with the hashed request.

The actual subprocess runs codex exec in a temporary empty directory, with user config/rules ignored, ephemeral state and tools/plugins/apps disabled. It removes nesting environment identifiers. The source request accepts only case_id, task_instructions and documents. The complete model-visible prompt, effort, CLI profile, model, stage and limits enter the cache identity.

Repair feedback is restricted to original_output and validator_feedback. The latter accepts only wrong_fields, schema_failed and evidence_failed_fields, with distinct names from the seven answer fields and a Boolean schema flag. Expected values, explanations, traces and arbitrary feedback keys are rejected. The pipeline still needs to be checked for correct construction of original_output and selection of those field names.

A fresh attempt is persisted as pending before execution and atomically replaced with the terminal attempt. Replay checks request/key integrity, rejects incomplete pending records, and reuses recorded failures without silently retrying. Offline cache misses raise. There is one orchestration subprocess per request. Internal CLI network reconnects cannot be independently prohibited, and the module says so; observed reconnect/error events are retained. Terminal turn.failed, nonzero exit, timeout, unexpected tools and missing final answer remain transport errors, even if some text parses. Parse and case-ID diagnostics remain separate from successful transport.

Usage is taken once from the completed turn and attached to the request record. Aggregate usage deduplication, failed-output treatment and request-budget accounting must be checked in the experiment runner. No transport blocker was identified in this source review.

A mock-only probe confirmed successful cache replay invokes the supplied runner once, a pending cache raises even with live=True, request metadata and CLI options both specify high, maximum cases is one, and terminal turn.failed remains an error despite a parseable answer. The probe used a temporary cache and no live model calls.

One defense-in-depth issue was sent to the owner and fixed before collection: the repair feedback mapping now requires exactly the expected case IDs. Unexpected entries cannot bypass per-case feedback validation or enter the prompt. A mock-only boundary probe confirmed rejection. No actual leakage was observed.

## Pilot verdict: clear before collection

The completed high_experiment.py has no identified pilot blocker. high_prepare_pilot generates all 32 potential packets and passes them through both full fixture checks and the independent visible-text/SQL/Decimal material audit before any request. It freezes potential sources, instructions, profile, protocol and material-audit hash. high_model_input permits only case_id, instructions and the rendered document.

The pilot makes one high-effort Sol request per source. It stops at the first level with at least three successful usable replies having valid schema and a wrong typed field value. Citation-only, schema, parse, missing-output and transport failures cannot satisfy that threshold. If none qualifies, the declared maximum-level fallback records threshold_met=false. All eight cases in a visited level finish before threshold evaluation.

Owner reports five transport tests and the mocked pilot preflight/threshold/replay test passed before the core freeze. Fixture-agent mock probes independently confirmed the explicit high CLI profile, exact one-case bound, eligible-versus-ineligible boundary, generic flags, exact original-output feedback reference and shared model inputs. No model calls were made by this reviewer. The pilot gate is clear.

Reviewed core SHA256, after the exact-feedback-ID fix:

| File | SHA256 |
| --- | --- |
| high_transport.py | 71744C52BEB56A2123BE3E09F398A0863A5DA900B9F439161FC82A0FE22C4007 |
| high_experiment.py | 7877B64EF6ADD946CBFB67C75D4C9AA9731CEEF73075DEC6311408D1B065FF63 |

## Main runner review

The runner prepares all 160 initial sources, the fixed potential 80-source expansion and 24 audit sources before original calls. Both audits cover every potential source. IDs and semantic records must be unique, and main/pilot semantic overlap is rejected. A seeded random ranking of all potential collection IDs is frozen before outcomes. Its first at most 80 eligible original failures are selected, giving a random cap independent of intervention outcomes.

The expansion uses only initial-cohort valid-schema wrong-value cases: collect the fixed extra 80 exactly when that initial count is below 40. Expansion completes before selection or interventions. Selection is frozen before audit model calls; audit outputs never enter expansion or selection. The audit retains the declared same-semantic/different-heading limitation.

Fresh retry and feedback repair use the identical case object, instructions, rendered document, model, high effort, timeout and one-case transport profile. A mock probe confirmed all three stages have equal case_inputs but distinct full request hashes. Fresh retry receives no old answer or feedback. Repair receives the exact saved original response plus field-name flags, with no expected values or traces. The contrast is therefore the repair package (old output plus generic flags) versus another fresh attempt; it cannot isolate feedback from prior-answer exposure. Intervention jobs are shuffled with a fixed dispatch seed.

The source/answer reviewer can stop between the explicitly separate original and intervention phases. The intervention loader rechecks that selected rows are genuine collection value failures. Coverage must include both arms for every selected source. The final ledger rejects duplicate physical request hashes; the usage summary counts each ledger entry once and preserves token components separately. The prepare-main upper-bound calculation includes the actual pilot requests, initial/expansion/audit requests and two interventions per capped selected source, and refuses a total above the declared cap. Default maximum is 32 + 240 + 24 + 160 = 456 subprocesses.

Primary recovery requires a usable successful reply, valid schema and all seven values correct. Strict evidence acceptance is a separate secondary result. Numeric-error severity and newly wrong fields are recorded separately, avoiding the earlier mistake of calling a numerically worse existing error harmless. Paired statistics include all selected sources, with a predeclared sensitivity excluding observed reconnect pairs. The exact conditional McNemar calculation and paired bootstrap are explicitly descriptive after pilot/failure selection; shared templates and degenerate intervals limit inference.

Replay reconstructs requests from frozen inputs and reuses immutable request caches. Result files are guarded against unequal rewrites; elapsed/cache-replay diagnostics are written separately from frozen scientific results. No live runner behavior or actual sampled outputs have yet been assessed in this pre-collection source review. No critical main-runner blocker was identified; saved-artifact/source checks should continue after collection.
