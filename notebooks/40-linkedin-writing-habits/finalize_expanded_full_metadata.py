"""Update the current study's metadata after cached analysis and validation."""
import csv
from datetime import datetime, timezone
from pathlib import Path
import smoke_study as s
import expanded_full_analysis as a
import full_free_classification as c
import expanded_full_study as w


def finalize():
    summary=s.load(a.OUT/'summary.json');api=summary['classifier']
    assert api['cases']==800 and (a.OUT/'validation.json').exists()
    last=s.load(c.OUT/'collection_state.json')
    s.save(c.OUT/'progress.json',dict(completed_pairs=400,planned_pairs=400,active_pairs=0,pending_pairs=0,
        fresh_api_attempts=last['new_api_attempts'],total_api_attempts=api['attempts'],writers_finished=True,
        complete=True,updated_at_utc=datetime.now(timezone.utc).isoformat(),
        note='Final snapshot derived from both completed collection passes and all 800 case records. Fresh attempts refers to the last cache-resuming pass.'))
    with (a.OUT/'paired_patterns.csv').open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
    def row(style,pop='raw_sensitivity'):
        return next(r for r in rows if r['population']==pop and r['model']=='all' and r['zone']=='whole' and r['style_id']==style and r['threshold']=='0.5')
    def pair(style):
        r=row(style);return f"{r['baseline_present']}/{r['paired_posts']} → {r['expanded_present']}/{r['paired_posts']}"
    transport=f'''# Full free-classifier protocol and completion record

## Registered design, 2026-11-02 Toronto time

The owner authorized the full expanded-prompt study and requested free decision models. The frozen `protocol.json` retains the same 40 definitions, useful exceptions, per-post rules and six regions as the original classifier audit. Both current conditions use the dated `respan/span-01-lite-20260925` standard route, restricted to Respan, no fallback, maximum input/output prices zero. Its live endpoint catalogue advertises zero prices; the tiny route control reported zero and left the account's free-variant daily counter unchanged. This is a documented zero-price route, not a second classifier checkpoint, paid fallback or new account.

The `:free` pilot route is retained as history and not mixed into current counts. Reclassifying the original baseline through the same checkpoint avoids confounding a prompt change with a paid-versus-free classifier change. The classifier sees source, whole measured text, regions and rubric, but no writer identity, prompt condition or previous drafts. Shuffled matched pairs and within-pair arm order use fixed seeds. Writer conditions themselves were collected sequentially, so backend drift remains a confound.

The strict population uses the frozen baseline body parser and exact enclosed expanded body. A secondary raw-text audit was declared after early writer tag failures were observed, before any full-run style label. For nonempty invalid-tag replies it classifies the exact entire raw reply, with `strict_readable=false` and `input_kind=raw_unparsed_response`. It never guesses a body or discards a closing tag. No prose labels are manually assigned. The primary tag-valid population is selected by compliance, which limits generalization.

Each nonempty reply has 240 predicates: 40 patterns in six regions. Whole-text labels are primary. Assembled regional windows can change layout, so regional formatting labels are diagnostic. The unchanged questions are packed in order into batches of max(4, min(40, floor(900000 / state_characters))) questions. This size rule was frozen before full classification. Eight pair workers and a 0.5-second minimum fresh-request start interval bound transport. Each batch repeats the complete state. A long-source authored control, separate from study data, returned the intended obvious contrast/hashtag responses at native cost zero. It is not representative classifier validation or proof of full-source attention.

Successful exact requests replay from hash-keyed full private request/response records. All HTTP attempts remain cached. A 504/413 batch with more than four questions splits in half; other eligible transient failures have at most three attempts per leaf and honor Retry-After. Valid answers are never retried. Malformed or missing answers are unreadable, not absent. No generation is redrafted because of its wording or classifier label.

## Completion, 2026-11-02 Toronto time

There are 800 case records: 400 baseline and 400 expanded, including one explicit unreadable-generation record. The full audit returned {api['valid_probabilities']:,} valid typed probabilities; {api['invalid_probabilities']} invalid and {api['missing_probabilities']} missing predicates among nonempty cases. Primary strict comparison has {summary['strict_pairs']} matched pairs; exact-raw sensitivity has {summary['raw_pairs']}. The capacity-interrupted Sol SETI block is also excluded in a separate sensitivity.

The primary ledger contains {api['attempts']} HTTP attempts, statuses {api['statuses']}, with reported cost ${api['known_reported_cost_usd']:.6f}. Successful requests without cost fields: {api['successful_missing_cost']}; failed requests without cost fields: {api['failed_missing_cost']}. Native input tokens: {api['native_input_tokens']}; output tokens: {api['native_output_tokens']}. Cache-read counters are unavailable, not zero. The long-source control and route control each reported zero and are separate from this primary ledger. Earlier pilot attempts, including the unpriced 504, remain in their own ledger.

Thresholds 0.5, 0.2 and 0.8 and 2,000 article-cluster bootstrap draws are descriptive choices, not human-calibrated guarantees. The article-weighted estimate resamples all available paired cells within each sampled article; post-weighted changes are retained separately. Missing/tag-failed outputs are not converted to negative labels. The 40 overlapping patterns are never added into a quality score. The taxonomy/prompt were selected after viewing baseline data; no human factual, preference or editing-time outcome was collected.

Native answer reconstruction, writer/source/request fingerprints, exact raw sensitivity inputs, price/provider guards and source-free offline replay are checked in `../expanded_full_comparison/validation.json`. All 35 regression tests pass. Current reader material replaces the earlier paid-classifier comparison; old data remain untouched as design history.
'''
    (c.OUT/'PROTOCOL.md').write_text(transport,encoding='utf-8',newline='\n')
    finish=f'''\n## Completion record, 2026-11-02 Toronto time\n\nAll 400 planned slots were attempted in 80 model/article conversations. Twenty matching Kimi responses were imported byte-for-byte; 380 fresh CLI calls supplied the other slots. There are 399 nonempty replies, one empty Sol capacity failure, 292 valid enclosed bodies, 107 nonempty invalid-tag replies (86 with no tags; 21 with only a closing tag) and no outside commentary. No content-based generation retry occurred. Sol SETI turns 3–5 continued after the failed second slot, as documented above; excluding that entire block is a reported sensitivity. The exact request history retains the unanswered user turn.\n\nKnown Claude dollar equivalents are $4.9356308 including $0.2131714 from the preview; the 380-call extension adds $4.7224594 known Claude equivalents. Codex dollars and actual total subscription charges are unknown. Weighted warm-turn cache-read shares are Sol 81.98%, Terra 89.00%, Opus 84.19% and Sonnet 82.30%; the failed request has unknown counters and is excluded from these ratios. Full native requests/responses and logs are retained.\n\nThe same free decision checkpoint reclassifies both current arms: see `../simple_prose_v3_full_classifier/PROTOCOL.md`. Negative-contrast labels are {pair('negative_contrast')}; noun-heavy wording is {pair('nominalization')}. These are overlapping, unverified classifier labels, not human writing-quality scores. The strict valid-body comparison and raw-text sensitivity stay separate.\n'''
    path=w.OUT/'PROTOCOL.md';text=path.read_text(encoding='utf-8').split('\n## Completion record,')[0]
    path.write_text(text+finish,encoding='utf-8',newline='\n')
    candidate=s.load(w.ROOT/'data/prompt_conditions/simple_prose_v3.json')
    candidate.update(status='Full 20-article study: 400 slots attempted, 399 nonempty replies, 292 valid tagged bodies; both conditions reclassified with the same free checkpoint. No human quality validation.',
        results='data/expanded_full_comparison/summary.json',outputs='data/simple_prose_v3_full/outputs.md',
        known_reported_writer_cost_usd=4.9356308,known_reported_classifier_cost_usd=0,
        new_writer_calls=400,imported_matching_pilot_posts=20,fresh_full_extension_writer_calls=380,
        classifier_http_attempts=api['attempts'],new_model_calls=400+api['attempts']+119+2,
        model_call_counting_note='All expanded-condition writer calls (20 preview + 380 extension), full primary classifier attempts, 119 historical pilot API attempts, and two full-route diagnostic controls. Baseline and intermediate paid runs retain separate historical ledgers.',
        free_classifier=c.MODEL,free_classification_results='data/expanded_full_comparison/summary.json',free_classification_report='README.md',
        unpriced_classifier_attempts=api['failed_missing_cost']+api['successful_missing_cost']+1)
    candidate['planned_output_handling']['status']='Implemented for preview and full study; strict format failures retained separately.'
    candidate['planned_output_handling']['classification']='Strict comparison uses only the exact enclosed body. A separately declared sensitivity classifies exact nonempty invalid-tag raw replies, preserving input type and excluding them from strict rates.'
    candidate['limitations']=['Prompt, continuation and output contract change together; conditions were collected at different times using undated writer aliases.',
        'The prompt and taxonomy were chosen after baseline inspection; matching Kimi preview outputs are reused rather than held out.',
        'Many free-classifier contextual categories are near a floor; controls are small and no human labels calibrate probabilities.',
        'Missing tags select the strict population. Raw sensitivity preserves malformed output, not an inferred post body. One capacity-interrupted block has its own sensitivity.']
    s.save(w.ROOT/'data/prompt_conditions/simple_prose_v3.json',candidate)
    history=w.ROOT/'data/PROTOCOL.md';marker='\n## 2026-11-02, full expanded-prose comparison with free classification\n'
    body=f'''\nThe owner authorized the full study after the preview. The unchanged 15-constraint prompt, explicit standalone continuation, high effort, CLI-only writers and tools/search-off settings were frozen in the full registration. Reuse all 20 Kimi preview slots, including its format failure, then attempt the other 380 slots. One empty Sol SETI capacity error remains a failure; three later numbered slots continued in the same native session without retrying the failed slot. All 400 slots were attempted, with 399 nonempty replies, 292 valid tagged bodies and 107 nonempty tag failures. Exact request histories, source hashes, native usage and raw logs are validated.\n\nBoth the original 400 baseline slots and the 400 expanded slots are audited with the same dated free Span-01 Lite checkpoint and rubric; old paid labels remain separate. The standard zero-price route passed price/provider controls. The main ledger has {api['attempts']} HTTP attempts, {api['valid_probabilities']:,} valid probabilities and ${api['known_reported_cost_usd']:.6f} known reported cost. There are {api['failed_missing_cost']+api['successful_missing_cost']} primary attempts without cost fields. No paid fallback was used. Whole-text labels are primary; regional contradictions are preserved. Strict valid-body pairing, exact-raw sensitivity and a sensitivity excluding the capacity-interrupted block are reported. Missing answers never become absent labels.\n\nNegative contrast is {pair('negative_contrast')}; noun-heavy wording is {pair('nominalization')}, in the secondary matched nonempty population. The rewritten README, notebook and root table give one current answer from this comparison. Historical intermediate results remain in their data directories. The expanded condition's known Claude equivalent is $4.9356308 including the preview; Codex dollars are unknown. Classifier cache counters are unavailable. Native writer warm-cache ratios, literal phrases, all 40 definitions and every region are retained.\n\nAll 35 regression tests pass. Full writer/native provenance, API answer reconstruction and exact price guards pass. The notebook is executed top to bottom from public caches; a portable replay without source/private files or repository modules blocks network and CLI calls and reproduces analysis tables byte-for-byte. The six current figures are visually inspected. Local tracing/backfill availability is recorded separately; unavailable service access never triggers a model replay. See the full writer and classifier protocols and `expanded_full_comparison/validation.json` for details.\n'''
    history.write_text(history.read_text(encoding='utf-8').split(marker)[0]+marker+body,encoding='utf-8',newline='\n')
    root=w.ROOT.parents[1]/'README.md';text=root.read_text(encoding='utf-8');lines=text.splitlines()
    for i,line in enumerate(lines):
        if line.startswith('| 40 | ['):
            lines[i]=f"| 40 | [Can prose constraints change recurring LinkedIn writing habits?](notebooks/40-linkedin-writing-habits/) | Different drafts can repeat hooks, transitions and endings. Four writers each attempt five posts from 20 frozen AI articles under a minimal request and expanded prose constraints: 400 slots per condition, all at high effort. The same free typed classifier audits 40 overlapping patterns in six regions; 292 tag-valid pairs and 399 nonempty pairs are compared separately. | In the broader nonempty audit, hashtag-tail labels change from {pair('hashtag_tail')}, negative contrast from {pair('negative_contrast')} and noun-heavy wording from {pair('nominalization')}. The expanded prompt produces 107 nonempty tag failures and one empty capacity failure. Visible habits change, but contextual categories often sit near a floor and no human writing-quality improvement is established. |"
        elif line.startswith('| 40 | Twenty complete'):
            lines[i]='| 40 | Twenty complete public AI news articles; 800 writer slots across the current two prompting conditions | Fresh when collected: sources published 23–30 October 2026; writer collection 1–2 November Toronto time | Publishers retain article rights; full source text git-ignored, public URLs and hashes retained; generated outputs and free-classifier responses cached in the experiment |'
    root.write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':finalize()
