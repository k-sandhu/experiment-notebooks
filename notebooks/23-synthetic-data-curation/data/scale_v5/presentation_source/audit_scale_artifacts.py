"""Post-collection V5 integrity checks; never changes frozen collection artifacts."""
from collections import Counter
import ast
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path

from scale_resume import scale_resume_load, scale_resume_verify
from scale_intervention_resume import scale_intervention_resume_verify, SCALE_INTERVENTION_UNAVAILABLE
from scale_intervention_resume_003 import scale_intervention_resume_003_verify
from scale_intervention_resume_004 import scale_intervention_resume_004_verify
from scale_intervention_resume_005 import scale_intervention_resume_005_verify
from scale_intervention_resume_006 import scale_intervention_resume_006_verify

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent / 'experiment_notebooks' / 'notebooks' / '23-synthetic-data-curation'
DATA = ROOT / 'data' / 'scale_v5'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(',', ':')).encode('utf-8')).hexdigest()


def records(path):
    raw = path.read_bytes()
    if path.suffix == '.gz':
        raw = gzip.decompress(raw)
    return [json.loads(line) for line in raw.splitlines() if line.strip()]


def audit_exports(originals, interventions, unavailable_keys, namespace):
    """Check actual training candidates against sources and recorded model answers."""
    all_rows = originals + interventions
    by_candidate = {row['candidate_id']: row for row in all_rows}
    assert len(by_candidate) == len(all_rows)
    collection_ids = {row['case_id'] for row in originals if row['split'] == 'collection'}
    prompt_hashes = {}
    with gzip.open(DATA / 'main/sources/collection.jsonl.gz', 'rt', encoding='utf-8') as stream:
        for line in stream:
            case = json.loads(line)
            if case['case_id'] in collection_ids:
                prompt_hashes[case['case_id']] = canonical_sha(namespace['scale_case_prompt'](case))
    assert set(prompt_hashes) == collection_ids
    accepted_by_arm, statistics = {}, {}
    unknown_rejections = set()
    for arm in ('original', 'feedback_repair', 'fresh_retry'):
        folder = DATA / 'main/exports' / arm
        accepted = records(folder / 'accepted_examples.jsonl.gz')
        rejected = records(folder / 'rejected_examples.jsonl.gz')
        preferences = records(folder / 'value_preference_pairs.jsonl.gz')
        expected = {row['candidate_id']: row for row in all_rows
                    if row['split'] == 'collection' and row['arm'] == arm}
        accepted_ids = {row['candidate_id'] for row in accepted}
        rejected_ids = {row['candidate_id'] for row in rejected}
        assert len(accepted_ids) == len(accepted) and len(rejected_ids) == len(rejected)
        assert not accepted_ids.intersection(rejected_ids)
        assert accepted_ids | rejected_ids == set(expected), 'Export row missing, duplicated or audit data included'
        assert len({row['semantic_hash'] for row in accepted}) == len(accepted)
        for item in accepted:
            row = expected[item['candidate_id']]
            assert row['verification']['accepted'] is True and row['response'] is not None
            assert row['request_key'] not in unavailable_keys and not row['transport_error']
            for field in ('case_id', 'request_key', 'response', 'verification', 'semantic_hash', 'arm'):
                assert item[field] == row[field], 'Accepted target or provenance differs from the observed model answer'
            assert item['reasoning_effort'] == 'high'
            assert canonical_sha(item['prompt']) == prompt_hashes[row['case_id']]
        for item in rejected:
            assert item == expected[item['candidate_id']] and not item['verification']['accepted']
            if item['request_key'] in unavailable_keys:
                assert item.get('outcome_unavailable') is True and item['response'] is None
                unknown_rejections.add(item['request_key'])
        assert len(preferences) == (0 if arm == 'original' else len(accepted))
        chosen_ids = [pair['chosen_candidate_id'] for pair in preferences]
        assert len(chosen_ids) == len(set(chosen_ids))
        if arm != 'original':
            assert set(chosen_ids) == accepted_ids, 'A preference target is repeated or missing'
        for pair in preferences:
            chosen = expected[pair['chosen_candidate_id']]
            old = by_candidate[pair['rejected_candidate_id']]
            assert chosen['original_candidate_id'] == old['candidate_id']
            assert chosen['candidate_id'] in accepted_ids and chosen['request_key'] not in unavailable_keys
            assert old['arm'] == 'original' and old['split'] == 'collection' and not old['transport_error']
            assert old['response'] is not None and old['verification']['valid_schema'] and not old['verification']['exact_fields']
            assert pair['case_id'] == chosen['case_id'] == old['case_id']
            assert pair['semantic_hash'] == chosen['semantic_hash'] == old['semantic_hash']
            assert pair['chosen'] == chosen['response'] and pair['rejected'] == old['response']
            assert pair['request_keys'] == [chosen['request_key'], old['request_key']]
            assert pair['arm'] == arm and canonical_sha(pair['prompt']) == prompt_hashes[pair['case_id']]
        accepted_by_arm[arm] = {row['semantic_hash']: row for row in accepted}
        statistics[arm] = {'accepted': len(accepted), 'rejected_diagnostic_rows': len(rejected),
                           'verified_preference_pairs': len(preferences)}
    assert unknown_rejections == unavailable_keys
    curated = records(DATA / 'main/exports/curated_unique.jsonl.gz')
    curated_by_hash = {row['semantic_hash']: row for row in curated}
    assert len(curated_by_hash) == len(curated)
    assert set(curated_by_hash) == set().union(*(set(rows) for rows in accepted_by_arm.values()))
    for semantic, item in curated_by_hash.items():
        preferred = next(rows[semantic] for rows in accepted_by_arm.values() if semantic in rows)
        assert item == preferred, 'Curated export changed a model answer or arm-priority policy'
    return {'files_checked': 10, 'by_arm': statistics, 'distinct_accepted_sources': len(curated),
            'unavailable_rows_in_rejection_logs_only': len(unknown_rejections),
            'audit_sources_in_training_candidates': 0, 'invented_or_changed_training_targets': 0}


def audit_candidate_lineage(rows, caches, cases, namespace, unavailable_keys):
    """Bind source, exact request, cached raw answer, and independent verifier result."""
    originals = {row['candidate_id']: row for row in rows if row['arm'] == 'original'}
    assert len(originals) == len([row for row in rows if row['arm'] == 'original'])
    response_hashes = {}
    for row in rows:
        case = cases[row['case_id']]
        cache = caches[row['request_key']]
        request, attempt = cache['request'], cache['attempts'][0]
        expected_inputs = [namespace['scale_model_input'](case)]
        assert request['case_inputs'] == expected_inputs, 'Model request differs from its frozen source packet'
        assert row['request_input_hash'] == canonical_sha(expected_inputs)
        assert row['feedback_hash'] == canonical_sha(request['feedback'])
        if row.get('outcome_unavailable'):
            assert row['request_key'] in unavailable_keys and attempt.get('pending') is True
            assert row['response'] is None and row['transport_error'] == SCALE_INTERVENTION_UNAVAILABLE
            assert row.get('error_kind') == 'outcome_unavailable'
            parsed = None
        else:
            assert row['request_key'] not in unavailable_keys and attempt.get('pending') is not True
            parsed, parse_error = namespace['scale_extract_single'](attempt, row['case_id'])
            assert row['response'] == parsed, 'Saved parsed answer differs from the raw cached response'
            assert row['transport_error'] == attempt.get('error'), 'Saved transport status differs from the raw cache'
            assert row['parse_error'] == (attempt.get('parse_error') or parse_error), 'Saved parse status differs from the raw cache'
        verified = namespace['scale_validate_answer'](case, parsed if not attempt.get('error') else None)
        assert row['verification'] == verified, 'Saved verifier flags differ from the independent source-derived gold check'
        if row['arm'] == 'feedback_repair':
            original = originals[row['original_candidate_id']]
            expected_feedback = {row['case_id']: {'original_output': original['response'],
                'validator_feedback': namespace['scale_generic_feedback'](original)}}
            assert request['feedback'] == expected_feedback, 'Repair request does not match the exact original answer and verified failed-field feedback'
        else:
            assert request['feedback'] is None
        raw = attempt.get('final_assistant_response')
        response_hashes[row['request_key']] = hashlib.sha256(raw.encode('utf-8')).hexdigest() if isinstance(raw, str) else None
    return {'source_bound_rows': len(rows), 'raw_response_hashes': response_hashes,
            'gold_reverified_rows': len(rows), 'source_prompt_and_request_matches': True}


def main():
    manifest = read(DATA / 'main' / 'manifest.json')
    assert manifest['phase'] == 'interventions_complete', 'Never inspect efficacy before completion'
    baseline = read(BASE / 'scale_baseline_manifest.json')
    protected = {k: v for k, v in baseline['source_files'].items()
                 if k not in baseline['allowed_existing_changes']}
    assert len(protected) == 985
    assert all(sha(ROOT / k) == v for k, v in protected.items()), 'Historical bytes changed'
    prereg = read(DATA / 'preregistration.json')
    assert all(sha(DATA / 'source_snapshot' / k) == v for k, v in prereg['snapshot_sha256'].items())
    assert sha(DATA / 'source_freeze.json') == prereg['source_freeze_sha256']
    freeze = read(DATA / 'source_freeze.json')
    assert all(sha(BASE / k) == v for k, v in freeze['source_sha256'].items())
    notebook = read(ROOT / '23_synthetic_data_curation.ipynb')
    embedded_cells = [''.join(c['source']) for c in notebook['cells'] if c['cell_type'] == 'code']
    embedded_hashes = {}
    for name in ('scale_transport.py', 'scale_fixtures.py', 'scale_parallel.py', 'scale_experiment.py'):
        normalized = (BASE / name).read_text(encoding='utf-8').rstrip()
        matches = [source for source in embedded_cells if source.rstrip() == normalized]
        assert len(matches) == 1, 'Missing, duplicated or changed embedded V5 source: ' + name
        embedded_hashes[name] = hashlib.sha256(matches[0].encode('utf-8')).hexdigest()
    amendment_path = DATA / 'infrastructure_resume/amendment_001.json'
    resume = scale_resume_verify(ROOT, amendment_path, scale_resume_load(ROOT))
    amendment = resume['amendment']
    assert all(sha(DATA / k) == v for k, v in amendment['provenance_sha256'].items()), 'Continuation provenance changed'
    assert sha(BASE / 'scale_resume.py') == amendment['implementation']['sha256']
    assert sha(BASE / 'test_scale_resume.py') == amendment['implementation']['tests_sha256']
    implementation_review = read(DATA / 'infrastructure_resume/scale_resume_implementation_review.json')
    assert implementation_review['passed'] and implementation_review['source_sha256'] == amendment['implementation']['sha256']
    assert implementation_review['tests_sha256'] == amendment['implementation']['tests_sha256']
    embedded_resume = []
    for source in embedded_cells:
        for node in ast.parse(source).body:
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'SCALE_RESUME_SOURCE' for t in node.targets):
                embedded_resume.append(ast.literal_eval(node.value))
    assert embedded_resume == [(BASE / 'scale_resume.py').read_text(encoding='utf-8')], 'Embedded continuation differs from reviewed helper'
    embedded_hashes['scale_resume.py'] = hashlib.sha256(embedded_resume[0].encode('utf-8')).hexdigest()
    prior_inventory = read(DATA / amendment['cache_inventory']['path'])['requests']
    assert len(prior_inventory) == 696
    interruption = scale_intervention_resume_verify(ROOT, DATA / 'intervention_resume/amendment_002.json')
    interrupted_amendment = interruption['amendment']
    assert all(sha(DATA / k) == v for k, v in interrupted_amendment['provenance_sha256'].items()), 'Interruption provenance changed'
    assert sha(BASE / 'scale_intervention_resume.py') == interrupted_amendment['implementation']['sha256']
    interrupted_embedded = []
    for source in embedded_cells:
        for node in ast.parse(source).body:
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'SCALE_INTERVENTION_RESUME_SOURCE' for t in node.targets):
                interrupted_embedded.append(ast.literal_eval(node.value))
    assert interrupted_embedded == [(BASE / 'scale_intervention_resume.py').read_text(encoding='utf-8')], 'Embedded interruption companion differs from reviewed source'
    embedded_hashes['scale_intervention_resume.py'] = hashlib.sha256(interrupted_embedded[0].encode()).hexdigest()
    latest_interruption = scale_intervention_resume_003_verify(ROOT, DATA / 'intervention_resume_003/amendment_003.json')
    latest_amendment = latest_interruption['amendment']
    assert all(sha(DATA / k) == v for k, v in latest_amendment['provenance_sha256'].items()), 'Second interruption provenance changed'
    assert sha(BASE / 'scale_intervention_resume_003.py') == latest_amendment['implementation']['sha256']
    latest_embedded = []
    for source in embedded_cells:
        for node in ast.parse(source).body:
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'SCALE_INTERVENTION_RESUME_003_SOURCE' for t in node.targets):
                latest_embedded.append(ast.literal_eval(node.value))
    assert latest_embedded == [(BASE / 'scale_intervention_resume_003.py').read_bytes().decode('utf-8')], 'Embedded second interruption source differs'
    embedded_hashes['scale_intervention_resume_003.py'] = hashlib.sha256(latest_embedded[0].encode()).hexdigest()
    timeout_continuation = scale_intervention_resume_004_verify(ROOT, DATA / 'intervention_resume_004/amendment_004.json')
    timeout_amendment = timeout_continuation['amendment']
    assert all(sha(DATA / k) == v for k, v in timeout_amendment['provenance_sha256'].items()), 'Timeout continuation provenance changed'
    assert sha(BASE / 'scale_intervention_resume_004.py') == timeout_amendment['implementation']['sha256']
    timeout_embedded = []
    for source in embedded_cells:
        for node in ast.parse(source).body:
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'SCALE_INTERVENTION_RESUME_004_SOURCE' for t in node.targets):
                timeout_embedded.append(ast.literal_eval(node.value))
    assert timeout_embedded == [(BASE / 'scale_intervention_resume_004.py').read_bytes().decode('utf-8')], 'Embedded timeout continuation differs'
    embedded_hashes['scale_intervention_resume_004.py'] = hashlib.sha256(timeout_embedded[0].encode()).hexdigest()
    transport_continuation = scale_intervention_resume_005_verify(ROOT, DATA / 'intervention_resume_005/amendment_005.json')
    transport_amendment = transport_continuation['amendment']
    assert all(sha(DATA / k) == v for k, v in transport_amendment['provenance_sha256'].items()), 'Transport continuation provenance changed'
    assert sha(BASE / 'scale_intervention_resume_005.py') == transport_amendment['implementation']['sha256']
    transport_embedded = []
    for source in embedded_cells:
        for node in ast.parse(source).body:
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'SCALE_INTERVENTION_RESUME_005_SOURCE' for t in node.targets):
                transport_embedded.append(ast.literal_eval(node.value))
    assert transport_embedded == [(BASE / 'scale_intervention_resume_005.py').read_bytes().decode('utf-8')], 'Embedded fifth continuation differs'
    embedded_hashes['scale_intervention_resume_005.py'] = hashlib.sha256(transport_embedded[0].encode()).hexdigest()
    continuation006 = scale_intervention_resume_006_verify(ROOT, DATA / 'intervention_resume_006/amendment_006.json')
    amendment006 = continuation006['amendment']
    assert all(sha(DATA / k) == v for k, v in amendment006['provenance_sha256'].items()), '006 continuation provenance changed'
    assert sha(BASE / 'scale_intervention_resume_006.py') == amendment006['implementation']['sha256']
    embedded006 = []
    for source in embedded_cells:
        for node in ast.parse(source).body:
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'SCALE_INTERVENTION_RESUME_006_SOURCE' for t in node.targets):
                embedded006.append(ast.literal_eval(node.value))
    assert embedded006 == [(BASE / 'scale_intervention_resume_006.py').read_bytes().decode('utf-8')], 'Embedded sixth continuation differs'
    embedded_hashes['scale_intervention_resume_006.py'] = hashlib.sha256(embedded006[0].encode()).hexdigest()
    missing_source = (BASE / 'scale_missing_outcomes_003.py').read_text(encoding='utf-8')
    assert len([s for s in embedded_cells if s.startswith(missing_source+'\n\n')]) == 1, 'Frozen missing-outcome analysis is not embedded exactly once'
    embedded_hashes['scale_missing_outcomes_003.py'] = hashlib.sha256(missing_source.encode()).hexdigest()
    missing_source006 = (BASE / 'scale_missing_outcomes_006.py').read_text(encoding='utf-8')
    assert sum(s.count(missing_source006) for s in embedded_cells) == 1, 'Amendment-006 missing-outcome helper is not embedded exactly once'
    embedded_hashes['scale_missing_outcomes_006.py'] = hashlib.sha256(missing_source006.encode()).hexdigest()
    unavailable_keys = set(continuation006['approved'])
    assert len(unavailable_keys) == 9 and set(transport_continuation['approved']).issubset(unavailable_keys)
    retained_terminal_keys = set(continuation006['retained'])
    assert len(retained_terminal_keys) == 2 and not unavailable_keys.intersection(retained_terminal_keys)
    gate_names = ['pilot_start_declaration.json', 'main_start_declaration.json',
                  'intervention_start_declaration.json', 'intervention_resume/continuation_start_002.json',
                  'intervention_resume_003/continuation_start_003.json',
                  'intervention_resume_004/continuation_start_004.json',
                  'intervention_resume_005/continuation_start_005.json',
                  'intervention_resume_006/continuation_start_006.json']
    gates = {name: read(DATA / name) for name in gate_names}
    for gate in gates.values():
        assert all(sha(DATA / k) == v for k, v in gate['sha256'].items()), 'Gate lineage changed'
    ladder = read(DATA / 'pilot/ladder.json')
    pilot_keys = [key for tier in ladder['tiers'] for key in tier['request_keys']]
    scheduled_keys = pilot_keys + manifest['request_keys']
    assert len(scheduled_keys) == len(set(scheduled_keys)), 'Scheduled physical requests repeat'
    ledger_by_key = {}
    ledger_paths = [DATA / 'main/request_ledger.jsonl'] + [
        DATA / 'pilot' / ('tier_' + str(tier['tier'])) / 'request_ledger.jsonl' for tier in ladder['tiers']]
    for ledger_path in ledger_paths:
        for line in ledger_path.read_text(encoding='utf-8').splitlines():
            entry = json.loads(line)
            assert entry['request_key'] not in ledger_by_key, 'Duplicate physical ledger key'
            ledger_by_key[entry['request_key']] = entry
    assert set(ledger_by_key) == set(scheduled_keys), 'Scheduled keys and ledgers differ'
    attempts, categories, token_usage, unknown_usage, seen, cache_rows = [], Counter(), Counter(), 0, set(), {}
    for path in sorted(DATA.glob('**/cache/*.json.gz')):
        row = json.loads(gzip.decompress(path.read_bytes()))
        key, request = row['key'], row['request']
        cache_rows[key] = row
        assert path.name == key + '.json.gz' and canonical_sha(request) == key
        assert key not in seen, 'Duplicate physical request cache'
        seen.add(key)
        assert request['model'] == 'gpt-6.1-sol' and request['reasoning_effort'] == 'high'
        assert len(request['case_inputs']) == 1
        assert request['protocol'] == '23-scale-v5'
        assert key in ledger_by_key, 'Unscheduled cache found'
        entry = ledger_by_key[key]
        assert request['expected_case_ids'] == [entry['case_id']]
        assert request['case_inputs'][0]['case_id'] == entry['case_id']
        assert request['stage'] == entry['stage'] and request['sample'] == entry['sample']
        assert canonical_sha(request['case_inputs']) == entry['request_input_hash']
        assert canonical_sha(request['feedback']) == entry['feedback_hash']
        assert len(row['attempts']) == 1, 'Orchestration resubmission found'
        attempt = row['attempts'][0]
        if key in unavailable_keys:
            assert attempt['pending'] is True and set(attempt) == {'pending', 'started_at', 'timeout_s'}
            assert entry.get('outcome_unavailable') is True and entry.get('telemetry_status') == 'raw_pending_preserved'
            assert entry['started_at'] == attempt['started_at']
            assert entry['finished_at'] is None and entry['subprocess_elapsed_s'] is None and entry['return_code'] is None
            assert not entry['usage'] and not entry['cli_error_events'] and not entry['observed_reconnect_events']
        else:
            assert not attempt['pending'] and not attempt.get('unexpected_tools')
            if attempt.get('error'):
                assert key in set(resume['approved']) | retained_terminal_keys, 'Unreviewed terminal error in completed study'
            if key in retained_terminal_keys:
                retained = transport_continuation['retained'][key]
                assert sha(path) == retained['cache_sha256'] and attempt['error'] == retained['error']
                assert all(attempt.get(name) == value for name,value in retained['attempt_metadata'].items())
                assert ('token_usage' in attempt) is retained['token_usage_field_present']
                assert bool(attempt.get('token_usage')) is retained['token_usage_nonempty']
                assert not entry.get('outcome_unavailable'), 'Known terminal service failure became an unknown observation'
        gate_key = ('pilot_start_declaration.json' if 'pilot' in path.relative_to(DATA).parts
                    else 'intervention_start_declaration.json' if request.get('feedback') is not None or request.get('sample') == 1
                    else 'main_start_declaration.json')
        assert datetime.fromisoformat(attempt['started_at']) >= datetime.fromisoformat(gates[gate_key]['declared_at_utc'])
        assert datetime.fromisoformat(attempt['started_at']) >= datetime.fromisoformat(prereg['registered_at_utc'])
        if gate_key == 'main_start_declaration.json' and key not in prior_inventory:
            assert datetime.fromisoformat(attempt['started_at']) >= datetime.fromisoformat(amendment['declared_at_utc']), 'New original predates continuation amendment'
        if gate_key == 'intervention_start_declaration.json' and key not in interruption['inventory']:
            assert datetime.fromisoformat(attempt['started_at']) >= datetime.fromisoformat(interrupted_amendment['declared_at_utc']), 'New arm request predates interruption amendment'
            assert datetime.fromisoformat(attempt['started_at']) >= datetime.fromisoformat(gates['intervention_resume/continuation_start_002.json']['declared_at_utc']), 'New arm request predates independently reviewed continuation gate'
        if gate_key == 'intervention_start_declaration.json' and key not in latest_interruption['inventory']:
            assert datetime.fromisoformat(attempt['started_at']) >= datetime.fromisoformat(latest_amendment['declared_at_utc']), 'New arm request predates second interruption amendment'
            assert datetime.fromisoformat(attempt['started_at']) >= datetime.fromisoformat(gates['intervention_resume_003/continuation_start_003.json']['declared_at_utc']), 'New arm request predates second continuation gate'
        if gate_key == 'intervention_start_declaration.json' and key not in timeout_continuation['inventory']:
            assert datetime.fromisoformat(attempt['started_at']) >= datetime.fromisoformat(timeout_amendment['declared_at_utc']), 'New arm request predates terminal-timeout continuation amendment'
            assert datetime.fromisoformat(attempt['started_at']) >= datetime.fromisoformat(gates['intervention_resume_004/continuation_start_004.json']['declared_at_utc']), 'New arm request predates terminal-timeout continuation gate'
        if gate_key == 'intervention_start_declaration.json' and key not in transport_continuation['inventory']:
            assert datetime.fromisoformat(attempt['started_at']) >= datetime.fromisoformat(transport_amendment['declared_at_utc']), 'New arm request predates fifth continuation amendment'
            assert datetime.fromisoformat(attempt['started_at']) >= datetime.fromisoformat(gates['intervention_resume_005/continuation_start_005.json']['declared_at_utc']), 'New arm request predates fifth continuation gate'
        if gate_key == 'intervention_start_declaration.json' and key in continuation006['unsent_request_keys']:
            assert datetime.fromisoformat(attempt['started_at']) >= datetime.fromisoformat(amendment006['declared_at_utc']), 'New arm request predates sixth continuation amendment'
            assert datetime.fromisoformat(attempt['started_at']) >= datetime.fromisoformat(gates['intervention_resume_006/continuation_start_006.json']['declared_at_utc']), 'New arm request predates sixth continuation gate'
        usage = attempt.get('token_usage') or {}
        unknown_usage += not bool(usage)
        token_usage.update({k: v for k, v in usage.items() if type(v) in (int, float)})
        category = ('outcome_unavailable' if key in unavailable_keys else 'transport_failure' if attempt.get('error') else 'parse_failure' if attempt.get('parse_error') else 'successful_transport')
        categories[category] += 1
        attempts.append({'request_key': key, 'cache_file': path.relative_to(ROOT).as_posix(),
                         'sha256': sha(path), 'category': category,
                         'request_input_sha256': canonical_sha(request['case_inputs']),
                         'feedback_sha256': canonical_sha(request['feedback']),
                         'raw_response_sha256': (hashlib.sha256(attempt['final_assistant_response'].encode('utf-8')).hexdigest()
                             if isinstance(attempt.get('final_assistant_response'), str) else None),
                         'started_at': attempt['started_at'], 'finished_at': attempt.get('finished_at'),
                         'observed_reconnect_events': len(attempt.get('observed_reconnect_events') or [])})
    assert seen == set(scheduled_keys), 'Scheduled caches are missing or substituted'
    main_cache_keys = {key for key in seen if (DATA / 'main/cache' / (key + '.json.gz')).is_file()}
    assert main_cache_keys == set(read(DATA / 'main/original_manifest.json')['request_keys']) | set(manifest['request_keys'])
    new_keys = main_cache_keys - set(continuation006['inventory'])
    assert len(continuation006['inventory']) == 2268 and new_keys == set(continuation006['unsent_request_keys'])
    assert len(new_keys) == 52, 'Completion must add exactly the 52 previously unsent requests'
    assert len(attempts) == manifest['total_pilot_plus_main_requests'] <= 3376
    analysis_path = DATA / 'presentation_results/missing_outcome_analysis.json'
    analysis = read(analysis_path)
    plan006 = read(DATA / amendment006['analysis_plan']['path'])
    previous_plan006 = read(DATA / amendment006['previous_analysis_plan']['path'])
    assert sha(DATA / amendment006['analysis_plan']['path']) == amendment006['analysis_plan']['sha256']
    assert sha(DATA / amendment006['previous_analysis_plan']['path']) == amendment006['previous_analysis_plan']['sha256']
    assert plan006['previous_analysis_plan'] == amendment006['previous_analysis_plan']
    assert plan006['previous_analysis_plan'] == transport_amendment['analysis_plan']
    assert plan006['predecessor_calculator_sha256'] == hashlib.sha256((BASE / 'scale_missing_outcomes_003.py').read_bytes()).hexdigest()
    assert plan006['analysis_source_sha256'] == sha(BASE / 'scale_missing_outcomes_006.py')
    assert plan006['analysis_tests_sha256'] == sha(BASE / 'test_scale_missing_outcomes_006.py')
    assert plan006['unknown_request_keys'] == sorted(unavailable_keys)
    assert analysis['n_scheduled_pairs'] == 600 and analysis['n_observed_pairs'] == 595
    assert analysis['n_unavailable_pairs'] == 5 and analysis['n_unavailable_outcomes'] == 9
    assert analysis['n_wholly_unavailable_pairs'] == 4 and analysis['n_partially_unavailable_pairs'] == 1
    assert set(analysis['unavailable_request_keys']) == unavailable_keys
    assert analysis['n_completions'] == 512 and len(analysis['completion_sensitivity']) == 512
    assert all(row['hypothetical_only'] is True for row in analysis['completion_sensitivity'])
    assert analysis['bootstrap_seed'] == 246600 and analysis['bootstrap_draws'] == 20000
    assert analysis['amended_primary_decision']['criterion_met'] == all(row['primary_criterion_met'] for row in analysis['completion_sensitivity'])
    assert analysis['known_partner_request_keys'] == [plan006['known_partner_request_key']]
    assert analysis['known_partner_policy'] == 'Observed partner fixed in every scheduled-cohort completion; partial pair excluded only from complete-pair inference'
    selected = read(DATA / 'main/selection.json')['selected_case_ids']
    unavailable_ids = {row['case_id'] for row in continuation006['approved'].values()}
    observed_ids = [cid for cid in selected if cid not in unavailable_ids]
    assert analysis['observed_case_ids'] == observed_ids
    assert len(observed_ids) == 595
    arms = {arm: {} for arm in ('fresh_retry', 'feedback_repair')}
    intervention_rows = []
    for line in (DATA / 'main/interventions.jsonl').read_text(encoding='utf-8').splitlines():
        row = json.loads(line)
        intervention_rows.append(row)
        arms[row['arm']][row['case_id']] = row
    namespace = scale_resume_load(ROOT)
    candidate_originals = records(DATA / 'main/candidates.jsonl')
    all_candidate_rows = candidate_originals + intervention_rows
    lineage_ids = {row['case_id'] for row in all_candidate_rows}
    lineage_cases = {}
    for source_path in (DATA / 'main/sources/collection.jsonl.gz', DATA / 'main/sources/audit.jsonl.gz'):
        for case in namespace['scale_iter_corpus'](source_path):
            if case['case_id'] in lineage_ids:
                assert case['case_id'] not in lineage_cases, 'Source case ID is duplicated across frozen source groups'
                lineage_cases[case['case_id']] = case
    assert set(lineage_cases) == lineage_ids, 'A scored source is missing from the frozen source packets'
    lineage_audit = audit_candidate_lineage(all_candidate_rows, cache_rows, lineage_cases, namespace, unavailable_keys)
    partner_key = plan006['known_partner_request_key']
    assert partner_key not in unavailable_keys and partner_key in cache_rows
    partner_rows = [row for row in intervention_rows if row['request_key'] == partner_key]
    assert len(partner_rows) == 1 and partner_rows[0]['case_id'] == plan006['partial_pair_case_id']
    assert not partner_rows[0].get('outcome_unavailable')
    def good(row):
        return bool(not row['transport_error'] and row['response'] is not None and row['verification']['valid_schema'] and row['verification']['exact_fields'])
    observed_pairs = [(good(arms['fresh_retry'][cid]), good(arms['feedback_repair'][cid])) for cid in observed_ids]
    assert analysis['paired_value_recovery'] == scale_resume_load(ROOT)['scale_paired_statistics'](observed_pairs, 246600, 20000)
    analysis_namespace = {'__name__': 'scale_audit_missing_outcomes_006'}
    exec(compile((BASE / 'scale_missing_outcomes_003.py').read_text(encoding='utf-8'), 'scale_missing_outcomes_003.py', 'exec'), analysis_namespace)
    exec(compile((BASE / 'scale_missing_outcomes_006.py').read_text(encoding='utf-8'), 'scale_missing_outcomes_006.py', 'exec'), analysis_namespace)
    protocol = read(DATA / 'main/protocol.json')
    recomputed = analysis_namespace['scale_missing_outcome_analysis_006'](
        manifest, {'selected_case_ids': selected}, intervention_rows,
        list(continuation006['approved'].values()), protocol['config'], plan006,
        list(latest_interruption['approved'].values()), namespace['scale_paired_statistics'])
    assert analysis == recomputed, 'Saved 512-completion analysis differs from an independent recomputation'
    export_audit = audit_exports(records(DATA / 'main/candidates.jsonl'), intervention_rows,
                                 unavailable_keys, namespace)
    export_audit['candidate_lineage'] = lineage_audit
    report = {'checked_at_utc': datetime.now(timezone.utc).isoformat(), 'passed': True,
              'protected_historical_files': len(protected), 'frozen_snapshot_files': len(prereg['snapshot_sha256']),
              'notebook_embedded_runtime_lf_sha256': embedded_hashes,
              'cached_request_slots': len(attempts), 'cache_categories': dict(categories),
              'requests_missing_usage': unknown_usage, 'observed_tokens': dict(token_usage),
              'spend_usd': None, 'gates_checked': gate_names, 'cache_index': attempts,
              'infrastructure_amendment_sha256': resume['amendment_sha256'],
              'preserved_pre_continuation_raw_caches': len(prior_inventory),
              'reviewed_capacity_failure_keys': sorted(resume['approved']),
              'interruption_amendment_sha256': interruption['amendment_sha256'],
              'preserved_pre_interruption_raw_caches': len(interruption['inventory']),
              'second_interruption_amendment_sha256': latest_interruption['amendment_sha256'],
              'preserved_pre_second_interruption_raw_caches': len(latest_interruption['inventory']),
              'timeout_continuation_amendment_sha256': timeout_continuation['amendment_sha256'],
              'preserved_pre_timeout_continuation_raw_caches': len(timeout_continuation['inventory']),
              'retained_terminal_timeout_keys': sorted(timeout_continuation['retained']),
              'transport_continuation_amendment_sha256': transport_continuation['amendment_sha256'],
              'preserved_pre_transport_continuation_raw_caches': len(transport_continuation['inventory']),
              'retained_terminal_transport_failure_keys': sorted(retained_terminal_keys),
              'missingness_continuation_amendment_sha256': continuation006['amendment_sha256'],
              'preserved_pre_missingness_continuation_raw_caches': len(continuation006['inventory']),
              'newly_completed_unsent_requests': len(new_keys),
              'partial_pair_case_id': plan006['partial_pair_case_id'],
              'known_partner_request_key': partner_key,
              'known_partner_retained_as_observed': True,
              'unavailable_attempt_slot_keys': sorted(unavailable_keys),
              'terminal_cli_records': len(attempts)-len(unavailable_keys),
              'physical_cli_start_count_bounds': [len(attempts)-len(unavailable_keys), len(attempts)],
              'missing_outcome_analysis_sha256': sha(analysis_path),
              'observed_complete_pairs': len(observed_pairs),
              'hypothetical_completion_count': len(analysis['completion_sensitivity']),
              'curated_data_integrity': export_audit,
              'note': 'No live calls were made by this audit. Nine raw pending attempt slots have unknown physical launch and outcome status; their bytes and missing telemetry remain unchanged. The partial pair’s observed partner remains in all-observed reporting and every scheduled-cohort completion, while that source is excluded from conditional paired inference. The recorded timeout and capacity failure are known operational non-recoveries even if a parsed body exists. Their raw errors, elapsed times, return codes and usage stay unchanged. Token components must not be added twice; missing usage and USD spend are unknown.'}
    (DATA / 'artifact_audit.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'cache_index'}))


if __name__ == '__main__':
    main()
