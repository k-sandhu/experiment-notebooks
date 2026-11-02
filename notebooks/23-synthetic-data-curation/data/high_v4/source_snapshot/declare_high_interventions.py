"""Save the completed original/source review before either intervention is called."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

base = Path(__file__).resolve().parent
data = base.parent / 'experiment_notebooks/notebooks/23-synthetic-data-curation/data/high_v4'
read = lambda p: json.loads(p.read_text(encoding='utf-8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
main = data / 'main'
original = read(main / 'original_manifest.json')
selection = read(main / 'selection.json')
review = read(base / 'high_failure_material_review.json')
assert original['phase'] == 'originals_complete'
assert len(original['request_keys']) == original['n_called_collection'] + original['n_audit'] == 264
assert review['status'] == 'complete' and review['cache_audit']['cache_files'] == 264
assert review['cache_audit']['original_sample0_terminal'] == 264
assert not review['cache_audit']['incomplete_requests']
assert not review['source_gate']['source_check_failures']
assert not review['cache_audit']['request_hash_errors']
assert not review['cache_audit']['request_input_errors']
assert not review['original_outputs']['schema_or_integrity_issues']
assert not review['frozen_selection']['source_hash_errors']
audited_ids = review['frozen_selection']['selected_case_ids']  # The readable review sorts IDs.
selected_ids = selection['selected_case_ids']  # Dispatch retains the frozen random ranking.
assert len(audited_ids) == len(set(audited_ids)) == len(selected_ids) == len(set(selected_ids))
assert set(audited_ids) == set(selected_ids)
rows = [json.loads(line) for line in (main / 'candidates.jsonl').read_text(encoding='utf-8').splitlines()]
eligible = {row['case_id'] for row in rows if row['split'] == 'collection' and not row['transport_error']
            and row['response'] is not None and row['verification']['valid_schema'] and not row['verification']['exact_fields']}
allocation = read(main / 'allocation.json')
config = read(main / 'protocol.json')['config']
assert selected_ids == [cid for cid in allocation['failure_selection_ranking'] if cid in eligible][:config['max_selected']]
assert review['frozen_selection']['selected_ids_all_verified_failures']
assert review['frozen_selection']['selected_feedback_flag_checks_passed']
assert review['repair_feedback_audit']['n_repair_requests'] == 0
assert not (main / 'interventions.jsonl').exists()
freeze = read(data / 'main_source_freeze.json')
for name, item in freeze['core_freeze']['sources'].items():
    assert sha(base / name) == item['raw_sha256'], name
for name, value in freeze['files'].items():
    assert sha(base / name) == value, name
for suffix in ('json', 'md'):
    destination = data / ('original_failure_review.' + suffix)
    content = (base / ('high_failure_material_review.' + suffix)).read_bytes()
    if destination.exists():
        assert destination.read_bytes() == content
    else:
        destination.write_bytes(content)
declaration = {'reviewed_at_utc': datetime.now(timezone.utc).isoformat(),
    'phase': 'before_first_intervention_request', 'protocol': '23-high-v4e',
    'original_manifest_sha256': sha(main / 'original_manifest.json'),
    'selection_sha256': sha(main / 'selection.json'),
    'independent_failure_material_review_sha256': sha(data / 'original_failure_review.json'),
    'all_original_requests_terminal': 264, 'selected_genuine_original_failures': len(selection['selected_case_ids']),
    'source_and_failed_field_checks_passed': True, 'core_and_pre_main_source_freezes_unchanged': True,
    'arms': ['fresh_retry', 'feedback_repair'], 'cli_requests_per_selected_source': 2,
    'feedback': 'Exact original output plus failed-field names and schema/evidence field flags only; no expected values or calculation trace.',
    'dispatch': 'Frozen shuffled order and two-request bounded waves from the predeclared protocol.',
    'weights_updated': False}
destination = data / 'intervention_start_declaration.json'
if destination.exists():
    assert {k:v for k,v in read(destination).items() if k != 'reviewed_at_utc'} == {k:v for k,v in declaration.items() if k != 'reviewed_at_utc'}
else:
    destination.write_text(json.dumps(declaration, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(declaration, indent=2))
