"""Bind a passed independent audit before an explicit live phase is started."""
import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import shutil

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent / 'experiment_notebooks' / 'notebooks' / '23-synthetic-data-curation'
DATA = ROOT / 'data' / 'scale_v5'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=['main', 'interventions'])
    phase = parser.parse_args().phase
    review_name = 'scale_main_material_review' if phase == 'main' else 'scale_original_failure_review'
    review = read(BASE / (review_name + '.json'))
    assert review['passed'] and not review.get('issues'), 'Independent gate failed'
    assert review.get('model_calls', 0) == 0
    script = 'audit_scale_main_materials.py' if phase == 'main' else 'audit_scale_originals.py'
    copies = {review_name + suffix: BASE / (review_name + suffix) for suffix in ('.json', '.md')}
    copies['audit_source/' + script] = BASE / script
    names = ['preregistration.json', 'source_freeze.json', 'pilot/ladder.json',
             'main/protocol.json', 'main/allocation.json', review_name + '.json',
             review_name + '.md', 'audit_source/' + script]
    protocol = read(DATA / 'main/protocol.json')
    for block in protocol['blocks']:
        source = 'main/' + block['source_path']
        names += [source, source + '.manifest.json', source + '.audit.jsonl.gz']
    if phase == 'main':
        path = DATA / 'main_start_declaration.json'
    else:
        assert read(DATA / 'main/original_manifest.json')['phase'] == 'originals_complete'
        names += ['main/original_manifest.json', 'main/selection.json',
                  'main/candidates.jsonl', 'main/original_request_ledger.jsonl',
                  'main/original_metrics.json', 'main_start_declaration.json']
        amendment_name = 'infrastructure_resume/amendment_001.json'
        amendment = read(DATA / amendment_name)
        assert all(hashlib.sha256((DATA / name).read_bytes()).hexdigest() == digest
                   for name, digest in amendment['provenance_sha256'].items()), 'Continuation provenance changed'
        names += [amendment_name] + list(amendment['provenance_sha256'])
        runner_review = read(BASE / 'scale_intervention_runner_review.json')
        assert runner_review['passed'] and not runner_review.get('issues'), 'Intervention runner review failed'
        assert runner_review.get('live_model_calls', 0) == 0
        runner_files = {
            'intervention_runner/source_snapshot/run_scale_interventions_reviewed.py': BASE / 'run_scale_interventions_reviewed.py',
            'intervention_runner/source_snapshot/test_run_scale_interventions_reviewed.py': BASE / 'test_run_scale_interventions_reviewed.py',
            'intervention_runner/source_snapshot/scale_resume.py': DATA / amendment['implementation']['path'],
            'intervention_runner/source_snapshot/declare_scale_gate.py': BASE / 'declare_scale_gate.py',
            'intervention_runner/implementation_review.json': BASE / 'scale_intervention_runner_review.json',
            'intervention_runner/implementation_review.md': BASE / 'scale_intervention_runner_review.md',
            'intervention_runner/unit_tests.log': BASE / 'scale_intervention_runner_unit_tests.log'}
        assert hashlib.sha256(runner_files['intervention_runner/source_snapshot/run_scale_interventions_reviewed.py'].read_bytes()).hexdigest() == runner_review['source_sha256']
        assert hashlib.sha256(runner_files['intervention_runner/source_snapshot/test_run_scale_interventions_reviewed.py'].read_bytes()).hexdigest() == runner_review['tests_sha256']
        copies.update(runner_files)
        names += list(runner_files)
        path = DATA / 'intervention_start_declaration.json'
    declaration = {'protocol': '23-scale-v5', 'declared_at_utc': datetime.now(timezone.utc).isoformat(),
                   'phase': phase + '_authorized_after_independent_audit',
                   'material_review_passed': True, 'selected_tier': protocol['selected_tier'],
                   'potential_main_sources': sum(b['manifest']['n_cases'] for b in protocol['blocks']),
                   'sha256': {name: hashlib.sha256(copies.get(name, DATA / name).read_bytes()).hexdigest() for name in names},
                   'note': 'No model calls in this declaration. Start the frozen collector in a separate explicit command.'}
    if path.exists():
        assert read(path)['sha256'] == declaration['sha256'], 'Previously declared gate changed'
        assert all(hashlib.sha256((DATA / name).read_bytes()).hexdigest() == expected
                   for name, expected in declaration['sha256'].items()), 'Previously bound artifact changed'
    else:
        if phase == 'main':
            assert not list((DATA / 'main').glob('cache/*.json.gz')), 'Main calls already started'
        else:
            assert not (DATA / 'main/manifest.json').exists(), 'Interventions already completed'
            for path2 in (DATA / 'main/cache').glob('*.json.gz'):
                cached = json.loads(gzip.decompress(path2.read_bytes()))
                request = cached['request']
                assert request['stage'] == 'generate' and request['sample'] == 0, 'Intervention calls already started'
        for destination, source in copies.items():
            target = DATA / destination
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        path.write_text(json.dumps(declaration, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({'passed': True, 'phase': phase, 'declaration': str(path),
                      'bound_files': len(names), 'selected_tier': protocol['selected_tier']}))


if __name__ == '__main__':
    main()
