import os
from pathlib import Path

os.environ['NB_LIVE'] = '1'
os.environ['NB_PROFILE'] = 'smoke'
os.chdir(Path(__file__).resolve().parents[1])
for name in ['setup34.py', 'transport34.py', 'from_33/reading_rules_v1.py']:
    exec(compile((Path('data') / name).read_text(encoding='utf-8'), name, 'exec'))

try:
    rows = []
    for name, spec in {**JUDGES, **WRITERS}.items():
        prompt = 'Choose the correct sum. A: 4. B: 5. Task: 2+2. Return JSON only: {"winner":"A","confidence":99,"reason":"Four is correct."}'
        extra = dict(choices={'A': '4', 'B': '5'}, state='Choose the correct sum for 2+2.') if spec['backend'] == 'decisions' else {}
        row = ask(spec, prompt, 'nb34:capability:' + name, budget=300, **extra)
        parsed = parse_judgment(row, False)
        rows.append(dict(name=name, key=row['key'], parsed=parsed, text=row['response']['text'][:700]))
        save(DATA / 'capabilities.json', rows)
        print(name, parsed, flush=True)
    catalog = requests.get('https://openrouter.ai/api/v1/models', timeout=60)
    catalog.raise_for_status()
    save(DATA / 'catalog_snapshot.json', catalog.json())
    for name, spec in {**JUDGES, **WRITERS}.items():
        if spec['backend'] == 'openrouter':
            assert any(x['canonical_slug'] == spec['model'] for x in catalog.json()['data'])
    print('PROBES COMPLETE', flush=True)
except CollectorQuotaStop:
    p = ROOT / 'HANDOFF.md'
    p.write_text('# Status: collection stopped at a usage or quota limit\n\n' +
                 json.dumps(load(DATA / 'quota_stop.json'), indent=2) +
                 '\n\nCached replies are in data/cache_requests.jsonl; imported baseline attempts are in data/cache_from_33.jsonl.gz. '
                 'The limit response is preserved only in data/nonfinal_attempts.jsonl. '
                 'Probe progress is in data/capabilities.json. Remaining probes and the full experiment are pending. '
                 'No limit outcome was cached as a final reply. Resume data/probe34.py first.\n', encoding='utf-8')
    raise
