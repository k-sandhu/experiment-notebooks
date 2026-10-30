def evaluate_judgment(job):
 item,name,order,stage=job;spec=JUDGES[name]
 extra={}
 if spec['backend']=='decisions':
  a,b=('A','B') if order=='AB' else ('B','A')
  extra=dict(choices={'A':item['candidates'][a]['text'],'B':item['candidates'][b]['text']},state=DECISION_STATE_TEMPLATE.format(task=item['task']))
 row=ask(spec,judge_prompt(item,order),stage+':judge:'+item['item_id']+':'+order,budget=1600,**extra)
 strict=parse_judgment(row,True);loose=parse_judgment(row,False);complete=parse_judgment(row,False,allow_truncated=False)
 shown_better=item['better'] if order=='AB' else ('B' if item['better']=='A' else 'A')
 out=dict(item_id=item['item_id'],split=item['split'],family=item['family'],judge=name,order=order,
  displayed_better=shown_better,better_position=1 if shown_better=='A' else 2,raw_reply_cache_key=row['key'],
  strict_winner=strict['winner'],lenient_winner=loose['winner'],complete_json_winner=complete['winner'],complete_json_correct=None if complete['winner'] is None else complete['winner']==shown_better,complete_json_unreadable_type=complete['unreadable_type'],lenient_recovery_type=loose.get('recovery_type',''),confidence=loose['confidence'],reason=loose['reason'],
  strict_correct=None if strict['winner'] is None else strict['winner']==shown_better,
  correct=None if loose['winner'] is None else loose['winner']==shown_better,
  strict_unreadable_type=strict['unreadable_type'],unreadable_type=loose['unreadable_type'],
  latency_s=sum(CACHE[k]['response']['latency_s'] for k in row['attempt_keys']),
  cost=sum(float(CACHE[k]['response'].get('cost') or 0) for k in row['attempt_keys']) if spec['backend'] in ('openrouter','decisions') else None,
  cli_estimated_list_cost_usd=sum(float(cli_estimate(CACHE[k])[0] or 0) for k in row['attempt_keys']) if spec['backend'] in OPTIONS else None,cost_basis=cli_estimate(row)[1],
  trap=item['tags']['trap'],error_source=item['error_source'],attempts=len(row['attempt_keys']))
 winner=out['lenient_winner']
 if spec['backend']=='decisions' and winner is not None:
  probabilities=row['response']['raw']['answers']['winner']['probabilities'];total=sum(probabilities.values())
  out.update(probability_A=probabilities['A']/total,probability_B=probabilities['B']/total,provider_confidence=row['response']['raw']['answers']['winner'].get('confidence'))
 else:out.update(probability_A=None,probability_B=None,provider_confidence=None)
 out['canonical_winner']=winner if order=='AB' or winner is None else ('B' if winner=='A' else 'A')
 return out
def read_solve_response(item,row,strict=True):
 o=row['response'];body=o.get('text','').strip()
 fail=lambda kind,solution='':dict(correct=None,unreadable_type=kind,solution=solution,value=None,passed=None,total=None,execution_error='',runtime_errors=None)
 if 'Timeout' in str(o.get('error')):return fail('timeout')
 if o.get('error') or o.get('returncode',0) or o.get('status',200)!=200:return fail('transport_error')
 if not body:return fail('empty')
 try:
  if strict:obj=json.loads(body,parse_float=Decimal)
  else:
   decoder=json.JSONDecoder(parse_float=Decimal);obj=None
   for match in re.finditer(r'\{',body):
    try:obj=decoder.raw_decode(body[match.start():])[0];break
    except ValueError:pass
   if obj is None:raise ValueError('No complete JSON')
 except (ValueError,TypeError):
  refused=re.search(r'\b(I cannot|I can.t|unable to)\s+(solve|assist|comply|provide|write)',body,re.I)
  return fail('refusal' if refused else 'no_parseable_json')
 field='code' if item['family']=='code' else 'answer'
 if not isinstance(obj,dict) or (strict and set(obj)!={field}):return fail('schema_failure')
 value=obj.get(field)
 if not strict and item['family']=='worked' and type(value) in (int,float,Decimal):
  if isinstance(value,Decimal) and not value.is_finite():return fail('schema_failure')
  if isinstance(value,float) and not math.isfinite(value):return fail('schema_failure')
  value=format(value,'f') if isinstance(value,Decimal) else str(value)
 if not isinstance(value,str):return fail('schema_failure')
 if re.match(r'\s*(I cannot|I can.t|unable to)\s+(solve|assist|comply|provide|write)',value,re.I):return fail('refusal',value)
 if item['family']=='worked':
  if strict and not re.fullmatch(r'[-+]?\d[\d,]*(?:\.\d+)?(?:/\d+)?',value.strip()):return fail('schema_failure',value)
  scalar=value.strip()
  if not strict:scalar=re.sub(r'^Final answer:\s*','',scalar,flags=re.I)
  if '\n' in scalar or '\r' in scalar:return fail('schema_failure',value)
  number=numeric_answer('Final answer: '+scalar)
  if number is None:return fail('schema_failure',value)
  return dict(correct=number==Fraction(item['exact_answer']),unreadable_type='',solution=value,value=str(number),passed=None,total=None,execution_error='',runtime_errors=None)
 result=check_answer(item,value)
 # Valid JSON containing broken Python is a readable, wrong task answer.
 return dict(correct=bool(result['correct']),unreadable_type='',solution=value,value=None,passed=result.get('passed',0),total=result.get('total',len(item['hidden_tests'])),execution_error=result.get('error',''),runtime_errors=result.get('runtime_errors'))

def evaluate_solve(job):
 item,name,stage=job
 row=ask(JUDGES[name],solve_prompt(item),stage+':solve:'+item['item_id'],budget=2600)
 strict=read_solve_response(item,row,True);loose=read_solve_response(item,row,False)
 return dict(item_id=item['item_id'],family=item['family'],judge=name,raw_reply_cache_key=row['key'],
  strict_correct=strict['correct'],correct=loose['correct'],strict_unreadable_type=strict['unreadable_type'],unreadable_type=loose['unreadable_type'],
  solution=loose['solution'],normalized_value=loose['value'],passed=loose['passed'],total=loose['total'],
  execution_error=loose['execution_error'],strict_execution_error=strict['execution_error'],runtime_errors=loose['runtime_errors'],
  latency_s=sum(CACHE[k]['response']['latency_s'] for k in row['attempt_keys']),
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
 row=judgments.iloc[0];item=next(i for i in items if i['item_id']==row.item_id);cached=CACHE[row.raw_reply_cache_key]
 assert cached['request']['prompt']==judge_prompt(item,row.order)
 print('Worked readout item:',item['item_id'],'| Judge:',row.judge,'| Order:',row.order)
 display(pd.DataFrame([dict(item_id=i['item_id'],family=i['family'],better=i['better'],error_source=i['error_source'],trap=i['tags']['trap']) for i in items]).head(12))
 print('TASK:',item['task'][:1800]);print('CANDIDATES:',json.dumps(item['candidates'],indent=1)[:5000])
 print('EXACT PROMPT:',cached['request']['prompt'][:3000]);print('RAW RESPONSE:',cached['response'].get('text') or cached['response'].get('raw'));display(judgments.head())

