"""Record final outcome-blind tests and metadata review before one live run."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from scale_intervention_resume_004 import scale_intervention_resume_004_verify


BASE = Path(__file__).resolve().parent
ROOT = BASE.parent / 'experiment_notebooks/notebooks/23-synthetic-data-curation'
DATA = ROOT / 'data/scale_v5'
PUBLIC = DATA / 'intervention_resume_004'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    path = PUBLIC / 'continuation_start_004.json'
    if path.exists():
        gate = read(path)
        assert all(sha(DATA / name) == digest for name, digest in gate['sha256'].items())
        print(json.dumps({'existing_gate_verified': True, 'sha256': sha(path), 'model_calls': 0}))
        return
    state = scale_intervention_resume_004_verify(ROOT, PUBLIC / 'amendment_004.json')
    review = read(BASE / 'scale_intervention_resume_004_preflight.json')
    assert review['passed'] is True and review['model_calls'] == 0
    assert review['amendment_sha256'] == state['amendment_sha256']
    assert review.get('efficacy_reads', False) is False
    assert not (DATA / 'main/manifest.json').exists()
    assert not list((DATA / 'main').glob('intervention_resume_004_start_*.json'))
    integration = read(BASE / 'scale_cached_ancestors_004_integration.json')
    assert integration['passed'] is True and integration['amendment_sha256'] == state['amendment_sha256']
    assert integration['model_calls'] == integration['subprocesses_started'] == integration['network_connections'] == 0
    assert integration['intervention_stage_run'] is False and integration['intervention_efficacy_accessed'] is False
    assert integration['all_v5_raw_caches_unchanged'] is True
    assert integration['pilot_cases_replayed'] == 32
    assert integration['collection_originals_replayed'] == 1024 and integration['audit_originals_replayed'] == 96
    for name in ('scale_intervention_resume_004_preflight.json', 'scale_intervention_resume_004_preflight.md',
                 'scale_intervention_resume_004_packaged_unit_tests.log',
                 'scale_detached_worker_004_packaged_unit_tests.log',
                 'scale_cached_ancestors_004_integration.json', 'scale_cached_ancestors_004_integration.log'):
        source = BASE / name
        if name.endswith('_tests.log'):
            text = source.read_text(encoding='utf-8')
            assert '\nOK\n' in text and 'FAILED' not in text
        target = PUBLIC / name
        assert not target.exists() or target.read_bytes() == source.read_bytes()
        if not target.exists():
            with target.open('xb') as stream:
                stream.write(source.read_bytes())
    for name in (Path(__file__).name, 'check_scale_cached_ancestors_004.py'):
        source, target = BASE / name, PUBLIC / 'qa_snapshot' / name
        assert not target.exists() or target.read_bytes() == source.read_bytes()
        if not target.exists():
            with target.open('xb') as stream:
                stream.write(source.read_bytes())
    prior = DATA / 'intervention_resume_003/continuation_start_003.json'
    bindings = dict(read(prior)['sha256'])
    bindings[prior.relative_to(DATA).as_posix()] = sha(prior)
    for item in sorted(PUBLIC.rglob('*')):
        if item.is_file() and item != path and '__pycache__' not in item.parts and item.suffix != '.pyc':
            bindings[item.relative_to(DATA).as_posix()] = sha(item)
    assert all(sha(DATA / name) == digest for name, digest in bindings.items())
    gate = {'protocol': '23-scale-v5', 'phase': 'terminal_timeout_continuation',
            'declared_at_utc': datetime.now(timezone.utc).isoformat(),
            'amendment_sha256': state['amendment_sha256'], 'model_calls': 0, 'efficacy_reads': False,
            'recorded_raw_caches_preserved': len(state['inventory']),
            'unavailable_request_keys': sorted(state['approved']),
            'retained_terminal_timeout_keys': sorted(state['retained']), 'unsent_jobs': 664,
            'sha256': bindings,
            'scope': 'One reviewed continuation of unsent frozen requests only; no recorded request key resubmitted.'}
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(gate, stream, sort_keys=True, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'passed': True, 'bindings': len(bindings), 'sha256': sha(path),
                      'amendment_sha256': state['amendment_sha256'], 'model_calls': 0}))


if __name__ == '__main__':
    main()
