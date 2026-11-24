
# %% Setup
import ast, copy, gzip, hashlib, itertools, json, math, os, platform, random, re, shutil, subprocess, sys, tempfile, threading, time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
from IPython.display import display

ROOT = Path.cwd()
DATA, FIG = ROOT/'data', ROOT/'figures'
DATA.mkdir(exist_ok=True); FIG.mkdir(exist_ok=True)
TMP = DATA/'tmp'
TMP.mkdir(exist_ok=True)
tempfile.tempdir = str(TMP.resolve())
for temp_name in ('TMP','TEMP','TMPDIR'):os.environ[temp_name]=str(TMP.resolve())
LIVE = os.environ.get('NB_LIVE') == '1'
if not LIVE:
 def offline_network_guard(*args,**kwargs):raise RuntimeError('Network disabled in notebook replay')
 requests.sessions.Session.request=offline_network_guard
PROFILE = os.environ.get('NB_PROFILE', 'smoke' if LIVE else 'full')
N_TEST_PER_FAMILY = 60 if PROFILE == 'full' else 1
N_POLISHED_PER_FAMILY = 30 if PROFILE == 'full' else 1
STAGE = os.environ.get('NB_STAGE', 'all')
WORKERS = 7
N_BOOTSTRAP = 5000
SOURCE_COMMIT = 'cf854303'
STARTED = time.perf_counter()
N_DEV_PER_FAMILY = 6
MAX_WRITER_ASSISTED_ATTEMPTS = 8
MAX_TRANSCRIPTION_CHARS = 2200
MAX_CHUNK_ATTEMPTS = 8
LONG_MESSAGE_WORD_TARGETS = {7:1000, 8:1600, 9:2400, 10:700, 11:1000, 12:1400}
SEED = 3310302026
AUTHORED_ON = '2026-10-30'
MAX_OPENROUTER_USD = 5.00
MAX_NEW_CALLS = 16000
BOOTSTRAPS = 5000
PROTOCOL = 'structured-judging-v1.0'
JUDGES = {
 'Sol': dict(backend='codex', model='gpt-6.1-sol'),
 'Luna': dict(backend='codex', model='gpt-6-luna'),
 'Granite 8B': dict(backend='openrouter', model='ibm-granite/granite-4.2-8b-20260831', provider='coreweave/bf16', rate_in=.06, rate_out=.15, reasoning='none', json_mode=True),
}
AUTHOR = dict(backend='claude', model='claude-opus-5-5')
WRITERS = {'Checklist author': AUTHOR}
METHODS = ['free_form','exam_prompt','general_rubric','item_checklist','separate_scoring','own_requirements']
FAMILIES = ['code','worked','instructions','grounded']
CODEX_OPTIONS = ['exec','--skip-git-repo-check','--ephemeral','--ignore-user-config','--sandbox','read-only',
 '--disable','shell_tool','--disable','unified_exec','--disable','apps','--disable','plugins','--disable','multi_agent',
 '--disable','browser_use','--disable','computer_use','--disable','image_generation','--disable','code_mode',
 '--disable','code_mode_host','--disable','shell_snapshot','-c','web_search="disabled"',
 '-c','model_reasoning_effort="medium"','--json','-c','project_doc_max_bytes=0']
CLAUDE_OPTIONS = ['-p','--tools','','--safe-mode','--no-session-persistence','--output-format','json','--effort','medium']
MUSE_OPTIONS = ['exec','--preset','empty','--no-session-log','--disable-web-tools','--disable-reminders',
 '--disable-request-user-input','--no-foreign-personal-context','--disable-write','--disable-shell',
 '--reasoning-effort','medium','--max-model-steps','1']
OPTIONS = dict(claude=CLAUDE_OPTIONS,codex=CODEX_OPTIONS,muse=MUSE_OPTIONS)
plt.rcParams.update({'figure.dpi':110,'savefig.dpi':160,'savefig.bbox':'tight','axes.spines.top':False,
 'axes.spines.right':False,'axes.grid':True,'grid.alpha':.16,'axes.axisbelow':True,'axes.titlelocation':'left',
 'font.size':10,'figure.facecolor':'white','axes.prop_cycle':plt.cycler(color=['#315f9c','#ac5832','#34816b','#8654a2'])})
pd.set_option('display.max_colwidth',100)
def canonical(x): return json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False)
def digest(x): return hashlib.sha256(canonical(x).encode()).hexdigest()
def filehash(p): return hashlib.sha256(Path(p).read_bytes().replace(b'\r\n',b'\n')).hexdigest()
def save(p,x): Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
def load(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def now(): return datetime.now(timezone.utc).isoformat()
def log(event,**kw):
 if LIVE:
  with (DATA/'run_log.jsonl').open('a',encoding='utf-8') as f: f.write(canonical(dict(at=now(),event=event,**kw))+'\n')
def first_json(s):
 for m in re.finditer(r'\{',s):
  try: return json.JSONDecoder().raw_decode(s[m.start():])[0]
  except ValueError: pass
 raise ValueError('No complete JSON object')

print('Mode:', 'live' if LIVE else 'replay', '| Profile:', PROFILE, '| Stage:',STAGE)

# %% Cached transports
CACHE_PATH = DATA/'cache_requests.jsonl'
ATTEMPT_PATH = DATA/'nonfinal_attempts.jsonl'
QUOTA_PATTERN = re.compile(r'usage\s+limit|hit\s+your\s+usage\s+limit|try\s+again\s+at|quota|credit\s+balance|insufficient\s+credits',re.I)
class CollectorQuotaStop(RuntimeError):pass
collector_stop=threading.Event()
def response_diagnostics(out):
 return '\n'.join(v if isinstance(v,str) else json.dumps(v,ensure_ascii=False,default=str) for k,v in out.items() if k in ('text','stdout','stderr','error','raw'))
def error_channels(out):
 channels=[]
 for key in ('stderr','error'):
  if out.get(key):channels.append(str(out[key]))
 raw=out.get('raw');objects=[];plain=[]
 if isinstance(raw,list):objects.extend(raw)
 elif isinstance(raw,dict):objects.append(raw)
 else:
  for line in str(out.get('stdout') or raw or '').splitlines():
   try:objects.append(json.loads(line))
   except ValueError:plain.append(line)
 for obj in objects:
  if not isinstance(obj,dict):continue
  kind=obj.get('type');item=obj.get('item')
  if kind in ('error','turn.failed'):
   channels.append(json.dumps(obj,ensure_ascii=False));continue
  if isinstance(item,dict) and item.get('type')=='error':
   channels.append(json.dumps(item,ensure_ascii=False));continue
  subtype=obj.get('subtype')
  if obj.get('is_error') is True or (subtype and subtype!='success'):
   channels.append(json.dumps(obj,ensure_ascii=False));continue
  if obj.get('error'):channels.append(json.dumps(obj['error'],ensure_ascii=False))
  success=obj.get('is_error') is False or subtype=='success' or kind in ('agent_message','turn.completed') or (isinstance(item,dict) and item.get('type')=='agent_message')
  if out.get('returncode',0) and not success and any(key in obj for key in ('message','detail','details','errors')):
   channels.append(json.dumps(obj,ensure_ascii=False))
  if out.get('status',200)!=200 and obj.get('unparsed_body'):channels.append(str(obj['unparsed_body']))
 # Non-JSON stdout from a failed CLI is an error channel; successful output is excluded.
 if out.get('returncode',0) and plain:channels.extend(plain)
 return '\n'.join(channels)

def quota_message(out):
 diagnostic=error_channels(out);match=QUOTA_PATTERN.search(diagnostic)
 return diagnostic[max(0,match.start()-150):match.end()+1200] if match else None
NONFINAL=[]
if ATTEMPT_PATH.exists():
 NONFINAL=[json.loads(line) for line in ATTEMPT_PATH.read_text(encoding='utf-8').splitlines() if line.strip()]
CACHE = {}
for cache_file in [DATA/'cache_requests.jsonl.gz',CACHE_PATH,*sorted(DATA.glob('cache*probe.jsonl'))]:
 if not cache_file.exists():continue
 opener=gzip.open(cache_file,'rt',encoding='utf-8') if cache_file.suffix=='.gz' else cache_file.open(encoding='utf-8')
 with opener as stream:
  for line in stream:
   r=json.loads(line);assert r['key']==digest(r['request'])
   if quota_message(r['response']):continue
   assert r['key'] not in CACHE
   CACHE[r['key']]=r
cache_lock=threading.RLock(); key_locks=defaultdict(threading.Lock)
gates={b:threading.Semaphore(n) for b,n in dict(claude=2,codex=2,muse=1).items()}
for s in [*JUDGES.values(),*WRITERS.values()]:
 if s['backend'] in ('openrouter','decisions'): gates[s['model']]=threading.Semaphore(3)
new_calls=0; pending_usd=0.; used_keys=set()
def accounted_openrouter():
 interrupted=load(DATA/'interrupted_attempts.json')['total_reservation_usd'] if (DATA/'interrupted_attempts.json').exists() else 0.
 return interrupted+sum(float(r['response'].get('cost') or r['response'].get('unpriced_reservation') or 0) for r in [*CACHE.values(),*NONFINAL] if r['request']['backend'] in ('openrouter','decisions'))
def require_running():
 if collector_stop.is_set() or (LIVE and (DATA/'quota_stop.json').exists()):raise CollectorQuotaStop('Collector stopped after a usage/quota limit; resume later from cache')
def record_nonfinal(row,disposition):
 row=dict(row,disposition=disposition,recorded_at=now())
 NONFINAL.append(row)
 with ATTEMPT_PATH.open('a',encoding='utf-8') as f:f.write(canonical(row)+'\n');f.flush()
def cli_estimate(row):
 req=row['request'];o=row['response'];u=o.get('usage') or {};backend=req['backend']
 if backend=='claude':return o.get('list_cost_usd'),'reported CLI total_cost_usd'
 if backend=='codex':
  ri,ro=(2,10) if req['model']=='gpt-6.1-sol' else (.1,.5)
  inp=u.get('input_tokens',0) or 0;out=u.get('output_tokens',0) or 0;cached=u.get('cached_input_tokens',0) or 0
  return ((inp-cached)*ri+cached*ri*.05+out*ro)/1e6,'reported Codex tokens at public list prices'
 if backend=='muse':return (len(req['prompt'])/4*4+len(o.get('text',''))/4*20)/1e6,'proxy only: chars/4 at Muse Wonder 4/20; Full price unavailable; hidden reasoning omitted'
 return None,'reported OpenRouter usage cost'
def cli_executable(backend):
 if backend=='codex':
  if os.environ.get('NB_CODEX_EXE'):return os.environ['NB_CODEX_EXE']
  wrapper=shutil.which('codex.cmd') or shutil.which('codex')
  if wrapper:
   native=Path(wrapper).parent/'node_modules/@openai/codex/node_modules/@openai/codex-win32-x64/vendor/x86_64-pc-windows-msvc/bin/codex.exe'
   if native.is_file():return str(native)
  return shutil.which('codex.exe') or shutil.which('codex')
 return shutil.which(backend+'.cmd') or shutil.which(backend)

def transport(req):
 assert LIVE,'Model transport is disabled in replay'
 backend=req['backend']
 if backend in ('openrouter','decisions'):
  url='https://openrouter.ai/api/alpha/decisions' if backend=='decisions' else 'https://openrouter.ai/api/v1/chat/completions'
  response=requests.post(url,json=req['payload'],headers={'Authorization':'Bearer '+os.environ['OPENROUTER_API_KEY'],'Content-Type':'application/json'},timeout=180)
  try: raw=response.json()
  except ValueError: raw={'unparsed_body':response.text}
  choices=raw.get('choices') or []
  msg=choices[0].get('message',{}) if choices else {}
  return dict(text=msg.get('content') or '',raw=raw,status=response.status_code,usage=raw.get('usage',{}),
   cost=raw.get('usage',{}).get('cost'),finish_reason=choices[0].get('finish_reason') if choices else None)
 with tempfile.TemporaryDirectory(prefix='nb37_cli_',dir=TMP) as tmp:
  exe=cli_executable(backend)
  env={k:v for k,v in os.environ.items() if k not in ('FORCE_COLOR',)};env['NO_COLOR']='1'
  if backend=='muse':
   pf=Path(tmp)/'prompt.txt';pf.write_text(req['prompt'],encoding='utf-8')
   cmd=[exe,*req['options'],'--model',req['model'],'--prompt-file',str(pf)]
   proc=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace',cwd=tmp,env=env,timeout=600)
   return dict(text=proc.stdout.strip(),raw=proc.stdout,stdout=proc.stdout,stderr=proc.stderr,returncode=proc.returncode,usage={})
  cmd=[exe,*req['options'], '--model',req['model']] if backend=='claude' else [exe,*req['options'],'-m',req['model'],'-']
  proc=subprocess.run(cmd,input=req['prompt'],capture_output=True,text=True,encoding='utf-8',errors='replace',cwd=tmp,env=env,timeout=600)
  if backend=='claude':
   try: obj=json.loads(proc.stdout)
   except ValueError: obj={}
   return dict(text=obj.get('result',''),raw=proc.stdout,stdout=proc.stdout,stderr=proc.stderr,returncode=proc.returncode,
    error=obj.get('result') if obj.get('is_error') else None,usage=obj.get('usage',{}),list_cost_usd=obj.get('total_cost_usd'))
  events=[]
  for line in proc.stdout.splitlines():
   try: events.append(json.loads(line))
   except ValueError: pass
  items=[e.get('item',{}) for e in events if e.get('type')=='item.completed']
  tools=[i for i in items if i.get('type') not in ('agent_message','reasoning','error')]
  assert not tools, 'Model attempted tool use'
  answers=[i['text'] for i in items if i.get('type')=='agent_message']
  return dict(text=answers[-1] if answers else '',raw=events,stdout=proc.stdout,stderr=proc.stderr,returncode=proc.returncode,
   usage=next((e['usage'] for e in events if e.get('type')=='turn.completed'),{}))

def request_for(spec,prompt,purpose,budget=1600,temperature=0,choices=None,state=None):
 req=dict(protocol=PROTOCOL,backend=spec['backend'],model=spec['model'],prompt=prompt,purpose=purpose,timeout_s=600 if spec['backend'] in OPTIONS else 180)
 if spec['backend'] in OPTIONS: req['options']=OPTIONS[spec['backend']]
 else:
  payload=dict(model=spec['model'],provider=dict(order=[spec['provider']],allow_fallbacks=False))
  if spec['backend']=='decisions':
   payload.update(state=prompt if state is None else state,questions={'winner':dict(type='choice',instructions='Which answer is better? Correctness comes first. Presentation only breaks a tie in correctness. Choose exactly one.',criteria=choices if choices is not None else {'A':'{displayed_answer_A}','B':'{displayed_answer_B}'})})
  else:
   payload.update(messages=[dict(role='user',content=prompt)],max_tokens=budget,temperature=temperature)
   if spec.get('reasoning'):payload['reasoning']=dict(effort=spec['reasoning'])
   if spec.get('json_mode'):payload['response_format']=dict(type='json_object')
  req['payload']=payload
 return req

def retry_required(o):
 error=error_channels(o)
 if re.search(r'usage.policy|acceptable.use|Details:\s*\[bio\]',error,re.I):return False
 return bool(o.get('status') in (429,500,502,503,504) or re.search(r'rate.?limit|overloaded|too many requests|at capacity|temporarily unavailable',error,re.I) or o.get('finish_reason')=='length')

def ask(spec,prompt,purpose,budget=1600,temperature=0,choices=None,state=None):
 global new_calls,pending_usd
 require_running()
 if spec['backend']=='decisions' and choices is None:raise ValueError('Decisions requires the actual answer texts as choices')
 base=request_for(spec,prompt,purpose,budget,temperature,choices,state)
 base_key=digest(base)
 with key_locks[base_key]:
  attempts=[]
  for attempt in range(3):
   require_running()
   req=copy.deepcopy(base)
   req['attempt']=attempt
   if attempt and req['backend']=='openrouter': req['payload']['max_tokens']=min(6400,budget*2**attempt)
   key=digest(req)
   with cache_lock:
    used_keys.add(key)
    if key in CACHE: row=CACHE[key]
    else: row=None
   if row is None:
    if not LIVE: raise RuntimeError('Offline cache miss '+key+' '+purpose)
    gate=gates[spec['model'] if spec['backend'] in ('openrouter','decisions') else spec['backend']]
    with gate:
     require_running()
     reservation=max(.001,len(canonical(req).encode())*spec.get('rate_in',.15)/1e6+req.get('payload',{}).get('max_tokens',100)*spec.get('rate_out',.6)/1e6)
     with cache_lock:
      require_running()
      if new_calls>=MAX_NEW_CALLS: raise RuntimeError('Call cap')
      if spec['backend'] in ('openrouter','decisions'):
       if accounted_openrouter()+pending_usd+reservation>MAX_OPENROUTER_USD: raise RuntimeError('USD 5 OpenRouter guard')
       pending_usd+=reservation
      new_calls+=1
      with (DATA/'attempt_lifecycle.jsonl').open('a',encoding='utf-8') as f:f.write(canonical(dict(at=now(),event='started',key=key,backend=req['backend'],model=req['model'],purpose=purpose,reservation_usd=reservation if req['backend'] in ('openrouter','decisions') else 0))+'\n')
     start=time.perf_counter(); started=now()
     try: out=transport(req)
     except subprocess.TimeoutExpired as exc: out=dict(text='',error='TimeoutExpired',stdout=str(exc.stdout or ''),stderr=str(exc.stderr or ''),raw={},usage={})
     except Exception as exc: out=dict(text='',error=type(exc).__name__+': '+str(exc)[:2000],raw={},usage={})
     out.update(latency_s=time.perf_counter()-start,started_at=started,completed_at=now())
     if spec['backend'] in ('openrouter','decisions') and out.get('cost') is None: out['unpriced_reservation']=reservation
     row=dict(key=key,request=req,response=out)
     with cache_lock:
      with (DATA/'attempt_lifecycle.jsonl').open('a',encoding='utf-8') as f:f.write(canonical(dict(at=now(),event='returned',key=key,quota_limit=bool(quota_message(out))))+'\n')
      quota=quota_message(out)
      if quota or collector_stop.is_set():
       if quota:
        collector_stop.set()
        log('quota_limit_stop',key=key,model=req['model'],purpose=purpose,message=quota,no_final_reply_cached=True)
        save(DATA/'quota_stop.json',dict(at=now(),key=key,model=req['model'],purpose=purpose,message=quota,resumable=True))
       record_nonfinal(row,'quota_limit' if quota else 'completed_after_quota_stop')
       if spec['backend'] in ('openrouter','decisions'):pending_usd-=reservation
       raise CollectorQuotaStop(quota or 'In-flight attempt preserved without final caching after quota stop')
      CACHE[key]=row
      with CACHE_PATH.open('a',encoding='utf-8') as f: f.write(canonical(row)+'\n'); f.flush()
      if spec['backend'] in ('openrouter','decisions'): pending_usd-=reservation
   attempts.append(key)
   o=row['response']; raw=o.get('raw',{}); err=str(o.get('error') or '')+' '+str(raw.get('error','') if isinstance(raw,dict) else '')+' '+o.get('stderr','')
   retry=retry_required(o)
   if not retry or attempt==2: return dict(**row,attempt_keys=attempts)
   if LIVE: log('retry',key=key,purpose=purpose,reason=err[:500]); time.sleep(3*(attempt+1))


# %% Frozen checker and reading rules
def code_check(source,tests):
 try:
  ast.parse(source)
 except (SyntaxError,TypeError): return dict(readable=False,passed=0,total=len(tests),error='syntax')
 # Isolated cwd; no API credentials, no user site, restricted imports, one process per candidate.
 runner="""import json,sys,builtins,types
request=json.load(sys.stdin)
real_import=builtins.__import__
allowed={'math','decimal','fractions','collections','itertools','functools','datetime','calendar','re','statistics','bisect','heapq','operator','string','typing','copy','json','ast','dataclasses','numbers','unicodedata'}
def guarded(name,*a,**kw):
 if name.split('.')[0] not in allowed: raise ImportError('blocked import')
 return real_import(name,*a,**kw)
b=dict(vars(builtins));b['__import__']=guarded
for k in ['open','input','eval','exec','compile','breakpoint']:b.pop(k,None)
module=types.ModuleType('candidate');module.__dict__['__builtins__']=b;sys.modules['candidate']=module;ns=module.__dict__
try:
 exec(request['source'],ns)
 results=[];runtime_errors=0
 for t in request['tests']:
  try:
   before=json.dumps(t['input'],sort_keys=True)
   value=ns['solve'](t['input'])
   results.append(value==t['expected'] and before==json.dumps(t['input'],sort_keys=True))
  except Exception: results.append(False);runtime_errors+=1
 print(json.dumps({'readable':True,'passed':sum(results),'total':len(results),'checks':results,'runtime_errors':runtime_errors,'error':''}))
except Exception as e: print(json.dumps({'readable':False,'passed':0,'total':len(request['tests']),'error':type(e).__name__}))
"""
 try:
  with tempfile.TemporaryDirectory(prefix='nb33_code_') as tmp:
   env={'SYSTEMROOT':os.environ.get('SYSTEMROOT','C:\\Windows'),'NO_COLOR':'1'}
   p=subprocess.run([sys.executable,'-I','-c',runner],input=json.dumps(dict(source=source,tests=tests)),capture_output=True,text=True,encoding='utf-8',cwd=tmp,env=env,timeout=4)
  return json.loads(p.stdout)
 except subprocess.TimeoutExpired: return dict(readable=False,passed=0,total=len(tests),error='timeout')
 except (ValueError,OSError): return dict(readable=False,passed=0,total=len(tests),error='subprocess')


def numeric_answer(text):
 lines=re.findall(r'Final answer:\s*([^\n]*)',text,re.I)
 if not lines:return None
 m=re.fullmatch(r'([-+]?\d[\d,]*(?:\.\d+)?(?:/\d+)?)(?:\s+(?:credits?|litres?|units?|cents))?\.?',lines[-1].strip(),re.I)
 if not m:return None
 try:return Fraction(m.group(1).replace(',',''))
 except (ValueError,ZeroDivisionError):return None


def instruction_checks(text,rules):
 words=re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?",text)
 lower=[w.lower() for w in words]
 checks=dict(word_count=rules['min_words']<=len(words)<=rules['max_words'],required=rules['required'] in lower,
  forbidden=rules['forbidden'] not in lower,no_digits=not bool(re.search(r'\d',text)),
  paragraphs=len([p for p in re.split(r'\n\s*\n',text.strip()) if p.strip()])==rules['paragraphs'],
  opening=text.startswith(rules['opening']),closing=text.endswith(rules['closing']))
 return checks,len(words)


def check_answer(item,text):
 if item['family']=='code':
  code=text.strip()
  if code.startswith('```'):code=re.sub(r'^```(?:python)?\s*','',code).rsplit('```',1)[0].strip()
  out=code_check(code,item['hidden_tests']);out['correct']=out['readable'] and out['passed']==out['total'];out['normalized']=code
  return out
 if item['family']=='instructions':
  checks,wc=instruction_checks(text,item['rules']);return dict(correct=all(checks.values()),readable=True,checks=checks,word_count=wc,normalized=text)
 value=numeric_answer(text)
 return dict(correct=value==Fraction(item['exact_answer']),readable=value is not None,value=str(value) if value is not None else None,normalized=text)


def truncated_verdict_prefix(text):
 source=re.sub(r'^```(?:json)?\s*','',text.strip(),flags=re.I)
 pattern=r'\A\{\s*"winner"\s*:\s*(?P<w>"[^"\n]*")\s*,\s*"confidence"\s*:\s*(?P<c>"[^"\n]*"|-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*,\s*"reason"\s*:\s*"(?P<reason>[\s\S]*)\Z'
 match=re.match(pattern,source)
 if not match or not match['reason'].strip():return None
 try:return dict(winner=json.loads(match['w']),confidence=json.loads(match['c']),reason=match['reason'][:4000])
 except (ValueError,TypeError):return None


def parse_judgment(row,strict=True,allow_truncated=True):
 o=row['response'];s=o.get('text','').strip(); backend=row['request']['backend']
 fail=lambda t:dict(winner=None,confidence=None,reason='',unreadable_type=t,recovery_type='')
 if 'Timeout' in str(o.get('error')): return fail('timeout')
 if o.get('error') or o.get('status',200)!=200 or o.get('returncode',0): return fail('transport_error')
 if backend=='decisions':
  try:
   x=o['raw']['answers']['winner'];p=x['probabilities'];w=x['choice']
   assert x['type']=='choice' and set(p)=={'A','B'} and w in p
   assert all(type(v) in (int,float) and math.isfinite(v) and 0<=v<=1 for v in p.values())
   assert abs(sum(p.values())-1)<=.02 and p[w]>=max(p.values())-1e-6
   return dict(winner=w,confidence=100*p[w]/sum(p.values()),reason='',unreadable_type='',recovery_type='native_choice')
  except (AssertionError,KeyError,TypeError,ValueError): return fail('schema_failure')
 if not s: return fail('empty')
 if re.search(r'\b(I cannot|I can.t|unable to)\s+(evaluate|choose|assist|comply)',s,re.I): return fail('refusal')
 recovery='strict_json' if strict else 'complete_json'
 try:x=json.loads(s) if strict else first_json(s)
 except (ValueError,TypeError):
  x=truncated_verdict_prefix(s) if not strict and allow_truncated and o.get('finish_reason')=='length' else None
  if x is None:return fail('no_parseable_json')
  recovery='truncated_json_prefix'
 if not isinstance(x,dict): return fail('schema_failure')
 w=x.get('winner'); conf=x.get('confidence'); reason=x.get('reason')
 if not strict:
  w=str(w).strip().upper()
  if isinstance(conf,str):
   try: conf=float(conf.rstrip('%'))
   except ValueError: pass
 if (strict and set(x)!={'winner','confidence','reason'}) or w not in ('A','B') or type(conf) not in (float,int) or not math.isfinite(conf) or not 0<=conf<=100 or not isinstance(reason,str) or not reason.strip(): return fail('schema_failure')
 return dict(winner=w,confidence=float(conf),reason=reason,unreadable_type='',recovery_type=recovery)

