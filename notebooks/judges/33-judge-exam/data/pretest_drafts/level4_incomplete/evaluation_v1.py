def evaluate_judgment(job):
 item,name,order,stage=job;spec=JUDGES[name]
 row=ask(spec,judge_prompt(item,order),stage+':judge:'+item['item_id']+':'+order,budget=1600)
 strict=parse_judgment(row,True);loose=parse_judgment(row,False)
 shown_better=item['better'] if order=='AB' else ('B' if item['better']=='A' else 'A')
 out=dict(item_id=item['item_id'],split=item['split'],family=item['family'],judge=name,order=order,
  displayed_better=shown_better,better_position=1 if shown_better=='A' else 2,raw_reply_cache_key=row['key'],
  strict_winner=strict['winner'],lenient_winner=loose['winner'],confidence=loose['confidence'],reason=loose['reason'],
  strict_correct=None if strict['winner'] is None else strict['winner']==shown_better,
  correct=None if loose['winner'] is None else loose['winner']==shown_better,
  strict_unreadable_type=strict['unreadable_type'],unreadable_type=loose['unreadable_type'],
  latency_s=sum(CACHE[k]['response']['latency_s'] for k in row['attempt_keys']),
  cost=sum(float(CACHE[k]['response'].get('cost') or 0) for k in row['attempt_keys']) if spec['backend'] in ('openrouter','decisions') else None,
  cli_estimated_list_cost_usd=sum(float(cli_estimate(CACHE[k])[0] or 0) for k in row['attempt_keys']) if spec['backend'] in OPTIONS else None,cost_basis=cli_estimate(row)[1],
  trap=item['tags']['trap'],error_source=item['error_source'],attempts=len(row['attempt_keys']))
 winner=out['lenient_winner']
 out['canonical_winner']=winner if order=='AB' or winner is None else ('B' if winner=='A' else 'A')
 return out
def evaluate_solve(job):
 item,name,stage=job
 row=ask(JUDGES[name],solve_prompt(item),stage+':solve:'+item['item_id'],budget=2600)
 o=row['response'];strict_error='';loose_error=''
 try:strict=json.loads(o['text'].strip());assert isinstance(strict,dict)
 except (ValueError,AssertionError):strict={};strict_error='no_parseable_json' if o.get('text') else 'empty'
 try:loose=first_json(o.get('text',''));assert isinstance(loose,dict)
 except (ValueError,AssertionError):loose={};loose_error='no_parseable_json' if o.get('text') else 'empty'
 field='code' if item['family']=='code' else 'answer'
 def check(obj):
  val=obj.get(field)
  if not isinstance(val,str):return None,'schema_failure',''
  if item['family']!='code' and not re.fullmatch(r'[-+]?\d[\d,]*(?:\.\d+)?(?:/\d+)?',val.strip()):return None,'schema_failure',val
  answer=val if item['family']=='code' else 'Final answer: '+val
  c=check_answer(item,answer)
  if not c['readable']:return None,c.get('error') or 'unscorable',val
  return c,'',val
 sc,se,st=check(strict);lc,le,lt=check(loose)
 err='timeout' if 'Timeout' in str(o.get('error')) else 'transport_error' if o.get('error') or o.get('returncode',0) or o.get('status',200)!=200 else ''
 return dict(item_id=item['item_id'],family=item['family'],judge=name,raw_reply_cache_key=row['key'],
  strict_correct=sc['correct'] if sc else None,correct=lc['correct'] if lc else None,
  strict_unreadable_type=err or strict_error or se,unreadable_type=err or loose_error or le,
  solution=lt,normalized_value=lc.get('value') if lc else None,passed=lc.get('passed') if lc else None,
  total=lc.get('total') if lc else None,latency_s=sum(CACHE[k]['response']['latency_s'] for k in row['attempt_keys']),
  cost=sum(float(CACHE[k]['response'].get('cost') or 0) for k in row['attempt_keys']) if JUDGES[name]['backend']=='openrouter' else None,
  cli_estimated_list_cost_usd=sum(float(cli_estimate(CACHE[k])[0] or 0) for k in row['attempt_keys']) if JUDGES[name]['backend'] in OPTIONS else None,cost_basis=cli_estimate(row)[1],attempts=len(row['attempt_keys']))
def parallel_jobs(fn,jobs,label,workers=24):
 out=[]
 with ThreadPoolExecutor(workers) as pool:
  futures=[pool.submit(fn,j) for j in jobs]
  for f in as_completed(futures):
   out.append(f.result())
   if len(out)%48==0 or len(out)==len(jobs):print(label,len(out),'/',len(jobs),'new calls',new_calls,'OR USD',round(accounted_openrouter(),4),flush=True)
 return out
def collect(items,names,stage,solving=False):
 jobs=[(item,name,order,stage) for item in items for name in names for order in ['AB','BA']]
 judgments=pd.DataFrame(parallel_jobs(evaluate_judgment,jobs,stage+' judgments'))
 judgments=judgments.sort_values(['item_id','judge','order']).reset_index(drop=True)
 solves=pd.DataFrame()
 if solving:
  jobs=[(item,name,stage) for item in items if item['family'] in ('code','worked') for name in names if JUDGES[name]['backend']!='decisions']
  solves=pd.DataFrame(parallel_jobs(evaluate_solve,jobs,stage+' solves')).sort_values(['item_id','judge']).reset_index(drop=True)
 return judgments,solves
def validation_examples(items,judgments):
 item=items[0];row=judgments.iloc[0];cached=CACHE[row.raw_reply_cache_key]
 display(pd.DataFrame([dict(item_id=i['item_id'],family=i['family'],better=i['better'],error_source=i['error_source'],trap=i['tags']['trap']) for i in items]).head(12))
 print('TASK:',item['task'][:1800]);print('CANDIDATES:',json.dumps(item['candidates'],indent=1)[:5000])
 print('EXACT PROMPT:',cached['request']['prompt'][:3000]);print('RAW RESPONSE:',cached['response'].get('text') or cached['response'].get('raw'));display(judgments.head())

