"""Write the current paid-study ledger, root summary and candidate metadata."""
import csv
from datetime import datetime, timezone
from pathlib import Path

import smoke_study as s
import paid_decision_study as paid
import paid_prose_analysis as analysis

ROOT=Path(__file__).resolve().parent


def finalize():
    result=s.load(analysis.OUT/'summary.json');assert result['complete'] and result['total_valid_probabilities']==576000
    assert (analysis.OUT/'validation.json').exists()
    api={r['classifier']:r for r in result['classifiers']}
    with (analysis.OUT/'paired_patterns.csv').open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
    def row(style,ident='gpt',population='raw'):
        return next(r for r in rows if r['classifier']==ident and r['population']==population and r['model']=='all' and r['zone']=='whole' and r['style_id']==style and r['threshold']=='0.5')
    def pair(style,ident='gpt',population='raw'):
        r=row(style,ident,population);return f"{r['baseline_present']} → {r['expanded_present']} out of {r['paired_posts']} paired replies"
    retry=ROOT/'data/simple_prose_v3_retry'
    (retry/'PROTOCOL.md').write_text('''# Authorized retry of one empty generation

## 2026-11-03, before generation

The owner explicitly requested rerunning the one failed generation and paid decision-model classification. The failed slot is expanded/14-seti/gpt-6.1-sol/02. Keep its original empty capacity-error record, all other generation files and the native original session unchanged.

The original session already contains later successful turns. Use the installed Codex app-server CLI's documented `thread/fork` operation with `lastTurnId` pointing to the first completed turn. This is local session control, not generation. Its native lazy-history reference is verified against the original first-turn byte/ordinal boundary and response items. The new CLI generation uses exactly the original continuation and visible message history, high effort, the same `codex exec resume` isolation settings and no tools/search. Actual generation is limited to one fresh CLI invocation, version 0.160.1.

## Session-control diagnostics

The first local session-control startup failed on an unknown field in the user's configuration with strict checking; it made no model call. Remove strict checking only from this non-generating control process and pass explicit fork overrides. The generation command still uses strict checking with user config and rules ignored, unchanged from the original study. The first fork validation expected materialized history; the installed CLI uses a lazy parent prefix instead. Validate that reference and reuse the same successful fork rather than creating another or regenerating anything. Full control transcripts and the expanded original prefix are retained privately.

## Completed retry

One fresh generation completed successfully with 176 words, exit code 0 and no tool events. It omitted the tag pair. Keep `post_body=null`, classify the entire raw reply only in the separately identified raw sensitivity, and do not retry for prose or formatting. The original failed record remains untouched. The current effective new condition now has 400 nonempty replies and 108 tag failures; strict pairing remains 292.

The retry consumed 8,901 input tokens, zero native cache reads and 399 output tokens under cumulative-session differencing. Its dollar equivalent is unavailable. The restored first-turn prefix was checked against the original native messages and preserved privately; no later draft is visible to this retry.

The existing successful turns 3–5 remain on their original branch and never saw the replacement. The current answer therefore retains a sensitivity excluding the whole Sol SETI block. This is a later, explicit failure recovery, not a claim that a coherent five-turn sequence was regenerated. The exact request and response share a hash-keyed private cache row; public outputs, hashes, command/settings and fork provenance remain inspectable.
''',encoding='utf-8',newline='\n')
    errors=sum(r['new_missing_cost_fields'] for r in api.values())
    classifier_protocol=f'''# Three paid classifiers: registration, transport and completion

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

The complete new ledger contains 606 HTTP 429 and 11 HTTP 502 responses from Mercury, all preserved. They have no native cost counter and are not called free or labelled absent. The request ledger contains {result['new_classifier_http_attempts']} fresh attempts and {result['reused_exact_requests']} exact historical imports. There are 4,009 fresh successful requests including nine diagnostic controls. The original 800 cached successes plus 4,000 new main successes supply the current study.

## Completed evidence

All three classifiers have 800 complete cases, 192,000 valid predicates each: 576,000 primary probabilities and zero final unreadable/missing predicates. Whole-text labels are primary; {result['regional_positive_whole_negative']} regional-positive/whole-negative results are retained without reconciliation. Sentence-window layout labels are diagnostic because extraction changes layout.

Negative contrast: OpenAI {pair('negative_contrast','gpt')}; Jev {pair('negative_contrast','jev')}; Mercury {pair('negative_contrast','mercury')}. Noun-heavy wording: OpenAI {pair('nominalization','gpt')}; Jev {pair('nominalization','jev')}; Mercury {pair('nominalization','mercury')}. The different frequencies are classifier judgments, not human writing-quality or accuracy scores. Intervals use 2,000 article-cluster bootstrap draws; they exclude classifier bias and prompt selection. The prompt/taxonomy were chosen after baseline inspection and writer aliases/collection dates remain a confound.

Known new classifier spend is ${result['known_new_classifier_cost_usd']:.9f}: OpenAI ${api['gpt']['known_new_cost_usd']:.9f}, Jev ${api['jev']['known_new_cost_usd']:.9f}, Mercury ${api['mercury']['known_new_cost_usd']:.9f}. There are {errors} fresh rejected attempts without cost counters. Cached historical OpenAI cost is separate. Native usage counters do not expose cache reads; three read-only generation-metadata probes also return null cached-token/cache-discount fields. Null is unknown, not zero. Metadata GETs are not model-generation calls.

Validation reconstructs every current probability and all 360 controls from native responses, checks request/source/post fingerprints and pinned routing, verifies the retry's original native prefix and CLI counters, and repeats all analysis with private inputs, original session, repository modules, network and CLI access unavailable. All tables replay byte-for-byte and all 38 regression tests pass. The self-contained notebook executes from cache. Local tracing/backfill status is recorded separately; full caches remain available if the service is unavailable.
'''
    (paid.OUT/'PROTOCOL.md').write_text(classifier_protocol,encoding='utf-8',newline='\n')
    s.save(paid.OUT/'progress.json',dict(complete=True,completed_pairs=1200,planned_pairs=1200,case_records=2400,
        valid_probabilities=576000,new_api_attempts=result['new_classifier_http_attempts'],reused_exact_requests=800,
        known_new_spend_usd=result['known_new_classifier_cost_usd'],unreadable_cases=0,
        updated_at_utc=datetime.now(timezone.utc).isoformat(),note='Final state combines first-pass and transport-repair ledgers.'))
    candidate_path=ROOT/'data/prompt_conditions/simple_prose_v3.json';candidate=s.load(candidate_path)
    old=candidate.get('earlier_free_stage')
    if old is None:
        old={k:candidate.get(k) for k in ['new_model_calls','new_writer_calls','classifier_http_attempts','known_reported_classifier_cost_usd','unpriced_classifier_attempts','free_classifier','free_classification_results','free_classification_report']}
    candidate['earlier_free_stage']=old
    for key in ['free_classifier','free_classification_results','free_classification_report']:candidate.pop(key,None)
    candidate.update(status='Full comparison with one authorized empty-failure retry and three paid classifiers: 400 effective replies per condition, 576000 valid study probabilities. No human quality validation.',
        results='data/paid_prose_comparison/summary.json',outputs='data/paid_prose_comparison/outputs.md',
        new_model_calls=1+result['new_classifier_http_attempts'],new_writer_calls=1,
        classifier_http_attempts=result['new_classifier_http_attempts'],reused_historical_paid_requests=800,
        model_call_counting_note='Current requested stage only: one fresh writer retry plus fresh paid-classifier HTTP attempts, including rejected transport attempts and nine controls. The 800 historical exact imports are not new calls; earlier free-stage counts are nested separately.',
        known_reported_classifier_cost_usd=result['known_new_classifier_cost_usd'],unpriced_classifier_attempts=errors,
        current_retry_reported_cost_usd=None,expanded_writer_attempts_including_retry=401,effective_expanded_replies=400,
        paid_classifiers=[r['model'] for r in api.values()],paid_classification_results='data/paid_prose_comparison/summary.json',
        paid_classification_report='README.md',strict_paired_replies=292,raw_paired_replies=400,
        nonempty_tag_failures=108,original_generation_failure_retained=True)
    candidate['limitations']=['Writer conditions were collected at different times using undated aliases; prompt, continuation and tags change together.',
        'Prompt and taxonomy were selected after baseline inspection; no held-out human-labelled quality test is provided.',
        'Classifiers disagree sharply on several definitions and some categories sit at a floor. Labels are never combined into a quality score.',
        'Tag failures select the strict population. Raw sensitivity preserves exact malformed text. The retry uses the original first-turn prefix, while later drafts remain on the original branch; an entire-block exclusion is reported.',
        'Mercury transport failures were recovered with slower pacing; rejected requests without native cost fields remain unpriced.']
    s.save(candidate_path,candidate)
    history=ROOT/'data/PROTOCOL.md';marker='\n## 2026-11-03, authorized generation retry and three paid classifiers\n'
    entry=f'''
The owner requested the one failed generation be rerun and paid decision models used for classification. Recover expanded/14-seti/gpt-6.1-sol/02 with one high-effort codex exec call from a native fork through the original first completed turn, using the unchanged continuation, no tools/search and CLI 0.160.1. Verify the lazy first-turn byte/ordinal reference and visible messages rather than giving the retry later drafts. Original session, failed record and all other outputs remain unchanged. The retry succeeds with 176 words but no valid tags: effective new replies become 400, tag failures 108 and strict paired bodies remain 292. Existing later turns did not see this replacement, so retain an entire-block exclusion sensitivity. See `simple_prose_v3_retry/PROTOCOL.md` for local-control diagnostics and native provenance.

Freeze all 800 effective fingerprints and the same 40 definitions/six regions before paid calls. Use pinned OpenAI Decisions, Jev 1.14 and Mercury Decide, single-provider routing and no fallback/tools. The typed API exposes no effort control; writer calls stay high. Reuse the 800 exact historical OpenAI baseline requests after full-wire/hash matching, with no fresh request or live trace. All other paid results are separate from the earlier free labels; the free comparison uses the same 399 unretried pairs across all classifiers.

All six fixed smoke cases and nine authored-control requests return readable predicates. First-pass Mercury rate limits/gateway errors and the fresh-request allowance leave 45 partial and 34 uncached cases. Preserve raw attempts and partial indices, then amend only transport: serialize Mercury at six-second starts, allow three extra exhausted-leaf attempts, honor cooldown/backoff, and reuse valid results. All 79 incomplete cases recover in 107 fresh requests. There are 606 rate-limit and 11 gateway-error attempts without cost fields; none is counted as absent prose or as a free request.

The current paid set has 2,400 complete cases and 576,000 valid probabilities, with zero current unreadable/missing predicates. Native reconstruction also checks 360 authored-control probabilities. New reported classification cost is ${result['known_new_classifier_cost_usd']:.9f} across {result['new_classifier_http_attempts']} fresh HTTP attempts. Historical reused OpenAI cost $2.2653584 is not charged again. Codex retry dollars and the {errors} rejected-call costs are unavailable. Native usage and three generation-metadata probes expose no cache-read counts; unknown is not zero. The earlier Claude writer equivalents remain $4.9356308.

Negative contrasts are {pair('negative_contrast','gpt')} under OpenAI, {pair('negative_contrast','jev')} under Jev and {pair('negative_contrast','mercury')} under Mercury. Noun-heavy labels disagree: {pair('nominalization','gpt')}, {pair('nominalization','jev')} and {pair('nominalization','mercury')}, respectively. Rewrite the report, notebook and root row around these three paid classifiers and retain all earlier data as history. The study has no human writing-quality outcome and reports model-specific floors, sensitivities and regional contradictions without manual reconciliation.

All 38 regression tests pass. Native retry context/usage, request fingerprints, dated providers and every probability are checked. A portable replay without sources, private caches or repository modules blocks network and CLI access and reproduces all analysis tables byte-for-byte. The notebook executes from embedded helpers and cached data; seven figures and local links are reviewed. Protocols, file hashes, failure records and tracing/backfill status remain separate from the reader's opening.
'''
    history.write_text(history.read_text(encoding='utf-8').split(marker)[0]+marker+entry,encoding='utf-8',newline='\n')
    root_readme=ROOT.parents[1]/'README.md';lines=root_readme.read_text(encoding='utf-8').splitlines()
    for i,line in enumerate(lines):
        if line.startswith('| 40 | ['):
            lines[i]='| 40 | [Changing LinkedIn prose and checking the classifier](notebooks/40-linkedin-writing-habits/) | Drafts can repeat hooks, transitions and endings. Four writers produce five posts from 20 frozen AI articles under a minimal request and prose constraints: 400 effective replies per condition. Three paid decision models classify 40 overlapping patterns in six locations. Does the measured change depend on the classifier? | Negative-contrast labels fall from 289 to 31 with OpenAI Decisions, 85 to 3 with Jev, and 48 to 1 with Mercury (400 paired replies each). Remaining noun-heavy counts range from 0 to 314/400 across classifiers. There are 108 new-condition tag failures; 292 valid-body pairs are reported separately. These are exploratory model judgments, with no human quality validation. |'
        elif line.startswith('| 40 | Twenty complete'):
            lines[i]='| 40 | Twenty complete public AI news articles; 800 effective writer replies and three paid-classifier audits | Fresh when first collected: articles published 23–30 October 2026; writing collected 1–2 November, with one authorized retry 3 November | Publisher inputs stay private and git-ignored; URLs/hashes, original failure, generated replies and native classifier results are retained |'
    root_readme.write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':finalize()
