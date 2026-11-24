import os, sys, json, gzip, hashlib, subprocess, platform
from pathlib import Path
from datetime import datetime, timezone
from importlib.metadata import version
import nbformat
import pandas as pd

root=Path(__file__).resolve().parents[1]
os.chdir(root)
data=root/'data'
assert (data/'live_validation.json').exists(),'Live collection has not completed'
assert not (data/'quota_stop.json').exists(),'Resolve quota stop before finishing'
plain=data/'cache_requests.jsonl'
archive=data/'cache_requests.jsonl.gz'
if plain.exists() and plain.stat().st_size:
    assert not archive.exists(),'Already archived; merge explicitly before archiving new records'
    with plain.open('rb') as src,archive.open('wb') as raw:
        with gzip.GzipFile(filename='',fileobj=raw,mode='wb',mtime=0) as dst:
            while block:=src.read(1024*1024):dst.write(block)
    plain.write_bytes(b'')

def hashes():
    paths=[data/'cache_from_33.jsonl.gz',archive,plain,data/'nonfinal_attempts.jsonl']
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.exists()}

before=hashes()
env={k:v for k,v in os.environ.items() if k not in ['NB_LIVE','NB_STAGE','FORCE_COLOR']}
env['NB_PROFILE']='full';env['NO_COLOR']='1'
started=datetime.now(timezone.utc).isoformat()
cmd=[sys.executable,'-X','utf8','-E','-P','-m','nbconvert','--to','notebook','--execute','--inplace','34_weak_tiebreakers.ipynb','--ExecutePreprocessor.timeout=-1']
with (data/'tmp/replay.log').open('w',encoding='utf-8') as out,(data/'tmp/replay.err').open('w',encoding='utf-8') as err:
    subprocess.run(cmd,cwd=root,env=env,stdout=out,stderr=err,check=True)
assert before==hashes(),'Replay changed the reply caches'
nb=nbformat.read(root/'34_weak_tiebreakers.ipynb',as_version=4)
code=[c for c in nb.cells if c.cell_type=='code']
assert all(c.execution_count is not None and c.outputs for c in code)
assert not any(o.output_type=='error' for c in code for o in c.outputs)
replay=json.loads((data/'replay_validation.json').read_text())
assert replay['new_calls']==0 and replay['mode']=='replay'
j=pd.read_csv(data/'judgments.csv');routes=pd.read_csv(data/'routing.csv')
all_ids=set(routes.item_id);tie_ids=set(routes.loc[routes.route.eq('disagreed'),'item_id'])
assert len(j)==4*len(all_ids)+26*len(tie_ids)
assert not j.duplicated(['item_id','condition','judge','order']).any()
for condition,names,expected_ids in [
    ('alone',['Opus','Sol'],all_ids),
    ('alone',['Haiku','Luna','Granite 8B','DeepSeek 763B','Decisions','Muse','Sonnet'],tie_ids),
    ('reasons',['Haiku','Luna','Granite 8B','DeepSeek 763B'],tie_ids),
    ('revise',['Opus','Sol'],tie_ids)]:
    for name in names:
        group=j[j.condition.eq(condition)&j.judge.eq(name)]
        assert set(group.item_id)==expected_ids,(condition,name)
        assert group.groupby('item_id').order.apply(lambda x:len(x)==2 and set(x)=={'AB','BA'}).all(),(condition,name)
assert int(j.origin.astype(str).eq('33').sum())==1436
key=os.environ.get('OPENROUTER_API_KEY','')
checked=0
if len(key)>8:
    for p in root.rglob('*'):
        if not p.is_file() or 'tmp' in p.relative_to(root).parts:continue
        raw=p.read_bytes()
        if p.suffix=='.gz':raw=gzip.decompress(raw)
        assert key.encode() not in raw,'Credential present in '+str(p.relative_to(root))
        checked+=1
audit=dict(started_at=started,completed_at=datetime.now(timezone.utc).isoformat(),before=before,after=hashes(),
           cache_unchanged=True,new_calls=0,code_cells=len(code),all_code_cells_have_outputs=True,no_error_outputs=True,
           credential_absent=True,credential_scan_files=checked,reader_prose_absent=not (root/'README.md').exists() and not (data/'PROTOCOL.md').exists(),
           logical_judgments=len(j),items=len(all_ids),disagreements=len(tie_ids),all_model_condition_orders_complete=True,reused_original_judgments=1436)
(data/'independent_replay_audit.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
environment=dict(python=sys.version,platform=platform.platform(),packages={k:version(k) for k in ['nbformat','nbconvert','ipykernel','numpy','pandas','matplotlib','requests']})
(data/'environment.json').write_text(json.dumps(environment,indent=2)+'\n',encoding='utf-8')
subprocess.run([sys.executable,'-X','utf8','-E','-P','data/supplemental34.py'],cwd=root,env=env,check=True)
subprocess.run([sys.executable,'-X','utf8','-E','-P','data/manifest34.py'],cwd=root,env=env,check=True)
subprocess.run([sys.executable,'-X','utf8','-E','-P','data/write_handoff34.py'],cwd=root,env=env,check=True)
print('FINAL OFFLINE REPLAY AND HANDOFF COMPLETE',flush=True)
