"""Bind one cached timeout and a reviewed continuation without reading efficacy."""
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path


BASE = Path(__file__).resolve().parent
ROOT = BASE.parent / 'experiment_notebooks/notebooks/23-synthetic-data-curation'
DATA = ROOT / 'data/scale_v5'
PUBLIC = 'intervention_resume_004/'
FAILED_KEY = '64a7643d257313d72af7aaf9ce1740f3399778233508012e65524da897385129'
FAILED_SHA = 'd0db3c3dfa53fe3d056b107f757673e9103e8b6a7bdc652c0c95a2ae42b68c13'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)


def encode(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def main():
    from scale_intervention_resume_004 import scale_intervention_resume_004_verify, ATTEMPT_FIELDS
    from scale_intervention_resume_003 import scale_intervention_resume_003_verify

    path = DATA / PUBLIC / 'amendment_004.json'
    if path.exists():
        state = scale_intervention_resume_004_verify(ROOT, path)
        print(json.dumps({'existing_amendment_verified': True, 'sha256': state['amendment_sha256'], 'model_calls': 0}))
        return
    assert not (DATA / 'main/manifest.json').exists(), 'Interventions are already complete'
    previous = scale_intervention_resume_003_verify(ROOT, DATA / 'intervention_resume_003/amendment_003.json')
    review = read(BASE / 'scale_intervention_resume_004_review.json')
    assert review['passed'] is True and not review['issues'] and review['model_calls'] == 0
    for field, name in (
        ('source_sha256', 'scale_intervention_resume_004.py'),
        ('tests_sha256', 'test_scale_intervention_resume_004.py'),
        ('test_log_sha256', 'scale_intervention_resume_004_unit_tests.log'),
        ('worker_sha256', 'scale_detached_worker_004.py'),
        ('worker_tests_sha256', 'test_scale_detached_worker_004.py'),
        ('worker_test_log_sha256', 'scale_detached_worker_004_unit_tests.log'),
        ('launcher_sha256', 'launch_scale_intervention_resume_004.ps1'),
        ('launcher_smoke_sha256', 'scale_detached_launcher_004_smoke.json'),
        ('declaration_sha256', Path(__file__).name)):
        assert review[field] == sha((BASE / name).read_bytes()), 'Reviewed file changed: ' + name
    smoke = read(BASE / 'scale_detached_launcher_004_smoke.json')
    assert smoke['passed'] is True and smoke['model_calls'] == 0
    assert smoke['launcher_sha256'] == review['launcher_sha256']
    assert smoke['worker_sha256'] == review['worker_sha256']
    evidence = BASE / 'scale_detached_launcher_004_evidence.json'
    assert smoke['evidence_sha256'] == sha(evidence.read_bytes())

    stopped = read(BASE / 'scale_intervention_003_stop_inventory.json')
    current = {p.name.removesuffix('.json.gz'): sha(p.read_bytes())
               for p in (DATA / 'main/cache').glob('*.json.gz')}
    assert len(current) == 1656 and current == stopped['requests']
    assert all(current.get(key) == digest for key, digest in previous['inventory'].items())
    dispatch = read(DATA / 'main/dispatch.json')['jobs']
    arm_keys = [job['request_key'] for job in dispatch]
    assert len(arm_keys) == 1200 and set(current).intersection(arm_keys) == set(arm_keys[:536])
    assert not set(arm_keys[536:]).intersection(current) and len(arm_keys[536:]) == 664
    job = dispatch[535]
    assert job['request_key'] == FAILED_KEY and current[FAILED_KEY] == FAILED_SHA
    plan_paths = previous['predecessor_state']['amendment']['request_plans']
    plans = {row['request_key']: row for binding in plan_paths for row in read(DATA / binding['path'])}
    plan = plans[FAILED_KEY]
    cached = read(DATA / 'main/cache' / (FAILED_KEY + '.json.gz'))
    assert len(cached['attempts']) == 1
    attempt = cached['attempts'][0]
    metadata = {key: attempt[key] for key in ATTEMPT_FIELDS if key in attempt}
    error_metadata = read(BASE / 'scale_intervention_003_error_metadata.json')
    assert error_metadata['request_key'] == FAILED_KEY and error_metadata['cache_sha256'] == FAILED_SHA
    assert error_metadata['attempt_metadata'] == metadata
    assert metadata['error'] == 'Codex CLI exceeded timeout of 900 seconds'
    assert metadata['pending'] is False and metadata['timed_out'] is True and metadata['timeout_s'] == 900
    assert metadata['return_code'] == 0
    retained = {'request_key': FAILED_KEY, 'cache_sha256': FAILED_SHA, 'dispatch_index': 535,
                'case_id': job['case_id'], 'arm': job['arm'], 'stage': plan['stage'], 'sample': plan['sample'],
                'content_hash': plan['source_hash'], 'request_input_hash': job['input_hash'],
                'feedback_hash': job['feedback_hash'], 'error': metadata['error'],
                'attempt_metadata': metadata, 'token_usage_field_present': 'token_usage' in attempt,
                'token_usage_nonempty': bool(attempt.get('token_usage'))}
    proof = read(BASE / 'scale_intervention_process_absence_004.json')
    assert proof['owned_workers'] == 0 and proof['collector_session_available'] is False
    assert proof['inaccessible_owned_candidates'] == 0
    supplied_stop = Path(stopped['stop_file'])
    stop = (supplied_stop if supplied_stop.is_absolute() else DATA / supplied_stop).resolve()
    assert stop.is_relative_to(DATA.resolve()) and sha(stop.read_bytes()) == stopped['stop_sha256']
    stop_relative = stop.relative_to(DATA.resolve()).as_posix()
    # Bind/copy stop and stderr as bytes. Never inspect wave_results or predictions.
    logbase = BASE / 'detached_operational_logs/scale003_20261027T212445936Z_81659ae6'
    now = datetime.now(timezone.utc).isoformat()
    handling = {'protocol': '23-scale-v5', 'declared_at_utc': now,
        'analysis_plan_unchanged': previous['amendment']['analysis_plan'],
        'scheduled_pairs': 600, 'observed_pair_target': 596, 'unknown_outcomes': 8,
        'unknown_whole_pairs': 4, 'hypothetical_completions': 256,
        'retained_terminal_failure_request_keys': [FAILED_KEY],
        'endpoint_policy': 'The frozen valid-output recovery endpoint counts the recorded timeout as a known non-recovery. Return code zero, usage or a retained parsed body cannot override the nonempty request error. Do not inspect or replace the recorded answer, rescore it as an extraction failure, or request another draw.',
        'diagnostic_policy': 'Keep the transport row in observed-pair recovery statistics. Exclude transport-derived validator flags and numeric fields from claims about actual wrong values or new field damage. Raw rows, metadata, error and elapsed time remain unchanged. Rejection logs retain it; accepted/preference targets cannot use it.',
        'unknown_policy': 'The same eight pending artifacts retain unknown physical-launch and outcome status. They are not wrong model answers. The exact 003 complete-pair plus all-256-completions plan and pure analysis code remain unchanged.',
        'spend_policy': 'The eight pre-Popen markers have unknown physical launch, outcome and USD cost. The new terminal timeout has nonempty recorded CLI usage, which may contribute observed token components without double counting; it does not establish USD spend. CLI dollar spend remains unknown, not zero. The 664 unsent slots have no recorded attempt before continuation.',
        'collection_policy': 'Continue only 664 previously unsent frozen slots. Retain all 1656 existing raw caches. Stop/drain on any new infrastructure error. No request, source, ranking, feedback, scoring, model or call-budget change.',
        'power_safeguard': 'A separate reviewed hidden worker acquires a temporary ES_CONTINUOUS | ES_SYSTEM_REQUIRED request during launch preparation before Popen, then holds it while supervising its exact collector child, with a 16-hour maximum lease. No display or away-mode request, power-plan change, task or service installation. It clears on launch failure, completion, failure or lease cap. User-initiated sleep remains possible.',
        'owned_process_safeguard': 'Before live dispatch the worker assigns the collector to its own kill-on-close job and writes a unique PID/creation/amendment-bound ready gate. The job owns descendants and is independent of the app tool job. Failure cleans only this owned job. Releasing the sleep lease at its time cap does not kill the collector.',
        'documentation_checked': '2026-10-27 America/Toronto',
        'documentation': ['https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate',
                          'https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-assignprocesstojobobject',
                          'https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_basic_limit_information'],
        'efficacy_access': 'No intervention predictions, verification flags, recovery rates or arm differences have been inspected. This amendment uses operational metadata only.'}
    copies = {PUBLIC + 'prior_cache_inventory_004.json': encode({'protocol': '23-scale-v5', 'count': 1656, 'requests': current}),
              PUBLIC + 'process_absence_004.json': encode(proof),
              PUBLIC + 'handling_plan.json': encode(handling),
              PUBLIC + 'stop_inventory.json': (BASE / 'scale_intervention_003_stop_inventory.json').read_bytes(),
              PUBLIC + 'error_metadata.json': (BASE / 'scale_intervention_003_error_metadata.json').read_bytes(),
              PUBLIC + 'sleep_event_001.json': (BASE / 'scale_intervention_003_sleep_event_001.json').read_bytes(),
              PUBLIC + 'previous_continuation_stdout.log': Path(str(logbase) + '.stdout.log').read_bytes(),
              PUBLIC + 'previous_continuation_stderr.log': Path(str(logbase) + '.stderr.log').read_bytes(),
              PUBLIC + 'previous_continuation_finished.json': Path(str(logbase) + '.finished.json').read_bytes(),
              PUBLIC + 'scale_detached_launcher_004_smoke.json': (BASE / 'scale_detached_launcher_004_smoke.json').read_bytes(),
              PUBLIC + evidence.name: evidence.read_bytes()}
    for name in ('scale_intervention_resume_004.py', 'test_scale_intervention_resume_004.py',
                 'scale_detached_worker_004.py', 'test_scale_detached_worker_004.py',
                 'launch_scale_intervention_resume_004.ps1', 'probe_scale_containment_child_004.py', Path(__file__).name):
        copies[PUBLIC + 'source_snapshot/' + name] = (BASE / name).read_bytes()
    for name in ('scale_intervention_resume.py', 'test_scale_intervention_resume.py',
                 'scale_intervention_resume_003.py', 'test_scale_intervention_resume_003.py'):
        copies[PUBLIC + 'source_snapshot/' + name] = (DATA / 'intervention_resume_003/source_snapshot' / name).read_bytes()
    for name in ('scale_intervention_resume_004_review.json', 'scale_intervention_resume_004_review.md',
                 'scale_intervention_resume_004_unit_tests.log', 'scale_detached_worker_004_unit_tests.log'):
        copies[PUBLIC + name] = (BASE / name).read_bytes()
    # Freeze the pre-outcome diagnostic policy implementation separately from
    # the final presentation, which may still need editorial repairs after QA.
    for name in ('scale_reporting.py', 'refresh_scale_report.py', 'scale_missing_outcomes_003.py',
                 'test_scale_reporting_missing.py', 'scale_reporting_transport_004_unit_tests.log'):
        copies[PUBLIC + 'reporting_snapshot/' + name] = (BASE / name).read_bytes()
    for name in ('scale_transport.py', 'scale_fixtures.py', 'scale_parallel.py', 'scale_experiment.py',
                 'high_fixtures.py', 'high_material_audit.py', 'audit_high_rendered_sources.py',
                 'test_scale_experiment.py', 'scale_power_plan.json'):
        copies[PUBLIC + 'reporting_snapshot/' + name] = (DATA / 'source_snapshot' / name).read_bytes()
    for name in ('replay_scale_notebook.py', 'verify_scale_delivery.py',
                 'test_replay_scale_intervention_diagnostics.py', 'test_verify_scale_recovery_004.py',
                 'scale_replay_delivery_004_unit_tests.log'):
        copies[PUBLIC + 'qa_snapshot/' + name] = (BASE / name).read_bytes()

    def binding(name):
        return {'path': name, 'sha256': sha(copies[name]) if name in copies else sha((DATA / name).read_bytes())}

    protected = ['source_freeze.json', 'intervention_start_declaration.json', 'main/dispatch.json',
                 'main/selection.json', 'main/original_manifest.json', 'main/protocol.json', 'main/allocation.json',
                 'intervention_resume_003/amendment_003.json', 'intervention_resume_003/continuation_start_003.json']
    amendment = {'protocol': '23-scale-v5', 'amendment_version': '23-scale-intervention-timeout-continuation-v1',
        'declared_at_utc': now, 'loss_observed_at_utc': proof['checked_at_utc'],
        'predecessor': binding('intervention_resume_003/amendment_003.json'),
        'implementation': binding(PUBLIC + 'source_snapshot/scale_intervention_resume_004.py'),
        'analysis_plan': previous['amendment']['analysis_plan'],
        'handling_plan': binding(PUBLIC + 'handling_plan.json'),
        'process_proof': binding(PUBLIC + 'process_absence_004.json'),
        'cache_inventory': binding(PUBLIC + 'prior_cache_inventory_004.json'),
        'stop_record': binding(stop_relative), 'sleep_event': binding(PUBLIC + 'sleep_event_001.json'),
        'error_metadata': binding(PUBLIC + 'error_metadata.json'),
        'protected_files': [binding(name) for name in protected],
        'tests': [binding(PUBLIC + 'source_snapshot/test_scale_intervention_resume_004.py'),
                  binding(PUBLIC + 'source_snapshot/test_scale_detached_worker_004.py')],
        'provenance_sha256': {name: sha(raw) for name, raw in copies.items()},
        'retained_transport_failures': [retained], 'retained_terminal_failure_request_keys': [FAILED_KEY],
        'unavailable_request_keys': sorted(previous['approved']),
        'unavailable_case_ids': sorted({row['case_id'] for row in previous['approved'].values()}),
        'remaining_unsent_jobs': 664, 'recorded_arm_requests': 536, 'retained_terminal_arm_requests': 528,
        'scope': 'One continuation of only 664 unsent slots. Retain every recorded key and the terminal timeout unchanged. Same 600 selected pairs, 1200 follow-up slots, model, high reasoning, four-worker waves, prompts, feedback and scoring. Any new infrastructure error drains and stops.',
        'scientific_handling': 'Same 596 observed-pair and all-256-completions analysis. The known transport timeout is operational non-recovery, not an inferred wrong extraction value or a new missing outcome.'}
    copies[PUBLIC + 'amendment_004.json'] = encode(amendment)
    for name, raw in copies.items():
        assert not (DATA / name).exists() or (DATA / name).read_bytes() == raw, 'Existing artifact differs: ' + name
    for name, raw in copies.items():
        target = DATA / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            with target.open('xb') as stream:
                stream.write(raw)
    state = scale_intervention_resume_004_verify(ROOT, path)
    print(json.dumps({'passed': True, 'model_calls': 0, 'raw_cache_prefix_preserved': len(state['inventory']),
        'known_terminal_failure_keys': sorted(state['retained']), 'unknown_outcomes': len(state['approved']),
        'unsent_jobs': 664, 'amendment_sha256': state['amendment_sha256'], 'declared_at_utc': now}))


if __name__ == '__main__':
    main()
