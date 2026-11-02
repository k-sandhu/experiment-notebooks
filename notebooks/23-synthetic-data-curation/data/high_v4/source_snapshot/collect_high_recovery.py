"""One declared whole-pilot service recovery, retaining both earlier attempts."""
import argparse
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone

base = Path(__file__).parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('phase', choices=['pilot', 'prepare-main', 'originals', 'interventions'])
parser.add_argument('--live', action='store_true')
args = parser.parse_args()
root = base.parent / 'experiment_notebooks/notebooks/23-synthetic-data-curation'
freeze = json.loads((base / 'high_source_frozen_v4b.json').read_text())
for name, hashes in freeze['sources'].items():
    assert hashlib.sha256((base / name).read_bytes()).hexdigest() == hashes['raw_sha256'], name
ns = {'__name__': 'high_v4c_recovery'}
for name in ('high_transport.py', 'high_fixtures.py', 'high_material_audit.py', 'high_experiment.py'):
    exec(compile((base / name).read_text(encoding='utf-8'), name, 'exec'), ns)
ns['HIGH_PROTOCOL'] = '23-high-v4c'
ns['HIGH_PILOT_CONFIG']['protocol'] = ns['HIGH_PROTOCOL']
ns['HIGH_MAIN_CONFIG']['protocol'] = ns['HIGH_PROTOCOL']
declaration = root / 'data/high_v4/recovery_declaration.json'
if not declaration.exists():
    if args.phase != 'pilot':
        raise RuntimeError('Declare the replacement pilot before any later phase')
    value = {'declared_utc': datetime.now(timezone.utc).isoformat(), 'protocol': ns['HIGH_PROTOCOL'],
        'core_source_freeze': freeze, 'runtime_overrides': {'HIGH_PROTOCOL': ns['HIGH_PROTOCOL'],
        'HIGH_PILOT_CONFIG.protocol': ns['HIGH_PROTOCOL'], 'HIGH_MAIN_CONFIG.protocol': ns['HIGH_PROTOCOL']},
        'reason': 'One additional whole-pilot attempt after cooldown following terminal429 service failures. All earlier attempts are retained and excluded from difficulty selection. Stop immediately on any new transport failure.',
        'maximum_additional_service_restarts_this_turn': 1,
        'unchanged': ['model', 'high reasoning', 'one worker', 'all source packets', 'instructions', 'seeds', 'failure thresholds', 'scoring', 'paired treatment design']}
    declaration.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')
count = [0]
def progress(event):
    count[0] += 1
    print(json.dumps({'completed_this_phase': count[0], **event}), flush=True)
dispatch = {
    'pilot': lambda: ns['high_run_pilot'](root=root, live=args.live, progress=progress),
    'prepare-main': lambda: ns['high_prepare_main'](root=root),
    'originals': lambda: ns['high_collect_originals'](root=root, live=args.live, progress=progress),
    'interventions': lambda: ns['high_run_interventions'](root=root, live=args.live, progress=progress),
}
result = dispatch[args.phase]()
print(json.dumps({'phase': args.phase, 'selected_level': result.get('selected_level'),
    'threshold_met': result.get('threshold_met'), 'metrics': result.get('metrics')}, indent=2), flush=True)
