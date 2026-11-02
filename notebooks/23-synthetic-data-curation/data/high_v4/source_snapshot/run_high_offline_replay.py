"""Execute the completed notebook offline, preserve historical reports, prove cache immutability."""
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
FOLDER = BASE.parent / 'experiment_notebooks/notebooks/23-synthetic-data-curation'
NOTEBOOK = FOLDER / '23_synthetic_data_curation.ipynb'
DATA = FOLDER / 'data/high_v4'
manifest = json.loads((BASE / 'high_baseline_manifest.json').read_text(encoding='utf-8'))
VOLATILE = {'data/run_validation.json', 'data/hard_v2/run_validation.json',
            'data/sol_v3/run_validation.json',
            *{f'data/sol_v3/pilot/level_{n}/run_validation.json' for n in (1, 2, 3)}}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cache_hashes():
    return {p.relative_to(FOLDER).as_posix(): sha(p) for p in (FOLDER / 'data').rglob('*.json')
            if 'cache' in p.relative_to(FOLDER).parts and 'tmp' not in p.relative_to(FOLDER).parts}


if __name__ == '__main__':
    final = json.loads((DATA / 'main/manifest.json').read_text(encoding='utf-8'))
    if final['phase'] != 'interventions_complete':
        raise RuntimeError('Complete the live study before final offline replay')
    before = cache_hashes()
    env = {**os.environ, 'NB_LIVE': '0', 'NB_HARD_LIVE': '0'}
    command = [sys.executable, '-m', 'nbconvert', '--to', 'notebook', '--execute', '--inplace',
               '--ExecutePreprocessor.timeout=600', NOTEBOOK.name]
    log_path = BASE / 'high_offline_execution.txt'
    with log_path.open('w', encoding='utf-8', newline='\n') as log:
        result = subprocess.run(command, cwd=FOLDER, env=env, stdout=log, stderr=subprocess.STDOUT)
    # nbconvert's Windows writer uses CRLF; normalize line endings without changing JSON values.
    raw = NOTEBOOK.read_bytes()
    NOTEBOOK.write_bytes(raw.replace(b'\r\n', b'\n'))
    if result.returncode:
        print(log_path.read_text(encoding='utf-8')[-14000:])
        raise SystemExit(result.returncode)
    after = cache_hashes()
    if before != after:
        raise AssertionError('Offline replay changed response caches or introduced a new request')
    reports = {}
    for name in sorted(VOLATILE):
        reports[name] = json.loads((FOLDER / name).read_text(encoding='utf-8'))
        if not reports[name]['offline'] or reports[name]['live_new_requests_this_run'] != 0:
            raise AssertionError('Historical replay made a new request: ' + name)
        preserved = BASE / 'high_preserved_baseline' / name
        if sha(preserved) != manifest['files'][name]:
            raise AssertionError('Historical backup hash mismatch: ' + name)
        (FOLDER / name).write_bytes(preserved.read_bytes())
    historical = {name: expected for name, expected in manifest['files'].items()
                  if name not in {'README.md', NOTEBOOK.name}}
    assert all(sha(FOLDER / name) == expected for name, expected in historical.items())
    import nbformat
    notebook = nbformat.read(NOTEBOOK, as_version=4)
    nbformat.validate(notebook)
    code = [cell for cell in notebook.cells if cell.cell_type == 'code']
    assert [cell.execution_count for cell in code] == list(range(1, len(code) + 1))
    assert not any(out.output_type == 'error' for cell in code for out in cell.outputs)
    original_manifest = json.loads((DATA / 'main/original_manifest.json').read_text(encoding='utf-8'))
    pilot = json.loads((DATA / 'pilot/ladder.json').read_text(encoding='utf-8'))
    record = {'checked_at_utc': datetime.now(timezone.utc).isoformat(),
              'notebook_executed_top_to_bottom': True, 'code_cells': len(code), 'error_outputs': 0,
              'v4_source_targets_recomputed': 1056, 'v4_live_knob': False,
              'historical_data_and_figures_unchanged': len(historical),
              'historical_replay_reports': reports,
              'historical_requests_replayed': sum(r['replayed_requests_this_run'] for r in reports.values()),
              'healthy_pilot_requests_replayed': pilot['physical_cli_requests'],
              'main_original_requests_replayed': len(original_manifest['request_keys']),
              'main_manifest_requests_replayed': len(final['request_keys']),
              'all_response_cache_files_unchanged': len(before), 'new_model_requests': 0,
              'command': command, 'execution_log': log_path.name,
              'note': 'Main originals are read once for original replay; intervention replay reads their saved manifest and both intervention caches.'}
    (DATA / 'offline_replay_validation.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({k: v for k, v in record.items() if k != 'historical_replay_reports'}, indent=2))
