# Free decision-model classification of the tagged Kimi preview

## 2026-11-02, model discovery and registration before classification

The owner requested free decision models on OpenRouter. Query the live models API with `output_modalities=decisions`, not the default text-model catalogue, and freeze the response and endpoint details in `catalogue.json`. There is one live zero-price checkpoint, Span-01 Lite, listed under standard and `:free` aliases. Its dated free route is `respan/span-01-lite-20260925:free`, served by Respan. The checked Mercury, Jev and Clef free aliases have no active endpoint. Do not count aliases as independent models or substitute paid models.

The owner's free-model request authorizes this free classification route. Add Respan Span-01 Lite, restricted to zero-price endpoints, to the repository's decision-model allowlist. Pin the dated free route and provider, disable fallback, send maximum prompt and completion prices of zero, and stop if a native response reports nonzero cost. No text writer is called again, and no full-study run is authorized by this classification step.

Use the unchanged 40 definitions, useful exceptions, per-post rules, six regions and thresholds from the earlier audit. The provider sees source and enclosed post only, with no writer label, prompt, condition, previous draft or earlier classifier result. The classifier API exposes no reasoning-effort setting. Preserve every native probability without manual relabelling. Classifier labels are unvalidated judgments about wording, not human quality scores.

Classify the 19 posts with valid tag pairs, with two requests of 120 questions each: 38 requests and 4,560 probabilities. Terra's first untagged response remains excluded as an unreadable generation-format outcome, never counted as absence of a prose pattern. Smoke-test Sol and Sonnet's first posts, both batches, and reuse those exact four requests in the complete collection. Definitions and labels are not tuned to the smoke. One attempt per complete request; transport or schema failures remain unreadable and stop collection for review. Pace starts at least 3.2 seconds apart.

Keep the full request and response together in a private hash-keyed cache, with a public derivative containing the returned answers and source/post fingerprints. Check local Langfuse health and trace fresh requests only if available. Offline analysis sends no requests. Keep results separate from the earlier paid classifier; changes across classifiers cannot establish a prompt effect. The context limit and weight openness of Span-01 Lite are not published in the checked catalogue, so do not claim either.

## 2026-11-02, transport-driven batch amendment before any style labels

The first 120-question request returned HTTP 504 after 30.8 seconds, with no usable answers and no cost counter. Preserve that response under `responses/` as an unreadable diagnostic. A two-question control on a tiny state then returned HTTP 200, correct near-certain present/absent probabilities and native cost zero. The pinned free route works on a small request.

Before any style probability was returned, reduce each primary batch to one region and 40 questions. Keep all 40 definitions, the full source/post state, each question's wording, all six regions and all thresholds unchanged. Freeze the revised plan in `protocol_40.json` and save primary responses under `responses_40/`: 114 requests still produce the same 4,560 planned answers. Smoke-check the whole-post batch for Sol and Sonnet's first posts, reuse those two requests, then finish the remaining requests. No manual style labels or content-based retries are introduced. The tiny control remains separate from measured style classifications.

Both reduced smoke batches returned 40 valid probabilities at native cost zero. Complete the remaining requests with at most two in flight and starts at least 3.2 seconds apart, as frozen in `scheduling.json`. This transport scheduling change preserves all wire content and classification thresholds.

## 2026-11-02, completed primary classifications and separate controls

All 114 primary requests completed with HTTP 200, 4,560 valid probabilities and native reported cost zero. All provider replies identify Respan and `respan/span-01-lite-20260925`. The whole-post analysis has one positive among 760 questions at 0.5 and none at 0.8: repeated conclusion in Terra's fifth post at 0.50605124. This near-floor result cannot rank writers or establish better prose. There are 14 region-positive/whole-negative inconsistencies; preserve them without manual relabelling.

After observing this near-floor result, freeze three authored sanity-check fixtures and expected observable patterns under `controls/protocol.json`, before making their calls. These are post-hoc controls and are excluded from measured post frequencies. The classifier flags 9 of 10 intended positive instances and leaves all 6 intended negative instances absent. It misses the intended question-and-answer pivot in the rhetorical fixture (0.06356258). The controls show recognition of several obvious patterns but are not a human-labelled validation set or evidence of accuracy on subtle prose.

There are 119 API attempts in total: 114 primary calls, the failed large batch, one tiny transport control and three pattern controls. Every successful call reports zero cost. The failed large batch exposes no cost counter. Provider cache-read/write counters are not exposed; do not interpret their absence as zero cache use. No writer was called again and no full-study collection ran.

All 33 regression tests pass. Validation checks every primary full-request fingerprint, the unchanged rubric, exact source and post, native provider/model/cost, all question slots, exclusion of the generation-format failure and source-free offline replay. The report and figure are built from cached probabilities. Local tracing/backfill status is recorded separately; full requests remain available for later backfill.

The backfill dry run recognizes all 139 new cached attempts across this worktree: 20 writer attempts and 119 classifier attempts. The failed 120-question diagnostic accounts for the one error trace and missing model output; every trace has its input. The local Langfuse service remains unavailable, so the actual backfill attempt could not send the traces. Full caches are preserved for later ingestion, without duplicate sends.
