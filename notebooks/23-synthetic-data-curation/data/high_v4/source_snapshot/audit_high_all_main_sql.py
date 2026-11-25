"""Audit every possible main packet before selecting its difficulty level."""
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone
from high_fixtures import high_make_cases, high_audit_fixtures, HIGH_TASK_INSTRUCTIONS
from high_material_audit import high_material_answer

base = Path(__file__).parent
rows, levels = [], []
for level in range(1, 5):
    cases = high_make_cases(160, 244160, level=level, split='collection', start_index=0)
    cases += high_make_cases(80, 244080, level=level, split='collection', start_index=160)
    cases += high_make_cases(24, 244024, level=level, split='audit', start_index=240)
    validation = high_audit_fixtures(cases)
    for case in cases:
        answer, trace = high_material_answer(case['document'])
        assert answer == case['gold'], case['case_id']
        rows.append({'case_id': case['case_id'], 'level': level, 'family': case['family'],
            'split': case['split'], 'semantic_hash': case['semantic_hash'],
            'document_sha256': hashlib.sha256(case['document'].encode()).hexdigest(),
            'answer_from_text': answer, 'passed': True,
            'trace': {k: v for k, v in trace.items() if k != 'contributions'},
            'n_contributions': len(trace['contributions'])})
    levels.append({'level': level, 'n_cases': len(cases), 'fixture_audit': validation})
    print(json.dumps({'level': level, 'n_cases': len(cases), 'passed': True}), flush=True)
assert len({r['case_id'] for r in rows}) == len(rows)
assert len({r['semantic_hash'] for r in rows}) == len(rows)
report = {'audited_at_utc': datetime.now(timezone.utc).isoformat(),
    'instruction_sha256': hashlib.sha256(HIGH_TASK_INSTRUCTIONS.encode()).hexdigest(),
    'method': 'Independent visible-text parser, SQL movement joins, Decimal pricing',
    'n_cases': len(rows), 'all_passed': True, 'levels': levels, 'cases': rows}
(base / 'high_all_main_sql_audit.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
