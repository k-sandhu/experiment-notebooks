"""Freeze the completed notebook and D delivery before a separate v5 extension."""
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
REPO = BASE.parent / 'experiment_notebooks'
FOLDER = REPO / 'notebooks/23-synthetic-data-curation'
DESTINATION = Path(r'D:\projects\experiment_notebooks\notebooks\23-synthetic-data-curation')
OUTPUT = BASE / 'scale_baseline_manifest.json'
ALLOWED = {'23_synthetic_data_curation.ipynb', 'README.md', '.gitattributes'}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == '__main__':
    if OUTPUT.exists():
        manifest = json.loads(OUTPUT.read_text(encoding='utf-8'))
        protected = {k: v for k, v in manifest['source_files'].items() if k not in ALLOWED}
        assert all(digest(FOLDER / key) == expected for key, expected in protected.items())
        print(json.dumps({'status': 'existing_baseline_verified', 'protected_files': len(protected)}))
        raise SystemExit(0)
    listed = subprocess.check_output(['git', 'ls-files', '-z', '--', 'notebooks/23-synthetic-data-curation'], cwd=REPO)
    names = [Path(raw.decode()).relative_to(Path('notebooks/23-synthetic-data-curation')).as_posix()
             for raw in listed.split(b'\0') if raw]
    assert len(names) == 988, 'Unexpected completed-study baseline; inspect before proceeding'
    hashes = {name: digest(FOLDER / name) for name in names}
    destination_hashes = {name: digest(DESTINATION / name) for name in names if (DESTINATION / name).is_file()}
    differing = [name for name in destination_hashes if destination_hashes[name] != hashes[name]]
    assert not differing, f'Destination changes require preservation: {differing}'
    backup = BASE / 'scale_preserved_baseline'
    for name in names:
        target = backup / name
        if target.exists():
            assert digest(target) == hashes[name]
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(FOLDER / name, target)
    manifest = {'recorded_at_utc': datetime.now(timezone.utc).isoformat(),
                'source': str(FOLDER), 'destination': str(DESTINATION),
                'branch': subprocess.check_output(['git', 'branch', '--show-current'], cwd=REPO, text=True).strip(),
                'commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip(),
                'source_files': hashes, 'destination_files': destination_hashes,
                'allowed_existing_changes': sorted(ALLOWED),
                'protected_files': len(hashes) - len(ALLOWED),
                'destination_differences': differing}
    OUTPUT.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({'status': 'baseline_frozen', 'source_files': len(hashes),
                      'destination_matches': len(destination_hashes), 'protected_files': manifest['protected_files']}))
