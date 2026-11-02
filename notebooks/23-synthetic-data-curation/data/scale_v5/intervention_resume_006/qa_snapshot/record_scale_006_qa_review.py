"""Record the completed synthetic-only delivery/replay tests before dispatch."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

base = Path(__file__).resolve().parent
log = base / 'scale_replay_delivery_006_final_tests.log'
text = log.read_text(encoding='utf-8')
assert 'Ran 10 tests in 78.218s' in text and '\nOK\n' in text and 'FAILED' not in text
sources = ['verify_scale_delivery.py', 'replay_scale_notebook.py', 'test_verify_scale_recovery_006.py']
report = dict(passed=True, checked_at_utc=datetime.now(timezone.utc).isoformat(),
              tests_run=10, elapsed_seconds=78.218, model_calls=0, efficacy_reads=False,
              scope='Disposable metadata fixtures only; real caches and outcomes are not opened.',
              checks=['2268 raw-prefix byte bindings', 'historical and current plan lineage',
                      'required predecessor and gate bytes', 'new analysis bytes',
                      'zero-call full 1200-slot offline receipt', 'reject partial 1199-slot receipt'],
              log_sha256=hashlib.sha256(log.read_bytes()).hexdigest(),
              source_sha256={name: hashlib.sha256((base / name).read_bytes()).hexdigest() for name in sources})
(base / 'scale_replay_delivery_006_unit_test_review.json').write_text(
    json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(report))
