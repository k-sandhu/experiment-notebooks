"""Declare the reviewed infrastructure-only continuation before new calls."""
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path

from scale_resume import scale_resume_load, scale_resume_verify

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent / 'experiment_notebooks/notebooks/23-synthetic-data-curation'
DATA = ROOT / 'data/scale_v5'
DEST = DATA / 'infrastructure_resume'
KEY = '914927327569cbc503218237464f5b516a3caeff4b3e5b4ce82e57c98ae1311d'
HELPER_SHA = '62d55e98fd877d518c187650caaf9fbbde3c01cdd86da15d65d276352cecd7ef'
TEST_SHA = '02d63e62c5ce1836f9bf01a3e090a915785cb01104600b33a37397e6373daf84'
CACHE_SHA = 'b6fcc0e73ee39665de4da0a6d4f7387744fe62f5a96b0c7675bcbb6d4d0dab64'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)+'\n').encode('utf-8')


def main():
    amendment_path = DEST / 'amendment_001.json'
    namespace = scale_resume_load(ROOT)
    if amendment_path.exists():
        state = scale_resume_verify(ROOT, amendment_path, namespace)
        print(json.dumps({'existing_amendment_verified': True, 'sha256': state['amendment_sha256']}))
        return
    assert sha((BASE/'scale_resume.py').read_bytes()) == HELPER_SHA
    assert sha((BASE/'test_scale_resume.py').read_bytes()) == TEST_SHA
    review = read(BASE/'scale_resume_implementation_review.json')
    assert review['passed'] and review['source_sha256'] == HELPER_SHA and review['tests_sha256'] == TEST_SHA
    assert review['live_model_calls'] == review['data_mutations'] == 0
    assert not (DATA/'main/original_manifest.json').exists()
    assert not (DATA/'main/selection.json').exists()
    assert not (DATA/'main/manifest.json').exists()
    cache_paths = sorted((DATA/'main/cache').glob('*.json.gz'))
    assert len(cache_paths) == 696
    inventory = {'protocol': '23-scale-v5', 'count': len(cache_paths), 'requests': {}}
    latest_finish = None
    for path in cache_paths:
        value = read(path)
        key = value['key']
        assert path.name == key+'.json.gz' and len(value['attempts']) == 1
        attempt = value['attempts'][0]
        assert attempt['pending'] is False
        assert value['request']['stage'] == 'generate' and value['request']['sample'] == 0
        finish = datetime.fromisoformat(attempt['finished_at'])
        latest_finish = max(latest_finish, finish) if latest_finish else finish
        inventory['requests'][key] = sha(path.read_bytes())
    assert inventory['requests'][KEY] == CACHE_SHA
    stop_raw = (DATA/'main/infrastructure_stop.json').read_bytes()
    stop = json.loads(stop_raw)
    failure = next(row for row in stop['wave_results'] if row['request_key'] == KEY)
    row = failure['row']
    stop_sha = sha(stop_raw)
    assert len(stop['completed_prior_wave_request_keys']) == 180
    assert len(stop['wave_results']) == 4 and stop['remaining_jobs_not_dispatched'] == 72
    plans = sorted((DATA/'main/request_plans').glob('*.json'))
    assert sorted(len(read(path)) for path in plans) == [256, 512]
    assert not set(inventory['requests']) - {job['request_key'] for path in plans for job in read(path)}
    copies = {'main/infrastructure_history/stop_001.json': stop_raw,
              'infrastructure_resume/prior_cache_inventory_001.json': encoded(inventory)}
    for name in ('scale_resume.py', 'test_scale_resume.py', 'declare_scale_resume.py'):
        copies['infrastructure_resume/source_snapshot/'+name] = (BASE/name).read_bytes()
    for name in ('scale_infrastructure_resume_review.json', 'scale_infrastructure_resume_review.md',
                 'scale_resume_implementation_review.json', 'scale_resume_implementation_review.md',
                 'scale_resume_unit_tests.log'):
        copies['infrastructure_resume/'+name] = (BASE/name).read_bytes()
    declared = datetime.now(timezone.utc)
    assert declared > latest_finish
    protected = ['preregistration.json', 'main_start_declaration.json', 'main/protocol.json', 'main/allocation.json']
    amendment = {
        'protocol': '23-scale-v5', 'amendment_version': '23-scale-capacity-continuation-v1',
        'declared_at_utc': declared.isoformat(), 'phase': 'reviewed_originals_continuation_before_interventions',
        'source_freeze_sha256': sha((DATA/'source_freeze.json').read_bytes()),
        'original_stop_sha256': stop_sha,
        'protected_files': [{'path': name, 'sha256': sha((DATA/name).read_bytes())} for name in protected],
        'request_plans': [{'path': path.relative_to(DATA).as_posix(), 'sha256': sha(path.read_bytes())} for path in plans],
        'archived_stops': [{'path': 'main/infrastructure_history/stop_001.json', 'sha256': stop_sha}],
        'cache_inventory': {'path': 'infrastructure_resume/prior_cache_inventory_001.json',
                            'sha256': sha(copies['infrastructure_resume/prior_cache_inventory_001.json'])},
        'implementation': {'path': 'infrastructure_resume/source_snapshot/scale_resume.py', 'sha256': HELPER_SHA,
                           'tests_path': 'infrastructure_resume/source_snapshot/test_scale_resume.py', 'tests_sha256': TEST_SHA,
                           'mocked_tests_passed': 13},
        'provenance_sha256': {name: sha(raw) for name, raw in copies.items()},
        'reviewed_failures': [{'request_key': KEY, 'cache_sha256': CACHE_SHA,
            'transport_error': row['transport_error'], 'case_id': row['case_id'],
            'content_hash': row['content_hash'], 'request_input_hash': row['request_input_hash'], 'stop_sha256': stop_sha,
            'profile': {'model': 'gpt-6.1-sol', 'reasoning_effort': 'high', 'stage': 'generate',
                        'sample': 0, 'protocol': '23-scale-v5', 'timeout_s': 900}}],
        'scope': 'Replay all 696 terminal attempts from unchanged caches. Never reissue a recorded request. Submit only the 72 unsent positions of the interrupted frozen chunk, then apply the original complete-chunk stopping rule and fixed audit.',
        'unchanged': ['source documents', 'instructions', 'model alias and high reasoning', 'CLI request profile',
                      '900-second timeout', 'four-worker waves and order', 'schema and value checker', 'seeds and ranking',
                      '600 genuine-failure target', '2048 collection-slot cap', '96 audit cases', '3376 total request ceiling',
                      'paired intervention plan and primary analysis'],
        'new_failure_policy': 'Drain the current wave and stop on any new infrastructure failure. Preserve the original stop and all raw caches. No automatic allowlist expansion or resubmission.',
        'limits': 'The original protocol had no infrastructure-resume clause. This separate amendment follows a capacity stop after some original outcomes were observed, but precedes every intervention outcome. The model alias is not an immutable checkpoint.'}
    copies['infrastructure_resume/amendment_001.json'] = encoded(amendment)
    # Preflight every target before any write. Existing bytes may only match.
    for name, raw in copies.items():
        target = DATA/name
        assert not target.exists() or target.read_bytes() == raw, 'Existing artifact differs: '+name
    for name, raw in copies.items():
        target = DATA/name
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            with target.open('xb') as stream:
                stream.write(raw)
    state = scale_resume_verify(ROOT, amendment_path, namespace)
    print(json.dumps({'passed': True, 'model_calls': 0, 'raw_caches_bound': len(cache_paths),
                      'reviewed_terminal_failures': len(state['approved']), 'unsent_current_chunk': 72,
                      'declared_at_utc': declared.isoformat(), 'amendment_sha256': state['amendment_sha256']}))


if __name__ == '__main__':
    main()
