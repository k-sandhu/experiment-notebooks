"""Replay only already-public pilot/original stages in a disposable clone."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

from scale_intervention_resume_004 import scale_intervention_resume_004_install
from verify_scale_delivery import scale_qa_files


BASE = Path(__file__).resolve().parent
SOURCE = BASE.parent / 'experiment_notebooks/notebooks/23-synthetic-data-curation'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cache_index(root):
    return {p.relative_to(root).as_posix(): sha(p) for p in (root / 'data/scale_v5').glob('**/cache/*.json.gz')}


def main():
    scratch = BASE / 'scale_cached_ancestor_qa'
    scratch.mkdir(exist_ok=True)
    clone = Path(tempfile.mkdtemp(prefix='004_', dir=scratch)).resolve()
    assert clone.is_relative_to(scratch.resolve()) and clone != SOURCE.resolve()
    for relative, path in scale_qa_files(SOURCE).items():
        target = clone / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    before_source, before_clone = cache_index(SOURCE), cache_index(clone)
    assert before_source == before_clone
    blocked = {'subprocesses': 0, 'network_connections': 0}

    def guard(event, args):
        if event == 'subprocess.Popen':
            blocked['subprocesses'] += 1
            raise RuntimeError('Cached-ancestor integration forbids every subprocess')
        if event in ('socket.connect', 'socket.getaddrinfo'):
            blocked['network_connections'] += 1
            raise RuntimeError('Cached-ancestor integration forbids network access')

    sys.addaudithook(guard)
    state = scale_intervention_resume_004_install(clone, clone / 'data/scale_v5/intervention_resume_004/amendment_004.json')
    namespace = state['namespace']
    pilot = namespace['scale_run_pilot'](root=clone, live=False)
    originals = namespace['scale_collect_originals'](root=clone, live=False)
    assert originals['manifest']['phase'] == 'originals_complete'
    assert originals['manifest']['n_collection'] == 1024 and originals['manifest']['n_audit'] == 96
    assert len(originals['candidates']) == 1120
    assert cache_index(clone) == before_clone and cache_index(SOURCE) == before_source
    assert not (clone / 'data/scale_v5/main/manifest.json').exists()
    assert blocked == {'subprocesses': 0, 'network_connections': 0}
    report = {'checked_at_utc': datetime.now(timezone.utc).isoformat(), 'passed': True,
              'clone': str(clone), 'amendment_sha256': state['amendment_sha256'],
              'selected_tier': pilot['selected_tier'], 'pilot_cases_replayed': 32,
              'collection_originals_replayed': 1024, 'audit_originals_replayed': 96,
              'all_v5_raw_caches_unchanged': True, 'cache_files_checked': len(before_clone),
              'model_calls': 0, 'subprocesses_started': 0, 'network_connections': 0,
              'intervention_stage_run': False, 'intervention_efficacy_accessed': False,
              'note': 'Only prior published pilot/original outcomes were replayed. No intervention predictions, verification flags or recovery rates were inspected. Source-folder bytes were not modified.'}
    (BASE / 'scale_cached_ancestors_004_integration.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
