"""Copy the recorded runs needed by the explainer from data.json into a compact JS object (no edits to values)."""
import json, sys
src = sys.argv[1]
d = json.load(open(src, encoding='utf-8'))
runs = {r['level']: r for r in d['runs']}
out = {'runs': {}, 'comparison': []}
for lv in ['L0_single_agent', 'L1_sync_handoff', 'L2_async_spawn', 'L3_progress_and_redirect']:
    r = runs[lv]
    out['runs'][lv] = {
        'wall_s': r['wall_s'], 'main_blocked_s': r['main_blocked_s_from_spans'], 'calls': r['calls'], 'correct': r['correct'],
        'spans': [[s['agent'], s['kind'], s['label'], s['start'], s['end']] for s in r['spans']],
        'events': [[e['t'], e['kind'], e['from'], e['to']] for e in r['events']],
    }
for c in d['comparison']:
    out['comparison'].append({'level': c['level'], 'wall_s': c['wall s'], 'blocked_s': c['main blocked s'],
                              'blocked_pct': c['main blocked %'], 'llm_calls': c['LLM calls'], 'correct': c['correct']})
print('const DATA = ' + json.dumps(out, separators=(',', ':')) + ';')
