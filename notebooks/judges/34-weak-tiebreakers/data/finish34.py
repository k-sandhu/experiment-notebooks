import os, sys, json, gzip, hashlib, subprocess, platform, re
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
assert not (data/'cli429_stop.json').exists(),'Resolve and archive exhausted CLI429 stop before finishing'
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
env['TEMP']=env['TMP']=str((data/'tmp').resolve())
smoke_env=dict(env,NB_PROFILE='smoke')
smoke_started=datetime.now(timezone.utc).isoformat()
smoke_cmd=[sys.executable,'-X','utf8','-E','-P','-m','nbconvert','--to','notebook','--execute','--inplace','34_weak_tiebreakers.ipynb','--ExecutePreprocessor.timeout=-1']
with (data/'tmp/smoke_replay.log').open('w',encoding='utf-8') as out,(data/'tmp/smoke_replay.err').open('w',encoding='utf-8') as err:
    subprocess.run(smoke_cmd,cwd=root,env=smoke_env,stdout=out,stderr=err,check=True)
smoke_nb=nbformat.read(root/'34_weak_tiebreakers.ipynb',as_version=4)
smoke_code=[c for c in smoke_nb.cells if c.cell_type=='code']
assert all(c.execution_count is not None and c.outputs for c in smoke_code)
assert not any(o.output_type=='error' for c in smoke_code for o in c.outputs)
smoke_text='\n'.join(o.get('text','') for c in smoke_code for o in c.outputs if o.output_type=='stream')
assert 'New calls in this executed replay: 0' in smoke_text
assert 'Items 4 judgments 68 disagreements 2' in smoke_text
assert before==hashes(),'Smoke replay changed request caches'
(data/'smoke_replay_validation.json').write_text(json.dumps(dict(started_at=smoke_started,completed_at=datetime.now(timezone.utc).isoformat(),
    items=4,disagreements=2,judgments=68,new_calls=0,cache_unchanged=True,all_code_cells_have_outputs=True,no_error_outputs=True),indent=2)+'\n',encoding='utf-8')
subprocess.run([sys.executable,'-X','utf8','-E','-P','data/build34.py'],cwd=root,env=env,check=True)
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
source=pd.read_csv(data/'from_33/judgments.csv')
reused=j[j.origin.astype(str).eq('33')]
matched=reused.merge(source[['item_id','judge','order','raw_reply_cache_key']],on=['item_id','judge','order'],suffixes=('_34','_33'),validate='one_to_one')
assert len(matched)==len(reused)==1436
assert matched.raw_reply_cache_key_34.eq(matched.raw_reply_cache_key_33).all(),'Reused baseline differs from exported source33 final reply'
starts={}
with (data/'attempt_lifecycle.jsonl').open(encoding='utf-8') as stream:
    for line in stream:
        event=json.loads(line)
        match=re.match(r'nb34test:judge:nb34b(\d+)-',event.get('purpose',''))
        if event.get('event')=='started' and match:
            batch=int(match.group(1));at=event['at']
            starts[batch]=min(starts.get(batch,at),at)
chronology=[]
for path in sorted(data.glob('batch_*_v1.jsonl.freeze.json')):
    frozen=json.loads(path.read_text(encoding='utf-8'));batch=int(path.name.split('_')[1])
    assert batch in starts,('No invocation start recorded for batch',batch)
    assert datetime.fromisoformat(starts[batch])>=datetime.fromisoformat(frozen['created_at']),('Strong call preceded batch freeze',batch)
    content=(data/frozen['filename']).read_bytes().replace(b'\r\n',b'\n')
    assert hashlib.sha256(content).hexdigest()==frozen['sha256']
    chronology.append(dict(batch=batch,frozen_at=frozen['created_at'],first_strong_call_at=starts[batch],sha256=frozen['sha256']))
key=os.environ.get('OPENROUTER_API_KEY','')
checked=0
json_files=0;jsonl_records=0
for p in data.rglob('*'):
    if not p.is_file() or 'tmp' in p.relative_to(data).parts:continue
    if p.name.endswith('.jsonl.gz') or p.suffix=='.jsonl':
        opener=gzip.open if p.name.endswith('.gz') else open
        with opener(p,'rt',encoding='utf-8') as stream:
            for line in stream:
                if line.strip():json.loads(line);jsonl_records+=1
        json_files+=1
    elif p.suffix=='.json':
        json.loads(p.read_text(encoding='utf-8'));json_files+=1
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
           logical_judgments=len(j),items=len(all_ids),disagreements=len(tie_ids),all_model_condition_orders_complete=True,reused_original_judgments=1436,
           reused_reply_keys_match_source33=True,batch_freezes_precede_strong_calls=chronology,
           parsed_json_files=json_files,parsed_jsonl_records=jsonl_records)
(data/'independent_replay_audit.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
environment=dict(python=sys.version,platform=platform.platform(),packages={k:version(k) for k in ['nbformat','nbconvert','ipykernel','numpy','pandas','matplotlib','requests']})
(data/'environment.json').write_text(json.dumps(environment,indent=2)+'\n',encoding='utf-8')
subprocess.run([sys.executable,'-X','utf8','-E','-P','data/manifest34.py'],cwd=root,env=env,check=True)
subprocess.run([sys.executable,'-X','utf8','-E','-P','data/write_handoff34.py'],cwd=root,env=env,check=True)
print('FINAL OFFLINE REPLAY AND HANDOFF COMPLETE',flush=True)
