import collections, hashlib, html, itertools, json, math, os, platform, random, re, shutil, subprocess, sys, threading, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display, HTML
from sklearn.feature_extraction.text import TfidfVectorizer

ROOT=Path.cwd()
DATA=ROOT/'data';FIG=ROOT/'figures';TMP=DATA/'tmp'
for p in (DATA,FIG,TMP):p.mkdir(parents=True,exist_ok=True)
LIVE=os.environ.get('NB_LIVE')=='1'
PROFILE=os.environ.get('NB_PROFILE','smoke' if LIVE else 'full')
assert PROFILE in ('preflight','smoke','development','freeze','full')
SEED=20261030
N_TEST=42
N_DEV=6
N_EXAMPLES=8
N_RUBRIC=40
METHODS=['M0','M1','M2','M3','M4','M5']
ORDERS=['before_first','after_first']
JUDGES={
 'Claude Opus 5.5':dict(backend='claude',model='claude-opus-5-5'),
 'Claude Haiku 5.5':dict(backend='claude',model='claude-haiku-5-5'),
 'GPT-6.1 Sol':dict(backend='codex',model='gpt-6.1-sol'),
 'Qwen3.5-9B':dict(backend='openrouter',model='qwen/qwen3.5-9b-20260310')}
EFFORT='medium'
MAX_OPENROUTER_USD=5.0
MAX_NEW_CALLS=int(os.environ.get('NB_MAX_CALLS','6500' if PROFILE=='full' else '256'))
MAX_ATTEMPTS=3
TIMEOUT_S=240
BOOTSTRAPS=4000
PROTOCOL='35-judge-taste-v1'
CODEX_OPTIONS=['exec','--skip-git-repo-check','--ephemeral','--ignore-user-config','--sandbox','read-only',
 '--disable','shell_tool','--disable','unified_exec','--disable','apps','--disable','plugins',
 '--disable','multi_agent','--disable','browser_use','--disable','computer_use','--disable','image_generation',
 '--disable','code_mode','--disable','code_mode_host','--disable','shell_snapshot',
 '-c','web_search="disabled"','-c','project_doc_max_bytes=0','-c','model_reasoning_effort="medium"','--json']
CLAUDE_OPTIONS=['-p','--tools','','--safe-mode','--no-session-persistence','--output-format','json','--effort','medium']
OPENROUTER_SETTINGS=dict(provider=dict(only=['primeintellect/bf16'],allow_fallbacks=False),
                         reasoning=dict(effort='medium'),temperature=0,max_tokens=8192)
plt.rcParams.update({'figure.dpi':110,'savefig.dpi':160,'savefig.bbox':'tight','figure.facecolor':'white',
 'axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,'grid.alpha':.18,'axes.axisbelow':True,
 'axes.titlelocation':'left','font.size':11,'axes.prop_cycle':plt.cycler(color=['#23659b','#c57730','#378365','#8b59a1'])})
pd.set_option('display.max_colwidth',95)

def canonical(x):return json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':'))
def digest(x):return hashlib.sha256(canonical(x).encode()).hexdigest()
def file_hash(p):return hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest()
def utc():return datetime.now(timezone.utc).isoformat()
def read_json(name):return json.loads((DATA/name).read_text(encoding='utf-8'))
def read_jsonl(name):return [json.loads(x) for x in (DATA/name).read_text(encoding='utf-8').splitlines() if x]
def save_json(name,x):
 p=DATA/name;p.parent.mkdir(parents=True,exist_ok=True)
 temp=p.with_suffix(p.suffix+'.tmp');temp.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');temp.replace(p)
def save_jsonl(name,x):
 p=DATA/name;p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(''.join(json.dumps(y,ensure_ascii=False)+'\n' for y in x),encoding='utf-8')
def event(kind,**kwargs):
 with STATE_LOCK:
  with (DATA/'run_events.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(dict(at=utc(),event=kind,**kwargs),ensure_ascii=False)+'\n')

STATE_LOCK=threading.RLock();KEY_LOCKS={};CACHE={};NEW_CALLS=0;USED_KEYS=set()
CACHE_DIR=DATA/'cache';CACHE_DIR.mkdir(exist_ok=True)
for p in CACHE_DIR.glob('*.json'):
 r=json.loads(p.read_text(encoding='utf-8'));assert r['key']==digest(r['request']);CACHE[r['key']]=r
SEMAPHORES={'claude':threading.Semaphore(3),'codex':threading.Semaphore(3),'openrouter':threading.Semaphore(4)}

def store_record(r):
 with STATE_LOCK:
  CACHE[r['key']]=r
  p=CACHE_DIR/(r['key']+'.json');tmp=p.with_suffix('.tmp')
  tmp.write_text(json.dumps(r,ensure_ascii=False)+'\n',encoding='utf-8');tmp.replace(p)

def or_spend_bound():
 with STATE_LOCK:
  return sum(float(a.get('reported_usd') if a.get('reported_usd') is not None else a.get('reserved_usd',0))
             for r in CACHE.values() if r['request']['backend']=='openrouter' for a in r['attempts'])

def make_request(judge,prompt,purpose='judgment'):
 spec=JUDGES[judge]
 return dict(protocol=PROTOCOL,judge=judge,backend=spec['backend'],model=spec['model'],prompt=prompt,purpose=purpose,
             effort=EFFORT,settings=(OPENROUTER_SETTINGS if spec['backend']=='openrouter' else
                                    (CLAUDE_OPTIONS if spec['backend']=='claude' else CODEX_OPTIONS)))

def transport(request,max_tokens=4096):
 assert LIVE,'Replay attempted a live transport'
 backend=request['backend'];start=time.perf_counter();out={}
 if backend=='openrouter':
  import requests
  payload=dict(model=request['model'],messages=[dict(role='user',content=request['prompt'])],**request['settings'])
  payload['max_tokens']=max_tokens
  response=requests.post('https://openrouter.ai/api/v1/chat/completions',headers={
   'Authorization':'Bearer '+os.environ['OPENROUTER_API_KEY'],'Content-Type':'application/json'},json=payload,timeout=TIMEOUT_S)
  try:raw=response.json()
  except ValueError:raw=dict(non_json=response.text[:10000])
  choices=raw.get('choices',[]);msg=choices[0].get('message',{}) if choices else {}
  usage=raw.get('usage',{})
  out=dict(text=msg.get('content') or '',raw=raw,usage=usage,reported_usd=usage.get('cost'),
           finish_reason=choices[0].get('finish_reason') if choices else None,http_status=response.status_code,
           provider=raw.get('provider'),error=raw.get('error') if response.status_code!=200 or 'error' in raw else None)
 else:
  exe=shutil.which(backend+'.cmd') or shutil.which(backend)
  if not exe:raise RuntimeError('CLI not found: '+backend)
  isolated=TMP/'isolated';isolated.mkdir(exist_ok=True)
  env={k:v for k,v in os.environ.items() if k not in ('FORCE_COLOR','CLAUDECODE')};env.update(NO_COLOR='1',PYTHONIOENCODING='utf-8')
  cmd=[exe,*request['settings']]+(['--model',request['model']] if backend=='claude' else ['-m',request['model'],'-'])
  proc=subprocess.run(cmd,input=request['prompt'],text=True,encoding='utf-8',errors='replace',capture_output=True,
                      cwd=isolated,env=env,timeout=TIMEOUT_S)
  if backend=='claude':
   try:raw=json.loads(proc.stdout)
   except ValueError:raw=dict(result='',raw_stdout=proc.stdout)
   out=dict(text=raw.get('result',''),raw=raw,usage=raw.get('usage',{}),list_cost_usd=raw.get('total_cost_usd'),
            returncode=proc.returncode,error=str(raw.get('result','')) if raw.get('is_error') else None,stderr=proc.stderr)
  else:
   events=[]
   for line in proc.stdout.splitlines():
    try:events.append(json.loads(line))
    except ValueError:pass
   items=[e['item'] for e in events if e.get('type')=='item.completed']
   unexpected=[x for x in items if x.get('type') not in ('agent_message','reasoning','error')]
   assert not unexpected,'Judge used a tool'
   answers=[x['text'] for x in items if x.get('type')=='agent_message']
   out=dict(text=answers[-1] if answers else '',raw=events,raw_stdout=proc.stdout if not events else None,
            usage=next((e['usage'] for e in events if e.get('type')=='turn.completed'),{}),
            returncode=proc.returncode,stderr=proc.stderr,error=proc.stderr[-2000:] if proc.returncode else None)
 out.update(latency_s=time.perf_counter()-start,collected_at=utc())
 return out

def transient(out):
 text=canonical(out.get('error',''))+' '+(out.get('stderr','') or '')
 return out.get('http_status') in (408,429,500,502,503,504) or bool(re.search(r'rate.limit|overloaded|temporar|connection|try again|capacity',text,re.I))

def ask(judge,prompt,purpose='judgment'):
 global NEW_CALLS
 request=make_request(judge,prompt,purpose);key=digest(request)
 with STATE_LOCK:lock=KEY_LOCKS.setdefault(key,threading.Lock());USED_KEYS.add(key)
 with lock:
  if key in CACHE and CACHE[key].get('complete'):return CACHE[key]
  if not LIVE:raise RuntimeError('Offline cache miss '+key)
  record=CACHE.get(key,dict(key=key,request=request,attempts=[],complete=False))
  for old_attempt in record['attempts']:
   if old_attempt.get('pending'):
    old_attempt.update(pending=False,error='interrupted previous process',interrupted_at=utc())
    store_record(record)
  with SEMAPHORES[request['backend']]:
   for i in range(len(record['attempts']),MAX_ATTEMPTS):
    # A larger output allowance follows an actual truncation, never an incorrect choice.
    max_tokens=request['settings'].get('max_tokens',4096) if request['backend']=='openrouter' else 4096
    if i:max_tokens=max(16384,max_tokens)
    reserve=0.0
    with STATE_LOCK:
     if NEW_CALLS>=MAX_NEW_CALLS:raise RuntimeError('New-call budget exhausted')
     if request['backend']=='openrouter':
      reserve=len(prompt.encode('utf-8'))*.000000052+max_tokens*.000000076+.0001
      if or_spend_bound()+reserve>MAX_OPENROUTER_USD:raise RuntimeError('OpenRouter USD 5 cap reached')
     NEW_CALLS+=1
     effective=dict(request['settings'],max_tokens=max_tokens) if request['backend']=='openrouter' else request['settings']
     attempt=dict(pending=True,started_at=utc(),reserved_usd=reserve,max_tokens=max_tokens,
                  effective_settings=effective,full_request_key=digest(dict(request,settings=effective)))
     record['attempts'].append(attempt);store_record(record)
    start=time.perf_counter()
    try:out=transport(request,max_tokens)
    except subprocess.TimeoutExpired as exc:
     out=dict(text='',error='timeout',raw_stdout=(exc.stdout or b'').decode('utf-8','replace') if isinstance(exc.stdout,bytes) else exc.stdout,
              stderr=(exc.stderr or b'').decode('utf-8','replace') if isinstance(exc.stderr,bytes) else exc.stderr,
              latency_s=time.perf_counter()-start,collected_at=utc())
    except Exception as exc:
     out=dict(text='',error=type(exc).__name__+': '+str(exc),latency_s=time.perf_counter()-start,collected_at=utc())
    attempt.update(out,pending=False)
    retry=transient(out) or (out.get('finish_reason')=='length' and not out.get('text'))
    record['response']=out;record['complete']=not retry or i==MAX_ATTEMPTS-1;store_record(record)
    if record['complete']:break
    event('retry',key=key,attempt=i+1,error=out.get('error'),finish_reason=out.get('finish_reason'))
    time.sleep(min(30,5*2**i))
   if not record.get('complete'):
    record.update(complete=True,response=dict(text='',error='interrupted attempts exhausted'));store_record(record)
  return record

def parse_reply(response,lenient=False):
 text=response.get('text','').strip();error=str(response.get('error','') or '')
 if 'timeout' in error.lower():return dict(valid=False,failure='timeout')
 if response.get('error') or response.get('returncode',0)!=0:return dict(valid=False,failure='transport_error')
 if not text:return dict(valid=False,failure='empty')
 try:
  if lenient:
   obj=None
   for m in re.finditer(r'\{',text):
    try:obj=json.JSONDecoder().raw_decode(text[m.start():])[0];break
    except ValueError:pass
   if obj is None:raise ValueError()
  else:obj=json.loads(text)
 except ValueError:
  refused=bool(re.search(r"cannot (?:choose|judge|comply)|can't (?:choose|judge|comply)|unable to (?:choose|judge|comply)|I (?:must )?decline",text,re.I))
  return dict(valid=False,failure='refusal' if refused else 'no_parseable_json')
 if not isinstance(obj,dict):return dict(valid=False,failure='schema_failure')
 better=obj.get('better');confidence=obj.get('confidence');reason=obj.get('reason')
 if lenient:
  better=str(better).strip().upper()
  try:confidence=float(confidence) if not isinstance(confidence,bool) else confidence
  except (ValueError,TypeError):pass
 if (better not in ('A','B') or isinstance(confidence,bool) or not isinstance(confidence,(int,float))
     or not math.isfinite(confidence) or not 0<=confidence<=100 or not isinstance(reason,str) or not reason.strip()):
  return dict(valid=False,failure='schema_failure')
 if not lenient:
  sentences=[x for x in re.split(r'(?<=[.!?])\s+(?=[A-Z])',reason.strip()) if x]
  if set(obj)!= {'better','confidence','reason'} or len(sentences)>2:return dict(valid=False,failure='schema_failure')
 return dict(valid=True,failure='',better=better,confidence=float(confidence),reason=reason)

def parallel_jobs(jobs,label):
 results=[]
 with ThreadPoolExecutor(max_workers=10) as pool:
  fs=[pool.submit(ask,j['judge'],j['prompt'],j.get('purpose','judgment')) for j in jobs]
  for i,f in enumerate(as_completed(fs),1):
   results.append(f.result())
   if i%24==0 or i==len(fs):
    print(f'{label}: {i}/{len(fs)}; new attempts={NEW_CALLS}; OpenRouter bound=${or_spend_bound():.5f}',flush=True)
    if LIVE:event('collection_progress',label=label,completed=i,total=len(fs),new_attempts=NEW_CALLS,openrouter_bound_usd=or_spend_bound())
 return results

print(dict(profile=PROFILE,live=LIVE,cache_requests=len(CACHE),effort=EFFORT))
