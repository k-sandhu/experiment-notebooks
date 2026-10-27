"""Freeze a second outcome-blind interruption amendment before unsent requests."""
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path


BASE = Path(__file__).resolve().parent
ROOT = BASE.parent / 'experiment_notebooks/notebooks/23-synthetic-data-curation'
DATA = ROOT / 'data/scale_v5'
PUBLIC = 'intervention_resume_003/'
INDICES = tuple(range(116, 120)) + tuple(range(416, 420))


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)


def encode(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def canonical(value):
    return sha(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf-8'))


def main():
    from scale_intervention_resume_003 import scale_intervention_resume_003_verify

    amendment_path = DATA / PUBLIC / 'amendment_003.json'
    if amendment_path.exists():
        verified = scale_intervention_resume_003_verify(ROOT, amendment_path)
        print(json.dumps({'existing_amendment_verified': True,
                          'sha256': verified['amendment_sha256'], 'model_calls': 0}))
        return

    sources = ('scale_intervention_resume_003', 'scale_missing_outcomes_003')
    for stem in sources:
        review = read(BASE / (stem + '_review.json'))
        assert review['passed'] is True and review['model_calls'] == 0 and not review['issues']
        assert review['source_sha256'] == sha((BASE / (stem + '.py')).read_bytes())
        assert review['tests_sha256'] == sha((BASE / ('test_' + stem + '.py')).read_bytes())
        assert review['test_log_sha256'] == sha((BASE / (stem + '_unit_tests.log')).read_bytes())
    assert read(DATA / 'main/original_manifest.json')['phase'] == 'originals_complete'
    assert not (DATA / 'main/manifest.json').exists(), 'Interventions are already complete'
    prior = read(BASE / 'scale_second_interruption_inventory.json')
    current = {p.name.removesuffix('.json.gz'): sha(p.read_bytes())
               for p in (DATA / 'main/cache').glob('*.json.gz')}
    assert current == prior['requests'] and len(current) == 1540
    old_inventory = read(DATA / 'intervention_resume/prior_cache_inventory_002.json')['requests']
    assert len(old_inventory) == 1240 and all(current.get(k) == v for k, v in old_inventory.items())

    dispatch = read(DATA / 'main/dispatch.json')['jobs']
    assert len(dispatch) == 1200
    arm_keys = [job['request_key'] for job in dispatch]
    assert set(current).intersection(arm_keys) == set(arm_keys[:420]), 'Recorded prefix differs'
    plans = []
    for path in (DATA / 'main/request_plans').glob('*.json'):
        rows = read(path)
        if [row['request_key'] for row in rows] == arm_keys:
            plans.append((path, rows))
    assert len(plans) == 1
    plan_path, plan_rows = plans[0]
    by_key = {row['request_key']: row for row in plan_rows}
    unavailable = []
    for index, job in enumerate(dispatch[:420]):
        key = job['request_key']
        cache = read(DATA / 'main/cache' / (key + '.json.gz'))
        assert cache['key'] == canonical(cache['request']) == key and len(cache['attempts']) == 1
        attempt = cache['attempts'][0]
        if index not in INDICES:
            assert attempt.get('pending') is False and attempt.get('finished_at') and not attempt.get('error')
            continue
        assert set(attempt) == {'pending', 'started_at', 'timeout_s'} and attempt['pending'] is True
        request, plan = cache['request'], by_key[key]
        assert request['model'] == 'gpt-6.1-sol' and request['reasoning_effort'] == 'high'
        assert canonical(request['case_inputs']) == job['input_hash']
        assert canonical(request['feedback']) == job['feedback_hash']
        unavailable.append({'request_key': key, 'cache_sha256': current[key], 'case_id': job['case_id'],
            'content_hash': plan['source_hash'], 'request_input_hash': job['input_hash'],
            'feedback_hash': job['feedback_hash'], 'arm': job['arm'], 'stage': request['stage'],
            'sample': request['sample'], 'profile': {'model': 'gpt-6.1-sol', 'reasoning_effort': 'high',
            'protocol': '23-scale-v5', 'timeout_s': 900}})
    assert len(unavailable) == 8 and len({row['case_id'] for row in unavailable}) == 4
    for cid in {row['case_id'] for row in unavailable}:
        assert {row['arm'] for row in unavailable if row['case_id'] == cid} == {'fresh_retry', 'feedback_repair'}
    previous = read(DATA / 'intervention_resume/amendment_002.json')
    assert set(previous['unavailable_request_keys']).issubset({row['request_key'] for row in unavailable})

    proof = read(BASE / 'scale_intervention_process_absence_003.json')
    assert proof['owned_workers'] == 0 and proof['collector_session_available'] is False
    assert proof['inaccessible_owned_candidates'] == 0
    launcher = BASE / 'launch_scale_intervention_resume_003.ps1'
    launch_proof = BASE / 'scale_detached_launcher_003_smoke.json'
    assert read(launch_proof)['passed'] is True and read(launch_proof)['model_calls'] == 0
    assert read(launch_proof)['launcher_sha256'] == sha(launcher.read_bytes())
    assert read(launch_proof)['worker_sha256'] == sha((BASE / 'scale_detached_worker_003.py').read_bytes())
    evidence = BASE / 'scale_detached_launcher_003_evidence.json'
    assert read(launch_proof)['evidence_sha256'] == sha(evidence.read_bytes())
    runtime_review = read(BASE / 'scale_intervention_resume_003_review.json')
    assert runtime_review['declaration_sha256'] == sha(Path(__file__).read_bytes())
    assert runtime_review['launcher_smoke_sha256'] == sha(launch_proof.read_bytes())
    assert runtime_review['launcher_sha256'] == sha(launcher.read_bytes())
    assert runtime_review['worker_sha256'] == sha((BASE / 'scale_detached_worker_003.py').read_bytes())

    now = datetime.now(timezone.utc).isoformat()
    source_sha = sha((BASE / 'scale_intervention_resume_003.py').read_bytes())
    analysis_sha = sha((BASE / 'scale_missing_outcomes_003.py').read_bytes())
    analysis_test_sha = sha((BASE / 'test_scale_missing_outcomes_003.py').read_bytes())
    analysis_plan = {
        'protocol': '23-scale-v5', 'version': '23-scale-v5-missing-outcomes-v2',
        'declared_at_utc': now, 'scheduled_pairs': 600, 'unavailable_whole_pairs': 4,
        'unavailable_outcomes': 8, 'available_pair_target': 596,
        'unavailable_request_keys': sorted(row['request_key'] for row in unavailable),
        'unavailable_case_ids': sorted({row['case_id'] for row in unavailable}),
        'analysis_source_sha256': analysis_sha, 'analysis_tests_sha256': analysis_test_sha,
        'predecessor_analysis_plan_sha256': sha((DATA / 'intervention_resume/analysis_plan.json').read_bytes()),
        'bootstrap_draws': 20000, 'bootstrap_seed': 246600,
        'complete_pair_analysis': 'Compute recovery rates, exact two-sided McNemar test and whole-pair percentile bootstrap on 596 pairs with both outcomes observed. Do not count any unavailable response as a wrong model answer.',
        'scheduled_pair_sensitivity': 'Enumerate all 256 binary assignments to the eight unknown response cells, retaining every known outcome. These are hypothetical statistical completions, never observed model answers. Bound the 600-pair repair-minus-fresh difference by (observed success difference minus four)/600 through (observed success difference plus four)/600. Calculate exact paired tests and common-random-number bootstrap endpoint envelopes for all completions.',
        'amended_claim_rule': 'Claim a repair advantage only if repair-minus-fresh is positive and the exact two-sided McNemar p-value is below 0.05 in EVERY completion. Otherwise the amended primary decision is inconclusive.',
        'selection_policy': 'Retain the same 600 selected sources, 1200 follow-up request slots and fixed dispatch order. No replacement, resampling, new model draw, prompt, feedback, source, scoring, ranking or budget change. Continue only the 780 provably unsent jobs.',
        'data_handling': 'Preserve all 1540 raw gzip files including eight pending artifacts. Overlay only unavailable status in memory. Do not invent any model output, launch confirmation, event, finish time, return code, elapsed time or usage. Recorded keys are never resubmitted.',
        'efficacy_access': 'No intervention answers, verification flags, recovery rates or arm differences were inspected before this declaration. This amendment is fixed using operational request metadata only.',
        'limit': 'This is a separate extension after a second collector interruption. Available-case results can be biased if missingness depends on runtime or dispatch order. The all-completions decision protects against the eight unknown binary outcomes within these selected cases, not generator bias or unmeasured training benefit.',
        'future_loss_policy': 'This amendment permits exactly the eight named unknown cells. Any new infrastructure failure drains the current wave and stops for independent review. No automatic expansion or retry.'}
    copies = {PUBLIC + 'prior_cache_inventory_003.json': encode({'protocol': '23-scale-v5',
                    'count': len(current), 'requests': current}),
              PUBLIC + 'process_absence_003.json': encode(proof),
              PUBLIC + 'analysis_plan.json': encode(analysis_plan),
              PUBLIC + 'second_interruption_inventory.json': (BASE / 'scale_second_interruption_inventory.json').read_bytes(),
              PUBLIC + 'previous_continuation_stdout.log': (BASE / 'detached_operational_logs/scale_intervention_resume_20261027T171453432Z_f144381d.stdout.log').read_bytes(),
              PUBLIC + 'previous_continuation_stderr.log': (BASE / 'detached_operational_logs/scale_intervention_resume_20261027T171453432Z_f144381d.stderr.log').read_bytes(),
              PUBLIC + launch_proof.name: launch_proof.read_bytes(),
              PUBLIC + evidence.name: evidence.read_bytes()}
    for name in ('scale_intervention_resume_003.py', 'test_scale_intervention_resume_003.py',
                 'scale_missing_outcomes_003.py', 'test_scale_missing_outcomes_003.py',
                 'declare_scale_intervention_resume_003.py', 'scale_detached_worker_003.py', launcher.name):
        copies[PUBLIC + 'source_snapshot/' + name] = (BASE / name).read_bytes()
    copies[PUBLIC + 'source_snapshot/scale_experiment.py'] = (DATA / 'source_snapshot/scale_experiment.py').read_bytes()
    for name in ('scale_intervention_resume.py', 'test_scale_intervention_resume.py'):
        copies[PUBLIC + 'source_snapshot/' + name] = (DATA / 'intervention_resume/source_snapshot' / name).read_bytes()
    for stem in sources:
        for suffix in ('_review.json', '_review.md', '_unit_tests.log'):
            copies[PUBLIC + stem + suffix] = (BASE / (stem + suffix)).read_bytes()

    def binding(name):
        return {'path': name, 'sha256': sha(copies[name]) if name in copies else sha((DATA / name).read_bytes())}

    protected = ['source_freeze.json', 'intervention_start_declaration.json',
                 'infrastructure_resume/amendment_001.json', 'intervention_resume/amendment_002.json',
                 'intervention_resume/continuation_start_002.json', 'main/dispatch.json',
                 'main/original_manifest.json', 'main/selection.json', 'main/protocol.json', 'main/allocation.json']
    amendment = {'protocol': '23-scale-v5', 'amendment_version': '23-scale-intervention-interruption-v2',
        'declared_at_utc': now, 'loss_observed_at_utc': proof['checked_at_utc'],
        'predecessor': binding('intervention_resume/amendment_002.json'),
        'protected_files': [binding(name) for name in protected],
        'request_plans': [binding(plan_path.relative_to(DATA).as_posix())],
        'cache_inventory': binding(PUBLIC + 'prior_cache_inventory_003.json'),
        'process_proof': binding(PUBLIC + 'process_absence_003.json'),
        'implementation': binding(PUBLIC + 'source_snapshot/scale_intervention_resume_003.py'),
        'analysis_plan': binding(PUBLIC + 'analysis_plan.json'),
        'tests': [binding(PUBLIC + 'source_snapshot/test_scale_intervention_resume_003.py'),
                  binding(PUBLIC + 'source_snapshot/test_scale_missing_outcomes_003.py')],
        'provenance_sha256': {name: sha(raw) for name, raw in copies.items()},
        'unavailable_requests': unavailable,
        'unavailable_case_ids': analysis_plan['unavailable_case_ids'],
        'unavailable_request_keys': analysis_plan['unavailable_request_keys'],
        'remaining_unsent_jobs': 780, 'recorded_arm_requests': 420, 'retained_terminal_arm_requests': 412,
        'scope': 'Continue only 780 unsent frozen jobs. Never reissue a recorded key. Preserve all 1540 prefix raw caches including the eight named pending records. New infrastructure failures drain and stop for review.',
        'scientific_handling': '596 observed complete pairs plus all 256 hypothetical completions, fixed before continuation and before efficacy access.'}
    copies[PUBLIC + 'amendment_003.json'] = encode(amendment)
    for name, raw in copies.items():
        assert not (DATA / name).exists() or (DATA / name).read_bytes() == raw, 'Existing artifact differs: ' + name
    for name, raw in copies.items():
        path = DATA / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            with path.open('xb') as stream:
                stream.write(raw)
    verified = scale_intervention_resume_003_verify(ROOT, amendment_path)
    print(json.dumps({'passed': True, 'model_calls': 0, 'raw_caches_preserved': len(current),
        'unknown_outcome_slots': len(verified['approved']), 'unsent_jobs': 780,
        'amendment_sha256': verified['amendment_sha256'], 'declared_at_utc': now}))


if __name__ == '__main__':
    main()
