"""Owner-requested numbered-entry workflow for Claude family replies that failed the flat JSON contract.

Same rules as indexed_recovery.py: the model resumes its own saved `claude -p` session, receives format-only
feedback (no scores, labels or other models' weights) and returns one-based numbered entries per tensor.
Continuations ask only for missing index ranges. At most three calls per model. The tester never pads,
truncates, fills or repairs a value; conflicting repeats stop assembly.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import re
import experiment as e
from analysis import indexed_entries, missing_ranges
from indexed_recovery import FORMAT, COUNTS
from claude_family import FAMILY, OUTPUT_TOKEN_CAP, BUDGET_USD

MAX_CALLS = 3


def first_feedback(result):
    if result['failure_category'] == 'wrong_weight_count':
        n = int(re.search(r'received (\d+)', result['format_failure']).group(1))
        return (f'Your prior flat JSON contained {n} values rather than 6570. Its extra or missing entries cannot be '
                'located reliably by the tester. Supply a NEW complete indexed parameter set, choosing every value '
                'yourself; do not assume the old flat vector is correct.')
    return ('The previous response emitted no complete final numerical weights. CONTINUE the task from your earlier '
            'work and now emit the indexed numerical answer.')


def session_of(record):
    return next(ev['session_id'] for ev in record['events'] if ev.get('type') == 'result')


def collect(key):
    base = e.DATA / 'claude_family' / key
    original = json.loads((base / 'response.json').read_text(encoding='utf-8'))
    first = json.loads((base / 'results.json').read_text(encoding='utf-8'))
    assert first['format_failure'] is not None, 'Only failed flat replies enter the numbered-entry workflow'
    root = e.DATA / 'indexed' / key
    root.mkdir(parents=True, exist_ok=True)
    merged = {name: {} for name in COUNTS}
    records = []
    previous = original
    prompt = FORMAT + '\n' + first_feedback(first)
    for turn in range(1, MAX_CALLS + 1):
        out = root / f'turn-{turn:02d}'
        out.mkdir(exist_ok=True)
        cmd = e.cli_command(key, out)
        cmd[cmd.index('--effort') + 1] = FAMILY[key]['effort']
        cmd[cmd.index('--max-budget-usd') + 1] = BUDGET_USD
        cmd += ['--resume', session_of(previous)]
        request = {'protocol': 'digits-indexed-claude-v1', 'config': FAMILY[key], 'prompt': prompt, 'command': cmd,
                   'output_token_cap': OUTPUT_TOKEN_CAP, 'schema': None, 'tools_enabled': [], 'turn': turn,
                   'resume_of': previous['cache_key'], 'expected_tensor_counts': COUNTS, 'task_feedback': False}
        cache_key = e.sha(json.dumps(request, sort_keys=True))
        cache = out / 'response.json'
        if cache.exists():
            record = json.loads(cache.read_text(encoding='utf-8'))
            assert record['cache_key'] == cache_key
        else:
            assert not (out / 'started.json').exists(), 'Unresolved indexed request; do not regenerate'
            e.dump(out / 'request.json', request)
            e.dump(out / 'started.json', {'started_utc': e.utc(), 'cache_key': cache_key})
            print(f'INDEXED START {key} {turn}', flush=True)
            record = e.run_cli(key, out, request)
            record.update(cache_key=cache_key, request=request)
            e.dump(cache, record)
            (out / 'weights_output.json').write_text(record.get('answer', ''), encoding='utf-8')
            (out / 'reasoning.txt').write_text(record.get('reasoning', ''), encoding='utf-8')
            e.trace_call(cache_key, FAMILY[key], request, record)
        records.append(record)
        previous = record
        entries, issue = indexed_entries(record.get('answer', ''))
        conflicts = []
        for name, values in entries.items():
            for index, value in values.items():
                if index in merged[name] and merged[name][index] != value:
                    conflicts.append([name, index])
                else:
                    merged[name][index] = value
        coverage = {'turn': turn, 'counts': {k: len(v) for k, v in merged.items()},
                    'total': sum(map(len, merged.values())), 'expected_total': e.N_PARAMS,
                    'missing_ranges': missing_ranges(merged), 'parse_issue': issue, 'conflicts': conflicts}
        e.dump(out / 'coverage.json', coverage)
        e.dump(root / 'coverage.json', coverage)
        if conflicts or (issue and not issue.get('partial')) or record.get('tool_events'):
            declined = issue and issue.get('kind') == 'not_json_object' and '{' not in record.get('answer', '')
            # A prose reply with no JSON at all is a decline, not a parsing error, and receives no continuation.
            e.dump(root / 'results.json', {'model': FAMILY[key]['model'], 'model_key': key,
                                           'format_failure': 'Prose reply declining to write weights; no JSON object' if declined
                                           else 'Indexed structural error, conflict or tool event; no repair',
                                           'failure_category': 'declined' if declined else 'unreadable_format', 'coverage': coverage,
                                           'tester_changed_weights': False, 'usage': record.get('usage'),
                                           'cost_usd': record.get('cost_usd'), 'wall_seconds': record.get('wall_seconds')})
            print(json.dumps({'indexed_model': key, 'turn': turn, 'stopped': coverage}), flush=True)
            return
        if not coverage['missing_ranges']:
            flat = [merged[name][i] for name, count in COUNTS.items() for i in range(1, count + 1)]
            answer = json.dumps({'weights': flat}, separators=(',', ':'))
            assembled = {'answer': answer, 'completed': True,
                         'tool_events': [t for r in records for t in r.get('tool_events', [])],
                         'usage': {'per_turn': [r.get('usage') for r in records]},
                         'cost_usd': sum(r.get('cost_usd') or 0 for r in records) if all(r.get('cost_usd') is not None for r in records) else None,
                         'started_utc': records[0]['started_utc'], 'finished_utc': records[-1]['finished_utc'],
                         'wall_seconds': sum(r['wall_seconds'] for r in records),
                         'reasoning': '\n'.join(r.get('reasoning', '') for r in records),
                         'request': {'protocol': 'digits-indexed-claude-v1', 'config': FAMILY[key],
                                     'turn_cache_keys': [r['cache_key'] for r in records], 'expected_tensor_counts': COUNTS},
                         'assembly': 'One-based indices mapped to existing tensor layout, no value changes',
                         'source_coverage': coverage}
            e.dump(root / 'assembled_response.json', assembled)
            (root / 'weights_output.json').write_text(answer, encoding='utf-8')
            (root / 'reasoning.txt').write_text(assembled['reasoning'], encoding='utf-8')
            result = e.validate_and_score(key, assembled, out_override=root)
            print(json.dumps({'indexed_model': key, 'turns': turn, 'coverage': coverage['total'],
                              'failure': result['format_failure'], 'test': result.get('test', {}).get('accuracy')}), flush=True)
            return
        prompt = ('CONTINUE the same indexed parameter output. Start with the first missing index below. Return a NEW valid '
                  'JSON object containing ONLY remaining indexed entries. Do not redo completed entries. Do not produce '
                  'prose or predictions. Missing tensor index ranges: ' + json.dumps(coverage['missing_ranges']))
    e.dump(root / 'results.json', {'model': FAMILY[key]['model'], 'model_key': key,
                                   'format_failure': 'Incomplete indexed coverage after continuation cap',
                                   'failure_category': 'missing_indexed_values', 'coverage': coverage,
                                   'tester_changed_weights': False})


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--models', nargs='+', required=True, choices=list(FAMILY))
    args = p.parse_args()
    with ThreadPoolExecutor(max_workers=len(args.models)) as pool:
        tasks = {pool.submit(collect, key): key for key in args.models}
        for future in as_completed(tasks):
            try:
                future.result()
            except Exception as exc:
                print(json.dumps({'model': tasks[future], 'error': f'{type(exc).__name__}: {exc}'}), flush=True)
