# Reporting-only analyses added after inspecting the test results.
METHOD_NAMES = {
 'M0':'No guidance', 'M1':'Written rules', 'M2':'8 random past choices',
 'M3':'8 similar past choices', 'M4':'Distilled rubric', 'M5':'Rules + 8 random choices'}

def named_table(frame):
 frame=frame.copy()
 for col in ['method','reference']:
  if col in frame:
   frame[col+'_name']=frame[col].map(METHOD_NAMES).fillna(frame[col])
 return frame

def reader_table(frame):
 frame=frame.copy()
 for col in ['method','reference']:
  if col in frame:
   frame[col]=frame[col].map(METHOD_NAMES).fillna(frame[col])
   frame=frame.drop(columns=[col+'_name'],errors='ignore')
 if 'comparison' in frame:
  frame['comparison']=frame.comparison.map(lambda s:re.sub(r'\bM[0-5]\b',lambda m:METHOD_NAMES[m.group()],s) if isinstance(s,str) else s)
 return frame.rename(columns={**METHOD_NAMES,'m3_minus_m0':'Similar choices minus No guidance'})

def save_named_tables():
 for path in DATA.glob('*.csv'):
  frame=pd.read_csv(path)
  if 'method' in frame or 'reference' in frame:
   # Read as strings to preserve the original numeric representations.
   frame=pd.read_csv(path,dtype=str,keep_default_na=False)
   named_table(frame).to_csv(path,index=False)

def lexical_words(text):
 return re.findall(r"[A-Za-z0-9]+(?:['’][A-Za-z0-9]+)*",text)

def mean_sentence_length(text):
 sentences=[s for s in re.split(r'[.!?]+(?:[\s\n]+|$)|\n\s*\n',text) if lexical_words(s)]
 return sum(len(lexical_words(s)) for s in sentences)/len(sentences) if sentences else 0.0

def syllables(word):
 word=re.sub('[^a-z]','',word.lower())
 if not word:return 1
 count=len(re.findall('[aeiouy]+',word))
 if word.endswith('e') and not re.search(r'[^aeiouy]le$',word) and count>1:count-=1
 return max(1,count)

def text_reporting(judgments):
 features=[]
 for p in TEST:
  row=dict(pair_id=p['pair_id'],notebook=p['notebook'])
  for side in ['before','after']:
   words=lexical_words(p[side]);row[side+'_words']=len(words)
   row[side+'_mean_sentence_words']=mean_sentence_length(p[side])
   row[side+'_polysyllables_per_100_words']=100*sum(syllables(w)>=3 for w in words)/len(words)
   row[side+'_mechanical_violations']=p[side+'_violations']
  row['length_direction']='shorter' if row['after_words']<row['before_words'] else 'longer' if row['after_words']>row['before_words'] else 'equal'
  features.append(row)
 features=pd.DataFrame(features);features.to_csv(DATA/'text_features.csv',index=False)
 features[['pair_id','notebook','before_words','after_words','length_direction']].to_csv(DATA/'length_direction.csv',index=False)
 baselines=[];decisions=[]
 for name,col in [('Pick the shorter version','words'),('Shorter mean sentence length','mean_sentence_words'),
                  ('Fewer polysyllabic words','polysyllables_per_100_words'),('Mechanical rule checker','mechanical_violations')]:
  before=features['before_'+col];after=features['after_'+col]
  correct=after<before;wrong=after>before;ties=after==before;n=len(features)
  lo,hi=wilson(int(correct.sum()),n);lo=max(0.0,lo);hi=min(1.0,hi)
  dl,dh=wilson(int(correct.sum()),int((~ties).sum()))
  baselines.append(dict(baseline=name,pairs=n,correct=int(correct.sum()),wrong=int(wrong.sum()),undecided=int(ties.sum()),
   unreadable=0,agreement=float(correct.mean()),ci_low=lo,ci_high=hi,decided=int((~ties).sum()),
   decided_agreement=float(correct.sum()/(~ties).sum()) if (~ties).sum() else np.nan,decided_ci_low=dl,decided_ci_high=dh))
  for i,r in features.iterrows():
   decisions.append(dict(pair_id=r.pair_id,baseline=name,before_value=before[i],after_value=after[i],
    choice='accepted' if correct[i] else 'earlier' if wrong[i] else 'undecided'))
 baselines=pd.DataFrame(baselines);baselines.to_csv(DATA/'text_baselines.csv',index=False)
 pd.DataFrame(decisions).to_csv(DATA/'text_baseline_decisions.csv',index=False)
 joined=judgments.merge(features[['pair_id','length_direction']],on='pair_id',validate='many_to_one')
 lengths=summarize(joined,['judge','method','length_direction']).query("parser == 'strict'").copy()
 named_table(lengths).to_csv(DATA/'agreement_by_length_direction.csv',index=False)
 sensitivity=[]
 for sample,frame in [('All 42 pairs',judgments),('Without notebook 26',judgments[~judgments.notebook.str.match(r'notebooks/26-')])]:
  scores=summarize(frame,['judge','method']).query("parser == 'strict'")
  for judge,g in frame.groupby('judge'):
   per=g.groupby(['pair_id','method']).strict_correct.mean().unstack('method')
   delta=per['M3']-per['M0'];lo,hi=ci_boot(delta)
   for r in scores[scores.judge==judge].to_dict('records'):
    r.update(sample=sample,source_groups=frame.notebook.nunique(),reference='M0',comparison='M3 minus M0',
     m3_minus_m0=float(delta.mean()),delta_ci_low=lo,delta_ci_high=hi)
    sensitivity.append(r)
 sensitivity=pd.DataFrame(sensitivity)
 named_table(sensitivity).to_csv(DATA/'sensitivity_without_26.csv',index=False)
 return features,baselines,lengths,sensitivity

def method_costs(jobs):
 rows=[]
 for job in jobs:
  rec=CACHE[digest(make_request(job['judge'],job['prompt'],job['purpose']))]
  attempts=rec['attempts'];backend=rec['request']['backend']
  usage_attempt,u=next(((i+1,a['usage']) for i,a in enumerate(attempts) if a.get('usage') and ('input_tokens' in a['usage'] or 'prompt_tokens' in a['usage'])),(0,{}))
  if backend=='claude' and 'input_tokens' in u:
   tokens=sum(u.get(k,0) or 0 for k in ['input_tokens','cache_creation_input_tokens','cache_read_input_tokens'])
   source='Recorded input + cache creation + cache read tokens'
  elif 'input_tokens' in u or 'prompt_tokens' in u:
   tokens=u.get('input_tokens',u.get('prompt_tokens'));source='Recorded input tokens (cached tokens included)'
  else:tokens=len(job['prompt'])/4;source='Prompt characters / 4; usage missing'
  costs=[]
  for a in attempts:
   usage=a.get('usage') or {}
   if backend=='codex':
    inp=usage.get('input_tokens',0);cached=usage.get('cached_input_tokens',0);out=usage.get('output_tokens',0)
    cost=((inp-cached)*2+cached*.1+out*10)/1e6 if usage else None
   elif backend=='claude':cost=a.get('list_cost_usd')
   else:cost=a.get('reported_usd')
   costs.append(cost)
  elapsed=(datetime.fromisoformat(attempts[-1]['collected_at'])-datetime.fromisoformat(attempts[0]['started_at'])).total_seconds()
  rows.append(dict(key=rec['key'],judge=job['judge'],method=job['method'],prompt_tokens=tokens,prompt_token_source=source,prompt_usage_attempt=usage_attempt,
   prompt_token_fallback=not bool(u),seconds=elapsed,transport_seconds=sum(a.get('latency_s',0) for a in attempts),
   attempts=len(attempts),known_cost_usd=sum(c for c in costs if c is not None),unpriced_attempts=sum(c is None for c in costs),
   cost_source='OpenRouter reported cost' if backend=='openrouter' else 'Claude CLI total_cost_usd' if backend=='claude' else 'Sol $2/$0.10/$10 per million uncached/cached input/output tokens'))
 detail=pd.DataFrame(rows);named_table(detail).to_csv(DATA/'method_cost_requests.csv',index=False)
 summary=[]
 for (judge,method),g in detail.groupby(['judge','method']):
  summary.append(dict(judge=judge,method=method,requests=len(g),mean_prompt_tokens=float(g.prompt_tokens.mean()),
   prompt_token_source='; '.join(sorted(g.prompt_token_source.unique())),prompt_token_fallback_requests=int(g.prompt_token_fallback.sum()),
   median_seconds=float(g.seconds.median()),mean_seconds=float(g.seconds.mean()),seconds_basis='First attempt start to final attempt completion, including retry waits; queue time excluded',
   dollars_per_100_judgments=float(g.known_cost_usd.sum()/len(g)*100),known_cost_usd=float(g.known_cost_usd.sum()),
   unpriced_attempts=int(g.unpriced_attempts.sum()),cost_source=g.cost_source.iloc[0],attempts=int(g.attempts.sum()),
   attempts_per_request=float(g.attempts.mean()),cost_note='Known reported/valued cost only; unpriced attempts excluded and counted separately'))
 summary=pd.DataFrame(summary);named_table(summary).to_csv(DATA/'method_cost.csv',index=False)
 return summary

print('Reporting labels, frozen-text baselines, source sensitivity and cost helpers defined.')

_original_display=display
def display(*objects,**kwargs):
 return _original_display(*(reader_table(o) if isinstance(o,pd.DataFrame) else o for o in objects),**kwargs)

def json_records(frame):
 return frame.astype(object).where(pd.notna(frame),'').to_dict('records')
