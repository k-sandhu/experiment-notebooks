"""Check the historical byte boundary, offline outputs, and guarded D: delivery."""
import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
FOLDER = BASE.parent / 'experiment_notebooks/notebooks/23-synthetic-data-curation'
DESTINATION = Path(r'D:\projects\experiment_notebooks\notebooks\23-synthetic-data-curation')
BASELINE = json.loads((BASE / 'high_baseline_manifest.json').read_text(encoding='utf-8'))
EXPLANATIONS = {'README.md', '23_synthetic_data_curation.ipynb'}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def files(folder):
    return {p.relative_to(folder).as_posix(): p for p in folder.rglob('*') if p.is_file()
            and not {'__pycache__', '.ipynb_checkpoints', 'tmp'}.intersection(p.relative_to(folder).parts)
            and p.suffix != '.pyc'}


def verify():
    historical = {name: value for name, value in BASELINE['files'].items() if name not in EXPLANATIONS}
    changed = [name for name, value in historical.items() if not (FOLDER / name).exists()
               or digest(FOLDER / name) != value]
    if changed:
        raise AssertionError('Historical data/figure changes: ' + ', '.join(changed))
    import nbformat
    notebook = nbformat.read(FOLDER / '23_synthetic_data_curation.ipynb', as_version=4)
    nbformat.validate(notebook)
    code = [cell for cell in notebook.cells if cell.cell_type == 'code']
    if any(cell.execution_count is None for cell in code):
        raise AssertionError('The notebook contains unexecuted code cells')
    if any(output.output_type == 'error' for cell in code for output in cell.outputs):
        raise AssertionError('Notebook contains an error output')
    counts = [cell.execution_count for cell in code]
    if counts != list(range(1, len(code) + 1)):
        raise AssertionError('Execution counts do not show one top-to-bottom replay')
    report = json.loads((FOLDER / 'data/high_v4/artifact_audit.json').read_text(encoding='utf-8'))
    if not report['passed'] or not report['main_complete']:
        raise AssertionError('Final artifact audit is incomplete')
    current = files(FOLDER)
    return {'checked_at_utc': datetime.now(timezone.utc).isoformat(),
            'historical_files_unchanged': len(historical), 'code_cells_executed_in_order': len(code),
            'files_for_delivery': len(current), 'artifact_audit_passed': True}


def deliver():
    result = verify()
    source_files = files(FOLDER)
    target_files = files(DESTINATION) if DESTINATION.exists() else {}
    conflicts = []
    for name, target in target_files.items():
        if name not in source_files:
            continue
        current_hash = digest(target)
        if current_hash not in {BASELINE['files'].get(name), digest(source_files[name])}:
            conflicts.append(name)
    if conflicts:
        raise RuntimeError('Delivery would overwrite user changes: ' + ', '.join(conflicts))
    for name, source in source_files.items():
        destination = DESTINATION / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.exists() or digest(destination) != digest(source):
            shutil.copy2(source, destination)
    mismatches = [name for name, source in source_files.items()
                  if not (DESTINATION / name).exists() or digest(DESTINATION / name) != digest(source)]
    if mismatches:
        raise AssertionError('Source/destination mismatches: ' + ', '.join(mismatches))
    return {**result, 'destination': str(DESTINATION), 'all_source_files_match_delivery': True,
            'unrelated_destination_files_preserved': len(set(target_files) - set(source_files))}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--deliver', action='store_true')
    args = parser.parse_args()
    result = deliver() if args.deliver else verify()
    (BASE / 'high_delivery_validation.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(result, indent=2))
