# Scale-v5 infrastructure-resume review

**Recommendation:** a narrowly scoped continuation is technically defensible after a separate protocol amendment and implementation review. This review does not authorize calls or change the preregistration. I read the preregistration, frozen prepared-main protocol and allocation, the original infrastructure stop record, the one named failed cache entry, and the frozen request plan containing its key. I did not inspect model answer contents or any intervention outputs. No calls were made, and no study/runtime files were changed.

## What stopped

The collection plan has a 512-case first tranche followed by fixed 256-case tranches. The stopped dispatch had submitted 184 requests from its second tranche. Its first 45 four-request waves settled; wave 45 also settled all four jobs, with one terminal capacity error. The stop record reports 72 planned requests in that tranche were never dispatched. The stopped study therefore has 696 terminal original attempts so far, including the failed transport attempt, and no selection, audit phase, or intervention phase has begun.

The failed request belongs to `account-bbbc0014d5d85695cce9`, generation index 692, at zero-based position 180 in the frozen 256-request plan. Its cache has exactly one terminal attempt, exit code 1, a `turn.failed` capacity event, no final assistant response, no parsed answer, no unexpected tool events, and no usage record. The cache key matches the request plan. Its cache SHA256 is `b6fcc0e73ee39665de4da0a6d4f7387744fe62f5a96b0c7675bcbb6d4d0dab64`. It is a terminal infrastructure failure, not an unfinished request or an answer that can be scored.

The frozen v5 rule stops after any infrastructure failure. The preregistration excludes infrastructure errors from eligible value failures and has no prewritten resume clause. So the safe path is a versioned, separately recorded amendment before any additional CLI request. The amendment should reference the exact hashes in [the companion JSON review](scale_infrastructure_resume_review.json), while keeping the preregistration, v5 runtime files, protocol/profile, source cohort and request plan byte-identical.

## Proposed continuation

First reconcile all 184 already-submitted requests in that chunk from their hash-keyed cache entries. Require one terminal entry for every submitted key, exact request/hash matches, and the verified capacity signature for the one known failed key. Reconstruct completed rows from those caches in offline mode. If any submitted entry is missing, pending, changed, or has another unexplained failure, stop for review. Do not resubmit any submitted key.

Then send only frozen plan positions 184–255, the 72 unsent jobs for generation indices 696–767. Keep the request order, model alias, high reasoning effort, instructions, source text, response schema, verifier, timeout, CLI profile and four-worker wave design unchanged. The companion dispatcher may treat the single named capacity cache as a settled transport outcome during reconciliation; it must not generalize that exception to another request key. If a new infrastructure failure occurs, let the current four-request wave settle, preserve its caches, and stop before dispatching another wave.

Count the capacity failure as one attempted source slot and one infrastructure failure, but never as a successful response or eligible value failure. Do not replace its source or issue its request again. Continue only at the already declared complete 256-case tranche boundaries until 600 usable, schema-valid value failures accrue or the 2,048 source-slot cap is reached. The existing 3,376 physical-call ceiling still holds if the failed request is never repeated: its attempt already counts toward the planned original-call budget.

After collection accrual ends, run the frozen 96-case baseline audit. Only then rebuild original outputs, rank all eligible value failures using the frozen seeded order, and perform the source/failure/feedback lineage review before the separate intervention command. Report transport failures and usable model responses separately. The failure remains outside the eligible pool under the original definition, so stopping or extending does not depend on repair outcomes.

## Required checks before any resumed call

- Save a timestamped continuation amendment with the hashes of the preregistration, prepared protocol, allocation, stop record, full 256-job request plan and failed cache. This is history alongside v5, not a rewrite of v5.
- Replay the 184 submitted keys offline and verify their exact caches. Allow only the exact failed key with the exact terminal capacity signature above. Never retry it.
- Dispatch only the 72 unsent frozen jobs, preserving request identities and order. Any unexpected failure blocks later waves.
- Keep the failed slot in the collection denominator as infrastructure failure, while excluding it from the 600 eligible-value-failure count. Do not substitute or resample a case.
- Continue the fixed chunk accrual rule and 2,048 cap. Do not alter model, effort, source, prompt, scoring, ranking, timeout, worker ceiling, audit set or intervention design.
- Complete all original slots and all 96 audit calls before selection and interventions. Repeat the independent source/failure and exact paired-request lineage gates.

The current evidence supports continuing the unfinished predeclared collection after the explicit amendment. It does not guarantee that the capacity issue will not recur; another infrastructure failure must stop the continuation again.
