# Kimi preview of the expanded prose constraints

## 2026-11-02, registered before generation

The owner authorized a preview on the existing Kimi article only: all four requested writer models, high effort, five posts per model. This is 20 fresh writer invocations in four new conversations. No full-study run or Decisions classification is part of this preview. The exact initial template and follow-up are frozen in the adjacent preregistration before the first invocation, with source and prompt hashes, CLI versions and settings.

The first turn receives the saved expanded-constraints prompt and the complete frozen article text. Turns 2-5 receive only the saved follow-up explicitly requesting another independent standalone post from the same article. Conversation IDs must remain constant within each model and be disjoint from previous runs. Independent describes the requested post, not statistical independence from earlier drafts.

Use the already validated CLI isolation, high effort, no tools and no web search. Run different model blocks concurrently and turns within each block sequentially. Keep the current runtime context limitations. There are no content-based retries or substitutions. Stop a model after a CLI, tool or session failure; retain tag failures and continue the requested drafts without silently regenerating them.

Require exactly one nonempty, non-nested `<linkedin_post>...</linkedin_post>` pair. Preserve raw output, the enclosed body and exact outside text separately. Missing, malformed, empty or ambiguous tags are format failures and are never guessed. Outside commentary is format noncompliance but does not make an otherwise enclosed post unreadable. Tags and outside text will be excluded from later post classification.

Private, git-ignored caches are keyed by the complete invocation request, including prompt, known conversation text, model, settings, command and session ID. Each stores the full request and response together. Public derivative records replace the publisher's article text with its template placeholder, retain the source hash and link to the private cache. Preserve every native CLI event stream, usage counter and output without editing the generated prose.

Check local Langfuse health with a two-second timeout before generation and trace fresh calls through OTLP if available; cache replays send nothing. Keep the Claude per-invocation $1 limit and enforce the explicit 20-new-call ceiling. Record native cache reads/writes, warm-turn reuse and available cost equivalents; unavailable dollars remain unknown. No extra warm-up call is made. Report all 20 raw outcomes for review before any full rerun.

## 2026-11-02, completed preview

All 20 CLI requests completed successfully, with four new conversation IDs, high effort, no observed tools and five distinct normalized responses per model. Nineteen responses contain one valid post tag pair. Terra's first response omitted both tags; preserve it as an unparsed raw response, without guessing a body or replacing the generation. All 19 tagged responses have no non-whitespace material outside the tags. Neither Claude model returned an outside correction note in this pilot.

Sol's first native stderr contains a system-skill installation access-denied startup warning. The invocation still returned exit code zero and a completed response with no observed tool event. Preserve that warning with the raw evidence; the existing limitation concerning mandatory CLI runtime scaffolding still applies.

Warm-turn cache-read shares are Sol 91.7551%, Terra 72.2995%, Opus 81.0580% and Sonnet 76.5441%. Native Claude reported equivalents total $0.2131714: Opus $0.1208008 and Sonnet $0.0923706. Codex dollar equivalents and actual subscription charges remain unknown. There were no classifier calls, extra warm-ups, content retries or full-study calls.

All 31 regression tests pass. The validation checks all 20 full private request/cache fingerprints, exact input and follow-up messages, source identity, native output identity, four new sessions, extraction and format outcomes. The review export reproduces byte-for-byte with article inputs absent and network and subprocess calls blocked. See `validation.json`, `summary.json` and `outputs.md` beside this file.

Local Langfuse was unavailable, so fresh tracing was skipped. The required backfill dry run recognized all 20 complete private requests and responses with no missing inputs, missing outputs or normalization errors. The subsequent backfill attempt could not reach the local service; `tracing_status.json` records this. Nothing was sent twice, and the saved full caches can be backfilled when the service is available.
