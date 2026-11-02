"""Independent saved-artifact checks for v4, including actual wrong model values.

No model calls. Read source hashes, all raw attempts, paired lineage and exports.
"""
import gzip
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from high_fixtures import HIGH_FIELDS, high_validate_answer

base = Path(__file__).parent
root = base.parent / 'experiment_notebooks/notebooks/23-synthetic-data-curation'
data = root / 'data'
target = data / 'high_v4'
read = lambda p: json.loads(p.read_text(encoding='utf-8'))
read_lines = lambda p: [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines() if s]
canonical = lambda v: json.dumps(v, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
sha = lambda v: hashlib.sha256(v).hexdigest()
source_index = read(target / 'preflight/manifest.json')
sql = {r['case_id']: r for r in read(target / 'preflight/independent_sql_audit.json')['cases']}
fraction = {r['case_id']: r for level in read(target / 'preflight/independent_fraction_audit.json')['levels'] for r in level['cases']}
sources = {}
for entry in source_index['levels']:
    packed = (target / 'preflight' / entry['file']).read_bytes()
    assert sha(packed) == entry['compressed_sha256']
    raw = gzip.decompress(packed)
    assert sha(raw) == entry['uncompressed_sha256']
    rows = [json.loads(s) for s in raw.decode('utf-8').splitlines()]
    assert len(rows) == entry['n_cases']
    for row in rows:
        cid = row['case_id']
        assert cid not in sources
        assert sha(row['document'].encode()) == sql[cid]['document_sha256'] == fraction[cid]['document_sha256']
        assert row['gold'] == sql[cid]['answer_from_text'] == fraction[cid]['answer_from_rendered_text']
        assert fraction[cid]['evidence_matches_stored_key']
        sources[cid] = row
assert len(sources) == 1056
pilot_rows = read_lines(target / 'pilot/potential_cases.jsonl')
assert len(pilot_rows) == 32
assert not set(sources) & {r['case_id'] for r in pilot_rows}
sources.update({r['case_id']: r for r in pilot_rows})

counts, usage, records, cached = Counter(), Counter(), [], {}
for directory in sorted(data.glob('high_v4*')):
    for path in sorted(directory.rglob('cache/*.json')):
        obj = read(path)
        req = obj['request']
        assert obj['key'] == path.stem == sha(canonical(req).encode())
        assert len(obj['attempts']) == 1
        assert req['model'] == 'gpt-6.1-sol' and req['reasoning_effort'] == 'high'
        assert 'model_reasoning_effort="high"' in req['cli_options']
        assert len(req['case_inputs']) == 1
        item = req['case_inputs'][0]
        assert set(item) == {'case_id', 'task_instructions', 'documents'}
        cid = item['case_id']
        assert item['documents'] == sources[cid]['document']
        assert item['task_instructions'] == source_index['task_instructions']
        attempt = obj['attempts'][0]
        result = None
        if attempt.get('pending'):
            category = 'interrupted_pending'
        elif attempt.get('error'):
            category = 'terminal_service_error'
        else:
            assert any(e.get('type') == 'turn.completed' for e in attempt['events'])
            parsed = attempt.get('parsed')
            if (isinstance(parsed, dict) and list(parsed) == ['results'] and isinstance(parsed['results'], list)
                    and len(parsed['results']) == 1 and parsed['results'][0].get('case_id') == cid):
                result = parsed['results'][0]
            verdict = high_validate_answer(sources[cid], result)
            category = ('schema_or_parse_failure' if not verdict['valid_schema'] else
                        'value_failure_response' if not verdict['exact_fields'] else
                        'accepted_response' if verdict['accepted'] else 'citation_only_failure')
        counts['request_records'] += 1
        counts[category] += 1
        counts['requests_with_usage'] += bool(attempt.get('token_usage'))
        usage.update(attempt.get('token_usage') or {})
        assert obj['key'] not in cached
        cached[obj['key']] = (req, attempt, result)
        records.append({'run': directory.name, 'case_id': cid, 'protocol': req['protocol'],
            'stage': req['stage'], 'sample': req['sample'], 'outcome': category,
            'request_key': obj['key'], 'cache_file': path.relative_to(root).as_posix()})

main = target / 'main'
complete = (main / 'manifest.json').exists()
pair_check = None
if complete:
    original = read_lines(main / 'candidates.jsonl')
    arms = read_lines(main / 'interventions.jsonl')
    selection = read(main / 'selection.json')
    allocation = read(main / 'allocation.json')
    cfg = read(main / 'protocol.json')['config']
    original_by_id = {r['candidate_id']: r for r in original}
    original_by_case = {r['case_id']: r for r in original}
    eligible = {r['case_id'] for r in original if r['split'] == 'collection'
        and not r['transport_error'] and r['response'] is not None
        and r['verification']['valid_schema'] and not r['verification']['exact_fields']}
    expected_selection = [cid for cid in allocation['failure_selection_ranking'] if cid in eligible][:cfg['max_selected']]
    assert expected_selection == selection['selected_case_ids']
    paired = {arm: {r['case_id']: r for r in arms if r['arm'] == arm} for arm in ['fresh_retry', 'feedback_repair']}
    for arm in paired:
        assert set(paired[arm]) == set(expected_selection)
    for row in original + arms:
        req, attempt, response = cached[row['request_key']]
        assert response == row['response']
        assert high_validate_answer(sources[row['case_id']], response) == row['verification']
        if row['arm'] == 'original':
            continue
        old = original_by_id[row['original_candidate_id']]
        assert row['original_request_key'] == old['request_key']
        assert req['case_inputs'] == cached[old['request_key']][0]['case_inputs']
        if row['arm'] == 'fresh_retry':
            assert req['feedback'] is None and req['stage'] == 'generate' and req['sample'] == 1
        else:
            assert set(req['feedback']) == {row['case_id']}
            package = req['feedback'][row['case_id']]
            assert set(package) == {'original_output', 'validator_feedback'}
            assert package['original_output'] == old['response']
            assert package['validator_feedback'] == {
                'wrong_fields': [f for f in HIGH_FIELDS if not old['verification']['field_correct'][f]],
                'schema_failed': not old['verification']['valid_schema'],
                'evidence_failed_fields': [f for f in HIGH_FIELDS if not old['verification']['evidence_correct'][f]]}
    def success(row):
        return not row['transport_error'] and row['response'] is not None and row['verification']['valid_schema'] and row['verification']['exact_fields']
    table = Counter((success(paired['fresh_retry'][cid]), success(paired['feedback_repair'][cid])) for cid in expected_selection)
    metrics = read(main / 'metrics.json')
    observed = metrics['paired_value_recovery']
    assert [table[True,True],table[False,True],table[True,False],table[False,False]] == [observed['both_success'],observed['repair_only'],observed['fresh_only'],observed['neither_success']]
    unique = {}
    for arm in ['original', 'feedback_repair', 'fresh_retry']:
        for path in sorted((main / 'exports' / arm).glob('accepted_examples.jsonl')):
            for row in read_lines(path):
                assert row['verification']['accepted'] and high_validate_answer(sources[row['case_id']], row['response'])['accepted']
                assert sources[row['case_id']]['split'] == 'collection'
                unique.setdefault(row['semantic_hash'], row)
        for path in sorted((main / 'exports' / arm).glob('value_preference_pairs.jsonl')):
            for row in read_lines(path):
                case = sources[row['case_id']]
                assert case['split'] == 'collection'
                assert high_validate_answer(case, row['chosen'])['accepted']
                assert not high_validate_answer(case, row['rejected'])['exact_fields']
    union_path = main / 'exports/curated_unique.jsonl'
    union_path.write_text(''.join(canonical(row) + '\n' for row in unique.values()), encoding='utf-8', newline='\n')
    pair_check = {'n_pairs': len(expected_selection), 'repair_only': table[False,True], 'fresh_only': table[True,False],
        'both': table[True,True], 'neither': table[False,False], 'unique_strictly_accepted_collection_sources': len(unique),
        'feedback_has_field_names_and_original_answer_only': True, 'selection_matches_predeclared_ranking': True}
report = {'audited_at_utc': datetime.now(timezone.utc).isoformat(), 'passed': True,
    'n_preflight_main_cases': 1056, 'n_pilot_cases': 32, 'unique_source_cases': len(sources),
    'independent_source_answers_and_evidence_agree': True, 'counts': dict(counts), 'observed_usage': dict(usage),
    'usage_incomplete': counts['requests_with_usage'] != counts['request_records'],
    'usage_note': 'Missing usage is unknown; components such as reasoning tokens are included in totals, not added twice.',
    'main_complete': complete, 'paired_lineage_check': pair_check, 'requests': records}
(target / 'artifact_audit.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps({k:v for k,v in report.items() if k != 'requests'}, indent=2))
