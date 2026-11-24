from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import json, gzip, hashlib
import pandas as pd

root=Path(__file__).resolve().parents[1]
data=root/'data'

def load(name):
    return json.loads((data/name).read_text(encoding='utf-8'))

def table(frame):
    if not len(frame):return 'No rows.\n'
    return frame.to_markdown(index=False,floatfmt='.6g')+'\n'

parts=['# Notebook 34 engineering handoff\n\nWritten '+datetime.now(timezone.utc).isoformat()+'. Claude owns all reader-facing prose. Delete HANDOFF.md before commit.\n']
complete=(data/'replay_validation.json').exists()
parts.append('Status: '+('live collection and offline executed-notebook replay complete.' if complete else 'implementation and development in progress; final collection/replay counts pending.')+'\n')
parts.append('''## 1. Design and choices

Claim #95, requested folder and notebook name. No git/gh operations. No repo file outside this notebook folder was changed. No README.md or PROTOCOL.md was authored. Notebook markdown cells are structured NARRATIVE TODO placeholders; Claude must write the introduction, worked explanations, diagrams, results interpretation and final reading section.

Notebook 33 source supplied at commit cf854303, copied from the absolute source path in data/from_33/SOURCE.md. All nine source freeze hashes checked after CRLF->LF normalization. The full source archive and judgment/solve exports are immutable copies. data/cache_from_33.jsonl.gz adds origin metadata to copied baseline/development attempt entries; the full request and key are unchanged. Imported records are excluded from new spend. The offline engineering audit recovers exactly 206 agreed and 34 disagreed of the original 240, with zero agreed-both-wrong and zero new calls.

New seed 3410302026; final generator level10, unchanged generation parameters, same four families and writer pins. Only checker child-Python launch flags differ from source33: -I becomes -X utf8 -E -P as requested; standard-library checker, labels and hidden tests are unchanged. No difficulty tuning or per-item test-driven changes. Original 24 development items reused for the development pipeline check, rather than spending on another difficulty-tuning draw: the requested final level10 is already fixed and the original strong-judge results provide non-ceiling examples. Both new prompt conditions were tested there before the full freeze.

Stopping rule fixed in data/freeze_record.json before generating new test batches: complete 120-item balanced batches (30 per family), stop at first cumulative >=80 primary lenient disagreements or 480 new items. Each batch is immutable and independently hashed before its first strong test verdict. Original/new/all results are always reported separately. The combined data/exam_v1.jsonl is a derived convenience export; original items are taken unchanged from the source exam and new items from batch files.

One strong verdict per model/item requires both answer-order replies readable and consistent. Different consistent winners or either split -> disagreement. Missing original verdicts form a separate missing route and are sent to the assumed-correct human. Tie-breakers are called only on primary disagreements. Each alone or reasons method uses both displayed answer orders, collapse to one item: consistent A/B -> exact checker result; split -> expected .5; any unreadable -> item unreadable. Failure variant gives 0; coin variant gives .5 to unreadable. Readable-only accuracy excludes unreadable items. Split is never reported as a readable wrong verdict.

Reasons prompts include task, both complete candidates, both same-order strong verdicts/confidences/reasons, anonymized as Judge1/2. Label order uses a deterministic independent seed per item/order, shared across weak models. This is independent judgments with reasons, not a live adversarial debate. Revision gets self and peer original judgment, independently once per displayed order; no communication after the two revisions. Only consistent agreement across both revised judges and both orders resolves an item. Unreadable revision is missing; readable nonagreement is unresolved. revise scores unresolved as automatic failure; revise+human sends unresolved or unreadable revised disagreements to a person.

The confidence heuristic chooses the higher stated confidence in each displayed order; equal confidence and equal verdict keep that verdict, equal confidence with different verdicts coin-flips. Different chosen verdicts across orders also get expected coin credit. Trust-Opus and Trust-Sol retain the same split/unreadable rules. Human is an oracle assumption, unpriced, not measured human performance.

Strict sensitivity uses the identical primary lenient-selected disagreement set, so all methods compare the same items. Strict full-rule agreement additionally requires strict consistent agreement; failed strict gates count unreadable, without new tie-breaker calls. It is not a separately recollected strict-route cascade. Missing original strong replies already routed to humans remain reviews.

Intervals: 5000 seeded item-cluster percentile bootstrap draws, including expected fractional scores, same-item paired differences. Reply-score intervals average the two orders within each item before bootstrap. Wilson bounds are used for the observed agreed-both-wrong proportion (upper endpoint of a two-sided95% Wilson interval). Selection and optional stopping make intervals descriptive for this realized generator sample. n<10 family/tag groups are flagged sparse. Reasons-feature associations are descriptive; randomized labels do not make reason length/confidence causal.

Before any new strong test judgment, data/interval_amendment.json corrects diagnostic interval implementation: when eligible/readable order counts differ across items, each bootstrap draw resamples item clusters and divides the sum of successes by the sum of eligible order counts, matching the reported order-weighted rate. Readable-only accuracy intervals are also included (readable_ci_low/high). Primary accuracies, case scoring, inputs, model calls and stopping are unchanged. The running collector retains its initial intermediate analysis functions; final offline notebook execution uses the corrected functions and replaces those intermediate exports. This has no effect on collection or its stopping rule. The prior analysis and freeze are preserved in data/freeze_history/.
''')
if (data/'stopping_history.json').exists():parts.append('\nStopping history:\n\n'+table(pd.DataFrame(load('stopping_history.json'))))
parts.append('## 2. Exact counts\n')
for name in ['route_summary','construction_summary','call_counts','coverage_by_model_condition','reply_summary','unreadable_summary','spend_by_model','cost_completeness']:
    p=data/(name+'.csv')
    if p.exists():parts.append('\n`data/'+name+'.csv`:\n\n'+table(pd.read_csv(p)))
parts.append('''
Every results row contains wrong, unreadable, splits and unresolved separately where relevant. Per-order wrong/unreadable types are data/reply_summary.csv and data/unreadable_summary.csv. Item-level method results are data/tie_breakers.csv; full cascades are data/full_rules.csv. Actual invocations, including probes, development, writers and retries, are in data/usage_ledger.csv. Logical calls are not invocation attempts. Imported baseline economic costs remain in full-rule cost columns but do not consume this notebook's USD5 cap.

data/call_counts.csv distinguishes logical requests, invocation attempts, reused requests and local attempts by cohort/condition/judge. data/coverage_by_model_condition.csv gives items with at least one readable order and with both readable orders, alongside readable-order reply counts. data/cost_completeness.csv flags missing CLI usage/prices, Muse proxy-only prices and missing returned OpenRouter cost across all cached attempts belonging to the selected logical requests, including inherited retries. Cost subtotals use0 for missing prices, which is not a verified zero charge; interrupted unknown costs additionally require the ledger/reservation files.

data/construction_summary.csv counts error_source (natural versus mutation), better-answer construction and traps by cohort/family. data/item_construction.csv connects each count to stable IDs, writer, worse construction, failed hidden-test count or word-count delta. These describe the realized generated inputs; do not assume original and new construction shares are identical merely because the generator and writer pins are unchanged.
''')
parts.append('## 3. Headline numbers and column provenance\n')
for name,query,columns in [
    ('tie_breakers',"report_cohort=='all' and reader=='lenient' and unreadable_policy=='failure'",['method','n','accuracy','ci_low','ci_high','wrong','unreadable','splits','unresolved','readable_n','readable_accuracy']),
    ('tie_breakers',"report_cohort=='all' and reader=='lenient' and unreadable_policy=='coin'",['method','n','accuracy','ci_low','ci_high','unreadable']),
    ('full_rules',"report_cohort=='all' and reader=='lenient' and unreadable_policy=='failure'",['method','n','accuracy','ci_low','ci_high','human_reviews','logical_calls','model_cost_usd','cli_estimated_list_usd']),
    ('paired_comparisons',"cohort=='all' and reader=='lenient' and unreadable_policy=='failure'",['method_a','method_b','n','accuracy_difference','ci_low','ci_high','a_better','b_better','equal']),
    ('reasons_alignment_summary',None,None)]:
    p=data/(name+'.csv')
    if p.exists():
        f=pd.read_csv(p);f=f.query(query) if query else f
        parts.append('\n`data/'+name+'.csv`'+(' filter `'+query+'`' if query else '')+':\n\n'+table(f[columns] if columns else f))
parts.append('''
Original/new/all cohorts: filter report_cohort in tie_breakers.csv/full_rules.csv/family_results.csv/trap_results.csv. Per-family composition and error floor are route_summary.csv columns items, disagreements, disagreement_family_share, agreed_both_wrong and agreed_error_95_upper. The last column is a proportion among agreed items, not all items. The full-rule unavoidable error floor is agreed_both_wrong/total_items; zero observed does not prove zero risk. Strict sensitivity is reader=strict in the same tables. Paired intervals crossing zero do not establish improvement. Ceilings/floors are marked by ceiling/floor boolean columns.
''')
parts.append('## 4. Candidate worked examples\n')
if (data/'worked_examples.json').exists():
    examples=load('worked_examples.json')
    for e in examples:
        item=e['item'];parts.append('- '+e['category']+': `'+e['item_id']+'`'+(' model '+e['model'] if 'model' in e else '')+', eligible_n='+str(e['eligible_n'])+', gold='+item['better']+'. The complete input, exact candidate checks, prompts and raw replies are in data/worked_examples.json.\n')
    absent=[x for x in ['reasons_helped','reasons_harmed','both_agreed_wrong'] if not any(e['category']==x for e in examples)]
    parts.append('Absent categories (do not invent an example): '+', '.join(absent)+'.\n')
if (data/'unreadable_examples.json').exists():
    for e in load('unreadable_examples.json'):
        parts.append('- Unreadable `'+e['item_id']+'` / '+e['judge']+' / '+e['condition']+' / '+e['order']+': '+e['lenient_unreadable_type']+' / '+e['diagnostic_subtype']+'. Key `'+e['raw_reply_cache_key']+'`. Raw excerpt: '+repr((e['raw_text'] or e['diagnostics'])[:650])+'.\n')
parts.append('''
Selection is deterministic: first stable-ID case satisfying each reasons-helped/harmed criterion, first disagreeing item per observed family, first ordinary correct agreement, and first agreed-wrong if any. Categories may repeat an item. eligible_n counts the exact criterion, not all such semantic behaviors. Figures include candidate differences and exact checker evidence. A reasons-harmed observation does not prove a particular argument caused the failure; inspect both raw strong arguments and the weak explanation before describing persuasion.

Prefer figures/readable_case_<item_id>.png for README-width panels: they show the checker evidence, the first answer difference in context and canonical verdicts in both orders, using larger type. The supplementary exporter was exercised offline on the24-item saved development run and a panel inspected visually. Some reasons-harmed selections can be a delivery failure rather than a readable wrong answer; use the raw reply and item_outcomes.wrong/unreadable columns to choose the persuasive-wrong example correctly.

data/code_case_audits.json gives the first already-failing hidden test for each selected code case: original input, expected value, actual candidate value_repr/type and input-mutation flag. It replays the existing test prefix in the frozen checker's restricted namespace, preserving any candidate state across preceding tests. These are diagnostics of existing scored tests, with no new test inputs and no label changes. Use them to explain a code boundary case without asking a reader to execute or understand Python.

The supplementary exporter also adds a first agreed-and-correct example for each family, preferring the original cohort when available. Their category is agreement_control_<family>, with selection-pool counts. These controls show what passes directly through the agreement gate, including families with no observed disagreements; no weak-model verdict is invented for those uncalled branches.

## 5. Exact prompts

data/prompt_templates.json holds baseline, reasons, revision, writer and writer-copy text. Each exact instantiated request, all settings and raw reply are stored at data/cache_requests.jsonl (new calls) or data/cache_from_33.jsonl.gz (reused baselines), fields request.prompt, request.payload and response. Join all exported judgments using raw_reply_cache_key. Decisions uses the source33 state template plus both full candidate texts as choice criteria, unchanged. No labels, hidden tests or writer metadata enter judge prompts. Worked examples embed actual prompt strings directly.

## 6. Models table
''')
models=load('models.json')
cols=['name','pinned_version','provider','access','size','precision','license','hugging_face_id','settings','date','date_basis','date_source','why_included','pin_limitation']
parts.append(table(pd.DataFrame(models)[cols]))
parts.append('''
These pins/providers and cutoff/release metadata are inherited from notebook33, with links recorded in each row. Requested CLI IDs are version pins without independently verified immutability; Gemma catalog canonical slugs have no date. OpenRouter catalog snapshot is data/catalog_snapshot.json, refreshed during the capability smoke. Granite provider coreweave/bf16; DeepSeek deepinfra/fp8; writer providers parasail/bf16 and deepinfra/fp8. All CLI effort medium. Granite reasoning none, DeepSeek low, temp0, JSON object mode, initial1600 output budget with prescribed length retries up to6400; writer temperatures and budgets unchanged from33. Muse Full list price remains unavailable: chars/4 at4/20 dollars per million is explicitly a proxy, not a verified bill.

## 7. Chronological engineering log and freezes

Read AGENTS.md and notebook33 notebook/HANDOFF, source generator/readers/evaluation/transport, plus reference helper cells in notebooks11,18,31,17. Verified source freeze before any model work. Capability probes called every one of the9 judges and2 writers once, with retry attempts separately cached. Then reused original level10 development items and strong replies, collected the new contexts, exercised scoring/tables/figures. No generator difficulty adjustments were made. data/engineering_checks.json independently confirms the original routing, exact request reuse, parser format sensitivity, quota detection and offline cache miss guard.

Machine chronological log is data/run_log.jsonl; every invocation start/return is data/attempt_lifecycle.jsonl. Request-level attempts and diagnostics are data/usage_ledger.csv. Frozen preregistration is data/analysis_plan.json and data/freeze_record.json; item-batch freezes have their own timestamps and hashes before their strong calls. Freeze hashes normalize CRLF to LF. data/source_manifest.json additionally records the immutable source copies (gzip uses raw bytes). Study artifacts and their hashes are in data/artifact_manifest.json when final QA has completed.
''')
if (data/'freeze_record.json').exists():parts.append('\nDesign freeze:\n\n```json\n'+json.dumps(load('freeze_record.json'),indent=2)+'\n```\n')
if (data/'run_log.jsonl').exists():
    logs=[json.loads(s) for s in (data/'run_log.jsonl').read_text(encoding='utf-8').splitlines()]
    for e in logs:
        if e['event'] in ('retry','quota_limit_stop'):
            parts.append('- '+e['at']+' '+e['event']+' '+str(e.get('purpose',''))+' '+str(e.get('reason',e.get('message','')))[:400]+'\n')
parts.append('''
Transport amendments relative to33: concurrency2Claude/2Codex/1Muse/3perOpenRouter model; imported cost excluded from the new cap; outstanding interrupted requests retain reservations; reservations use conservative byte-count input plus4096 overhead and verified pinned-provider prices; provider policy blocks never retried. Before any new strong test calls, a controlled restart corrected inflated generic price floors. See data/reservation_amendment.json; original freeze and transport are preserved in data/freeze_history/. Historical over-reservations were retained, not reduced. Then the collector process was observed absent with no exit diagnostic after three HTTP requests had exceeded180s without returning. data/deadline_amendment.json records a hard180s subprocess deadline added on resume; seven unreturned requests across both interruptions are conservatively reserved at USD0.02394752 in data/interrupted_attempts.json. Their charges and outputs are unknown, and these invocation attempts are additional to returned-attempt counts in usage_ledger.csv. The cause of the unexplained exit is not established. No generated item, prompt, model setting, scoring rule or generator parameter changed. Quota/usage/credit phrases are inspected in all diagnostic streams, never final-cached, and halt the collector with resumable handoff. No HTTP OpenAI/Anthropic SDK calls. Temp CLI workdirs are empty with tools disabled. Logs live in ignored data/tmp/. Caller env removes FORCE_COLOR and sets NO_COLOR=1.

## 8. Spend and wall time
''')
if (data/'usage_ledger.csv').exists():
    ledger=pd.read_csv(data/'usage_ledger.csv')
    parts.append('Actual local returned attempts: '+str(len(ledger))+'. OpenRouter reported dollars: '+str(ledger.openrouter_usd.sum())+'. Unpriced reservations: '+str(ledger.unpriced_reservation_usd.sum())+'. CLI estimated list/proxy dollars: '+str(ledger.cli_estimated_list_usd.sum())+'.\n')
    start=pd.to_datetime(ledger.started_at,utc=True).min();end=pd.to_datetime(ledger.completed_at,utc=True).max()
    parts.append('Local first invocation '+str(start)+' through last return '+str(end)+'; wall interval '+str((end-start).total_seconds())+' seconds, including implementation gaps. Sum latency overlaps concurrent work.\n')
parts.append('''
## 9. Replay and live

Run in this notebook folder. Install requirements-replay.txt if needed. Default is offline full replay; network requests are blocked and an uncached model request fails closed. New calls must be zero. Notebook embeds every helper/generator/reader/analysis function; it does not import source from another notebook. data/run34.py is the resumable command-line driver using the identical local source snapshots; data/build34.py rebuilds notebook cells and clears outputs, so do not rebuild after final executed replay unless re-executing.

```powershell
Remove-Item Env:NB_LIVE -ErrorAction SilentlyContinue
Remove-Item Env:NB_STAGE -ErrorAction SilentlyContinue
$env:NB_PROFILE='full'
$env:NO_COLOR='1'
Remove-Item Env:FORCE_COLOR -ErrorAction SilentlyContinue
python -X utf8 -E -P -m nbconvert --to notebook --execute --inplace 34_weak_tiebreakers.ipynb --ExecutePreprocessor.timeout=-1
```

Live full: set NB_LIVE=1, NB_PROFILE=full; clear NB_STAGE; run python -X utf8 -E -P data/run34.py (background hidden process with stdout/stderr in data/tmp). Notebook live uses the same knobs. Small smoke: NB_PROFILE=smoke; original one item per family, new contextual calls only as needed; smoke analysis outputs go under data/smoke and figures/smoke. Development: NB_STAGE=development, NB_PROFILE=smoke, NB_LIVE=1; uses the source33 development items. Run data/probe34.py to resume the tiny capability calls. All entrypoints preserve request caches. Never change frozen batch files or source copies to rerun.

## 10. Raw observations and remaining editorial work

Consult data/unreadable_examples.json and data/worked_examples.json before writing any claim. The source33 strict/lenient readers are unchanged. Haiku provider AUP blocks are transport_error/provider_safety_block, not wrong; code fences may fail strict and pass lenient; malformed reasons and truncated prefix recovery retain their fixed rules. Read every new unreadable group. Do not silently credit a semantically correct winner if it failed the fixed schema.

The reasons condition includes confidences as part of the strong judgments; any change versus alone mixes verdict/reason/confidence information. It does not isolate reasons alone. Feature-following rates use only same-order different-verdict arguments and readable weak replies; rows with identical strong verdicts are excluded from that diagnostic even when the item was selected because of an order split. No agreed-wrong example is available if the final count is0; state the count and bound, not a fabricated case. Domain ambiguity and mutation-heavy construction in notebook33 remain limitations.

Original test-code-002 is domain-sensitive. Muse's AB reply chooses B with confidence60, pointing to A's boolean/log-string handling. The two programs differ there, but all64 hidden inputs for this price/discount main rule are nonnegative integer pairs: A passes64/64 and B63/64, with B mishandling audit state after an omitted row. The generic audit preface mentions other row types. If this case is used, disclose the finite test domain and the broader-reading ambiguity; do not call it an uncomplicated reasoning failure, change its frozen label or add/exclude tests after seeing verdicts. Its existing failing input and outputs can be inspected in code_case_audits.json when selected.

Development inspection:24 items,4 disagreements,48 context judgments. All9 lenient-unreadable development replies came from Haiku:8 AUP/provider [bio] transport blocks (4 alone,4 reasons) and1 reasons reply that said it would not reconstruct content cut off by a safety classifier. The unchanged reader calls that last reply no_parseable_json rather than refusal because it does not match the frozen refusal regex; describe its semantics separately. Development replay made0 calls. Expected-coin and human-oracle baselines can have degenerate bootstrap intervals because their scores are deterministic expectations/assumptions, not observed random flips or measured human judgments.

Claude must finish README.md, every notebook markdown cell, workflow/call/sequence diagrams, PROTOCOL.md, root and judge-index README rows and git/PR work. Further-reading candidates: Khan et al.2024 canonical arXiv link opened on2026-10-30 in data/sources_checked.json; open any additional links before committing. Keep narrative numbers tied to the CSV filters above. Delete this handoff before commit.

Refresh data/artifact_manifest.json after reader prose/markdown edits and new README/PROTOCOL files with python -X utf8 -E -P data/manifest34.py. It normalizes CRLF to LF in text and hashes binary gzip/PNG as bytes. Do not rewrite model/input/prompt freezes for editorial changes. Markdown-only edits do not need another model collection or notebook execution under AGENTS.md.
''')
if complete:parts.append('\nReplay validation:\n\n```json\n'+json.dumps(load('replay_validation.json'),indent=2)+'\n```\n')
if (data/'quota_stop.json').exists():
    stop=load('quota_stop.json')
    cached=[]
    for path in [data/'cache_requests.jsonl.gz',data/'cache_requests.jsonl']:
        if not path.exists():continue
        with (gzip.open(path,'rt',encoding='utf-8') if path.suffix=='.gz' else path.open(encoding='utf-8')) as stream:
            cached.extend(json.loads(line) for line in stream if line.strip())
    model_counts=Counter((r['request']['model'],r['request']['purpose'].split(':')[0]) for r in cached)
    status='# Status: stopped at a usage or quota limit\n\n'+json.dumps(stop,indent=2)+'\n\n'
    status+='Completed new item files: '+str(len(list((data/'items').glob('*.json'))))+'. Locally cached returned attempts: '+str(len(cached))+'. Imported baseline/development cache has4512 attempt records from33.\n\n'
    status+='Local cached attempts by model/stage: '+json.dumps({str(k):v for k,v in sorted(model_counts.items())})+'.\n\n'
    status+='The limit reply is in data/nonfinal_attempts.jsonl, never final-cached. Full collection and final executed replay remain incomplete. Resume from caches only after the usage window clears; preserve then archive data/quota_stop.json as run history before final finish34.py. No automatic limit retries were made.\n\n'
    parts.insert(0,status)
(root/'HANDOFF.md').write_text('\n'.join(parts),encoding='utf-8')
print('Handoff written; final replay complete:',complete)
