"""Audit saved v4 sources, independent keys, request identities and observed calls."""
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path
from datetime import datetime, timezone
from high_fixtures import high_validate_answer

base = Path(__file__).parent
root = base.parent / 'experiment_notebooks/notebooks/23-synthetic-data-curation'
data = root / 'data'
preflight = data / 'high_v4/preflight'
read = lambda p: json.loads(p.read_text(encoding='utf-8'))
canonical = lambda v: json.dumps(v, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
sha = lambda v: hashlib.sha256(v).hexdigest()
manifest = read(preflight / 'manifest.json')
sql = {r['case_id']: r for r in read(preflight / 'independent_sql_audit.json')['cases']}
fraction = {r['case_id']: r for level in read(preflight / 'independent_fraction_audit.json')['levels'] for r in level['cases']}
cases = {}
for item in manifest['levels']:
    packed = (preflight / item['file']).read_bytes()
    assert sha(packed) == item['compressed_sha256']
    raw = gzip.decompress(packed)
    assert sha(raw) == item['uncompressed_sha256']
    block = [json.loads(s) for s in raw.decode().splitlines()]
    assert len(block) == item['n_cases']
    for c in block:
        cid = c['case_id']; assert cid not in cases
        assert sha(c['document'].encode()) == sql[cid]['document_sha256'] == fraction[cid]['document_sha256']
        assert c['gold'] == sql[cid]['answer_from_text'] == fraction[cid]['answer_from_rendered_text']
        assert fraction[cid]['evidence_matches_stored_key']
        cases[cid] = c
assert len(cases) == len(sql) == len(fraction) == 1056
potential = data / 'high_v4_service_attempt/pilot/potential_cases.jsonl'
pilots = [json.loads(s) for s in potential.read_text().splitlines()]
assert len(pilots) == 32
assert not set(cases) & {c['case_id'] for c in pilots}
cases.update({c['case_id']: c for c in pilots})
counts, usage, entries = Counter(), Counter(), []
roots = ('high_v4_service_attempt', 'high_v4_service_serial_attempt', 'high_v4')
for name in roots:
    for path in sorted((data / name).rglob('cache/*.json')):
        record = read(path); request = record['request']
        assert sha(canonical(request).encode()) == record['key']
        assert len(record['attempts']) == 1
        assert request['model'] == 'gpt-6.1-sol' and request['reasoning_effort'] == 'high'
        assert 'model_reasoning_effort="high"' in request['cli_options']
        assert len(request['case_inputs']) == 1
        for item in request['case_inputs']:
            assert set(item) == {'case_id', 'task_instructions', 'documents'}
            assert item['documents'] == cases[item['case_id']]['document']
            assert item['task_instructions'] == manifest['task_instructions']
        a = record['attempts'][0]
        if a.get('pending'):
            outcome = 'interrupted_pending'
        elif a.get('error'):
            outcome = 'terminal_service_error'
        else:
            result = a['parsed']['results'][0]
            assert high_validate_answer(cases[result['case_id']], result)['accepted']
            assert any(e.get('type') == 'turn.completed' for e in a['events'])
            outcome = 'accepted_response'
        counts[outcome] += 1
        counts['request_records'] += 1
        counts['requests_with_usage'] += bool(a.get('token_usage'))
        usage.update(a.get('token_usage', {}))
        entries.append({'run': name, 'cache_file': path.relative_to(root).as_posix(), 'key': record['key'],
            'case_id': request['expected_case_ids'][0], 'outcome': outcome,
            'reasoning_effort': request['reasoning_effort'], 'protocol': request['protocol'],
            'started_at': a['started_at'], 'error': a.get('error')})
report = {'audited_at_utc': datetime.now(timezone.utc).isoformat(), 'passed': True,
    'n_preflight_main_cases': 1056, 'n_pilot_cases': 32, 'unique_source_cases': len(cases),
    'independent_source_answers_and_evidence_agree': True, 'counts': dict(counts),
    'observed_usage': dict(usage), 'usage_incomplete': counts['requests_with_usage'] != counts['request_records'],
    'usage_note': 'Missing usage is unknown, not zero; interrupted attempts have no terminal result.',
    'requests': entries}
(data / 'high_v4/artifact_audit.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps({k: v for k, v in report.items() if k != 'requests'}, indent=2))
