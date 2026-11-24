"""Add stable Contents anchors without changing code or its saved outputs."""
import hashlib
import json
import re
from pathlib import Path

base = Path(__file__).resolve().parent
path = base.parent / 'experiment_notebooks/notebooks/23-synthetic-data-curation/23_synthetic_data_curation.ipynb'
notebook = json.loads(path.read_text(encoding='utf-8'))
before = json.dumps([c for c in notebook['cells'] if c['cell_type'] == 'code'], sort_keys=True)
changed = 0
for cell in notebook['cells']:
    if cell['cell_type'] != 'markdown':
        continue
    source = ''.join(cell['source'])
    match = re.search(r'^## (\d+\. [^\n]+)', source, re.M)
    if not match:
        continue
    heading = match.group(1)
    slug = re.sub(r'[^\w\- ]', '', heading.lower())
    slug = re.sub(r' +', '-', slug)
    anchor = f'<a id="{slug}"></a>'
    if anchor not in source:
        source = source[:match.end()] + '\n\n' + anchor + source[match.end():]
        cell['source'] = source.splitlines(keepends=True)
        changed += 1
after = json.dumps([c for c in notebook['cells'] if c['cell_type'] == 'code'], sort_keys=True)
assert before == after
path.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')
print(json.dumps({'anchors_added': changed, 'code_and_outputs_unchanged': True,
                  'code_sha256': hashlib.sha256(before.encode()).hexdigest()}))
