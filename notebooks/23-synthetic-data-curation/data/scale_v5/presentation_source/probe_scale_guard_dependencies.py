"""Exercise real installed imports and the two offline blocks, without models."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import replay_scale_notebook as replay

BASE = Path(__file__).resolve().parent
session = BASE / 'guard_dependency_probes' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
session.mkdir(parents=True)
env = dict(os.environ)
log = replay.scale_qa_prepare_guard(session, env)
code = '''
import importlib, json, os, site, socket, subprocess
import sitecustomize
assert site.ENABLE_USER_SITE is False
assert sitecustomize.SCALE_QA_GUARD_PID == os.getpid()
modules = ['nbconvert', 'nbformat', 'ipykernel', 'numpy', 'matplotlib']
for name in modules:
    importlib.import_module(name)
try:
    subprocess.run(['codex', '--version'], check=True)
except PermissionError:
    pass
else:
    raise AssertionError('Model CLI guard did not block the harmless version probe')
connection = socket.socket()
connection.settimeout(.1)
try:
    connection.connect(('203.0.113.1', 443))
except PermissionError:
    pass
else:
    raise AssertionError('External socket guard did not block the reserved test address')
finally:
    connection.close()
print(json.dumps(dict(passed=True, imported=modules, user_site_startup_disabled=True)))
'''
result = subprocess.run([sys.executable, '-c', code], env=env, capture_output=True, text=True, timeout=90)
(session / 'stdout.txt').write_text(result.stdout, encoding='utf-8', newline='\n')
(session / 'stderr.txt').write_text(result.stderr, encoding='utf-8', newline='\n')
assert result.returncode == 0, result.stderr
summary = json.loads(result.stdout)
events = [json.loads(line) for line in log.read_text(encoding='utf-8').splitlines()]
assert sum(event['kind'] == 'blocked_model_cli' for event in events) == 1
assert sum(event['kind'] == 'blocked_external_network' for event in events) == 1
assert sum(event['kind'] == 'guard_loaded' for event in events) == 1
summary.update(model_calls=0, external_connections=0,
               scope='Separate negative-control probe; no experiment replay or source/cache changes.',
               installed_dependency_paths=replay.scale_qa_dependency_paths(),
               replay_helper_sha256=hashlib.sha256((BASE / 'replay_scale_notebook.py').read_bytes()).hexdigest(),
               retained_probe_directory=str(session))
(BASE / 'scale_guard_dependency_probe_006.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(summary))
