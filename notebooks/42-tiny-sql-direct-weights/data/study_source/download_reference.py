"""Fetch only the pinned public reference weights and metadata. No reference-model generation."""
from pathlib import Path
import hashlib,json,time
import requests
ROOT=Path(__file__).resolve().parent/'data'/'reference'
ROOT.mkdir(parents=True,exist_ok=True)
REVISION='cf967c0a9a04383db6f7b1108d86b2962634b4ac'
EXPECTED_WEIGHT_SHA256='116a02532db461f91386a5b20f942ff2c8d4de7341e21b55caafc3d7b25f49a1'
started=time.monotonic()
meta=requests.get('https://huggingface.co/api/models/EleutherAI/pythia-14m/revision/'+REVISION+'?blobs=true',timeout=20)
meta.raise_for_status();data=meta.json()
assert data['sha']==REVISION and data['cardData']['license']=='apache-2.0'
(ROOT/'metadata.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
files={}
for name in ['config.json','model.safetensors']:
    path=ROOT/name
    if not path.exists():
        response=requests.get('https://huggingface.co/EleutherAI/pythia-14m/resolve/'+REVISION+'/'+name,stream=True,timeout=(15,90))
        response.raise_for_status()
        with path.open('wb') as out:
            for block in response.iter_content(1024*1024):out.write(block)
    files[name]={'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
assert files['model.safetensors']['sha256']==EXPECTED_WEIGHT_SHA256
provenance={'model':'EleutherAI/pythia-14m','revision':REVISION,'license':'Apache-2.0','hf_created_at':data.get('createdAt'),
            'files':files,'verification_wall_seconds':time.monotonic()-started,'local_reference_inference':False}
(ROOT/'provenance.json').write_text(json.dumps(provenance,indent=2),encoding='utf-8')
print(json.dumps(provenance,indent=2))
