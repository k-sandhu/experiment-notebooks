"""Freeze one reviewed unsent-only continuation using operational metadata only.

Do not execute until the independent source review and harmless launcher smoke
are complete. This script never launches collection or reads intervention results.
"""
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent / 'experiment_notebooks/notebooks/23-synthetic-data-curation'
DATA = ROOT / 'data/scale_v5'
PUBLIC = 'intervention_resume_005/'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)


def encode(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def main():
    from scale_intervention_resume_005 import scale_intervention_resume_005_verify, VERSION, ATTEMPT_FIELDS
    from scale_intervention_resume_004 import scale_intervention_resume_004_verify

    path = DATA / PUBLIC / 'amendment_005.json'
    if path.exists():
        state = scale_intervention_resume_005_verify(ROOT, path)
        print(json.dumps({'existing_amendment_verified': True, 'sha256': state['amendment_sha256'], 'model_calls': 0}))
        return
    assert not (DATA / 'main/manifest.json').exists(), 'Interventions are already complete'
    previous = scale_intervention_resume_004_verify(ROOT, DATA / 'intervention_resume_004/amendment_004.json')
    review = read(BASE / 'scale_intervention_resume_005_review.json')
    assert review['passed'] is True and not review['issues'] and review['model_calls'] == 0
    for field, name in (
        ('source_sha256', 'scale_intervention_resume_005.py'),
        ('tests_sha256', 'test_scale_intervention_resume_005.py'),
        ('test_log_sha256', 'scale_intervention_resume_005_unit_tests.log'),
        ('worker_sha256', 'scale_detached_worker_005.py'),
        ('worker_tests_sha256', 'test_scale_detached_worker_005.py'),
        ('worker_test_log_sha256', 'scale_detached_worker_005_unit_tests.log'),
        ('launcher_sha256', 'launch_scale_intervention_resume_005.ps1'),
        ('launcher_smoke_sha256', 'scale_detached_launcher_005_smoke.json'),
        ('declaration_sha256', Path(__file__).name)):
        assert review[field] == sha((BASE / name).read_bytes()), 'Reviewed file changed: ' + name
    smoke = read(BASE / 'scale_detached_launcher_005_smoke.json')
    assert smoke['passed'] is True and smoke['model_calls'] == 0
    assert smoke['launcher_sha256'] == review['launcher_sha256'] and smoke['worker_sha256'] == review['worker_sha256']
    evidence = BASE / 'scale_detached_launcher_005_evidence.json'
    assert smoke['evidence_sha256'] == sha(evidence.read_bytes())

    stopped = read(BASE / 'scale_intervention_004_final_inventory.json')
    current = {p.name.removesuffix('.json.gz'): sha(p.read_bytes()) for p in (DATA / 'main/cache').glob('*.json.gz')}
    assert len(current) == 2124 and current == stopped['requests']
    assert all(current.get(key) == digest for key, digest in previous['inventory'].items())
    dispatch = read(DATA / 'main/dispatch.json')['jobs']
    arm_keys = [job['request_key'] for job in dispatch]
    assert len(arm_keys) == 1200 and set(current).intersection(arm_keys) == set(arm_keys[:1004])
    assert not set(arm_keys[1004:]).intersection(current) and len(arm_keys[1004:]) == 196
    metadata_proof = read(BASE / 'error_metadata_005.json')
    key = metadata_proof['request_key']
    assert key not in previous['retained'] and key in arm_keys[536:1004]
    index = arm_keys.index(key)
    job = dispatch[index]
    plans = {row['request_key']: row for binding in previous['prior']['predecessor_state']['amendment']['request_plans'] for row in read(DATA / binding['path'])}
    plan = plans[key]
    cached = read(DATA / 'main/cache' / (key + '.json.gz'))
    assert len(cached['attempts']) == 1
    attempt = cached['attempts'][0]
    metadata = {name: attempt[name] for name in ATTEMPT_FIELDS if name in attempt}
    assert metadata_proof['cache_sha256'] == current[key] and metadata_proof['attempt_metadata'] == metadata
    assert metadata['pending'] is False and metadata['error'] and metadata['timeout_s'] == 900
    retained = list(previous['retained_transport_failures']) + [dict(
        request_key=key, cache_sha256=current[key], dispatch_index=index,
        case_id=job['case_id'], arm=job['arm'], stage=plan['stage'], sample=plan['sample'],
        content_hash=plan['source_hash'], request_input_hash=job['input_hash'], feedback_hash=job['feedback_hash'],
        error=metadata['error'], attempt_metadata=metadata,
        token_usage_field_present='token_usage' in attempt, token_usage_nonempty=bool(attempt.get('token_usage')))]
    assert len(retained) == 2
    proof = read(BASE / 'scale_intervention_process_absence_005.json')
    assert type(proof['owned_workers']) is int and proof['owned_workers'] == 0 and proof['collector_session_available'] is False
    assert type(proof['inaccessible_owned_candidates']) is int and proof['inaccessible_owned_candidates'] == 0
    supplied_stop = Path(stopped['stop_file'])
    stop = (supplied_stop if supplied_stop.is_absolute() else DATA / supplied_stop).resolve()
    assert stop.is_relative_to(DATA.resolve()) and sha(stop.read_bytes()) == stopped['stop_file_sha256']
    stop_relative = stop.relative_to(DATA.resolve()).as_posix()
    # Bind the stop bytes without inspecting wave_results or answers.
    logbase = BASE / 'detached_operational_logs/scale004_20261028T004121883Z_3395f3fc'
    finished = read(Path(str(logbase) + '.finished.json'))
    assert finished['return_code'] == 1 and finished['lease_active'] is False
    now = datetime.now(timezone.utc).isoformat()
    handling = {
        'protocol': '23-scale-v5', 'declared_at_utc': now,
        'analysis_plan_unchanged': previous['amendment']['analysis_plan'],
        'scheduled_pairs': 600, 'observed_pair_target': 596, 'unknown_outcomes': 8,
        'unknown_whole_pairs': 4, 'hypothetical_completions': 256,
        'retained_terminal_failure_request_keys': [item['request_key'] for item in retained],
        'endpoint_policy': 'Both named terminal errors are known operational non-recoveries under the frozen valid-output recovery endpoint. Nonempty request errors control the endpoint even if a parsed body, usage or zero return code exists. Preserve every recorded response and verification byte without inspecting or replacing them.',
        'diagnostic_policy': 'Retain both terminal errors in observed-pair recovery statistics. Exclude transport-derived validator flags and numeric fields from claims about actual wrong values or new field damage. Rejection logs retain both errors; accepted and preference targets cannot use them.',
        'unknown_policy': 'The same eight pending artifacts retain unknown physical-launch and outcome status. They are not wrong model answers. Keep the exact 003 complete-pair and all-256-completions plan and pure analysis implementation unchanged.',
        'spend_policy': 'The eight pending records retain unknown physical launch, outcomes and USD cost. Preserve observed usage metadata for both terminal errors without converting it to efficacy or a zero-cost assumption. USD spend remains unknown. The 196 unsent slots have no recorded attempt before continuation.',
        'collection_policy': 'Continue only 196 unsent frozen slots. Preserve all 2124 raw caches and both terminal errors. Drain and stop on every new infrastructure failure. Keep model, high reasoning, sources, selection, prompts, feedback, scoring and call budget fixed.',
        'power_safeguard': 'Reuse reviewed 004 hidden WMI worker mechanics with 005 paths. A same-thread temporary ES_CONTINUOUS | ES_SYSTEM_REQUIRED lease starts before Popen and ends on completion, failure or its 16-hour cap. No power-plan, display, away-mode, task or service change. User-initiated sleep remains possible.',
        'owned_process_safeguard': 'Assign the exact collector child to a new worker-owned kill-on-close job before publishing its PID, creation-time, script, amendment and nonce-bound startup gate. Clean only that owned job on worker failure. The lease cap releases the sleep request without terminating the collector.',
        'efficacy_access': 'Only operational metadata was inspected. No intervention predictions, verification flags, recovery rates or arm differences were accessed.'}
    copies = {
        PUBLIC + 'prior_cache_inventory_005.json': encode({'protocol': '23-scale-v5', 'count': 2124, 'requests': current}),
        PUBLIC + 'process_absence_005.json': encode(proof), PUBLIC + 'handling_plan.json': encode(handling),
        PUBLIC + 'stop_inventory.json': (BASE / 'scale_intervention_004_final_inventory.json').read_bytes(),
        PUBLIC + 'error_metadata.json': (BASE / 'error_metadata_005.json').read_bytes(),
        PUBLIC + 'previous_continuation_stdout.log': Path(str(logbase) + '.stdout.log').read_bytes(),
        PUBLIC + 'previous_continuation_stderr.log': Path(str(logbase) + '.stderr.log').read_bytes(),
        PUBLIC + 'previous_continuation_finished.json': Path(str(logbase) + '.finished.json').read_bytes(),
        PUBLIC + 'scale_detached_launcher_005_smoke.json': (BASE / 'scale_detached_launcher_005_smoke.json').read_bytes(),
        PUBLIC + evidence.name: evidence.read_bytes()}
    for name in ('scale_intervention_resume_005.py', 'test_scale_intervention_resume_005.py',
                 'scale_detached_worker_005.py', 'test_scale_detached_worker_005.py',
                 'launch_scale_intervention_resume_005.ps1', 'probe_scale_containment_child_005.py', Path(__file__).name):
        copies[PUBLIC + 'source_snapshot/' + name] = (BASE / name).read_bytes()
    # Copy only source/test dependencies needed to run the 005 mock tests. The
    # predecessor amendments bind their own history in place; do not clone it.
    for name in ('scale_intervention_resume.py', 'test_scale_intervention_resume.py',
                 'scale_intervention_resume_003.py', 'test_scale_intervention_resume_003.py',
                 'scale_intervention_resume_004.py', 'test_scale_intervention_resume_004.py'):
        copies[PUBLIC + 'source_snapshot/' + name] = (DATA / 'intervention_resume_004/source_snapshot' / name).read_bytes()
    for name in ('scale_intervention_resume_005_review.json', 'scale_intervention_resume_005_review.md',
                 'scale_intervention_resume_005_unit_tests.log', 'scale_detached_worker_005_unit_tests.log'):
        copies[PUBLIC + name] = (BASE / name).read_bytes()

    # Freeze the reviewed pre-outcome diagnostic/reporting policy and portable
    # mock-test dependencies. Final prose and delivery checklists remain posthoc.
    for name in ('scale_reporting.py', 'refresh_scale_report.py', 'test_scale_reporting_missing.py',
                 'scale_reporting_transport_005_mock_tests.log', 'scale_missing_outcomes_003.py'):
        copies[PUBLIC + 'reporting_snapshot/' + name] = (BASE / name).read_bytes()
    for name in ('scale_transport.py', 'scale_fixtures.py', 'scale_parallel.py', 'scale_experiment.py',
                 'high_fixtures.py', 'high_material_audit.py', 'audit_high_rendered_sources.py',
                 'test_scale_experiment.py', 'scale_power_plan.json'):
        copies[PUBLIC + 'reporting_snapshot/' + name] = (DATA / 'source_snapshot' / name).read_bytes()
    for name in ('replay_scale_notebook.py', 'verify_scale_delivery.py', 'test_verify_scale_recovery_003.py',
                 'test_verify_scale_recovery_004.py', 'test_verify_scale_recovery_005.py',
                 'test_replay_scale_intervention_diagnostics.py', 'scale_replay_delivery_005_unit_test_review.json'):
        copies[PUBLIC + 'qa_snapshot/' + name] = (BASE / name).read_bytes()

    def binding(name):
        return {'path': name, 'sha256': sha(copies[name]) if name in copies else sha((DATA / name).read_bytes())}

    protected = ['source_freeze.json', 'intervention_start_declaration.json', 'main/dispatch.json',
                 'main/selection.json', 'main/original_manifest.json', 'main/protocol.json', 'main/allocation.json',
                 'intervention_resume_004/amendment_004.json', 'intervention_resume_004/continuation_start_004.json']
    amendment = {
        'protocol': '23-scale-v5', 'amendment_version': VERSION, 'declared_at_utc': now,
        'loss_observed_at_utc': finished['finished_at_utc'],
        'predecessor': binding('intervention_resume_004/amendment_004.json'),
        'implementation': binding(PUBLIC + 'source_snapshot/scale_intervention_resume_005.py'),
        'analysis_plan': previous['amendment']['analysis_plan'], 'handling_plan': binding(PUBLIC + 'handling_plan.json'),
        'process_proof': binding(PUBLIC + 'process_absence_005.json'),
        'cache_inventory': binding(PUBLIC + 'prior_cache_inventory_005.json'),
        'stop_record': binding(stop_relative), 'error_metadata': binding(PUBLIC + 'error_metadata.json'),
        'protected_files': [binding(name) for name in protected],
        'tests': [binding(PUBLIC + 'source_snapshot/test_scale_intervention_resume_005.py'), binding(PUBLIC + 'source_snapshot/test_scale_detached_worker_005.py')],
        'provenance_sha256': {name: sha(raw) for name, raw in copies.items()},
        'retained_transport_failures': retained, 'retained_terminal_failure_request_keys': [item['request_key'] for item in retained],
        'unavailable_request_keys': sorted(previous['approved']),
        'unavailable_case_ids': sorted({row['case_id'] for row in previous['approved'].values()}),
        'remaining_unsent_jobs': 196, 'recorded_arm_requests': 1004, 'retained_terminal_arm_requests': 996,
        'scope': 'One continuation of only 196 unsent slots. Keep all 2124 raw caches, two named terminal errors and eight unknowns unchanged. Same 600 selected pairs, 1200 slots, model, high reasoning, four-worker waves, requests, sources, feedback and scoring. Every new infrastructure error drains and stops.',
        'scientific_handling': 'Same 596 observed pairs and all 256 completions under unchanged 003 analysis. Both terminal errors are operational non-recovery, not inferred extraction damage or new missing outcomes.'}
    copies[PUBLIC + 'amendment_005.json'] = encode(amendment)
    for name, raw in copies.items():
        assert not (DATA / name).exists() or (DATA / name).read_bytes() == raw, 'Existing artifact differs: ' + name
    for name, raw in copies.items():
        target = DATA / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            with target.open('xb') as stream:
                stream.write(raw)
    state = scale_intervention_resume_005_verify(ROOT, path)
    print(json.dumps({'passed': True, 'model_calls': 0, 'raw_cache_prefix_preserved': len(state['inventory']),
        'known_terminal_failure_keys': sorted(state['retained']), 'unknown_outcomes': len(state['approved']),
        'unsent_jobs': 196, 'amendment_sha256': state['amendment_sha256'], 'declared_at_utc': now}))


if __name__ == '__main__':
    main()
