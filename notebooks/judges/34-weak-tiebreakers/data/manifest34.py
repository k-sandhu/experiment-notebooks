from pathlib import Path
from datetime import datetime,timezone
import hashlib,json

root=Path(__file__).resolve().parents[1]
text_extensions={'.json','.jsonl','.csv','.md','.py','.ipynb','.txt'}
files={}
for path in sorted(root.rglob('*')):
    if not path.is_file() or 'tmp' in path.relative_to(root).parts or path.name in ['HANDOFF.md','artifact_manifest.json']:continue
    raw=path.read_bytes()
    if path.suffix.lower() in text_extensions or path.name=='.gitignore':raw=raw.replace(b'\r\n',b'\n')
    files[path.relative_to(root).as_posix()]=hashlib.sha256(raw).hexdigest()
record=dict(created_at=datetime.now(timezone.utc).isoformat(),normalization='CRLF to LF for text; raw bytes for gzip and PNG',files=files)
(root/'data/artifact_manifest.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print('Artifact manifest saved:',len(files),'files')
