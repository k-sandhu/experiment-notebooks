CACHE_PATH = DATA/'cache_requests.jsonl'
CACHE = {}
for cache_file in [CACHE_PATH,*sorted(DATA.glob('cache*probe.jsonl'))]:
 if not cache_file.exists():continue
 for line in cache_file.read_text(encoding='utf-8').splitlines():
  r=json.loads(line); assert r['key']==digest(r['request']) and r['key'] not in CACHE
  CACHE[r['key']]=r
cache_lock=threading.RLock(); key_locks=defaultdict(threading.Lock)
gates={b:threading.Semaphore(n) for b,n in dict(claude=3,codex=3,muse=2).items()}
for s in [*JUDGES.values(),*WRITERS.values()]:
 if s['backend'] in ('openrouter','decisions'): gates[s['model']]=threading.Semaphore(4)
new_calls=0; pending_usd=0.; used_keys=set()
def accounted_openrouter():
 interrupted=load(DATA/'interrupted_attempts.json')['total_reservation_usd'] if (DATA/'interrupted_attempts.json').exists() else 0.
 return interrupted+sum(float(r['response'].get('cost') or r['response'].get('unpriced_reservation') or 0) for r in CACHE.values() if r['request']['backend'] in ('openrouter','decisions'))
def cli_estimate(row):
 req=row['request'];o=row['response'];u=o.get('usage') or {};backend=req['backend']
 if backend=='claude':return o.get('list_cost_usd'),'reported CLI total_cost_usd'
 if backend=='codex':
  ri,ro=(2,10) if req['model']=='gpt-6.1-sol' else (.1,.5)
  inp=u.get('input_tokens',0) or 0;out=u.get('output_tokens',0) or 0;cached=u.get('cached_input_tokens',0) or 0
  return ((inp-cached)*ri+cached*ri*.05+out*ro)/1e6,'reported Codex tokens at public list prices'
 if backend=='muse':return (len(req['prompt'])/4*4+len(o.get('text',''))/4*20)/1e6,'proxy only: chars/4 at Muse Wonder 4/20; Full price unavailable; hidden reasoning omitted'
 return None,'reported OpenRouter usage cost'
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
 with tempfile.TemporaryDirectory(prefix='nb33_cli_') as tmp:
  exe=shutil.which(backend+'.cmd') or shutil.which(backend)
  env={k:v for k,v in os.environ.items() if k not in ('FORCE_COLOR',)};env['NO_COLOR']='1'
  if backend=='muse':
   pf=Path(tmp)/'prompt.txt';pf.write_text(req['prompt'],encoding='utf-8')
   cmd=[exe,*req['options'],'--model',req['model'],'--prompt-file',str(pf)]
   proc=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace',cwd=tmp,env=env,timeout=600)
   return dict(text=proc.stdout.strip(),raw=proc.stdout,stderr=proc.stderr,returncode=proc.returncode,usage={})
  cmd=[exe,*req['options'], '--model',req['model']] if backend=='claude' else [exe,*req['options'],'-m',req['model'],'-']
  proc=subprocess.run(cmd,input=req['prompt'],capture_output=True,text=True,encoding='utf-8',errors='replace',cwd=tmp,env=env,timeout=600)
  if backend=='claude':
   try: obj=json.loads(proc.stdout)
   except ValueError: obj={}
   return dict(text=obj.get('result',''),raw=proc.stdout,stderr=proc.stderr,returncode=proc.returncode,
    error=obj.get('result') if obj.get('is_error') else None,usage=obj.get('usage',{}),list_cost_usd=obj.get('total_cost_usd'))
  events=[]
  for line in proc.stdout.splitlines():
   try: events.append(json.loads(line))
   except ValueError: pass
  items=[e.get('item',{}) for e in events if e.get('type')=='item.completed']
  tools=[i for i in items if i.get('type') not in ('agent_message','reasoning','error')]
  assert not tools, 'Model attempted tool use'
  answers=[i['text'] for i in items if i.get('type')=='agent_message']
  return dict(text=answers[-1] if answers else '',raw=events,stderr=proc.stderr,returncode=proc.returncode,
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
 raw=o.get('raw',{});messages=[str(o.get('error') or ''),str(o.get('stderr') or '')]
 if isinstance(raw,dict):messages.append(str(raw.get('error','')))
 elif isinstance(raw,list):
  for event in raw:
   if event.get('type') in ('error','turn.failed'):messages.append(str(event.get('message') or event.get('error') or ''))
 error=' '.join(messages)
 return bool(o.get('status') in (429,500,502,503,504) or re.search(r'rate.?limit|overloaded|too many requests|at capacity|temporarily unavailable',error,re.I) or o.get('finish_reason')=='length')

def ask(spec,prompt,purpose,budget=1600,temperature=0,choices=None,state=None):
 global new_calls,pending_usd
 if spec['backend']=='decisions' and choices is None:raise ValueError('Decisions requires the actual answer texts as choices')
 base=request_for(spec,prompt,purpose,budget,temperature,choices,state)
 base_key=digest(base)
 with key_locks[base_key]:
  attempts=[]
  for attempt in range(3):
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
     reservation=max(.001,len(canonical(req).encode())*spec.get('rate_in',.15)/1e6+req.get('payload',{}).get('max_tokens',100)*spec.get('rate_out',.6)/1e6)
     with cache_lock:
      if new_calls>=MAX_NEW_CALLS: raise RuntimeError('Call cap')
      if spec['backend'] in ('openrouter','decisions'):
       if accounted_openrouter()+pending_usd+reservation>MAX_OPENROUTER_USD: raise RuntimeError('USD 5 OpenRouter guard')
       pending_usd+=reservation
      new_calls+=1
     start=time.perf_counter(); started=now()
     try: out=transport(req)
     except Exception as exc: out=dict(text='',error=type(exc).__name__+': '+str(exc)[:2000],raw={},usage={})
     out.update(latency_s=time.perf_counter()-start,started_at=started,completed_at=now())
     if spec['backend'] in ('openrouter','decisions') and out.get('cost') is None: out['unpriced_reservation']=reservation
     row=dict(key=key,request=req,response=out)
     with cache_lock:
      CACHE[key]=row
      with CACHE_PATH.open('a',encoding='utf-8') as f: f.write(canonical(row)+'\n'); f.flush()
      if spec['backend'] in ('openrouter','decisions'): pending_usd-=reservation
   attempts.append(key)
   o=row['response']; raw=o.get('raw',{}); err=str(o.get('error') or '')+' '+str(raw.get('error','') if isinstance(raw,dict) else '')+' '+o.get('stderr','')
   retry=retry_required(o)
   if not retry or attempt==2: return dict(**row,attempt_keys=attempts)
   if LIVE: log('retry',key=key,purpose=purpose,reason=err[:500]); time.sleep(3*(attempt+1))

