"""Freeze the v5 design, tested code and all potential pilot sources before calls."""
import hashlib
import json
import platform
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
REPO = BASE.parent / 'experiment_notebooks'
FOLDER = REPO / 'notebooks/23-synthetic-data-curation'
DATA = FOLDER / 'data/scale_v5'
FINAL_RUNTIME = {
    'scale_transport.py': 'f5e82af94fae2f200badf9f14622ebaa32031269274534111418cbd435593b5c',
    'scale_parallel.py': '11e8ef1da3db3a5ab527816a11b35b8ae29f00aa01a97d55620411b82e129f72',
    'scale_experiment.py': 'a9a16ceae0b03522f3286947c8c124ba8a95328f1be3d3aec2b16e180eb86812',
    'collect_scale.py': '4d0bcd88574d850d1c892d109e9794d49bd9ffe19c0d87272ff29ce8f481b52a',
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')


def main():
    if (DATA / 'preregistration.json').exists():
        previous = read(DATA / 'preregistration.json')
        assert all(sha(BASE / name) == expected for name, expected in previous['runtime_source_sha256'].items())
        print('Existing preregistration verified; no tests, preparation or calls repeated.')
        return
    baseline = read(BASE / 'scale_baseline_manifest.json')
    protected = {k: v for k, v in baseline['source_files'].items()
                 if k not in baseline['allowed_existing_changes']}
    assert len(protected) == 985
    assert all(sha(FOLDER / name) == expected for name, expected in protected.items())
    assert all(sha(BASE / name) == expected for name, expected in FINAL_RUNTIME.items())
    review = read(BASE / 'scale_design_review.json')
    assert review['result'].startswith('passed') and not review['blockers']
    power = read(BASE / 'scale_power_plan.json')
    assert power['recommendation']['fixed_eligible_failure_pairs'] == 600
    assert power['recommendation']['adopted_original_case_cap'] == 2048
    assert power['recommendation']['maximum_planned_cli_requests'] == 3376
    assert power['recommendation']['minimum_primary_positive_direction_power_over_requested_discordances'] >= .90
    assert not list(DATA.glob('**/cache/*.json.gz')), 'No live v5 cache may precede this declaration'
    command = [sys.executable, '-m', 'unittest', '-v', 'test_scale_fixtures', 'test_scale_transport', 'test_scale_experiment']
    result = subprocess.run(command, cwd=BASE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, encoding='utf-8', errors='replace')
    log = result.stdout.replace('\r\n', '\n')
    (BASE / 'scale_unit_tests.log').write_text(log, encoding='utf-8', newline='\n')
    if result.returncode:
        print(log[-14000:])
        raise SystemExit(result.returncode)
    matches = re.findall(r'Ran (\d+) tests in ([0-9.]+)s', log)
    assert len(matches) == 1 and int(matches[0][0]) == 26
    test_summary = {'passed': 26, 'fixture_tests': 12, 'transport_tests': 6, 'engine_tests': 8,
                    'elapsed_seconds': float(matches[0][1]), 'live_model_calls': 0,
                    'command': command, 'log_sha256': sha(BASE / 'scale_unit_tests.log')}
    prepare = [sys.executable, str(BASE / 'collect_scale.py'), 'prepare-pilot', '--root', str(FOLDER)]
    result = subprocess.run(prepare, cwd=BASE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, encoding='utf-8', errors='replace')
    (BASE / 'scale_pilot_preparation.log').write_text(result.stdout, encoding='utf-8', newline='\n')
    if result.returncode:
        print(result.stdout[-14000:])
        raise SystemExit(result.returncode)
    freeze = read(DATA / 'source_freeze.json')
    assert all(freeze['source_sha256'][name] == expected for name, expected in FINAL_RUNTIME.items())
    snapshot_names = list(freeze['source_sha256']) + [
        'test_scale_fixtures.py', 'test_scale_transport.py', 'test_scale_experiment.py',
        'scale_power.py', 'scale_power_plan.json', 'scale_power_plan.md',
        'scale_fixture_plan.json', 'scale_fixture_plan.md', 'scale_design_review.json', 'scale_design_review.md',
        'prepare_scale_baseline.py', 'freeze_scale_preregistration.py']
    snapshot_names = sorted(set(snapshot_names))
    snapshot_hashes = {name: sha(BASE / name) for name in snapshot_names}
    preregistration = {
        'protocol': '23-scale-v5', 'registered_at_utc': datetime.now(timezone.utc).isoformat(),
        'question': 'Does the prior-answer-plus-verified-field-feedback repair package recover more genuine high-reasoning Sol extraction failures than a fresh retry?',
        'prior_v4_used_only_for_planning': True, 'prior_v4_pairs_pooled_into_inference': False,
        'pilot': freeze['pilot_config'], 'main': freeze['main_config'],
        'maximum_planned_cli_requests': 3376,
        'pilot_policy': 'First of128 then192 base-shipment tiers with at least6 genuine value failures among16 cases; otherwise fixed192 fallback explicitly marked threshold-not-met. No upper failure-rate cutoff.',
        'source_gate': 'All32 potential pilot packets are audited before pilot calls. After selection, all2144 possible main packets at the selected tier must be independently audited before any main call. Master seeds, rules and generator code are frozen here before pilot outcomes.',
        'eligibility': 'Successful usable single-case original response, valid schema and at least one incorrect typed value. Citation-only, schema, parsing and infrastructure errors are excluded from genuine-failure accrual.',
        'accrual': '512 original collection cases, then complete fixed256-case tranches until at least600 qualifying failures or2048 collection cases. Selection ranks all accrued eligible failures with the pre-outcome random ranking and takes600, or all if the fixed cap yields a shortfall.',
        'audit_boundary': '96 separately seeded audit cases, called after collection selection freezes, excluded from accrual, repairs and primary comparison. Audit is baseline only; no model is trained.',
        'paired_dispatch': 'Default4 workers. Each randomized four-request wave contains fresh and repair calls for two sources. Both settle before another wave. No request sees its sibling result.',
        'intervention_gate': 'All originals and audit calls complete, source/failure review recorded, and exact selection/feedback lineage checked before a separate explicit intervention command.',
        'stopping': 'No intervention-effect peeking or advantage-based stopping. Stop before the next bounded wave on an infrastructure failure; preserve all attempts, including failed/pending records. No orchestration retries. CLI internal reconnect/inference behavior is not independently guaranteed.',
        'primary': 'Positive repair-minus-fresh all-seven-value recovery difference AND exact two-sided conditional McNemar p<0.05. Report paired percentile-bootstrap95% interval with20000 resamples, seed246600. Citation acceptance and numeric harms are secondary.',
        'planning_effect_percentage_points': 10,
        'nominal_power_at_600_minimum_over_discordance_025_035_050': power['recommendation']['minimum_primary_positive_direction_power_over_requested_discordances'],
        'power_scope': 'Independent case pairs from one fixed generator with six overlapping variants. This is not600 independent task programs and does not establish broader task generalization. A5-point effect can remain uncertain.',
        'shortfall': 'Keep the fixed original cap. Report attained pairs and reduced nominal power; do not extend based on an observed repair advantage. A target shortfall is explicitly separated from the planned600-case comparison.',
        'interpretation': 'The contrast includes prior-answer exposure as well as correct field-name feedback. Equal calls do not equalize tokens or time. Original collection accuracy is descriptive under failure-count stopping. No training or weight update is performed.',
        'storage': 'Lossless full-request/raw-response gzip caches keyed by canonical requestSHA256; frozen source and independent-audit gzipJSONL with compressed and uncompressed hashes.',
        'data_rights': 'Fresh fictional data generated in code. Model outputs are service outputs; this demonstration does not grant unrestricted downstream training rights.',
        'model': {'id': 'gpt-6.1-sol', 'reasoning_effort': 'high', 'documented_cutoff': '2026-04-30',
                  'official_source': 'https://developers.openai.com/api/docs/models/gpt-6.1-sol',
                  'source_checked_on': '2026-10-26', 'immutable_dated_checkpoint_established': False},
        'source_creation_date': '2026-10-26', 'date_filter': 'All generated packets postdate the documented cutoff.',
        'runtime_source_sha256': freeze['source_sha256'], 'snapshot_sha256': snapshot_hashes,
        'source_freeze_sha256': sha(DATA / 'source_freeze.json'),
        'independent_design_review_sha256': sha(BASE / 'scale_design_review.json'),
        'python_version': platform.python_version(), 'test_summary': test_summary,
        'spend_usd': None, 'cost_note': 'Subscription CLI dollar spend is unavailable. Preserve observed tokens and unknown usage; authoring-agent usage is outside experiment CLI counters.'}
    for name in snapshot_names:
        destination = DATA / 'source_snapshot' / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(BASE / name, destination)
    write(DATA / 'test_summary.json', test_summary)
    (DATA / 'unit_tests.log').write_text(log, encoding='utf-8', newline='\n')
    write(DATA / 'baseline.json', {'previous_commit': baseline['commit'], 'files': baseline['source_files'],
                                   'allowed_existing_changes': baseline['allowed_existing_changes'],
                                   'protected_files': len(protected)})
    write(DATA / 'preregistration.json', preregistration)
    print(json.dumps({'status': 'preregistered_no_live_calls', 'tests_passed': 26,
                      'target_failures': 600, 'max_originals': 2048, 'max_requests': 3376,
                      'source_snapshot_files': len(snapshot_names)}, indent=2))


if __name__ == '__main__':
    main()
