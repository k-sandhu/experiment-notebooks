# Three paid classifiers: registration, transport and completion

## Registered before paid calls, 2026-11-03

The owner requested paid decision models. Use all three paid, repo-approved live endpoints: OpenAI GPT-6 Luna Decisions (`openai/gpt-6-luna-decisions-20261006`), TypeSafe Jev 1.14 (`typesafe/jev-1.14-20261014`) and Inception Mercury Decide (`inception/mercury-decide-20260930`). `catalogue.json` preserves the live dated IDs, providers, context sizes and prices. Each successful response must return the pinned dated model and its named provider; fallback is disabled. No tools/search or unsupported effort parameter is sent. Original writer calls and the retry use high effort.

`protocol.json` freezes all 800 effective response fingerprints, the unchanged 40 definitions and useful exceptions, six regions, 0.5 primary threshold, 0.2/0.8 sensitivities, provider routing, request packing, controls and budgets. The only writing overlay is the owner's one retry. All other generated outputs remain unchanged. The strict analysis uses 292 paired valid bodies; the raw sensitivity uses 400 paired nonempty replies, retaining missing-tag text exactly. The capacity/retry block is excluded in an additional sensitivity.

Two 120-question batches normally return all 240 predicates for a case. States are identical and question sets disjoint. Matched condition order and case order are shuffled; writer identity, prompting condition and other drafts are withheld. There is no majority vote, hand classification or combined prose-defect score. The free classifier is compared only on the common unretried 399 pairs.

The old OpenAI baseline has 800 full-payload exact matches. Reuse them only after comparing the complete private wire body and hash with the new payload and matching native response. These are historical requests with $2.2653584 reported cost; no new HTTP request or live trace is emitted. Other current paid calls are fresh. Full request and response are stored together privately for every new or imported row. Public rows redact publisher-bearing state and retain request/question fingerprints and native results.

Default collection knobs are small (two article/model/turn pairs and 12 fresh calls); full collection is explicitly invoked. A $20 new-classification guard reserves allowance before fresh requests and retains reservations when native costs are absent. The preregistered forecast was $5–$10; actual known reported new cost is lower. This is not an actual subscription invoice or a guarantee of missing failure costs.

## Smoke and controls

For each classifier, expanded Kimi Sol/01 and baseline longest-source Sonnet/01 are fixed smoke cases, both batches. All six cases returned readable probabilities. Their exact requests are reused in the main run, and no rubric or threshold is tuned to their labels. The three fixed authored fixtures from the free audit are separately evaluated in the whole region. Their 360 probabilities are diagnostics, excluded from the 576,000 study predicates. Intended positive expectations are not a representative human-labelled validation set.

## First-pass outage and transport-only recovery

The first pass returned 789 fully readable OpenAI cases, 794 Jev cases and 738 Mercury cases. Mercury also had 45 partial case indices after transport attempts exhausted. The initial request allowance left 34 cases uncached across the three classifiers. `first_pass.json`, `transport_repair.json` and `case_history/` retain that evidence.

The amendment adds at most three attempts per exhausted leaf (six total), fills only missing cases and keeps every valid typed response. Mercury recovery is serialized with six seconds between fresh starts, an initial 60-second cooldown and at least 45 seconds after a new 429. Cached failures do not incur an artificial new backoff. No semantic answer, question text, state, taxonomy or probability threshold changes. All 79 incomplete cases recover in 107 fresh requests; no current case remains unreadable.

The complete new ledger contains 606 HTTP 429 and 11 HTTP 502 responses from Mercury, all preserved. They have no native cost counter and are not called free or labelled absent. The request ledger contains 4626 fresh attempts and 800 exact historical imports. There are 4,009 fresh successful requests including nine diagnostic controls. The original 800 cached successes plus 4,000 new main successes supply the current study.

## Completed evidence

All three classifiers have 800 complete cases, 192,000 valid predicates each: 576,000 primary probabilities and zero final unreadable/missing predicates. Whole-text labels are primary; 5329 regional-positive/whole-negative results are retained without reconciliation. Sentence-window layout labels are diagnostic because extraction changes layout.

Negative contrast: OpenAI 289 → 31 out of 400 paired replies; Jev 85 → 3 out of 400 paired replies; Mercury 48 → 1 out of 400 paired replies. Noun-heavy wording: OpenAI 72 → 68 out of 400 paired replies; Jev 374 → 314 out of 400 paired replies; Mercury 0 → 0 out of 400 paired replies. The different frequencies are classifier judgments, not human writing-quality or accuracy scores. Intervals use 2,000 article-cluster bootstrap draws; they exclude classifier bias and prompt selection. The prompt/taxonomy were chosen after baseline inspection and writer aliases/collection dates remain a confound.

Known new classifier spend is $3.720108074: OpenAI $2.258266600, Jev $0.930274674, Mercury $0.531566800. There are 617 fresh rejected attempts without cost counters. Cached historical OpenAI cost is separate. Native usage counters do not expose cache reads; three read-only generation-metadata probes also return null cached-token/cache-discount fields. Null is unknown, not zero. Metadata GETs are not model-generation calls.

Validation reconstructs every current probability and all 360 controls from native responses, checks request/source/post fingerprints and pinned routing, verifies the retry's original native prefix and CLI counters, and repeats all analysis with private inputs, original session, repository modules, network and CLI access unavailable. All tables replay byte-for-byte and all 38 regression tests pass. The self-contained notebook executes from cache. Local tracing/backfill status is recorded separately; full caches remain available if the service is unavailable.

## Tracing completion check

The backfill dry run found 11,386 traceable cached calls with no missing inputs or duplicate keys. Three metadata-only rows were excluded. The send attempt stopped at the local Langfuse health check because port 3300 refused the connection; no successful trace submission is claimed. Full caches remain intact. See [the tracing status](tracing_status.json) for counts and private log locations.
