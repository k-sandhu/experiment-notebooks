"""Owner-requested open-weight comparison (2026-11-05): the three highest-ranked open-weight models on OpenRouter.

Ranking: Artificial Analysis Progress Index v1, large open-weight class, top entries that OpenRouter serves with
published weights and a context window that holds the ~300,000-token packet. Each model's own lab is the pinned
provider, with no fallback.

The packet is the frozen digits packet with one change: its return section asks for named tensors with one-based
numbered entries from the first request (the owner's format), plus an output-budget note. Safeguards:
  * reasoning effort medium (MiMo exposes only on/off), 131,072-token output allowance for all three;
  * a reply with reasoning but no entries gets one follow-up that hands its emitted reasoning back, with low effort;
  * a reply cut off mid-way keeps every complete entry and the follow-up asks only for missing index ranges;
  * a reply that is not the JSON contract gets format-only feedback;
  * transient provider errors (timeouts, 408/429/5xx) are retried and do not count as content calls;
  * one surrounding Markdown code fence is removed before parsing, never a value.
At most three content calls per model. No scores, labels or other models' weights are ever supplied, and the tester
never pads, truncates, fills or repairs a value; conflicting repeats stop assembly.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
import copy
import json
import time
import experiment as e
from analysis import indexed_entries, missing_ranges, strip_fence, COUNTS

OPEN = {
    'deepseek': {'backend': 'openrouter', 'model': 'deepseek/deepseek-v4.1-flash-1017',
                 'canonical': 'deepseek/deepseek-v4.1-flash-20261017', 'provider': 'deepseek', 'effort': 'medium'},
    'glm': {'backend': 'openrouter', 'model': 'z-ai/glm-5.3', 'canonical': 'z-ai/glm-5.3-20260816',
            'provider': 'z-ai', 'effort': 'medium'},
    'mimo': {'backend': 'openrouter', 'model': 'xiaomi/mimo-v2.6-pro', 'canonical': 'xiaomi/mimo-v2.6-pro-20260921',
             'provider': 'xiaomi', 'effort': None},
}
MAX_CONTENT_CALLS = 3
TRANSIENT_RETRIES = 2
MAX_OUTPUT_TOKENS = 131072
RUN = 'open-weight-numbered-2026-11-05'

RETURN_FLAT = '''RETURN ONLY {"weights":[6570 explicit finite JSON numbers]}.
Flatten tensors in the following order; flatten each tensor in C/row-major order.
W1 [64,64]: offsets 0..4095, then b1 [64]: 4096..4159;
W2 [32,64]: 4160..6207, then b2 [32]: 6208..6239;
W3 [10,32]: 6240..6559, then b3 [10]: 6560..6569.
Rows of a weight matrix are output neurons; columns are input neurons.
Return ALL 6570 numbers, including zeros. No prose, Markdown, code, formulas, ellipses,
repetition notation, omitted entries, extra keys, or special NaN/Infinity values.
There is one submission and no intermediate feedback. Maximize held-out accuracy.'''
RETURN_NUMBERED = '''RETURN ONLY one JSON object with six named tensors, each an object of numbered entries:
{"W1":{"1":v,"2":v,...,"4096":v},"b1":{"1":v,...,"64":v},"W2":{"1":v,...,"2048":v},
 "b2":{"1":v,...,"32":v},"W3":{"1":v,...,"320":v},"b3":{"1":v,...,"10":v}}
Keys are quoted one-based index strings. The ellipses only explain the format: write EVERY
entry explicitly, including zeros. Entry i of a tensor is its C/row-major position plus one;
for W1 [64,64], entry i is row (i-1)//64 and column (i-1)%64. Rows of a weight matrix are
output neurons; columns are input neurons. W1 [64,64]: 4096 entries; b1 [64]: 64;
W2 [32,64]: 2048; b2 [32]: 32; W3 [10,32]: 320; b3 [10]: 10. Total 6570.
After the last index of a tensor, close it and start the next. After b3 "10", close the JSON
and STOP. Never write an index outside its tensor's range. No prose, Markdown, code fences,
formulas, ellipses, repetition notation, extra keys, or special NaN/Infinity values.
OUTPUT BUDGET: writing all 6570 entries takes roughly 45,000 output tokens. Keep your private
reasoning short enough to leave room for them; you do not need to reason about every number.
If your reply is cut off, the tester keeps every complete entry and asks you to CONTINUE with
only the missing index ranges. There is no feedback on accuracy. Maximize held-out accuracy.'''


def numbered_prompt():
    prompt = (e.DATA / 'prompt.txt').read_text(encoding='utf-8')
    assert e.sha(prompt) == json.loads((e.DATA / 'manifest.json').read_text(encoding='utf-8'))['prompt_sha256']
    assert prompt.count(RETURN_FLAT) == 1
    prompt = prompt.replace(RETURN_FLAT, RETURN_NUMBERED)
    old_end = 'END SAMPLE. Return only the complete JSON weights object.'
    assert prompt.count(old_end) == 1
    return prompt.replace(old_end, 'END SAMPLE. Return only the complete JSON object of numbered tensor entries.')


def reasoning_setting(cfg, low):
    if cfg['effort'] is None:
        return {'enabled': not low, 'exclude': False}
    return {'effort': 'low' if low else cfg['effort'], 'exclude': False}


def transient(record):
    err = record.get('error') or {}
    if record.get('answer') or record.get('reasoning'):
        return False
    return isinstance(err, dict) and (err.get('status') in [408, 429, 500, 502, 503, 504]
                                      or err.get('code') in [408, 429, 500, 502, 503, 504]
                                      or err.get('kind') == 'exception')


def call(key, out, request):
    try:
        return e.run_openrouter(key, out, request)
    except Exception as exc:  # timeouts and dropped connections are transport failures, not content
        return {'answer': '', 'reasoning': '', 'usage': {}, 'completed': False, 'tool_events': [], 'events': [],
                'error': {'kind': 'exception', 'type': type(exc).__name__, 'message': str(exc)},
                'started_utc': e.utc(), 'finished_utc': e.utc(), 'wall_seconds': 0.0, 'cost_usd': None}


def collect(key):
    cfg = OPEN[key]
    e.MODELS[key] = cfg
    root = e.DATA / 'open_models' / key
    root.mkdir(parents=True, exist_ok=True)
    meta = e.requests.get('https://openrouter.ai/api/v1/models', timeout=30).json()['data']
    model = next(m for m in meta if m['id'] == cfg['model'])
    assert model['canonical_slug'] == cfg['canonical'] and model.get('hugging_face_id'), model.get('canonical_slug')
    e.dump(root / 'model_metadata.json', model)
    prompt = numbered_prompt()
    messages = [{'role': 'user', 'content': prompt}]
    merged = {name: {} for name in COUNTS}
    records, issues, content_calls, n = [], [], 0, 0
    low = False
    while content_calls < MAX_CONTENT_CALLS:
        for attempt in range(TRANSIENT_RETRIES + 1):
            n += 1
            out = root / f'call-{n:02d}'
            out.mkdir(exist_ok=True)
            body = {'model': cfg['model'], 'messages': copy.deepcopy(messages), 'max_tokens': MAX_OUTPUT_TOKENS,
                    'reasoning': reasoning_setting(cfg, low),
                    'provider': {'only': [cfg['provider']], 'allow_fallbacks': False},
                    'stream': True, 'stream_options': {'include_usage': True}, 'plugins': []}
            request = {'protocol': 'digits-open-numbered-v1', 'run': RUN, 'config': cfg, 'body': body,
                       'content_call': content_calls + 1, 'attempt': attempt + 1, 'tools_enabled': [],
                       'expected_tensor_counts': COUNTS, 'task_feedback': False}
            cache_key = e.sha(json.dumps(request, sort_keys=True))
            cache = out / 'response.json'
            if cache.exists():
                record = json.loads(cache.read_text(encoding='utf-8'))
                assert record['cache_key'] == cache_key
            else:
                assert not (out / 'started.json').exists(), 'Unresolved request; inspect logs instead of regenerating'
                e.dump(out / 'request.json', request)
                e.dump(out / 'started.json', {'started_utc': e.utc(), 'cache_key': cache_key})
                print(f'START {key} call {n} (content {content_calls + 1}, attempt {attempt + 1})', flush=True)
                record = call(key, out, request)
                record.update(cache_key=cache_key, request=request)
                e.dump(cache, record)
                e.trace_call(cache_key, cfg, request, record)
                print(f'END {key} call {n}: answer {len(record.get("answer", ""))} chars, reasoning '
                      f'{len(record.get("reasoning", ""))} chars, error {json.dumps(record.get("error"))[:200]}', flush=True)
            records.append(record)
            if not transient(record):
                break
            time.sleep(30 * (attempt + 1))
        else:
            break
        if (record.get('error') or {}).get('status') == 400:
            break  # a rejected request generated nothing; inspect it rather than spend content calls
        content_calls += 1
        answer = strip_fence(record.get('answer', ''))
        entries, issue = indexed_entries(answer)
        conflicts = []
        for name, values in entries.items():
            for index, value in values.items():
                if index in merged[name] and merged[name][index] != value:
                    conflicts.append([name, index])
                else:
                    merged[name][index] = value
        coverage = {'content_call': content_calls, 'calls': n, 'counts': {k: len(v) for k, v in merged.items()},
                    'total': sum(map(len, merged.values())), 'expected_total': e.N_PARAMS,
                    'missing_ranges': missing_ranges(merged), 'parse_issue': issue, 'conflicts': conflicts,
                    'finish': (record.get('error') or {}).get('finish_reason') or ('stop' if record.get('completed') else None)}
        e.dump(root / f'coverage-{content_calls:02d}.json', coverage)
        e.dump(root / 'coverage.json', coverage)
        if issue:
            issues.append(issue)
        if conflicts or record.get('tool_events'):
            break
        if not coverage['missing_ranges']:
            flat = [merged[name][i] for name, count in COUNTS.items() for i in range(1, count + 1)]
            answer_flat = json.dumps({'weights': flat}, separators=(',', ':'))
            assembled = {'answer': answer_flat, 'completed': True,
                         'tool_events': [t for r in records for t in r.get('tool_events', [])],
                         'usage': {'per_turn': [r.get('usage') for r in records]},
                         'cost_usd': sum(r.get('cost_usd') or 0 for r in records),
                         'started_utc': records[0]['started_utc'], 'finished_utc': records[-1]['finished_utc'],
                         'wall_seconds': sum(r['wall_seconds'] for r in records),
                         'reasoning': '\n'.join(r.get('reasoning', '') for r in records),
                         'request': {'protocol': 'digits-open-numbered-v1', 'config': cfg,
                                     'turn_cache_keys': [r['cache_key'] for r in records], 'expected_tensor_counts': COUNTS},
                         'assembly': 'One-based indices mapped to existing tensor layout, no value changes',
                         'source_coverage': coverage, 'parse_issues': issues}
            e.dump(root / 'assembled_response.json', assembled)
            (root / 'weights_output.json').write_text(answer_flat, encoding='utf-8')
            (root / 'reasoning.txt').write_text(assembled['reasoning'], encoding='utf-8')
            result = e.validate_and_score(key, assembled, out_override=root)
            print(json.dumps({'model': key, 'content_calls': content_calls, 'calls': n, 'coverage': coverage['total'],
                              'failure': result['format_failure'], 'test': result.get('test', {}).get('accuracy')}), flush=True)
            return
        # Follow-up: output coverage and format only. No accuracy, labels or parameter suggestions.
        if coverage['total'] == 0 and not record.get('answer') and record.get('reasoning'):
            messages.append({'role': 'assistant', 'content': 'Prior provider-emitted reasoning, with no final entries:\n'
                             + record['reasoning']})
            messages.append({'role': 'user', 'content': 'Your previous reply used its output allowance on reasoning and '
                             'emitted no numbered entries. Do not restart the analysis. Using the work above, now write '
                             'the complete JSON object of numbered tensor entries in the required format.'})
        elif coverage['total'] == 0:
            messages.append({'role': 'assistant', 'content': record.get('answer') or '[No final content was emitted.]'})
            messages.append({'role': 'user', 'content': 'Your previous reply was not the required JSON object. Return '
                             'ONLY the JSON object of numbered tensor entries, starting with {"W1":{"1":'})
        else:
            messages.append({'role': 'assistant', 'content': record.get('answer') or '[No final content was emitted.]'})
            messages.append({'role': 'user', 'content': 'CONTINUE the same indexed parameter output. Start with the first '
                             'missing index below. Return a NEW valid JSON object containing ONLY remaining indexed entries. '
                             'Do not redo completed entries. Do not produce prose or predictions. Missing tensor index '
                             'ranges: ' + json.dumps(coverage['missing_ranges'])})
        low = True
    last = records[-1] if records else {}
    if any(r.get('tool_events') for r in records) or (root / 'coverage.json').exists() and \
            json.loads((root / 'coverage.json').read_text(encoding='utf-8')).get('conflicts'):
        category, text = 'unreadable_format', 'Conflicting repeated entries or tool event; no repair'
    elif (last.get('error') or {}).get('status') == 400:
        category, text = 'request_rejected', 'Provider rejected the request before generation'
    elif records and all(transient(r) for r in records):
        category, text = 'provider_unavailable', 'Provider errors before any numerical output'
    else:
        category, text = 'missing_indexed_values', 'Entries still missing after the content-call cap'
    coverage = json.loads((root / 'coverage.json').read_text(encoding='utf-8')) if (root / 'coverage.json').exists() else None
    e.dump(root / 'results.json', {'model': cfg['model'], 'model_key': key, 'format_failure': text,
                                   'failure_category': category, 'coverage': coverage, 'tester_changed_weights': False,
                                   'cost_usd': sum(r.get('cost_usd') or 0 for r in records),
                                   'wall_seconds': sum(r.get('wall_seconds') or 0 for r in records)})
    print(json.dumps({'model': key, 'stopped': category, 'error': last.get('error')}, default=str)[:600], flush=True)


def compact(key):
    """Lossless storage compaction: gzip each call's stream log and replace the duplicate event list in
    response.json with a pointer plus finish reasons. Answer, reasoning, usage, error and cache key are unchanged."""
    import gzip
    for call_dir in sorted((e.DATA / 'open_models' / key).glob('call-*')):
        log = call_dir / 'events.jsonl'
        if log.exists():
            raw = log.read_bytes()
            with gzip.open(call_dir / 'events.jsonl.gz', 'wb', compresslevel=9) as f:
                f.write(raw)
            with gzip.open(call_dir / 'events.jsonl.gz', 'rb') as f:
                assert f.read() == raw
            log.unlink()
        path = call_dir / 'response.json'
        record = json.loads(path.read_text(encoding='utf-8'))
        if isinstance(record.get('events'), list):
            finishes = [c.get('finish_reason') for ev in record['events'] for c in ev.get('choices', []) if c.get('finish_reason')]
            record['events'] = {'stored_in': 'events.jsonl.gz', 'n_events': len(record['events']), 'finish_reasons': finishes}
            e.dump(path, record)


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--models', nargs='+', default=list(OPEN), choices=list(OPEN))
    p.add_argument('--compact', action='store_true', help='compress stored stream logs after collection')
    args = p.parse_args()
    if args.compact:
        for key in args.models:
            compact(key)
        raise SystemExit
    with ThreadPoolExecutor(max_workers=len(args.models)) as pool:
        tasks = {pool.submit(collect, key): key for key in args.models}
        for future in as_completed(tasks):
            try:
                future.result()
            except Exception as exc:
                print(json.dumps({'model': tasks[future], 'error': f'{type(exc).__name__}: {exc}'}), flush=True)
